# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(807, 739)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(160, 10, 641, 351))
        self.label.setText("")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(160, 370, 641, 341))
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(20, 250, 121, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(0, 250, 31, 16))
        self.label_3.setObjectName("label_3")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(0, 60, 141, 23))
        self.pushButton_2.setMaximumSize(QtCore.QSize(16777215, 69))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(0, 90, 141, 23))
        self.pushButton_3.setMaximumSize(QtCore.QSize(16777215, 69))
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setGeometry(QtCore.QRect(0, 120, 141, 23))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_5.setGeometry(QtCore.QRect(0, 150, 141, 23))
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_6 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_6.setGeometry(QtCore.QRect(0, 180, 141, 23))
        self.pushButton_6.setObjectName("pushButton_6")
        self.vertify_Button = QtWidgets.QPushButton(self.centralwidget)
        self.vertify_Button.setGeometry(QtCore.QRect(0, 210, 141, 23))
        self.vertify_Button.setObjectName("vertify_Button")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_image = QtWidgets.QAction(MainWindow)
        self.actionOpen_image.setObjectName("actionOpen_image")
        self.actionOpen_video = QtWidgets.QAction(MainWindow)
        self.actionOpen_video.setObjectName("actionOpen_video")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_3.setText(_translate("MainWindow", "sn:"))
        self.pushButton_2.setText(_translate("MainWindow", "capture"))
        self.pushButton_3.setText(_translate("MainWindow", "calibration"))
        self.pushButton_4.setText(_translate("MainWindow", "download"))
        self.pushButton_5.setText(_translate("MainWindow", "update eeprom"))
        self.pushButton_6.setText(_translate("MainWindow", "imu data write"))
        self.vertify_Button.setText(_translate("MainWindow", "vertify"))
        self.actionOpen_image.setText(_translate("MainWindow", "Open image"))
        self.actionOpen_video.setText(_translate("MainWindow", "Open video"))
