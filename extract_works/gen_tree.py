import copy
import re
from collections import defaultdict
from typing import List
from operator import itemgetter, attrgetter
from itertools import count, groupby
from treelib import Tree, Node
from sexpdata import loads


def show_tree(tree: Tree, nid=None, level=0, filter=None,
              key=None, reverse=False, line_type='ascii-ex', func=print):
    """代替tree.show，直接显示node.data"""
    for pre, node in tree._Tree__get(nid, level, filter, key, reverse,
                                     line_type):
        label = "%s %s %s" % (node.identifier, node.tag, node.data)

        func('{0}{1}'.format(pre, label))


def load_from_ltp_tuple(ltp_tree_old, segment=None, root_id=0):
    """
    将哈工大输出的树结构转为treelib的树
    :param segment: 分词的词汇
    :type segment: List[str]
    :param ltp_tree: 列表，每个节点为一个tuple，(节点编号，父节点，依存标记)，节点编号为下标+1
    :type ltp_tree: List[tuple]
    :param root_id: 将句子编号存到root的data中
    :type root_id: int
    :return: treelib tree
    :rtype:Tree
    """
    # 转换为树 treelib库
    tree = Tree()
    tree.create_node(identifier=0, data=str(root_id + 1), tag='isRoot')
    ltp_tree = copy.deepcopy(ltp_tree_old)
    while len(ltp_tree) > 0:
        ltp_tree_steady = tuple(ltp_tree)
        for ltp_tuple in ltp_tree_steady:
            assert len(ltp_tuple) == 3
            node_id, parent, tag = ltp_tuple

            if tree.contains(parent):
                if segment is not None:
                    tree.create_node(identifier=int(node_id), data=segment[node_id - 1], parent=parent, tag=tag)
                else:
                    tree.create_node(identifier=int(node_id), parent=parent, tag=tag)
                ltp_tree.remove(ltp_tuple)
    # tree.show()
    return tree


def load_from_mutiple_tuple(tuples: List[tuple]):
    """
    从(父，子)的元组中形成Tree
    :param tuples: [(parent_line_no, child_line_no),]
    """
    tree = Tree()
    tree.create_node('root', 'root')
    for parent, tpl in groupby(tuples, itemgetter(0)):
        if not tree.contains(parent):
            tree.create_node(parent, parent, 'root')
        for p, c in tpl:
            if tree.contains(c):
                tree.move_node(c, p)
            else:
                tree.create_node(c, c, parent=p)
    return tree


def save2s_expr(tree):
    """treelib的tree 转换为s expression"""
    stack = [-1, ]
    s_expr = ""
    for id in tree.expand_tree():  # 深度遍历
        node: Node = tree.nodes[id]
        depth = tree.depth(node=id)

        while depth < stack[-1]:  # 如果是上一个的祖先节点
            s_expr += ")"
            stack.pop()

        if depth > stack[-1]:  # 如果是上一个的子节点
            stack.append(depth)  # 压入栈
        elif depth == stack[-1]:  # 如果是上一个的兄弟节点
            s_expr += ")"
            # pop out又stack in 相同level，抵消

        s_expr += "\n%s(%s,%s" % ("\t" * depth, node.identifier, node.tag + "," + node.data)

    while stack[-1] >= 0:
        s_expr += ")"
        stack.pop()

    # print(s_expr)
    if s_expr.count('(') != s_expr.count(')'):
        print("bracket not balanced! ")
        print(s_expr)
        return ""
    return s_expr


def trans2s_expr(ltp_tree, segment, id=0):
    """
    将哈工大输出的树结构转为tregex可读的s expression格式
    :param ltp_tree: 列表，每个节点为一个tuple，(节点编号，父节点，依存标记)，节点编号为下标+1
    :type ltp_tree:list
    :param id: 将句子编号存到root的data中
    :type id: int
    :return:s expression
    :rtype:str
    """
    tree = load_from_ltp_tuple(ltp_tree, segment, id)

    s_expr = save2s_expr(tree)
    return s_expr


