import sys
from PyQt5.QtWidgets import QDialog, QApplication
from client.start_dialog_config import Ui_Dialog


# Стартовый диалог с выбором имени пользователя
class UserNameDialog(QDialog):
    def __init__(self, app):
        self.app = app
        self.ok_clicked = False
        super().__init__()

    def init_ui(self):
        # Загружаем конфигурацию окна из дизайнера
        self.user_interface = Ui_Dialog()
        self.user_interface.setupUi(self)
        self.name_edit = self.user_interface.nameLineEdit
        self.user_interface.exitButton.clicked.connect(self.app.quit)
        self.user_interface.startButton.clicked.connect(self.click_start)
        self.show()

    def click_start(self):
        if self.user_interface.nameLineEdit.text():
            self.ok_clicked = True
            self.app.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = UserNameDialog(app)
    main_window.init_ui()
    sys.exit(app.exec_())
