# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
爬取网页，并提取网页标题和正文，并保存附件（这里主要处理图片资源）.
"""
from urllib import request, parse
from bs4 import BeautifulSoup
from threading import Thread, Lock
from queue import Queue
import string
import json
import time

lock = Lock()
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/81.0.4044.122 Safari/537.36 Edg/81.0.416.64'}
start_url, legal_urls = 'https://news.163.com/rank/', ['news.163.com', 'ent.163.com', 'gov.163.com', 'tech.163.com']
url_queue, craw_res = Queue(), []
url_num, url_with_file = 0, 0  # 动态变量，随已爬取网页变化
num, file_url_num = 1000, 100  # 定值，实验要求参数


def get_urls(k=1.2):
    url2visit = [start_url]  # 将要访问的URL队列
    for url in url2visit:
        print('进度：%.2f' % str(float(len(url2visit)) / (num * 1.2) * 100) + '%')
        try:
            f = request.urlopen(request.Request(url, headers=headers))
        except:
            continue
        else:
            bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')
            if len(url2visit) >= k * num:
                return url2visit
            for href in filter(None, map(lambda item: item.get('href'), bs.find_all('a'))):  # 获取所有a标签中的href的值
                if href.startswith('https://') and str(href).split('/')[2] in legal_urls:
                    href = parse.quote(href, safe=string.printable)  # 中文字符需要处理
                    if href not in url2visit:
                        url2visit.append(href)


def craw_url(url, img_dir='./output/img/'):
    def process_img_url(url_of_img: str) -> str:
        symbols = {'&', '!', '?'}
        for idx, char in enumerate(url_of_img):
            if char in symbols:
                url_of_img = url_of_img[:idx]
                break
        url_of_img = ('https:' if url_of_img.startswith('//') else '') + url_of_img
        return url_of_img

    global url_num, url_with_file, craw_res
    try:
        f = request.urlopen(request.Request(url, headers=headers))
    except:
        return False
    else:
        bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')

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
                    if file_name not in files:
                        try:
                            request.urlretrieve(img_url, file_path)  # 下载图片到file_path中
                        except:
                            continue
                        else:
                            flag = True
                            files.add(file_name)
            lock.acquire()
            if url_num >= num and url_with_file >= file_url_num:
                lock.release()
                return
            url_num += 1
            if flag:
                url_with_file += 1
            craw_res.append({'url': url, 'title': title, 'paragraphs': ' '.join(para), 'file_name': list(files)})
            print('进度：%.2f' % str(float(url_num) / num * 100) + '%')
            lock.release()


def output(craw_file='./output/craw_res.json') -> list:  # 以json格式输出爬取的结果到文件中
    res = [json.dumps(item, ensure_ascii=False) for item in craw_res]  # 构造输出的json格式列表
    with open(craw_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(res))
    return res


class MyThread(Thread):
    def run(self) -> None:
        while True:
            try:
                lock.acquire()
                url = url_queue.get_nowait()
                if url_num >= num and url_with_file >= file_url_num:
                    lock.release()
                    break
                lock.release()
                craw_url(url)
            except:
                break


def main(thread_num=10):
    # 抓取网页URL
    print('*' * 100 + '\n开始获取网页地址...')
    time0 = time.time()
    for url in get_urls():
        url_queue.put(url)
    time1 = time.time()
    print('获取完毕，用时：' + str(time1 - time0) + '秒\n' + '*' * 100 + '\n开始处理网页内容...')

    # 爬取处理网页内容
    threads = [MyThread(name='Thread' + str(idx)) for idx in range(thread_num)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    time2 = time.time()
    print('处理完成，用时：' + str(time2 - time1), '秒\n' + '*' * 100 + '\n开始导出结果...')

    output()
    print('导出完成。\n总用时%d秒。' % (time.time() - time0))


if __name__ == '__main__':
    main()
