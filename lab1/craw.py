# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
爬取网页，并提取网页标题和正文，并保存附件（这里主要处理图片资源）
"""

from bs4 import BeautifulSoup
import json
import string
import time
from urllib import request, parse


# todo 使用线程安全的Queue实现多线程爬虫

class Craw:
    def __init__(self, config_path='./input/config.json'):
        self.url2visit = []  # 要访问的URL

        self.start_urls = []  # 开始的URL
        self.url_num = 0  # 要爬取的URL数目
        self.url_with_file = 0  # 要爬取的URL中带有附件的URL数目
        self.craw_res_file = ''  # json格式的爬取结果的输出文件
        self.__read_config(config_path)  # 读取配置文件

    def __read_config(self, config_path):
        with open(config_path, encoding='utf-8') as f:
            config_dic = json.load(f)
            self.start_urls = config_dic['start_urls']
            self.url_num = config_dic['url_num']
            self.url_with_file = config_dic['url_with_file']
            self.craw_res_file = config_dic['craw_res_file']
            self.url2visit.extend(self.start_urls)

    def run_craw(self):
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' +
                                 ' Chrome/81.0.4044.122 Safari/537.36 Edg/81.0.416.64'}
        url_with_file, out_lst, err_num = 0, [], 0  # 带有附件的URL数目，输出的json格式，错误的URL数目
        start_time = time.time()
        for url_num, url in enumerate(self.url2visit):  # 将要访问的URL队列
            try:
                with request.urlopen(request.Request(url, headers=headers)) as f:
                    bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')
                    if url_num >= self.url_num + err_num and url_with_file >= self.url_with_file:
                        print('爬取完成，用时：' + str((time.time() - start_time)) + '秒')
                        break

                    # 信息处理：获取标题、正文、附件
                    title = bs.find('body').find('h1').getText().strip()  # 新闻标题
                    para, files, img_dir, flag = [], set(), './output/img/', False  # flag标志是否已经标识为有照片
                    for paragraph in bs.select('p'):  # 正文
                        text = paragraph.text.replace('\n', '').replace(' ', '')
                        if text:
                            para.append(text)
                    for item in bs.body.find_all('img'):  # 照片
                        if 'src' in item.attrs or 'data-original' in item.attrs:  # 图片资源不全在src属性里，也在data-original中
                            img_url = item.attrs['src'] if 'src' in item.attrs else item.attrs['data-original']
                            img_url = process_img_url(img_url)
                            file_path = img_dir + img_url.split('/')[-1]  # 选取文件名
                            try:
                                if file_path not in files:
                                    request.urlretrieve(img_url, file_path)  # 下载图片到file_path中
                                    url_with_file = url_with_file + (0 if flag else 1)
                                    files.add(file_path)
                                    flag = True
                            except:
                                continue
                    out_lst.append({'url': url, 'title': title, 'paragraphs': ' '.join(para), 'file_name': list(files)})
                    print(url_num - err_num + 1, url, url_with_file)

                    # 获取超链接资源地址，用于广度优先搜索
                    for tag in bs.find_all('a'):
                        href = tag.get('href')  # 获取所有a标签中的href的值
                        if href and (href.startswith('http') or href.startswith('/')):
                            href = href if href.startswith('http') else url + href  # 中文字符需要处理
                            href = parse.quote(href, safe=string.printable)
                            if href.startswith(self.start_urls[0]) and href not in self.url2visit:
                                self.url2visit.append(href)
            except:
                err_num += 1
        return out_lst

    def output_res(self, craw_lst: list):  # 以json格式输出爬取的结果到文件中
        res = []
        for item in craw_lst:  # 构造输出的json格式列表
            res.append(json.dumps(item, ensure_ascii=False))
        with open(self.craw_res_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(res))
        with open('./output/preprocessed.json', 'w', encoding='utf-8') as f:
            f.write('\n'.join(res[:10]))


def process_img_url(img_url: str) -> str:
    """得到真正的html中获取的img资源地址.

    Args:
        img_url: 通过beautifulSoup直接得到的图片资源地址.

    Returns:
        可以直接访问的，作为urllib.request.urlretrieve参数的URL.
    """

    # 获取处理前的图片URL地址
    symbols = {'&', '!', '?'}
    for idx, char in enumerate(img_url):
        if char in symbols:
            img_url = img_url[:idx]
            break

    # 处理URL地址以//开头
    img_url = ('https:' if img_url.startswith('//') else '') + img_url
    return img_url


if __name__ == '__main__':
    craw = Craw()
    craw.output_res(craw.run_craw())  # 将爬取结果输出到配置文件中规定的craw_res_file目录
