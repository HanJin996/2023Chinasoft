# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import torch.nn.functional as F
import torch, csv, gc, warnings, os
from torch import cuda
from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler
# from loader import GeneratorDataset
import my_loader
import logging
logging.basicConfig(level=logging.ERROR)


class JavaDelimiter:
    @property
    def varargs(self):
        return "..."

    @property
    def rightBrackets(self):
        return "]"

    @property
    def leftBrackets(self):
        return "["

    @property
    def biggerThan(self):
        return ">"
    

def isDelimiter(token):
    return not token.upper().isupper()


# 将预测的sequence(tokens)转换成java源代码的格式
def toJavaSourceCode(prediction):
    tokens = prediction.strip().split(" ")
    tokens = [token.replace("<seq2seq4repair_space>", " ") for token in tokens]
    codeLine = ""
    delimiter = JavaDelimiter()
    for i in range(len(tokens)):
        if(tokens[i] == "<unk>"):
            return ""
        if(i+1 < len(tokens)):
            # DEL = delimiters
            # ... = method_referece
            # STR = token with alphabet in it
            if(not isDelimiter(tokens[i])):
                if(not isDelimiter(tokens[i+1])): # STR (i) + STR (i+1)
                    codeLine = codeLine+tokens[i]+" "
                else: # STR(i) + DEL(i+1)
                    codeLine = codeLine+tokens[i]
            else:
                if(tokens[i] == delimiter.varargs): # ... (i) + ANY (i+1)
                    codeLine = codeLine+tokens[i]+" "
                elif(tokens[i] == delimiter.biggerThan): # > (i) + ANY(i+1)
                    codeLine = codeLine+tokens[i]+" "
                elif(tokens[i] == delimiter.rightBrackets and i > 0):
                    if(tokens[i-1] == delimiter.leftBrackets): # [ (i-1) + ] (i)
                        codeLine = codeLine+tokens[i]+" "
                    else: # DEL not([) (i-1) + ] (i)
                        codeLine = codeLine+tokens[i]
                else: # DEL not(... or ]) (i) + ANY
                    codeLine = codeLine+tokens[i]
        else:
            codeLine = codeLine+tokens[i]
    return codeLine

# 向tmp_path路径下写入java源代码格式的预测sequence的txt文件
def gen_fix_txt(tokenizer, model, device, loader, num_generated_seq, tmp_path):
    model.eval()
    with torch.no_grad():
        for _, data in enumerate(loader, 0):
            gc.collect()
            torch.cuda.empty_cache()
            source_ids = data['source_ids'].to(device, dtype = torch.long)
            source_mask = data['source_mask'].to(device, dtype = torch.long)
            bugid = ''.join(data['bugid'])
            generated_ids = model.generate(
                input_ids=source_ids,
                attention_mask=source_mask, 
                max_length=100, 
                num_beams=num_generated_seq,
                length_penalty=1.0, 
                early_stopping=True,
                num_return_sequences=num_generated_seq, # 作为参数传递进来，要求模型返回生成序列的数量
                num_beam_groups=1,
                output_scores=True
                )
            preds = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]
            # 将模型生成的sequence转换成java源代码的句法格式
            preds_toJavaSourceCode = [] # 这是对于一个bug生成的num_generated_seq条补丁
            for pred in preds:
                    pred = pred.replace('> =','>=').replace('< =','<=').replace('= =','==').replace('! =','!=')
                    pred = toJavaSourceCode(pred)
                    preds_toJavaSourceCode.append(pred)
            # 生成用于暂存txt格式的补丁集合的文件夹
            if os.path.exists(os.path.join(tmp_path, bugid)): continue
            os.makedirs(os.path.join(tmp_path, bugid))
            written_file = os.path.join(tmp_path, bugid, 'predictions_JavaSource.txt')
            with open(written_file, 'w') as w:
                for pred_toJavaSourceCode in set(preds_toJavaSourceCode):
                    w.write(pred_toJavaSourceCode + '\n')

