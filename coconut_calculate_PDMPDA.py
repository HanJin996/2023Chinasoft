import os


failed_project_list = []
failed_d4jbug_list1 = []
failed_d4jbug_list2 = []
d4jbug_list = []

res_path = ''
for project in os.listdir(res_path):
    if not os.path.isdir(os.path.join(res_path, project)): continue 
    patch_id_list = os.listdir(os.path.join(res_path, project))
    bug, bugid, _, _ = project.split('---')
    d4jbug_list.append(bug+'_'+bugid)
    for i, id in enumerate(patch_id_list):
        if 'passed' in id:
            print(project + 'is passed test!')
            break
        if i == len(patch_id_list) - 1:
            failed_project_list.append(project)
            if project.split('_')[-1] == 'rc': failed_d4jbug_list1.append(bug+'_'+bugid)
            else: failed_d4jbug_list2.append(bug+'_'+bugid)

d4jbug_list = list(set(d4jbug_list))
failed_d4jbug_list1 = list(set(failed_d4jbug_list1))
failed_d4jbug_list2 = list(set(failed_d4jbug_list2))

num_failed_project = len(failed_project_list)
num_failed_d4jbug1 = len(failed_d4jbug_list1)
num_failed_d4jbug2 = len(failed_d4jbug_list2)
num_project = len(os.listdir(res_path))
num_d4jbug = len(d4jbug_list)
                
print('PDM = {}/{} = {}'.format(num_failed_project, num_project, float(num_failed_project/num_project)))
print('ReorderCondition PDA = {}/{} = {}'.format(num_failed_d4jbug1, num_d4jbug, float(num_failed_d4jbug1/num_d4jbug)))
print('VariableRenaming PDA = {}/{} = {}'.format(num_failed_d4jbug2, num_d4jbug, float(num_failed_d4jbug1/num_d4jbug)))