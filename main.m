% main.m - Main DICOM Processing Script

% Clear workspace and command window
clear;
clc;

% Add the directory containing dicom_library.m to the MATLAB path
addpath(pwd);

% Ensure the library file is available
if exist('dicom_library.m', 'file') ~= 2
    error('dicom_library.m is not in the current directory or MATLAB path');
end

% Define paths
path = 'D:\PHTANTOM-2024JUL22\PHTANTOM-2024JUL22';
mkdirfoldername = 'organize_folder';

% Get function handles for DICOM utilities
[findDicomFiles, ~] = dicom_library('dicomUtils');

% Find all DICOM files in the directory
dicomFiles = findDicomFiles(path);

% Organize DICOM files into folders
dicom_library('organizeDicomFiles', path, dicomFiles);

% Process DICOM files in each folder
dicom_library('processDicomFolders', path, findDicomFiles);

% Merge CSV files
dicom_library('mergeCSVFiles', '.', fullfile(mkdirfoldername, 'merged_output.csv'));

% Create the output folder if it doesn't exist
if ~exist(mkdirfoldername, 'dir')
    mkdir(mkdirfoldername);
end

% Move all CSV files to the output folder
movefile('*.csv', mkdirfoldername);

disp('DICOM processing completed successfully.');