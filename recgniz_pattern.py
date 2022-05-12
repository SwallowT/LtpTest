import re

from operator import attrgetter
from treelib import Tree, Node
from typing import List, Dict, Tuple
import subprocess
from collections import defaultdict

from gen_tree import gen_node, load_from_sexp_file, show_tree
from expand_list import gen_list_struct
from gen_log import Logger

log = Logger('pat.log', level='debug', when='D')

SUB = ['AGT', 'EXP']
VEB = ['ePREC', 'eSUCC', 'ROOT']
OBJ = ['PAT', 'CONT', 'DATV', 'LINK']
# verb_keys = ['包括', '属于', '分为', '分成', '例如', '如', '比如', '有', '如下', '示例']

verb_keys = ['包括', '属于']
rev_verb_keys = ['属于']

constellation = ['、', '以及', '和', '/', '与']  # 并列关系

v_patterns: List[str] = []
output_pattern = {}

hypers_id = {}  # tree_id: 上义词id,
hypos_id = defaultdict(list)  # tree_id: [下义词id1, ...]
key_v_id = {}


def get_sdp_pos(tag: str, flag='sdp'):
    sdp, pos = tag.split("|")
    if flag == 'sdp':
        return sdp
    else:
        return pos


def is_hyper(data: str) -> bool:
    return data.endswith(("数据", "信息", '数据域')) and all([x not in data for x in ('、', '，')])


def is_hypo(data: str) -> bool:
    return any([c in data for c in constellation]) or \
           (data.endswith(("数据", "信息", '数据域')) and '的' not in data) or \
           '等' in data or 2 < len(data) < 5


def init_hyper(trees: List[Tree]):
    for tree in trees:
        hyper, hyper_id = 0, 0
        for node_id in tree.expand_tree(mode=tree.WIDTH):
            pat = r'/%s/ > '
            # Root在第一层，Root主语在第2层
            depth = tree.depth(node_id)
            if depth > 2:
                break
            if depth < 1:
                continue

            # node, data, sdp, pos
            node: Node = tree.get_node(node_id)
            node_data: str = node.data
            sdp_tag, pos_tag = node.tag.split("|", maxsplit=1)

            if is_hyper(node_data):
                # Root是动词，hyper是主语
                if depth == 2:
                    pre_pos = tree[node.predecessor(tree.identifier)].tag.split("|", maxsplit=1)[1]
                    if pre_pos == 'v' and sdp_tag in SUB:
                        #:
                        # print(tree[tree.root].data, node.identifier, node_data)
                        if not hyper or hyper_id > node_id:
                            hyper, hyper_id = node_data, node_id
                        else:
                            log.logger.info('hyper conflict: tree id %s, old %s, new %s' % (
                                tree[0].data, hyper, node_data))  # 上义词冲突，记录

                # Root是名词，hyper是Root
                elif depth == 1 and pos_tag == 'n':
                    if not hyper:
                        hyper, hyper_id = node_data, node_id
                    else:
                        log.logger.info('hyper conflict: tree id %s, old %s, new %s' % (
                            tree[0].data, hyper, node_data))  # 上义词冲突，记录
            if hyper_id:
                # hypers[tree[0].data] = hyper
                hypers_id[tree[0].data] = hyper_id


def init_hypo(trees: List[Tree]):
    new_hypos_id = update_hypo_and_revhyper(trees, verb_keys, rev_verb_keys)
    hypos_id.update(new_hypos_id)


def update_hypo_and_revhyper(trees: List[Tree], new_k_v: List[str], new_rev_k_v: List[str]):
    new_hypos_id = defaultdict(list)
    new_hypers_id = defaultdict(list)
    for tree in trees:
        for node_id in tree.expand_tree(mode=tree.WIDTH):
            # 跳过root、ROOT
            if tree.depth(node_id) < 2:
                continue

            # node, data, sdp, pos
            node: Node = tree.get_node(node_id)
            node_data: str = node.data
            sdp_tag, pos_tag = node.tag.split("|", maxsplit=1)

            parent_str = tree[node.predecessor(tree.identifier)].data
            if parent_str in new_k_v:
                tree_no = tree[0].data

                if parent_str in new_rev_k_v:
                    # 逆反关键动词
                    if is_hypo(node_data) and sdp_tag in SUB:
                        new_hypos_id[tree_no].append(node_id)
                    elif is_hyper(node_data) and sdp_tag in OBJ:
                        new_hypers_id[tree_no].append(node_id)

                elif is_hypo(node_data) and sdp_tag in OBJ:
                    # 父节点是关键动词，下义词是宾语
                    new_hypos_id[tree_no].append(node_id)

        # if len(hypos_current) > 0:
        #     print(tree[0].data, hypos_current)
        #     hypos[tree[0].data].extend(hypos_current)
    return new_hypos_id


