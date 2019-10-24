import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from client.main_window_config import Ui_MainWindow


class ClientMainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def init_ui(self):
        # Загружаем конфигурацию окна из дизайнера
        self.user_interface = Ui_MainWindow()
        self.user_interface.setupUi(self)

        self.user_interface.actionClose.triggered.connect(self.app.quit)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ClientMainWindow(app)
    main_window.init_ui()
    sys.exit(app.exec_())



