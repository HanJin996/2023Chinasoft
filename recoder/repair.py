import sys
python_path = "/opt/conda/lib/python3.6/site-packages"
sys.path.append(python_path)
import json
import os
from Searchnode import Node
from stringfycode import stringfyRoot
import subprocess
import time
import signal
import traceback
import javalang


def convert_time_to_str(time):
    #时间数字转化成字符串，不够10的前面补个0
    if (time < 10):
        time = '0' + str(time)
    else:
        time=str(time)
    return time
def sec_to_data(y):
    h=int(y//3600 % 24)
    d = int(y // 86400)
    m =int((y % 3600) // 60)
    s = round(y % 60,2)
    h=convert_time_to_str(h)
    m=convert_time_to_str(m)
    s=convert_time_to_str(s)
    d=convert_time_to_str(d)
    return d + ":" + h + ":" + m + ":" + s
def getroottree2(tokens, isex=False):
    root = Node(tokens[0], 0)
    currnode = root
    idx = 1
    for x in tokens[1:]:
        if x != "^":
            nnode = Node(x, idx)
            nnode.father = currnode
            currnode.child.append(nnode)
            currnode = nnode
            idx += 1
        else:
            currnode = currnode.father
    return root
starttime = time.time()
timelst = []

# the range of the bug to fix
prlist = ['Chart', 'Closure', 'Lang', 'Math', 'Time', 'Mockito', 'Cli', 'Codec', 'Collections', 'Compress', 'Csv', 'JacksonCore', 'JacksonDatabind', 'JacksonXml', 'Jsoup', 'JxPath']
ids = [list(range(1, 27)), list(range(1, 134)), list(range(1, 66)), list(range(1, 107)), list(range(1, 28)), list(range(1, 39)), list(range(1, 41)), list(range(1, 19)), list(range(25, 29)), list(range(1, 48)), list(range(1, 17)), list(range(1, 27)), list(range(1, 58)), list(range(1, 7)), list(range(1, 94)), list(range(1, 23))]

for i, xss in enumerate(prlist):
    for idx in ids[i]:
        idss = xss + "-" + str(idx)
        print(idss)
        x = idss
        wf = open('patches/' + x + "patch.txt", 'a')
        patches = json.load(open("patch/%s.json"%x, 'r'))
        curride = ""
        proj = x.split("-")[0]
        bid = x.split("-")[1]
        x = x.replace("-", "")
        if os.path.exists('buggy%s' % x):
            os.system('rm -rf buggy%s' % x)
        os.system("defects4j checkout -p %s -v %s -w buggy%s" % (proj, bid + 'b', x))
        xsss = x
        testmethods = os.popen('defects4j export -w buggy%s -p tests.trigger'%x).readlines()
        for i, p in enumerate(patches):
            if i < 0:
                continue
            endtime = time.time()
            if endtime - starttime > 18000:
                open('timeg.txt', 'a').write(xsss + "\t" + sec_to_data(endtime - starttime) + "\n")
                exit(0)
            iden = x + str(p['line']) + p['filename'].replace("/", "")[::-1]
            if iden != curride:
                if curride != "":
                    os.system('rm -rf buggy%s'%x)
            os.system('defects4j checkout -p %s -v %s -w buggy%s' % (proj, bid + 'b', x))
            curride = iden
            try:
                root = getroottree2(p['code'].split())
            except:
                continue
            mode = p['mode']
            precode = p['precode']
            aftercode = p['aftercode']        
            oldcode = p['oldcode']
            if '-1' in oldcode:
                continue
            if mode == 1:
                aftercode = oldcode + aftercode
            lines = aftercode.splitlines()
            if 'throw' in lines[0] and mode == 1:
                for s, l in enumerate(lines):
                    if 'throw' in l or l.strip() == "}":
                        precode += l + "\n"
                    else:
                        break
                aftercode = "\n".join(lines[s:])
            if lines[0].strip() == '}' and mode == 1:
                precode += lines[0] + "\n"
                aftercode = "\n".join(lines[1:])
            try:
                code = stringfyRoot(root, False, mode)
            except:
                continue
            if '<string>' in code:
                if '\'.\'' in oldcode:
                    code = code.replace("<string>", '"."')
                elif '\'-\'' in oldcode:
                    code = code.replace("<string>", '"-"')
                elif '\"class\"' in oldcode:
                    code = code.replace("<string>", '"class"')
                else:
                    code = code.replace("<string>", "\"null\"")
            if len(root.child) > 0 and root.child[0].name == 'condition' and mode == 0:
                code = 'if' + code + "{"
            if code == "" and 'for' in oldcode and mode == 0:
                code = oldcode + "if(0!=1)break;"
            filepath2 = 'buggy%s'%x + p['filename'][5:]
            lnum = 0
            for l in code.splitlines():
                if l.strip() != "":
                    lnum += 1
                else:
                    continue
            if mode == 1 and len(precode.splitlines()) > 0 and 'case' in precode.splitlines()[-1]:
                lines = precode.splitlines()
                for i in range(len(lines) - 2, 0, -1):
                    if lines[i].strip() == '}':
                        break
                precode = "\n".join(lines[:i])
                aftercode = "\n".join(lines[i:]) + "\n" + aftercode
            if lnum == 1 and 'if' in code and mode == 1:
                if p['isa']:
                    code = code.replace("if", 'while')
                if len(precode.splitlines()) > 0 and 'for' in precode.splitlines()[-1]:
                    code = code + 'continue;\n}\n'    
                else:
                    afterlines = aftercode.splitlines()
                    lnum = 0
                    rnum = 0
                    ps = p
                    for p, y in enumerate(afterlines):
                        if ps['isa'] and y.strip() != '':
                            aftercode = "\n".join(afterlines[:p + 1] + ['}'] + afterlines[p + 1:])
                            break
                        if '{' in y:
                            lnum += 1
                        if '}' in y:
                            if lnum == 0:
                                aftercode = "\n".join(afterlines[:p] + ['}'] + afterlines[p:])
                                break
                            lnum -= 1
                print(code)
                tmpcode = precode + "\n" + code + aftercode
                tokens = javalang.tokenizer.tokenize(tmpcode)
                parser = javalang.parser.Parser(tokens)
            else:
                print(code)
                tmpcode = precode + "\n" + code + aftercode
                tokens = javalang.tokenizer.tokenize(tmpcode)
                parser = javalang.parser.Parser(tokens)
            try:
                tree = parser.parse()
            except:
                continue
            print(filepath2)
            open(filepath2, "w").write(tmpcode)
            bugg = False
            for t in testmethods:
                cmd = 'defects4j test -w buggy%s/ -t %s' % (x, t.strip())
                Returncode = ""
                child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1, start_new_session=True)
                while_begin = time.time() 
                while True:                
                    Flag = child.poll()
                    if  Flag == 0:
                        Returncode = child.stdout.readlines()
                        break
                    elif Flag != 0 and Flag is not None:
                        bugg = True
                        break
                    elif time.time() - while_begin > 15:
                        print('ppp')
                        os.killpg(os.getpgid(child.pid), signal.SIGTERM)
                        bugg = True
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
                print('s')
                cmd = 'defects4j test -w buggy%s/' % (x)
                Returncode = ""
                child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1, start_new_session=True)
                while_begin = time.time() 
                while True:                
                    Flag = child.poll()
                    if  Flag == 0:
                        Returncode = child.stdout.readlines()
                        break
                    elif Flag != 0 and Flag is not None:
                        bugg = True
                        break
                    elif time.time() - while_begin > 180:
                        os.killpg(os.getpgid(child.pid), signal.SIGTERM)
                        bugg = True
                        break
                    else:
                        time.sleep(1)
                log = Returncode
                print(log)
                if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
                    print('success')
                    endtime = time.time()
                    open('timeg.txt', 'a').write(xsss + "\t" + sec_to_data(endtime - starttime) + "\n")
                    wf.write(curride + "\n")
                    wf.write("-" + oldcode + "\n")
                    wf.write("+" +  code + "\n")
                    wf.write("🚀\n")
                    wf.flush()    
                    if os.path.exists('buggy%s' % x):
                        os.system('rm -rf buggy%s' % x)
                    exit(0)
endtime = time.time()

