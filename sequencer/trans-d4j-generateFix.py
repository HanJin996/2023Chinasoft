# -*- coding: utf-8 -*-
# 调用trans-d4j-predict.sh脚本
import os
import subprocess

trans_buggy_classes_path = r'/SequenceR/SequenceR_data/trans_buggy_classes' #在docker中再替换
trans_list = ['ReorderCondition', 'VariableRenaming']
buggy_lineINclass_idx_path = r'/SequenceR/SequenceR_data/buggy_lineINclass_idx.txt'#在docker中再替换

def run_shell_script(script_name, *args):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    command = ['bash', script_path] + list(args)
    subprocess.call(command)



for trans in trans_list:
    trans_buggy_classes_path_ = os.path.join(trans_buggy_classes_path, trans)
    for trans_file in os.listdir(trans_buggy_classes_path_):
        buggy_file = os.path.join(trans_buggy_classes_path_, trans_file) # shell脚本的第1个参数
        file_name_ = trans_file.split('_')[0]
        idx_messages = open(buggy_lineINclass_idx_path, 'r').readlines()
        line_idx = ''
        for idx_message in idx_messages:
            file_name = idx_message.split(' ')[0]
            if file_name_ == file_name:
                line_idx = idx_message.split(' ')[-1]
                break
        buggy_line = line_idx.replace('\r\n', '') # shell脚本的第2个参数
        beam_size = str(50) # shell脚本的第3个参数
        tmp_dir_ = r'/SequenceR/SequenceR_data/tmp/' + trans
        tmp_dir = os.path.join(tmp_dir_, trans_file.split('.')[0]) # shell脚本的第4个参数
        pro_name = file_name_.split('---')[0]
        pro_id = file_name_.split('---')[1]
        csv_file = open(r'/SequenceR/src/Defects4J_Experiment/Defects4J_oneLiner_metadata.csv', 'r').readlines()
        for csv_item in csv_file:
                csv_name = csv_item.split(',')[0]
                csv_id = csv_item.split(',')[1]
                if csv_name == pro_name and csv_id == pro_id:
                    project_sub_path = csv_item.split(',')[2]
                    break
        project_name = pro_name + '_' + pro_id 
        diff_path = os.path.join(r'/SequenceR/SequenceR_data/Defects4J_projects', project_name, project_sub_path)  # shell脚本的第5个参数
        script_name = 'trans-d4j-predict.sh'
        run_shell_script(script_name, '--buggy_file={buggy_file}'.format(buggy_file=buggy_file), '--buggy_line={buggy_line}'.format(buggy_line=buggy_line), '--beam_size={beam_size}'.format(beam_size=beam_size), '--tmp_dir={tmp_dir}'.format(tmp_dir=tmp_dir), '--diff_path={diff_path}'.format(diff_path=diff_path))