def load_from_ltp_files(path_sdps='data/ltp_sdps.txt', path_segs='data/ltp_segs.txt', with_seg=True) -> List[Tree]:
    """从ltp生成的文本文件中，提取转换生成树列表"""
    fortrees = []
    for ltp_path in (path_sdps, path_segs):
        with open(ltp_path, 'r', encoding='utf-8') as f:
            str_ltp = f.read()
        ltp_obj = eval(str_ltp)
        fortrees.append(ltp_obj)

    assert len(fortrees[0]) == len(fortrees[1])
    assert len(fortrees) == 2
    sdps, segs = fortrees

    if with_seg:
        trees = [load_from_ltp_tuple(sdp, seg, i) for i, (sdp, seg) in enumerate(zip(sdps, segs))]
    else:
        trees = [load_from_ltp_tuple(sdp, root_id=i) for i, sdp in enumerate(sdps)]
    return trees


def load_from_sexpr(s_str):
    """从s expression读取到树"""

    def build_tree(s, t, p=None):
        last_p = None
        for a, b in groupby(s, key=lambda x: not isinstance(x, list)):
            if a:
                for i in b:
                    seperates = i._val.split(",")
                    last_p = int(seperates[0])
                    t.create_node(identifier=int(seperates[0]), tag=seperates[1], data=seperates[2], parent=p)
            else:
                for i in b:
                    build_tree(i, t, p=last_p)

    tree = Tree()
    s_obj = loads(s_str)
    try:
        iter(s_obj)
        if "Root" not in s_str:
            tree.create_node('root', 'root')
            build_tree(s_obj, tree, 'root')
        else:
            build_tree(s_obj, tree)
    except TypeError:
        node = gen_node(s_obj._val)
        tree.add_node(node)

    return tree


def load_from_sexpr_to_nodes(s_str, isReturnedMerged=False):
    nodes = []

    def build_tree(s):
        try:
            iter(s)
            for a, b in groupby(s, key=lambda x: not isinstance(x, list)):
                # a: bool, b:List[Symbol] iter or Symbol iter
                if a:  # b is a Symbol iter
                    for i in b:  # i: Symbol
                        nodes.append(gen_node(i._val))
                else:  # b is List[Symbol] iter
                    for i in b:  # i is a List[Symbol]
                        build_tree(i)
        except TypeError:  # 不可迭代，只有一个节点
            nodes.append(nodes.append(gen_node(s._val)))

    build_tree(loads(s_str))
    if isReturnedMerged:
        sorted_nodes = sorted(nodes, key=attrgetter('identifier'))
        return "".join([n.data for n in sorted_nodes])
    else:
        return nodes


def gen_node(n_s_str: str):
    """
    由sexp生成节点Node
    :param n_s_str: 形如“3,sTOOL,个人信息”
    :type n_s_str: str
    :return: node
    :rtype:Node
    """
    assert "(" not in n_s_str  # 确保只有一个节点
    id, tag, data = n_s_str.split(',')
    return Node(identifier=int(id), tag=tag, data=data)


def load_from_sexp_file(path='data/cutted_trees_sexpr.txt') -> List[Tree]:
    """从cutted s expression还原到treelib树"""
    with open(path, 'r', encoding='utf-8') as f:
        cutted_s = f.read()
    cutted_ss = re.split('(?=\(0,isRoot,[0-9]+)', cutted_s)

    trees = []
    for ct in cutted_ss:
        if len(ct) == 1:
            continue
        trees.append(load_from_sexpr(ct))
    return trees


def gen_tree_from_sexpr(t_b:str):
    t_b = t_b.strip()
    parent_stack = [-1]
    tree = Tree()
    tree.create_node(identifier=-1, tag='isRoot')
    lines = t_b.split('\n')
    for ln in lines:
        ln = ln.strip()
        nodes_str = ln.split(' ')
        for n_str in nodes_str:
            node = gen_node(n_str.strip('()'))
            tree.add_node(node, parent=parent_stack[-1])
            if '(' in n_str:
                parent_stack.append(node.identifier)
            if ')' in n_str:
                cnt = n_str.count(')')
                for i in range(cnt):
                    parent_stack.pop()
    # if 'Root' in t_b:
    #     tree.remove_node(-1)
    # show_tree(tree)

    return tree


if __name__ == '__main__':
    # tree = load_from_sexpr('(18,LINK,三类 17,eCOO,系统运行安全数据)')
    # show_tree(tree)
    pass
