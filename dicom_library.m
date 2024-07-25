function varargout = dicom_library(functionName, varargin)
% DICOM_LIBRARY A library of functions for DICOM processing
%   This function serves as a wrapper for various DICOM processing functions.
%   Call it with the name of the desired function and any necessary arguments.

switch functionName
    case 'dicomUtils'
        [varargout{1}, varargout{2}] = dicomUtils();
    case 'organizeDicomFiles'
        organizeDicomFiles(varargin{:});
    case 'processDicomFolders'
        processDicomFolders(varargin{:});
    case 'mergeCSVFiles'
        mergeCSVFiles(varargin{:});
    case 'gatherinfo'
        gatherinfo(varargin{:});
    case 'catstruct'
        varargout{1} = catstruct(varargin{:});
    otherwise
        error('Unknown function name: %s', functionName);
end
end

function [findDicomFilesFunc, isDicomFileFunc] = dicomUtils()
    function dicomFiles = findDicomFilesInternal(folderPath)
        allFiles = dir(fullfile(folderPath, '*'));
        dicomFiles = {};
        
        for i = 1:length(allFiles)
            if ~allFiles(i).isdir
                filePath = fullfile(allFiles(i).folder, allFiles(i).name);
                if isDicomFileInternal(filePath)
                    dicomFiles{end+1} = filePath;
                end
            end
        end
    end

    function isDicom = isDicomFileInternal(filePath)
        try
            dicominfo(filePath);
            isDicom = true;
        catch
            isDicom = false;
        end
    end

    findDicomFilesFunc = @findDicomFilesInternal;
    isDicomFileFunc = @isDicomFileInternal;
end

function organizeDicomFiles(path, dicomFiles)
    for i = 1:numel(dicomFiles)
        file = dicomFiles{i};
        infostructure = dicominfo(file);
        foldername = strcat(string(infostructure.SeriesNumber),'_',infostructure.SeriesDescription);
        new_folder_full_path = fullfile(path, foldername);
        if ~exist(new_folder_full_path, 'dir')
           mkdir(new_folder_full_path);
        end
        movefile(file, new_folder_full_path);
    end
end

function processDicomFolders(path, findDicomFiles)
    fileList = dir(path);
    for i = 1:numel(fileList)
        foldername = fileList(i).name;
        if foldername == "." || foldername == ".."
            continue
        end
        subject = fullfile(path, foldername);
        if ~isfolder(subject)
            continue
        end
        dicomFiles = findDicomFiles(subject);
        if isempty(dicomFiles)
            continue
        else
            dicom_library('gatherinfo', dicomFiles, foldername)
        end
    end
end

function mergeCSVFiles(inputPath, outputFilename)
    fileList = dir(fullfile(inputPath, '*.csv'));
    
    mergedTable = table();
    
    essentialColumns = {'SeriesNumber', 'FolderName', 'SeriesDescription', 'Rx_Coil', ...
                        'MRAcquisitionType', 'SliceOrientation', 'X_Fov', 'Y_Fov', 'Z_Fov', ...
                        'X_Dim', 'Y_Dim', 'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel', ...
                        'SliceGap', 'MultiBandAcqType', 'InversionTime', 'EchoTime', ...
                        'RepetitionTime', 'FlipAngle', 'Position', 'StudyDescription', ...
                        'StudyAcqTime', 'SeriesAcqTime'};
    
    for i = 1:length(fileList)
        T = readtable(fullfile(fileList(i).folder, fileList(i).name), 'TextType', 'string', 'EmptyValue', NaN);
        
        T.Properties.VariableNames = matlab.lang.makeValidName(T.Properties.VariableNames);
        
        % Fill missing columns with appropriate empty values
        for col = essentialColumns
            if ~ismember(col, T.Properties.VariableNames)
                if ismember(col, {'SeriesNumber', 'X_Fov', 'Y_Fov', 'Z_Fov', 'X_Dim', 'Y_Dim', 'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel', 'SliceGap', 'InversionTime', 'EchoTime', 'RepetitionTime', 'FlipAngle'})
                    T.(col{1}) = NaN;
                else
                    T.(col{1}) = "";
                end
            elseif iscell(T.(col{1}))
                T.(col{1}) = string(T.(col{1}));
            end
        end
        
        % Ensure all essential columns are present and in the correct order
        T = T(:, essentialColumns);
        
        % Remove completely empty rows
        T = T(any(~ismissing(T), 2), :);
        
        mergedTable = [mergedTable; T];
    end
    
    % Sort the merged table by SeriesNumber
    if ismember('SeriesNumber', mergedTable.Properties.VariableNames)
        mergedTable = sortrows(mergedTable, 'SeriesNumber');
    end
    
    % Write the merged table to CSV
    writetable(mergedTable, outputFilename);
