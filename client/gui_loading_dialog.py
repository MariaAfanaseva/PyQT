import sys
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import pyqtSlot
from client.loading_config import Ui_Loading


class LoadingWindow(QDialog):
    def __init__(self, app):
        self.app = app
        self.message_window = QMessageBox()
        self.progress = 25
        super().__init__()

    def init_ui(self):
        self.user_interface = Ui_Loading()
        self.user_interface.setupUi(self)
        self.setWindowTitle(f'Loading')
        self.show()

    @pyqtSlot()
    def connection_lack(self):
        self.message_window.critical(self, 'Error', 'No connection to server!')
        self.close()

    @pyqtSlot()
    def change_value(self):
        self.progress += 25
        self.user_interface.loadingProgressBar.setValue(self.progress)
        if self.progress == 100:
            self.close()

    def make_connection_with_signals(self, transport_client_obj):
        transport_client_obj.connection_lack_signal.connect(self.connection_lack)
        transport_client_obj.progressbar_signal.connect(self.change_value)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = LoadingWindow(app)
    main_window.init_ui()
    sys.exit(app.exec_())
