# -*- coding: utf-8 -*-
import os


# 对于生成的predictions_JavaSource.txt文件，将其转化至/results下的patches
def generate_patches(buggy_file_path, buggy_line_idx, prediction_path, output_path):
    predictions = open(prediction_path, 'r').readlines() # 预测的txt文件
    buggy_file_lines = open(buggy_file_path, 'r').readlines() # check out 后的bug file
    buggy_line_idx = int(buggy_line_idx)
    buggy_line = buggy_file_lines[buggy_line_idx-1] # 准备被替换掉的错误行
    white_space_before_buggy_line = buggy_line[0:buggy_line.find(buggy_line.lstrip())]
    for i in range(len(predictions)):
        output_file = os.path.join(output_path, str(i+1), os.path.basename(buggy_file_path))
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        output_file = open(output_file, "w")
        for j in range(len(buggy_file_lines)):
            if(j + 1 == buggy_line_idx):
                output_file.write(white_space_before_buggy_line + predictions[i])
            else:
                output_file.write(buggy_file_lines[j])
        output_file.close()
    

def main(): 
    path = ''
    for buggy_folder in os.listdir(path):
        prediction_path = os.path.join(path, buggy_folder, 'predictions_JavaSource.txt')
        buggy_name =  buggy_folder.split('---')[0]
        buggy_id =  buggy_folder.split('---')[1]
        buggy_project = buggy_name + '_' + buggy_id
        csv_file1 = open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JMeta.csv', 'r').readlines()
        csv_file2 = open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JV1.2.csv', 'r').readlines()
        csv_file3 = open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JV2.0.csv', 'r').readlines()
        project_sub_path = ''
        project_idx = ''
        for csv_item1 in csv_file1:
            csv_project = csv_item1.split('\t')[1]
            if buggy_project == csv_project:
                project_sub_path = csv_item1.split('\t')[2]
                project_idx = csv_item1.split('\t')[3]
                break
        if project_sub_path == '' or project_idx == '' or ',' in project_sub_path:
            print(buggy_project)
            continue
        buggy_file_path = os.path.join(r'/home/lqy/Workspace/rewardrepair/Coconut_Defects4J_projects', buggy_project, project_sub_path)
        buggy_line_idx = project_idx
        output_path = os.path.join(r'/home/lqy/Workspace/rewardrepair/Coconut_results', buggy_folder)
        generate_patches(
            buggy_file_path=buggy_file_path, 
            buggy_line_idx=buggy_line_idx, 
            prediction_path=prediction_path, 
            output_path=output_path
            )



if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    device = 'cuda' if cuda.is_available() else 'cpu'
    print(torch.__version__)
    gc.collect()
    torch.cuda.empty_cache()
    main()


