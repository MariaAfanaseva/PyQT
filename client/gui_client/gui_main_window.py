import sys
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5 import QtGui
from client.gui_client.main_window_config import Ui_MainWindow
from client.gui_client.gui_add_contact import AddContactDialog
from client.gui_client.gui_del_contact import DelContactDialog
from client.database_client import ClientDB


class ClientMainWindow(QMainWindow):
    """Class of the main user interaction window."""
    def __init__(self, app, client_transport, database_client):
        self.app = app
        self.client_transport = client_transport
        self.database_client = database_client
        self.message_window = QMessageBox()
        self.current_chat = None
        super().__init__()

    def init_ui(self):
        """Downloading the window configuration from the designer and subscribing handlers."""
        self.user_interface = Ui_MainWindow()
        self.user_interface.setupUi(self)

        self.field_disable()

        self.user_interface.actionClose.triggered.connect(self.app.quit)
        self.user_interface.addContactButton.clicked.connect(self.add_contact_dialog)
        self.user_interface.actionAdd_contact.triggered.connect(self.add_contact_dialog)
        self.user_interface.actionRemove_contact.triggered.connect(self.del_contact_dialog)
        self.user_interface.remContactButton.clicked.connect(self.del_contact_dialog)

        self.user_interface.sendMessageButton.clicked.connect(self.send_message)

        self.user_interface.clearMessageButton.clicked.connect(self.clear_edit_message)
        # Double-click on the contact list is sent to the handler
        self.user_interface.contactsListView.doubleClicked.connect(self.select_active_user)

        self.user_interface.messageHistoryEdit.fontItalic()
        self.user_interface.messageHistoryEdit.setFont(QtGui.QFont('SansSerif', 10))

        self.update_clients_list()
        self.show()

    def field_disable(self):
        """
        Blocking function, input field and send button are not active
        until a recipient is selected.
        """
        self.user_interface.messageLabel.setText('To select a recipient, '
                                                 'double-click it in the contacts window.')
        self.user_interface.sendMessageButton.setDisabled(True)
        self.user_interface.clearMessageButton.setDisabled(True)
        self.user_interface.messageEdit.setDisabled(True)

    def add_contact_dialog(self):
        """Open add contact dialog method"""
        self.add_contact_window = AddContactDialog(self.client_transport, self.database_client)
        self.add_contact_window.init_ui()
        self.add_contact_window.user_interface.addContactButton.clicked.\
            connect(self.update_clients_list)
        self.add_contact_window.show()

    def add_contact(self, new_contact):
        """Сontact adding method."""
        if self.client_transport.add_contact(new_contact):
            item_contact = QStandardItem(new_contact)
            item_contact.setEditable(False)
            self.contacts_model.appendRow(item_contact)
            self.message_window.information(self, 'Success',
                                            f'Contact {new_contact} successfully added.')
        else:
            self.message_window.information(self, 'Error', 'Lost server connection!')
            self.close()

    def update_clients_list(self):
        """"Updating the contact list on the main window."""
        self.contacts_list = self.database_client.get_contacts()
        self.contacts_model = QStandardItemModel()
        for contact in sorted(self.contacts_list):
            item = QStandardItem(contact)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.user_interface.contactsListView.setModel(self.contacts_model)

    def del_contact_dialog(self):
        """Method for calling the delete contact window."""
        self.del_contact_name = self.user_interface.contactsListView.currentIndex().data()
        if not self.del_contact_name:
            self.message_window.information(self, 'Warning', 'Select a contact to delete!')
        else:
            self.del_contact_dialog = DelContactDialog(self.client_transport, self.del_contact_name)
            self.del_contact_dialog.init_ui()
            self.del_contact_dialog.user_interface.removeButton.clicked.connect(self.update_clients_list)
            self.del_contact_dialog.show()

    def select_active_user(self):
        """Interlocutor selection method."""
        self.current_chat = self.user_interface.contactsListView.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """The method of activating chat with the interlocutor."""
        if self.client_transport.is_received_pubkey(self.current_chat):
            self.user_interface.messageLabel.setText(f'Enter message for {self.current_chat}:')
            self.user_interface.clearMessageButton.setDisabled(False)
            self.user_interface.sendMessageButton.setDisabled(False)
            self.user_interface.messageEdit.setDisabled(False)

            self.history_list_update()
        else:
            self.message_window.warning(
                self, 'Warning', 'User is not online.')

    def send_message(self):
        """Sending an message to the current user"""
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
                self.add_message_history(message_text)
            else:
                self.message_window.warning(self, 'Warning', is_success)

    def add_message_history(self, message):
        """Add message user in history"""
        msg = f'Outgoing message from {datetime.datetime.now().replace(microsecond=0)}:\n {message}\n'
        self.user_interface.messageHistoryEdit.setTextBackgroundColor(QColor(204, 255, 204))
        self.user_interface.messageHistoryEdit.setAlignment(Qt.AlignRight)
        self.user_interface.messageHistoryEdit.append(msg)

        self.user_interface.messageHistoryEdit.ensureCursorVisible()

    def history_list_update(self):
        """Message history update method."""
        list_messages = sorted(self.database_client.get_history(self.current_chat),
                               key=lambda item: item[3])  # sort by date

        self.user_interface.messageHistoryEdit.clear()

        length = len(list_messages)
        start_index = 0
        if length > 20:
            start_index = length - 20

        for i in range(start_index, length):
            item = list_messages[i]
            if item[1] == 'in':
                msg = f'Incoming message from {item[3].replace(microsecond=0)}:\n {item[2]}\n'
                self.user_interface.messageHistoryEdit.setTextBackgroundColor(QColor(255, 213, 213))
                self.user_interface.messageHistoryEdit.setAlignment(Qt.AlignLeft)
                self.user_interface.messageHistoryEdit.append(msg)
            elif item[1] == 'out':
                msg = f'Outgoing message from {item[3].replace(microsecond=0)}:\n {item[2]}\n'
                self.user_interface.messageHistoryEdit.setTextBackgroundColor(QColor(204, 255, 204))
                self.user_interface.messageHistoryEdit.setAlignment(Qt.AlignRight)
                self.user_interface.messageHistoryEdit.append(msg)
        self.user_interface.messageHistoryEdit.ensureCursorVisible()

    def clear_edit_message(self):
        """Button handler - clear. Clears message input fields."""
        self.user_interface.messageEdit.clear()

    @pyqtSlot(str)
    def get_message(self, sender):
        """
        Slot handler of incoming messages.
        Asks the user if a message was received not from the current interlocutor.
        If necessary, change the interlocutor.
        """
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database_client.is_contact(sender):
                if self.message_window.question(self, 'New message',
                                                f'Received a new message from {sender}, '
                                                f'open chat with him? ',
                                                QMessageBox.Yes,
                                                QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                if self.message_window.question(self, 'New message',
                                                f'Received a new message from {sender}.\n '
                                                f'This user is not in your contact list.\n '
                                                f'Add to contacts and open a chat with him?',
                                                QMessageBox.Yes,
                                                QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """Server signal loss processing slot."""
        self.message_window.critical(self, 'Error', 'Lost server connection!')
        self.close()

    def make_connection_with_signals(self, transport_client_obj):
        """Signal connection method."""
        transport_client_obj.new_message_signal.connect(self.get_message)
        transport_client_obj.connection_lost_signal.connect(self.connection_lost)


if __name__ == '__main__':
    database = ClientDB('lala')
    app = QApplication(sys.argv)
    main_window = ClientMainWindow(app, database)
    main_window.init_ui()
    sys.exit(app.exec_())
