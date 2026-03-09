# ui/window_simulation.py
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QPushButton, QFileDialog, QMessageBox, 
    QDoubleSpinBox, QSpinBox, QFormLayout, QTabWidget, QLineEdit
)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QIcon

from logic.controller_simulation import SimulationController
from ui.plot_canvas import MplCanvas
from ui.logger import LogWidget
from ui.worker import SimulationWorker

class SimulationWindow(QMainWindow):
    def __init__(self, launcher=None):
        super().__init__()
        self.launcher = launcher
        self.setWindowTitle("DOME - Surface Scaling Simulation")
        self.resize(1280, 850)
        
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        self.setWindowIcon(QIcon(resource_path("assets/icon_purple_gray.svg")))
        
        self.controller = SimulationController()
        
        # Track visual limits. None means "Auto"
        self.custom_limits = {
            "x_min": None, "x_max": None,
            "y_min": None, "y_max": None
        }
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # ==========================
        # LEFT PANEL: CONTROLS
        # ==========================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # --- LOAD EXISTING SIMULATION ---
        self.btn_load_sim = QPushButton("Load Simulation Results")
        self.btn_load_sim.setStyleSheet("""
            QPushButton { background-color: #7030a0; color: white; font-weight: bold; padding: 10px; font-size: 11pt; }
            QPushButton:hover { background-color: #5c2682; }
        """)
        self.btn_load_sim.clicked.connect(self.load_simulation_dialog)
        left_layout.addWidget(self.btn_load_sim)

        # Separator
        line_top = QWidget(); line_top.setFixedHeight(2); line_top.setStyleSheet("background-color: #a0a0a0;")
        left_layout.addWidget(line_top)

        # --- SOURCE PROJECT ---
        group_load = QGroupBox("1. Source Project")
        vbox_load = QVBoxLayout()
        
        hbox_file = QHBoxLayout()
        self.lbl_filename = QLineEdit()
        self.lbl_filename.setPlaceholderText("No project loaded...")
        self.lbl_filename.setReadOnly(True)
        hbox_file.addWidget(self.lbl_filename)
        
        self.btn_load = QPushButton("Load Project")
        self.btn_load.clicked.connect(self.load_project_dialog)
        hbox_file.addWidget(self.btn_load)
        
        vbox_load.addLayout(hbox_file)
        group_load.setLayout(vbox_load)
        left_layout.addWidget(group_load)

        # --- PARAMETERS ---
        group_params = QGroupBox("2. Simulation Parameters")
        form = QFormLayout()

        # Scaling Threshold (0.0 - 1.0)
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.0, 1.0)
        self.spin_threshold.setSingleStep(0.01)
        self.spin_threshold.setValue(0.75)
        form.addRow("Scaling Threshold:", self.spin_threshold)

        # Matrix Jitter (Float)
        self.spin_jitter = QDoubleSpinBox()
        self.spin_jitter.setRange(0.0, 100.0)
        self.spin_jitter.setSingleStep(0.01)
        self.spin_jitter.setValue(0.30)
        form.addRow("Matrix Jitter:", self.spin_jitter)
        
        # Asymmetry Factor (Float)
        self.spin_asym = QDoubleSpinBox()
        self.spin_asym.setRange(0.0, 100.0)
        self.spin_asym.setSingleStep(0.01)
        self.spin_asym.setValue(1.5)
        form.addRow("Asymmetry Factor:", self.spin_asym)

        # Number of Points (Int)
        self.spin_points = QSpinBox()
        self.spin_points.setRange(10, 1000000)
        self.spin_points.setValue(200000)
        form.addRow("Number of Points:", self.spin_points)

        # Scaling Hist Bins (Int)
        self.spin_bins = QSpinBox()
        self.spin_bins.setRange(5, 1001)
        self.spin_bins.setValue(201)
        form.addRow("Histogram Bins:", self.spin_bins)

        # Diameter Cut Value (Float)
        self.spin_cut = QDoubleSpinBox()
        self.spin_cut.setRange(0.0, 100.0)
        self.spin_cut.setValue(2.0)
        form.addRow("Diameter Cut Value [mm]:", self.spin_cut)

        group_params.setLayout(form)
        left_layout.addWidget(group_params)

        # --- EXECUTE SIMULATION ---
        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.clicked.connect(self.run_simulation)
        left_layout.addWidget(self.btn_run)
        
        # --- PLOT SETTINGS ---
        group_plot = QGroupBox("3. Plot Settings")
        vbox_plot = QVBoxLayout()

        # Helper to create rows: Label | Input | Default Button
        def create_axis_row(label, default_key):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(-1000000.0, 1000000.0) # Allow wide range
            spin.setSingleStep(0.01)
            row.addWidget(spin)
            
            btn = QPushButton("Default")
            btn.setFixedWidth(60)
            # Use lambda to pass the specific key (e.g. 'x_min')
            btn.clicked.connect(lambda: self.set_axis_default(default_key))
            row.addWidget(btn)
            return row, spin

        # X-Min
        row_xmin, self.spin_xmin = create_axis_row("X Min:", "x_min")
        vbox_plot.addLayout(row_xmin)
        # X-Max
        row_xmax, self.spin_xmax = create_axis_row("X Max:", "x_max")
        vbox_plot.addLayout(row_xmax)
        # Y-Min
        row_ymin, self.spin_ymin = create_axis_row("Y Min:", "y_min")
        vbox_plot.addLayout(row_ymin)
        # Y-Max
        row_ymax, self.spin_ymax = create_axis_row("Y Max:", "y_max")
        vbox_plot.addLayout(row_ymax)

        # Update Button
        self.btn_update_plot = QPushButton("Update Plot Axes")
        self.btn_update_plot.clicked.connect(self.apply_axis_limits)
        vbox_plot.addWidget(self.btn_update_plot)

        group_plot.setLayout(vbox_plot)
        left_layout.addWidget(group_plot)

        # Spacer to push Save button to bottom
        left_layout.addStretch()

        # --- SAVE RESULTS ---
        line_bot = QWidget(); line_bot.setFixedHeight(2); line_bot.setStyleSheet("background-color: #a0a0a0;")
        left_layout.addWidget(line_bot)

        self.btn_save_sim = QPushButton("Save Simulation Results")
        self.btn_save_sim.setStyleSheet("""
            QPushButton { background-color: #7030a0; color: white; font-weight: bold; padding: 10px; font-size: 11pt; }
            QPushButton:hover { background-color: #5c2682; }
        """)
        self.btn_save_sim.clicked.connect(self.save_simulation_dialog)
        left_layout.addWidget(self.btn_save_sim)

        # ==========================
        # RIGHT PANEL: VISUALS
        # ==========================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        v_splitter = QSplitter(Qt.Vertical)

        # Single Tab
        self.tabs = QTabWidget()
        self.plot_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.plot_canvas, "Scaling Analysis")
        v_splitter.addWidget(self.tabs)

        # Log
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container); log_layout.setContentsMargins(0,0,0,0)
        lbl_log = QLabel("System Log:"); lbl_log.setStyleSheet("font-weight: bold; margin-top: 5px;")
        log_layout.addWidget(lbl_log)
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        v_splitter.addWidget(log_container)

        v_splitter.setSizes([650, 200])
        right_layout.addWidget(v_splitter)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 930])

        main_layout.addWidget(splitter)
    
    def load_project_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Source Project", "", "JSON Files (*.json)", options=options)
        if file_name:
            success = self.controller.load_source_project(file_name)
            if success:
                self.lbl_filename.setText(os.path.basename(file_name))
                print(f"Loaded source project: {file_name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load project file.")
    
    # ==========================
    # LOGIC HANDLERS: THREADED
    # ==========================
    def run_simulation(self):
        # Check prerequisites
        if self.controller.sim_data.source_project is None:
            QMessageBox.warning(self, "Missing Data", "Please load a Source Project (Module 1) first.")
            return

        # Gather Inputs
        ui_inputs = {
            "scaling_threshold": self.spin_threshold.value(),
            "matrix_jitter_value": self.spin_jitter.value(),
            "matrix_asym_factor": self.spin_asym.value(),
            "number_of_points": self.spin_points.value(),
            "scaling_hist_bins": self.spin_bins.value(),
            "diameter_cut_value": self.spin_cut.value()
        }

        # Setup Thread
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Running... (See Log)")
        
        self.worker_thread = QThread()
        self.worker = SimulationWorker(self.controller, ui_inputs)
        
        self.worker.moveToThread(self.worker_thread)
        
        # Connect Signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.result_ready.connect(self.handle_results) # <--- New handler
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.on_simulation_finished)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        # Start
        self.worker_thread.start()

    def handle_results(self, results):
        """Called when the worker successfully returns data."""
        self.update_plot(results)
        print("Simulation completed successfully.")

    def on_simulation_finished(self):
        """Cleanup after thread ends."""
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run Simulation")

    def on_worker_error(self, err_msg):
        """Called if the worker crashes."""
        QMessageBox.critical(self, "Simulation Error", f"An error occurred:\n{err_msg}")

    # ==========================
    # PLOTTING & SAVING
    # ==========================
    def set_axis_default(self, key):
        """
        Triggered by small 'Default' buttons.
        Sets the internal limit to None (Auto) and refreshing plot.
        """
        self.custom_limits[key] = None
        self.update_plot(self.controller.sim_data.results)

    def apply_axis_limits(self):
        """
        Triggered by 'Update Plot Axes' button.
        Reads values from SpinBoxes and applies them.
        """
        self.custom_limits["x_min"] = self.spin_xmin.value()
        self.custom_limits["x_max"] = self.spin_xmax.value()
        self.custom_limits["y_min"] = self.spin_ymin.value()
        self.custom_limits["y_max"] = self.spin_ymax.value()
        
        self.update_plot(self.controller.sim_data.results)
    
    def update_plot(self, results):
        plot_data = results.get("plot_data")
        if not plot_data: return

        # Get the list of curves (default to empty list if missing)
        curves = plot_data.get("curves", [])
        
        ax = self.plot_canvas.axes
        ax.cla()
        
        # Loop through and plot each line
        for curve in curves:
            x = curve['x']
            y = curve['y']
            lbl = curve.get('label', 'Data')
            
            # Plot
            ax.plot(x, y, linewidth=2, label=lbl)
            
        # Set Labels (Shared for all lines)
        ax.set_xlabel(plot_data.get('xlabel', 'X'))
        ax.set_ylabel(plot_data.get('ylabel', 'Y'))
        
        ax.set_title("Surface Scaling Simulation")
        
        ax.set_xlim(left=self.custom_limits["x_min"], right=self.custom_limits["x_max"])
        ax.set_ylim(bottom=self.custom_limits["y_min"], top=self.custom_limits["y_max"])
        
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Add Legend to distinguish the lines
        # ax.legend()
        
        self.plot_canvas.draw()
        
        # Sync SpinBoxes to plot limits
        current_xlim = ax.get_xlim()
        current_ylim = ax.get_ylim()
        
        # Use blockSignals to prevent loop if valueChanged connected
        self.spin_xmin.blockSignals(True); self.spin_xmin.setValue(current_xlim[0]); self.spin_xmin.blockSignals(False)
        self.spin_xmax.blockSignals(True); self.spin_xmax.setValue(current_xlim[1]); self.spin_xmax.blockSignals(False)
        self.spin_ymin.blockSignals(True); self.spin_ymin.setValue(current_ylim[0]); self.spin_ymin.blockSignals(False)
        self.spin_ymax.blockSignals(True); self.spin_ymax.setValue(current_ylim[1]); self.spin_ymax.blockSignals(False)
    
    def load_simulation_dialog(self):
        """
        Loads a previously saved simulation result.
        """
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Simulation", "", "JSON Files (*.json)", options=options)
        
        if file_name:
            success = self.controller.load_simulation(file_name)
            if success:
                self.populate_ui_from_data()
                self.update_plot(self.controller.sim_data.results)
                
                # Check if the source project was successfully re-linked
                if self.controller.sim_data.source_project:
                    # Display the simple filename
                    src_name = self.controller.sim_data.source_filename
                    self.lbl_filename.setText(src_name)
                    print(f"Simulation loaded. Source project '{src_name}' linked.")
                else:
                    self.lbl_filename.setText("Source not found")
                    print("Simulation loaded, but source project is missing.")
                
                QMessageBox.information(self, "Success", "Simulation results loaded.")
            else:
                QMessageBox.critical(self, "Error", "Failed to load simulation file.")

    def populate_ui_from_data(self):
        """
        Sets the spinboxes based on the loaded data.
        """
        inputs = self.controller.sim_data.inputs
        
        self.spin_threshold.setValue(inputs.get("scaling_threshold", 0.5))
        self.spin_jitter.setValue(inputs.get("matrix_jitter_value", 0.1))
        self.spin_asym.setValue(inputs.get("matrix_asym_factor", 1.0))
        self.spin_points.setValue(inputs.get("number_of_points", 1000))
        self.spin_bins.setValue(inputs.get("scaling_hist_bins", 50))
        self.spin_cut.setValue(inputs.get("diameter_cut_value", 5.0))

    def save_simulation_dialog(self):
        if self.controller.sim_data.results is None:
            QMessageBox.warning(self, "No Results", "Run the simulation first.")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Results", "", "JSON Files (*.json)", options=options)
        
        if file_name:
            if not file_name.endswith('.json'): file_name += '.json'
            try:
                self.controller.save_simulation(file_name)
                QMessageBox.information(self, "Success", f"Saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def closeEvent(self, event):
        if self.launcher:
            self.launcher.show()
        event.accept()