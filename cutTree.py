from functools import partial
from operator import attrgetter
from typing import List

from gen_tree import load_from_ltp_files
from treelib import Tree, Node
from gen_tree import save2s_expr

verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下']  # '可识别为', '是', '如', '涉及'

SCENE = ['TOOL', 'MATL', 'MANN', 'SCO', 'REAS', 'TIME', 'LOC', 'STAT']  # , 'FEAT', 'MEAS'
dump_tag = SCENE + ['mRELA', 'mDEPD']  # 删除情景依存关系\关系标记\依附标记
merge_tag = ['FEAT', 'MEAS', 'eCOO']  # 删除子树FEAT\MEAS\eCOO并合并到父节点, 'mNEG'


def Rule_template(old_tree: Tree, condition, isprint=False, extra_func=None):
    """树删减规则模板"""
    new_tree = Tree(tree=old_tree, deep=True)  # 深度复制旧树
    dumped_ids = []  # 已经删除的节点id
    depth = 0

    for node in old_tree.all_nodes():  # 遍历

        if node.identifier not in dumped_ids:
            children = node.successors(old_tree.identifier)
            children_dump = []

            for child_id in children:

                child = old_tree.nodes[child_id]

                if condition(child) and child.identifier not in dumped_ids:
                    subtree = new_tree.remove_subtree(child_id)
                    _dum = subtree.nodes.keys()
                    dumped_ids += _dum
                    children_dump += subtree.all_nodes()

            if extra_func is not None and len(children_dump) > 0:
                extra_func(children_dump, new_tree.get_node(node.identifier), new_tree)

    if isprint and len(dumped_ids) > 0:
        sorted_dumped_ids = sorted(dumped_ids)
        print(old_tree.nodes[0].data, end='\t', file=log_file)
        print(" ".join([old_tree.get_node(nd).data for nd in sorted_dumped_ids]), file=log_file)

    return new_tree


def paste_subtree_2_parent(children_dump: List[Node], node: Node, tree: Tree):
    """
    将子树的data整理排序填充到父节点data
    :param children_dump: dumped subtree nodes
    :param node: parent node
    """
    # 防止关键字动词被合并，先挪到父节点下面
    notmoved: List[Node] = []
    for suc in children_dump:
        if suc.data.strip("，：") in verb_keys:
            tree.add_node(suc, node.identifier)
        else:
            notmoved.append(suc)
    # 加入父节点
    notmoved.append(node)

    # 合并
    sorted_dums = sorted(notmoved, key=attrgetter('identifier'))
    node.data = "".join([i.data for i in sorted_dums])


def move_punc(tree: Tree):
    for id in tree.expand_tree():
        punc_node = tree.get_node(id)
        if punc_node.tag == 'mPUNC':
            tree.remove_node(id)

            if punc_node.data in ('（', '“'):
                tree.get_node(id + 1).data = punc_node.data + tree.get_node(id + 1).data
            else:
                last_node = id - 1
                while not tree.contains(last_node):
                    last_node -= 1
                tree.get_node(last_node).data += punc_node.data

    return tree


def replace_entity(tree: Tree):
    """把以“数据”等关键词结尾的节点提前挪到不会被删除的位置"""
    for node in tree.all_nodes():
        if node.data.strip("、，").endswith(("数据", "信息", '数据域')):
            # 找路径中会被删减的父节点
            parents_dumpting: List[Node] = []
            for i in tree.rsearch(node.identifier):
                if tree.get_node(i).tag.strip('rd') in dump_tag:
                    parents_dumpting.append(tree.get_node(i).identifier)
            # 找到了，移动到不会被删除的位置
            if len(parents_dumpting) != 0:
                node.tag = "s" + node.tag  # 特殊标记，防止被删除和合并
                new_parent: Node = tree.parent(parents_dumpting[-1])
                tree.move_node(node.identifier, new_parent.identifier)
                # tree.remove_node(parents_dumpting[-1])


def strip_punc(tree: Tree):
    for node in tree.all_nodes():
        node.data = node.data.strip("：，。；")


def cut_tree(ltp_tree, pos_tree):
    tree_temp = move_punc(ltp_tree)  # 标点附回去
    replace_entity(tree_temp)
    tree_temp = Rule_template(tree_temp,
                              condition=lambda node: node.tag.strip('rd') in merge_tag
                                                     and (not node.data.endswith(("数据", "信息", '数据域'))),
                              extra_func=paste_subtree_2_parent)  # 合并依存关系
    strip_punc(tree_temp)
    tree_temp = Rule_template(tree_temp,
                              condition=lambda node: node.tag.strip('rd') in dump_tag
                                                     and node.data not in verb_keys,
                              isprint=True)  # 删除该删除的依存关系tag

    return tree_temp


if __name__ == "__main__":
    # sents, ltp, sdps, segments, hiddens = ltp_prepro()
    # pos = ltp.pos(hiddens)  # 词性

    # trees = [tuple2tree(sdp, seg, i) for i, (sdp, seg) in enumerate(zip(sdps, segments))]
    trees = load_from_ltp_files()
    pos_trees = load_from_ltp_files(path_sdps='data/ltp_poss.txt')
    log_file = open('data/dumped/SCENE.txt', 'w', encoding='utf-8')

    for i, (tree, pos_tree) in enumerate(zip(trees, pos_trees)):
        with open(f'data/trees/cutted_trees_sexpr_{i}.txt', 'w', encoding='utf-8') as f:  # merged
            cutted_tree = cut_tree(tree, pos_tree)
            f.write(save2s_expr(cutted_tree))

    log_file.close()
