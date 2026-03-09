import numpy as np
from scipy.stats import beta
from scipy.stats import truncnorm

########################################################################################################################
# Histogram Functions
def wiggly_beta(x, a, b, amp, freq):
    """Modified Beta function with a sine wave."""
    rv = beta(a, b)
    wiggly_beta = (amp * np.sin(np.pi*freq*x) - (amp/(np.pi*freq)*(1 - np.cos(np.pi*freq)))) + rv.pdf(x)
    
    # Compute the minimum value over [0,1] and shift if necessary
    min_value = np.min(wiggly_beta)
    if min_value < 0:
        # Shift entire function up to make all values non-negative
        wiggly_beta -= min_value
    
    return wiggly_beta

def symmetric_beta(x, a):
    """Symmetric Beta function."""
    rv = beta(a, a)
    symmetric_beta = rv.pdf(x)
    
    return symmetric_beta

def generate_histogram(n, a, num_bins):
    """
    Creates a histogram with 'n' points distributed under the wiggly beta function.
    Uses adaptive normalization to ensure a smooth distribution across all bins.

    Parameters:
    - n (int): Total number of points to distribute.
    - a, b (float): Beta distribution parameters.
    - amp (float): Amplitude of sine wave modification.
    - freq (float): Frequency of sine wave.
    - num_bins (int): Number of histogram bins.

    Returns:
    - bin_counts (np.array): The number of points in each bin.
    - x_centers (np.array): The bin center positions.
    """
    # Define bin edges and centers
    x_bins = np.linspace(0, 1, num_bins + 1)  # Bin edges
    x_centers = (x_bins[:-1] + x_bins[1:]) / 2  # Bin centers

    # Evaluate function on x-centers
    # y_values = wiggly_beta(x_centers, a, b, amp, freq)
    y_values = symmetric_beta(x_centers, a)

    # Compute bin widths and integrate area under the curve
    bin_widths = x_bins[1:] - x_bins[:-1]
    y_integral = np.sum(y_values * bin_widths)  # Approximates total area

    # Normalize to get probabilities
    bin_probs = (y_values * bin_widths) / y_integral  # Use area instead of sum

    # Compute expected counts per bin
    expected_counts = bin_probs * n  

    # Allocate integer counts per bin
    bin_counts = np.floor(expected_counts).astype(int)  

    # Fix rounding error: Adjust bins to match exactly 'n'
    error = n - np.sum(bin_counts)
    if error != 0:
        error = int(error)
        fractional_parts = expected_counts - bin_counts
        adjustment_indices = np.argsort(-fractional_parts)[:abs(error)]
        bin_counts[adjustment_indices] += np.sign(error)
    
    # # Distribute values evenly
    # if a == b == 1:
    #     bin_counts = distribute_non_floor_values(bin_counts)
    # Distribute values evenly
    if a <= 1:
        bin_counts = distribute_non_floor_values(bin_counts)
    # bin_counts = distribute_non_floor_values(bin_counts)

    return bin_counts, x_centers

def distribute_non_floor_values(arr):
    value_floor = np.min(arr)  # Determine the floor value
    non_floor_vals = arr[arr != value_floor]  # Extract non-floor values
    num_non_floor = len(non_floor_vals)
    total_positions = len(arr)

    if num_non_floor == 0:
        return arr  # Nothing to distribute

    # Ensure at least two non-floor values (one for start, one for end)
    if num_non_floor < 2:
        new_arr = np.full_like(arr, value_floor)
        new_arr[0] = non_floor_vals[0]
        new_arr[-1] = non_floor_vals[0]  # Repeat the same value at the end if needed
        return new_arr

    # Create new array filled with the floor value
    new_arr = np.full_like(arr, value_floor)

    # Assign first and last non-floor element
    new_arr[0] = non_floor_vals[0]
    new_arr[-1] = non_floor_vals[-1]

    # Distribute the remaining values
    remaining_vals = non_floor_vals[1:-1]
    num_remaining = len(remaining_vals)

    if num_remaining > 0:
        step = (total_positions - 1) / (num_remaining + 1)  # Space between remaining values

        for i, val in enumerate(remaining_vals):
            index = round((i + 1) * step)  # Compute evenly spaced index
            new_arr[index] = val

    return new_arr

