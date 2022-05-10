import logging
from collections import defaultdict, Counter
from operator import attrgetter
from typing import List

from gen_tree import load_from_sexp_file
from treelib import Tree, Node
from gen_tree import save2s_expr, show_tree

logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='data/logs/new.log',
                    filemode='w',  # 模式，有w和a，默认是a
                    format=
                    '%(asctime)s - %(levelname)s: %(message)s'
                    # 日志格式
                    )

verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下']  # '可识别为', '是', '如', '涉及'

SCENE = ['TOOL', 'MATL', 'MANN', 'SCO', 'REAS', 'TIME', 'LOC', 'STAT']  # , 'FEAT', 'MEAS'
dump_tag = SCENE + ['mRELA', 'mDEPD']  # 删除情景依存关系\关系标记\依附标记
merge_tag = ['FEAT', 'rFEAT', 'dFEAT', 'MEAS', 'eCOO', 'rCONT', 'rPAT', 'rEXP']  # 删除子树FEAT\MEAS\eCOO并合并到父节点, 'mNEG'

record_comma_path = []  # [node_id,] 记录每棵树逗号路径上的节点
record_comma = []  # [node_id,] 记录每棵树逗号路径上的节点

commas = ("，", "；", '：')


def is_endswith_comma(node: Node) -> bool:
    return node.data.endswith(commas)


def Rule_Merge(old_tree: Tree):
    """树删减规则模板"""
    new_tree = Tree(tree=old_tree, deep=True)  # 深度复制旧树
    dumped_ids = []  # 已经删除的节点id
    to_merge = defaultdict(list)  # parent: children，结束后一起merge

    comma_counter = Counter(record_comma_path)

    def delete_and_merge(parent: int, current_node: Node):
        subtree = new_tree.remove_subtree(current_node.identifier)  # remove
        _dum = subtree.nodes.keys()  # logs nodes id
        dumped_ids.extend(_dum)

        if len(_dum) > 0:
            to_merge[parent] += subtree.all_nodes()

    for id in old_tree.expand_tree():  # 遍历
        node: Node = new_tree.get_node(id)
        if id in dumped_ids or id == 0:
            continue

        sdp_tag, pos_tag = node.tag.split("|", maxsplit=1)
        if sdp_tag in merge_tag:
            parent_id = node.predecessor(old_tree.identifier)
            if tree[parent_id].tag == 'Root|v':
                continue
            if id > parent_id and parent_id in record_comma_path:
                if parent_id not in record_comma:  # parent没逗号
                    if id in record_comma_path and comma_counter[id] == 1:
                        # 特殊情况需要合并，其他的不合并

                        # 得到最大的后代节点id
                        descendants = tree.subtree(id).all_nodes()  # 包括自己
                        max_id = max([n.identifier for n in descendants])
                        # 得到逗号节点id
                        comma_id = [n.identifier for n in descendants if is_endswith_comma(n)][0]

                        if comma_id == max_id:  # 逗号在最右边，直接合并所有
                            record_comma.append(parent_id)
                            delete_and_merge(parent_id, node)
                        else:
                            record_comma.append(id)
                            for child in tree.children(node.identifier):
                                if (child.identifier < comma_id and child.identifier not in record_comma_path) or (
                                        child.identifier == comma_id and child.is_leaf(old_tree.identifier)):
                                    # 子节点在逗号左边
                                    delete_and_merge(id, child)  # 合并它的子节点
                    elif id not in record_comma_path:
                        delete_and_merge(parent_id, node)

            elif id < parent_id and id in record_comma_path:
                if comma_counter[id] == 1:
                    # 得到逗号节点id
                    descendants = tree.subtree(id).all_nodes()  # 包括自己
                    comma_id = [n.identifier for n in descendants if is_endswith_comma(n)][0]
                    if id <= comma_id:
                        record_comma.append(id)
                        for child in tree.children(node.identifier):
                            if (child.identifier < comma_id and child.identifier not in record_comma_path) or (
                                    child.identifier == comma_id and child.is_leaf(old_tree.identifier)):
                                # 子节点在逗号左边
                                delete_and_merge(id, child)  # 合并它的子节点
                    else:
                        for child in tree.children(node.identifier):
                            if (child.identifier < comma_id and child.identifier not in record_comma_path) or (
                                    child.identifier == comma_id):  # and child.is_leaf(old_tree.identifier)):
                                # 子节点在逗号左边
                                new_tree.move_node(child.identifier, parent_id)  # 子节点移到父节点下面
                        delete_and_merge(parent_id, node)

            else:
                delete_and_merge(parent_id, node)

    # 统一合并
    for parent_id, children in to_merge.items():
        parent_id = new_tree[parent_id]
        # 防止关键字动词被合并，先挪到父节点下面
        notmoved: List[Node] = []
        for suc in children:
            if suc.data.strip("，：；") in verb_keys:
                new_tree.add_node(suc, parent_id.identifier)
            else:
                notmoved.append(suc)
        # 加入父节点
        notmoved.append(parent_id)

        # 合并
        sorted_dums = sorted(notmoved, key=attrgetter('identifier'))
        parent_id.data = "".join([i.data for i in sorted_dums])

    return new_tree


