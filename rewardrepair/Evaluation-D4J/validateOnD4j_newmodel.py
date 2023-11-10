# -*- coding: utf-8 -*-
import os
import sys
import select
import subprocess
from shutil import copyfile

MAX_COMPILE_TIME = 60
MAX_TEST_TIME = 300

def validate_patches(trans_patch_dir, bug_project_dir, bug_project_file):
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
        # print(1)
        sys.stdout.write("Testing " + os.path.join(trans_patch_dir, patch,os.path.basename(bug_project_file)) + "\n")
        sys.stdout.flush()
        copyfile(os.path.join(trans_patch_dir,patch,os.path.basename(bug_project_file)), bug_project_file)
        cmd = ""
        cmd += "cd " + bug_project_dir + ";"
        cmd += "/home/lqy/defects4j/framework/bin/defects4j compile"
        # print(2)
        # 创建子进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 等待子进程完成或超时
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
        # print(3)
        if process.stdout in rlist or process.stderr in rlist:
          # 子进程输出可读取
            # print(4)
            output, error = process.communicate()
            # print('compile error: ', error)
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
            # print('test error: ', error)
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


def main():
    sub_results_patch_dir = r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/results_new'
    for bugid in sorted(os.listdir(sub_results_patch_dir)):
        results_patch_dir = os.path.join(sub_results_patch_dir, bugid) # 参数1
        bug_project_dir = os.path.join(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4J_projects', bugid) # 参数2
        Metas = open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JMeta.csv', 'r').readlines()
        open(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4JMeta.csv', 'r').close()
        for meta in Metas:
            if bugid == meta.split('\t')[1]:
                sub_buggy_file = meta.split('\t')[2]
                break
        if ',' in sub_buggy_file:
            # print('jump this project because it has multi bug file')
            continue
        bug_project_file = os.path.join(bug_project_dir, sub_buggy_file) # 参数3
        # print('results patch dir: ', results_patch_dir)
        # print('bug project dir: ', bug_project_dir)
        # print('bug project file: ', bug_project_file)
        # print('\n')
        # print('**************Starting validate on {bugid} project!**************'.format(bugid=bugid))
        validate_patches(
            trans_patch_dir=results_patch_dir,
            bug_project_dir=bug_project_dir,
            bug_project_file=bug_project_file
        )
        # print('**************Finishing validate on {bugid} project!**************'.format(bugid=bugid))



if __name__ == '__main__':
    main()