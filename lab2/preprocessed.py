"""
对文本集合进行处理、建立索引.
检索模型：自己实现的向量空间模型.
"""
# todo 去停用词处理
# todo 现在计算tf与idf的log底数为10
# todo 现在计算相似度的查询权重为1
from util import load, dump, read_json, write_json, seg_line, passages_path, train_path
from math import pow, log
import os

model_path, preprocess_path = './preprocessed/vsm.json', './preprocessed/train_preprocessed.json'
weight = {}  # VSM模型权重矩阵，形式如：{pid: {word: weight}}


def seg_document(res_lst):  # 使用LTP进行分词操作，返回{pid:[[],[]]}
    res = {}
    for item in res_lst:  # 分词结果转换为list类型，去掉文本中的空格
        res[item['pid']] = [seg_line(line.replace(' ', '')) for line in item['document']]
    return res


def vsm_init():  # 从JSON文件中加载权重矩阵；若文件不存在，则重新初始化矩阵，并写入JSON文件，
    global weight
    if os.path.exists(model_path):
        print('正在加载VSM模型...')
        weight = load(model_path)
    else:
        print('正在创建VSM模型...')
        res_dic, words = seg_document(read_json(passages_path)), {}  # 词表，保存所有的词语，形式如：{word: log(N/df)]}
        print('分词完毕...')
        for pid, passage in res_dic.items():
            passage_words, weight[pid] = [word for word_lst in passage for word in word_lst], {}
            for word in passage_words:  # 计算每一个篇章中每一个词项的tf，结果保存在weight中
                if word not in weight[pid]:
                    weight[pid][word] = 0
                    words[word] = words[word] + 1 if word in words else 1  # 计算每一个词项的df，保存在words中
                weight[pid][word] += 1

        for word, df in words.items():  # 计算log(N/df)
            words[word] = log(len(res_dic) / df, 10)

        for pid in weight:  # 计算权重矩阵
            for word, tf in weight[pid].items():  # 遍历每一个词项
                weight[pid][word] = (1 + log(tf, 10)) * words[word]
        print('导出VSM模型...')
        dump(model_path, weight)


def calc_inner_product(query_dic: dict):  # {word: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res = {pid: sum([weight[pid][word] * w for word, w in query_dic.items() if word in weight[pid]]) for pid in weight}
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_cosine(query_dic: dict):  # {word: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res = {pid: sum([weight[pid][word] * w for word, w in query_dic.items() if word in weight[pid]]) for pid in weight}
    query_value = pow(sum([pow(w, 2) for w in query_dic.values()]), 0.5)  # 归一化查询的平方和的1/2
    for (pid, similarity) in res.items():  # res为内积结果
        doc_value = pow(sum([pow(w, 2) for w in weight[pid].values()]), 0.5)  # 归一化文档的平方和的1/2
        res[pid] = similarity / (query_value * doc_value)
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_jaccard(query_dic: dict):  # {word: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res = {pid: sum([weight[pid][word] * w for word, w in query_dic.items() if word in weight[pid]]) for pid in weight}
    query_value = sum([pow(w, 2) for w in query_dic.values()])  # 归一化中查询的平方和
    for (pid, similarity) in res.items():  # res为内积结果
        doc_value = sum([pow(w, 2) for w in weight[pid].values()])  # 归一化中文档的平方和
        res[pid] = similarity / (query_value + doc_value - similarity)
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_line(query, similarity_func=calc_inner_product):  # 计算一个查询的相似度
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    query_dic = {word: 1 for word in seg_line(query)}
    return similarity_func(query_dic)


def calc_vsm_perform(similarity_func):
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    if os.path.exists(preprocess_path):
        print('正在加载训练集的预处理文件...')
        res_lst = read_json(preprocess_path)  # 加载训练集初步处理后的文件
    else:
        print('正在预处理训练及文件...')
        res_lst = read_json(train_path)  # 加载训练集源文件
        for question in res_lst:
            question['question'] = seg_line(question['question'])
        print('分词结束，开始导出训练集的与处理文件...')
        write_json(preprocess_path, res_lst)

    print('正在计算相似度...')
    res = {}
    for question in res_lst:
        query_dic, pid = {word: 1 for word in question['question']}, question['pid']
        pred_pid = similarity_func(query_dic)[0][0]
        res[question['qid']] = int(pred_pid) == pid
        # print('进度: %.2f%%' % (len(res) / len(res_lst) * 100))
    return len(list(filter(lambda item: res[item], res))) / len(res)


def main():
    print('*' * 100)
    vsm_init()
    print('VSM模型内积准确率为: %.2f%%' % (calc_vsm_perform(calc_inner_product) * 100))
    print('*' * 100)


if __name__ == '__main__':
    main()
