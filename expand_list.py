import re
from cn2an import an2cn, cn2an
from ltp_standard import preprocessing

from gen_tree import load_from_mutiple_tuple

chi_num = "一二三四五六七八九十"


def assign_role(lines):
    # 找列表
    role_per_line = [0] * len(lines)  # 每行的角色：0文本，+1列表标题，+2列表项，(3列表标题和列表项），第一项列表项+4(即为6或7)
    expecting = ""
    for index, ln in enumerate(lines):
        x = 1
        # 判断是否是列表标题，be like "包括以下数据："
        if ("以下" in ln or "如下" in ln or ln.endswith("：")) \
                and re.search("[表图][0-9]", ln) is None:
            # ”以下“、冒号、不含表图、下一行有列表标记（不以中文开头）
            role_per_line[index] += 1

        # 判断是否为列表项
        if re.search("^[^\u4e00-\u9fa5]", ln):  # 不以中文开头，认为是列表项
            role_per_line[index] += 2
            if role_per_line[index - 1] % 2 == 1:  # 如果上一个是标题（奇数），那么这一个列表项是第一个
                role_per_line[index] += 4
            res = re.search("^（?(.{1,3}?)）", ln)
            # 找列表项符号
            if res is None:  # 没有括号，即无序列表
                symbol = ln[0]
                next_expecting = symbol
                if symbol != expecting and role_per_line[index] < 5:
                    role_per_line[index] += 4
            else:  # 有括号，一般是有序列表
                symbol = res.group(1)
                if symbol.isdigit():  # 阿拉伯数字
                    symbol = int(symbol)
                    next_expecting = int(symbol) + 1
                elif re.search('^[a-zA-Z]+$', symbol):  # 英文字母
                    next_expecting = chr(ord(symbol) + 1)
                elif all(x in chi_num for x in symbol):  # 中文数字
                    next_expecting = an2cn(cn2an(symbol) + 1)
                else:
                    print("alert new type: ", symbol)
                    exit(1)
                    next_expecting = symbol
                # 判断漏网之鱼
                if role_per_line[index] < 5:
                    if symbol in (1, 'a', 'A', '一'):  # 是否为第一个列表项
                        role_per_line[index] += 4
                    elif symbol != expecting:  # 否则可能是接着上一级列表
                        role_per_line[index] += 10

            expecting = next_expecting
        # if role_per_line[index] == 0:
        #     expecting = ""
    return role_per_line


# 展开列表
# role总结，1：标题；2：非开头的列表项；3：同时是标题和列表项，下一行是嵌套的子列表；6：开头列表项；7：开头的、是标题的列表项
def expand_texts_after_list_item(role_per_line):
    """第一轮，将非开头列表项前的正文解释（即非列表项），附到列表项后面"""

    parent_child = []
    index = 0
    while index < len(role_per_line):
        skip = 1
        i = 0
        if role_per_line[index] > 1:
            # 找下一个非正文的角色
            next_role = 0
            while next_role == 0 and index + i + 1 < len(role_per_line):
                i += 1
                next_role = role_per_line[index + i]
            # 下一个是非开头的列表项 即2或3
            if (next_role == 2 or next_role == 3) and i > 1:
                # 以index为父节点、index+1到index+i为子节点，存储为元组关系
                for j in range(index + 1, index + i):
                    parent_child.append((index, j))
                skip = i

        index += skip
    return parent_child


def hierarchy(role_per_line: list):
    """
    梳理标题的嵌套层级关系
    :param role_per_line: 每行的角色
    :return: [(parent_line_no, child_line_no),]
    """
    last_parent_stack = [-1, ]
    hiers = []

    for index, role in enumerate(role_per_line):
        if role == 1:  # 一级标题，重置
            last_parent_stack = [-1, ]
        if role > 10:  # 嵌套标题结束，弹出栈
            last_parent_stack.pop()
        if role > 1:  # 所有列表项
            if role == 6 and role_per_line[index - 1] == 0:  # 没有一级标题，不计入
                last_parent_stack = [-1, ]
            if last_parent_stack[-1] != -1:  # 必须有可用的标题行
                hiers.append((last_parent_stack[-1], index))
        if role % 2 == 1:  # 标题，压入栈
            last_parent_stack.append(index)

    return hiers


def gen_list_struct(lines):
    """把文本列表关系整理为tree"""
    roles = assign_role(lines)
    hiers1 = expand_texts_after_list_item(roles)
    hiers2 = hierarchy(roles)
    # print(roles)
    # print(hiers1)
    # print(hiers2)
    return load_from_mutiple_tuple(hiers1 + hiers2)


if __name__ == '__main__':
    lines = preprocessing()
    hiers = gen_list_struct(lines)
    print(hiers)

