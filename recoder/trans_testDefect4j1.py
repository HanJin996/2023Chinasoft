import sys
python_path = "/opt/conda/lib/python3.6/site-packages"
sys.path.append(python_path)
import os
import json
import pickle
from tqdm import tqdm
import numpy as np
from run import *
from stringfycode import stringfyRoot
from copy import deepcopy
import time
import io
import subprocess
from Searchnode import Node
import javalang


linenode = ['Statement_ter', 'BreakStatement_ter', 'ReturnStatement_ter', 'ContinueStatement', 'ContinueStatement_ter', 'LocalVariableDeclaration', 'condition', 'control', 'BreakStatement', 'ContinueStatement', 'ReturnStatement', "parameters", 'StatementExpression', 'return_type']
def getLocVar(node):
  varnames = []
  if node.name == 'VariableDeclarator':
    currnode = -1
    for x in node.child:
      if x.name == 'name':
        currnode = x
        break
    varnames.append((currnode.child[0].name, node))
  if node.name == 'FormalParameter':
    currnode = -1
    for x in node.child:
      if x.name == 'name':
        currnode = x
        break
    varnames.append((currnode.child[0].name, node))
  if node.name == 'InferredFormalParameter':
    currnode = -1
    for x in node.child:
      if x.name == 'name':
        currnode = x
        break
    varnames.append((currnode.child[0].name, node))
  for x in node.child:
    varnames.extend(getLocVar(x))
  return varnames
n = 0
def setid(root):
  global n
  root.id = n
  n += 1
  for x in root.child:
    setid(x)
def solveLongTree(root, subroot):
    global n
    m = 'None'
    troot = 'None'
    for x in root.child:
        if x.name == 'name':
            m = x.child[0].name
    if len(root.getTreestr().strip().split()) >= 1000:
        tmp = subroot
        if len(tmp.getTreestr().split()) >= 1000:
            assert(0)
        lasttmp = None
        while True:
            if len(tmp.getTreestr().split()) >= 1000:
                break
            lasttmp = tmp
            tmp = tmp.father
        index = tmp.child.index(lasttmp)
        ansroot = Node(tmp.name, 0)
        ansroot.child.append(lasttmp)
        ansroot.num = 2 + len(lasttmp.getTreestr().strip().split())
        while True:
            b = True
            afternode = tmp.child.index(ansroot.child[-1]) + 1
            if afternode < len(tmp.child) and ansroot.num + tmp.child[afternode].getNum() < 1000:
                b = False
                ansroot.child.append(tmp.child[afternode])
                ansroot.num += tmp.child[afternode].getNum()
            prenode = tmp.child.index(ansroot.child[0]) - 1
            if prenode >= 0 and ansroot.num + tmp.child[prenode].getNum() < 1000:
                b = False
                ansroot.child.append(tmp.child[prenode])
                ansroot.num += tmp.child[prenode].getNum()
            if b:
                break
        troot = ansroot
    else:
        troot = root
    n = 0
    setid(troot)
    varnames = getLocVar(troot)
    fnum = -1
    vnum = -1
    vardic = {}
    vardic[m] = 'meth0'
    typedic = {}
    for x in varnames:
        if x[1].name == 'VariableDeclarator':
            vnum += 1
            vardic[x[0]] = 'loc' + str(vnum)
            t = -1
            for s in x[1].father.father.child:
                #print(s.name)
                if s.name == 'type':
                    t = s.child[0].child[0].child[0].name[:-4]
                    break
            assert(t != -1)
            typedic[x[0]] = t
        else:
            fnum += 1
            vardic[x[0]] = 'par' + str(fnum)
            t = -1
            for s in x[1].child:
                if s.name == 'type':
                    t = s.child[0].child[0].child[0].name[:-4]
                    break
            assert(t != -1)
            typedic[x[0]] = t
    return troot, vardic, typedic
def addter(root):
    if len(root.child) == 0:
        root.name += "_ter"
    for x in root.child:
        addter(x)
    return
def setProb(r, p):
    r.possibility =  p
    for x in r.child:
        setProb(x, p)
