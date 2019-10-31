import sys
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from client.gui_client.add_contact_config import Ui_Dialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from client.database_client import ClientDB


class AddContactDialog(QDialog):
    def __init__(self, client_transport, database_client):
        self.client_transport = client_transport
        self.database_client = database_client
        self.message_window = QMessageBox()
        super().__init__()

    def init_ui(self):
        self.user_interface = Ui_Dialog()
        self.user_interface.setupUi(self)

        self.user_interface.closeWindowAddContact.clicked.connect(self.close)
        self.user_interface.updateAllUsersList.clicked.connect(self.update_users_all)
        self.user_interface.addContactButton.clicked.connect(self.add_contact)
        self.update_users_all()
        self.show()

    def update_users_all(self):
        users_list = self.database_client.get_users_known()
        self.users_model = QStandardItemModel(self)
        for user in sorted(users_list):
            item = QStandardItem(user)
            item.setEditable(False)
            self.users_model.appendRow(item)
        self.user_interface.allUsersListView.setModel(self.users_model)

    def add_contact(self):
        # Выбранный пользователем (даблклик) находится в выделеном элементе в QListView
        self.selected_contact = self.user_interface.allUsersListView.currentIndex().data()
        if self.client_transport.add_contact(self.selected_contact):
            self.message_window.information(self, 'Success', 'Contact successfully added.')
            self.close()
        else:
            self.message_window.information(self, 'Error', 'Lost server connection')
            self.close()


if __name__ == '__main__':
    database = ClientDB('lala')
    app = QApplication(sys.argv)
    main_window = AddContactDialog(database)
    main_window.init_ui()
    sys.exit(app.exec_())
