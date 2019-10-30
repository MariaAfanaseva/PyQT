# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'del_contact.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName('Remove contact')
        Dialog.resize(478, 161)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.removeButton = QtWidgets.QPushButton(Dialog)
        self.removeButton.setObjectName("removeButton")
        self.gridLayout.addWidget(self.removeButton, 1, 0, 1, 1)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cencelButton")
        self.gridLayout.addWidget(self.cancelButton, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate('Remove contact', 'Remove contact'))
        self.removeButton.setText(_translate('Remove contact', "Remove"))
        self.cancelButton.setText(_translate('Remove contact', "Cancel"))
        self.label.setText(_translate(
            'Remove contact', "<html><head/><body><p align=\"center\">"
                              "<span style=\" font-size:10pt;\">"
                              "Are you sure you want to remove from your contact list?"
                              "</span></p></body></html>"))
