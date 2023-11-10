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
    cmd += "defects4j export -p tests.trigger"
    result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    failling_tests = []
    cmd = ""
    cmd += "cd " + bug_project_dir + ";"
    cmd += "defects4j test"
    timeout = MAX_TEST_TIME
    # 创建子进程
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # 等待子进程完成或超时
    rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
    if process.stdout in rlist or process.stderr in rlist:
      # 子进程输出可读取
        output, error = process.communicate()
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
    sys.stdout.write(bug_project_dir + " has following failing tests:\n")
    for test in failling_tests:
        sys.stdout.write(test+"\n")
        sys.stdout.flush()

    for patch in os.listdir(trans_patch_dir):
        sys.stdout.write("Testing " + os.path.join(trans_patch_dir, patch,os.path.basename(bug_project_file)) + "\n")
        sys.stdout.flush()
        copyfile(os.path.join(trans_patch_dir,patch,os.path.basename(bug_project_file)), bug_project_file)
        cmd = ""
        cmd += "cd " + bug_project_dir + ";"
        cmd += "defects4j compile"
        # 创建子进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 等待子进程完成或超时
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
        if process.stdout in rlist or process.stderr in rlist:
          # 子进程输出可读取
            output, error = process.communicate()
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
        cmd += "defects4j test"
        # 创建子进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 等待子进程完成或超时
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
        if process.stdout in rlist or process.stderr in rlist:
          # 子进程输出可读取
            output, error = process.communicate()
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
    results_path_ = r'/SequenceR/SequenceR_data/results'
    trans_list = ['ReorderCondition', 'VariableRenaming']
    for trans in trans_list:
        results_path = os.path.join(results_path_, trans)
        bug_name_id_list = os.listdir(results_path)
        for bug_name_id in bug_name_id_list:
            trans_patch_dir = os.path.join(results_path, bug_name_id) # transd4j_validatePatch()的第1个参数
            bug_name = bug_name_id.split('---')[0]
            bug_id = bug_name_id.split('---')[1]
            project_name_id = bug_name + '_' + bug_id
            bug_project_dir = os.path.join(r'/SequenceR/SequenceR_data/Defects4J_projects', project_name_id) # transd4j_validateProject()的第2个参数
            csv_file = open(r'/SequenceR/src/Defects4J_Experiment/Defects4J_oneLiner_metadata.csv', 'r').readlines()
            for csv_item in csv_file:
                csv_name = csv_item.split(',')[0]
                csv_id = csv_item.split(',')[1]
                if csv_name == bug_name and csv_id == bug_id:
                    project_sub_path = csv_item.split(',')[2]
                    break
            bug_project_file = os.path.join(bug_project_dir, project_sub_path) # transd4j_validateProject()的第3个参数
            transd4j_validatePatch(trans_patch_dir, bug_project_dir, bug_project_file)