# Histogram wrapper functions
def generate_histogram_wrapper(num_bins_max, container_length, radius_single_sphere, n, a):
    # Determine x distance depending on radius of sphere
    x_dist = container_length - (2 * radius_single_sphere)
    num_bins_i = int(np.floor(x_dist / (2/3 * radius_single_sphere)))
    
    # Generate histogram
    bin_counts, x_centers = generate_histogram(n, a, num_bins_i)
    
    # Normalize bins (same counts for all radii)
    bin_counts = spread_histogram_even_ends(bin_counts, num_bins_max)
    x_centers = np.linspace(0, 1, num_bins_max)
    # x_centers = spread_x_centers_anchored(x_centers, num_bins_max)
    
    # Spread x values along x-axis
    x_values = (x_centers * ((container_length - radius_single_sphere) - radius_single_sphere)) + radius_single_sphere
    
    return bin_counts, x_values

def spread_histogram_even_ends(original_counts, target_n_bins):
    n_small = len(original_counts)
    
    # Create the empty container
    new_counts = np.zeros(target_n_bins, dtype=original_counts.dtype)
    
    # Generate indices:
    # We want 'n_small' points, starting at 0, ending exactly at target_n_bins - 1
    # np.linspace handles the float math to keep spacing as even as possible
    target_indices = np.linspace(0, target_n_bins - 1, n_small)
    
    # Round to the nearest integer to find the bin slot
    target_indices = np.round(target_indices).astype(int)
    
    # Assign values
    new_counts[target_indices] = original_counts
    
    return new_counts

# def spread_x_centers_anchored(original_x, target_n_bins):
#     n_small = len(original_x)
    
#     # 1. Define the "physical" locations of the OLD data (0.0 to 1.0)
#     old_locations = np.linspace(0, 1, n_small)
    
#     # 2. Define the "physical" locations of the NEW data (0.0 to 1.0)
#     new_locations = np.linspace(0, 1, target_n_bins)
    
#     # 3. Interpolate
#     # This draws a line between the points. Because both arrays start at 0.0
#     # and end at 1.0, the first and last values are guaranteed to match.
#     new_x = np.interp(new_locations, old_locations, original_x)
    
#     return new_x

########################################################################################################################
# Distribution Calculations
def main_cubic_polynomial_hist(x_hist, x, x0, r):
    """Computes the cumulative sum of the sphere's cross-sectional area along the x-axis as a cubic polynomial.
    Better description: Computes the cumulative volume of spheres (or spherical caps) along the x-axis.
    
    Parameters:
    x  -- Position(s) at which to evaluate C(x)
    r  -- Radius of the sphere
    x0 -- Center of the sphere on the x-axis
    """
    x_shifted = x[:, None] - x0  # Shift x by x0 to place the sphere anywhere
    
    C = np.where(
        x_shifted < -r, 
        0,  # No area before reaching the sphere
        np.where(
            x_shifted > r,
            x_hist * ((4/3) * np.pi * r**3),  # The full volume when x >= x0 + r
            x_hist * (np.pi * (r**2 * x_shifted - (x_shifted**3) / 3 + (2/3) * r**3))  # Integral for -r < x - x0 < r
        )
    )
    return np.sum(C, axis=1)

def perimeter_length_hist(x_hist, x, x0, r):
    """Computes the cumulative sum of the sphere's slice circumferences along the x-axis.
    """
    x_shifted = x[:, None] - x0 
        
    C = np.where(
        x_shifted < -r, 
        0, 
        np.where(
            x_shifted > r,
            # 1. Total is pi^2 * r^2
            x_hist * ((np.pi**2) * r**2), 
            
            # 2. Integral of 2*pi*sqrt(r^2 - x^2)
            # This is exactly pi times the 'cumulative diameter' formula
            x_hist * np.pi * (
                x_shifted * np.sqrt(r**2 - x_shifted**2) + 
                r**2 * (np.arcsin(x_shifted / r) + np.pi / 2)
            )
        )
    )
    return np.sum(C, axis=1)

def cumulative_radius_hist(x_hist, x, x0, r):
    """Computes the cumulative sum of the sphere's slice radius along the x-axis.
    Physical interpretation: This calculates the cumulative Area of the 
    semi-circle profile of the sphere.
    """
    x_shifted = x[:, None] - x0 
        
    C = np.where(
        x_shifted < -r, 
        0, 
        np.where(
            x_shifted > r,
            # 1. Total is Area of semi-circle: (pi * r^2) / 2
            x_hist * (0.5 * np.pi * r**2), 
            
            # 2. Integral of sqrt(r^2 - x^2)
            # Note: This is exactly 1/2 of the bracketed term used in your 
            # perimeter function (because perimeter integrates 2*sqrt(...))
            x_hist * 0.5 * (
                x_shifted * np.sqrt(r**2 - x_shifted**2) + 
                r**2 * (np.arcsin(x_shifted / r) + np.pi / 2)
            )
        )
    )
    return np.sum(C, axis=1)

