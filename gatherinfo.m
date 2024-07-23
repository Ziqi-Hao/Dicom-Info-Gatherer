function gatherinfo(fileList,cursubfodername)
for i = 1:numel(fileList)
    filename=fileList(i).name;
    if filename == "." || filename == ".."
        continue
    end
    file = strcat(fileList(i).folder,'\',filename);
    aa=dicominfo(file);
    if i==1
        combined=aa;
    end
    if (i~=1) && (i <= numel(fileList))
        FieldNameNum = size(fieldnames(aa),1);
        CombStructNum = size(fieldnames(combined),1);
        if FieldNameNum ~= CombStructNum
            combined2 = catstruct(combined(end),aa);
            NewFN = fieldnames(combined);
            for j = 1:size(combined,2)
                for k = 1:size(NewFN,1)
                    combined2(j).(NewFN{k})=combined(j).(NewFN{k});
                end
            end
            combined = combined2;
            NewRowNum = size(combined,2)+1;
            addName = fieldnames(aa);
            for l = 1:size(addName,1)
                combined(NewRowNum).(addName{l})=aa.(addName{l});
            end
        else
            combined = [combined,aa];
        end
    end

end

T = struct2table(combined,"AsArray",true); % convert the struct array to a table
sortedT = sortrows(T, 'InstanceNumber'); % sort the table by 'DOB'
combined = table2struct(sortedT); % change it back to struct array if necessary

%% This section finds the header difference
fn = fieldnames(combined);
% same_folder_diff_m=repmat(' ',[numel(combined)-1 numel(fn)]);
same_folder_diff_m = strings([numel(combined)-1 numel(fn)]);
for i = 1:numel(combined)-1
    for j = 1:numel(fn)
        % For now I will pass the sub-structure comparision
        if isstruct(combined(i).(fn{j}))
            continue
        end
        % sotre the diffrence in a matrix, the "if" structure is designed 
        % to accomodate data structure
        same_folder_diff_single = setdiff(combined(i).(fn{j}),combined(i+1).(fn{j}));
        if isempty( same_folder_diff_single )
            same_folder_diff_single = num2str(same_folder_diff_single);
            same_folder_diff_m(i,j)=strcat(same_folder_diff_single, ' ');
        elseif max(size( same_folder_diff_single )) ~= 1
            same_folder_diff_m(i,j)=num2str(same_folder_diff_single(:)');
        else
            same_folder_diff_m(i,j)=string(same_folder_diff_single(:)');
        end
    end
end

%%
% Time
serst = string(unique({combined.SeriesTime}));
SeriesTime = string(strcat(extractBetween(serst,1,2),':',extractBetween(serst,3,4)));
sersd = string(unique({combined.SeriesDate}));
SeriesDate = string(strcat(extractBetween(sersd,1,4),'-',extractBetween(sersd,5,6),'-',extractBetween(sersd,7,8)));
SeriesDT = strcat(SeriesDate,'-',SeriesTime);

studt = string(unique({combined.StudyTime}));
StudyTime = string(strcat(extractBetween(studt,1,2),':',extractBetween(studt,3,4)));
studd = string(unique({combined.SeriesDate}));
StudyDate = string(strcat(extractBetween(studd,1,4),'-',extractBetween(studd,5,6),'-',extractBetween(studd,7,8)));
StudyDT = strcat(StudyDate,'-',StudyTime);


% Name

SeriesNumber = unique([combined.SeriesNumber]);
ProtocolName = string ( unique({combined.ProtocolName}));
SeriesDescription = string(unique({combined.SeriesDescription}));
StudyDescription = string(unique({combined.StudyDescription}));


% Dimension
Height = unique([combined.Height]);Width = unique([combined.Width]);
if isempty(Width)
    Width = ' ';
end
if isempty(Height)
    Height = ' ';
end
%Depth = numel(combined);
% if isfield(combined,'SequenceName')
%     SequenceName = unique({combined.SequenceName});
% 
% else
%     SequenceName = '  ';
%     
% end

if isfield(combined,'SliceOrientation')
    SliceOrientation = string(unique({combined.Private_0051_100e}));
    SliceOrientation = strjoin(SliceOrientation,',');
else
    SliceOrientation = '  ';
    
end
if isfield(combined,'ReceivingCoilName')
    ReceivingCoilName = string(unique({combined.Private_0051_100f}));
else
    ReceivingCoilName = '  ';
end
if isfield(combined,'TransmtiCoilName')
    TransmtiCoilName = string(unique({combined.TransmitCoilName}));
else
    TransmtiCoilName = '  ';
end

if isfield(combined, 'Private_0019_100a')
    Depth = combined.Private_0019_100a;
else
    Depth = numel(combined);
end
if isfield(combined, 'PixelSpacing')
%Resolution
    Res = unique([combined.PixelSpacing]','rows'); x_res = Res(2);
    y_res = Res(1);
    % z_res = combined(end).ImagePositionPatient(1)-combined(end-1).ImagePositionPatient(1);
    z_res = combined(1).SliceThickness;
else
    x_res = '  '; y_res = '  '; z_res = '  ';
end

if isfield(combined,'SpacingBetweenSlices')
    SpaceBetweenSlice = unique([combined.SpacingBetweenSlices]);
else
    SpaceBetweenSlice = '  ';
end

if isfield (combined, 'Private_0051_100c')
    FieldOfView = combined.Private_0051_100c;
    [C,matches] = strsplit(FieldOfView,{' ','*'});
    x_fov = string(C(2));
    y_fov = string(C(3));
    z_fov = z_res * Depth;
else
    x_fov = '  ';
    y_fov = '  ';
    z_fov = '  ';
end

if isfield(combined,'Private_0051_1011')
    MultiSlice = unique([combined.Private_0051_1011]);
else
    MultiSlice = '  ';
end
if isfield(combined,'InversionTime')
    InversionTime = unique([combined.InversionTime]);
else
    InversionTime = '  ';
end

if isfield(combined,'ImagePositionPatient')  
    if ProtocolName =='localizer'
        Position = num2str([combined.ImagePositionPatient]);
        Position = strjoin(string(Position),';');
    elseif contains(ProtocolName,'t1')
        Position = num2str([combined(1).ImagePositionPatient]');
        Position = regexprep(Position, ' +', ' ,');
    else
        Position = num2str(unique([combined.ImagePositionPatient])');
        Position = regexprep(Position, ' +', ' ,');
    end
else
    Position = ' ';
end

if isfield(combined,'FlipAngle')
    FlipAngle = unique([combined.FlipAngle]);
else
    FlipAngle = ' ';
end

if isfield(combined,'MRAcquisitionType')
    MRAcquisitionType = unique([combined.MRAcquisitionType]);
else
    MRAcquisitionType = ' ';
end

if isfield(combined,'RepetitionTime')
    RepetitionTime = unique([combined.RepetitionTime]);
else
    RepetitionTime = ' ';
end
if isfield(combined,'EchoTime')
    EchoTime = unique([combined.EchoTime]);
else
    EchoTime = '  ';
end


%% Output
FileName = strcat(ProtocolName,'_',TransmtiCoilName,'_',string(sersd),'_',extractBetween(serst,1,4),'_',string(SeriesNumber));

OutputStructure = struct('SeriesNumber',SeriesNumber,'FolderName',cursubfodername,...
    'SeriesDescription',SeriesDescription,'Rx_Coil',ReceivingCoilName,... %'SequenceName',SequenceName, 
    'MRAcquisitionType',MRAcquisitionType,...
    'SliceOrientation',SliceOrientation,...
    'X_Fov',x_fov,'Y_Fov',y_fov,'Z_Fov',z_fov,...
    'X_Dim',Width,'Y_Dim',Height,'Z_Dim',Depth,...
    'X_Voxel',x_res,'Y_Voxel',y_res, 'Z_Voxel',z_res,...
    'SliceGap',SpaceBetweenSlice,...
    'MultiBandAcqType',MultiSlice,'InversionTime',InversionTime,...
    'EchoTime',EchoTime,'RepetitionTime',RepetitionTime,'FlipAngle',FlipAngle,...
    'Position',Position,'StudyDescription',StudyDescription, ...
    'StudyAcqTime',StudyDT,'SeriesAcqTime',SeriesDT);
writefilename = strcat (string(cursubfodername),'.csv');
writetable(struct2table(OutputStructure),writefilename);
end