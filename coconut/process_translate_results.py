import re, codecs, os

def get_strings_numbers(string):
    # FIXME Does not work for s.append(',').append(',') return [',', ').append(', ',']
    matches1 = re.findall(r'(?<=\")(.*?)(?=\")', string)
    matches2 = re.findall(r"(?<=\')(.*?)(?=\')", string)
    strings = matches1 + matches2
    numbers = re.findall(r'\d+', string)
    return strings, numbers

def token2statement(token_list, numbers, strings):
    flag_string_statements = 0
    ### if strings and numbers format of statement is [n1s1, n1s2, n1s3, n2s1, n2,s2, ...]
    if "$STRING$" in token_list and "$NUMBER$" in token_list:
        statements = [""] * len(strings) * len(numbers)
        flag_string_statements = 3
    elif "$NUMBER$" in token_list:
        statements = [""] * len(numbers)
        flag_string_statements = 2
    elif "$STRING$" in token_list:
        statements = [""] * len(strings)
        flag_string_statements = 1
    else:
        statements = [""]
    for i, token in enumerate(token_list):
        if i < len(token_list) - 1:
            # if token_list[i] == "or" or "and":
            #    for s in range(0, len(statements)):
            #        statements[s] += " " + token + " "
            if token_list[i] == "return":
                if token_list[i + 1].isdigit() or token_list[i + 1] == "$NUMBER$":
                    for s in range(0, len(statements)):
                        statements[s] += token + " "
                elif token_list[i + 1] == "CaMeL":
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1] == ".":  # no space
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1] == "(":  # Actually it does not seem to be needed.
                    for s in range(0, len(statements)):
                        statements[s] += " " + token
                elif token_list[i + 1] == "_":  # no space
                    for s in range(0, len(statements)):
                        statements[s] += token
                else:
                    for s in range(0, len(statements)):
                        statements[s] += token + " "

            elif token_list[i] == "$STRING$":
                if flag_string_statements == 3:
                    for s in range(0, len(statements)):
                        if "'" not in strings[s % len(strings)]:
                            statements[s] += "'" + strings[s % len(strings)] + "'"
                        else:
                            statements[s] += '"' + strings[s % len(strings)] + '"'
                elif flag_string_statements == 1:
                    for s in range(0, len(statements)):
                        if "'" not in strings[s]:
                            statements[s] += "'" + strings[s] + "'"
                        else:
                            statements[s] += '"' + strings[s] + '"'
                else:
                    for s in range(0, len(statements)):
                        statements[s] += "'DEFAULT'"

            elif token_list[i] == "$NUMBER$":
                if flag_string_statements == 3:
                    count = 0
                    # print("len_statemnt", len(statements))
                    for s in range(0, len(numbers)):
                        # print("s: ", len(numbers))
                        # print(len(statements))
                        # print(len(numbers)* len(strings) - 1 )
                        for stringlen in range(s, s + len(strings)):
                            statements[count] += numbers[s]
                            count += 1
                            # print("Count: ", count)

                elif flag_string_statements == 2:
                    for s in range(0, len(statements)):
                        statements[s] += numbers[s]
                else:
                    # use default number 2 (0 and 1 are specific tokens)
                    statements[s] += 2
            elif token_list[i] == "CaMeL":  # no space
                pass
            elif token_list[i] == '*':
                for s in range(0, len(statements)):
                    statements[s] += token
            elif token_list[i] == ".":  # no space
                for s in range(0, len(statements)):
                    statements[s] += token
            elif token_list[i].isdigit():  # no space in general
                if token_list[i + 1] == 'or' or token_list[i + 1] == 'and':
                    for s in range(0, len(statements)):
                        statements[s] += token + ' '
                else:
                    for s in range(0, len(statements)):
                        statements[s] += token

            elif token_list[i] == "_":  # no space
                for s in range(0, len(statements)):
                    statements[s] += token

            else:  # Default case"
                if token_list[i + 1] == "CaMeL":  # no space
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1] == ".":  # no space
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1] == "(":  # Actually it does not seem to be needed.
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1] == "_":  # no space
                    for s in range(0, len(statements)):
                        statements[s] += token
                elif token_list[i + 1].isdigit() or token_list[i + 1] == "$NUMBER$":  # no space
                    if token_list[i + 1] == 'or' or token_list[i + 1] == 'and':
                        for s in range(0, len(statements)):
                            statements[s] += token + " "
                    else:
                        for s in range(0, len(statements)):
                            statements[s] += token
                else:
                    for s in range(0, len(statements)):
                        statements[s] += token + " "
        else:  # no space after the last statement
            if token_list[i] == "$STRING$":
                if flag_string_statements == 3:
                    for s in range(0, len(statements)):
                        if "'" not in strings[s % len(strings)]:
                            statements[s] += "'" + strings[s % len(strings)] + "'"
                        else:
                            statements[s] += '"' + strings[s % len(strings)] + '"'
                elif flag_string_statements == 1:
                    for s in range(0, len(statements)):
                        if "'" not in strings[s]:
                            statements[s] += "'" + strings[s] + "'"
                        else:
                            statements[s] += '"' + strings[s] + '"'
                else:
                    for s in range(0, len(statements)):
                        statements[s] += "'DEFAULT'"
            elif token_list[i] == "$NUMBER$":
                if flag_string_statements == 3:
                    count = 0
                    for s in range(0, len(numbers)):
                        for stringlen in range(s, s + len(strings)):
                            statements[count] += numbers[s]
                            count += 1
                elif flag_string_statements == 2:
                    for s in range(0, len(statements)):
                        statements[s] += numbers[s]
                else:
                    # use default number 2 (0 and 1 are specific tokens)
                    statements[s] += 2
            elif token_list[i] == "CaMeL":  # no space
                pass
            else:
                for s in range(0, len(statements)):
                    statements[s] += token
    return statements

