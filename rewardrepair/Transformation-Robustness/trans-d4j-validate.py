# -*- coding: utf-8 -*-
import os
import sys
import select
import subprocess
from shutil import copyfile

MAX_COMPILE_TIME = 60
MAX_TEST_TIME = 300

def transd4j_validatePatch(trans_patch_dir, bug_project_dir, bug_project_file):
    global MAX_COMPILE_TIME, MAX_TEST_TIME
    if(not os.path.exists(trans_patch_dir)):
        sys.stderr.write("Found no patch in " + trans_patch_dir + "\n")
        sys.stderr.flush()
        sys.exit(0)
    
    trigger_tests = []
    cmd = ""
    cmd += "cd " + bug_project_dir + ";"
    cmd += "/home/lqy/defects4j/framework/bin/defects4j export -p tests.trigger"
    result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print("Finishing defects4j export -p tests.trigger on {bug_project_dir}! ***************************".format(bug_project_dir=bug_project_dir))

    failling_tests = []
    cmd = ""
    cmd += "cd " + bug_project_dir + ";"
    cmd += "/home/lqy/defects4j/framework/bin/defects4j test"
    timeout = MAX_TEST_TIME
    # 创建子进程
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # 等待子进程完成或超时
    rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
    if process.stdout in rlist or process.stderr in rlist:
      # 子进程输出可读取
        output, error = process.communicate()
        # print(error)
    else:
      # 超时
        process.kill()
        process.wait()
        sys.stderr.write("Time limit exceeded when running the original bug version on " + bug_project_dir +"\n")
        sys.stderr.flush()
        sys.exit(1)
    result = output
    result = result.decode('utf-8')
    result = result.split("\n")
    result = list(filter(None, result))
    for i in range(len(result)):
        if(result[i].startswith("Failing tests:")):
            for j in range(i+1, len(result)):
                failling_tests.append(result[j][4:].strip())
            break
    # if (len(failling_tests) != 0):
        # sys.stdout.write(bug_project_dir + " has following failing tests:\n")
        # for test in failling_tests:
        #     sys.stdout.write(test+"\n")
        #     sys.stdout.flush()
    print("Finishing defects4j test on {bug_project_dir}! ***************************".format(bug_project_dir=bug_project_dir))

    for patch in os.listdir(trans_patch_dir):
        sys.stdout.write("Testing " + os.path.join(trans_patch_dir, patch,os.path.basename(bug_project_file)) + "\n")
        sys.stdout.flush()
        copyfile(os.path.join(trans_patch_dir,patch,os.path.basename(bug_project_file)), bug_project_file)
        cmd = ""
        cmd += "cd " + bug_project_dir + ";"
        cmd += "/home/lqy/defects4j/framework/bin/defects4j compile"
        # 创建子进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 等待子进程完成或超时
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
        if process.stdout in rlist or process.stderr in rlist:
          # 子进程输出可读取
            output, error = process.communicate()
            # print(error)
        else:
          # 超时
            process.kill()
            process.wait()
            continue
        result = error
        result = result.decode('utf-8')
        result = result.split("\n")
        result = list(filter(None, result))
        compile_error = False
        for line in result:
            if(not line.endswith("OK")):
                compile_error = True
        if(compile_error):
            continue
        cmd = ""
        cmd += "cd " + bug_project_dir + ";"
        cmd += "/home/lqy/defects4j/framework/bin/defects4j test"
        # 创建子进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 等待子进程完成或超时
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
        if process.stdout in rlist or process.stderr in rlist:
          # 子进程输出可读取
            output, error = process.communicate()
            # print(error)
        else:
          # 超时
            process.kill()
            process.wait()
            continue
        result = output
        result = result.decode('utf-8')
        result = result.split("\n")
        result = list(filter(None, result))
        passing_triggerTests = True
        passing_oldTests = True
        for i in range(len(result)):
            if(result[i].startswith("Failing tests:")):
                for j in range(i+1, len(result)):
                    if(result[j][4:] in trigger_tests):
                        passing_triggerTests = False
                    if(result[j][4:] not in failling_tests):
                        passing_oldTests = False
                break
        if(passing_triggerTests and passing_oldTests):
            os.rename(os.path.join(trans_patch_dir, patch), os.path.join(trans_patch_dir, patch+"_passed"))
        else:
            os.rename(os.path.join(trans_patch_dir, patch), os.path.join(trans_patch_dir, patch+"_compiled"))




if __name__=="__main__":
    results_path_ = ''
    trans_list = ['ReorderCondition', 'VariableRenaming']
    for trans in trans_list:
        results_path = os.path.join(results_path_, trans)
    for buggy_folder in os.listdir(results_path):
            trans_patch_dir = os.path.join(results_path, buggy_folder) # transd4j_validatePatch()的第1个参数
            bug_name = buggy_folder.split('---')[0]
            bug_id = buggy_folder.split('---')[1]
            buggy_project = bug_name + '_' + bug_id
            # print(buggy_project)
            bug_project_dir = os.path.join(r'/home/lqy/Workspace/rewardrepair/Coconut_Defects4J_projects', buggy_project) # transd4j_validateProject()的第2个参数
            csv_file1 = open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JMeta.csv', 'r').readlines()
            project_sub_path = ''
            for csv_item1 in csv_file1:
                csv_project = csv_item1.split('\t')[1]
                if buggy_project == csv_project:
                    project_sub_path = csv_item1.split('\t')[2]
                    project_idx = csv_item1.split('\t')[3]
                    break
            if project_sub_path == '' or ',' in project_sub_path:
                print(buggy_project)
                continue
            bug_project_file = os.path.join(bug_project_dir, project_sub_path) # transd4j_validateProject()的第3个参数
            transd4j_validatePatch(trans_patch_dir, bug_project_dir, bug_project_file)