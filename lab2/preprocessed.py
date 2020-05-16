"""
对文本集合进行处理、建立索引.
检索模型：自己实现的向量空间模型.
"""
# todo 去停用词处理
# todo 现在计算tf与idf的log底数为10
cws_model_path = 'E:\pyltp\ltp_data_v3.4.0\cws.model'  # pyltp模型文件路径
passages_path = './data/passages_multi_sentences.json'

words = {}  # 词表，保存所有的词语，形式如：{word: log(N/df)]}
weight = {}  # 权重矩阵，形式如：{pid: {word: weight}}


def read_json(json_path):  # 读取json文件，要求每一行都是标准的json格式文件，返回：list[python对象]
    with open(json_path, 'r', encoding='utf-8') as f:
        import json
        return [json.loads(json_line) for json_line in f]


def seg_document(res_lst):  # 使用LTP进行分词操作，返回{pid:[[],[]]}
    from pyltp import Segmentor
    seg, res = Segmentor(), {}
    seg.load(cws_model_path)  # 加载模型
    for item in res_lst:  # 分词结果转换为list类型，去掉文本中的空格
        res[item['pid']] = [list(seg.segment(str(line).replace(' ', ''))) for line in item['document']]
    seg.release()  # 释放模型
    return res


def output(res_dic):  # 测试程序
    with open('./res_dic.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(res_dic, f, ensure_ascii=False)


def input():  # 测试程序
    with open('./res_dic.json', 'r', encoding='utf-8') as f:
        import json
        return json.load(f)


def calc_weight_matrix(res_dic):  # 计算权重矩阵
    global words, weight
    for pid, passage in res_dic.items():
        passage_words, weight[pid] = [word for word_lst in passage for word in word_lst], {}
        for word in passage_words:  # 计算每一个篇章中每一个词项的tf，结果保存在weight中
            if word not in weight[pid]:
                weight[pid][word] = 0
                words[word] = words[word] + 1 if word in words else 1  # 计算每一个词项的df，保存在words中
            weight[pid][word] += 1

    from math import log
    for word, df in words.items():  # 计算log(N/df)
        words[word] = log(len(res_dic) / df, 10)

    for pid in weight:  # 计算权重矩阵
        for word, tf in weight[pid].items():  # 遍历每一个词项
            weight[pid][word] = (1 + log(tf, 10)) * words[word]


def similarity_inner_product(query_dic: dict):  # {word: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res = {pid: sum([weight[pid][word] * w for word, w in query_dic.items() if word in weight[pid]]) for pid in weight}
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def similarity_cosine(query_dic: dict):  # {word: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res, inner_product_res = {}, similarity_inner_product(query_dic)  # 得到内积结果
    from math import pow
    query_value = pow(sum([pow(w, 2) for w in query_dic.values()]), 0.5)  # 归一化查询的平方和的1/2
    for (pid, similarity) in inner_product_res:
        doc_value = pow(sum([pow(w, 2) for w in weight[pid].values()]), 0.5)  # 归一化文档的平方和的1/2
        res[pid] = similarity / (query_value * doc_value)
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def similarity_jaccard(word_lst: list):
    pass


def main():
    # res = read_json(passages_path)
    # res = seg_document(res)
    # output(res)
    res_dic = input()
    calc_weight_matrix(res_dic)
    res = similarity_cosine({'我': 1, '喜欢': 1, '腾讯': 1, '公司': 1})


if __name__ == '__main__':
    main()
