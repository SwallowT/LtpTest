# from ltp import LTP
#
# from gen_tree import load_from_ltp_tuple, show_tree
# from ltp_standard import add_pos
# from cutTree import cut_tree
#
# ltp = LTP()
# ltp.init_dict(path="data/user_dict.txt", max_window=4)
# # ltp.add_words(words=['用户鉴别辅助信息'], max_window=4)
# segments, hiddens = ltp.seg(['支付敏感信息包括但不限于银行卡磁道数据或芯片等效信息、卡片验证码、卡片有效期、银行卡密码、网络支付交易密码等用于支付鉴权的个人金融信息。'])
# sdps = ltp.sdp(hiddens, mode='tree')
# sdps = add_pos(ltp, hiddens, sdps)
# outputs = [load_from_ltp_tuple(sdp, seg, id) for id, (sdp, seg) in enumerate(zip(sdps, segments))]
#
# for t in outputs:
#     show_tree(t)
#     show_tree(cut_tree(t))

# ------------------

import pickle
from recgniz_pattern import hyper_node2str, hypo_node2str

with open('../data/serialized/cutted_trees', 'rb') as f:
    trees = pickle.load(f)
with open('../data/serialized/hypers_hypos_id', 'rb') as f:
    hypers_id, hypos_id = pickle.load(f)

hyper_str = hyper_node2str(trees, hypers_id)
hypo_str = hypo_node2str(trees, hypos_id)

with open('../data/serialized/text_hypers_for_line', 'wb') as f:
    pickle.dump(hyper_str, f)
with open('../data/serialized/text_hypos_for_line', 'wb') as f:
    pickle.dump(hypo_str, f)
print(len(hyper_str), len(hypo_str))
for t_id, hypos in hypo_str.items():
    print(t_id)
    print(hypos)