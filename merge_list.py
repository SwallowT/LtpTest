#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/5/20 17:06
# @Author  : tanly
# @Project ：SyntaxTree
# @File    : merge_list.py
from recgniz_pattern import main_proc
from expand_list import gen_list_struct

hiers = gen_list_struct()
hypers, hypos = main_proc()

all_pairs = []


def sparse_hypo_list(hyper:str, hypos:list):
    for item in hypos:
        if isinstance(item, str):
            all_pairs.append((hyper, item))
        elif isinstance(item, list):
            assert len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], list)
            sparse_hypo_list(item[0], item[1])


for hyper_line, hypo_line in hiers:
    hyper_line = str(hyper_line)
    hypo_line = str(hypo_line)
    if hyper_line in hypers:
        hyper_line_str = hypers[hyper_line]
    elif hyper_line in hypos:
        hyper_line_str = hypos[hyper_line]
    else:
        hyper_line_str = False

    if hypo_line in hypers:
        hypo_line_str = hypers[hypo_line]
    elif hypo_line in hypos:
        hypo_line_str = hypos[hypo_line]
    else:
        hypo_line_str = False

    if hypo_line_str and hyper_line_str:
        if isinstance(hypo_line_str, str):
            all_pairs.append((hyper_line_str, hypo_line_str))
        elif isinstance(hypo_line_str, list):
            sparse_hypo_list(hyper_line_str, hypo_line_str)

concurrence = set(hypers).intersection(set(hypos))
for t_id in concurrence:
    sparse_hypo_list(hypers[t_id], hypos[t_id])
print(all_pairs)

