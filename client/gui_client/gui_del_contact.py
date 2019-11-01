import sys
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from client.gui_client.del_contact_config import Ui_Dialog
from PyQt5 import QtGui
from client.database_client import ClientDB


class DelContactDialog(QDialog):
    """Create new window for remove contact."""
    def __init__(self, client_transport, del_contact_name):
        self.client_transport = client_transport
        self.del_contact_name = del_contact_name
        self.message_window = QMessageBox()
        super().__init__()

    def init_ui(self):
        self.user_interface = Ui_Dialog()
        self.user_interface.setupUi(self)
        self.user_interface.cancelButton.clicked.connect(self.close)
        self.user_interface.removeButton.clicked.connect(self.del_contact)
        self.user_interface.label.setText(
            f'Are you sure you want to remove {self.del_contact_name} from your contact list?')
        self.user_interface.label.setFont(QtGui.QFont('SansSerif', 10))
        self.show()

    def del_contact(self):
        if self.client_transport.del_contact(self.del_contact_name):
            self.message_window.information(self, 'Success', 'Contact successfully removed.')
            self.close()
        else:
            self.message_window.information(self, 'Error', 'Lost server connection')
            self.close()


if __name__ == '__main__':
    database = ClientDB('lala')
    app = QApplication(sys.argv)
    main_window = DelContactDialog('test1')
    main_window.init_ui()
    sys.exit(app.exec_())