def find_v_id(trees: List[Tree]):
    for tree in trees:
        # 已有，跳过
        tree_no = tree[0].data
        if tree_no in key_v_id:
            continue

        for node_id in tree.expand_tree(mode=tree.WIDTH):
            # 跳过root
            if tree.depth(node_id) < 1:
                continue

            node: Node = tree.get_node(node_id)
            if node.data in verb_keys:
                if node.data in rev_verb_keys:
                    key_v_id[tree_no] = 1000 + node_id
                else:
                    key_v_id[tree_no] = node_id
                break


def gen_tregex_from_shortest_path(trees):
    def gen_tgx_per_tree(tree: Tree, p: int, q: int):
        # 两树节点的最短路径：1.找到最近公共祖先；2.合并两节点到公共祖先的路径；3.生成tregex
        # p is hyper, q is hypo
        if not type(p) is int:
            print(p)
        if not type(q) is int:
            print(q)
        p_path, q_path = list(tree.rsearch(p)), list(tree.rsearch(q))
        p_path.reverse()
        q_path.reverse()

        # p_path是从Root到p的节点id列表

        def tag_escape(tag: str):
            return tag.replace('|', '\\|')

        def lowestCommonAncestor():

            if p in q_path:
                return p
            if q in p_path:
                return q

            last_common_ancestor = 0
            for p_anc, q_anc in zip(p_path, q_path):
                if p_anc != q_anc:
                    break
                else:
                    last_common_ancestor = p_anc
            return last_common_ancestor

        def gen_tregex(root: int, key_v_search=False):
            # root即公共祖先
            q_sub = q_path[q_path.index(root):]  # root到下义词
            p_sub = p_path[p_path.index(root) + 1:]
            p_sub.reverse()  # 上义词到root

            # 先形成下义词路径
            stack, q_str = 0, ''
            for i in q_sub[:-1]:
                if tree[i].data in verb_keys:  # 节点是关键动词，存为sdp+文本
                    if key_v_search:
                        q_str += r'(/,%s,/=keyv < ' % tag_escape(tree[i].tag)
                    else:
                        q_str += r'(/,%s.*,%s/ < ' % (get_sdp_pos(tree[i].tag, 'sdp'), tree[i].data)
                else:  # 其他，存为文本
                    q_str += r'(/,%s/ < ' % tree[i].data
                stack += 1
            # 节点是下义词，存为sdp+pos
            q_str += r'/,%s,/=hypo' % tag_escape(tree[q].tag)
            q_str += ')' * stack

            stack, p_str = 0, r'/,%s,/=hyper > ' % tag_escape(tree[p].tag)
            for i in p_sub[1:]:
                p_str += r'(/,%s/ > ' % tree[i].data
                stack += 1
            p_str.strip('>')
            p_str += q_str
            p_str += ')' * stack
            p_str.strip('()')

            return p_str

        root = lowestCommonAncestor()

        # output pattern
        tregex_out = gen_tregex(root, key_v_search=False)

        # searching-v pattern
        trgex_search_keyv = gen_tregex(root, key_v_search=True)

        return tregex_out, trgex_search_keyv

    new_search = []
    for t in trees:
        t_id = t[0].data
        if t_id in output_pattern.keys():
            continue
        if t_id in hypers_id.keys() and t_id in hypos_id.keys():
            for hypo in hypos_id[t_id]:
                tregex_out, trgex_search = gen_tgx_per_tree(t, hypers_id[t_id], hypo)

                output_pattern[t_id] = tregex_out

                if trgex_search not in v_patterns:
                    v_patterns.append(trgex_search)
                    new_search.append(trgex_search)

    return new_search