# 对于生成的predictions_JavaSource.txt文件，将其转化成*.java形式的patches
def gen_patches(predictions_txt_file, buggy_file, buggy_line_idx, output_path):
    predictions = open(predictions_txt_file, 'r').readlines() # predictions_JavaSource.txt
    buggy_file_lines = open(buggy_file, 'r').readlines() # check out的bug文件
    buggy_line_idx = int(buggy_line_idx)
    if (len(buggy_file_lines) < buggy_line_idx):
        print('wrong file or index!')
        return
    buggy_line = buggy_file_lines[buggy_line_idx-1] # 准备被替换掉的错误行
    white_space_before_buggy_line = buggy_line[0:buggy_line.find(buggy_line.lstrip())]
    bugid = os.path.basename(os.path.dirname(predictions_txt_file))
    for i in range(len(predictions)):
        output_file = os.path.join(output_path, bugid, str(i+1), os.path.basename(buggy_file))
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
    print('start main()!')
    SEED = 42 # random seed (default: 42)
    MAX_LEN = 512
    SUMMARY_LEN = 64
    torch.manual_seed(SEED) # set pytorch random seed
    np.random.seed(SEED) # set numpy random seed
    torch.backends.cudnn.deterministic = True
    torch.cuda.empty_cache()

    # tokenzier
    tokenizer = T5Tokenizer.from_pretrained('./model/RewardRepair_new')
    tokenizer.add_tokens(['{', '}','<','^'])
    print('tokenizer init done!')

    # model
    model = T5ForConditionalGeneration.from_pretrained('./model/RewardRepair_new')
    device = 'cuda' if cuda.is_available() else 'cpu'
    model = model.to(device)
    print('model init done!')

    # prepare data
    params = {
    'batch_size': 1,
    'shuffle': False,
    'num_workers': 2
    }
    csv_file1 = r'./MyCode/MyData/Defects4JV1.2.csv'
    csv_file2 = r'./MyCode/MyData/Defects4JV2.0.csv'
    input_dataframe1 = pd.read_csv(csv_file1, encoding='latin-1', delimiter='\t')
    input_dataframe2 = pd.read_csv(csv_file2, encoding='latin-1', delimiter='\t')
    # print(input_dataframe1.head())
    # print(input_dataframe2.head())
    input_dataframe = pd.concat([input_dataframe1, input_dataframe2], ignore_index=True)
    input_dataframe = input_dataframe[['bug','buggy','patch']]
    input_set = my_loader.GeneratorDataset(input_dataframe, tokenizer, MAX_LEN, SUMMARY_LEN)
    input_loader = DataLoader(input_set, **params) # 读取了D4J1.2和D4J2.0
    print('preparing data done!')

    # generate prediction txt file(predictions_JavaSource.txt) & generate patches
    num_generated_seq = 200
    tmp_path = r'./MyCode/MyData/tmp'
    # gen_fix_txt(
    #     tokenizer=tokenizer, 
    #     model=model, 
    #     device=device, 
    #     loader=input_loader, 
    #     num_generated_seq=num_generated_seq,
    #     tmp_path=tmp_path
    # )
    print('gengrate txt done!')
    output_path = r'./MyCode/MyData/results_new' # 参数4
    for bugid in os.listdir(tmp_path):
        predictions_txt_file = os.path.join(tmp_path, bugid, 'predictions_JavaSource.txt') # 参数1
        Metas = open(r'./MyCode/MyData/Defects4JMeta.csv', 'r').readlines()
        open(r'./MyCode/MyData/Defects4JMeta.csv', 'r').close()
        input_dataframe1 = pd.read_csv(csv_file1, encoding='latin-1', delimiter='\t')
        input_dataframe2 = pd.read_csv(csv_file2, encoding='latin-1', delimiter='\t')
        input_dataframe = pd.concat([input_dataframe1, input_dataframe2], ignore_index=True)
        for i, id in enumerate(input_dataframe['bug'].tolist()):
            if id == bugid:
                buggy_line_idx = (input_dataframe['lineNo'].tolist())[i] # 参数3
                break
        for meta in Metas:
            # if ',' in meta: continue
            if bugid == meta.split('\t')[1]:
                sub_buggy_file = meta.split('\t')[2]
                break
        buggy_file = os.path.join('./MyCode/MyData/Defects4J_projects', bugid, sub_buggy_file) # 参数2
        if not os.path.exists(buggy_file): continue
        print("start to gengrate {bugid}'s patches".format(bugid=bugid))
        print(buggy_line_idx)
        gen_patches(
            predictions_txt_file=predictions_txt_file,
            buggy_file=buggy_file,
            buggy_line_idx=buggy_line_idx,
            output_path=output_path
        )
    print('gengrate patches done!')




# 在/home/lqy/Workspace/rewardrepair/MyCode/MyData/results下生成补丁
if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    device = 'cuda' if cuda.is_available() else 'cpu'
    print(torch.__version__)
    gc.collect()
    torch.cuda.empty_cache()
    main()

