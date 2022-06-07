#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/5/26 16:01
# @Author  : tanly
# @Project ：SyntaxTree
# @File    : fenji_recgniz.py
from recgniz_pattern import tregex_search_terminal, parse_terminal, is_hyper
from typing import Dict, List
from treelib import Node

patterns = [
    '/EXP\|n/=hyper > (/v,低于/ < /[0-9]级/=hypo < /mNEG/)'
]

for pat in patterns:
    res = tregex_search_terminal(pat)
    res_dict: Dict[str, List[List[Node]]] = parse_terminal(res)
    for t_id, node_list in res_dict.items():
        for hyper, hypo in node_list:
            # if is_hyper(hyper.data):
            print(hyper, hypo)