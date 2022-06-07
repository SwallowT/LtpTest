import pickle
import re

from ltp import LTP
from gen_tree import trans2s_expr, load_from_ltp_tuple, save2s_expr


def preprocessing(path="data/useful_sent.txt"):
    """预处理：去掉空格和换行符，英文标点转换为中文，去掉空行
    :rtype: list
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    trantab = str.maketrans(u',.!?:;()"\'', u'，。！？：；（）“‘')  # 制作翻译表
    lines = [ln.strip().replace(" ", "") for ln in lines]  # 去掉空格和换行符
    lines = [ln.translate(trantab) for ln in lines]  # 英文标点转换为中文
    sents = [ln for ln in lines if len(ln) > 0]  # 去掉空行

    return sents


def ltp_prepro(path="data/useful_sent.txt"):
    """
    将文本预处理，转换为ltp对象
    :return: sents, ltp, sdps, segments, hiddens
    :rtype: tuple
    """
    # 读取文本，去除前面的列表符号
    old_sents = preprocessing(path)
    sents = [re.sub('^(\*|[a-z]）|[0-9]+）|—|（[一二三四五六七八九十]+）)\s?', '', s) for s in old_sents]
    # 转换为ltp对象
    ltp = LTP()
    ltp.init_dict(path="../data/user_dict.txt", max_window=4)
    segments, hiddens = ltp.seg(sents)
    sdps = ltp.sdp(hiddens, mode='tree')

    return sents, ltp, sdps, segments, hiddens


def save2file(sdps, segs, path1="data/ltp_sdps.txt", path2="data/ltp_segs.txt"):
    """ltp存到文件"""
    for ltp_s, path in ((sdps, path1), (segs, path2)):
        with open(path, "w", encoding="utf-8") as f:
            f.write('[')
            for s in ltp_s:
                f.write(str(s))
                f.write(', \n')
            f.write(']')


def add_pos(ltp, hiddens, sdps):
    """在语义依存树上添加词性, part of speech, pos"""
    poss = ltp.pos(hiddens)

    new_sdps = []
    for sdp, pos in zip(sdps, poss):
        new_sdps.append([(p, c, tag + '|' + pos) for (p, c, tag), pos in zip(sdp, pos)])

    return new_sdps


if __name__ == '__main__':

    sents, ltp, sdps, segments, hiddens = ltp_prepro()

    sdps = add_pos(ltp, hiddens, sdps)

    tree_outputs = [load_from_ltp_tuple(sdp, seg, id) for id, (sdp, seg) in enumerate(zip(sdps, segments))]
    with open('../data/serialized/original_trees', 'wb') as f:
        pickle.dump(tree_outputs, f)

    # outputs = [trans2s_expr(sdp, seg, id) for id, (sdp, seg) in enumerate(zip(sdps, segments))]
    outputs = [save2s_expr(tree) for tree in tree_outputs]
    with open("../data/trees_output_words.txt", "w", encoding="utf-8") as f:
        for out in outputs:
            f.write(out)
            f.write('\n')
