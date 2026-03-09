# ui/window_comparator.py
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QPushButton, QListWidget, QFileDialog, 
    QMessageBox, QTabWidget, QListWidgetItem, QCheckBox, 
    QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from logic.controller_comparator import ComparatorController
from ui.plot_canvas import MplCanvas
from ui.logger import LogWidget

class ComparatorWindow(QMainWindow):
    """
    Main window for the Mesostructure Comparator Module.
    Allows loading multiple project files (.json), comparing their results
    in overlay plots, and filtering specific sub-curves (additional analysis).
    """

    def __init__(self, launcher=None):
        """
        Initialize window, setup controller, and build UI.
        
        Args:
            launcher (QMainWindow): Reference to the main Launcher window 
                                    to re-show it upon closing this window.
        """
        super().__init__()
        self.launcher = launcher
        self.setWindowTitle("DOME - Comparator Module")
        self.resize(1280, 850)
        
        # Locate assets/icon.svg
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        self.setWindowIcon(QIcon(resource_path("assets/icon_green_gray.svg")))
        
        # Initialize Logic Controller for this module
        self.controller = ComparatorController()
        
        # Flag to track if user is overriding the auto-calculated limit
        self.manual_axis_mode = False
        
        # Build Graphical User Interface
        self.init_ui()

    def init_ui(self):
        """
        Constructs layout:
        - Left Panel: Project Management & Filter Controls
        - Right Panel: Visualization Tabs (Main vs Additional) & System Log
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Main Splitter to separate Controls (Left) from Visuals (Right)
        splitter = QSplitter(Qt.Horizontal)

        # ==========================================================
        # LEFT PANEL: CONTROLS
        # ==========================================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # --- Project List ---
        group_proj = QGroupBox("1. Loaded Projects")
        vbox_proj = QVBoxLayout()
        
        # List widget to display currently loaded filenames
        self.list_projects = QListWidget()
        vbox_proj.addWidget(self.list_projects)
        
        # Button to load JSON files
        self.btn_add = QPushButton("Add Projects...")
        self.btn_add.clicked.connect(self.add_projects_dialog)
        vbox_proj.addWidget(self.btn_add)
        
        # Buttons to remove specific or all projects
        hbox_rem = QHBoxLayout()
        self.btn_rem = QPushButton("Remove Selected")
        self.btn_rem.clicked.connect(self.remove_selected_project)
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_all_projects)
        hbox_rem.addWidget(self.btn_rem)
        hbox_rem.addWidget(self.btn_clear)
        
        vbox_proj.addLayout(hbox_rem)
        group_proj.setLayout(vbox_proj)
        left_layout.addWidget(group_proj)
        
        # --- Filter List (for additional analysis) ---
        group_filter = QGroupBox("2. Curve Filter (Sub-Plots)")
        vbox_filter = QVBoxLayout()
        
        # Checkable list widget to show all available 'Additional Curves'
        self.list_filters = QListWidget()
        vbox_filter.addWidget(self.list_filters)
        
        # Buttons to bulk select/deselect filters
        hbox_filter_btns = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(lambda: self.set_filter_state(True))
        btn_none = QPushButton("Select None")
        btn_none.clicked.connect(lambda: self.set_filter_state(False))
        hbox_filter_btns.addWidget(btn_all)
        hbox_filter_btns.addWidget(btn_none)
        vbox_filter.addLayout(hbox_filter_btns)
        
        self.btn_refresh = QPushButton("Refresh Comparison Plots")
        # self.btn_refresh.setStyleSheet("font-weight: bold; padding: 10px; font-size: 11pt;")
        self.btn_refresh.clicked.connect(self.update_plots)
        vbox_filter.addWidget(self.btn_refresh)
        
        group_filter.setLayout(vbox_filter)
        left_layout.addWidget(group_filter)

        # --- lot Settings ---
        group_settings = QGroupBox("3. Plot Settings")
        vbox_settings = QVBoxLayout()
        
        # Row 1: Label | Input | Default Button
        hbox_xaxis = QHBoxLayout()
        hbox_xaxis.addWidget(QLabel("Max X-Axis [mm]:"))
        
        self.spin_xmax = QSpinBox()
        self.spin_xmax.setRange(1, 999999)
        self.spin_xmax.setValue(100) 
        hbox_xaxis.addWidget(self.spin_xmax)
        
        # "Set Default" button next to input
        self.btn_reset_axis = QPushButton("Default")
        self.btn_reset_axis.setToolTip("Reset to maximum value from all loaded projects")
        self.btn_reset_axis.clicked.connect(self.reset_auto_axis)
        hbox_xaxis.addWidget(self.btn_reset_axis)
        
        vbox_settings.addLayout(hbox_xaxis)
        
        # Row 2: "Update" button below
        self.btn_apply_axis = QPushButton("Update Plot Axis")
        self.btn_apply_axis.clicked.connect(self.apply_manual_axis)
        vbox_settings.addWidget(self.btn_apply_axis)
        
        group_settings.setLayout(vbox_settings)
        left_layout.addWidget(group_settings)

        # ==========================================================
        # RIGHT PANEL: VISUALIZATION
        # ==========================================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Vertical Splitter for Tabs (Top) and Log (Bottom)
        v_splitter = QSplitter(Qt.Vertical)

        # --- Tabs Area ---
        self.main_tabs = QTabWidget()
        
        # Compare Main Results (e.g. Area, Perimeter totals)
        self.mod3_subtabs = QTabWidget()
        self.main_tabs.addTab(self.mod3_subtabs, "Main Results")
        
        # Compare Additional Results (e.g. specific curves inside a category)
        self.mod3_add_subtabs = QTabWidget()
        self.main_tabs.addTab(self.mod3_add_subtabs, "Additional Analysis")
        
        v_splitter.addWidget(self.main_tabs)

        # --- Log Area ---
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_log = QLabel("System Log:")
        lbl_log.setStyleSheet("font-weight: bold; margin-top: 5px;")
        log_layout.addWidget(lbl_log)
        
        self.log_widget = LogWidget()
        log_layout.addWidget(self.log_widget)
        
        v_splitter.addWidget(log_container)
        
        # Set Initial Sizes: [Top Height, Bottom Height]
        v_splitter.setSizes([650, 200])

        right_layout.addWidget(v_splitter)

        # Add panels to the main horizontal splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 930])

        main_layout.addWidget(splitter)

    # ==========================================================
    # LOGIC HANDLERS: PROJECT MANAGEMENT
    # ==========================================================
    def calculate_global_max_x(self):
        """
        Scans ALL loaded data (Main and Additional) to find the 
        absolute maximum X value defined in the saved limits.
        """
        global_max = 0.0
        
        # Check Main Data
        main_data = self.controller.get_module_3_comparison_data()
        for curves in main_data.values():
            for curve in curves:
                # curve['x_y_lims'] = [xmin, xmax, ymin, ymax]
                x_max = curve['x_y_lims'][1]
                if x_max > global_max:
                    global_max = x_max

        # Check Additional Data
        add_data = self.controller.get_module_3_additional_data()
        for curves in add_data.values():
            for curve in curves:
                x_max = curve['x_y_lims'][1]
                if x_max > global_max:
                    global_max = x_max
                    
        return int(global_max) if global_max > 0 else 100

    def apply_manual_axis(self):
        """User clicked 'Set' button."""
        self.manual_axis_mode = True
        print(f"X-Axis limit set manually to {self.spin_xmax.value()}")
        self.update_plots()

    def reset_auto_axis(self):
        """User clicked 'Set Default' button."""
        self.manual_axis_mode = False
        print("X-Axis limit reset to automatic.")
        self.update_plots()
    
    def add_projects_dialog(self):
        """
        Opens a File Dialog to select multiple JSON project files.
        Loads them via controller and updates the UI lists.
        """
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "Load Projects", "", "JSON Files (*.json);;All Files (*)", options=options
        )
        
        if files:
            # Unpack the two lists
            loaded_names, failed_names = self.controller.load_projects(files)
            
            # Add successes to the list
            self.list_projects.addItems(loaded_names)
            
            # Show Popup for failures
            if failed_names:
                msg_text = "The following files could not be loaded:\n(Wrong file type or corrupt data)\n\n"
                msg_text += "\n".join(failed_names)
                QMessageBox.warning(self, "Load Warning", msg_text)

            # Update UI elements if anything was successfully loaded
            if loaded_names:
                self.populate_filter_list()
                self.manual_axis_mode = False 
                self.update_plots()

    def remove_selected_project(self):
        """
        Removes the currently selected project(s) from memory and the UI list.
        """
        selected_items = self.list_projects.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            name = item.text()
            self.controller.remove_project(name)
            self.list_projects.takeItem(self.list_projects.row(item))
            
        # Refresh filters and plots to reflect removal
        self.populate_filter_list()
        self.update_plots()

    def clear_all_projects(self):
        """
        Removes ALL projects and clears all plots.
        """
        self.controller.clear_all()
        self.list_projects.clear()
        self.list_filters.clear()
        self.mod3_subtabs.clear()
        self.mod3_add_subtabs.clear()
        print("All projects cleared.") 

    # ==========================================================
    # LOGIC HANDLERS: FILTERING
    # ==========================================================
    def populate_filter_list(self):
        """
        Scans all loaded data for 'y_additional' curves.
        Populates the 'Curve Filter' list with checkable items.
        Preserves the check-state of existing items where possible.
        """
        # Fetch available additional data structure
        all_data = self.controller.get_module_3_additional_data()
        
        # Collect unique labels
        unique_labels = set()
        for curves in all_data.values():
            for curve in curves:
                unique_labels.add(curve['label'])
        
        # Snapshot current check states to preserve user selection
        checked_labels = set()
        for i in range(self.list_filters.count()):
            item = self.list_filters.item(i)
            if item.checkState() == Qt.Checked:
                checked_labels.add(item.text())

        # Rebuild the list
        self.list_filters.clear()
        sorted_labels = sorted(list(unique_labels))
        
        for label in sorted_labels:
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Default to Checked if new, or preserve previous Checked state
            if label in checked_labels or len(checked_labels) == 0:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
                
            self.list_filters.addItem(item)

    def set_filter_state(self, checked):
        """Helper to Check All or Uncheck All in the filter list."""
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.list_filters.count()):
            self.list_filters.item(i).setCheckState(state)

    def get_allowed_curves(self):
        """Returns a set of labels that are currently checked in the filter list."""
        allowed = set()
        for i in range(self.list_filters.count()):
            item = self.list_filters.item(i)
            if item.checkState() == Qt.Checked:
                allowed.add(item.text())
        return allowed

    # ==========================================================
    # LOGIC HANDLERS: PLOTTING
    # ==========================================================
    def update_plots(self):
        """
        Master refresh function. Clears and replots both
        Main Results and Additional Analysis tabs.
        """
        print("Updating comparison plots...")
        # Handle Axis Logic
        if not self.manual_axis_mode:
            # Calculate the auto-max
            auto_max = self.calculate_global_max_x()
            # Update spinbox silently (block signals if you had connected valueChanged)
            self.spin_xmax.setValue(auto_max)
            
        self.update_main_plots()
        self.update_additional_plots()
        print("All plots updated.")

    def update_main_plots(self):
        """
        Handles plotting for Tab 1 (Main Results).
        Calculates global axis limits per plot type to ensure all curves fit.
        """
        # --- CAPTURE STATE ---
        current_tab_title = None
        if self.mod3_subtabs.currentIndex() != -1:
            current_tab_title = self.mod3_subtabs.tabText(self.mod3_subtabs.currentIndex())
    
        # --- REBUILD ---
        self.mod3_subtabs.clear()
        comp_data = self.controller.get_module_3_comparison_data()
        if not comp_data:
            return

        # Get the X-Limit to use (from SpinBox)
        user_x_max = self.spin_xmax.value()

        for title, curves_list in comp_data.items():
            type_x_min = None; type_y_min = None; type_y_max = None

            canvas = MplCanvas(self, width=5, height=4, dpi=100)
            ax = canvas.axes
            
            for curve in curves_list:
                ax.plot(curve['x'], curve['y'], linewidth=2, label=curve['label'])
                ax.set_xlabel(curve['xlabel'])
                ax.set_ylabel(curve['ylabel'])
                
                # Update limits for Y and X-Min
                c_x_min, _, c_y_min, c_y_max = curve['x_y_lims']
                if type_x_min is None or c_x_min < type_x_min: type_x_min = c_x_min
                if type_y_min is None or c_y_min < type_y_min: type_y_min = c_y_min
                if type_y_max is None or c_y_max > type_y_max: type_y_max = c_y_max

            if type_x_min is not None:
                # Apply user defined max x
                ax.set_xlim(type_x_min, user_x_max)
                ax.set_ylim(type_y_min, type_y_max)
            
            ax.set_title(f"Main: {title}")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend()
            canvas.draw()
            self.mod3_subtabs.addTab(canvas, title)
        
        # --- RESTORE STATE ---
        if current_tab_title:
            for i in range(self.mod3_subtabs.count()):
                if self.mod3_subtabs.tabText(i) == current_tab_title:
                    self.mod3_subtabs.setCurrentIndex(i)
                    break

    def update_additional_plots(self):
        """
        Handles plotting for Tab 2 (Additional Analysis).
        Filters visible curves based on the Checkbox List.
        """
        # --- CAPTURE STATE ---
        current_tab_title = None
        if self.mod3_add_subtabs.currentIndex() != -1:
            current_tab_title = self.mod3_add_subtabs.tabText(self.mod3_add_subtabs.currentIndex())
    
        # --- REBUILD ---
        self.mod3_add_subtabs.clear()
        all_add_data = self.controller.get_module_3_additional_data()
        if not all_add_data:
            return
        allowed_labels = self.get_allowed_curves()
        
        # Get the X-Limit to use (from SpinBox)
        user_x_max = self.spin_xmax.value()

        for title, curves_list in all_add_data.items():
            visible_curves = [c for c in curves_list if c['label'] in allowed_labels]
            if not visible_curves: continue 

            type_x_min = None; type_y_min = None; type_y_max = None

            canvas = MplCanvas(self, width=5, height=4, dpi=100)
            ax = canvas.axes
            
            for curve in visible_curves:
                ax.plot(curve['x'], curve['y'], linewidth=1.5, label=curve['label'])
                ax.set_xlabel(curve['xlabel'])
                ax.set_ylabel(curve['ylabel'])

                c_x_min, _, c_y_min, c_y_max = curve['x_y_lims']
                if type_x_min is None or c_x_min < type_x_min: type_x_min = c_x_min
                if type_y_min is None or c_y_min < type_y_min: type_y_min = c_y_min
                if type_y_max is None or c_y_max > type_y_max: type_y_max = c_y_max

            if type_x_min is not None:
                # Apply user defined max x
                ax.set_xlim(type_x_min, user_x_max)
                ax.set_ylim(type_y_min, type_y_max)
            
            ax.set_title(f"Additional: {title}")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(fontsize='small') 
            canvas.draw()
            self.mod3_add_subtabs.addTab(canvas, title)
        
        # --- RESTORE STATE ---
        if current_tab_title:
            for i in range(self.mod3_add_subtabs.count()):
                if self.mod3_add_subtabs.tabText(i) == current_tab_title:
                    self.mod3_add_subtabs.setCurrentIndex(i)
                    break

    def closeEvent(self, event):
        """
        Triggered when the window is closed.
        Re-opens the Launcher window to allow module switching.
        """
        if self.launcher:
            self.launcher.show()
        event.accept()