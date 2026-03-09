# logic/controller_generator.py
from logic.generate_aggregates import AggregateGenerator
from logic.distribute_aggregates import AggregateDistributor
from logic.calculate_parameters import ParameterCalculator
from ui.project_data import ProjectData

class GeneratorController:
    def __init__(self):
        # Sub-modules
        self.mod_gen = AggregateGenerator()
        self.mod_dist = AggregateDistributor()
        self.mod_calc = ParameterCalculator()
        
        # Project Data
        self.project_data = ProjectData()

    @property
    def output_dict(self):
        """
        Helper for the GUI to check if Module 1 has run.
        Returns Module 1 results dictionary or None.
        """
        return self.project_data.results.get("module_1")

    def execute_generation(self, input_dict_generation):
        """
        Run Module 1
        """
        # Update Project Data Inputs
        self.project_data.inputs["module_1"].update({
            "container_dims": input_dict_generation.get('container_dims'),
            "volume_fraction": input_dict_generation.get('volume_fraction'),
            "diameter_params": input_dict_generation.get('diameter_params')
        })
        
        # Prepare Data for Calculation (Convert String -> List)
        # Create copy of the input dict to not mess up the original data
        calculation_dict = input_dict_generation.copy()
        
        raw_diameters = input_dict_generation.get('diameter_params', "")
        
        try:
            if isinstance(raw_diameters, str) and raw_diameters.strip():
                # Convert "1, 2, 3" -> [1.0, 2.0, 3.0]
                diam_list = [float(x.strip()) for x in raw_diameters.split(',') if x.strip()]
                calculation_dict['diameter_params'] = diam_list
            elif isinstance(raw_diameters, list):
                # Handle edge case where it might already be a list
                calculation_dict['diameter_params'] = raw_diameters
            else:
                # Handle empty string or None
                calculation_dict['diameter_params'] = []
        except ValueError:
            # Raise a clean error that the UI can catch and show in a MessageBox
            raise ValueError("Diameters input contains non-numeric values.\nPlease check your comma-separated list.")

        # Run Module
        output_dict = self.mod_gen.run(calculation_dict)
        
        # Store Results
        self.project_data.results["module_1"] = output_dict
        
        return output_dict

    def execute_distribution(self, input_dict_worker):
        """
        Run Module 2
        """
        # Update Project Data Inputs
        self.project_data.inputs["module_2"].update(input_dict_worker)
        
        # Prepare Data for Module (Combine inputs + previous results)
        mod1_results = self.project_data.results["module_1"]
        mod1_inputs = self.project_data.inputs["module_1"]
        
        input_dict = {
            'payload_for_distribution': mod1_results['payload_for_distribution'], 
            'container_dims': mod1_inputs['container_dims'], 
            **input_dict_worker
        }
        
        # Run Module
        output_dict = self.mod_dist.run(input_dict)
        
        # Store Results
        self.project_data.results["module_2"] = output_dict
        
        return output_dict

    def execute_calculation(self, input_dict_densities):
        """
        Run Module 3
        """
        # Update Project Data Inputs
        self.project_data.inputs["module_3"].update(input_dict_densities)
        
        # Prepare Data for Module
        mod1_results = self.project_data.results["module_1"]
        mod1_inputs = self.project_data.inputs["module_1"]
        mod2_results = self.project_data.results["module_2"]
        mod2_inputs = self.project_data.inputs["module_2"]
        
        input_dict = {
            'y_main': mod2_results['y_main'], 
            'x_range': mod2_results['x_range'], 
            'meso_minimized_x': mod2_results['meso_minimized_x'], 
            'payload_for_distribution': mod1_results['payload_for_distribution'], 
            'n_bins': mod2_inputs['n_bins'], 
            'container_dims': mod1_inputs['container_dims'], 
            'accuracy': mod2_inputs['accuracy'], 
            **input_dict_densities
        }
        
        # Run Module
        output_dict = self.mod_calc.run(input_dict)
        
        # Store Results
        self.project_data.results["module_3"] = output_dict
        
        return output_dict