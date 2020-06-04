"""
使用逻辑回归和SVM方法进行问题分类.
"""
from util import train_question_path, test_question_path, seg_line, file_exists, read_json, write_json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from preprocessed import test_predict_path
import joblib

lr_model_path, tf_idf_path = './question_classification/lr_model', './question_classification/tf_idf'
test_label_path = './question_classification/test_predict.json'


def load_data():  # 加载问题分类训练和测试数据
    two_items = [(train_question_path, [], []), (test_question_path, [], [])]
    for path, x_data, y_data in two_items:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if len(line) > 1:
                    [label, line] = line.strip().split('\t')
                    x_data.append(' '.join(seg_line(line)))
                    y_data.append(label)
    return two_items[0][1], two_items[0][2], two_items[1][1], two_items[1][2]


def tf_idf_init(x_train):
    if file_exists(tf_idf_path):
        return joblib.load(tf_idf_path)
    else:
        tf_idf_vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        tf_idf_vec.fit_transform(x_train)
        joblib.dump(tf_idf_vec, tf_idf_path)
        return tf_idf_vec


def lr_init(x_train, y_train):  # solver选用默认的lbfgs, multi_class选用多分类问题中的multinomial
    if file_exists(lr_model_path):
        return joblib.load(lr_model_path)
    else:
        print('正在通过网格搜索获取最佳模型参数...')
        lr = LogisticRegression(max_iter=400, n_jobs=-1)
        param_grid = [{'C': [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]}]
        grid_search = GridSearchCV(lr, param_grid, cv=3, n_jobs=-1).fit(x_train, y_train)
        joblib.dump(grid_search.best_estimator_, lr_model_path, compress=3)  # 导出模型
        print('合理的超参数为', grid_search.best_params_)
        return grid_search.best_estimator_


def get_train_labels():  # 将train.json文件中的所有问题分类
    tf_idf_vec = joblib.load(tf_idf_path)
    lr = joblib.load(lr_model_path)
    res_lst = read_json('./preprocessed/train_preprocessed.json')
    x_data = [' '.join(item['question']) for item in res_lst]
    y_data = lr.predict(tf_idf_vec.transform(x_data))
    for item, label in zip(res_lst, y_data):
        item['label'] = label
    return res_lst


def main():
    print('*' * 100 + '\n正在加载VSM模型和LR逻辑回归模型...')
    x_train, y_train, x_test, y_test = load_data()
    tf_idf_vec = tf_idf_init(x_train)
    x_train, x_test = tf_idf_vec.transform(x_train), tf_idf_vec.transform(x_test)
    lr = lr_init(x_train, y_train)
    print('模型准确率：%.4f%%' % (lr.score(x_test, y_test) * 100))

    print('*' * 100 + '\n正在对测试集进行问题类别预测...')
    json_lst = read_json(test_predict_path)  # 对测试集的问题进行类别预测
    x_data = [' '.join(item['question']) for item in json_lst]
    y_data = lr.predict(tf_idf_vec.transform(x_data))
    for item, label in zip(json_lst, y_data):
        item['label'] = label
    write_json(test_label_path, json_lst)
    print('预测结束\n' + '*' * 100)


if __name__ == '__main__':
    main()