def getLineNode(root, block, add=True):
  ans = []
  block = block + root.name
  for x in root.child:
    if x.name in linenode:
      if 'info' in x.getTreestr() or 'assert' in x.getTreestr() or 'logger' in x.getTreestr() or 'LOGGER' in x.getTreestr() or 'system.out' in x.getTreestr().lower():
        continue
      x.block = block
      ans.append(x)
    else:
      s = ""
      if not add:
        s = block
      else:
        s = block + root.name
      tmp = getLineNode(x, block)
      ans.extend(tmp)
  return ans
def getroottree(tokens, isex=False):
    root = Node(tokens[0], 0)
    currnode = root
    idx = 1
    for i, x in enumerate(tokens[1:]):
        if x != "^":
            if isinstance(x, tuple):
                nnode = Node(x[0], idx)
                nnode.position = x[1]
            else:
                nnode = Node(x, idx)
            nnode.father = currnode
            currnode.child.append(nnode)
            currnode = nnode
            idx += 1
        else:
            currnode = currnode.father
    return root
def ismatch(root, subroot):
    index = 0
    for x in subroot.child:
        while index < len(root.child) and root.child[index].name != x.name:
            index += 1
        if index == len(root.child):
            return False
        if not ismatch(root.child[index], x):
            return False
        index += 1
    return True
def findSubtree(root, subroot):
    if root.name == subroot.name:
        if ismatch(root, subroot):
            return root
    for x in root.child:
        tmp = findSubtree(x, subroot)
        if tmp:
            return tmp
    return None
def generateAST(tree):
    sub = []
    if not tree:
        return ['None', '^']
    if isinstance(tree, str):
        tmpStr = tree
        tmpStr = tmpStr.replace(" ", "").replace(":", "")
        if "\t" in tmpStr or "'" in tmpStr or "\"" in tmpStr:
            tmpStr = "<string>"
        if len(tmpStr) == 0:
            tmpStr = "<empty>"
        if tmpStr[-1] == "^":
            tmpStr += "<>"
        sub.append(tmpStr)
        sub.append("^")
        return sub
    if isinstance(tree, list):
        if len(tree) == 0:
            sub.append("empty")
            sub.append("^")
        else:
            for ch in tree:
                subtree = generateAST(ch)
                sub.extend(subtree)
        return sub
    position = None
    if hasattr(tree, 'position'):
        position = tree.position
    curr = type(tree).__name__
    if True:
        if False:
            assert(0)
        else:
            sub.append((curr, position))
            try:
                for x in tree.attrs:
                    if x == "documentation":
                        continue
                    if not getattr(tree, x):
                        continue
                    sub.append(x)
                    node = getattr(tree, x)
                    if isinstance(node, list):
                        if len(node) == 0:
                            sub.append("empty")
                            sub.append("^")
                        else:
                            for ch in node:
                                subtree = generateAST(ch)
                                sub.extend(subtree)
                    elif isinstance(node, javalang.tree.Node):
                        subtree = generateAST(node)
                        sub.extend(subtree)
                    elif not node:
                        continue
                    elif isinstance(node, str):
                        tmpStr = node
                        tmpStr = tmpStr.replace(" ", "").replace(":", "")
                        if "\t" in tmpStr or "'" in tmpStr or "\"" in tmpStr:
                            tmpStr = "<string>"
                        if len(tmpStr) == 0:
                            tmpStr = "<empty>"
                        if tmpStr[-1] == "^":
                            tmpStr += "<>"
                        sub.append(tmpStr)
                        sub.append("^")
                    elif isinstance(node, set):
                        for ch in node:
                            subtree = generateAST(ch)
                            sub.extend(subtree)
                    elif isinstance(node, bool):
                        sub.append(str(node))
                        sub.append("^")
                    else:
                        print(type(node))
                        assert(0)
                    sub.append("^")
            except AttributeError:
                assert(0)
                pass
        sub.append('^')
        return sub
    else:
        print(curr)
    return sub
def getSubroot(treeroot):
    currnode = treeroot
    lnode = None
    mnode = None
    while currnode:
        if currnode.name in linenode:
            lnode = currnode
            break
        currnode = currnode.father
    currnode = treeroot
    while currnode:
        if currnode.name == 'MethodDeclaration' or currnode.name == 'ConstructorDeclaration':
            mnode = currnode
            break
        currnode = currnode.father
    return lnode, mnode
