from ltp import LTP
from s_expr_parse import trans2s_expr


def preprocessing():
    with open("data/useful_sent.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    trantab = str.maketrans(u',.!?:;()"\'', u'，。！？：；（）“‘')  # 制作翻译表
    lines = [ln.strip().replace(" ", "") for ln in lines]  # 去掉空格和换行符
    lines = [ln.translate(trantab) for ln in lines]  # 英文标点转换为中文
    sents = [ln for ln in lines if len(ln) > 0]   # 去掉空行

    return sents


def ltp_prepro(expand=True):
    preprocessing()
    ltp = LTP()
    sents = preprocessing()
    segments, hiddens = ltp.seg(sents)
    sdps = ltp.sdp(hiddens, mode='tree')
    # print("trees number", len(sdps))
    # if expand:
    #     new_sdps = []  # 把原文附在标记后面
    #     for segment, sdp in zip(segments, sdps):  # 一句
    #         new_sentents = []
    #         for seg, sd in zip(segment, sdp):  # 一词
    #             # new_sentents.append((sd[0], sd[1], sd[2] + "," + seg))
    #             new_sentents.append((sd[0], sd[1], sd[2], seg))
    #         new_sdps.append(new_sentents)

    return sents, ltp, sdps, segments, hiddens



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
