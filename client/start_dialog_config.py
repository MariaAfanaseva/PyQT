# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'start_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Welcome")
        Dialog.resize(255, 127)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(15)
        self.gridLayout.setObjectName("gridLayout")
        self.startButton = QtWidgets.QPushButton(Dialog)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 3, 0, 1, 1)
        self.exitButton = QtWidgets.QPushButton(Dialog)
        self.exitButton.setObjectName("exitButton")
        self.gridLayout.addWidget(self.exitButton, 3, 1, 1, 1)
        self.nameLineEdit = QtWidgets.QLineEdit(Dialog)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.gridLayout.addWidget(self.nameLineEdit, 2, 0, 1, 2)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Welcome", "Welcome"))
        self.startButton.setText(_translate("Welcome", "Start"))
        self.exitButton.setText(_translate("Welcome", "Exit"))
        self.label.setText(_translate("Welcome", "<html><head/><body><p><span style=\" font-size:10pt;\">Enter your name</span></p></body></html>"))
