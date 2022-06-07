#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/6/1 10:33
# @Author  : tanly
# @Project ：SyntaxTree
# @File    : evaluate.py
import pickle
from operator import itemgetter

import logging

logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='../data/logs/evaluate-0606.log',
                    filemode='w',  # 模式，有w和a，默认是a
                    format=
                    '%(message)s'
                    )


def get_standards(path: str):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    all_hypers, all_hypos = [], []

    for ln in lines:
        ln = ln.strip()
        if '：' in ln:
            hyper, hypos = ln.split('：', maxsplit=1)
            if len(hyper) > 0:
                all_hypers.append(hyper)
            hypos_sp = hypos.split('、')
            all_hypos.extend(hypos_sp)
        else:
            all_hypers.append(ln)
    return set(all_hypers), set(all_hypos)


def expand_nested_structure(nested_lists):
    # all_pairs = []
    all_hypers, all_hypos = [], []

    def sparse_hypo_list(hyper: str, hypos: list):
        for item in hypos:
            if isinstance(item, str):
                # all_pairs.append((hyper, item))
                all_hypers.append(hyper)
                all_hypos.append(item)
            elif isinstance(item, list):
                assert len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], list)
                sparse_hypo_list(item[0], item[1])

    for n_l in nested_lists:
        for elem in n_l:
            if isinstance(elem, str):
                all_hypos.append(elem)
            elif isinstance(elem, list):
                assert len(elem) == 2 and isinstance(elem[0], str) and isinstance(elem[1], list)
                sparse_hypo_list(elem[0], elem[1])
            else:
                print(elem, 'wrong type')

    return set(all_hypers), set(all_hypos)


def calculate_indicators(P: set, detected: set, name: str, isprint=True):
    output = ''

    TP_elems = P.intersection(detected)
    FP_elems = detected - P
    FN_elems = P - detected
    TP, FP, FN = len(TP_elems), len(FP_elems), len(FN_elems)
    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    f1 = 2 * ((precision * recall) / (precision + recall))

    if isprint:
        output += 'FN %s %s\n' % (FN, FN_elems)
        output += 'FP %s %s\n' % (FP, FP_elems)
        output += 'TP %s %s\n' % (TP, TP_elems)
    output += ('\n'
               '{0}_TP: {1} \n'
               '{0}_FP: {2} \n'
               '{0}_FN: {3} \n'
               '{0} precision: {4} \n'
               '{0} recall: {5} \n'
               '{0} f1: {6}\n\n'.format(name, TP, FP, FN, precision, recall, f1))
    return output, (TP, FP, FN)


if __name__ == '__main__':

    with open('../data/serialized/text_all_hypers_hypos', 'rb') as f:
        text_all_hypers, text_all_hypos = pickle.load(f)
    # text_all_hypers = set(map(itemgetter(0), text_all_pairs))
    # text_all_hypos = set(map(itemgetter(1), text_all_pairs))
    hypers_P, hypos_P = get_standards('../data/standard/useful_hyperhypo.txt')
    er, (TP11, FP11, FN11) = calculate_indicators(hypers_P, text_all_hypers, 'hyper')
    o, (TP12, FP12, FN12) = calculate_indicators(hypos_P, text_all_hypos, 'hypo')
    logging.debug(er)
    logging.debug(o)
    print(er)
    print(o)
