#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/5/20 17:06
# @Author  : tanly
# @Project ：SyntaxTree
# @File    : merge_list.py
import pickle

from operator import itemgetter

from expand_list import gen_list_struct
from evaluate import expand_nested_structure

hiers = gen_list_struct()
with open('../data/serialized/text_hypers_for_line', 'rb') as f:
    hypers: dict = pickle.load(f)
with open('../data/serialized/text_hypos_for_line', 'rb') as f:
    hypos: dict = pickle.load(f)

all_pairs = []
all_hypers, all_hypos = [], []


def sparse_hypo_list(hyper: str, hypos: list):
    for item in hypos:
        if isinstance(item, str):
            all_pairs.append((hyper, item))
            all_hypers.append(hyper)
        elif isinstance(item, list):
            assert len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], list)
            sparse_hypo_list(item[0], item[1])


for hyper_line, hypo_line in hiers:
    hyper_line = str(hyper_line)
    hypo_line = str(hypo_line)
    if hyper_line in hypers:
        hyper_line_str = hypers[hyper_line]
    elif hyper_line in hypos:
        hyper_line_str = False
        print(hyper_line, end='\t')
        print(hypos[hyper_line])
    else:
        hyper_line_str = False
        print(hyper_line)

    if hypo_line in hypers:
        hypo_line_str = hypers[hypo_line]
    elif hypo_line in hypos:
        hypo_line_str = hypos[hypo_line]
    else:
        hypo_line_str = False

    if hypo_line_str and hyper_line_str:
        if isinstance(hypo_line_str, str):
            all_pairs.append((hyper_line_str, hypo_line_str))
            all_hypos.append(hypo_line_str)
        elif isinstance(hypo_line_str, list):
            sparse_hypo_list(hyper_line_str, hypo_line_str)

# all_hypers.extend([map(itemgetter(0), all_pairs)])
# all_hypos.extend([map(itemgetter(1), all_pairs)])

# concurrence = set(hypers).intersection(set(hypos))
# for t_id in concurrence:
#     sparse_hypo_list(hypers[t_id], hypos[t_id])
# with open('data/serialized/text_all_pairs', 'wb') as f:
#     pickle.dump(all_pairs, f)
# print(all_pairs)

all_hypers.extend([v for k, v in hypers.items()])  # hyper

_hypers, _hypos = expand_nested_structure(hypos.values())  # hypo内部的_hyper _hypo
all_hypers.extend(_hypers) # 添加_hyper
all_hypos.extend(_hypos)
all_hypos.extend(_hypers) # _hyper也是hypo

with open('../data/serialized/text_all_hypers_hypos', 'wb') as f:
    pickle.dump([set(all_hypers), set(all_hypos)], f)

print(all_hypos)