end

function gatherinfo(dicomFiles, cursubfodername)
    % Process DICOM files
    for i = 1:numel(dicomFiles)
        filename = dicomFiles{i};
        aa = dicominfo(filename);
        if i == 1
            combined = aa;
        else
            combined = catstruct(combined, aa);
        end
    end

    % Extract relevant information
    SeriesNumber = combined.SeriesNumber;
    SeriesDescription = combined.SeriesDescription;
    
    % Handle potentially missing fields
    fields_to_check = {'MRAcquisitionType', 'SliceOrientation', 'PixelSpacing', 'SpacingBetweenSlices', ...
                       'Private_0051_100c', 'Private_0051_1011', 'InversionTime', 'ImagePositionPatient', ...
                       'FlipAngle', 'RepetitionTime', 'EchoTime', 'Rows', 'Columns', 'SliceThickness', ...
                       'SpacingBetweenSlices', 'ReceivingCoilName', 'StudyDescription', 'SeriesTime', 'StudyTime'};

    for field = fields_to_check
        if ~isfield(combined, field{1})
            combined.(field{1}) = NaN;
        end
    end

    % Extract dimension information
    X_Dim = combined.Columns;
    Y_Dim = combined.Rows;
    Z_Dim = numel(dicomFiles);

    % Extract voxel size information
    if isnumeric(combined.PixelSpacing) && numel(combined.PixelSpacing) >= 2
        X_Voxel = combined.PixelSpacing(1);
        Y_Voxel = combined.PixelSpacing(2);
        Z_Voxel = combined.SliceThickness;
    else
        X_Voxel = NaN;
        Y_Voxel = NaN;
        Z_Voxel = NaN;
    end

    % Extract FOV information
    if ischar(combined.Private_0051_100c)
        fov_parts = sscanf(combined.Private_0051_100c, '%f*%f');
        if numel(fov_parts) == 2
            X_Fov = fov_parts(1);
            Y_Fov = fov_parts(2);
        else
            X_Fov = NaN;
            Y_Fov = NaN;
        end
    else
        X_Fov = NaN;
        Y_Fov = NaN;
    end
    Z_Fov = Z_Voxel * Z_Dim;

    % Extract other information
    MRAcquisitionType = string(combined.MRAcquisitionType);
    SliceOrientation = string(combined.SliceOrientation);
    SliceGap = combined.SpacingBetweenSlices;
    MultiBandAcqType = string(combined.Private_0051_1011);
    InversionTime = combined.InversionTime;
    EchoTime = combined.EchoTime;
    RepetitionTime = combined.RepetitionTime;
    FlipAngle = combined.FlipAngle;
    
    % Handle Position
    if isnumeric(combined.ImagePositionPatient) && numel(combined.ImagePositionPatient) >= 3
        Position = string(sprintf('%.4f,%.4f,%.4f', combined.ImagePositionPatient(1), combined.ImagePositionPatient(2), combined.ImagePositionPatient(3)));
    else
        Position = "";
    end

    % Extract coil information
    Rx_Coil = string(combined.ReceivingCoilName);

    % Extract study information
    StudyDescription = string(combined.StudyDescription);

    % Format date and time
    function formatted_datetime = format_datetime(date_str, time_str)
        if ischar(date_str) && ischar(time_str)
            date_parts = regexp(date_str, '(\d{4})(\d{2})(\d{2})', 'tokens');
            time_parts = regexp(time_str, '(\d{2})(\d{2})(\d{2})', 'tokens');
            if ~isempty(date_parts) && ~isempty(time_parts)
                formatted_datetime = sprintf('%s-%s-%s-%s:%s', ...
                    date_parts{1}{1}, date_parts{1}{2}, date_parts{1}{3}, ...
                    time_parts{1}{1}, time_parts{1}{2});
            else
                formatted_datetime = '';
            end
        else
            formatted_datetime = '';
        end
    end

    StudyAcqTime = string(format_datetime(combined.StudyDate, combined.StudyTime));
    SeriesAcqTime = string(format_datetime(combined.SeriesDate, combined.SeriesTime));

    % Create output structure
    OutputStructure = struct('SeriesNumber', SeriesNumber, ...
                             'FolderName', string(cursubfodername), ...
                             'SeriesDescription', SeriesDescription, ...
                             'Rx_Coil', Rx_Coil, ...
                             'MRAcquisitionType', MRAcquisitionType, ...
                             'SliceOrientation', SliceOrientation, ...
                             'X_Fov', X_Fov, 'Y_Fov', Y_Fov, 'Z_Fov', Z_Fov, ...
                             'X_Dim', X_Dim, 'Y_Dim', Y_Dim, 'Z_Dim', Z_Dim, ...
                             'X_Voxel', X_Voxel, 'Y_Voxel', Y_Voxel, 'Z_Voxel', Z_Voxel, ...
                             'SliceGap', SliceGap, ...
                             'MultiBandAcqType', MultiBandAcqType, ...
                             'InversionTime', InversionTime, ...
                             'EchoTime', EchoTime, ...
                             'RepetitionTime', RepetitionTime, ...
                             'FlipAngle', FlipAngle, ...
                             'Position', Position, ...
                             'StudyDescription', StudyDescription, ...
                             'StudyAcqTime', StudyAcqTime, ...
                             'SeriesAcqTime', SeriesAcqTime);

    % Write the output to CSV
    writefilename = strcat(string(cursubfodername), '.csv');
    writetable(struct2table(OutputStructure), writefilename);
