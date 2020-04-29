# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
爬取网页，并提取网页标题和正文，并保存附件（这里主要处理图片资源）.
"""
from urllib import request, parse, robotparser, error
from bs4 import BeautifulSoup
from threading import Thread, Lock
from queue import Queue, Empty
import string
import json
import time

lock = Lock()
start_url, legal_urls = 'https://news.163.com/rank/', ['news.163.com', 'ent.163.com', 'gov.163.com', 'tech.163.com']
user_agent = 'python3.6-urllib HIT-IR-lab1 author-zjr-1172510217'
url_queue, craw_res, all_files = Queue(), [], set()  # 程序运行中，已经下载过的资源文件
url_num, url_with_file = 0, 0  # 动态变量，随已爬取网页变化
num, file_url_num = 1000, 100  # 定值，实验要求参数
rps, craw_delay = [], 0  # 礼貌规则集合，爬取时间间隔


def get_urls(k=1.2):
    """
    从start_url开始，通过超链接的形式拓展爬取url，爬取的url形式满足legal_urls参数中的一个形式.

    :param k: 拓展因子，由于爬取的网页存在非法网页或者不带有附件的网页，所以需要设置k>1，确保爬取的数目不会小于num=1000.
    :return: url2visit，待爬取的网页列表.
    """
    url2visit = [start_url]  # 将要访问的URL队列
    for url in url2visit:
        print('抓取进度：%.2f%%' % (float(len(url2visit)) / (num * 1.2) * 100))
        try:
            f = request.urlopen(request.Request(url, headers={'user-agent': 'IR-robot'}))
        except error.URLError:
            continue
        else:
            bs = BeautifulSoup(f.read(), 'html.parser', from_encoding='gb18030')
            if len(url2visit) >= k * num:
                return url2visit
            for href in filter(None, map(lambda item: item.get('href'), bs.find_all('a'))):  # 获取所有a标签中的href的值
                if href.startswith('https://') and href.split('/')[2] in legal_urls:
                    href = parse.quote(href, safe=string.printable)  # 中文字符需要处理
                    if href not in url2visit and rps[legal_urls.index(href.split('/')[2])].can_fetch('*', href):
                        url2visit.append(href)  # 不违反机器人排除协议且未曾出现过，则将其加入到待访问URL队列中


def craw_url(url, img_dir='./output/img/'):
    """
    爬取单个网页，并将附件输出到output/img文件夹中.

    :param url: 待爬取的url.
    :param img_dir: 输出的图片所在的文件夹.
    """

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
        f = request.urlopen(request.Request(url))
    except error.URLError:
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
                        visited = file_name in all_files  # 该图片是否被下载过
                        if not visited:
                            try:
                                request.urlretrieve(img_url, file_path)  # 下载图片到file_path中
                            except (error.URLError, TimeoutError):
                                continue
                            else:
                                flag = True
                                files.add(file_name)
                                lock.acquire()
                                all_files.add(file_name)
                                lock.release()
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
            print('处理进度：%.2f%%' % (float(url_num) / num * 100))
            lock.release()


def output(craw_file='./output/craw_res.json') -> list:  # 以json格式输出爬取的结果到文件中
    res = [json.dumps(item, ensure_ascii=False) for item in craw_res]  # 构造输出的json格式列表
    with open(craw_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(res))
    return res


class MyThread(Thread):  # 多线程爬取网页，采用线程安全的Queue储存url
    def run(self) -> None:
        while True:
            try:
                lock.acquire()
                url = url_queue.get_nowait()
                if url_num >= num and url_with_file >= file_url_num:
                    lock.release()
                    break
                if craw_delay > 0:
                    time.sleep(craw_delay)
                lock.release()
                craw_url(url)
            except (Empty, ConnectionResetError):
                break


def main(thread_num=15):
    # 初始化所有的机器人排除协议
    global rps
    print('*' * 100 + '\n开始获取机器人排除协议信息...')
    rps = [robotparser.RobotFileParser('https://' + legal_url + '/robots.txt') for legal_url in legal_urls]
    for rp in rps:
        rp.read()

    # 抓取网页URL
    print('获取完毕.\n' + '*' * 100 + '\n开始获取网页地址...')
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
