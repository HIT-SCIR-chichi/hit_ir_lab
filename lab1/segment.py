#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
将爬取的网页文本进行分词和去停用词处理，并将结果保存.
"""
import json
import time


def process(stop_words='stopwords.txt', craw_file='./output/craw_res.json',
            model_path='E:/pyltp/ltp_data_v3.4.0/cws.model'):
    with open(stop_words, 'r', encoding='utf-8') as f, open(craw_file, 'r', encoding='utf-8') as f1:
        stop_words = set(f.read().split('\n'))  # 获取停用词

        from pyltp import Segmentor
        seg, res = Segmentor(), []  # 初始化分词实例
        seg.load(model_path)  # 加载模型
        for craw in [json.loads(line) for line in f1]:  # 按行转换json格式到python数据结构格式
            title_lst = [word for word in seg.segment(craw['title']) if word not in stop_words]
            para_lst = [word for word in seg.segment(craw['paragraphs']) if word not in stop_words]
            res.append({'url': craw['url'], 'segmented_title': title_lst, 'segmented_paragraphs': para_lst,
                        'file_name': craw['file_name']})
        seg.release()
        return res


def output(seg_lst: list, output_num=10, seg_file='./output/seg_res.json', output_file='./output/preprocessed.json'):
    res = [json.dumps(item, ensure_ascii=False) for item in seg_lst]  # 构造输出的json格式列表
    with open(seg_file, 'w', encoding='utf-8') as f, open(output_file, 'w', encoding='utf-8') as f1:
        f.write('\n'.join(res))  # 输出爬取结果的所有行
        f1.write('\n'.join(res[:output_num]))  # 输出爬取结果的前几行
    return res


if __name__ == '__main__':
    print('*' * 100 + '\n开始进行分词和停用词处理...')
    time0 = time.time()
    output(process())  # 将分词结果输出到配置文件中规定的seg_res_file和output_file文件中
    print('处理完成，用时：' + str(time.time() - time0) + '秒\n' + '*' * 100)
