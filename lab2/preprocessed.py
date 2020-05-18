"""
对文本集合进行处理、建立索引.
检索模型：自己实现的向量空间模型.
"""
# todo 去停用词处理
# todo 现在计算tf与idf的log底数为10
# todo 现在计算相似度的查询权重为1
from pyltp import Segmentor
from math import pow, log
import json
import os

cws_model_path = 'E:/pyltp/ltp_data_v3.4.0/cws.model'  # pyltp模型文件路径
vsm_model_path = './preprocessed/vsm.json'  # VSM模型的权重路径
passages_path = './data/passages_multi_sentences.json'
train_path = './data/train.json'  # 训练集文本
train_preprocess_path = './preprocessed/train_preprocessed.json'  # 训练集初步分词的结果
word2tid, weight = {}, {}  # {word: tid}；VSM模型权重矩阵，形式如：{pid: {tid: weight}}


def read_json(json_path):  # 读取json文件，要求每一行都是标准的json格式文件，返回：list[python对象]
    with open(json_path, 'r', encoding='utf-8') as f:
        return [json.loads(json_line) for json_line in f]


def write_json(json_path, obj):  # 导出json文件，输出的每一行都是标准的json格式文件，输入：list[python对象]
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join([json.dumps(item, ensure_ascii=False) for item in obj]))


def load(json_path):  # 读取JSON文件，获取python数据结构
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def dump(json_path, obj):  # 导出python对象到JSON文件中
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)


def seg_document(res_lst):  # 使用LTP进行分词操作，返回{pid:[[],[]]}
    seg, res = Segmentor(), {}
    seg.load(cws_model_path)  # 加载模型
    for item in res_lst:  # 分词结果转换为list类型，去掉文本中的空格
        res[item['pid']] = [list(seg.segment(str(line).replace(' ', ''))) for line in item['document']]
    seg.release()  # 释放模型
    return res


def vsm_init():  # 从JSON文件中加载权重矩阵；若文件不存在，则重新初始化矩阵，并写入JSON文件，
    global weight, word2tid
    if os.path.exists(vsm_model_path):
        print('正在加载VSM模型...')
        json_dic = load(vsm_model_path)
        word2tid, weight = json_dic['word2tid'], json_dic['weight']
    else:
        print('正在创建VSM模型...')
        json_dic, words = seg_document(read_json(passages_path)), {}  # 词表，保存所有的词语，形式如：{tid: log(N/df)]}
        print('分词完毕...')
        for pid, passage in json_dic.items():
            passage_words, weight[pid] = [word for word_lst in passage for word in word_lst], {}
            for word in passage_words:  # 计算每一个篇章中每一个词项的tf，结果保存在weight中
                if word not in word2tid:
                    word2tid[word] = len(word2tid)
                tid = word2tid[word]
                if tid not in weight[pid]:
                    weight[pid][tid] = 0
                    words[tid] = words[tid] + 1 if tid in words else 1  # 计算每一个词项的df，保存在words中
                weight[pid][tid] += 1

        for tid, df in words.items():  # 计算log(N/df)
            words[tid] = log(len(json_dic) / df, 10)

        for pid in weight:  # 计算权重矩阵
            for tid, tf in weight[pid].items():  # 遍历每一个词项
                weight[pid][tid] = (1 + log(tf, 10)) * words[tid]
        print('导出VSM模型...')
        dump(vsm_model_path, {'word2tid': word2tid, 'weight': weight})


def calc_inner_product(query_dic: dict):  # {tid: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res = {pid: sum([weight[pid][tid] * w for tid, w in query_dic.items() if tid in weight[pid]]) for pid in weight}
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_cosine(query_dic: dict):  # {tid: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res, inner_product_res = {}, calc_inner_product(query_dic)  # 得到内积结果
    query_value = pow(sum([pow(w, 2) for w in query_dic.values()]), 0.5)  # 归一化查询的平方和的1/2
    for (pid, similarity) in inner_product_res:
        doc_value = pow(sum([pow(w, 2) for w in weight[pid].values()]), 0.5)  # 归一化文档的平方和的1/2
        res[pid] = similarity / (query_value * doc_value)
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_jaccard(query_dic: dict):  # {tid: weight}weight默认为1，返回值形如[(pid, similarity), ()]
    res, inner_product_res = {}, calc_inner_product(query_dic)  # 得到内积结果
    query_value = sum([pow(w, 2) for w in query_dic.values()])  # 归一化中查询的平方和
    for (pid, similarity) in inner_product_res:
        doc_value = sum([pow(w, 2) for w in weight[pid].values()])  # 归一化中文档的平方和
        res[pid] = similarity / (query_value + doc_value - similarity)
    return sorted(res.items(), key=lambda item: item[1], reverse=True)  # 将结果排序


def calc_line(query, similarity_func=calc_inner_product):  # 计算一个查询的相似度
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    seg = Segmentor()
    seg.load(cws_model_path)  # 加载模型
    query_dic = {str(word2tid[word]): 1 for word in seg.segment(query) if word in word2tid}
    seg.release()
    return similarity_func(query_dic)


def calc_vsm_perform(similarity_func):
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    if os.path.exists(train_preprocess_path):
        print('正在加载训练集的预处理文件...')
        res_lst = read_json(train_preprocess_path)  # 加载训练集初步处理后的文件
    else:
        print('正在预处理训练及文件...')
        seg = Segmentor()
        seg.load(cws_model_path)
        res_lst = read_json(train_path)  # 加载训练集源文件
        for question in res_lst:
            question['question'] = list(seg.segment(question['question']))
        seg.release()
        print('分词结束，开始导出训练集的与处理文件...')
        write_json(train_preprocess_path, res_lst)

    print('正在计算相似度...')
    res = {}
    for question in res_lst:
        query_dic, pid = {str(word2tid[word]): 1 for word in question['question'] if word in word2tid}, question['pid']
        pred_pid = similarity_func(query_dic)[0][0]
        res[question['qid']] = int(pred_pid) == pid
        print(len(res)/len(res_lst))
    return len(list(filter(lambda item: res[item], res))) / len(res)


def main():
    print('*' * 100)
    vsm_init()
    print('*' * 100)
    print(calc_vsm_perform(calc_inner_product))
    print('*' * 100)


if __name__ == '__main__':
    main()