########################################################################################################################
# Scaling Simulation
def diameter_percentage_hist(x_hist, x, x0, r):
    """Computes the weighted sum of the linear diameter percentage traversed at position x.
    
    This acts as a linear ramp function:
    - Returns 0 if x is before the sphere starts.
    - Returns 1 if x is after the sphere ends.
    - Returns a linear value between 0 and 1 if x is inside the sphere.
    """
    x_shifted = x[:, None] - x0 
    
    # Calculate linear progression
    # Formula: (Current Position - Start Position) / Total Width
    #        = (x_shifted - (-r)) / (r - (-r))
    #        = (x_shifted + r) / (2 * r)
    
    C = np.where(
        x_shifted < -r, 
        0, 
        np.where(
            x_shifted > r,
            1.0,  # 100% (or 1.0) when fully traversed
            (x_shifted + r) / (2 * r)  # Linear ramp 0 -> 1
        )
    )
    # C = np.sum(C, axis=1)    
    return C

def cross_sectional_area_hist(x_hist, x, x0, r):
    """Computes the cross-sectional area of the sphere's slice at position x.
    
    Returns:
    0             (when x < -r)
    0             (when x > r)
    pi*(r^2 - x^2) (when inside the sphere)
    """
    x_shifted = x[:, None] - x0 
    
    # We calculate the area of the slice: A = pi * (radius_at_x)**2
    # radius_at_x = sqrt(r^2 - x^2)
    # Therefore: A = pi * (r^2 - x^2)
    
    C = np.where(
        x_shifted < -r, 
        0, 
        np.where(
            x_shifted > r,
            0,  # Goes back to 0 because it's not cumulative
            x_hist * (np.pi * (r**2 - x_shifted**2))
            # x_hist * (np.pi * r**2) # This calculates the area of the sphere's max radius (not used currently)
        )
    )
    # np.sum(C, axis=1)
    return C

def get_weighted_random_indices(n, weights, special_weight, replace=True):
    """
    Appends a new row to weights, samples n indices, and splits the results.

    Parameters:
    - n: Number of points to select.
    - weights: Original 2D numpy array.
    - special_weight: The weight value for the first element of the new row.
    - replace: Boolean. Default is True.
    
    Returns:
    - (orig_rows, orig_cols, special_count): 
        orig_rows: numpy array of row indices belonging to the original array.
        orig_cols: numpy array of col indices belonging to the original array.
        special_count: integer count of how many times the new row was picked.
    """
    
    # Construct new row
    new_row = np.zeros(weights.shape[1])
    new_row[0] = special_weight
    
    # Combine original weights with new row
    expanded_weights = np.vstack((weights, new_row))
    
    # Flatten and Calculate Probabilities
    flat_weights = expanded_weights.flatten()
    total_weight = flat_weights.sum()
    
    if total_weight == 0:
        raise ValueError("Total weight is zero. Cannot sample.")
        
    probs = flat_weights / total_weight

    # Check for unique sampling validity
    if not replace:
        non_zero_count = np.count_nonzero(flat_weights)
        if n > non_zero_count:
            raise ValueError(f"Cannot pick {n} unique items. Only {non_zero_count} non-zero weights exist.")

    # Perform the weighted random selection
    flat_indices = np.random.choice(
        flat_weights.size, 
        size=n, 
        replace=replace, 
        p=probs
    )

    # Convert to 2D coordinates
    all_rows, all_cols = np.unravel_index(flat_indices, expanded_weights.shape)
    
    # Split results
    special_row_index = weights.shape[0]
    
    # Create a boolean mask: True where the special row was picked
    is_special = (all_rows == special_row_index)
    
    # Count specials
    special_count = np.count_nonzero(is_special)
    
    # Filter the arrays to keep only original indices
    orig_rows = all_rows[~is_special]
    orig_cols = all_cols[~is_special]
    
    return orig_rows, orig_cols, special_count

def bin_count_at_x(x_hist, x, x0, r):
    """Returns the bin count for each sphere size at x.
    """
    x_shifted = x[:, None] - x0 
    
    C = np.where(x_shifted < -r, 0, np.where(x_shifted > r, 0, x_hist))
    # C = np.sum(C, axis=1)    
    return C

