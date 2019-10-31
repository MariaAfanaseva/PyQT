# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'add_contact.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Add contact")
        Dialog.resize(382, 620)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.allUsersLabel = QtWidgets.QLabel(Dialog)
        self.allUsersLabel.setObjectName("allUsersLabel")
        self.gridLayout.addWidget(self.allUsersLabel, 0, 0, 1, 1)
        self.allUsersListView = QtWidgets.QListView(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.allUsersListView.sizePolicy().hasHeightForWidth())
        self.allUsersListView.setSizePolicy(sizePolicy)
        self.allUsersListView.setObjectName("allUsersListView")
        self.gridLayout.addWidget(self.allUsersListView, 2, 0, 4, 2)
        self.updateAllUsersList = QtWidgets.QPushButton(Dialog)
        self.updateAllUsersList.setObjectName("updateAllUsersList")
        self.gridLayout.addWidget(self.updateAllUsersList, 0, 1, 1, 1)
        self.addContactButton = QtWidgets.QPushButton(Dialog)
        self.addContactButton.setObjectName("addContactButton")
        self.gridLayout.addWidget(self.addContactButton, 7, 0, 1, 1)
        self.closeWindowAddContact = QtWidgets.QPushButton(Dialog)
        self.closeWindowAddContact.setObjectName("closeWindowAddContact")
        self.gridLayout.addWidget(self.closeWindowAddContact, 7, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.allUsersLabel.setText(_translate(
            "Dialog", "<html><head/><body><p><span style=\" font-size:10pt;\">"
                      "All users list</span></p></body></html>"))
        self.updateAllUsersList.setText(_translate("Dialog", "Update users all list"))
        self.addContactButton.setText(_translate("Dialog", "Add contact"))
        self.closeWindowAddContact.setText(_translate("Dialog", "Close"))
