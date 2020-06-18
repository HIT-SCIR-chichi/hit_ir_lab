"""
使用自己构建的BM25模型进行检索系统的构建.
检索网页正文的系统：docs输入为所有的网页正文；
检索附件的系统：docs输入为所有的标题，返回最相关的文档；
检索照片的系统：docs输入为所有照片的文件名，构建对应的VSM模型
若检索对象为照片附件，则采取的操作是：采用检索附件的系统获取最相关的文档，随后采用检索照片的系统获取该文档中重要性最高的照片，并展示。
"""
from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidgetItem, QLabel, QWidget, QVBoxLayout, QDialog, \
    QMessageBox
from PyQt5.QtGui import QFont, QPixmap
from json import load, dump, loads
from search import Ui_MainWindow
from show_img import Ui_Dialog
from PyQt5.QtCore import QSize, Qt
from pyltp import Segmentor
from os.path import exists
from math import log
import sys

level_dic = {idx: int(idx / 250) + 1 for idx in range(1000)}  # 0-249等级1才可以访问，250—499等级1、2可访问，500-749等级1、2、3可访问
bm25_model_path, bm25_file_model = './retrieval_system/bm25', './retrieval_system/bm25_file'
bm25_img_model, cws_path = './retrieval_system/bm25_img', 'E:/pyltp/ltp_data_v3.4.0/cws.model'
passages_path, img_path = './data/seg_res.json', './data/img/'
seg, passages = None, []


class BM25:
    def __init__(self, k1=1.5, b=0.75, k3=1.5):
        self.idf = {}  # 形如{word:idf}
        self.tf = []  # 形如[{word:tf}]
        self.doc_lens = []  # 形如[len(doc)]
        self.avg_doc_len = 0  # 所有文档的平均词数
        self.param = {'k1': k1, 'b': b, 'k3': k3}  # 模型超参数

    def fit(self, docs):  # 初始化模型参数
        self.doc_lens = [len(doc) for doc in docs]
        self.avg_doc_len = sum(self.doc_lens) / len(docs)
        for doc in docs:
            self.tf.append({})
            for word in doc:
                if word not in self.tf[-1]:
                    self.tf[-1][word] = 0
                    self.idf[word] = self.idf.get(word, 0) + 1
                self.tf[-1][word] += 1
        for word, df in self.idf.items():
            self.idf[word] = log(len(docs) / df)

    def calc_score(self, query_words):
        k1, b, k3, rsv_lst, query_tf = self.param['k1'], self.param['b'], self.param['k3'], [], {}
        for word in query_words:
            query_tf[word] = query_tf.get(word, 0) + 1
        for idx in range(len(self.tf)):
            rsv = sum([self.idf[word] * (k1 + 1) * self.tf[idx][word] / (
                    k1 * (1.0 - b + b * self.doc_lens[idx] / self.avg_doc_len) + self.tf[idx][word]) * (
                               k3 + 1) * tf / (k3 + tf) for word, tf in query_tf.items() if word in self.tf[idx]])
            rsv_lst.append(rsv)
        return rsv_lst

    def load(self, model_path):  # 加载模型
        with open(model_path, 'r', encoding='utf-8') as f:
            json_dic = load(f)
            self.idf, self.tf, self.doc_lens, self.avg_doc_len, self.param = json_dic['idf'], json_dic['tf'], json_dic[
                'doc_lens'], json_dic['avg_doc_len'], json_dic['param']

    def dump(self, model_path):  # 导出模型
        with open(model_path, 'w', encoding='utf-8') as f:
            dump({'idf': self.idf, 'tf': self.tf, 'doc_lens': self.doc_lens, 'avg_doc_len': self.avg_doc_len,
                  'param': self.param}, f, ensure_ascii=False)