def get_volumes_by_percentage(x, radius, percentage):
    """
    Calculates the passed and remaining volumes of a sphere slice.
    
    Args:
        x (float): The current position on the x-axis (accepted but not used for calc).
        radius (float): The radius of the sphere.
        percentage (float): The linear fraction of the diameter passed (0.0 to 1.0).
                            0.0 = Start of sphere
                            0.5 = Center of sphere
                            1.0 = End of sphere
        
    Returns:
        tuple: (passed_volume, remaining_volume)
    """
    # Clamp percentage to ensure it stays between 0 and 1 
    p = max(0.0, min(1.0, percentage))
    
    # Calculate the "height" (h) of the slice
    # If percentage is 0.25 (25%), the height is 25% of the diameter (2 * radius)
    diameter = 2 * radius
    h = p * diameter
    
    # Calculate passed volume using Spherical Cap formula: V = (pi * h^2 / 3) * (3r - h)
    vol_passed = (np.pi * (h**2) / 3) * (3 * radius - h)
    
    # Calculate remaining volume (Total - Passed)
    total_volume = (4/3) * np.pi * (radius**3)
    vol_remaining = total_volume - vol_passed
    
    return vol_passed, vol_remaining

def generate_half_normal(size):
    scale = 0.45
    a, b = 0, 1  # bounds
    
    # convert bounds to standard normal space
    a_scaled = (a - 0) / scale
    b_scaled = (b - 0) / scale
    
    return truncnorm.rvs(a_scaled, b_scaled, loc=0, scale=scale, size=size)

def calculate_projections(sphere_radius, percentage, threshold):
    """
    Calculates a random point on a slice of a sphere and the distances 
    to the sphere's edge from that point.
    """
    
    # Ensure inputs are numpy arrays for consistent shape handling
    sphere_radius = np.asarray(sphere_radius)
    percentage = np.asarray(percentage)
    
    # Determine Slice Offset
    sphere_diameter = 2 * sphere_radius
    h = percentage * sphere_diameter
    slice_offset = sphere_radius - h
    
    # Determine the radius of the 2D circle created by the slice
    radius_sq_val = np.maximum(0, sphere_radius**2 - slice_offset**2) 
    circle_radius = np.sqrt(radius_sq_val)

    # Pick random radius
    # random_values = np.random.random(size=sphere_radius.shape)
    random_values = generate_half_normal(size=sphere_radius.shape)
    r_random = circle_radius * np.sqrt(random_values)
    
    # Project
    dist_from_sphere_axis_sq = r_random**2
    
    half_chord_length = np.sqrt(sphere_radius**2 - dist_from_sphere_axis_sq)
    
    x_intersection_positive = half_chord_length
    x_intersection_negative = -half_chord_length

    # Calculate lengths
    dist_pos = -np.abs(x_intersection_positive - slice_offset)
    dist_neg = np.abs(x_intersection_negative - slice_offset)
    
    # Determine output based on threshold
    output = np.where(percentage <= threshold, dist_pos, dist_neg)

    return output

def generate_jittered_values_uniform(base_value, n, jitter_value):
    jitter_min = base_value - jitter_value
    jitter_max = base_value + jitter_value
    
    jittered_values = np.random.uniform(jitter_min, jitter_max, size=n)
    
    jittered_values[jittered_values < 0] = 0
    
    return jittered_values

def generate_jittered_values_normal(base_value, n, jitter_value):
    jittered_values = np.random.normal(base_value, jitter_value, size=n)
    
    jittered_values[jittered_values < 0] = 0
    
    return jittered_values

def generate_jittered_values_normal_anchored(base_value, n, jitter_value, anchor_sharpness=5.5):
    """
    Generates values peaking at base_value with an asymmetric spread.
    
    Parameters:
    - base_value: The peak (mode) of the distribution.
    - n: Total number of values.
    - jitter_value: The standard deviation for the RIGHT side (the decline).
    - anchor_sharpness: Controls the LEFT side. It represents how many standard 
                        deviations fit between 0 and the base_value.
                        Lower = Fatter tail towards 0.
                        Higher = Sharper drop towards 0.
    """
    
    # Calculate the Left Sigma (Standard Deviation)
    sigma_left = base_value / anchor_sharpness  
    
    # Right Sigma is simply the jitter provided
    sigma_right = jitter_value
    
    # Determine how many points fall on the left vs right side
    total_sigma = sigma_left + sigma_right
    prob_left = sigma_left / total_sigma
    
    # Randomly decide how many points go left vs right based on probability
    n_left = np.random.binomial(n, prob_left)
    n_right = n - n_left
    
    # Generate data
    # Left: Half-Normal, flipped and subtracted from base
    left_side = base_value - np.abs(np.random.normal(0, sigma_left, n_left))
    
    # Right: Half-Normal, added to base
    right_side = base_value + np.abs(np.random.normal(0, sigma_right, n_right))
    
    # Combine, shuffle, and clip
    all_values = np.concatenate([left_side, right_side])
    np.random.shuffle(all_values)
    
    # Clip to 0 just in case the random generation produces a rare outlier < 0
    all_values = np.maximum(all_values, 0)
    
    return all_values

