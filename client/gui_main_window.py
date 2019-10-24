import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from client.main_window_config import Ui_MainWindow


class ClientMainWindow(QMainWindow):
    def __init__(self, app, database):
        super().__init__()
        self.app = app
        self.database = database

    def init_ui(self):
        # Загружаем конфигурацию окна из дизайнера
        self.user_interface = Ui_MainWindow()
        self.user_interface.setupUi(self)
        
        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.user_interface.sendMessageButton.setDisabled(True)
        self.user_interface.clearMessageButton.setDisabled(True)
        self.user_interface.messageEdit.setDisabled(True)

        self.user_interface.actionClose.triggered.connect(self.app.quit)
        self.update_clients_list()
        self.show()

    def update_clients_list(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for contact in sorted(contacts_list):
            item = QStandardItem(contact)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.user_interface.contactsListView.setModel(self.contacts_model)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ClientMainWindow(app)
    main_window.init_ui()
    sys.exit(app.exec_())



