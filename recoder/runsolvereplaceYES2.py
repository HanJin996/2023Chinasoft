import pickle
import math
from Searchnode1 import Node
import numpy as np
from tqdm import tqdm
import pickle
import sys
import re
import random
import time
#from stringfycode import stringfyNode
#lines1 = open("process1_1.txt", "r").read().strip()
#lines2 = open("process1_2.txt", "r").read().strip()
onelist = ['SRoot', 'arguments', 'parameters', 'body', 'block', 'selectors', 'cases', 'statements', 'throws', 'initializers', 'declarators', 'annotations', 'prefix_operators', 'postfix_operators', 'catches', 'types', 'dimensions', 'modifiers', 'case', 'finally_block', 'type_parameters']
rulelist = []
fatherlist = []
fathername = []
depthlist = []
copynode = {}
rules = pickle.load(open("rule.pkl", "rb"))#{"pad":0}
assert('value -> <string>_ter' in rules)
#rules['start -> unknown'] = len(rules)
#print(len(rules))
#assert(0)
#ruleter = pickle.load(open("ruleter.pkl", "rb"))
#rulenoter = pickle.load(open("rulenoter.pkl", "rb"))
#print(rulenoter)
#print(len(rulenoter))
#exit(0)
#print(rules)
#rules['delete -> node'] = len(rules)
cnum = len(rules)
#print(cnum)
#assert(0)
rulead = np.zeros([cnum, cnum])
#rules['statements -> End'] = len(rules)
#rulenoter['root -> End'] = 1
linenode = ['Statement_ter', 'BreakStatement_ter', 'ReturnStatement_ter', 'ContinueStatement', 'ContinueStatement_ter', 'LocalVariableDeclaration', 'condition', 'control', 'BreakStatement', 'ContinueStatement', 'ReturnStatement', "parameters", 'StatementExpression', 'return_type']
#print(len(rules))
rrdict = {}
for x in rules:
  rrdict[rules[x]] = x
hascopy = {}
def find_all(sub,s):
	index_list = []
	index = s.find(sub)
	while index != -1:
		index_list.append(index)
		index = s.find(sub,index+1)
	
	if len(index_list) > 0:
		return index_list
	else:
		return []
