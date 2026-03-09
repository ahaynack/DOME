# logic/controller_simulation.py
import os
from ui.project_data import ProjectData
from ui.simulation_data import SimulationData
from logic.simulate_surface_scaling import SurfaceScalingSimulator

class SimulationController:
    def __init__(self):
        # Logic Module
        self.simulator = SurfaceScalingSimulator()
        
        # Data Container
        self.sim_data = SimulationData()

    def load_source_project(self, filepath):
        """Loads the DOME Generator Project (Module 1/2/3 data)"""
        proj = ProjectData()
        success = proj.load_from_json(filepath)
        if success:
            self.sim_data.source_project = proj
            
            # Store Name for UI Display
            self.sim_data.source_filename = os.path.basename(filepath)
            
            # Store Full Path for Reloading
            self.sim_data.source_project_path = os.path.abspath(filepath)
            
            return True
        return False
    
    def load_simulation(self, filepath):
        """
        Loads a saved Simulation JSON.
        Also attempts to auto-load the linked Source Project using the full path.
        """
        success = self.sim_data.load_from_json(filepath)
        if not success:
            return False

        # FULL PATH to find source
        source_path = self.sim_data.source_project_path
        
        # If path is empty, try filename in current dir
        if not source_path:
            source_path = self.sim_data.source_filename

        if source_path and os.path.exists(source_path):
            print(f"Auto-loading source project from: {source_path}")
            # Re-populate self.sim_data.source_project
            self.load_source_project(source_path)
        else:
            print(f"Warning: Source project not found at '{source_path}'.")
            self.sim_data.source_project = None
            
        return True

    def execute_simulation(self, ui_inputs):
        """
        Updates internal data with UI inputs, then runs the logic.
        """
        # Update Data Object
        self.sim_data.inputs.update(ui_inputs)

        # Prepare payload for Logic
        input_payload = {
            "source_data": self.sim_data.source_project,
            "params": self.sim_data.inputs
        }

        # Run
        results = self.simulator.run(input_payload)

        # Store
        self.sim_data.results = results
        
        return results

    def save_simulation(self, filepath):
        self.sim_data.save_to_json(filepath)