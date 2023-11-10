import codecs
import json
import os

RERANK_DIR = os.path.abspath(__file__)[: os.path.abspath(__file__).rindex('/') + 1]

# using for transformation d4j
def read_defects4j_meta(meta_path):
    fp = codecs.open(meta_path, 'r', 'utf-8')
    meta = []
    for l in fp.readlines():
        proj, bug_id, path, start_loc, end_loc = l.replace('\r\n', '').split('\t')
        meta.append([
            proj + '_' + bug_id, path, start_loc, str(int(end_loc) + 1)
        ])
    return meta


def read_quixbugs_meta(meta_path):
    fp = codecs.open(meta_path, 'r', 'utf-8')
    meta = []
    for l in fp.readlines():
        proj, loc = l.strip().split('\t')
        if '-' in loc:
            start_loc, end_loc = loc.split('-')
            start_loc = int(start_loc)
            end_loc = int(end_loc)
        else:
            start_loc, end_loc = int(loc), int(loc) + 1
        meta.append([
            proj, str(start_loc), str(end_loc)
        ])
    return meta


def read_hypo(hypo_path):
    fp = codecs.open(hypo_path, 'r', 'utf-8')
    hypo = {}
    for l in fp.readlines():
        l = l.strip().split()
        if l[0][:2] == 'S-':
            id = int(l[0][2:])
            src = ' '.join(l[1:]).strip()
            src = src.replace('@@ ', '')
            hypo[id] = {'src': src, 'patches': []}
        if l[0][:2] == 'H-':
            id = int(l[0][2:])
            patch = ' '.join(l[2:]).strip()
            patch = patch.replace('@@ ', '')
            score = float(l[1])
            hypo[id]['patches'].append([patch, score])
    return hypo


def cure_rerank(meta, hypo_path_list, output_path):
    # the patch with same rank from different models are grouped together
    group_by_rank = {}
    for hypo_path in hypo_path_list:
        hypo = read_hypo(hypo_path)
        print('finish loading', hypo_path)
        for id in hypo:
            if id not in group_by_rank:
                group_by_rank[id] = {'src': hypo[id]['src'], 'patches': []}
            for rank, (patch, score) in enumerate(hypo[id]['patches']):
                if rank >= len(group_by_rank[id]['patches']):
                    group_by_rank[id]['patches'].append([])
                group_by_rank[id]['patches'][rank].append([patch, score])

    # the patch with same rank are ranked by scores
    reranked_hypo = {}
    for id in group_by_rank:
        key = '@'.join(meta[id]) # 因为key是唯一索引，所以trans后但是名字还是Chart-1的话，只能保留一个(连字符换成"_", 方便后续不与"---"冲突)
        reranked_hypo[key] = {'src': group_by_rank[id]['src'], 'patches': []}

        added_patches = set()
        for patches_same_rank in group_by_rank[id]['patches']:
            ranked_by_score = sorted(patches_same_rank, key=lambda e: e[1], reverse=True)
            for patch, score in ranked_by_score:
                if patch not in added_patches:
                    added_patches.add(patch)
                    reranked_hypo[key]['patches'].append({'patch': patch, 'score': score})
            if len(added_patches) >= 5000:
                break

    print('dumping result in json file')
    json.dump(reranked_hypo, open(output_path, 'w'), indent=2)


if __name__ == '__main__':
    # rerank the patches
    trans_list = ['ReorderCondition', 'VariableRenaming']
    for trans in trans_list:
        # print('#'*144)
        # print('Strat generating trans patches for {trans} transformation !'.format(trans=trans))
        # print('#'*144)
        meta_path = os.path.join(r'/root/lqy/cure/CURE_data/patches', trans, 'meta.txt')
        d4j_meta = read_defects4j_meta(meta_path)
        file_name_list = sorted(os.listdir(os.path.join(r'/root/lqy/cure/CURE_data/trans-d4j-classes', trans)))
        assert len(d4j_meta) == len(file_name_list)
        for i in range(len(file_name_list)):
            file_name = file_name_list[i].split('.')[0]
            assert d4j_meta[i][0].split('_')[0] == file_name.split('---')[0] and d4j_meta[i][0].split('_')[1] == file_name.split('---')[1]
            d4j_meta[i][0] = file_name
        hypo_path_list = [os.path.join(r'/root/lqy/cure/CURE_data/patches', trans, 'gpt_conut_1.txt')] + [os.path.join(r'/root/lqy/cure/CURE_data/patches', trans, 'gpt_fconv_1.txt')]
        output_path = os.path.join(r'/root/lqy/cure/CURE_data/patches', trans, 'reranked_patches.json')
        cure_rerank(d4j_meta, hypo_path_list, output_path)
