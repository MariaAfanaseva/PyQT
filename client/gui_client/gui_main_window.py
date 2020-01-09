import sys
import os
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from gui_client.main_window_config import Ui_MainWindow
from gui_client.gui_add_contact import AddContactDialog
from gui_client.gui_del_contact import DelContactDialog
from database.database_client import ClientDB
from gui_client.gui_image import ImageAddForm
from gui_client.text_edit import TextEdit


class ClientMainWindow(QMainWindow):
    """Class of the main user interaction window."""
    def __init__(self, app, client_transport, database_client):
        self.app = app
        self.client_transport = client_transport
        self.database_client = database_client
        self.login = self.client_transport.client_login
        self.message_window = QMessageBox()
        self.current_chat = None
        super().__init__()

    def init_ui(self):
        """Downloading the window configuration from the designer and subscribing handlers."""
        self.user_interface = Ui_MainWindow()
        self.user_interface.setupUi(self)

        self.user_interface.messageEdit = TextEdit(self.user_interface.messageWidget)
        self.user_interface.messageEdit.setMaximumSize(QSize(16777215, 150))
        self.user_interface.messageEdit.setStyleSheet("font-size: 10pt ;")
        self.user_interface.messageLayout.addWidget(self.user_interface.messageEdit, 7, 0, 1, 3)
        self.user_interface.messageEdit.send_enter_signal.connect(self.send_enter)

        self.user_interface.actionClose.triggered.connect(self.app.quit)
        self.user_interface.addContactButton.clicked.connect(self.add_contact_dialog)
        self.user_interface.actionAdd_contact.triggered.connect(self.add_contact_dialog)
        self.user_interface.actionRemove_contact.triggered.connect(self.del_contact_dialog)
        self.user_interface.remContactButton.clicked.connect(self.del_contact_dialog)

        self.user_interface.sendMessageButton.clicked.connect(self.send_message)

        self.user_interface.boldButton.clicked.connect(self.set_bold_font)
        self.user_interface.italicButton.clicked.connect(self.set_italic_font)
        self.user_interface.underlinedButton.clicked.connect(self.set_underline_font)
        self.user_interface.normalTextButton.clicked.connect(self.normal_font)
        self.user_interface.fotoButton.setText('\U0001F4F7')
        self.user_interface.fotoButton.setStyleSheet('padding-bottom: 6px;'
                                                     'padding-right: 3px;')
        self.user_interface.fotoButton.clicked.connect(self.image_window)
        self.user_interface.smileButton.setText('\U0001F600')
        self.user_interface.smileButton_2.setText('\U0001F610')
        self.user_interface.smileButton_3.setText('\U0001F612')
        self.user_interface.smileButton.clicked.\
            connect(lambda: self.user_interface.messageEdit.insertPlainText('\U0001F600'))
        self.user_interface.smileButton_2.clicked.\
            connect(lambda: self.user_interface.messageEdit.insertPlainText('\U0001F610'))
        self.user_interface.smileButton_3.clicked.\
            connect(lambda: self.user_interface.messageEdit.insertPlainText('\U0001F612'))

        self.user_interface.clearMessageButton.clicked.connect(self.clear_edit_message)
        # Double-click on the contact list is sent to the handler
        self.user_interface.contactsListView.doubleClicked.connect(self.select_active_user)

        self.user_interface.searchContactPushButton.clicked.connect(self.search_contact)
        self.user_interface.searchMessagePushButton.clicked.connect(self.search_message)

        self.field_disable()
        self.update_clients_list()
        self.show_avatar()
        self.show()

    def field_disable(self):
        """
        Blocking function, input field and send button are not active
        until a recipient is selected.
        """
        self.user_interface.messageLabel.setText('To select a recipient, '
                                                 'double-click it in the contacts window.')

        self.user_interface.messageLabel.setFont(QFont('SansSerif', 10))

        self.user_interface.sendMessageButton.setDisabled(True)
        self.user_interface.clearMessageButton.setDisabled(True)
        self.user_interface.messageEdit.setDisabled(True)
        self.user_interface.boldButton.setDisabled(True)
        self.user_interface.italicButton.setDisabled(True)
        self.user_interface.underlinedButton.setDisabled(True)
        self.user_interface.normalTextButton.setDisabled(True)
        self.user_interface.smileButton.setDisabled(True)
        self.user_interface.smileButton_2.setDisabled(True)
        self.user_interface.smileButton_3.setDisabled(True)
        self.user_interface.searchMessageTextEdit.setDisabled(True)
        self.user_interface.searchMessagePushButton.setDisabled(True)

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
        """'Updating the contact list on the main window."""
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
            self.user_interface.boldButton.setDisabled(False)
            self.user_interface.italicButton.setDisabled(False)
            self.user_interface.underlinedButton.setDisabled(False)
            self.user_interface.normalTextButton.setDisabled(False)
            self.user_interface.smileButton.setDisabled(False)
            self.user_interface.smileButton_2.setDisabled(False)
            self.user_interface.searchMessageTextEdit.setDisabled(False)
            self.user_interface.smileButton_3.setDisabled(False)
            self.user_interface.searchMessagePushButton.setDisabled(False)

            self.history_list_update()

            if self.client_transport.avatar_request(self.current_chat):
                self.avatar_contact_show(self.current_chat)
        else:
            self.message_window.warning(
                self, 'Warning', 'User is not online.')

    def avatar_contact_show(self, contact):
        path = f'img/avatar_{contact}.jpg'
        if os.path.exists(path):
            pix_img = QPixmap(path)
            pix_img_size = pix_img.scaled(70, 70, Qt.KeepAspectRatio)
            self.user_interface.fotoLabel.setPixmap(pix_img_size)

    def send_message(self):
        """Sending an message to the current user"""
        message_text = self.user_interface.messageEdit.toHtml()
        if not self.user_interface.messageEdit.toPlainText():
            return
        else:
            self.user_interface.messageEdit.clear()
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
        time = f'<b style="color:#006400">Outgoing message from ' \
            f'{datetime.datetime.now().replace(microsecond=0)}: </b><br>'
        self.user_interface.messageHistoryEdit.insertHtml(time)
        self.user_interface.messageHistoryEdit.insertHtml(message)
        self.user_interface.messageHistoryEdit.insertHtml(f'<br>')
        self.user_interface.messageHistoryEdit.ensureCursorVisible()

    def show_history(self, list_message):
        self.user_interface.messageHistoryEdit.clear()

        length = len(list_message)
        start_index = 0
        if length > 20:
            start_index = length - 20

        for i in range(start_index, length):
            item = list_message[i]
            if item[1] == 'in':
                time = f'<b style="color:#ff0000">Incoming message from' \
                    f' {item[3].replace(microsecond=0)}:</b><br>'
                self.user_interface.messageHistoryEdit.insertHtml(time)
                self.user_interface.messageHistoryEdit.insertHtml(item[2])
                self.user_interface.messageHistoryEdit.insertHtml(f'<br>')
            elif item[1] == 'out':
                time = f'<b style="color:#006400">Outgoing message from' \
                    f' {item[3].replace(microsecond=0)}:</b><br>'
                self.user_interface.messageHistoryEdit.insertHtml(time)
                self.user_interface.messageHistoryEdit.insertHtml(item[2])
                self.user_interface.messageHistoryEdit.insertHtml(f'<br>')
        self.user_interface.messageHistoryEdit.ensureCursorVisible()

    def history_list_update(self):
        """Message history update method."""
        list_message = sorted(self.database_client.get_history(self.current_chat),
                              key=lambda item: item[3])  # sort by date

        self.show_history(list_message)

    def clear_edit_message(self):
        """Button handler - clear. Clears message input fields."""
        self.user_interface.messageEdit.clear()

    def get_text(self):
        cursor = self.user_interface.messageEdit.textCursor()
        text = cursor.selectedText()
        return text

    def set_bold_font(self):
        text = self.get_text()
        self.user_interface.messageEdit.insertHtml(f'<b>{text}</b>')

    def set_italic_font(self):
        text = self.get_text()
        self.user_interface.messageEdit.insertHtml(f'<i>{text}</i>')

    def set_underline_font(self):
        text = self.get_text()
        self.user_interface.messageEdit.insertHtml(f'<u>{text}</u>')

    def normal_font(self):
        text = self.get_text()
        self.user_interface.messageEdit.insertHtml(f'<p>{text}</ps>')

    def image_window(self):
        self.img_window = ImageAddForm(self.database_client)
        self.img_window.init_ui()
        self.img_window.user_interface.saveButton.clicked.connect(self.show_avatar)
        self.img_window.user_interface.saveButton.clicked.connect(self.client_transport.send_avatar_to_server)

    def show_avatar(self):
        path = f'img/avatar_{self.login}.jpg'
        if os.path.exists(path):
            pix_img = QPixmap(path)
            pix_img_size = pix_img.scaled(70, 70, Qt.KeepAspectRatio)
            self.user_interface.avatarLabel.setPixmap(pix_img_size)

    def search_contact(self):
        """Search contact in Contacts and show in contacts list view"""
        text = self.user_interface.searchContactTextEdit.toPlainText()
        if text:
            self.search_list = self.database_client.get_search_contact(text)
            self.search_model = QStandardItemModel()
            for contact in sorted(self.search_list):
                item = QStandardItem(contact)
                item.setEditable(False)
                self.search_model.appendRow(item)
            self.user_interface.contactsListView.setModel(self.search_model)
        else:
            self.update_clients_list()

    def search_message(self):
        """Search message in history"""
        text = self.user_interface.searchMessageTextEdit.toPlainText()
        if text:
            list_message = self.database_client.get_search_message(self.current_chat, text)
            self.show_history(list_message)
        else:
            self.history_list_update()

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

    @pyqtSlot()
    def send_enter(self):
        self.send_message()

    def make_connection_with_signals(self, client_obj):
        """Signal connection method."""
        client_obj.new_message_signal.connect(self.get_message)
        client_obj.connection_lost_signal.connect(self.connection_lost)


if __name__ == '__main__':
    database = ClientDB('lala')
    app = QApplication(sys.argv)
    main_window = ClientMainWindow(app, database)
    main_window.init_ui()
    sys.exit(app.exec_())