def repair(treeroot, troot, oldcode, filepath, filepath2, patchpath, patchnum, isIf, mode, subroot, vardic, typedic, idxs, testmethods, idss, classname):
    global aftercode
    global precode
    actionlist = solveone(troot.printTreeWithVar(troot, vardic), troot.getTreeProb(troot), model, subroot, vardic, typedic, idxs, idss, classname, mode)
    for x in actionlist:
        if x.strip() in patchdict:
            continue
        patchdict[x.strip()] = 1 
        root = getroottree(x.split())
        code = stringfyRoot(root, isIf, mode)
        print(precode[-1000:])
        print(code) 
        print(aftercode[:1000])
        lnum = 0
        for x in code.splitlines():
            if x.strip() != "":
                lnum += 1
            else:
                continue
        print('lnum', lnum, mode)
        if lnum == 1 and 'if' in code:
            if mode == 0:
                continue
            afterlines = aftercode.splitlines()
            lnum = 0
            rnum = 0
            for p, x in enumerate(afterlines):
                if '{' in x:
                    lnum += 1
                if '}' in x:
                    if lnum == 0:
                        aftercode = "\n".join(afterlines[:p] + ['}'] + afterlines[p:])
                        #print(aftercode)
                        #assert(0)
                        break
                    lnum -= 1
            tmpcode = precode + "\n" + code + aftercode
            tokens = javalang.tokenizer.tokenize(tmpcode)
            parser = javalang.parser.Parser(tokens)
        else:
            tmpcode = precode + "\n" + code + aftercode
            tokens = javalang.tokenizer.tokenize(tmpcode)
            parser = javalang.parser.Parser(tokens)
        try:
            tree = parser.parse()
        except:
            #assert(0)
            print(code)
            continue
        open(filepath2, "w").write(tmpcode)
        bugg = False
        for t in testmethods:
            cmd = 'defects4j test -w buggy2/ -t %s' % t.strip()
            Returncode = ""
            child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
            while_begin = time.time() 
            while True:                
                Flag = child.poll()
                print(Flag)
                if  Flag == 0:
                    Returncode = child.stdout.readlines()#child.stdout.read()
                    break
                elif Flag != 0 and time.time() - while_begin > 10:
                    child.kill()
                    break
                else:
                    time.sleep(1)
            log = Returncode
            if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
                continue
            else:
                bugg = True
                break
        if not bugg:
            print('success')
            patchnum += 1
            wf = open(patchpath + 'patch' + str(patchnum) + ".txt", 'w')
            wf.write(filepath + "\n")
            wf.write("-" + oldcode + "\n")
            wf.write("+" +  code + "\n")
            if patchnum >= 5:
                return patchnum
    return patchnum
def getNodeById(root, line):
    if root.position:
        if root.position.line == line and root.name != 'IfStatement' and root.name != 'ForStatement':
            return root
    for x in root.child:
        t = getNodeById(x, line)
        if t:
            return t
    return None
def containID(root):
    ans = []
    if root.position is not None:
        ans.extend([root.position.line])
    for x in root.child:
        ans.extend(containID(x))
    return ans
def getAssignMent(root):
    if root.name == 'Assignment':
        return root
    for x in root.child:
        t = getAssignMent(x)
        if t:
            return t
    return None
def isAssign(line):
    if 'Assignment' not in line.getTreestr():
        return False
    anode = getAssignMent(line)
    if anode.child[0].child[0].name == 'MemberReference' and anode.child[1].child[0].name == 'MethodInvocation':
        try:
            m = anode.child[0].child[0].child[0].child[0].name
            v = anode.child[1].child[0].child[0].child[0].name
        except:
            return False
        print(m, v)
        return m == v
    if anode.child[0].child[0].name == 'MemberReference':
        try:
            m = anode.child[0].child[0].child[0].child[0].name
        except:
            return False
        if "qualifier " + m in anode.child[1].getTreestr():
            return True
    return False

