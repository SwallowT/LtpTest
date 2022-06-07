#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/5/27 11:36
# @Author  : tanly
# @Project ：SyntaxTree
# @File    : parse_table_hypos.py
import re
from typing import List

import logging
from treelib import Tree, Node

from ltp_standard import ltp_prepro, add_pos
from gen_tree import trans2s_expr, load_from_sexp_file, save2s_expr, gen_tree_from_sexpr, show_tree, gen_node
from cutTree import cut_tree
from recgniz_pattern import main_proc, tregex_search_terminal, split_hypo
from evaluate import get_standards, expand_nested_structure, calculate_indicators

from collections import defaultdict
from operator import itemgetter, attrgetter


def LTP_TREE():
    sents, ltp, sdps, segments, hiddens = ltp_prepro('../data/表格复合下义.txt')

    sdps = add_pos(ltp, hiddens, sdps)

    outputs = [trans2s_expr(sdp, seg, id) for id, (sdp, seg) in enumerate(zip(sdps, segments))]

    with open("../data/TABLE/trees_output_words.txt", "w", encoding="utf-8") as f:
        for out in outputs:
            f.write(out)
            f.write('\n')


def CUT_TREE():
    trees = load_from_sexp_file('../data/TABLE/trees_output_words.txt')

    with open(f'../data/TABLE/cutted_trees_sexpr.txt', 'w', encoding='utf-8') as f:  # merged
        for i, tree in enumerate(trees):
            cutted_tree = cut_tree(tree)
            # show_tree(cutted_tree)
            f.write(save2s_expr(cutted_tree))


def parse_terminal_hypo(res: str):
    if ":" not in res:
        return
    line_trees = defaultdict(list)
    tree_lines = res.strip().split('\n\n')
    for tr in tree_lines:
        t_id, tr_line = tr.split(": ")
        line_trees[int(t_id)].append(gen_tree_from_sexpr(tr_line))

    return line_trees

def parse_termianl_hyper_hypo(res:str):
    if ":" not in res:
        return
    pairs = re.split('\n\n(?=[0-9]+:)', res)
    records_t = defaultdict(list)
    _line_splitted = defaultdict(list)
    for tpr in pairs:
        t_id, pr = tpr.split(': ', maxsplit=1)
        hyper_str, hypo_str = pr.split('\n\n', maxsplit=1)

        hyper = gen_node(hyper_str)
        hypo = gen_tree_from_sexpr(hypo_str)

        splitted, record = parse_hypo(hypo, [])
        records_t[int(t_id)].extend(record)
        _line_splitted[int(t_id)].append([hyper.data, splitted])
    return records_t, _line_splitted


def RECGNIZ_TREGEX_PATTERN():
    line_hypo = defaultdict(list)
    line_splitted = defaultdict(list)
    records_t = 0
    with open('../data/TABLE/patterns.txt') as f:
        all_patterns = f.readlines()
    for pat in all_patterns:
        if 'hyper' in pat:
            res = tregex_search_terminal(pat, para='-h hyper -h hypo',
                                         filepath='/home/tanly/pywork/SyntaxTree/data/TABLE/cutted_trees_sexpr.txt')
            if len(res) == 0:
                continue
            records_t, _line_splitted = parse_termianl_hyper_hypo(res)
            line_splitted.update(_line_splitted)

        else:
            res = tregex_search_terminal(pat, para='-h hypo',
                                         filepath='/home/tanly/pywork/SyntaxTree/data/TABLE/cutted_trees_sexpr.txt')
            if len(res) == 0:
                continue
            res_dct = parse_terminal_hypo(res)
            for t_id, trees in res_dct.items():
                line_hypo[int(t_id)].extend(trees)

    for t_id, trees in line_hypo.items():
        if isinstance(records_t, dict) and t_id in records_t.keys():
            record = records_t[t_id]
        else:
            record=[]
        for t in trees:
            splitted, record = parse_hypo(t, record)
            line_splitted[int(t_id)].extend(splitted)
    return line_splitted


def parse_hypo(tree: Tree, record:list):
    hypos_whole = []
    hypos_splitted = []
    descendants: List[Node] = tree.all_nodes()  # 包括node自己
    sorted_desc = sorted(descendants, key=attrgetter('identifier'))
    for desc in sorted_desc:
        if desc.identifier==-1:
            continue
        if desc.identifier in record:
            continue
        else:
            record.append(desc.identifier)
        if len(hypos_whole) == 0 or \
                ('eCOO' in desc.tag and "（" not in desc.data and "）" not in desc.data):
            # 没有括号的并列关系，直接加
            hypos_whole.append(desc.data)
        else:
            # 其他合并
            hypos_whole[-1] += desc.data
    for hypo_sent in hypos_whole:
        splitted_hypos = split_hypo(hypo_sent)
        hypos_splitted.extend(splitted_hypos)
    return hypos_splitted, record


def REGEX_PATTERNS(skip_tids):
    with open('../data/表格复合下义.txt', encoding='utf-8') as f:
        original = f.readlines()

    pattern1 = re.compile('示例：(.+?，)+(.+)')
    # pattern2 = re.compile('([0-9]-?)+[\u4e00-\u9fa5]*：[\u4e00-\u9fa5]*')
    be_left = set(range(1, len(original) + 1)) - set(skip_tids)
    res_hypos = {}

    for t_id in be_left:
        line = original[t_id - 1].strip()
        res = pattern1.search(line)
        if res:  # '：' in line and '数据级别数据特征' not in line
            sent = res.group()
            res_hypos[t_id] = (split_hypo(sent))
        else:
            # res = pattern2.search(line)
            res_hypos[t_id] = split_hypo(line)
    return res_hypos


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                        filename='../data/logs/TABLE-evaluate-0606.log',
                        filemode='w',  # 模式，有w和a，默认是a
                        format=
                        '%(message)s'
                        )
    # LTP_TREE()
    # CUT_TREE()

    line_hypo_treg = RECGNIZ_TREGEX_PATTERN()
    line_hypo_reg = REGEX_PATTERNS(line_hypo_treg.keys())

    line_hypo = {}
    line_hypo.update(line_hypo_reg)
    line_hypo.update(line_hypo_treg)

    # sorted_line_hypo = sorted(line_hypo.items(), key=itemgetter(0))
    # for t_id, lists in sorted_line_hypo:
    #     print(t_id)
    #     # for t in trees: show_tree(t)
    #     print(lists)
    #
    # print(len(line_hypo))
    hypers_P, hypos_P = get_standards('../data/standard/table_hypos.txt')
    hypers, hypos = expand_nested_structure(line_hypo.values())

    print(calculate_indicators(hypers_P, hypers, 'hyper'))
    print(calculate_indicators(hypos_P, hypos, 'hypo'))
