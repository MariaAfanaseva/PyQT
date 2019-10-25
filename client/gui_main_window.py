import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from client.main_window_config import Ui_MainWindow
from client.gui_add_contact import AddContactDialog
from client.gui_del_contact import DelContactDialog
from database_client import ClientDB


class ClientMainWindow(QMainWindow):
    def __init__(self, app, client_transport, database_client):
        super().__init__()
        self.app = app
        self.client_transport = client_transport
        self.database_client = database_client
        self.message_window = QMessageBox()

    def init_ui(self):
        # Загружаем конфигурацию окна из дизайнера
        self.user_interface = Ui_MainWindow()
        self.user_interface.setupUi(self)
        
        self.field_disable()

        self.user_interface.actionClose.triggered.connect(self.app.quit)
        self.user_interface.addContactButton.clicked.connect(self.add_contact_dialog)
        self.user_interface.actionAdd_contact.triggered.connect(self.add_contact_dialog)
        self.user_interface.actionRemove_contact.triggered.connect(self.del_contact_dialog)
        self.user_interface.remContactButton.clicked.connect(self.del_contact_dialog)
        self.user_interface.sendMessageButton.clicked.connect(self.send_message)
        # Даблклик по листу контактов отправляется в обработчик
        self.user_interface.contactsListView.doubleClicked.connect(self.select_active_user)

        self.user_interface.messageHistoryEdit.ensureCursorVisible()
        self.user_interface.messageHistoryEdit.fontItalic()
        self.user_interface.messageHistoryEdit.setFont(QtGui.QFont('SansSerif', 10))
        
        self.update_clients_list()
        self.show()

    def field_disable(self):
        self.user_interface.messageLabel.setText('To select a recipient, double-click it in the contacts window.')
        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.user_interface.sendMessageButton.setDisabled(True)
        self.user_interface.clearMessageButton.setDisabled(True)
        self.user_interface.messageEdit.setDisabled(True)

    def add_contact_dialog(self):
        self.add_contact_window = AddContactDialog(self.client_transport, self.database_client)
        self.add_contact_window.init_ui()
        # Update contacts list 
        self.add_contact_window.user_interface.addContactButton.clicked.connect(self.update_clients_list)
        self.add_contact_window.show()

    def update_clients_list(self):
        self.contacts_list = self.database_client.get_contacts()
        self.contacts_model = QStandardItemModel()
        for contact in sorted(self.contacts_list):
            item = QStandardItem(contact)       
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.user_interface.contactsListView.setModel(self.contacts_model)
        
    def del_contact_dialog(self):
        # Определяем выбранного контакта
        self.del_contact_name = self.user_interface.contactsListView.currentIndex().data()
        if not self.del_contact_name:
            self.message_window.information(self, 'Warning', 'Select a contact to delete!')
        else:
            #  Создаем диалог с пользователем
            self.del_contact_dialog = DelContactDialog(self.client_transport, self.del_contact_name)
            self.del_contact_dialog.init_ui()
            self.del_contact_dialog.user_interface.removeButton.clicked.connect(self.update_clients_list)
            self.del_contact_dialog.show()
            
    def select_active_user(self):
        self.current_chat = self.user_interface.contactsListView.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        self.user_interface.messageLabel.setText(f'Enter message for {self.current_chat}:')
        self.user_interface.clearMessageButton.setDisabled(False)
        self.user_interface.sendMessageButton.setDisabled(False)
        self.user_interface.messageEdit.setDisabled(False)

        # Заполняем окно историю сообщений
        self.history_list_update()

    def send_message(self):
        message_text = self.user_interface.messageEdit.toPlainText()
        self.user_interface.messageEdit.clear()
        if not message_text:
            return
        else:
            is_success = self.client_transport.send_user_message(self.current_chat, message_text)
            if not is_success:
                self.message_window.critical(self, 'Error', 'Lost server connection!')
                self.close()
            elif is_success is True:
                self.history_list_update()
                # self.message_window.warning(self, 'OK', 'Message sent!')
            else:
                self.message_window.warning(self, 'Warning', is_success)

    def history_list_update(self):
        # Sorted date
        list_messages = sorted(self.database_client.get_history(self.current_chat), key=lambda item: item[3])

        self.user_interface.messageHistoryEdit.clear()

        length = len(list_messages)
        start_index = 0
        if length > 20:
            start_index = length - 20

        for i in range(start_index, length):
            item = list_messages[i]
            if item[1] == 'in':
                msg = f'Incoming message from {item[3].replace(microsecond=0)}:\n {item[2]}\n'
                self.user_interface.messageHistoryEdit.append(msg)
                self.user_interface.messageHistoryEdit.setTextBackgroundColor(QColor(255, 213, 213))
                self.user_interface.messageHistoryEdit.setAlignment(Qt.AlignLeft)
            else:
                msg = f'Outgoing message from {item[3].replace(microsecond=0)}:\n {item[2]}\n'
                self.user_interface.messageHistoryEdit.append(msg)
                self.user_interface.messageHistoryEdit.setTextBackgroundColor(QColor(204, 255, 204))
                self.user_interface.messageHistoryEdit.setAlignment(Qt.AlignRight)    


if __name__ == '__main__':
    database = ClientDB('lala')
    app = QApplication(sys.argv)
    main_window = ClientMainWindow(app, database)
    main_window.init_ui()
    sys.exit(app.exec_())