def readF2L(filepath):
    lines=[]
    with open(filepath,'r',encoding='utf-8')as f:
        for line in f:
            lines.append(line.strip())
        f.close()
    return lines

def Recovery_CoCoNut_one(buggy_str, pred_str):
    strings, numbers = get_strings_numbers(buggy_str)
    recovery_tokens = pred_str.split()
    recovery_str = token2statement(recovery_tokens, numbers, strings)
    # print(recovery_str)
    if len(recovery_str) == 0:
        recovery_str = [pred_str]
    return recovery_str[0]

def Prepare_CoCoNut_patches(beam_size, id_file, pred_file, output_file):
    ids = readF2L(id_file)
    preds = readF2L(pred_file)
    assert len(ids) * (beam_size + 2) == len(preds)
    with open(output_file, 'w') as w:
        for pred in preds:
            if pred.startswith('S-') or pred.startswith('T-'):
                # w.write(pred)
                continue
            else:
                pred_id = pred.split('\t')[0].replace('H-', '')
                # pred_id += 1
                file_name = ids[int(pred_id)].replace('\n', '')
                buggy_line = codecs.open(os.path.join('/home/lqy/Workspace/NPR4J/CoConutMyData/buggy_lines',file_name+".txt")).read().strip()
                recover_pred = Recovery_CoCoNut_one(buggy_line, pred)
                w.write(recover_pred + '\n')

def process2valid_style(beam_size, recover_preds_file, id_file, tmp_folder):
    ids = readF2L(id_file)
    preds = readF2L(recover_preds_file)
    assert len(ids)*beam_size == len(preds)
    for pred in preds:
        pred = pred.replace('\t', ' ')
        pred_id = pred.split(' ')[0].replace('H-', '')
        folder_name = ids[int(pred_id)].replace('\n', '')
        if not os.path.exists(os.path.join(tmp_folder, folder_name)):
            os.makedirs(os.path.join(tmp_folder, folder_name))
        a = open(os.path.join(tmp_folder, folder_name, 'predictions_JavaSource.txt'), 'a')
        a.write(pred.replace(pred.split(' ')[0], '').replace(pred.split(' ')[1], '').strip() + '\n')
        a.close()
    
if __name__ == '__main__':
    # Prepare_CoCoNut_patches(
    #     beam_size=300,
    #     id_file='./CoConutMyData/ids_f.txt',
    #     pred_file='./CoConutMyData/outputs/coconut_10/coconut_10_bm300_trans-d4j.pred',
    #     output_file='./CoConutMyData/outputs/coconut_10/recover_preds.txt'
    # )
    process2valid_style(
        beam_size=300,
        recover_preds_file='./CoConutMyData/outputs/coconut_10/recover_preds.txt',
        id_file='./CoConutMyData/ids_f.txt',
        tmp_folder='./CoConutMyData/final_results_tmp'
    )