class MainWindow(QMainWindow, Ui_MainWindow):
    class CustomQListWidgetItem(QListWidgetItem):
        def __init__(self, title, passage, url, file_lst):
            super().__init__()
            self.widget = QWidget()
            self.passage = QLabel(text=passage)
            self.title = QLabel(text='<a href="{}">{} <a/>'.format(url, title))
            self.file_lst = file_lst

            self.setSizeHint(QSize(100, 90))
            self.__set_widget()

        def __set_widget(self):
            self.title.setFont(QFont("Microsoft YaHei", pointSize=10, weight=50))
            self.title.setOpenExternalLinks(True)  # 可打开外部链接
            self.passage.setWordWrap(True)  # 自动换行

            v_layout = QVBoxLayout()
            v_layout.addWidget(self.title)
            v_layout.addWidget(self.passage)
            self.widget.setLayout(v_layout)

    class ImgDialog(QDialog, Ui_Dialog):
        def __init__(self, path):
            super().__init__()
            self.setupUi(self)
            self.label_img.setPixmap(QPixmap(path))
            self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)  # 设置弹窗右上角按钮

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.img_dialog = None

        self.bm25 = get_bm25(bm25_model_path, [item['segmented_paragraphs'] for item in passages])  # BM25模型实例
        self.bm25_file = get_bm25(bm25_file_model, [item['segmented_title'] for item in passages])  # 检索附件的模型
        self.bm25_img = get_bm25(bm25_img_model, [item['file_name'] for item in passages])  # 照片重要度

        self.__set_search_res(passages[:int(self.sb_num.text())])  # 默认加载一定数目的新闻

    def __set_search_res(self, res_passages):
        self.lw_res.clear()  # 清除所有项
        self.lw_res.itemClicked.connect(self.__passage_click)  # 单击listWidgetItem的动作
        for item in res_passages:
            url, title_words, passage_words, file_lst = item['url'], item['segmented_title'], item[
                'segmented_paragraphs'], item['file_name']
            item = self.CustomQListWidgetItem(''.join(title_words), ''.join(passage_words), url, file_lst)
            self.lw_res.addItem(item)
            self.lw_res.setItemWidget(item, item.widget)

    def __passage_click(self, item: CustomQListWidgetItem):  # 点击一篇passage后的操作
        img_dic = {}  # 根据VSM的思想计算该网络文本中的附件的重要程度
        for path in item.file_lst:
            img_dic[path] = img_dic.get(path, 0) + 1
        img_dic = {path: val * self.bm25_img.idf[path] for path, val in img_dic.items()}
        res_lst = sorted(img_dic, key=lambda key: img_dic[key], reverse=True)  # 照片按照重要性排序
        if res_lst:
            self.img_dialog = self.ImgDialog(img_path + res_lst[0])
            self.img_dialog.show()
        else:
            QMessageBox.information(self, '无图片', '当前网页无插图')

    def get_search_res(self):  # 点击搜索按钮的绑定动作
        bm25, num, = self.bm25 if self.cb_type.isChecked() else self.bm25_file, int(self.sb_num.text())
        rsv_lst = bm25.calc_score(seg_line(self.et_query.text()))
        rsv_lst = sorted([(idx, val) for idx, val in enumerate(rsv_lst)], key=lambda item: item[1], reverse=True)
        level, res_passages = self.cb_level.currentIndex() + 1, []  # 当前的等级
        for tuple_item in rsv_lst:  # 获取所有的篇章结构，形式等同于seg_res文件中的格式，同时满足权限要求
            if level <= level_dic[tuple_item[0]]:
                res_passages.append(passages[tuple_item[0]])
            if len(res_passages) == num:
                break
        self.__set_search_res(res_passages)

    def get_search_type(self):  # 点击搜索类型的绑定动作
        if not self.cb_type.isChecked():
            self.cb_type.setText('搜索附件')
        else:
            self.cb_type.setText('搜索新闻')


def is_authorized(level: int, doc_num):  # level标识用户等级，越小等级越高；doc_num标识目前文档编号
    return level <= level_dic[doc_num]


def seg_line(line: str) -> list:
    global seg
    if not seg:
        seg = Segmentor()
        seg.load(cws_path)  # 加载模型
    return list(seg.segment(line))


def get_bm25(model_path, docs):  # 构造器，返回model_path对应的模型实例
    bm25 = BM25()
    if exists(model_path):
        bm25.load(model_path)
    else:
        bm25.fit(docs)
        bm25.dump(model_path)
    return bm25


if __name__ == '__main__':
    with open(passages_path, 'r', encoding='utf-8') as passages_f:
        passages = [loads(json_line) for json_line in passages_f]  # 读取爬取的所有文章

        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec_())
