from ltp import LTP
from gen_tree import trans2s_expr


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


def ltp_prepro():
    """
    将文本转换为ltp对象
    :return: sents, ltp, sdps, segments, hiddens
    :rtype: tuple
    """
    ltp = LTP()
    sents = preprocessing()
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


if __name__ == '__main__':

    sents, ltp, sdps, segments, hiddens = ltp_prepro()

    outputs = [trans2s_expr(sdp, seg) for sdp, seg in zip(sdps, segments)]

    # outputs = []
    # for index, sdp in enumerate(new_sdps):
    #     outputs.append(trans2s_expr(sdp))

    with open("data/trees_output_words.txt", "w", encoding="utf-8") as f:
        for out in outputs:
            f.write(out)
            f.write('\n')

    # for index, sdp in enumerate(new_sdps):
    #     s_temp = trans2s_expr(sdp)
    #     with open(f"data/s_expr_files/tree_{index}.txt", 'w', encoding='utf-8') as f:
    #         f.write(s_temp)