def generate_jittered_values_normal_asym(base_value, n, jitter_value, asym_factor=1.5):
    """
    Generates values peaking at base_value with an asymmetric spread.
    
    Parameters:
    - base_value: The peak (mode) of the distribution.
    - n: Total number of values.
    - jitter_value: The standard deviation for the RIGHT side (the decline).
    - asym_factor: Multiplicator of the standard deviation for the LEFT side.
    """
    
    # Calculate the Left Sigma (Standard Deviation)
    sigma_left = jitter_value * asym_factor
    
    # Right Sigma is simply the jitter provided
    sigma_right = jitter_value
    
    # Determine how many points fall on the left vs right side
    total_sigma = sigma_left + sigma_right
    prob_left = sigma_left / total_sigma
    
    # Randomly decide how many points go left vs right based on probability
    n_left = np.random.binomial(n, prob_left)
    n_right = n - n_left
    
    # Generate the data
    # Left: Half-Normal, flipped and subtracted from base
    left_side = base_value - np.abs(np.random.normal(0, sigma_left, n_left))
    
    # Right: Half-Normal, added to base
    right_side = base_value + np.abs(np.random.normal(0, sigma_right, n_right))
    
    # Combine, shuffle, and clip
    all_values = np.concatenate([left_side, right_side])
    np.random.shuffle(all_values)
    
    # Clip to 0 just in case the random generation produces a rare outlier < 0
    all_values = np.maximum(all_values, 0)
    # all_values[all_values <= 0] = np.random.normal(3.5, 1)
    
    # test = all_values[all_values <= 0]
    
    # test_dist = np.random.normal(0.25, 0.2, size=len(test))
    # test_dist = np.maximum(test_dist, 0)
    # # test_dist = -test
    
    # all_values = all_values[all_values > 0]
    
    # all_values = np.hstack((all_values, test_dist))
    
    return all_values

########################################################################################################################
# Distribution Minimization
def cumulative_segment_area_axis(row, num_bins, container_length, x_range):
    """
    Parameters:
    num_bins -- Number of bins for histogram generation
    """
    
    a, n, radius_single_sphere = row
    
    bin_counts, x_values = generate_histogram_wrapper(num_bins, container_length, radius_single_sphere, n, a)
    
    y_main = main_cubic_polynomial_hist(bin_counts, x_range, x_values, radius_single_sphere)
    
    return y_main

########################################################################################################################
# Wrapper function for distribution calculations
def create_solver(core_calc_func, mode):
    """
    Returns a new function that performs the full area_distribution logic
    using the provided core_calc_func.
    """
    
    # Internal helper needed for apply_along_axis
    def _middle_layer_wrapper(row, num_bins, container_length, x_range):
        # This matches the logic of cumulative_segment_area_axis
        a, n, radius_single_sphere = row
        
        num_bins_max = 5001
        bin_counts, x_values = generate_histogram_wrapper(num_bins_max, container_length, radius_single_sphere, n, a)
        
        # Call the core function provided to the parent
        return core_calc_func(bin_counts, x_range, x_values, radius_single_sphere)

    # The actual function to be returned
    def wrapper(x_init, meso_input, num_bins, container_length, x_range, x_init_shape):
        x_init = np.reshape(x_init, x_init_shape)
        x_init_meso = np.hstack((x_init, meso_input))
        
        y_main = np.apply_along_axis(
            _middle_layer_wrapper, 
            axis=1, 
            arr=x_init_meso, 
            num_bins=num_bins, 
            container_length=container_length, 
            x_range=x_range
        )
        
        if mode == 'normal':
            return y_main
        
        if mode == 'cumulative':
            x_range_delta = np.diff(x_range)
            y_main_diff = np.apply_along_axis(np.diff, axis=1, arr=y_main) / x_range_delta
            y_main_diff = np.concatenate((np.zeros((len(y_main_diff),1)), y_main_diff, np.zeros((len(y_main_diff),1))), axis=1)
            return y_main_diff
        
    return wrapper

########################################################################################################################
# Solvers for distribution calculations
solve_area_distribution = create_solver(main_cubic_polynomial_hist, mode='cumulative')
solve_perimeter_lengths = create_solver(perimeter_length_hist, mode='cumulative')
solve_radii = create_solver(cumulative_radius_hist, mode='cumulative')

solve_diameter_percentage = create_solver(diameter_percentage_hist, mode='normal')
solve_cross_sectional_area = create_solver(cross_sectional_area_hist, mode='normal')