def getcopyid(nls, name, idx):
  original = " ".join(nls)
  idxs = find_all(name, original)#original.find(name)
  if len(idxs) != 0:
    minv = 100000
    idxx = -1
    for x in idxs:
      tmpid = len(original[:x].replace("^", "").split())
      if minv > abs(idx - tmpid):
        minv = abs(idx - tmpid)
        idxx = tmpid
    return 2000000 + idxx 
  return -1
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
isvalid = True
def getRule(node, nls, currId, d, idx, varnames, copy=True, calvalid=True):
  global rules
  global onelist
  global rulelist
  global fatherlist
  global depthlist
  global copynode
  global rulead
  global isvalid
  if not isvalid:
    return
  if len(node.child) == 0:
    return [], []
  copyid = -1
  child = node.child#sorted(node.child, key=lambda x:x.name)
  if len(node.child) == 1 and len(node.child[0].child) == 0 and copyid == -1 and copy:
    if node.child[0].name in varnames:
      rule = node.name + " -> " + varnames[node.child[0].name]
      if rule in rules:
        rulelist.append(rules[rule])
      else:
        #assert(0)
        #rules[rule] = len(rules)
        #rulelist.append(rules[rule])
        #print('b', rule)
        isvalid = False
        return
        #assert(0)
        #rules[rule] = len(rules)
      fatherlist.append(currId)
      fathername.append(node.name)
      depthlist.append(d)
      return
  if copyid == -1:
    copyid = getcopyid(nls, node.getTreestr(), node.id)
    if node.name == 'MemberReference' or node.name == 'operator' or node.name == 'type' or node.name == 'prefix_operators' or node.name == 'value': #or node.name == 'Literal' or node.name == 'value':
      copyid = -1
    if node.name == 'operandl' or node.name == 'operandr':
      if node.child[0].name == 'MemberReference' and node.child[0].child[0].name == 'member':
        copyid = -1
    if node.name == 'Literal':
      if 'value -> ' + node.child[0].child[0].name in rules:
        copyid = -1 
      #varname = node.child[0].child[0].name
      #for i in range(len(varnames)):
      #  v = varnames[len(varnames) - 1 - i]
      #  if varname == v[0]:
      #    copyid = -1#2000000 + v[1].id
      #    #assert(0)
      #    break
  if len(node.child) == 1 and len(node.child[0].child) == 0 and copyid == -1:
      rule = node.name + " -> " + node.child[0].name
      if rule not in rules and (node.name == 'member' or node.name == 'qualifier'):
        rule = rules['start -> unknown']
        rulelist.append(rule)
        fatherlist.append(currId)
        fathername.append(node.name)
        depthlist.append(d)
        return
  if copyid != -1:
    #assert(0)
    #print(node.printTree(node))
    copynode[node.name] = 1
    rulelist.append(copyid)
    fatherlist.append(currId)
    fathername.append(node.name)
    depthlist.append(d)
    currid = len(rulelist) - 1
    if rulelist[currId] >= cnum:
      pass
    elif currId != -1:
      rulead[rulelist[currId], rules['start -> copyword']] = 1
      rulead[rules['start -> copyword'], rulelist[currId]] = 1
    else:
      rulead[rules['start -> copyword'], rules['start -> root']] = 1
      rulead[rules['start -> root'], rules['start -> copyword']] = 1
    return
    #for x in child:
    #  getRule(x, nls, currid, d + 1)
      #rulelist.extend(a)
      #fatherlist.extend(b)
  else:
    if node.name not in onelist:
      rule = node.name + " -> "
      for x in child:
        rule += x.name + " "
      rule = rule.strip()
      if rule in rules:
        rulelist.append(rules[rule])
      else:
        print('b', rule)
        isvalid = False
        return
        rulelist.append(rules['start -> unknown'])
        #print(rule)
        #rule = node.name + " -> " + 'unknown_var'
        #isvalid = False
        #return
        #if rule not in rules:
        #assert(0)
        #  rules[rule] = len(rules)
        #rulelist.append(rules[rule])
      fatherlist.append(currId)
      fathername.append(node.name)
      depthlist.append(d)
      if rulelist[-1] < cnum and rulelist[currId] < cnum:#not (len(child) == 1 and len(child[0].child) == 0):
        if currId != -1:
          rulead[rulelist[currId], rulelist[-1]] = 1
          rulead[rulelist[-1], rulelist[currId]] = 1
        else:
          #print(rulelist)
          rulead[rules['start -> root'], rulelist[-1]] = 1
          rulead[rulelist[-1], rules['start -> root']] = 1
      currid = len(rulelist) - 1
      for x in child:
        getRule(x, nls, currid, d + 1, idx, varnames)
    else:
      #print(node.name)
      for x in (child):
        rule = node.name + " -> " + x.name
        rule = rule.strip()
        if rule in rules:
          rulelist.append(rules[rule])
        else:
          #if calvalid:
          print('b', rule)
          isvalid = False
          return
          rulelist.append(rules['start -> unknown'])
          #rule = 'start -> unknown_var'#node.name + " -> " + 'unknown_var'
          #isvalid = False
          #return
          #if rule not in rules:
          #  rules[rule] = len(rules)
          '''if len(x.child) == 0:
            ruleter[rule] = 1
          else: 
            rulenoter[rule] = 1
          rules[rule] = len(rules)'''
          #rulelist.append(rules[rule])
        if rulelist[-1] < cnum and rulelist[currId] < cnum:
          rulead[rulelist[currId], rulelist[-1]] = 1
          rulead[rulelist[-1], rulelist[currId]] = 1
        fatherlist.append(currId)
        fathername.append(node.name)
        depthlist.append(d)
        getRule(x, nls, len(rulelist) - 1, d + 1, idx, varnames)
      rule = node.name + " -> End "
      rule = rule.strip()
      if rule in rules:
        rulelist.append(rules[rule])
      else:
        print(rule)
        rulenoter[rule] = 1
        assert(0)
        rules[rule] = len(rules)
        rulelist.append(rules[rule])
      rulead[rulelist[currId], rulelist[-1]] = 1
      rulead[rulelist[-1], rulelist[currId]] = 1
      fatherlist.append(currId)
      fathername.append(node.name)
      depthlist.append(d)
