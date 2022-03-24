from operator import attrgetter

from gen_tree import load_from_ltp
from treelib import Tree, Node
from gen_tree import treelib2s_expr

verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下']  # '可识别为', '是', '如', '涉及'
SUB = ['AGT', 'EXP']
VEB = ['ePREC', 'eSUCC', 'ROOT']
OBJ = ['PAT', 'CONT', 'DATV', 'LINK']
SCENE = ['TOOL', 'MATL', 'MANN', 'SCO', 'REAS', 'TIME', 'LOC', 'STAT']  # , 'FEAT', 'MEAS'

dump_tag = SCENE + ['mRELA', 'mDEPD']  # 删除情景依存关系\关系标记\依附标记
merge_tag = ['FEAT', 'MEAS', 'eCOO']


def Rule_template(old_tree, condition, isprint=False, extra_func=None):
    """树删减规则模板"""
    new_tree = Tree(tree=old_tree, deep=True)  # 深度复制旧树
    dumped_ids = []  # 已经删除的节点id
    depth = 0

    for node in old_tree.all_nodes():  # 广度优先遍历

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
                extra_func(children_dump, new_tree.get_node(node.identifier))

    if isprint and len(dumped_ids) > 0:
        sorted_dumped_ids = sorted(dumped_ids)
        print(old_tree.nodes[0].data, end='\t', file=log_file)
        print(" ".join([old_tree.get_node(nd).data for nd in sorted_dumped_ids]), file=log_file)

    return new_tree


def paste_subtree_2_parent(children_dump, node):
    """
    将子树的data整理排序填充到父节点data
    :param children_dump: dumped subtree nodes
    :type list
    :param node: parent node
    :type Node
    """
    children_dump.append(node)

    sorted_dums = sorted(children_dump, key=attrgetter('identifier'))
    feat_str = sorted_dums[0].data
    for i in range(1, len(sorted_dums)):
        if sorted_dums[i].identifier - sorted_dums[i - 1].identifier == 1:
            feat_str += sorted_dums[i].data
        else:
            feat_str += " " + sorted_dums[i].data

    node.data = feat_str


def remove_punc(tree: Tree):
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


def cut_tree(ltp_tree):
    tree_temp = remove_punc(ltp_tree)  # 标点附回去
    tree_temp = Rule_template(tree_temp, condition=lambda node: node.tag.strip('rd') in merge_tag,
                              extra_func=paste_subtree_2_parent)  # 合并依存关系
    tree_temp = Rule_template(tree_temp,
                              condition=lambda node: node.tag.strip('rd') in dump_tag and node.data.strip('，：') not in verb_keys,
                              isprint=True)  # 删除该删除的依存关系tag

    return tree_temp


if __name__ == "__main__":
    # sents, ltp, sdps, segments, hiddens = ltp_prepro()
    # pos = ltp.pos(hiddens)  # 词性

    # trees = [tuple2tree(sdp, seg, i) for i, (sdp, seg) in enumerate(zip(sdps, segments))]
    trees = load_from_ltp()
    log_file = open('data/dumped/SCENE.txt', 'w', encoding='utf-8')

    with open('data/cutted_trees_sexpr.txt', 'w', encoding='utf-8') as f:  # merged
        for tree in trees:
            cutted_tree = cut_tree(tree)
            f.write(treelib2s_expr(cutted_tree))

    log_file.close()
