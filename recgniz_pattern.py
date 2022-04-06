from treelib import Tree, Node
from typing import List
import subprocess
from collections import defaultdict

from gen_tree import load_from_sexpr_to_nodes

SUB = ['AGT', 'EXP']
VEB = ['ePREC', 'eSUCC', 'ROOT']
OBJ = ['PAT', 'CONT', 'DATV', 'LINK']
verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下']
entity_key = ("数据", "信息", '数据域')


def tregex_search(pattern: str, para: List[str] = ('-f',)):
    """
    tregex命令行匹配
    :param pattern: tregex模式
    :param para: 参数
    :return:匹配到的节点
    """
    parastr = " ".join(para)
    command = f"java -cp '/home/tanly/pywork/stanford-tregex/stanford-tregex.jar:' " \
              f"edu.stanford.nlp.trees.tregex.TregexPattern {parastr} '{pattern}' " \
              "/home/tanly/pywork/stanford-tregex/data/."
    res = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    resstr = str(res.stdout, encoding='utf-8')

    matches = resstr.strip().split('\n\n')
    if '#' in resstr:
        nodes = defaultdict(list)
        for mat in matches:
            lines = mat.split('\n', maxsplit=1)
            tree_id = lines[0][63:].strip('.txt')
            nodes[tree_id].append(load_from_sexpr_to_nodes(lines[1].strip()))
    else:
        nodes = []
        for mat in matches:
            nodes.append(load_from_sexpr_to_nodes(mat.strip()))

    return nodes


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


# def split_entity(seg):
if __name__ == '__main__':
    nodes = tregex_search('/(数据)|(信息)/>/分为/|>/分成/')
    print(nodes)
