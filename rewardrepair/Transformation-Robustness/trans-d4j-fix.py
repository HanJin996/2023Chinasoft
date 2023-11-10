# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import torch.nn.functional as F
import torch, csv, gc, warnings, loader, os
from torch import cuda
from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler


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


# 对于每一个bug，生成num_generate_seq个候选patch，结果写入特定目录下的predictions_JavaSource.txt文件中
def trans_d4j_generate_txt(tokenizer, model, device, loader, num_generated_seq, trans_way):
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
                num_beams=num_generated_seq, # 作为参数传递进来，要求模型生成序列的数量
                length_penalty=1.0, 
                early_stopping=True,
                num_return_sequences=num_generated_seq, # 作为参数传递进来，要求模型生成序列的数量
                num_beam_groups=1,
                output_scores=True
                )
            preds = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]
            preds_toJavaSourceCode = []
            for pred in preds:
                    pred = pred.replace('> =','>=').replace('< =','<=').replace('= =','==').replace('! =','!=')
                    pred = toJavaSourceCode(pred)
                    preds_toJavaSourceCode.append(pred)
            os.makedirs('/home/lqy/Workspace/rewardrepair/MyCode/MyData/trans_tmp/{trans_way}/{bugid}'.format(trans_way=trans_way, bugid=bugid))
            written_path = r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/trans_tmp/{trans_way}/{bugid}/predictions_JavaSource.txt'.format(trans_way=trans_way, bugid=bugid)
            written_file = open(written_path, 'a')
            for pred_toJavaSourceCode in set(preds_toJavaSourceCode):
                written_file.write(pred_toJavaSourceCode + '\n')
            written_file.close()


# 对于生成的predictions_JavaSource.txt文件，将其转化至/results下的patches
def trans_d4j_generate_patches(buggy_file_path, buggy_line_idx, prediction_path, output_path):
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
    SEED = 42 # random seed (default: 42)
    MAX_LEN = 512
    SUMMARY_LEN = 64
    torch.manual_seed(SEED) # set pytorch random seed
    np.random.seed(SEED) # set numpy random seed
    torch.backends.cudnn.deterministic = True
    torch.cuda.empty_cache()

    # tokenzier
    tokenizer = T5Tokenizer.from_pretrained('./model/RewardRepair')
    tokenizer.add_tokens(['{', '}','<','^'])

    # model
    model = T5ForConditionalGeneration.from_pretrained('./model/RewardRepair')
    device = 'cuda' if cuda.is_available() else 'cpu'
    model = model.to(device)

    # prepare data
    trans_list = ['ReorderCondition', 'VariableRenaming']
    for trans_way in trans_list:
        input_dataframe = pd.read_csv(r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/trans-{trans_way}-d4j.csv'.format(trans_way=trans_way), encoding='latin-1', delimiter=',')
        input_dataframe = input_dataframe[['bugid','buggy','patch']]
        input_set = loader.GeneratorDataset(input_dataframe, tokenizer, MAX_LEN, SUMMARY_LEN)
        params = {
        'batch_size': 1,
        'shuffle': False,
        'num_workers': 2
        }
        input_loader = DataLoader(input_set, **params)

        # generate prediction txt file(predictions_JavaSource.txt)
        num_generated_seq = 50
        trans_d4j_generate_txt(
        tokenizer=tokenizer, 
        model=model, 
        device=device, 
        loader=input_loader, 
        num_generated_seq=num_generated_seq,
        trans_way=trans_way
        )
    
        # generate patches in /home/lqy/MyProject/rewardrepair/RewardRepair_data/results...
        path = r'/home/lqy/Workspace/rewardrepair/MyCode/MyData/trans_tmp'
        trans_list = ['ReorderCondition', 'VariableRenaming']
        for trans_way in trans_list:
            buggy_folder_list = os.listdir(os.path.join(path, trans_way))
            for buggy_folder in buggy_folder_list:
                for buggy_folder in os.listdir(os.path.join(path, trans_way, buggy_folder)):
                    prediction_path = os.path.join(path, buggy_folder, 'predictions_JavaSource.txt') # transd4j_generatePatches的第3个参数
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
                            # project_sub_path_ = csv_item1.split('\t')[2]
                            project_sub_path = csv_item1.split('\t')[2]
                            project_idx = csv_item1.split('\t')[3]
                            break
            if project_sub_path == '' or project_idx == '' or ',' in project_sub_path:
                print(buggy_project)
                continue
            buggy_file_path = os.path.join(r'/home/lqy/Workspace/rewardrepair/Coconut_Defects4J_projects', buggy_project, project_sub_path) # transd4j_generatePatches的第1个参数
            buggy_line_idx = project_idx # transd4j_generatePatches的第2个参数
            output_path = os.path.join(r'/home/lqy/Workspace/rewardrepair/Coconut_results', buggy_folder)# transd4j_generatePatches的第4个参数
            trans_d4j_generate_patches(
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
    # 结束后，会在/home/lqy/Workspace/rewardrepair/MyCode/MyData/trans_results下生成每个transformation对应的patches


