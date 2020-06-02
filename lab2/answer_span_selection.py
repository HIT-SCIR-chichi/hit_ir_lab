"""
基于规则方法实现答案句抽取.
"""
from answer_sentence_selection import test_ans_path as test_select_path
from util import read_json, pos_tag, write_json, test_answer_path, train_path
import re

test_span_path = './answer_span_selection/test_predict.json'


def _get_hum_ans(query_lst, ans_lst):
    query, ans, res = ''.join(query_lst), ''.join(ans_lst), ''
    tags = pos_tag(ans_lst)
    for idx, tag in enumerate(tags):
        if (tag == 'ni' or tag == 'nh') and ans_lst[idx] not in res:
            res += ans_lst[idx]
    return res if res else ans


def _get_loc_ans(query_lst, ans_lst):
    query, ans, res = ''.join(query_lst), ''.join(ans_lst), ''
    tags = pos_tag(ans_lst)
    for idx, tag in enumerate(tags):
        if (tag == 'ns' or tag == 'nl') and ans_lst[idx] not in res:
            res += ans_lst[idx]
    return res if res else ans


def _get_num_ans(query_lst: list, ans_lst: list):
    query, ans, res_lst = ''.join(query_lst), ''.join(ans_lst), []
    tags = pos_tag(ans_lst)
    for idx, tag in enumerate(tags):
        if tag == 'm' and idx < len(tags) - 1 and tags[idx + 1] == 'q':
            res_lst.append(ans_lst[idx] + ans_lst[idx + 1])
    return res_lst[0] if res_lst else ans  # 当前默认选择第一个数字 todo 优化选取


def _get_time_ans(query_lst: list, query_type, ans_lst: list):  # query_type：参考哈工大问题分类体系.
    query, ans, res_lst = ''.join(query_lst), ''.join(ans_lst), []
    if query_type == 'TIME_YEAR':
        res_lst = re.findall(r'\d{2,4}年', ans)
    elif query_type == 'TIME_MONTH':  # xx月或x月
        res_lst = re.findall(r'\d{1,2}月', ans)
    elif query_type == 'TIME_DAY':
        res_lst = re.findall(r'\d{1,2}日}', ans)
    elif query_type == 'TIME_WEEK':
        res_lst = re.findall(r'((周|星期|礼拜)[1-7一二三四五六日])', ans)
        res_lst = [item[0] for item in res_lst]
    elif query_type == 'TIME_RANGE':
        res_lst = re.findall(r'\d{2,4}[年]?[-到至]\d{2,4}[年]?', ans)  # xxxx年到xxxx年或者xxxx年-xxxx年
    else:
        res_lst = re.findall(r'\d{1,4}[年/-]\d{1,2}[月/-]\d{1,2}[日号]?', ans)  # 年月日
        if not res_lst:
            res_lst = re.findall(r'\d{1,4}[年/-]\d{1,2}月?', ans)  # 年月
        if not res_lst:
            res_lst = re.findall(r'\d{1,2}[月/-]\d{1,2}[日号]?', ans)  # 月日
        if not res_lst:
            res_lst = re.findall(r'\d{2,4}年', ans)
        if not res_lst:
            res_lst = re.findall(r'\d{1,2}月', ans)
    return res_lst[0] if res_lst else ans  # 当前默认选择第一个数字 todo 优化选取


def get_ans(query_lst: list, query_type: str, ans_lst: list) -> str:
    if query_type.startswith('HUM'):
        return _get_hum_ans(query_lst, ans_lst)
    elif query_type.startswith('LOC'):
        return _get_loc_ans(query_lst, ans_lst)
    elif query_type.startswith('NUM'):
        return _get_num_ans(query_lst, ans_lst)
    elif query_type.startswith('TIME'):
        return _get_time_ans(query_lst, query_type, ans_lst)
    else:
        return ''.join(ans_lst)


def predict():
    res_lst = read_json(test_select_path)
    for item in res_lst:
        item['answer'] = get_ans(item['question'], item['label'], item['answer_sentence'][0])
    res_lst.sort(key=lambda val: val['qid'])
    write_json(test_span_path, res_lst)  # 对结果数组按照qid升序排列，可注释掉此行
    write_json(test_answer_path, [{'qid': item['qid'], 'question': ''.join(item['question']),
                                   'answer_pid': [item['pid']], 'answer': item['answer']} for item in res_lst])


def evaluate():
    res_lst = read_json(train_path)
    pass


if __name__ == '__main__':
    print('*' * 100 + '\n正在对测试集进行答案抽取...')
    predict()
    print('答案抽取完成...\n' + '*' * 100)