def dist(l1, l2):
  if l1[0] != l2[0]:
    return 0
  ans = []
  dic = {}
  for i in range(0, len(l1) + 1):
    dic[(i, 0)] = 0
  for i in range(0, len(l2) + 1):
    dic[(0, i)] = 0
  for i in range(1, len(l1) + 1):
    for j in range(1, len(l2) + 1):
      if l1[i - 1] == l2[j - 1]:
        dic[(i, j)] = dic[(i - 1, j - 1)] + 1
      elif dic[(i - 1, j)] > dic[(i, j - 1)]:
        dic[(i, j)] = dic[(i - 1, j)]
      else:
        dic[(i, j)] = dic[(i, j - 1)]
  return -dic[(len(l1), len(l2))] / min(len(l1), len(l2))
def hassamechild(l1, l2):
  for x in l1.child:
    for y in l2.child:
      if x == y:
        return True
  return False
action = []
def setProb(r, p):
  r.possibility =  p#max(min(np.random.normal(0.8, 0.1, 10)[0], 1), 0)
  #print(r.possibility)
  for x in r.child:
    setProb(x, p)
def getLineNode(root, block, add=True):
  ans = []
  block = block + root.name
  #print(root.name, 'lll')
  for x in root.child:
    if x.name in linenode:
      if 'info' in x.getTreestr() or 'assert' in x.getTreestr() or 'logger' in x.getTreestr() or 'LOGGER' in x.getTreestr() or 'system.out' in x.getTreestr().lower():
        continue
      x.block = block
      ans.append(x)
    else:
      #print(x.name)
      s = ""
      if not add:
        s = block
        #tmp = getLineNode(x, block)
      else:
        s = block + root.name
      #print(block + root.name + "--------")
      tmp = getLineNode(x, block)
      '''if x.name == 'then_statement' and tmp == []:
        print(tmp)
        print(x.father.printTree(x.father))
        assert(0)'''
      ans.extend(tmp)
  return ans
reslist = []
n = 0
def setid(root):
  global n
  root.id = n
  n += 1
  for x in root.child:
    setid(x)
def isexpanded(lst):
  ans = False
  for x in lst:
    ans = ans or x.expanded
  return ans
def ischanged(root1, root2):
  #root1.name ==
  if root1.name != root2.name:
    return False
  if root1 == root2:
    return True
  if root1.name == 'MemberReference' or root1.name == 'BasicType' or root1.name == 'operator' or root1.name == 'qualifier' or root1.name == 'member' or root1.name == 'Literal':
    return True
  if len(root1.child) != len(root2.child):
    return False
    #if root1.father.father.name == 'MemberReference' or root1.father.father.name == 'BasicType' or root1.father.name == 'operator':
    #  return True
    #else:
    #  return False
  ans = True
  for i in range(len(root1.child)):
    node1 = root1.child[i]
    node2 = root2.child[i]
    ans = ans and ischanged(node1, node2)
  return ans
def getchangednode(root1, root2):
  if root1 == root2:
    return []
  ans = []
  if root1.name == 'MemberReference' or root1.name == 'BasicType' or root1.name == 'operator' or root1.name == 'qualifier' or root1.name == 'member' or root1.name == 'Literal':
    return [(root1, root2)]
  #if len(root1.child) == 0:
    #if root1.father.father.name == 'MemberReference' or root1.father.father.name == 'BasicType':
    #  return [(root1.father.father, root2.father.father)]
    #if root1.father.name == 'operator':
    #  return [(root1.father, root2.father)]
  for i in range(len(root1.child)):
    ans.extend(getchangednode(root1.child[i], root2.child[i]))
  return ans
