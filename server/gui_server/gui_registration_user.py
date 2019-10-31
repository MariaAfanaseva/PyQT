import sys
import hashlib
import binascii
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from server.gui_server.user_registration_config import Ui_Dialog


class RegistrationDialog(QDialog):
    def __init__(self, database):
        self.database = database
        self.message_window = QMessageBox
        super().__init__()

    def init_ui(self):
        self.user_interface = Ui_Dialog()
        self.user_interface.setupUi(self)
        self.user_interface.cancelPushButton_2.clicked.connect(self.close)
        self.user_interface.savePushButton.clicked.connect(self.registration_user)
        self.show()

    def registration_user(self):
        login_user = self.user_interface.loginLineEdit.text()
        password = self.user_interface.passwordLineEdit.text()
        confirm_password = self.user_interface.confirmLineEdit.text()
        fullname = self.user_interface.fullNameLineEdit.text()

        if login_user and password and confirm_password:
            if password != confirm_password:
                self.message_window.critical(self, 'Error', 'The entered passwords do not match.')
                return
            elif self.database.is_user(login_user):
                self.message_window.critical(self, 'Error', 'User already exists.')
                return
            else:
                password_bytes = password.encode('utf-8')
                salt = login_user.encode('utf-8')
                password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
                password_hash_str = binascii.hexlify(password_hash)
                self.database.add_user(login_user, password_hash_str, fullname)
                self.message_window.information(self, 'Success', 'User successfully registered.')
                self.close()
        else:
            self.message_window.information(self, 'Warning', 'Required fields all, but full name.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = RegistrationDialog(app)
    main_window.init_ui()
    sys.exit(app.exec_())
