from treelib import Tree, Node


def tuple2tree(ltp_tree, segment, root_id=0):
    """
    将哈工大输出的树结构转为treelib的树
    :param ltp_tree: 列表，每个节点为一个tuple，(节点编号，父节点，依存标记)，节点编号为下标+1
    :type ltp_tree:listb
    :param root_id: 将句子编号存到root的data中
    :type root_id: int
    :return: treelib tree
    :rtype:Tree
    """
    # 转换为树 treelib库
    tree = Tree()
    tree.create_node(identifier=0, data=str(root_id+1), tag='isRoot')
    while len(ltp_tree) > 0:
        ltp_tree_steady = tuple(ltp_tree)
        for ltp_tuple in ltp_tree_steady:
            node_id, parent, tag = ltp_tuple
            if tree.contains(parent):
                tree.create_node(identifier=node_id, data=segment[node_id - 1], parent=parent, tag=tag)
                ltp_tree.remove(ltp_tuple)
    # tree.show()
    return tree


def treelib2s_expr(tree):
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
    tree = tuple2tree(ltp_tree, segment, id)

    s_expr = treelib2s_expr(tree)
    return s_expr


def load_from_ltp(path_sdps='data/ltp_sdps.txt', path_segs='data/ltp_segs.txt'):
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

    trees = [tuple2tree(sdp, seg, i) for i, (sdp, seg) in enumerate(zip(sdps, segs))]
    return trees
