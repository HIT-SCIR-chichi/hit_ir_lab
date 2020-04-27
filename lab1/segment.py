#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
将爬取的网页文本进行分词和去停用词处理，并将结果保存.
"""
import json


class Segment:
    def __init__(self, config_path='./input/config.json'):
        with open(config_path, encoding='utf-8') as f:  # 读取配置文件
            config_dic = json.load(f)
            self.craw_res_file = config_dic['craw_res_file']  # 爬取的json结果文件
            self.seg_res_file = config_dic['seg_res_file']  # 经分词的的结果文件
            self.output_file = config_dic['output_file']  # 输出的结果文件
            self.output_num = config_dic['output_num']  # 输出的json结果行数
            self.cws_model_path = config_dic['cws_model_path']  # 分词模型路径，模型名称为`cws.model`
            self.stop_words = config_dic['stop_words']  # 停用词文件

    def process_craw_res(self):  # 将爬取结果分词并去除停用词
        with open(self.stop_words, 'r', encoding='utf-8') as f, open(self.craw_res_file, 'r', encoding='utf-8') as f1:
            stop_words = set(f.read().split('\n'))  # 获取停用词

            from pyltp import Segmentor
            seg, res = Segmentor(), []  # 初始化分词实例
            seg.load(self.cws_model_path)  # 加载模型
            for craw in [json.loads(line) for line in f1]:  # 按行转换json格式到python数据结构格式
                title_lst = [word for word in seg.segment(craw['title']) if word not in stop_words]
                para_lst = [word for word in seg.segment(craw['paragraphs']) if word not in stop_words]
                res.append({'url': craw['url'], 'segmented_title': title_lst, 'segmented_paragraphs': para_lst,
                            'file_name': craw['file_name']})
            print('分词和去停用词处理完成')
            seg.release()
            return res

    def output_res(self, seg_lst: list) -> list:  # 以json格式输出处理的结果到文件中
        res = [json.dumps(item, ensure_ascii=False) for item in seg_lst]  # 构造输出的json格式列表
        with open(self.seg_res_file, 'w', encoding='utf-8') as f, open(self.output_file, 'w', encoding='utf-8') as f1:
            f.write('\n'.join(res))  # 输出爬取结果的所有行
            f1.write('\n'.join(res[:self.output_num]))  # 输出爬取结果的前几行
        return res


if __name__ == '__main__':
    segment = Segment()
    segment.output_res(segment.process_craw_res())  # 将分词结果输出到配置文件中规定的seg_res_file和output_file文件中
