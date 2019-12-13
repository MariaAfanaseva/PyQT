# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'loading.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Loading(object):
    def setupUi(self, Loading):
        Loading.setObjectName("Loading")
        Loading.resize(354, 152)
        self.gridLayout_2 = QtWidgets.QGridLayout(Loading)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(-1, -1, -1, 18)
        self.gridLayout.setObjectName("gridLayout")
        self.waitLabel = QtWidgets.QLabel(Loading)
        self.waitLabel.setObjectName("waitLabel")
        self.gridLayout.addWidget(self.waitLabel, 0, 0, 1, 1)
        self.loadingProgressBar = QtWidgets.QProgressBar(Loading)
        self.loadingProgressBar.setMinimumSize(QtCore.QSize(0, 50))
        self.loadingProgressBar.setProperty("value", 24)
        self.loadingProgressBar.setObjectName("loadingProgressBar")
        self.gridLayout.addWidget(self.loadingProgressBar, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Loading)
        QtCore.QMetaObject.connectSlotsByName(Loading)

    def retranslateUi(self, Loading):
        _translate = QtCore.QCoreApplication.translate
        Loading.setWindowTitle(_translate("Loading", "Dialog"))
        self.waitLabel.setText(_translate("Loading", "<html><head/><body><p align=\"center\"><span style=\" font-size:10pt;\">Server is loading. Please wait!</span></p></body></html>"))
