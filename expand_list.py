import re
import numpy as np
from cn2an import an2cn, cn2an

from ltp_standard import preprocessing

chi_num = "一二三四五六七八九十"


def assign_role(lines):
    # 找列表
    role_per_line = [0] * len(lines)  # 每行的角色：0文本，+1列表标题，+2列表项，(3列表标题和列表项），第一项列表项+4(即为6或7)
    expecting = ""
    for index, ln in enumerate(lines):
        x=1
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
                if symbol != expecting and role_per_line[index]<5:
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
                # 判断是否为第一个列表项
                if symbol in (1, 'a', 'A', '一') and role_per_line[index]<5:
                    role_per_line[index] += 4
                elif symbol != expecting:  # 否则可能是接着上一级列表
                    role_per_line[index] += 10

            expecting = next_expecting
        # if role_per_line[index] == 0:
        #     expecting = ""
    return role_per_line


# 展开列表
# role总结，1：标题；2：非开头的列表项；3：同时是标题和列表项，下一行是嵌套的子列表；6：开头列表项；7：开头的、是标题的列表项
def expand_texts_after_list_item(lines):
    """第一轮，将非开头列表项前的正文解释（即非列表项），附到列表项后面"""

    role_per_line = assign_role(lines)

    index = 0
    new_lines = []
    while index < len(role_per_line):
        skip = i = 1
        if role_per_line[index] > 0:
            # 找下一个非正文的角色
            next_list_role = 0
            while next_list_role == 0 and index + i < len(role_per_line):
                next_list_role = role_per_line[index + i]
                i += 1
            i -= 1
            # 下一个是非开头的列表项 即2或3
            if (next_list_role == 2 or next_list_role == 3) and i > 1:
                str_temp = "".join(lines[index:index + i])
                # print(str_temp)
                new_lines.append(str_temp)
                skip = i
                # del lines[index+1:index+i]
            else:
                new_lines.append(lines[index])
        else:
            new_lines.append(lines[index])
        index += skip
    return new_lines


def expand_nested_lists(lines, filter, roles=None):
    """第二轮，合并被嵌套的列表"""
    if roles == None:
        role_per_line = assign_role(lines)
    else:
        role_per_line = roles
    new_lines = []
    new_roles = []
    index = 0
    while index < len(role_per_line):
        skip = 1
        if role_per_line[index] in filter:  # 奇数就是标题项
            nextRole = role_per_line[index + 1]
            if nextRole > 5:  # 是第一项
                n_nextRole = role_per_line[index + 2]
                i = 3
                while n_nextRole == 2 and index + i < len(role_per_line):
                    n_nextRole = role_per_line[index + i]
                    i += 1
                i -= 1

                if i > 2:  # (n_nextRole > 10 or n_nextRole == 1) and
                    nested_list = lines[index:index + i]
                    nested_list[0] = nested_list[0].strip("：")
                    new_lines.append(nested_list[0])
                    new_roles.append(2)
                    for idx in range(1, i):
                        # if idx < len(role_per_line) and index < len(role_per_line):
                        temp_sent = nested_list[0] + re.sub("^（?(.{1,3}?)）", "", nested_list[idx])
                        new_lines.append(temp_sent)
                        new_roles.append(2)
                        # print(temp_sent)
                    skip = i
                else:
                    # new_lines.append(lines[index])
                    # print(index, role_per_line[index], lines[index], role_per_line[index + i], n_nextRole, i)
                    new_lines.append(lines[index])
                    new_roles.append(role_per_line[index])
            else:
                new_lines.append(lines[index])
                new_roles.append(role_per_line[index])
        else:
            new_lines.append(lines[index])
            new_roles.append(role_per_line[index])
        index += skip

    return new_lines, new_roles


if __name__ == '__main__':
    lines = preprocessing()
    print(0, len(lines))
    # 第一轮
    new_lines = expand_texts_after_list_item(lines)
    print(1, len(new_lines))
    # for ln in new_lines:
    #     print(ln)
    # 第二轮
    lines = new_lines
    del new_lines
    new_lines, new_roles = expand_nested_lists(lines, (3, 7))
    print(2, len(new_lines))

    # 第三轮
    lines = new_lines
    del new_lines
    new_lines, new_roles = expand_nested_lists(lines, (1,), new_roles)
    print(3, len(new_lines))

    with open('data/expanded.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(new_lines))
