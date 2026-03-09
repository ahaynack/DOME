# ui/_project_data.py
import json
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """ Helper to convert Numpy arrays to Lists for JSON saving. """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class ProjectData:
    # Define Tag Constant
    FILE_TAG = "DOME_GENERATOR_PROJECT"
    
    def __init__(self):
        # Structure to hold User Inputs
        self.inputs = {
            "module_1": {
                "container_dims": (150.0, 150.0, 150.0),
                "volume_fraction": 0.67,
                "curve_name": "", 
                "diameter_params": "0.125, 0.25, 0.5, 1, 2, 4, 8"
            },
            "module_2": {
                "n_bins": 801,
                "accuracy": 201,
                "edge_percentage": 10,
                "alpha_bounds": (0.65, 1.10)
            },
            "module_3": {
                "rho_agg": 2.65,
                "rho_mat": 2.00
            }
        }

        # Structure to hold Calculated Results
        self.results = {
            "module_1": None,
            "module_2": None,
            "module_3": None
        }

    @staticmethod
    def get_example_data():
        """Returns a ProjectData instance pre-filled with the 'Example' values."""
        proj = ProjectData()
        # Only filling inputs, results remain None for example
        proj.inputs["module_1"]["curve_name"] = "[STD] Standard AB8"
        # Ensure default string is set
        proj.inputs["module_1"]["diameter_params"] = "0.125, 0.25, 0.5, 1, 2, 4, 8"
        return proj

    def save_to_json(self, filepath):
        """Saves the current state to a JSON file."""
        data_dump = {
            "file_type": self.FILE_TAG,
            "inputs": self.inputs,
            "results": self.results
        }
        with open(filepath, 'w') as f:
            json.dump(data_dump, f, cls=NumpyEncoder, indent=4)
            print(f"Project saved successfully: {filepath}")

    def load_from_json(self, filepath):
        """Loads state from JSON and converts Lists back to Numpy Arrays."""
        try:
            with open(filepath, 'r') as f:
                data_dump = json.load(f)
            
            # --- VALIDATION CHECK ---
            ftype = data_dump.get("file_type")
            
            # If tag exists, it MUST match
            if ftype and ftype != self.FILE_TAG:
                print(f"Error: File '{filepath}' is a {ftype}, expected {self.FILE_TAG}.")
                return False
            
            # If tag is missing, check structure
            if not ftype:
                # Generator projects must have 'module_1' in inputs
                if "module_1" not in data_dump.get("inputs", {}):
                    print(f"Error: File '{filepath}' does not look like a Generator Project.")
                    return False
            # ------------------------
            
            # Load Inputs
            if "inputs" in data_dump:
                self.inputs.update(data_dump["inputs"])
            
            # Load Results
            if "results" in data_dump:
                loaded_results = data_dump["results"]
                self.results = self._recursive_list_to_array(loaded_results)
            
            return True
        except Exception as e:
            print(f"Failed to load project: {e}")
            return False

    def _recursive_list_to_array(self, obj):
        """Helper to walk through loaded JSON and convert Lists to NumPy Arrays."""
        if isinstance(obj, list):
            # Check if it is a list of numbers
            if len(obj) > 0 and isinstance(obj[0], (int, float, list)):
                 return np.array(obj)
            return obj
        elif isinstance(obj, dict):
            return {k: self._recursive_list_to_array(v) for k, v in obj.items()}
        else:
            return obj