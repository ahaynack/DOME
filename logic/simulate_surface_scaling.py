# logic/simulate_surface_scaling.py
import numpy as np

import logic.functions as fct

class SurfaceScalingSimulator:
    def run(self, input_dict):
        """
        Main logic for Surface Scaling.
        input_dict contains:
            - source_data: The ProjectData object (access .results['module_2'] etc)
            - params: The dictionary of input parameters
        """
        # print("--- [Simulation] Starting Surface Scaling ---")
        
        source_project = input_dict.get('source_data')
        params = input_dict.get('params')
        
        # Accessing parameters
        scaling_threshold = params['scaling_threshold']
        matrix_jitter_value = params['matrix_jitter_value']
        matrix_asym_factor = params['matrix_asym_factor']
        n_points = params['number_of_points']
        scaling_hist_bins = params['scaling_hist_bins']
        diameter_cut_value = params['diameter_cut_value']
        x_specific = params['x_specific']
        x_half_sample = params['x_half_sample']

        # print(f"Params: Threshold={scaling_threshold}, Points={n_points}, Cut={diameter_cut_value}")
        
        # Accessing project input data
        meso_minimized_x = source_project.results['module_2']['meso_minimized_x']
        meso_input = source_project.results['module_1']['payload_for_distribution']
        num_bins = source_project.inputs['module_2']['n_bins']
        container_length, container_width, container_height = source_project.inputs['module_1']['container_dims']
        
        if x_specific is not None:
            x_range = np.array([x_specific])
        else:
            # x_range = source_project.results['module_2']['x_range']
            x_range = np.arange(0, 5, 0.2)
            # x_range = np.array([0, 0.75, 2, 2.5])
        
        if x_half_sample is not None:
            x_range = x_range + x_half_sample
        
        x_init = np.ones((len(meso_input), 1))
        x_init_shape = x_init.shape

        # Validation
        if not source_project or not source_project.results.get("module_2"):
            raise ValueError("Source Project has no valid Mesostructure (Module 2) data.")

        # --- SIMULATION LOGIC ---
        # Simulate Surface Scaling
        slice_area_total = container_width * container_height
        radii_ = meso_input[:,1]
        
        cross_sectional_area = fct.solve_cross_sectional_area(meso_minimized_x, meso_input, num_bins, container_length, x_range, x_init_shape)
        diameter_percentages = fct.solve_diameter_percentage(meso_minimized_x, meso_input, num_bins, container_length, x_range, x_init_shape)
        
        # Remove diameters smaller then diameter_cut_value
        diameter_cut_index = np.searchsorted(radii_, diameter_cut_value/2, side='left')
        radii_ = radii_[diameter_cut_index:]
        cross_sectional_area = cross_sectional_area[diameter_cut_index:,:,:]
        diameter_percentages = diameter_percentages[diameter_cut_index:,:,:]
        
        # Half sample
        if x_half_sample is not None:
            x_range = x_range - x_half_sample
        
        total_area = slice_area_total
        
        curves = []
        for slice_index in range(len(x_range)):
            x_ = x_range[slice_index]
            # print(f'\rScaling at x = {x_:.2f}', end='')
            slice_ = cross_sectional_area[:,slice_index,:]
            slice_area_total = np.sum(slice_)
            slice_area_total_normalized = slice_area_total / total_area
            
            slice_normalized = slice_ / total_area
            
            matrix_normalized = 1 - slice_area_total_normalized
            
            rows, cols, matrix_choices = fct.get_weighted_random_indices(n_points, slice_normalized, matrix_normalized, replace=True)
            
            diameter_percentages_choices = diameter_percentages[rows, slice_index, cols]
            radii_choices = radii_[rows]
            
            scaling_aggregates = fct.calculate_projections(radii_choices, diameter_percentages_choices, threshold=scaling_threshold)
            scaling_aggregates = x_ + scaling_aggregates
            scaling_aggregates = np.maximum(scaling_aggregates, 0)
            
            scaling_matrix = fct.generate_jittered_values_normal_asym(x_, matrix_choices, matrix_jitter_value, matrix_asym_factor)
            
            scaling_total = np.hstack((scaling_aggregates, scaling_matrix))
            
            scaling_hist, scaling_bin_edges = np.histogram(scaling_total, bins=scaling_hist_bins, density=False)
            scaling_pdf = scaling_hist / scaling_hist.sum()
            scaling_cdf = np.cumsum(scaling_pdf)
            scaling_hist_x = scaling_bin_edges[:-1] + np.diff(scaling_bin_edges).mean()
            
            curves.append({
                "x": scaling_hist_x,
                "y": scaling_cdf,
                "label": f"Depth = {x_:.2f}"
            })
        
        results = {
            "plot_data": {
                "curves": curves,
                "xlabel": "Depth [mm]",
                "ylabel": "Probability Density [-]"
            },
            "stats": {
                "max_depth": np.max(scaling_hist_x),
                "mean_depth": np.mean(scaling_hist_x)
            }
        }
        
        # print("\n--- [Simulation] Finished ---")
        return results