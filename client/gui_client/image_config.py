# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'image.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(417, 400)
        Form.setMaximumSize(QtCore.QSize(417, 400))
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.grayButton = QtWidgets.QPushButton(Form)
        self.grayButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.grayButton.setObjectName("grayButton")
        self.gridLayout.addWidget(self.grayButton, 2, 2, 1, 1)
        self.bwButton = QtWidgets.QPushButton(Form)
        self.bwButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.bwButton.setObjectName("bwButton")
        self.gridLayout.addWidget(self.bwButton, 2, 3, 1, 1)
        self.defaultButton = QtWidgets.QPushButton(Form)
        self.defaultButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.defaultButton.setObjectName("defaultButton")
        self.gridLayout.addWidget(self.defaultButton, 4, 0, 1, 1)
        self.openButton = QtWidgets.QPushButton(Form)
        self.openButton.setObjectName("openButton")
        self.gridLayout.addWidget(self.openButton, 1, 1, 1, 2)
        self.saveButton = QtWidgets.QPushButton(Form)
        self.saveButton.setObjectName("saveButton")
        self.gridLayout.addWidget(self.saveButton, 4, 3, 1, 1)
        self.cutButton = QtWidgets.QPushButton(Form)
        self.cutButton.setObjectName("cutButton")
        self.gridLayout.addWidget(self.cutButton, 4, 1, 1, 1)
        self.negativeButton = QtWidgets.QPushButton(Form)
        self.negativeButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.negativeButton.setObjectName("negativeButton")
        self.gridLayout.addWidget(self.negativeButton, 2, 1, 1, 1)
        self.sepiaButton = QtWidgets.QPushButton(Form)
        self.sepiaButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.sepiaButton.setObjectName("sepiaButton")
        self.gridLayout.addWidget(self.sepiaButton, 2, 0, 1, 1)
        self.imageLabel = QtWidgets.QLabel(Form)
        self.imageLabel.setMaximumSize(QtCore.QSize(700, 600))
        self.imageLabel.setText("")
        self.imageLabel.setObjectName("imageLabel")
        self.gridLayout.addWidget(self.imageLabel, 0, 0, 1, 4)
        self.cancelButton = QtWidgets.QPushButton(Form)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 4, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.grayButton.setText(_translate("Form", "Gray"))
        self.bwButton.setText(_translate("Form", "BW"))
        self.defaultButton.setText(_translate("Form", "Default"))
        self.openButton.setText(_translate("Form", "Open image"))
        self.saveButton.setText(_translate("Form", "Save"))
        self.cutButton.setText(_translate("Form", "Сut"))
        self.negativeButton.setText(_translate("Form", "Negative"))
        self.sepiaButton.setText(_translate("Form", "Sepia"))
        self.cancelButton.setText(_translate("Form", "Cancel"))
