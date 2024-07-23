clear;clc;

path = 'D:\PHTANTOM-2024JUL22\ANTOM2024JUL21_24_07_21-08_11_50-DST-1_3_12_2_1107_5_2_43_166092\DR_SHMUEL_HUMAN_DMRI_PILOT_20240721_081413_245000';
filetype = "*.IMA";
mkdirfoldername = 'organize_folder';

fileList = dir(path);
for i = 1:numel(fileList)
    filename = fileList(i).name;
    if filename == "." || filename == ".."
        continue
    end
    file = strcat(fileList(i).folder,'\',filename);
    if isfolder( file ) 
        continue
    else
        infostructure = dicominfo(file);
        foldername = strcat(string(infostructure.SeriesNumber),'_',infostructure.SeriesDescription);
        new_folder_full_path = strcat(fileList(i).folder,'\',foldername);
        if ~exist(new_folder_full_path, 'dir')
           mkdir(new_folder_full_path);
           movefile(file, new_folder_full_path);
        else
           movefile(file, new_folder_full_path);
        end
    end
end

fileList = dir(path);
for i = 1:numel(fileList)
    foldername=fileList(i).name;
    if foldername == "." || foldername == ".."
        continue
    end
    subject = strcat(path , '\' , foldername);
    path2 = strcat(subject ,'\', filetype);
    pathsplit = strsplit(path2,'\');
    pathparts = size(pathsplit);
    cursubfodername = pathsplit{pathparts(2)-1};
    fileList2 = dir(path2);
    if size(fileList2,1)==0
        continue
    else
        gatherinfo(fileList2,cursubfodername)
    end
end


%clear;clc;
path = './*.csv';
fileList = dir(path);

for i = 1:numel(fileList)
    filename=fileList(i).name;
    file = strcat(fileList(i).folder,'\',filename);
    T = readtable(file);
    T = table2struct(T,'ToScalar',true);
    if i == 1
        merged_struct = T;
    else
        FieldNameNum = size(fieldnames(T),1);
        CombStructNum = size(fieldnames(merged_struct),1);
        if FieldNameNum ~= CombStructNum
            merged_struct2 = catstruct(merged_struct(end),T);
            NewFN = fieldnames(merged_struct);
            for j = 1:max(size(merged_struct))
                for k = 1:size(NewFN,1)
                    merged_struct2(j).(NewFN{k})=merged_struct(j).(NewFN{k});
                end
            end
            NewRowNum = max(size(merged_struct))+1;
            addName = fieldnames(T);
            for l = 1:size(addName,1)
                merged_struct2(NewRowNum).(addName{l})=T.(addName{l});
            end
            merged_struct = merged_struct2;
        else
            merged_struct =[merged_struct; T];
        end
    end

end
date_list =[merged_struct.SeriesAcqTime];
[~,order]=sort(date_list);
merged_struct = struct2table(merged_struct);
sorted=merged_struct(order,:);
tablename = strcat(mkdirfoldername,'.csv');
writetable(sorted,tablename);
%mkdir PANT_ZH_64COIL_21_07_30
mkdir(mkdirfoldername)
movefile ('*.csv', mkdirfoldername)