import numpy as np
from scipy.optimize import minimize
import time

import logic.functions as fct

########################################################################################################################
# Main
class AggregateDistributor:
    def run(self, input_dict):
        meso_input = input_dict['payload_for_distribution']
        container_length, container_width, container_height = input_dict['container_dims']
        
        num_bins = input_dict['n_bins']
        n_ = input_dict['accuracy']
        edge_percentage = input_dict['edge_percentage']
        bounds = [input_dict['alpha_bounds']] * len(meso_input)
        
        x_range = np.linspace(0, container_length, n_)
        
        x_init = np.ones((len(meso_input), 1))
        x_init_shape = x_init.shape
        
        edge_percentage_index = int(np.ceil((edge_percentage / 100) * n_))
        
        # Linear function
        def lin_func(x, a):
            return a * x

        def calculate_linear_line(y_main):
            lin_func_steepness = np.max(y_main) / np.max(range(len(y_main)))
            # lin_func_steepness_max = np.max(container_length*container_width*container_height) / np.max(range(len(y_main)))
            
            linear_line = lin_func(range(len(y_main)), lin_func_steepness)
            # linear_line_max = lin_func(range(len(y_main)), lin_func_steepness_max)
            
            return linear_line
        
        def calculate_y_main(x_init, meso_input, num_bins, container_length, x_range, x_init_shape):
            x_init = np.reshape(x_init, x_init_shape)
            
            x_init_meso = np.hstack((x_init, meso_input))
            
            y_main = np.apply_along_axis(fct.cumulative_segment_area_axis, axis=1, arr=x_init_meso, 
                                         num_bins=num_bins, container_length=container_length, x_range=x_range)
            y_main_plot = y_main
            y_main = np.sum(y_main, axis=0)
            
            # Refer values to total aggregate volume
            y_main_max = np.max(y_main)
            y_main = (y_main / y_main_max) * 100
            y_main_plot = (y_main_plot / y_main_max) * 100
            
            return y_main, y_main_plot
        
        # R2 score
        def r2_score(y, y_fit):
            # Residual sum of squares
            ss_res = np.sum((y - y_fit) ** 2)
            
            # Total sum of squares
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            # R-squared
            r2 = 1 - (ss_res / ss_tot)
            return r2

        # Minimize function
        self.step_counter = 0
        timer_start = time.time()
        def minimize_func(x_init, meso_input, num_bins, container_length, x_range, x_init_shape):
            # Calculate cumulative volume curve
            y_main, y_main_plot = calculate_y_main(x_init, meso_input, num_bins, container_length, x_range, x_init_shape)
            
            # Calculate linear volume line
            linear_line = calculate_linear_line(y_main)
            
            # Determine goodness of fit (R²)
            r2 = r2_score(y_main[:edge_percentage_index], linear_line[:edge_percentage_index])
            
            self.step_counter += 1
            
            print(f"\rNumber of Iterations: {self.step_counter}, R2 Score: {r2}", end='')
            
            return 1-r2
        
        meso_minimized = minimize(minimize_func, x0=x_init.ravel(), args=(meso_input, num_bins, container_length, x_range, x_init_shape), 
                                  bounds=bounds, method='Powell')

        meso_minimized_x = meso_minimized.x
        timer_end = time.time()
        
        self.run_time = timer_end - timer_start
        
        y_main, y_main_plot = calculate_y_main(meso_minimized_x, meso_input, num_bins, container_length, x_range, x_init_shape)
        linear_line = calculate_linear_line(y_main)
        
        output_dict = {
            'y_main': y_main, 
            'y_main_plot': y_main_plot, 
            'linear_line': linear_line, 
            'x_range': x_range, 
            'meso_minimized_x': meso_minimized_x, 
            'iterations': self.step_counter, 
            'run_time': self.run_time
            }
        
        print('\n-----------------------')
        
        return output_dict













