# logic/controller_comparator.py
import os
from ui.project_data import ProjectData

class ComparatorController:
    def __init__(self):
        # Dictionary to store loaded projects
        self.loaded_projects = {}

    def load_projects(self, file_paths):
        """
        Loads multiple JSON files.
        Returns:
            tuple: (loaded_names, failed_names)
        """
        loaded_names = []
        failed_names = []
        
        for path in file_paths:
            proj = ProjectData()
            success = proj.load_from_json(path)
            
            name = os.path.basename(path)
            
            if success:
                self.loaded_projects[name] = proj
                loaded_names.append(name)
                print(f"Successfully loaded: {name}")
            else:
                failed_names.append(name)
                print(f"Failed to load: {name}")
        
        return loaded_names, failed_names

    def remove_project(self, name):
        if name in self.loaded_projects:
            del self.loaded_projects[name]
            print(f"Removed project: {name}")

    def clear_all(self):
        self.loaded_projects.clear()
        print("Cleared all loaded projects.")

    def get_module_3_comparison_data(self):
        """
        Organizes data for comparing Module 3 results.
        
        Returns:
            A dictionary where:
            Key = Plot Title (e.g., "Area Distribution")
            Value = List of dictionaries, each containing:
                {
                    'label': Project Name,
                    'x': x_data,
                    'y': y_data,
                    'xlabel': x_label,
                    'ylabel': y_label,
                    'x_y_lims': x_y_lims
                }
        """
        comparison_data = {}
        
        # print(f"Analyzing {len(self.loaded_projects)} project(s) for Module 3 data...")
        
        # Iterate through all loaded projects
        for proj_name, proj_obj in self.loaded_projects.items():
            # Get Module 3 results
            mod3_res = proj_obj.results.get("module_3")
            
            if not mod3_res:
                print(f"Project '{proj_name}' has no Module 3 results. Skipping.")
                continue 
            
            # Iterate through the plots in that module result
            for plot_title, plot_data in mod3_res.items():
                if plot_title not in comparison_data:
                    comparison_data[plot_title] = []
                
                # Add project curve to the list for plot title
                comparison_data[plot_title].append({
                    'label': proj_name,
                    'x': plot_data['x_data'],
                    'y': plot_data['y_data'],
                    'xlabel': plot_data['x_label'],
                    'ylabel': plot_data['y_label'],
                    'x_y_lims': plot_data.get('x_y_lims')
                })
                
        return comparison_data
    
    def get_module_3_additional_data(self):
        """
        Organizes the 'y_additional' data.
        """
        additional_data = {}

        for proj_name, proj_obj in self.loaded_projects.items():
            mod3_res = proj_obj.results.get("module_3")
            if not mod3_res: continue

            for plot_title, plot_data in mod3_res.items():
                
                # Get the list/array safely
                y_add_list = plot_data.get('y_additional')
                
                # Check if it exists and has content
                if y_add_list is None or len(y_add_list) == 0:
                    continue

                if plot_title not in additional_data:
                    additional_data[plot_title] = []

                # Handle Labels
                y_add_labels = plot_data.get('y_additional_labels')
                
                # Ensure labels exist and match length
                if y_add_labels is None or len(y_add_labels) < len(y_add_list):
                    y_add_labels = [f"Curve {i+1}" for i in range(len(y_add_list))]

                # Iterate
                for i, y_row in enumerate(y_add_list):
                    
                    # Skip empty rows if any
                    if y_row is None or len(y_row) == 0:
                        continue
                        
                    curve_label = f"{proj_name} - {y_add_labels[i]}"
                    
                    additional_data[plot_title].append({
                        'label': curve_label,
                        'x': plot_data['x_data'],
                        'y': y_row,
                        'xlabel': plot_data['x_label'],
                        'ylabel': plot_data['y_label'],
                        'x_y_lims': plot_data.get('x_y_lims')
                    })
                    
        return additional_data