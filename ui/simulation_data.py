# ui/simulation_data.py
import json
import numpy as np
from ui.project_data import ProjectData, NumpyEncoder

class SimulationData:
    # Define Tag Constant
    FILE_TAG = "DOME_SIMULATION_RESULT"
    
    def __init__(self):
        # Source project (ProjectData object)
        self.source_project = None
        
        # Display Name
        self.source_filename = "" 
        
        # Full Path
        self.source_project_path = ""

        # Inputs specific to Surface Scaling
        self.inputs = {
            "scaling_threshold": 0.75,
            "matrix_jitter_value": 0.30,
            "matrix_asym_factor": 1.50,
            "number_of_points": 200000,
            "scaling_hist_bins": 201,
            "diameter_cut_value": 2.0,
            "x_specific": None,
            "x_half_sample": None
        }

        # Results from simulation
        self.results = None

    def save_to_json(self, filepath):
        """Saves simulation inputs and results to JSON."""
        data_dump = {
            "file_type": self.FILE_TAG,
            "source_project_file": self.source_filename,
            "source_project_path": self.source_project_path,
            "inputs": self.inputs,
            "results": self.results
        }
        with open(filepath, 'w') as f:
            json.dump(data_dump, f, cls=NumpyEncoder, indent=4)

    def load_from_json(self, filepath):
        """Loads simulation data (inputs/results). Does NOT auto-load the source project."""
        try:
            with open(filepath, 'r') as f:
                data_dump = json.load(f)
            
            # --- VALIDATION CHECK ---
            ftype = data_dump.get("file_type")
            
            # Tag Check
            if ftype and ftype != self.FILE_TAG:
                print(f"Error: File '{filepath}' is a {ftype}, expected {self.FILE_TAG}.")
                return False
            
            # Legacy Check (no tag)
            if not ftype:
                if "source_project_file" not in data_dump:
                    print(f"Error: File '{filepath}' does not look like a Simulation Result.")
                    return False
            # ------------------------
            
            self.source_filename = data_dump.get("source_project_file", "")
            
            # Load Path
            self.source_project_path = data_dump.get("source_project_path", "")
            
            if "inputs" in data_dump:
                self.inputs.update(data_dump["inputs"])
            
            if "results" in data_dump:
                helper = ProjectData() 
                self.results = helper._recursive_list_to_array(data_dump["results"])
            
            return True
        except Exception as e:
            print(f"Failed to load simulation data: {e}")
            return False