def getDiffNode(linenode1, linenode2, root, nls, m):
  global reslist
  global rules
  global onelist
  global rulelist
  global fatherlist
  global depthlist
  global copynode
  global rulead
  global fathername
  global n
  global isvalid
  #print(len(linenode1), len(linenode2))
  #for i in range(len(linenode1)):
  #  print(linenode1[i].getTreestr())
  #for i in range(len(linenode2)):
  #  print(linenode2[i].getTreestr())
  deletenode = []
  addnode = []
  node2id = {}
  #varnames = getLocVar(root)
  for i, x in enumerate(linenode1):
    node2id[str(x)] = i
  dic = {}
  dic2 = {}
  #linenode1 = list(reversed(linenode1))
  #linenode2 = list(reversed(linenode2))
  for i, x in enumerate(linenode1):
    hasSame = False
    #print('oooo')
    for j, y in enumerate(linenode2):
      if x == y and not y.expanded and not hasSame:
        y.expanded = True
        x.expanded = True
        dic[i] = j
        dic2[j] = i
        hasSame = True
        #print('ccccccc')
        continue
      if x == y and not y.expanded and hasSame:
        if x.getTreestr().strip() == 'StatementExpression expression MethodInvocation arguments MemberReference member pos_ter ^ ^ ^ ^ member next_ter ^ ^ ^ ^ ^':
          print(linenode1[i - 1].getTreestr())
        if i - 1 in dic and dic[i - 1] == j - 1:
          print('pppppp')
          print(x.getTreestr())
          hasSame = True
          linenode2[dic[i]].expanded = False
          y.expaned = True
          del dic2[dic[i]]
          dic[i] = j
          dic2[j] = i
          break
    if not hasSame:
      print('d', x.getTreestr())
      deletenode.append(x)
  '''tdic = {}
  for i, x in enumerate(linenode1):
    #hasSame = False
    for j, y in enumerate(linenode2):
      if x == y:
        tdic.setdefault(i, []).append(j)
    #if not hasSame:
    #  print(linenode1[i].getTreestr())
    #  deletenode.append(x)
  for i, x in enumerate(linenode1):
    if i not in tdic:
      deletenode.append(linenode1[i])
    elif i == 0 or tdic[i][0] == 0:
      dic[i] = tdic[i][0]
      dic2[tdic[i][0]] = i
      linenode2[tdic[i][0]].expanded = True
      linenode1[i].expanded = True
  for i, x in enumerate(linenode1):
    if i in tdic:
      bid = -1
      bscore = -1
      for yid in tdic[i]:
        ts = 0
        if i - 1 >= 0 and i - 1 in dic:
          if dic[i - 1] == yid - 1:
            ts += 1
        if i + 1 < len(linenode1) and i + 1 in dic:
          if dic[i + 1] == yid + 1:
            ts += 1
        if ts > bscore and ts != 0:
          bid = yid
          bscore = ts
      if bid == -1:
        deletenode.append(linenode1[yid])
      else:
        dic[i] = bid
        dic2[bid] = i
        assert(not linenode2[bid].expanded)
        linenode2[bid].expanded = True
        linenode1[i].expanded = True
  print('ps', len(deletenode))
  print(dic2)'''
  print('ps', len(deletenode))
  #assert(0)
  if len(deletenode) > 1:
    return
  preiddict = {}
  afteriddict = {}
  preid = -1
  for i in range(len(linenode1)):
    if linenode1[i].expanded:
      preid = i
    else:
      preiddict[i] = preid
  afterid = len(linenode1)
  dic[afterid] = len(linenode2)
  dic[-1] = -1
  for i in range(len(linenode1) - 1, -1, -1):
    if linenode1[i].expanded:
      afterid = i
    else:
      afteriddict[i] = afterid
  for i in range(len(linenode1)):
    if linenode1[i].expanded:
      continue
    else:
      preid = preiddict[i]
      afterid = afteriddict[i]
      preid2 = dic[preiddict[i]]
      afterid2 = dic[afteriddict[i]]
      print('ttt', preid, afterid, preid2, afterid2)
      if preid + 2 == afterid and preid2 + 2 == afterid2:
        troot = root
        if len(root.getTreestr().strip().split()) >= 1000:
          tmp = linenode1[preid + 1]
          if len(tmp.getTreestr().split()) >= 1000:
            continue
          #print(tmp.getTreestr())
          lasttmp = None
          while True:
            if len(tmp.getTreestr().split()) >= 1000:
              break
            lasttmp = tmp
            tmp = tmp.father
          #print(tmp.child)
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
              ansroot.child = [tmp.child[prenode]] + ansroot.child#.child.append(tmp.child[prenode])
              ansroot.num += tmp.child[prenode].getNum()
            if b:
              break
          troot = ansroot
        for k in range(preid + 1, afterid):
          print('--', linenode1[k].printTree(linenode1[k]))
          linenode1[k].expanded = True
          setProb(linenode1[k], 1)
        if preid >= 0:
          setProb(linenode1[preid], 3)
        if afterid < len(linenode1):
          setProb(linenode1[afterid], 4)
        '''if linenode1[preid + 1].name == 'condition':
          for k in range(preid2 + 1, afterid2):
            sys.stderr.write(linenode2[k].getTreestr() + "\n")
          sys.stderr.write(linenode1[preid + 1].getTreestr() + "\n")
          sys.stderr.write("-----------------------------\n")'''
        nls = troot.getTreestr().split()
        n = 0
        setid(troot)
        print('oo', troot.id)
        varnames = getLocVar(troot)
        fnum = -1
        vnum = -1
        vardic = {}
        vardic[m] = 'meth0'
        for x in varnames:
          if x[1].name == 'VariableDeclarator':
            vnum += 1
            vardic[x[0]] = 'loc' + str(vnum)
          else:
            fnum += 1
            vardic[x[0]] = 'par' + str(fnum)
        rulelist.append(rules['root -> modified'])
        fathername.append('root')
        fatherlist.append(-1)
        if ischanged(linenode1[preid + 1], linenode2[preid2 + 1]) and len(getchangednode(linenode1[preid + 1], linenode2[preid2 + 1])) <= 1:
          nodes = getchangednode(linenode1[preid + 1], linenode2[preid2 + 1])
          for x in nodes:
            rulelist.append(1000000 + x[0].id)
            fathername.append('root')
            fatherlist.append(-1)
            if x[0].name == 'BasicType' or x[0].name == 'operator':
              getRule(x[1], nls, len(rulelist) - 1, 0, 0, vardic, False, calvalid=False)
            else:
              getRule(x[1], nls, len(rulelist) - 1, 0, 0, vardic, calvalid=False)
            '''if x[0].father.name == 'operator':
              rule = 'operator -> ' + x[1].name
              rulelist.append(rules[rule])
              fathername.append('operator')
              fatherlist.append(len(rulelist) - 2)
            else:
              copyid = -1
              for i in range(len(varnames)):
                v = varnames[len(varnames) - 1 - i]
                if x[1] == v[0]:
                  copyid = 2000000 + v[1].id
                  break
              if copyid != -1:
                rulelist.append(copyid)
                fathername.append(x[0].father.name)
                fatherlist.append(len(rulelist) - 2)
              else:
                rule = x[0].father.name + " -> " + x[1]
                if rule not in rules:
                  rules[rule] = len(rules)
                  print(rule)
                  assert(0)
                rulelist.append(rules[rule])
                fathername.append(x[0].father.name)
                fatherlist.append(len(rulelist) - 2)'''
          rulelist.append(rules['root -> End'])
          fatherlist.append(-1)
          fathername.append('root')
          reslist.append({'input': root.printTreeWithVar(troot, vardic).strip().split(), 'rule':rulelist, 'problist':root.getTreeProb(troot), 'fatherlist':fatherlist, 'fathername':fathername, 'vardic':vardic})
          rulelist = []
          fathername = []
          fatherlist = []
          setProb(root, 2)  
          continue
        for k in range(preid2 + 1, afterid2):
          linenode2[k].expanded = True
          print('--2', linenode2[k].getTreestr())
          if linenode2[k].name == 'condition':
            rule = 'root -> ' + linenode2[k].father.name
          else:
            rule = 'root -> ' + linenode2[k].name
          if rule not in rules:
            rulenoter[rule] = 1
            rules[rule] = len(rules)
          rulelist.append(rules[rule])
          fathername.append('root')
          fatherlist.append(-1)
          if linenode2[k].name == 'condition':
            tmpnode = Node(linenode2[k].father.name, 0)
            tmpnode.child.append(linenode2[k])
            getRule(tmpnode, nls, len(rulelist) - 1, 0, 0, vardic)
          else:
            getRule(linenode2[k], nls, len(rulelist) - 1, 0, 0, vardic)
        if not isvalid:
          #assert(0)
          isvalid = True
          rulelist = []
          fathername = []
          fatherlist = []
          setProb(root, 2) 
          continue
        rulelist.append(rules['root -> End'])
        fatherlist.append(-1)
        fathername.append('root')
        '''if afterid2 == preid2 + 1:
          fatherlist.append(-1)
          fathername.append('root')
          rule = 'delete -> node'
          rulelist.append(rules[rule])'''
          #reslist.append({'input': ansroot.getTreestr().strip().split(), 'rule':rulelist, 'problist':root.getTreeProb(root), 'fatherlist':fatherlist, 'fathername':fathername})
        assert(len(root.printTree(troot).strip().split()) <= 1000)
        reslist.append({'input': root.printTreeWithVar(troot, vardic).strip().split(), 'rule':rulelist, 'problist':root.getTreeProb(troot), 'fatherlist':fatherlist, 'fathername':fathername})
        #print(reslist[-1])
        rulelist = []
        fathername = []
        fatherlist = []
        setProb(root, 2)  
        isvalid = True
        continue   
      else:
        continue   
  preiddict = {}
  afteriddict = {}
  preid = -1
  for i in range(len(linenode2)):
    if linenode2[i].expanded:
      preid = i
    else:
      preiddict[i] = preid
  afterid = len(linenode2)
  dic2[afterid] = len(linenode1)
  dic2[-1] = -1
  print(dic)
  for i in range(len(linenode2) - 1, -1, -1):
    if linenode2[i].expanded:
      afterid = i
    else:
      afteriddict[i] = afterid
  for i in range(len(linenode2)):
    #print(linenode2[i].getTreestr())
    if linenode2[i].expanded:
      continue
    else:
      print('dddddd', linenode2[i].getTreestr())
      preid = preiddict[i]
      afterid = afteriddict[i]
      if preiddict[i] not in dic2:
        #print(1)
        return
      preid2 = dic2[preiddict[i]]
      if afteriddict[i] not in dic2:
        #print(2)
        return
      afterid2 = dic2[afteriddict[i]]
      if preid2 + 1 != afterid2:
        if len(linenode1) > 16:
          print(linenode1[15].getTreestr())
          print(linenode1[15].getTreestr())
          print(linenode1[16].getTreestr())
        print(4, preid2, afterid2)
        continue
      troot = root
      if len(root.getTreestr().strip().split()) >= 1000:
        if preid2 >= 0:
          tmp = linenode1[preid2]
        elif afterid2 < len(linenode1):
          tmp = linenode1[afterid2]
        else:
          assert(0)
        if len(tmp.getTreestr().split()) >= 1000:
          continue
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
            ansroot.child = [tmp.child[prenode]] + ansroot.child#.child.append(tmp.child[prenode])
            ansroot.num += tmp.child[prenode].getNum()
          if b:
            break
        troot = ansroot
      nls = troot.getTreestr().split()
      n = 0
      setid(troot)
      print('oo', troot.id)
      varnames = getLocVar(troot)
      fnum = -1
      vnum = -1
      vardic = {}
      vardic[m] = 'meth0'
      for x in varnames:
        if x[1].name == 'VariableDeclarator':
          vnum += 1
          vardic[x[0]] = 'loc' + str(vnum)
        else:
          fnum += 1
          vardic[x[0]] = 'par' + str(fnum)
      if preid2 >= 0:
        print('ll', linenode1[preid2].getTreestr())
        setProb(linenode1[preid2], 3)
      if afterid2 < len(linenode1):
        print('ll', linenode1[afterid2].getTreestr())
        setProb(linenode1[afterid2], 1)
      if afterid2 + 1 < len(linenode1):
        setProb(linenode1[afterid2 + 1], 4)
      rulelist.append(rules['root -> add'])
      fathername.append('root')
      fatherlist.append(-1)
      for k in range(preid + 1, afterid):
        linenode2[k].expanded = True
        print('ll', linenode2[k].getTreestr())
        if linenode2[k].name == 'condition':
          rule = 'root -> ' + linenode2[k].father.name
        else:
          rule = 'root -> ' + linenode2[k].name
        if rule not in rules:
          rulenoter[rule] = 1
          rules[rule] = len(rules)
        rulelist.append(rules[rule])
        fathername.append('root')
        fatherlist.append(-1)
        if linenode2[k].name == 'condition':
          tmpnode = Node(linenode2[k].father.name, 0)
          tmpnode.child.append(linenode2[k])
          getRule(tmpnode, nls, len(rulelist) - 1, 0, 0, vardic)
        else:
          getRule(linenode2[k], nls, len(rulelist) - 1, 0, 0, vardic)
      if not isvalid:
        isvalid = True
        rulelist = []
        fathername = []
        fatherlist = []
        setProb(root, 2) 
        continue
      rulelist.append(rules['root -> End'])
      fatherlist.append(-1)
      fathername.append('root')
      assert(len(root.printTree(troot).strip().split()) <= 1000)
      reslist.append({'input': root.printTreeWithVar(troot, vardic).strip().split(), 'rule':rulelist, 'problist':root.getTreeProb(troot), 'fatherlist':fatherlist, 'fathername':fathername})
        #print(reslist[-1])
      rulelist = []
      fathername = []
      fatherlist = []
      setProb(root, 2)