def tregex_search_terminal(pattern: str, para='-h hyper -h hypo'):
    """
    tregex命令行匹配
    :param pattern: tregex模式
    :param para: 参数, 会自动添上-u -n
    :return:匹配到的节点
    """
    parastr = '-u -n ' + para
    command = f"java -cp '/home/tanly/pywork/stanford-tregex/stanford-tregex.jar:' " \
              f"edu.stanford.nlp.trees.tregex.TregexPattern {parastr} '{pattern}' " \
              f"/home/tanly/pywork/SyntaxTree/data/cutted_trees_sexpr.txt "
    res = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    resstr = str(res.stdout, encoding='utf-8')
    return resstr


def parse_terminal(resstr):
    """解析tregex返回内容"""
    # 形如：
    # 4: 35, PAT, 数据
    # 41, LINK, 公开级（1级）、内部级（2级）、敏感级（3级）、
    # 4: 35, PAT, 数据
    # 67, LINK, 重要级（4级）、核心级（5级）五个级别
    if len(resstr) == 0:
        return
    assert ": " in resstr
    matches = resstr.strip().split('\n')
    allHasColon = True
    for mat in matches:
        if ": " not in mat:
            allHasColon = False
            break

    if not allHasColon:
        nodes_per_line: Dict[str, List[List[Node]]] = defaultdict(list)  # tree_id:[[node1,node2,...],...]
        tree_id, header = '0', Node()  # 第一行
        temp_node_list: List[Node] = []
        for mat in matches:
            if ": " in mat:
                # 存储上一组节点
                nodes_per_line[tree_id].append(temp_node_list)
                temp_node_list = []
                # 开启下一组节点
                tree_id, header_str = mat.split(': ', maxsplit=1)
                header = gen_node(header_str)
                temp_node_list.append(header)
            else:
                suc_node = gen_node(mat)
                temp_node_list.append(suc_node)
        nodes_per_line.pop('0')
        return nodes_per_line
    else:
        kv_node_per_line: Dict[str, Node] = {}
        for mat in matches:
            tree_id, kv_str = mat.split(': ', maxsplit=1)
            kv_node = gen_node(kv_str)
            kv_node_per_line[tree_id] = kv_node
        return kv_node_per_line


def split_hypo(hypo_sent: str) -> list:
    # 假设：左右括号完整，没有嵌套括号
    if "、" in hypo_sent:  # 分开逗号分割的子句
        subs = re.split('[，；。]', hypo_sent)
        sep = constellation
    else:
        subs = re.split('[；。]', hypo_sent)
        sep = constellation + ['，']

    res = []  # 'A(B、C)' -> ['A', ['B', 'C']]
    is_inBracket = False
    is_after_colon = False
    for sb in subs:
        ent_list = re.split('|'.join(sep), sb)

        if len(ent_list) == 1:
            res.extend(ent_list)
            continue

        for ent in ent_list:
            if len(ent) == 0:
                continue

            rm_reg = re.compile('等.*')

            if "（" in ent and "）" not in ent:  # eg. 存款信息（包括资金数量

                is_inBracket = True

                p, c = ent.split("（")
                for v in verb_keys: c = c.strip(v)  # 去掉“包括”
                res.append([p, [c]])

            elif is_inBracket:  # eg. 业务订购等）数据等
                assert isinstance(res[-1][-1], list)

                if "）" in ent:
                    is_inBracket = False
                    c, p = ent.split("）")
                    c, p = rm_reg.sub('', c), rm_reg.sub('', p)
                    res[-1][-2] += p
                    res[-1][-1].append(c)
                else:
                    res[-1][-1].append(ent)

            elif "：" in ent:  # 示例：老年人优待证信息，无偿献血证
                p, c = ent.split("：")
                c = rm_reg.sub('', c)
                if p in verb_keys:
                    res.append(c)
                else:
                    res.append([p, [c]])
                    is_after_colon = True
            elif is_after_colon:
                res[-1][-1].append(rm_reg.sub('', ent))
            else:
                res.append(rm_reg.sub('', ent))
    # print(res)
    return res


