from ltp import LTP
from s_expr_parse import trans2s_expr

ltp = LTP()

with open("data/merged_useful_sent.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

sents = [ln.strip() for ln in lines]


segments, hiddens = ltp.seg(sents)
sdps = ltp.sdp(hiddens, mode='tree')
print("trees number", len(sdps))

new_sdps = []  # 把原文附在标记后面
for segment, sdp in zip(segments, sdps):  # 一句
    new_sentents = []
    for seg, sd in zip(segment, sdp):
        new_sentents.append((sd[0], sd[1], sd[2] + "," + seg))
    new_sdps.append(new_sentents)

# outputs = [trans2s_expr(sdp) for sdp in new_sdps]
outputs = []
for index, sdp in enumerate(new_sdps):
    outputs.append(trans2s_expr(sdp))

with open("data/trees_output_words.txt", "w", encoding="utf-8") as f:
    for out in outputs:
        f.write(out)
        f.write('\n')
