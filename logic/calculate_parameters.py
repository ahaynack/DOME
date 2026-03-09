# logic/calculate_parameters.py
import numpy as np

import logic.functions as fct

class ParameterCalculator:
    def run(self, input_dict):
        """
        Calculates parameters.
        
        Returns:
            A dictionary where:
            Key = Title of the Plot (String)
            Value = Tuple (x_data, y_data, x_label, y_label)
        """
        
        # Input data
        meso_minimized_x = input_dict['meso_minimized_x']
        meso_input = input_dict['payload_for_distribution']
        num_bins = input_dict['n_bins']
        container_length, container_width, container_height = input_dict['container_dims']
        x_range = input_dict['x_range']
        n_ = input_dict['accuracy']
        
        x_init = np.ones((len(meso_input), 1))
        x_init_shape = x_init.shape
        
        # Area Distribution
        area_dist = fct.solve_area_distribution(meso_minimized_x, meso_input, num_bins, container_length, x_range, x_init_shape)
        area_dist_sum = np.sum(area_dist, axis=0)

        x_range_derivation = np.linspace(0, container_length, n_+1)
        slice_area_total = container_width * container_height

        area_frac_list = area_dist / slice_area_total
        area_frac_total = area_dist_sum / slice_area_total
        
        y_additional_labels = list(meso_input[:,1] * 2)
        
        output_dict_area_dist = { 
            'x_data': x_range_derivation, 
            'y_data': area_frac_total, 
            'y_additional': area_frac_list, 
            'x_label': 'Sample Length [mm]', 
            'y_label': 'Area Fraction [-]', 
            'y_additional_labels': y_additional_labels, 
            'x_y_lims': (0, np.max(x_range), 0, 1)
            }
        
        # Perimeter Lengths
        peri_lens = fct.solve_perimeter_lengths(meso_minimized_x, meso_input, num_bins, container_length, x_range, x_init_shape)
        peri_lens_sum = np.sum(peri_lens, axis=0)
        
        y_additional_labels = list(meso_input[:,1] * 2)
        
        output_dict_peri_lens = { 
            'x_data': x_range_derivation, 
            'y_data': peri_lens_sum, 
            'y_additional': peri_lens, 
            'x_label': 'Sample Length [mm]', 
            'y_label': 'Perimeter Length [mm]', 
            'y_additional_labels': y_additional_labels, 
            'x_y_lims': (0, np.max(x_range), 0, None)
            }
        
        # Density Calculation
        rho_GK = input_dict['rho_agg']
        rho_cem = input_dict['rho_mat']

        y_main = input_dict['y_main']
        y_main = y_main * (container_length**2)

        container_integral = np.linspace(0, container_length, len(y_main))
        container_integral = container_integral * (container_length**2)

        y_cem = container_integral - y_main

        rho_func = (rho_GK * y_main) + (rho_cem * y_cem)
        rho_func = rho_func / container_integral
        rho_func = np.nan_to_num(rho_func)

        rho_func_x = np.linspace(0, container_length, len(rho_func))
        
        output_dict_density = { 
            'x_data': rho_func_x, 
            'y_data': rho_func, 
            'y_additional': [], 
            'x_label': 'Sample Length [mm]', 
            'y_label': 'Density [g/cm³]', 
            'y_additional_labels': [], 
            'x_y_lims': (0, np.max(x_range), np.min([rho_cem, rho_GK]), np.max([rho_cem, rho_GK]))
            }
        
        # Pack results into a dictionary
        # GUI will loop through this and create a tab for every key.
        results = {
            "Area Distribution": output_dict_area_dist, 
            "Perimeter Lengths": output_dict_peri_lens, 
            "Cumulative Density": output_dict_density
        }
        
        return results
