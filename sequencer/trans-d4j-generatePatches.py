# -*- coding: utf-8 -*-

import sys
import os

def transd4j_generatePatches(buggy_file_path, buggy_line_idx, prediction_path, output_path):
    predictions = open(prediction_path, 'r').readlines() # 预测的txt文件
    buggy_file_lines = open(buggy_file_path, 'r').readlines() # check out 后的bug file
    buggy_line_idx = int(buggy_line_idx)
    buggy_line = buggy_file_lines[buggy_line_idx-1] # 准备被替换掉的错误行
    white_space_before_buggy_line = buggy_line[0:buggy_line.find(buggy_line.lstrip())]
    for i in range(len(predictions)):
        output_file = os.path.join(output_path, str(i+1), os.path.basename(buggy_file_path))
        os.makedirs(os.path.dirname(output_file))
        output_file = open(output_file, "w")
        for j in range(len(buggy_file_lines)):
            if(j+1 == buggy_line_idx):
                output_file.write(white_space_before_buggy_line+predictions[i])
            else:
                output_file.write(buggy_file_lines[j])
        output_file.close()


if __name__=="__main__":
    path = r'/SequenceR/SequenceR_data/tmp'
    trans_list = ['ReorderCondition', 'VariableRenaming']
    for trans in trans_list:
        buggy_folder_list = os.listdir(os.path.join(path, trans))
        for buggy_folder in buggy_folder_list:
            prediction_path = os.path.join(path, trans, buggy_folder, 'predictions_JavaSource.txt') # transd4j_generatePatches的第3个参数
            buggy_name =  buggy_folder.split('---')[0]
            buggy_id =  buggy_folder.split('---')[1]
            csv_file = open(r'/SequenceR/src/Defects4J_Experiment/Defects4J_oneLiner_metadata.csv', 'r').readlines()
            for csv_item in csv_file:
                csv_name = csv_item.split(',')[0]
                csv_id = csv_item.split(',')[1]
                if csv_name == buggy_name and csv_id == buggy_id:
                    project_sub_path = csv_item.split(',')[2]
                    project_idx = csv_item.split(',')[3]
                    break
            project_name = buggy_name + '_' + buggy_id 
            buggy_file_path = os.path.join(r'/SequenceR/SequenceR_data/Defects4J_projects', project_name, project_sub_path) # transd4j_generatePatches的第1个参数
            buggy_line_idx = project_idx # transd4j_generatePatches的第2个参数
            output_path = os.path.join(r'/SequenceR/SequenceR_data/results', trans, buggy_folder)# transd4j_generatePatches的第4个参数

            # generate patches for transformed D4J project
            transd4j_generatePatches(buggy_file_path, buggy_line_idx, prediction_path, output_path)
    print('********************************************* done *********************************************')


    