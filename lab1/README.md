# 实验一：网页文本的预处理
## 环境
- Python 3.6
- Pycharm 专业版 2020.1
- pyltp 分词工具
- urllib 爬虫工具
- bs4.BeautifuleSoup 解析工具
## 输入输出（输出文件除了preprocessed.json外均未在code文件夹内）
- 输入：停用词文件[stop_word.txt](./stopwords.txt)
- 输入：分词模型文件cws.model，该文件需要下载
- 输出：图片文件，code/img
- 输出：craw_res.json，craw.py文件的默认产出文件，是爬取结果文件
- 输出：seg_res.json，segment.py文件的默认产出文件，是分词和停用词处理结果
- 输出：[preprocessed.json](./output/preprocessed.json)，seg_res.json文件的前10行
## 如何运行
- 运行[craw.py](./craw.py)文件：获取海量URL，并进行爬取处理，下载图片附件
- 运行[segment.py](segment.py)文件：将craw.py文件的输出进行分词和停用词处理，并输出结果
## 特点
- 礼貌规则的处理
  - 使用user-agent标识自己
  - 使用urllib.robotparser进行机器人排除协议解析
  - 降低带宽使用量，设置craw-delay参数
- 多线程爬取网页：实验得出，爬取1000个网页耗时1h（单线程）->10分钟（多线程）