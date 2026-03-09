# ui/window_generator.py
import sys
import os
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QComboBox, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QTabWidget, QMessageBox, QDoubleSpinBox, 
    QLineEdit, QInputDialog, QSpinBox, QFormLayout, QFileDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread

# --- Custom Module Imports ---
from logic.controller_generator import GeneratorController
from ui.logger import LogWidget
from ui.plot_canvas import MplCanvas
from ui.worker import Module2Worker
from ui.project_data import ProjectData 

class GeneratorWindow(QMainWindow):
    def __init__(self, launcher=None):
        super().__init__()
        self.launcher = launcher
        self.setWindowTitle("DOME - Generator Module")
        self.resize(1280, 850)
        
        # Icon setup
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        app_icon = QIcon(resource_path("assets/icon_blue_gray.svg"))
        self.setWindowIcon(app_icon)

        # Initialize Controller
        self.controller = GeneratorController()
        
        # Data Paths
        self.std_json_path = os.path.join("data", "standard_curves.json")
        self.cust_json_path = os.path.join("data", "custom_curves.json")
        self.ensure_json_files()

        # UI Layout
        self.init_ui()

        # Load Data
        self.load_grading_curves()
        
        # Initialize with Example Data
        self.fill_example_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT PANEL ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Project management buttons
        hbox_proj = QHBoxLayout()
        
        self.btn_load_proj = QPushButton("Load Project")
        self.btn_load_proj.clicked.connect(self.load_project_dialog)
        hbox_proj.addWidget(self.btn_load_proj)
        
        self.btn_fill_ex = QPushButton("Fill Example Data")
        self.btn_fill_ex.clicked.connect(self.fill_example_data)
        hbox_proj.addWidget(self.btn_fill_ex)
        
        left_layout.addLayout(hbox_proj)
        
        # Separator
        line_top = QWidget(); line_top.setFixedHeight(1); line_top.setStyleSheet("background-color: #a0a0a0;")
        left_layout.addWidget(line_top)

        # Modules
        self.init_module_1_ui(left_layout)
        self.init_module_2_ui(left_layout)
        self.init_module_3_ui(left_layout)
        
        left_layout.addStretch() 
        
        # Save Button
        line_bot = QWidget(); line_bot.setFixedHeight(2); line_bot.setStyleSheet("background-color: #a0a0a0;")
        left_layout.addWidget(line_bot)

        self.btn_save_project = QPushButton("Save Project Data")
        self.btn_save_project.setStyleSheet("""
            QPushButton { background-color: #0078d4; color: white; font-weight: bold; padding: 10px; font-size: 11pt; }
            QPushButton:hover { background-color: #0063b1; }
        """)
        self.btn_save_project.clicked.connect(self.save_project_dialog)
        left_layout.addWidget(self.btn_save_project)

        # --- RIGHT PANEL ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.tabs = QTabWidget()
        
        self.plot_grading = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.plot_grading, "1. Grading Curve Analysis")
        
        self.plot_structure = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.plot_structure, "2. Mesostructure Minimization")
        
        self.sub_tabs_mod3 = QTabWidget()
        self.tabs.addTab(self.sub_tabs_mod3, "3. Calculated Parameters")

        right_layout.addWidget(self.tabs, stretch=2)

        lbl_log = QLabel("System Log:")
        lbl_log.setStyleSheet("font-weight: bold; margin-top: 5px;")
        right_layout.addWidget(lbl_log)
        
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget, stretch=1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([420, 860])

        main_layout.addWidget(splitter)

    # =========================================
    # PROJECT DATA HANDLERS
    # =========================================
    def fill_example_data(self):
        """Reset internal data to Example and update UI."""
        self.controller.project_data = ProjectData.get_example_data()
        self.populate_ui_from_data()
        print("Example data loaded.")

    def load_project_dialog(self):
        """Open file dialog and load JSON."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_name:
            success = self.controller.project_data.load_from_json(file_name)
            if success:
                self.populate_ui_from_data()
                self.restore_plots_from_data()
                QMessageBox.information(self, "Success", "Project loaded successfully.")
                print("Project data loaded.")
            else:
                QMessageBox.critical(self, "Error", "Failed to load project file.")

    def save_project_dialog(self):
        """Open file dialog and save JSON."""
        self.capture_current_ui_to_data()
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)", options=options)
        
        if file_name:
            if not file_name.endswith('.json'): file_name += '.json'
            try:
                self.controller.project_data.save_to_json(file_name)
                QMessageBox.information(self, "Success", f"Project saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def populate_ui_from_data(self):
        """Maps values from self.controller.project_data TO the Widgets."""
        inputs = self.controller.project_data.inputs
        
        self.block_ui_signals(True)

        # --- MODULE 1 ---
        m1 = inputs["module_1"]
        self.spin_dim_x.setValue(m1["container_dims"][0])
        self.spin_dim_y.setValue(m1["container_dims"][1])
        self.spin_dim_z.setValue(m1["container_dims"][2])
        self.spin_vol_frac.setValue(m1["volume_fraction"])
        self.line_diameter_params.setText(m1.get("diameter_params", ""))
        
        # Handle Curve Name
        curve_name = m1.get("curve_name", "")
        if curve_name:
            # Check if name exists in standard/custom lists
            idx = self.combo_curves.findText(curve_name)
            
            if idx == -1:
                # If name is "Unsaved Curve Data" (or a custom curve that was deleted from json)
                # It will be added as a temporary item to the dropdown
                self.combo_curves.addItem(curve_name)
                # Set index to this new last item
                self.combo_curves.setCurrentIndex(self.combo_curves.count() - 1)
            else:
                # Standard existing curve
                self.combo_curves.setCurrentIndex(idx)

        # Populate the Table
        saved_curve_data = m1.get("curve_data")
        
        if saved_curve_data and len(saved_curve_data) > 0:
            # Load specific numbers from Project File
            self.table.setRowCount(0)
            for row, (size, rate) in enumerate(saved_curve_data):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(size)))
                self.table.setItem(row, 1, QTableWidgetItem(str(rate)))
        else:
            # Fallback: Load from Name if no specific data saved
            self.block_ui_signals(False)
            if curve_name:
                self.on_curve_selected(curve_name)
            self.block_ui_signals(True)

        # --- MODULE 2 ---
        m2 = inputs["module_2"]
        self.spin_bins.setValue(m2["n_bins"])
        self.spin_accuracy.setValue(m2["accuracy"])
        self.spin_edge.setValue(m2["edge_percentage"])
        self.spin_alpha_min.setValue(m2["alpha_bounds"][0])
        self.spin_alpha_max.setValue(m2["alpha_bounds"][1])

        # --- MODULE 3 ---
        m3 = inputs["module_3"]
        self.spin_rho_agg.setValue(m3["rho_agg"])
        self.spin_rho_mat.setValue(m3["rho_mat"])

        self.block_ui_signals(False)

    def capture_current_ui_to_data(self):
        """Scrapes current UI values and puts them into ProjectData inputs."""
        
        # --- MODULE 1 ---
        current_table_data = self.get_table_data()
        current_combo_name = self.combo_curves.currentText()
        
        # Check if the table data matches the named curve's definition
        # Assumed that the name is correct initially. If there is a mismatch, the name is changed
        final_save_name = current_combo_name
        
        # Look up the original data for the selected name
        original_data = self.curve_data.get(current_combo_name)
        
        # Compare
        # If current_table_data is None (empty), check is skipped
        if current_table_data and original_data:
            if current_table_data != original_data:
                # Mismatch: Table was modified but didn't get saved as a custom curve
                final_save_name = "Unsaved Curve Data"

        # Update Project Data
        self.controller.project_data.inputs["module_1"].update({
            "container_dims": (self.spin_dim_x.value(), self.spin_dim_y.value(), self.spin_dim_z.value()),
            "volume_fraction": self.spin_vol_frac.value(),
            "curve_name": final_save_name,
            "curve_data": current_table_data,
            "diameter_params": self.line_diameter_params.text()
        })

        # --- MODULE 2 ---
        self.controller.project_data.inputs["module_2"].update({
            "n_bins": self.spin_bins.value(),
            "accuracy": self.spin_accuracy.value(),
            "edge_percentage": self.spin_edge.value(),
            "alpha_bounds": (self.spin_alpha_min.value(), self.spin_alpha_max.value())
        })

        # --- MODULE 3 ---
        self.controller.project_data.inputs["module_3"].update({
            "rho_agg": self.spin_rho_agg.value(),
            "rho_mat": self.spin_rho_mat.value()
        })

    def restore_plots_from_data(self):
        """If results exist in loaded data, replot them."""
        # Module 1
        res1 = self.controller.project_data.results.get("module_1")
        if res1:
            self.update_grading_plot(res1)
        
        # Module 2
        res2 = self.controller.project_data.results.get("module_2")
        if res2:
            self.handle_module_2_results(res2)

        # Module 3
        res3 = self.controller.project_data.results.get("module_3")
        if res3:
            self.update_module_3_dynamic_plots(res3)

    def block_ui_signals(self, block):
        self.combo_curves.blockSignals(block)

    # =========================================
    # MODULE 1
    # =========================================
    def init_module_1_ui(self, layout):
        group = QGroupBox("Module 1: Aggregate Generation")
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Container Dimensions [mm]:"))
        
        hbox_dims = QHBoxLayout()
        def config_spin(val):
            sb = QDoubleSpinBox(); sb.setRange(0.0, 10000.0); sb.setValue(val); return sb
        
        hbox_dims.addWidget(QLabel("X:")); self.spin_dim_x = config_spin(150.0); hbox_dims.addWidget(self.spin_dim_x)
        hbox_dims.addSpacing(15)
        hbox_dims.addWidget(QLabel("Y:")); self.spin_dim_y = config_spin(150.0); hbox_dims.addWidget(self.spin_dim_y)
        hbox_dims.addSpacing(15)
        hbox_dims.addWidget(QLabel("Z:")); self.spin_dim_z = config_spin(150.0); hbox_dims.addWidget(self.spin_dim_z)
        vbox.addLayout(hbox_dims)

        hbox_vol = QHBoxLayout()
        hbox_vol.addWidget(QLabel("Target Volume Fraction (0.0 - 1.0):"))
        self.spin_vol_frac = QDoubleSpinBox(); self.spin_vol_frac.setRange(0, 1); self.spin_vol_frac.setSingleStep(0.01); self.spin_vol_frac.setValue(0.67);
        hbox_vol.addWidget(self.spin_vol_frac)
        vbox.addLayout(hbox_vol)

        vbox.addWidget(QLabel("Select Grading Curve:"))
        self.combo_curves = QComboBox(); self.combo_curves.currentTextChanged.connect(self.on_curve_selected); vbox.addWidget(self.combo_curves)

        vbox.addWidget(QLabel("Curve Data (Size [mm] | Passing [%]):"))
        self.table = QTableWidget(); self.table.setColumnCount(2); self.table.setHorizontalHeaderLabels(["Size (mm)", "Passing (%)"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); vbox.addWidget(self.table)

        hbox_btns = QHBoxLayout()
        btn_add = QPushButton("Add Row"); btn_add.clicked.connect(self.add_table_row)
        btn_rem = QPushButton("Remove Row"); btn_rem.clicked.connect(self.remove_table_row)
        hbox_btns.addWidget(btn_add); hbox_btns.addWidget(btn_rem)
        vbox.addLayout(hbox_btns)

        self.btn_save = QPushButton("Save Current Curve"); self.btn_save.clicked.connect(self.save_custom_curve); vbox.addWidget(self.btn_save)
        
        line = QWidget(); line.setFixedHeight(1); line.setStyleSheet("background-color: #cccccc;"); vbox.addWidget(line)

        vbox.addWidget(QLabel("Diameters of Generated Curve (Separated by comma ','):"))
        self.line_diameter_params = QLineEdit(); self.line_diameter_params.setPlaceholderText("e.g. 1.5, 2.0"); self.line_diameter_params.setText("0.125, 0.25, 0.5, 1, 2, 4, 8"); vbox.addWidget(self.line_diameter_params)
        
        self.btn_gen_agg = QPushButton("Generate Aggregates"); self.btn_gen_agg.setStyleSheet("background-color: #d4e3fc; font-weight: bold; padding: 5px;"); self.btn_gen_agg.clicked.connect(self.run_module_1); vbox.addWidget(self.btn_gen_agg)

        group.setLayout(vbox)
        layout.addWidget(group)

    def run_module_1(self):
        data = self.get_table_data()
        if not data:
            QMessageBox.warning(self, "Input Error", "Table is empty or invalid.")
            return

        raw_diameter_text = self.line_diameter_params.text()
        
        input_dict_generation = {
            'target_sizes': [d[0] for d in data], 
            'target_rates': [d[1] for d in data], 
            'volume_fraction': self.spin_vol_frac.value(),
            'container_dims': (self.spin_dim_x.value(), self.spin_dim_y.value(), self.spin_dim_z.value()),
            'diameter_params': raw_diameter_text
        }

        try:
            self.capture_current_ui_to_data()
            actual_curve_data = self.controller.execute_generation(input_dict_generation)
            self.tabs.setCurrentIndex(0)
            self.update_grading_plot(actual_curve_data)
        except Exception as e:
            print(f"Error in Module 1: {e}")

    def update_grading_plot(self, actual_data):
        ax = self.plot_grading.axes
        ax.cla() 
        
        if actual_data:
            target_x = actual_data['gsd_mesh_sizes']
            target_y = actual_data['gsd_passing_rates_export']
            act_x = actual_data['meso_input_mesh_sizes']
            act_y = actual_data['meso_volume']
            
            ax.plot(target_x, target_y, color='k', linestyle='-', marker='', 
                    label='Grain size distribution related to $F_V$', clip_on=False)
            
            ax.step(act_x, act_y, color=(1.0, 0.0, 0.0, 0.3), markerfacecolor=(1.0, 0.0, 0.0, 1.0), markeredgecolor=(1.0, 0.0, 0.0, 1.0),
                    linestyle='--', marker='s', label='Generated aggregates', clip_on=False, where='post')

        ax.set_xlabel("Mesh Size [mm]")
        ax.set_ylabel("Cumulative Volume Fraction [-]")
        ax.set_title("Grading Curve Comparison")
        ax.set_xscale('log') 
        ax.grid(True, which="both", ls="--", alpha=0.5)
        ax.legend()
        self.plot_grading.draw()

    # =========================================
    # MODULE 2
    # =========================================
    def init_module_2_ui(self, layout):
        group = QGroupBox("Module 2: Aggregate Distribution")
        vbox = QVBoxLayout()
        form = QFormLayout()

        self.spin_bins = QSpinBox(); self.spin_bins.setRange(10, 10000); self.spin_bins.setValue(801)
        form.addRow("Number of Bins:", self.spin_bins)

        self.spin_accuracy = QSpinBox(); self.spin_accuracy.setRange(10, 100000); self.spin_accuracy.setValue(201)
        form.addRow("X Range Accuracy:", self.spin_accuracy)
        
        self.spin_edge = QSpinBox(); self.spin_edge.setRange(0, 100); self.spin_edge.setValue(10)
        form.addRow("X Edge Minimization Percentage:", self.spin_edge)

        hbox_alpha = QHBoxLayout()
        hbox_alpha.addWidget(QLabel("Min:")); self.spin_alpha_min = QDoubleSpinBox(); self.spin_alpha_min.setRange(0, 2); self.spin_alpha_min.setSingleStep(0.05); self.spin_alpha_min.setValue(0.65); hbox_alpha.addWidget(self.spin_alpha_min)
        hbox_alpha.addSpacing(15)
        hbox_alpha.addWidget(QLabel("Max:")); self.spin_alpha_max = QDoubleSpinBox(); self.spin_alpha_max.setRange(0, 2); self.spin_alpha_max.setSingleStep(0.05); self.spin_alpha_max.setValue(1.10); hbox_alpha.addWidget(self.spin_alpha_max)
        form.addRow("Alpha Bounds (0.0 - 2.0):", hbox_alpha)

        vbox.addLayout(form)

        self.btn_run_dist = QPushButton("Run Distribution Algorithm")
        self.btn_run_dist.setStyleSheet("background-color: #d4e3fc; font-weight: bold; padding: 5px;")
        self.btn_run_dist.clicked.connect(self.run_module_2_threaded)
        vbox.addWidget(self.btn_run_dist)

        group.setLayout(vbox)
        layout.addWidget(group)

    def run_module_2_threaded(self):
        if self.controller.output_dict is None:
            QMessageBox.warning(self, "Sequence Error", "Please run Module 1 first.")
            return

        alpha_min = self.spin_alpha_min.value()
        alpha_max = self.spin_alpha_max.value()
        if alpha_min >= alpha_max:
            QMessageBox.warning(self, "Input Error", "Alpha Min must be smaller than Alpha Max.")
            return

        self.capture_current_ui_to_data()

        input_dict_distribution = {
            'n_bins': self.spin_bins.value(), 
            'accuracy': self.spin_accuracy.value(), 
            'edge_percentage': self.spin_edge.value(), 
            'alpha_bounds': (alpha_min, alpha_max)
        }

        self.btn_run_dist.setEnabled(False)
        self.btn_run_dist.setText("Running... (See Log)")
        self.tabs.setCurrentIndex(1)

        self.worker_thread = QThread()
        self.worker = Module2Worker(self.controller, input_dict_distribution)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.result_ready.connect(self.handle_module_2_results)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.on_module_2_finished)
        self.worker.error_occurred.connect(self.on_worker_error)
        self.worker_thread.start()

    def handle_module_2_results(self, result):        
        x_range = result['x_range']
        y_main = result['y_main']
        linear_line = result['linear_line']
        ax = self.plot_structure.axes; ax.cla()
        ax.plot(x_range, y_main, 'b'); ax.plot(x_range, linear_line, 'k--')
        ax.set_xlim(0, max(x_range)); ax.set_ylim(0, 100)
        ax.set_xlabel("Sample Length [mm]"); ax.set_ylabel("Cumulative Aggregate Volume [%]"); ax.set_title("Minimization of Aggregate Distribution")
        self.plot_structure.draw()

    def on_module_2_finished(self):
        self.btn_run_dist.setEnabled(True); self.btn_run_dist.setText("Run Distribution Algorithm")
    
    def on_worker_error(self, err_msg):
        QMessageBox.critical(self, "Algorithm Error", f"An error occurred:\n{err_msg}")

    # =========================================
    # MODULE 3
    # =========================================
    def init_module_3_ui(self, layout):
        group = QGroupBox("Module 3: Parameter Calculation")
        vbox = QVBoxLayout()
        form = QFormLayout()

        hbox_agg = QHBoxLayout(); self.spin_rho_agg = QDoubleSpinBox(); self.spin_rho_agg.setRange(0.1, 10); self.spin_rho_agg.setSingleStep(0.01); self.spin_rho_agg.setValue(2.65); hbox_agg.addWidget(self.spin_rho_agg); hbox_agg.addWidget(QLabel("g/cm³")); form.addRow("Aggregate Density:", hbox_agg)
        hbox_mat = QHBoxLayout(); self.spin_rho_mat = QDoubleSpinBox(); self.spin_rho_mat.setRange(0.1, 10); self.spin_rho_mat.setSingleStep(0.01); self.spin_rho_mat.setValue(2.00); hbox_mat.addWidget(self.spin_rho_mat); hbox_mat.addWidget(QLabel("g/cm³")); form.addRow("Matrix Density:", hbox_mat)
        
        vbox.addLayout(form)
        self.btn_run_calc = QPushButton("Calculate Parameters"); self.btn_run_calc.setStyleSheet("background-color: #d4e3fc; font-weight: bold; padding: 5px;"); self.btn_run_calc.clicked.connect(self.run_module_3); vbox.addWidget(self.btn_run_calc)
        group.setLayout(vbox); layout.addWidget(group)
    
    def run_module_3(self):
        if self.controller.output_dict is None:
            QMessageBox.warning(self, "Sequence Error", "Please run Module 2 first.")
            return

        self.capture_current_ui_to_data()

        input_dict_calculation = {
            'rho_agg': self.spin_rho_agg.value(), 
            'rho_mat': self.spin_rho_mat.value()
        }
        
        try:
            results_dict = self.controller.execute_calculation(input_dict_calculation)
            self.tabs.setCurrentIndex(2)
            self.update_module_3_dynamic_plots(results_dict)
        except Exception as e:
            print(f"Error in Module 3: {e}")

    def update_module_3_dynamic_plots(self, results_dict):
        # --- CAPTURE STATE ---
        current_tab_title = None
        # Check if a tab is currently selected
        if self.sub_tabs_mod3.currentIndex() != -1:
            current_tab_title = self.sub_tabs_mod3.tabText(self.sub_tabs_mod3.currentIndex())
    
        # --- REBUILD ---
        self.sub_tabs_mod3.clear()
        for title, data in results_dict.items():
            x = data['x_data']; y = data['y_data']; y_additional = data['y_additional']
            x_lbl = data['x_label']; y_lbl = data['y_label']
            x_lim_min, x_lim_max, y_lim_min, y_lim_max = data['x_y_lims']
            
            canvas = MplCanvas(self, width=5, height=4, dpi=100); ax = canvas.axes
            ax.plot(x, y, 'k', marker='', linestyle='-')
            if len(y_additional) > 0:
                for row in y_additional:
                    ax.plot(x, row, marker='', linestyle='-')
            
            ax.set_title(title); ax.set_xlabel(x_lbl); ax.set_ylabel(y_lbl)
            ax.set_xlim(x_lim_min, x_lim_max); ax.set_ylim(y_lim_min, y_lim_max)
            canvas.draw()
            self.sub_tabs_mod3.addTab(canvas, title)
        
        # --- RESTORE STATE ---
        # If a tab was open before, try to find it in the new list
        if current_tab_title:
            for i in range(self.sub_tabs_mod3.count()):
                if self.sub_tabs_mod3.tabText(i) == current_tab_title:
                    self.sub_tabs_mod3.setCurrentIndex(i)
                    break

    # =========================================
    # DATA & JSON HELPERS
    # =========================================
    def ensure_json_files(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.std_json_path):
            data = {
                "Standard AB8": [[0.063, 0.17], [0.125, 0.36], [0.25, 7.39], [0.5, 18.13], [1, 29.74], [2, 49.11], [4, 81.1], [8, 98.2], [16, 100]], 
                "Fuller Curve": [[0.125, 8], [0.25, 20], [1.0, 45], [4.0, 75], [8.0, 100]]
            }
            with open(self.std_json_path, 'w') as f:
                json.dump(data, f, indent=4)
        
        if not os.path.exists(self.cust_json_path):
            with open(self.cust_json_path, 'w') as f:
                json.dump({}, f)

    def load_grading_curves(self):
        self.curve_data = {}
        if os.path.exists(self.std_json_path):
            with open(self.std_json_path, 'r') as f:
                std = json.load(f)
                for k, v in std.items():
                    self.curve_data[f"[STD] {k}"] = v
        
        if os.path.exists(self.cust_json_path):
            with open(self.cust_json_path, 'r') as f:
                cust = json.load(f)
                for k, v in cust.items():
                    self.curve_data[f"[CUSTOM] {k}"] = v

        self.combo_curves.blockSignals(True)
        self.combo_curves.clear()
        self.combo_curves.addItems(self.curve_data.keys())
        self.combo_curves.blockSignals(False)
        
        if self.combo_curves.count() > 0:
            self.on_curve_selected(self.combo_curves.currentText())

    def on_curve_selected(self, name):
        if not name or name not in self.curve_data: return
        data = self.curve_data[name]
        
        self.table.setRowCount(0)
        for row, (size, rate) in enumerate(data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(size)))
            self.table.setItem(row, 1, QTableWidgetItem(str(rate)))

    def get_table_data(self):
        data = []
        try:
            for r in range(self.table.rowCount()):
                item_size = self.table.item(r, 0)
                item_rate = self.table.item(r, 1)
                if item_size and item_rate:
                    s = float(item_size.text())
                    ra = float(item_rate.text())
                    data.append([s, ra])
            data.sort(key=lambda x: x[0]) 
            return data
        except ValueError:
            return None

    def add_table_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_table_row(self):
        if self.table.rowCount() > 0:
            self.table.removeRow(self.table.rowCount() - 1)

    def save_custom_curve(self):
        new_curve_data = self.get_table_data()
        if not new_curve_data:
            QMessageBox.warning(self, "Data Error", "Table is empty or invalid.")
            return

        try:
            with open(self.std_json_path, 'r') as f:
                std_data = json.load(f)
            with open(self.cust_json_path, 'r') as f:
                cust_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Could not read JSON files: {e}")
            return

        for name, data in std_data.items():
            if data == new_curve_data:
                QMessageBox.warning(self, "Duplicate Content", f"Exists in Standard Curves as:\n'{name}'")
                return 

        for name, data in cust_data.items():
            if data == new_curve_data:
                QMessageBox.warning(self, "Duplicate Content", f"Exists in Custom Curves as:\n'{name}'")
                return 

        name, ok = QInputDialog.getText(self, "Save Custom Curve", "Enter a name for this curve:")
        if not ok or not name.strip(): return
        name = name.strip()

        if name in std_data:
            QMessageBox.warning(self, "Name Conflict", f"'{name}' is a Standard Curve.")
            return

        if name in cust_data:
            reply = QMessageBox.question(self, "Overwrite?", f"Overwrite '{name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No: return

        try:
            cust_data[name] = new_curve_data
            with open(self.cust_json_path, 'w') as f:
                json.dump(cust_data, f, indent=4)
            
            self.load_grading_curves() 
            idx = self.combo_curves.findText(f"[CUSTOM] {name}")
            if idx >= 0: self.combo_curves.setCurrentIndex(idx)
            QMessageBox.information(self, "Success", f"Curve '{name}' saved.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"{e}")
    
    def closeEvent(self, event):
        """When this window closes, show the launcher again."""
        if self.launcher:
            self.launcher.show()
        event.accept()