lst = ['Chart-1', 'Chart-4', 'Chart-8', 'Chart-9', 'Chart-11', 'Chart-12', 'Chart-13', 'Chart-20', 'Chart-24', 'Chart-26', 'Closure-10', 'Closure-14', 'Closure-18', 'Closure-20', 'Closure-31', 'Closure-38', 'Closure-51', 'Closure-52', 'Closure-55', 'Closure-57', 'Closure-59', 'Closure-62', 'Closure-71', 'Closure-73', 'Closure-86', 'Closure-104', 'Closure-107', 'Closure-113', 'Closure-123', 'Closure-124', 'Closure-125', 'Closure-130', 'Closure-133', 'Lang-6', 'Lang-16', 'Lang-24', 'Lang-26', 'Lang-29', 'Lang-33', 'Lang-55', 'Lang-57', 'Lang-59', 'Lang-61', 'Math-2', 'Math-3', 'Math-5', 'Math-11', 'Math-27', 'Math-30', 'Math-32', 'Math-33', 'Math-34', 'Math-41', 'Math-48', 'Math-53', 'Math-57', 'Math-58', 'Math-59', 'Math-63', 'Math-69', 'Math-70', 'Math-73', 'Math-75', 'Math-80', 'Math-82', 'Math-85', 'Math-94', 'Math-96', 'Math-101', 'Math-105', 'Time-4', 'Time-15', 'Time-16', 'Time-19', 'Time-27', 'Lang-43', 'Math-50', 'Math-98', 'Time-7', 'Mockito-38']
if __name__ == '__main__':
  res = []
  tres = []
  #data = pickle.load(open('dataextra.pkl', 'rb'))#pickle.load(open('/data/zqh/data/detection_dataset/data.pkl', "rb"))
  #data = pickle.load(open('/home/zqh/dedata.pkl', "rb"))
  data = []#data * 100
  #data.extend(pickle.load(open('data2.pkl', "rb")))
  data.extend(pickle.load(open('data0.pkl', "rb")))
  #data.extend(pickle.load(open('/raid/zqh/copyhome/data1.pkl', "rb")))
  #data.extend(pickle.load(open('/data/zqh/data/detection_dataset/data.pkl', "rb")))
  print(data[0])
  assert(0)
  newdata = []
  v = int(sys.argv[1])
  data = data[v * 10000:v*10000 + 10000]#data[v * 10000:v*10000+10000]
  i = 0
  #wf = open('deresult.txt', 'w')
  for xs in tqdm(data):
      if 'oldtree' in xs:
        lines1 = xs['oldtree']
        lines2 = xs['newtree']
      else:
        lines1 = xs['old']
        lines2 = xs['new']
      #print(xs['old'])
      #print(xs['new'])
      #if i > 10:
      #  assert(0)
      i += 1
      #print(lines1)
      #print(lines2)
      #if i > 1000:
      #  break
      lines1, lines2 = lines2, lines1
      if lines1.strip().lower() == lines2.strip().lower():
        continue
      #if xs['id'] not in lst:
      #  continue
      tokens = lines1.strip().split()
      #print(tokens)
      #if len(tokens) > 1800:
      #  continue
      #print(x['old'])
      #print(x['new'])
      #print(i)
      root = Node(tokens[0], 0)
      currnode = root
      idx1 = 1
      for j, x in enumerate(tokens[1:]):
        if x != "^":
          if tokens[j + 2] == '^':
            #assert(0)
            x = x + "_ter"
          nnode = Node(x, idx1)
          idx1 += 1
          nnode.father = currnode
          currnode.child.append(nnode)
          currnode = nnode
        else:
          currnode = currnode.father
      root2 = Node(tokens[0], 0)
      currnode = root2
      tokens = lines2.strip().split()
      idx = 1
      for j, x in enumerate(tokens[1:]):
        if x != "^":
          if tokens[j + 2] == '^':
            x = x + "_ter"
          nnode = Node(x, idx)
          idx += 1
          nnode.father = currnode
          currnode.child.append(nnode)
          currnode = nnode
        else:
          currnode = currnode.father
      print(lines1)
      print(len(tres))
      #print(stringfyNode(root))
      print("------------\n")
      print(lines2)
      #print(stringfyNode(root2))
      print("&&&&&&&&&&&&&&\n")
      linenode1 = getLineNode(root, "")
      linenode2 = getLineNode(root2, "")
      if len(linenode1) == 0 or len(linenode2) == 0:
        continue
      #if linenode1[0].name == 'parameters' and linenode1[0].getTreestr() != linenode2[0].getTreestr():
      #  continue
      #print('**********')
      setProb(root, 2)
      olen = len(reslist)
      m = 'None'
      for x in root.child:
        if x.name == 'name':
          m = x.child[0].name
      getDiffNode(linenode1, linenode2, root, root.printTree(root).strip().split(), m)
      #print(stringfyNode(root))
      #print(stringfyNode(root2))
      if len(reslist) - olen == 1:
        #wf.write(xs['id'] + "\n")
        #wf.write("\n".join(xs['df']) + "\n")
        tres.append(reslist[-1])
        newdata.append(xs)
        '''rrdict = {}
        for x in rules:
          rrdict[rules[x]] = x
        for x in [tres[-1]]:
          print(x['input'])
          print(x['rule'])
          tmp = []
          for s in x['input']:
            if s != '^':
              tmp.append(s) 
          for x in x['rule']:
            if x < 2000000:
              print(rrdict[x], end=',')
            else:
              i = x - 2000000
              print('copy-' + tmp[i], end=',')
          print()'''
      #else:
        #print(len(reslist) - olen)
        #print("\n".join(xs['df']), xs['id'])
        #print(len(lines1), len(lines2))
        #if xs['id'] != 'Math-50':
        #  assert(0)
      #print(reslist)
      #print('----------')
      #computedist(root, root2, 2, root.printTree(root).strip().split())
      if i <= -5:
        assert(0)
      #if len(rulelist) == 0:
      ##  continue
      #res.append({'input': root.printTree(root).strip().split(), 'rule':rulelist, 'problist':root.getTreeProb(root), 'fatherlist':fatherlist, 'fathername':fathername, 'depth':depthlist})
      #print(idx1, res[-1]['rule'], len(res[-1]['input']))
      #print(action)
      #for x in res[-1]['rule']:
      #  if x >= 2000000:
      #    ind = x - 2000000
      #    assert(ind < idx1)
      rulelist = []
      fatherlist = []
      fathername = []
      depthlist = []
      copynode = {}
      hascopy = {}
      action = []
      #print(root.printprob())
      #assert(0)
      '''print(lines1.strip())
      print(lines2.strip())
      print(res[-1]['rule'])
      rrdict = {}
      for x in rules:
        rrdict[rules[x]] = x
      for x in res[-1]['rule']:
        if x < 2000000:
          print(rrdict[x])
        else:
          print(x - 2000000)
          print('copy' + res[-1]['input'][x - 2000000])'''
      #print(res[-1])
      #exit(0)
  rrdict = {}
  for x in rules:
    rrdict[rules[x]] = x
  for p, x in enumerate(tres):
    print(x['input'])
    print(x['rule'])
    print(p)
    tmp = []
    for s in x['input']:
      if s != '^':
        tmp.append(s) 
    for x in x['rule']:
      if x < 1000000:
        print(rrdict[x], end=',')
      else:
        if x >= 2000000:
          i = x - 2000000
        else:
          i = x - 1000000
        print('copy-' + tmp[i], end=',')
    print()
  #print(tres[0])
  print(rules)
  open('rulead%d.pkl'%v, "wb").write(pickle.dumps(rulead))
  open('rule2.pkl', "wb").write(pickle.dumps(rules))
  open('process_datacopy%d.pkl' % v, "wb").write(pickle.dumps(tres))
  #open('dataour.pkl', "wb").write(pickle.dumps(newdata))
  print(len(tres))
  print(len(lst))
  exit(0)