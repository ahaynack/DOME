# DOME - Distribution-Optimized Mesostructure Estimation

DOME is an open source software package for generating virtual depth-dependent 2D representations of 3D concrete mesostructures. It is implemented in Python. DOME provides a modular GUI to generate and compare mesostructures.

The latest documentation for DOME is available at <LINK>.

## Features
The features available in the current version of DOME are listed below.

### Generation Module
#### Generation of Aggregate Size Groups
- Generation of aggregates used for the mesostructure generation by optimization against target grain size distribution.
- Aggregate size groups are defined by the provided aggregate radii.
- Definition of input parameters:
  - Sample geometry $x$, $y$, $z$ (length, width, height)
  - Target volume fraction of aggregates $F_V$

#### Distribution of Aggregates
- Generation of total aggregate distribution by optimization of individual aggregate size group distributions.
- Definition of input parameters:
  - Number of bins $n_{\text{bins}}$ (depth levels of aggregates)
  - Edge percentage $p_{\text{edge}}$ (range of optimization in reference to total sample depth)
  - Resolution of depth $x_{\text{range}}$
  - Bounds of $\alpha$ parameters for grain size group distributions (symmetrical Beta distributions)

#### Calculation of Depth-Dependent Mesostructure Parameters
- Calculation of:
  - Distribution of area fraction
  - Distribution of perimeter lengths
  - Cumulative sample density
- Definition of input parameters:
  - Density of aggregates $\rho_{\text{aggr}}$
  - Density of cement matrix $\rho_{\text{matrix}}$

### Comparison Module
#### Comparison of Generated Mesostructures from the 'Generation Module'
In this module, generated mesostructures form the 'Generation Module' can be loaded and compared.

## Publications
coming soon...

## Installation
coming soon...

## Acknowledgement
This work has been partially supported by the German Research Foundation (DFG), project number 398216472. This support is gratefully acknowledged.

## License
[MIT] (https://github.com/ahaynack/DOME/blob/main/LICENSE)
