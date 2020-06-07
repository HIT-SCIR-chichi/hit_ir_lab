# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(960, 540)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.et_query = QtWidgets.QLineEdit(self.frame)
        self.et_query.setAlignment(QtCore.Qt.AlignCenter)
        self.et_query.setObjectName("et_query")
        self.horizontalLayout.addWidget(self.et_query)
        self.bt_confirm = QtWidgets.QPushButton(self.frame)
        self.bt_confirm.setStyleSheet("background-color: rgb(51, 133, 255);\n"
"color: rgb(255, 255, 255);")
        self.bt_confirm.setObjectName("bt_confirm")
        self.horizontalLayout.addWidget(self.bt_confirm)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(self.centralwidget)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout_2.setSpacing(7)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.cb_type = QtWidgets.QCheckBox(self.frame_2)
        self.cb_type.setChecked(True)
        self.cb_type.setObjectName("cb_type")
        self.verticalLayout_2.addWidget(self.cb_type)
        self.lw_res = QtWidgets.QListWidget(self.frame_2)
        self.lw_res.setObjectName("lw_res")
        self.verticalLayout_2.addWidget(self.lw_res)
        self.verticalLayout.addWidget(self.frame_2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.bt_confirm.clicked.connect(MainWindow.get_search_res)
        self.cb_type.clicked.connect(MainWindow.get_search_type)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "易搜@张景润"))
        self.et_query.setText(_translate("MainWindow", "请输入检索内容"))
        self.bt_confirm.setText(_translate("MainWindow", "易搜一下"))
        self.cb_type.setText(_translate("MainWindow", "搜索新闻"))
