from pyltp import Segmentor
import json

cws_model_path = 'E:/pyltp/ltp_data_v3.4.0/cws.model'  # pyltp模型文件路径
seg = None


def seg_line(line: str) -> list:
    global seg
    if not seg:
        seg = Segmentor()
        seg.load(cws_model_path)  # 加载模型
    return list(seg.segment(line))


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