def search_kv_by_tregex(v_search_pattern):
    """搜索新的关键动词"""
    new_v: List[Node] = []
    new_rev_v: List[Node] = []

    all_new_v = []

    for trgx in v_search_pattern:

        res = tregex_search_terminal(trgx, para='-h keyv -h hyper -h hypo')
        nodes_perline = parse_terminal(res)

        if not nodes_perline:
            continue

        for t_id, nodes_list in nodes_perline.items():
            for keyv, hyper, hypo in nodes_list:
                if keyv.data in all_new_v or keyv.data in verb_keys:
                    break
                if keyv.data not in verb_keys:
                    if is_hyper(hyper.data) and is_hypo(hypo.data):
                        new_v.append(keyv)
                        all_new_v.append(keyv.data)
                    elif is_hyper(hypo.data) and is_hypo(hyper.data):  # 交换位置
                        new_rev_v.append(keyv)
                        all_new_v.append(keyv.data)
                    else:
                        log.logger.info("上义词或下义词被过滤。keyv, hyper, hypo依次为：%s %s %s" % (keyv.data, hyper.data, hypo.data))

    return new_v, new_rev_v


def search_ent_by_tregex(new_v: List[Node], new_rev_v: List[Node]):
    """生成新的pattern，match新的上下义词"""
    new_hypers_id = {}  # tree_id: 上义词id,
    new_hypos_id = defaultdict(list)  # tree_id: [下义词id1, ...]

    for keyv in new_v:
        for pat in v_patterns:
            # 用新的动词替换旧的pattern v
            forsub = ",%s.*,%s" % (get_sdp_pos(keyv.tag), keyv.data)
            temp_pat = re.sub(r'(?<=\(/)(,[A-Za-z]+\\\|[a-z]+,)(?=/=keyv <)', forsub, pat)
            temp_pat = temp_pat.replace('=keyv', '')
            if keyv in new_rev_v:  # 交换hyper、hypo
                temp_pat = temp_pat.replace('hyper', 'temp')
                temp_pat = temp_pat.replace('hypo', 'hyper')
                temp_pat = temp_pat.replace('temp', 'hypo')

            # 用新的pattern搜索新的上下义词
            tregex_res_str = tregex_search_terminal(pattern=temp_pat)
            nodes_dict: Dict[str, List[List[Node]]] = parse_terminal(tregex_res_str)
            if not nodes_dict:
                continue

            for t_id, pairs in nodes_dict.items():
                for hyper, hypo in pairs:
                    if is_hyper(hyper.data) and is_hypo(hypo.data):
                        if t_id not in output_pattern:
                            output_pattern[t_id] = temp_pat
                            log.logger.debug('output pattern: %s, tid: %s, hyper: %s, hypo: %s' %
                                             (temp_pat, t_id, hyper, hypo))
                        # 存上义词
                        if t_id not in hypers_id:
                            new_hypers_id[t_id] = hyper.identifier
                        elif hypers_id[t_id] != hyper.identifier:
                            log.logger.info('hyper conflict: tree id %s, old %s, new %s' % (
                                t_id, hypers_id[t_id], hyper.data))  # 上义词冲突，记录
                        # 存下义词
                        if t_id not in hypos_id or hypo.identifier not in hypos_id[t_id]:
                            new_hypos_id[t_id].append(hypo.identifier)

    return new_hypers_id, new_hypos_id


def merge_hypos(hypos: Dict[str, List]):
    """
    将新的hypo添加到hypos_id，去重
    :param hypos: tree_id: [hypo_node_id]
    :type hypos: dict
    :return:
    :rtype:
    """
    for t_id, _hypos in hypos.items():
        if t_id not in hypos_id:
            hypos_id[t_id] = list(set(_hypos))
            continue

        for _hypo_id in _hypos:
            if _hypo_id not in hypos_id[t_id]:
                hypos_id[t_id].append(_hypo_id)


def exam_identical_hyper_hypo():
    concurrence = set(hypers_id).intersection(set(hypos_id))
    for t_id in concurrence:
        _hyper = hypers_id[t_id]
        for _hypo in hypos_id[t_id]:
            if _hyper == _hypo:
                if t_id in key_v_id:
                    # 在关键动词前的就是主语
                    v_id = key_v_id[t_id]
                    if v_id > 1000:  # 逆反
                        if _hyper < v_id - 1000:  # hyper在v_id前，是主语，错误
                            hypers_id.pop(t_id)
                        else:
                            hypos_id[t_id].remove(_hypo)
                    else:
                        if _hyper < v_id:  # hyper在v_id前，是主语，正确
                            hypos_id[t_id].remove(_hypo)
                        else:
                            hypers_id.pop(t_id)
                else:
                    hypos_id[t_id].remove(_hypo)