def Rule_Delete(old_tree: Tree, isprint=True):
    """树删减规则模板"""
    new_tree = Tree(tree=old_tree, deep=True)  # 深度复制旧树
    dumped_ids = []  # 已经删除的节点id

    for node in old_tree.all_nodes():  # 遍历
        node: Node
        id = node.identifier
        if id in dumped_ids or id == 0:
            continue

        sdp_tag, pos_tag = node.tag.split("|", maxsplit=1)
        if sdp_tag.strip('rd') in dump_tag and node.data not in verb_keys:
            subtree = new_tree.remove_subtree(id)  # remove
            _dum = subtree.nodes.keys()  # logs nodes id
            dumped_ids.extend(_dum)

    if isprint and len(dumped_ids) > 0:
        sorted_dumped_ids = sorted(dumped_ids)
        logging.info(old_tree.nodes[0].data + '\t' + " ".join([old_tree.get_node(nd).data for nd in sorted_dumped_ids]))

    return new_tree


def move_punc(tree: Tree):
    record_comma_path.clear()
    record_comma.clear()
    for id in tree.expand_tree():
        punc_node: Node = tree.get_node(id)
        if id == 0:
            continue
        sdp, pos = punc_node.tag.split("|")
        punc = punc_node.data
        if sdp == 'mPUNC':

            tree.remove_node(id)

            if punc in ('（', '“', '《'):
                tree.get_node(id + 1).data = punc + tree.get_node(id + 1).data
            else:
                last_node = id - 1
                while not tree.contains(last_node):
                    last_node -= 1
                if last_node == 0:
                    continue
                tree.get_node(last_node).data += punc

                # 记录路径和父节点
                if punc in commas:
                    record_comma_path.extend(tree.rsearch(last_node))
                    record_comma.append(last_node)

    for id in tree.expand_tree():
        punc_node: Node = tree.get_node(id)
        if id == 0:
            continue
        sdp, pos = punc_node.tag.split("|")
        if pos == 'u' and punc_node.is_leaf(tree.identifier):

            tree.remove_node(id)

            last_node = id - 1
            while not tree.contains(last_node):
                last_node -= 1
            if last_node == 0:
                continue
            tree.get_node(last_node).data += punc_node.data

        elif pos == 'c' and tree.contains(id+1):
            tree.remove_node(id)
            tree.get_node(id + 1).data = punc_node.data + tree.get_node(id + 1).data

def replace_entity(tree: Tree):
    """把以“数据”等关键词结尾的节点提前挪到不会被删除的位置"""
    for node in tree.all_nodes():
        if node.data.strip("、，）").endswith(("数据", "信息", '数据域')):
            # 找路径中会被删减的父节点
            parents_dumpting: List[Node] = []
            for i in tree.rsearch(node.identifier):
                if i == 0:
                    continue
                ancestor = tree.get_node(i)
                sdp_tag, pos_tag = ancestor.tag.split("|", maxsplit=1)
                if sdp_tag.strip('rd') in dump_tag:
                    parents_dumpting.append(ancestor.identifier)
            # 找到了，移动到不会被删除的位置
            if len(parents_dumpting) != 0:
                node.tag = "s" + node.tag  # 特殊标记，防止被删除和合并
                new_parent: Node = tree.parent(parents_dumpting[-1])
                tree.move_node(node.identifier, new_parent.identifier)
                # tree.remove_node(parents_dumpting[-1])


def strip_punc(tree: Tree):
    for node in tree.all_nodes():
        node.data = node.data.strip("：，。；")


def cut_tree(ltp_tree):
    move_punc(ltp_tree)  # 标点附回去
    replace_entity(ltp_tree)  # 实体节点防删
    ltp_tree = Rule_Merge(ltp_tree)  # 合并依存关系
    strip_punc(ltp_tree)
    ltp_tree = Rule_Delete(ltp_tree, isprint=True)  # 删除该删除的依存关系tag

    return ltp_tree


if __name__ == "__main__":
    trees = load_from_sexp_file('data/trees_output_words.txt')

    with open(f'data/cutted_trees_sexpr.txt', 'w', encoding='utf-8') as f:  # merged
        for i, tree in enumerate(trees):
            cutted_tree = cut_tree(tree)
            # show_tree(cutted_tree)
            f.write(save2s_expr(cutted_tree))
