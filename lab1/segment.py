#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
this is the doc.
"""


def segment(str2seg) -> list:
    """分词.

    Args:
        str2seg: 待分词字符串.

    Returns:
        分词结果列表.
    """
    cws_model_path = 'E:/pyltp/ltp_data_v3.4.0/cws.model'  # 分词模型路径，模型名称为`cws.model`
    from pyltp import Segmentor

    segmentor = Segmentor()  # 初始化实例
    segmentor.load(cws_model_path)  # 加载模型
    words = segmentor.segment(str2seg)  # 分词
    segmentor.release()  # 释放模型
    return list(words)  # 将VectorOfString类型转换为list


def _read_stop_words(path) -> list:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read()
        return lines.split('\n')


if __name__ == '__main__':
    res = segment('元芳你怎么看')
    _read_stop_words('./input/stopwords(new).txt')
