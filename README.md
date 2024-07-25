# Dicom-Info-Gatherer

## Overview

This MATLAB-based tool is designed to process DICOM (Digital Imaging and Communications in Medicine) files, extract relevant information, and generate structured CSV outputs. It's particularly useful for researchers and medical professionals working with MRI data.

## Features

- Automatically identifies and processes DICOM files in a specified directory
- Extracts key information from DICOM headers
- Organizes DICOM files into folders based on series information
- Generates individual CSV files for each series
- Merges all CSV files into a single comprehensive output

## Prerequisites

- MATLAB (developed and tested on version R2021a, but should work on recent versions)
- MATLAB Image Processing Toolbox (for DICOM file handling)

## Installation

1. Clone this repository to your local machine:
   ```
   git clone https://github.com/your-username/dicom-processing-tool.git
   ```
2. Navigate to the cloned directory in MATLAB

## Usage

1. Open MATLAB and navigate to the project directory
2. Edit the `main.m` file to set your input directory:
   ```matlab
   path = 'C:\path\to\your\dicom\files';
   ```
3. Run the `main.m` script in MATLAB

## File Description

- `main.m`: The main script to run the DICOM processing
- `dicom_library.m`: Contains all the functions used for DICOM processing
- `README.md`: This file, containing project information and instructions

## Output

The script will generate:
- Individual CSV files for each DICOM series in the input directory
- A merged CSV file containing information from all series

