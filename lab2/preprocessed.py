"""
对文本集合进行处理、建立索引.
检索模型：自己实现的向量空间模型.
"""
# todo 去停用词处理
# todo 现在计算tf与idf的log底数为10
# todo 现在计算相似度的查询权重为1
from util import read_json, write_json, seg_line, train_path, test_path, load_seg_passages, file_exists
from joblib import dump, load
from math import pow, log

model_path, preprocess_path = './preprocessed/vsm', './preprocessed/train_preprocessed.json'
weight, idf = {}, {}  # VSM模型权重矩阵，形式如：{pid: {word: weight}}；idf形如{word: idf}
test_predict_path = './preprocessed/test_predict.json'


def vsm_init():  # 从JSON文件中加载权重矩阵；若文件不存在，则重新初始化矩阵，并写入JSON文件，
    global weight, idf
    if file_exists(model_path):
        model = load(model_path)
        weight, idf = model['weight'], model['idf']
    else:
        res_dic = load_seg_passages()
        for pid, passage in res_dic.items():
            passage_words, weight[pid] = [word for word_lst in passage for word in word_lst], {}
            for word in passage_words:  # 计算每一个篇章中每一个词项的tf，结果保存在weight中
                if word not in weight[pid]:
                    weight[pid][word] = 0
                    idf[word] = idf[word] + 1 if word in idf else 1  # 计算每一个词项的df，保存在words中
                weight[pid][word] += 1

        for word, df in idf.items():  # 计算log(N/df)
            idf[word] = log(len(res_dic) / df, 10)

        for pid in weight:  # 计算权重矩阵
            for word, tf in weight[pid].items():  # 遍历每一个词项
                weight[pid][word] = (1 + log(tf, 10)) * idf[word]
        dump({'weight': weight, 'idf': idf}, model_path, compress=3)


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
    query_dic = {word: idf.get(word, 0) for word in seg_line(query)}
    return similarity_func(query_dic)


def calc_vsm_perform(similarity_func=calc_inner_product):
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    print('正在加载训练集的预处理文件...')
    if file_exists(preprocess_path):
        res_lst = read_json(preprocess_path)  # 加载训练集初步处理后的文件
    else:
        res_lst = read_json(train_path)  # 加载训练集源文件
        for question in res_lst:
            question['question'] = seg_line(question['question'])
        write_json(preprocess_path, res_lst)

    print('正在计算相似度...')
    res = {}
    for question in res_lst:
        query_dic, pid = {word: idf.get(word, 0) for word in question['question']}, question['pid']
        pred_pid = similarity_func(query_dic)[0][0]
        res[question['qid']] = int(pred_pid) == pid
        # print('进度: %.2f%%' % (len(res) / len(res_lst) * 100))
    return len(list(filter(lambda item: res[item], res))) / len(res)


def predict(similarity_func=calc_inner_product):  # 对测试集进行预测，要求在此函数前必须执行了vsm_init()函数.
    if similarity_func.__name__ not in [calc_cosine.__name__, calc_inner_product.__name__, calc_jaccard.__name__]:
        print('错误的输入相似度计算函数...')
        return
    test_lst = read_json(test_path)
    for q_item in test_lst:
        q_item['question'] = seg_line(q_item['question'])  # 分词
        q_item['pid'] = int(similarity_func({word: idf.get(word, 0) for word in q_item['question']})[0][0])
    write_json(test_predict_path, test_lst)


def main():
    print('*' * 100 + '\n正在加载VSM模型...')
    vsm_init()
    print('VSM模型内积准确率为: %.2f%%' % (calc_vsm_perform() * 100))
    print('*' * 100 + '\n正在对测试集进行预测...')
    predict()
    print('预测结束\n' + '*' * 100)


if __name__ == '__main__':
    main()
