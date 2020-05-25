"""
运用机器学习方法进行问题多分类；
机器学习方法：SVM.
"""
# todo 考虑是否去停用词
# todo 0作为特征右侧填充
from sklearn.model_selection import GridSearchCV
from util import seg_line, dump, load
from sklearn.metrics import f1_score, recall_score, accuracy_score
from sklearn.svm import SVC
from os.path import exists
import numpy as np
import joblib

word_model_path, svm_model_path = './question_classification/word', './question_classification/svm_model'
train_path, test_path = './data/train_questions.txt', './data/test_questions.txt'
labels, words, max_len = {}, {}, 0  # labels:{label: index}; words:{word: index}，其中word的index从1开始，因为0填充


def pad_sequence(data: list, pad='post', truncating='pre', value=0):
    res = []
    for lst in data:
        if len(lst) > max_len:
            res.append(lst[-max_len:] if truncating == 'pre' else lst[:max_len])
        else:
            pad_lst = [value] * (max_len - len(lst))
            res.append(lst + pad_lst if pad == 'post' else pad_lst + lst)
    return res


def test_init():  # 获取测试集文件
    with open(test_path, 'r', encoding='utf-8') as f:
        x_test, y_test = [], []
        for line in f:
            line = line.replace('\n', '')
            if line:
                [label, line] = line.split('\t')
                x_test.append([words.get(word, 0) for word in seg_line(line)])
                y_test.append(labels[label])
        return pad_sequence(x_test), y_test


def svm_init():
    global words, labels, max_len
    if exists(svm_model_path) and exists(word_model_path):  # 模型已经训练过，且存在对应的模型文件
        json_dic = load(word_model_path)
        words, labels, max_len = json_dic['words'], json_dic['labels'], json_dic['max_len']
        clf = joblib.load(svm_model_path)
    else:
        with open(train_path, 'r', encoding='utf-8') as f:
            x_train, y_train = [], []
            for line in f:
                line = line.replace('\n', '')
                if line:
                    [label, line] = line.split('\t')
                    labels[label] = labels.get(label, len(labels))
                    x_train.append([])
                    y_train.append(labels[label])
                    for word in seg_line(line):
                        words[word] = words.get(word, len(words) + 1)
                        x_train[-1].append(words[word])
            labels['OBJ_ADDRESS'] = len(labels)

            max_len = max(len(item) for item in x_train)
            dump(word_model_path, {'labels': labels, 'words': words, 'max_len': max_len})

            svc = SVC(kernel='rbf', class_weight='balanced')
            svc.fit(pad_sequence(x_train), y_train)
            c_range = np.logspace(-5, 15, 11, base=2)
            gamma_range = np.logspace(-9, 3, 13, base=2)
            param_grid = [{'kernel': ['rbf'], 'C': c_range, 'gamma': gamma_range}]
            grid = GridSearchCV(svc, param_grid, cv=3, n_jobs=-1)
            clf = grid.fit(pad_sequence(x_train), y_train)
            joblib.dump(clf, svm_model_path, compress=3)  # 导出模型
    return clf


def main():
    svc = svm_init()  # 加载模型
    x_test, y_test = test_init()  # 获取测试集
    res = svc.predict(x_test)
    print(f1_score(y_test, res, average='macro'))


if __name__ == '__main__':
    main()
