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
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                                      ' Chrome/81.0.4044.122 Safari/537.36 Edg/81.0.416.64'}
        with open(config_path, encoding='utf-8') as f:
            config_dic = json.load(f)
            self.start_url = config_dic['start_url']  # 开始的URL
            self.legal_urls = config_dic['legal_urls']  # 合法的URL地址
            self.url_num = config_dic['url_num']  # 要爬取的URL数目
            self.url_with_file = config_dic['url_with_file']  # 要爬取的URL中带有附件的URL数目
            self.craw_res_file = config_dic['craw_res_file']  # json格式的爬取结果的输出文件
            self.url2visit = [self.start_url]  # 要访问的URL

    def get_urls(self, k=1.2):  # urls中可能存在无效网址
        print(self.url2visit[0], 1)
        for url in self.url2visit:  # 将要访问的URL队列
            try:
                f = request.urlopen(request.Request(url, headers=self.headers))
            except:
                continue
            else:
                bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')
                if len(self.url2visit) >= k * self.url_num:
                    break
                for href in filter(None, map(lambda item: item.get('href'), bs.find_all('a'))):  # 获取所有a标签中的href的值
                    if href.startswith('https://') and str(href).split('/')[2] in self.legal_urls:
                        href = parse.quote(href, safe=string.printable)  # 中文字符需要处理
                        if href not in self.url2visit:
                            self.url2visit.append(href)
                            print(href, len(self.url2visit))

    def craw(self):
        url_with_file, out_lst, img_dir, all_files = 0, [], './output/img/', set()  # 带附件URL数目，输出的json列表
        for url in self.url2visit:  # 将要访问的URL队列
            try:
                f = request.urlopen(request.Request(url, headers=self.headers))
            except:
                continue
            else:
                bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')
                if len(out_lst) == self.url_num and url_with_file >= self.url_with_file:
                    return out_lst

                # 信息处理：获取标题、正文、附件
                title_tag = bs.find('body').find('h1')
                if title_tag and title_tag.getText().strip():
                    title = title_tag.getText().strip()  # 新闻标题
                    para = filter(None, [tag.text.replace('\n', '').replace(' ', '') for tag in bs.select('p')])  # 正文
                    files, flag = set(), False  # flag标志是否已经标识为有照片
                    for tag in bs.body.find_all('img'):  # 照片
                        if 'src' in tag.attrs or 'data-original' in tag.attrs:  # 图片资源不全在src属性里，也在data-original中
                            img_url = process_img_url(tag.attrs['src' if 'src' in tag.attrs else 'data-original'])
                            file_name = img_url.split('/')[-1]  # 保存的文件名
                            file_path = img_dir + file_name  # 文件相对地址
                            files.add(file_name)
                            if file_name not in all_files:
                                try:
                                    request.urlretrieve(img_url, file_path)  # 下载图片到file_path中
                                except:
                                    continue
                                else:
                                    url_with_file, flag = url_with_file + (0 if flag else 1), True
                                    all_files.add(file_name)
                    out_lst.append({'url': url, 'title': title, 'paragraphs': ' '.join(para), 'file_name': list(files)})
                    print(out_lst[-1])

    def output_res(self, craw_res: list) -> list:  # 以json格式输出爬取的结果到文件中
        res = [json.dumps(item, ensure_ascii=False) for item in craw_res]  # 构造输出的json格式列表
        with open(self.craw_res_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(res))
        return res


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
    print('*' * 100 + '\n开始获取网页地址...')
    time0 = time.time()
    craw.get_urls()
    time1 = time.time()
    print('获取完毕，用时：' + str(time1 - time0) + '秒\n' + '*' * 100 + '\n开始处理网页内容...')
    craw_lst = craw.craw()
    time2 = time.time()
    print('处理完成，用时：' + str(time2 - time1), '秒\n' + '*' * 100 + '\n开始导出结果...')
    craw.output_res(craw_lst)
    print('导出完成')