def main_proc():
    # 初始化
    trees = load_from_sexp_file()
    init_hyper(trees)
    init_hypo(trees)
    find_v_id(trees)
    exam_identical_hyper_hypo()
    new_v_search_pattern = gen_tregex_from_shortest_path(trees)
    times = 1
    for t_id, pt in output_pattern.items(): log.logger.debug(t_id + " " + pt)

    # 循环
    while times < 10:
        log.logger.debug('time: ' + str(times))

        # 搜索新的关键动词
        new_v, new_rev_v = search_kv_by_tregex(new_v_search_pattern)
        all_new_v = new_v + new_rev_v
        all_new_v_str = [vnode.data for vnode in all_new_v]
        new_rev_v_str = [vnode.data for vnode in new_rev_v]

        if not len(all_new_v):
            break
        log.logger.debug('new key verb: '+str(all_new_v_str))

        # 生成新的模式，搜索新的上下义词
        # 1. 新关键动词替换旧动词，代入旧的tregex，生成了新的模式；搜索新的上下义词
        new_hypers_id, new_hypos_id = search_ent_by_tregex(all_new_v, new_rev_v)
        # 2. 搜索新动词的宾语；root不变，init hyper不变，而init hypo随key v增加而增加
        new_hypos_id2 = update_hypo_and_revhyper(trees, all_new_v_str, new_rev_v_str)

        if not (len(new_hypers_id) + len(new_hypos_id2) + len(new_hypos_id)):
            break

        # 将新上下义词加入总集
        hypers_id.update(new_hypers_id)
        merge_hypos(new_hypos_id)
        merge_hypos(new_hypos_id2)
        # 将新动词加入总集
        verb_keys.extend(all_new_v_str)
        rev_verb_keys.extend(new_rev_v_str)

        # 去除上下义词相同的情况
        find_v_id(trees)
        exam_identical_hyper_hypo()
        # 生成最短路径tregex，输出
        new_v_search_pattern = gen_tregex_from_shortest_path(trees)

        times += 1

    # 上义词的id转换为文本
    hypers_str = dict()
    for t_id, node_id in hypers_id.items():
        node = trees[int(t_id) - 1].get_node(node_id)
        node_data: str = node.data

        # if '的' in node_data:
        #     former, latter = node_data.split('的', maxsplit=1)
        #     if len(latter) > 2:
        #         node_data = latter

        hypers_str[t_id] = node_data

    # 下义词的id转换为文本，同时分开
    hypos_str = defaultdict(list)
    for t_id, nodes_ids in hypos_id.items():
        tree = trees[int(t_id) - 1]
        for node_id in nodes_ids:
            node = tree.get_node(node_id)
            node_data = node.data

            hypos_current = []
            if node.is_leaf(tree.identifier):
                # 叶节点，直接加
                hypos_current.append(node_data)
            else:
                # 子节点重排序
                descendants: List[Node] = tree.subtree(node_id).all_nodes()  # 包括node自己
                sorted_desc = sorted(descendants, key=attrgetter('identifier'))
                for desc in sorted_desc:
                    if len(hypos_current) == 0 or \
                            ('eCOO' in desc.tag and "（" not in desc.data and "）" not in desc.data):
                        # 没有括号的并列关系，直接加
                        hypos_current.append(desc.data)
                    else:
                        # 其他合并
                        hypos_current[-1] += desc.data
            for hypo_sent in hypos_current:
                splitted_hypos = split_hypo(hypo_sent)
                hypos_str[t_id].extend(splitted_hypos)

    # 打印结果
    print('---------result--------------')
    # 打印pattern
    instinct_pattern = set(output_pattern.values())
    for i in instinct_pattern: log.logger.info("output pattern: " + i)
    # 打印上下义词
    for i in range(len(trees)):
        index = str(i + 1)
        if index in hypers_str:
            log.logger.debug(index + ' hyper:' + hypers_str[index])
        if index in hypos_str:
            log.logger.debug(index + ' hypo:' + str(hypos_str[index]))
    return hypers_str, hypos_str


if __name__ == '__main__':
    hypers, hypos = main_proc()