model = test()
index_list = open(os.path.join(r'transformation_defects4j/buggy_lineINclass_idx.txt'), 'r').readlines()
open(os.path.join(r'transformation_defects4j/buggy_lineINclass_idx.txt')).close()
path_list = os.listdir(r'./trans_buggy_classes/')
for bug_path in sorted(path_list): # bug_path是Recoder要修复的bug的路径
    xss = bug_path.split('---')[0]
    idx = bug_path.split('---')[1]
    bug_class = bug_path.split('---')[2]
    trans_way = bug_path.split('_')[-1].split('.')[0]
    if trans_way == 'rc':
        if len(bug_path.split('_')) > 2: idss = xss + "-" + idx + '_' + bug_path.split('_')[-2] + '_rc'
        else: idss = xss + "-" + idx + '_rc'
    else:
        if len(bug_path.split('_')) > 2: idss = xss + "-" + idx + '_' + bug_path.split('_')[-2] + '_vr'
        else: idss = xss + "-" + idx + '_vr'
    data = []
    print(idss) # for debugging
    bug_index = 0
    for index in index_list:
        if index.split('---')[0] == xss and index.split('---')[1] == idx and index.split('---')[2] == bug_class:
            bug_index = int(index.split(' ')[-1].replace('\n', '')) # bug_index是Recoder要修复的bug的缺陷定位
            break
        
    classname = bug_path.split('---')[2]
    filepath = os.path.join(r'./trans_buggy_classes', bug_path)
    if bug_index != 0: lineid = eval(str(bug_index))
    else:
        print('no bug index, continuing!') 
        continue
    # lines1 = open(filepath, "r").read().strip()
    # liness = lines1.splitlines()
    # tokens = javalang.tokenizer.tokenize(lines1)
    # parser = javalang.parser.Parser(tokens)
    # tree = parser.parse()
    lines1 = open(filepath, "r").read().strip()
    liness = lines1.splitlines()
    try:
        tokens = javalang.tokenizer.tokenize(lines1)
        parser = javalang.parser.Parser(tokens)
        tree = parser.parse()
        # 在这里添加您希望执行的操作，如处理tree等
    except javalang.parser.JavaSyntaxError as e:
        # 在这里添加出现异常时希望执行的操作，比如跳过或打印出错误信息
        print(f"An error occurred during parsing: {e}")
        # 或者使用 pass 语句跳过
        pass
    tmproot = getroottree(generateAST(tree))
    currroot = getNodeById(tmproot, lineid)
    lnode, mnode = getSubroot(currroot)
    if mnode is None:
        continue
    oldcode = liness[lineid - 1]
    isIf = True
    subroot = lnode
    treeroot = mnode
    presubroot = None
    aftersubroot = None     
    linenodes = getLineNode(treeroot, "")
    if subroot not in linenodes:
        continue
    currid = linenodes.index(subroot)
    if currid > 0:
        presubroot = linenodes[currid - 1]
    if currid < len(linenodes) - 1:
        aftersubroot = linenodes[currid + 1]
    setProb(treeroot, 2)
    addter(treeroot)
    if subroot is None:
        continue
    if True:
        setProb(treeroot, 2)
        if subroot is not None:
            setProb(subroot, 1)
        if aftersubroot is not None:
            setProb(aftersubroot, 4)
        if presubroot is not None:
            setProb(presubroot, 3)
        cid = set(containID(subroot))
        maxl = -1
        minl = 1e10
        for l in cid:
            maxl = max(maxl, l - 1)
            minl = min(minl, l - 1)
        precode = "\n".join(liness[0:minl])
        aftercode = "\n".join(liness[maxl + 1:])
        oldcode = "\n".join(liness[minl:maxl + 1])
        troot, vardic, typedic = solveLongTree(treeroot, subroot)
        data.append({'treeroot':treeroot, 'troot':troot, 'oldcode':oldcode, 'filepath':filepath, 'subroot':subroot, 'vardic':vardic, 'typedic':typedic, 'idss':idss, 'classname':classname, 'precode':precode, 'aftercode':aftercode, 'tree':troot.printTreeWithVar(troot, vardic), 'prob':troot.getTreeProb(troot), 'mode':0, 'line':lineid, 'isa':False})
    solveone(data, model)

# # the range of the bug to fix
# prlist = ['Chart', 'Closure', 'Lang', 'Math', 'Time']
# ids = [list(range(1, 27)), list(range(1, 134)), list(range(1, 66)), list(range(1, 107)), list(range(1, 28))]