end

function A = catstruct(varargin)
% CATSTRUCT   Concatenate or merge structures with different fieldnames
%   X = CATSTRUCT(S1,S2,S3,...) merges the structures S1, S2, S3 ...
%   into one new structure X. X contains all fields present in the various
%   structures. If a fieldname is not unique among structures, only the value 
%   from the last structure with this field is used.

narginchk(1,Inf);
N = nargin;

% Check if the last input is 'sorted'
if ischar(varargin{end}) && strcmp(varargin{end},'sorted')
    sorted = true;
    N = N-1;
else
    sorted = false;
end

% Initialize
FN = cell(1,N);
VAL = cell(1,N);

for ii=1:N
    X = varargin{ii};
    if ~isstruct(X)
        error('catstruct:InvalidArgument',['Argument #' num2str(ii) ' is not a structure.']);
    end
    
    if ~isempty(X)
        FN{ii} = fieldnames(X);
        VAL{ii} = struct2cell(X);
    end
end

% Concatenate the fieldnames and values
FN = cat(1,FN{:});
VAL = cat(1,VAL{:});

% Remove duplicates
[UFN, idx] = unique(FN, 'last');
VAL = VAL(idx);

% Sort if requested
if sorted
    [UFN, idx] = sort(UFN);
    VAL = VAL(idx);
end

% Create the output structure
A = cell2struct(VAL, UFN);

end
