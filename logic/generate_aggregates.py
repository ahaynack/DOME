import numpy as np

class AggregateGenerator:
    def run(self, input_dict):
        # --- Parse input_dict ---
        target_sizes = np.array(input_dict['target_sizes'])
        target_rates = np.array(input_dict['target_rates'])
        volume_fraction = input_dict['volume_fraction']
        container_dims = input_dict['container_dims']
        diameter_params = np.array(input_dict['diameter_params'])
        
        # --- Geometry Setup ---
        container_x, container_y, container_z = container_dims
        container_V = container_x * container_y * container_z
        
        # Ensure available diameters are sorted (smallest to largest) for cumulative logic
        sort_idx = np.argsort(diameter_params)
        meso_input_mesh_sizes = diameter_params[sort_idx]
        
        # --- Interpolation ---
        # Map target GSD curve onto the specific available diameters
        gsd_passing_rates = target_rates / 100
        gsd_passing_rates_vf = gsd_passing_rates * volume_fraction
        gsd_passing_rates_export =  gsd_passing_rates_vf
        
        # Linear interpolation (np.interp handles sorting of x coordinates automatically)
        target_cumulative_rates = np.interp(meso_input_mesh_sizes, target_sizes, gsd_passing_rates_vf)
        
        # --- Calculation ---
        # Convert Target Rates to Target Cumulative Volumes
        target_cumulative_vol = target_cumulative_rates * container_V
        
        # Calculate Volume required per specific diameter (Incremental Volume)
        # Vol(size_i) = Cumulative(size_i) - Cumulative(size_i-1)
        target_incremental_vol = np.diff(target_cumulative_vol, prepend=0)
        
        # Clip negative values to 0
        target_incremental_vol = np.maximum(target_incremental_vol, 0)
        
        # Calculate Volume of Single Spheres for each diameter
        meso_radii = meso_input_mesh_sizes / 2.0
        sphere_volumes = (4/3) * np.pi * (meso_radii ** 3)
        
        # Determine Count (Volume Needed / Volume per Sphere)
        # round() or ceil() can be used
        calculated_counts = np.round(target_incremental_vol / sphere_volumes).astype(int)
        
        # Check total volume
        meso_volume = np.cumsum(((4/3) * np.pi * meso_radii**3) * calculated_counts)
        meso_volume_max = np.max(meso_volume)
        
        # --- Results & Reporting ---
        # Re-calculate actual achieved volume
        actual_incremental_vol = calculated_counts * sphere_volumes
        actual_cumulative_vol = np.cumsum(actual_incremental_vol)
        actual_max_vol_fraction = np.max(actual_cumulative_vol) / container_V
        
        print('Input aggregate diameters:\t', meso_input_mesh_sizes)
        print('Calculated aggregate amounts:\t', calculated_counts)
        print('Final Volume Fraction reached:\t', actual_max_vol_fraction)
        print('Total Sphere Volume:\t', meso_volume_max)
        
        # Format output
        output_counts = []
        for count, size in zip(calculated_counts, meso_input_mesh_sizes):
            output_counts.append([count, size/2]) # Output is [count, radius]
        output_counts = np.array(output_counts)
        
        # Output dictionary
        output_dict = {
            'payload_for_distribution': output_counts, 
            'gsd_mesh_sizes': target_sizes, 
            'gsd_passing_rates_export': gsd_passing_rates_export, 
            'meso_input_mesh_sizes': meso_input_mesh_sizes, 
            'meso_volume': actual_cumulative_vol / container_V
        }
        
        return output_dict




