# # print('start model test')
# model = test()
# # print('end model test')
# for i, xss in enumerate(prlist[:1]):
#     for idx in ids[i][:1]:
#         # xss = 'Chart'
#         # idx = 10
#         idss = xss + "-" + str(idx)
#         bugid = idss
#         print(bugid)
#         # print('p')
#         timecurr = time.time()
#         x = xss
#         locationdir = './location/groundtruth/%s/%d' % (x.lower(), idx)
#         if not os.path.exists(locationdir):
#             print('dont have locationdir!')
#             continue
#         os.system('defects4j checkout -p %s -v %db -w buggy'%(x, idx))
#         patchnum = 0
#         lines = open(locationdir, 'r').readlines()
#         location = []
#         for loc in lines:
#             loc = loc.split("||")[0]
#             classname, lineid= loc.split(':')
#             location.append((classname, eval(lineid)))         
#         dirs = os.popen('defects4j export -p dir.src.classes -w buggy').readlines()[-1]
#         data = []
#         print('location length: ', len(location))
#         for j in range(1):
#             if j >= len(location):
#                 break
#             patchdict = {}
#             ac = location[j]
#             classname = ac[0]
#             if '$' in classname:
#                 classname = classname[:classname.index('$')]
#             s = ".".join(classname.split(".")[:-1])
#             classname = s
#             filepath = "buggy/%s/%s.java"%(dirs, s.replace('.', '/'))
#             print('filepath: ', filepath)
#             print('location: ', location)
#             print('classname: ', classname)
#             print('lineid1: ', lineid)
#             filepathx = "fixed/%s/%s.java"%(dirs, s.replace('.', '/'))
#             lines1 = open(filepath, "r").read().strip()
#             liness = lines1.splitlines()
#             tokens = javalang.tokenizer.tokenize(lines1)
#             parser = javalang.parser.Parser(tokens)
#             tree = parser.parse()
#             tmproot = getroottree(generateAST(tree))
#             lineid = ac[1]
#             print('lineid2: ', lineid)
#             currroot = getNodeById(tmproot, lineid)
#             lnode, mnode = getSubroot(currroot)
#             if mnode is None:
#                 continue
#             oldcode = liness[ac[1] - 1]
#             isIf = True
#             subroot = lnode
#             treeroot = mnode
#             presubroot = None
#             aftersubroot = None     
#             linenodes = getLineNode(treeroot, "")
#             if subroot not in linenodes:
#                 continue
#             currid = linenodes.index(subroot)
#             if currid > 0:
#                 presubroot = linenodes[currid - 1]
#             if currid < len(linenodes) - 1:
#                 aftersubroot = linenodes[currid + 1]
#             setProb(treeroot, 2)
#             addter(treeroot)
#             if subroot is None:
#                 continue
#             if True:
#                 setProb(treeroot, 2)
#                 if subroot is not None:
#                     setProb(subroot, 1)
#                 if aftersubroot is not None:
#                     setProb(aftersubroot, 4)
#                 if presubroot is not None:
#                     setProb(presubroot, 3)
#                 cid = set(containID(subroot))
#                 maxl = -1
#                 minl = 1e10
#                 for l in cid:
#                     maxl = max(maxl, l - 1)
#                     minl = min(minl, l - 1)
#                 precode = "\n".join(liness[0:minl])
#                 aftercode = "\n".join(liness[maxl + 1:])
#                 oldcode = "\n".join(liness[minl:maxl + 1])
#                 troot, vardic, typedic = solveLongTree(treeroot, subroot)
#                 data.append({'treeroot':treeroot, 'troot':troot, 'oldcode':oldcode, 'filepath':filepath, 'subroot':subroot, 'vardic':vardic, 'typedic':typedic, 'idss':idss, 'classname':classname, 'precode':precode, 'aftercode':aftercode, 'tree':troot.printTreeWithVar(troot, vardic), 'prob':troot.getTreeProb(troot), 'mode':0, 'line':lineid, 'isa':False})
#         # print('data: ', data)
#         # print('model: ', model)
#         solveone(data, model)
        