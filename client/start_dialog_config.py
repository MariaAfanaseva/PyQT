# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'start_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(249, 214)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(15)
        self.gridLayout.setObjectName("gridLayout")
        self.passwordLineEdit = QtWidgets.QLineEdit(Dialog)
        self.passwordLineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.passwordLineEdit.setObjectName("passwordLineEdit")
        self.gridLayout.addWidget(self.passwordLineEdit, 4, 0, 1, 2)
        self.loginLineEdit = QtWidgets.QLineEdit(Dialog)
        self.loginLineEdit.setEnabled(True)
        self.loginLineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.loginLineEdit.setText("")
        self.loginLineEdit.setObjectName("loginLineEdit")
        self.gridLayout.addWidget(self.loginLineEdit, 2, 0, 1, 2)
        self.exitButton = QtWidgets.QPushButton(Dialog)
        self.exitButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exitButton.setObjectName("exitButton")
        self.gridLayout.addWidget(self.exitButton, 5, 1, 1, 1)
        self.startButton = QtWidgets.QPushButton(Dialog)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 5, 0, 1, 1)
        self.loginLabel = QtWidgets.QLabel(Dialog)
        self.loginLabel.setObjectName("loginLabel")
        self.gridLayout.addWidget(self.loginLabel, 1, 0, 1, 2)
        self.passwordLabel = QtWidgets.QLabel(Dialog)
        self.passwordLabel.setObjectName("passwordLabel")
        self.gridLayout.addWidget(self.passwordLabel, 3, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.exitButton.setText(_translate("Dialog", "Exit"))
        self.startButton.setText(_translate("Dialog", "Start"))
        self.loginLabel.setText(_translate(
            "Dialog", "<html><head/><body><p><span style=\" font-size:10pt;\">"
                      "Enter your login:</span></p></body></html>"))
        self.passwordLabel.setText(_translate(
            "Dialog", "<html><head/><body><p><span style=\" font-size:10pt;\">"
                      "Enter your password:</span></p></body></html>"))
