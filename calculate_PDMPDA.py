import os


failed_project_list = []
failed_d4jbug_list1 = []
failed_d4jbug_list2 = []
num_failed_project = 0
num_failed_d4jbug = 0
res_path = r'/home/lqy/MyProject/sequencer/@MyCodeAndData/new_model_trans-d4j_results'
trans_list = ['ReorderCondition', 'VariableRenaming']
for tran in trans_list:
    project_list = os.listdir(os.path.join(res_path, tran))
    for project in project_list:
        patch_id_list = os.listdir(os.path.join(res_path, tran, project))
        for i, id in enumerate(patch_id_list):
            if 'passed' in id:
                print(os.path.join(tran, project) + 'is passed test!')
                break
            if i == len(patch_id_list) - 1:
                failed_project_list.append(os.path.join(tran, project))
                bug, bugid, _, _ = project.split('---')
                if tran == 'ReorderCondition': failed_d4jbug_list1.append(bug+'_'+bugid)
                else: failed_d4jbug_list2.append(bug+'_'+bugid)
failed_d4jbug_list1 = list(set(failed_d4jbug_list1))
failed_d4jbug_list2 = list(set(failed_d4jbug_list2))
num_failed_project = len(failed_project_list)
num_failed_d4jbug1 = len(failed_d4jbug_list1)
num_failed_d4jbug2 = len(failed_d4jbug_list2)
w_path = './PDM_PDA_results.txt'
with open(w_path, 'w') as w:
    for item in failed_project_list:
        w.write(item + '\n')
    for item in failed_d4jbug_list1:
        w.write(item + '\n')
    for item in failed_d4jbug_list2:
        w.write(item + '\n')
print('number of failed projects: ', num_failed_project)
print('number of ReorderCondition failed d4jbugs: ', num_failed_d4jbug1)
print('number of VariableRenaming failed d4jbugs: ', num_failed_d4jbug2)
                
        
