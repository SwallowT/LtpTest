import re

from treelib import Tree, Node
from typing import List, Dict, Tuple
import subprocess
from collections import defaultdict

from gen_tree import gen_node, load_from_sexpr

SUB = ['AGT', 'EXP']
VEB = ['ePREC', 'eSUCC', 'ROOT']
OBJ = ['PAT', 'CONT', 'DATV', 'LINK']
verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下', '示例']
entity_key = ("数据", "信息", '数据域')
constellation = ['、', '以及', '和', '/', '与']  # 并列关系

ent_patterns: List[str] = [f'/(数据)|(信息)/=hyper >/{v}/ $/、/= hypo' for v in verb_keys]
v_patterns: List[str] = []

ent_str_list = []

# hypers = {}  # tree_id: 上义词str,
# hypos = defaultdict(list)  # tree_id: [下义词str1, ...]
hyper_hypos: Dict[str, List[str]] = defaultdict(list)  # {上义词str: [下义词str1, ...]}
hypo_hyper: Dict[str, str] = dict()  # hypo.data: hyper.data
# hyper_hypo_id: Dict[str, List[str]] = dict()  # hyper.data: [hypo_node]
# class LineInfo(object):


def tregex_search_terminal(pattern: str, para: List[str] = ('-u', '-n', '-h hyper', '-h hypo')):
    """
    tregex命令行匹配
    :param pattern: tregex模式
    :param para: 参数
    :return:匹配到的节点
    """
    parastr = " ".join(para)
    command = f"java -cp '/home/tanly/pywork/stanford-tregex/stanford-tregex.jar:' " \
              f"edu.stanford.nlp.trees.tregex.TregexPattern {parastr} '{pattern}' " \
              f"/home/tanly/pywork/SyntaxTree/data/cutted_trees_sexpr.txt "
    res = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    resstr = str(res.stdout, encoding='utf-8')
    return resstr


def parse_terminal(resstr):
    """解析tregex返回内容"""
    # 形如：
    # 4: 35, PAT, 数据
    # 41, LINK, 公开级（1级）、内部级（2级）、敏感级（3级）、
    # 4: 35, PAT, 数据
    # 67, LINK, 重要级（4级）、核心级（5级）五个级别
    ent_node_per_line: Dict[str, List[Tuple[Node, Node]]] = defaultdict(list)  # tree_id:[(hyper_node1,hypo_node1)...]
    matches = resstr.strip().split('\n')

    assert ": " in resstr

    tree_id, hyper = 0, Node()
    for mat in matches:
        if ": " in mat:
            tree_id, hyper_str = mat.split(': ', maxsplit=1)
            hyper = gen_node(hyper_str)
        else:
            hypo = gen_node(mat)
            ent_node_per_line[tree_id].append((hyper, hypo))

    return ent_node_per_line


def find_entity_seg(tree: Tree, isDump=False):
    """找到实体"""
    entity_list: List[str] = []
    for node in tree.all_nodes():
        if any([node.data.strip("：，").endwith(i) for i in entity_key]):
            entity_list.append(node.data.strip("：，"))
    if isDump:
        with open('data/entity_list.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(entity_list))
    return entity_list


def find_hyper_hypo(entity_list):
    pass


def split_hypo(hypo_sent: str) -> list:
    # 假设：左右括号完整，没有嵌套括号
    if "、" in hypo_sent:  # 分开逗号分割的子句
        subs = re.split('[，；。]', hypo_sent)
        sep = constellation
    else:
        subs = re.split('[；。]', hypo_sent)
        sep = constellation + ['，']

    res = []  # 'A(B、C)' -> ['A', ['B', 'C']]
    is_inBracket = False
    is_after_colon = False
    for sb in subs:
        ent_list = re.split('|'.join(sep), sb)

        if len(ent_list) == 1:
            continue

        for ent in ent_list:
            if len(ent) == 0:
                continue

            rm_reg = re.compile('等.*')

            if "（" in ent and "）" not in ent:  # eg. 存款信息（包括资金数量

                is_inBracket = True

                p, c = ent.split("（")
                for v in verb_keys: c = c.strip(v)  # 去掉“包括”
                res.append([p, [c]])

            elif is_inBracket:  # eg. 业务订购等）数据等
                assert isinstance(res[-1][-1], list)

                if "）" in ent:
                    is_inBracket = False
                    c, p = ent.split("）")
                    c, p = rm_reg.sub('', c), rm_reg.sub('', p)
                    res[-1][-2] += p
                    res[-1][-1].append(c)
                else:
                    res[-1][-1].append(ent)

            elif "：" in ent:  # 示例：老年人优待证信息，无偿献血证
                p, c = ent.split("：")
                c = rm_reg.sub('', c)
                if p in verb_keys:
                    res.append(c)
                else:
                    res.append([p, [c]])
                    is_after_colon = True
            elif is_after_colon:
                res[-1][-1].append(rm_reg.sub('', ent))
            else:
                res.append(rm_reg.sub('', ent))
    # print(res)
    return res
    # temp=""
    # i=0
    # trees = []
    # while i < len(hypo_sent):
    #     chr = hypo_sent[i]
    #     if chr == '、':


# def init(trees):
#     ent_list = defaultdict(list)
#     for i, tree in enumerate(trees):
#         tree: Tree
#         for node in tree.expand_tree():
#             node = tree[node]
#
#             if node.data.endswith(("数据", "信息", '数据域')) or "、" in node.data:
#                 ent_list[i].append(node)
#
#     return ent_list


def find_pattern(ent_list, pattern_list):
    pass


def main_proc():
    # 根据ent_pattern实体模式找实体
    for pt in ent_patterns:
        tregex_res_str = tregex_search_terminal(pattern=pt)
        nodes_dict = parse_terminal(tregex_res_str)

        # 存到hypo-hyper
        for t_id, pairs in nodes_dict.items():
            for hyper, hypo in pairs:
                if hypo.data in hypo_hyper.keys():
                    # 已经存在该下义词
                    old_hyper, new_hyper = hypo_hyper[hypo.data], hyper.data
                    if old_hyper != new_hyper and (len(old_hyper) < len(new_hyper) or len(old_hyper)>10):
                        # 上义词不一致
                        print('changed:', old_hyper, new_hyper)
                        hypo_hyper[hypo.data] = new_hyper
                    else:
                        print('unchanged:', old_hyper, new_hyper)
                else:
                    hypo_hyper[hypo.data] = hyper.data

        # 分开hypo, 转换为hyper-hypo
        for hypo, hyper in hypo_hyper.items():
            splitted_hypos = split_hypo(hypo)
            hyper_hypos[hyper].extend(splitted_hypos)

        print(hyper_hypos)
    # print(ent_node_per_line)
    # 根据ent_list找v_pattern



# def split_entity(seg):
if __name__ == '__main__':
    # nodes = tregex_search('/(数据)|(信息)/>/分为/|>/分成/')
    # print(nodes)
    # print(split_hypo('银行账户、鉴别信息（口令）、存款信息（包括资金数量、支付收款记录等）、房产信息、信贷记录、征信信息、交易和消费记录、流水记录等，以及虚拟货币、虚拟交易、游戏类兑换码等虚拟财产信息'))

    main_proc()

    # ent_list = init(trees)
    # for k, v in ent_list.items():
    #     print(k, end='\t')
    #     for node in v:
    #         print(node.data, end='\t')
    #     print()
