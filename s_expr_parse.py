from treelib import Tree, Node


def trans2s_expr(ltp_tree):
    """
    将哈工大输出的树结构转为tregex可读的s expression格式
    :param ltp_tree: 列表，每个节点为一个tuple，(节点编号，父节点，依存标记)，节点编号为下标+1
    :type ltp_tree:list
    :return:s expression
    :rtype:str
    """
    # 转换为树 treelib库
    tree = Tree()
    tree.create_node(identifier=0, data='Root')
    while len(ltp_tree) > 0:
        ltp_tree_steady = tuple(ltp_tree)
        for ltp_tuple in ltp_tree_steady:
            id, parent, tag = ltp_tuple
            if tree.contains(parent):
                tree.create_node(identifier=id, data=tag, parent=parent)
                ltp_tree.remove(ltp_tuple)
    # tree.show()

    # 转换为s expression
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

        s_expr += "\n%s(%s,%s" % ("\t" * depth, node.identifier, node.data)

    while stack[-1] >= 0:
        s_expr += ")"
        stack.pop()

    # print(s_expr)
    return s_expr
