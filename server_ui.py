import sys
import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QApplication, QTableView, QMainWindow, \
    QAction, QLabel, QGridLayout, QDialog, QPushButton, QFileDialog, QLineEdit, QGroupBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer


class MainWindow(QMainWindow):
    def __init__(self, app, database):
        self.app = app
        self.database = database
        super().__init__()

    def init_ui(self):
        self.resize(700, 600)
        self.move(500, 300)

        self.setWindowTitle('Server')

        self.statusBar()

        exit_action = QAction('Close', self)
        exit_action.setFont(QtGui.QFont('Montserrat', 10))
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.app.quit)

        update_connected_users_action = QAction('Update connected users', self)
        update_connected_users_action.setFont(QtGui.QFont('Montserrat', 10))
        update_connected_users_action.triggered.connect(self.update_connected_users_list)

        self.settings_window = SettingsWindow()
        server_settings_action = QAction('Settings', self)
        server_settings_action.setFont(QtGui.QFont('Montserrat', 10))
        server_settings_action.triggered.connect(self.settings_window.init_ui)

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(update_connected_users_action)
        self.toolbar.addAction(server_settings_action)
        self.toolbar.addAction(exit_action)

        self.central_widget = QWidget(self)
        self.layout = QGridLayout(self.central_widget)

        self.connected_users_label = QLabel('Connected users:')
        self.connected_users_label.setFont(QtGui.QFont('Montserrat', 10))
        self.connected_users_table = QTableView(self)

        self.connected_users_table.setFont(QtGui.QFont('Montserrat', 10))

        self.connected_users_list = QStandardItemModel(self)
        self.connected_users_table.setModel(self.connected_users_list)

        self.layout.addWidget(self.connected_users_label, 0, 0)
        self.layout.addWidget(self.connected_users_table, 1, 0)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.statusBar().showMessage("Window init completed")

        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.update_connected_users_list)
        # self.timer.start(2000)

        self.update_connected_users_list()

        self.show()

    def add_connected_user(self, user_name, ip_address, port, connection_time):
        user_name = QStandardItem(user_name)
        user_name.setEditable(False)  # Зпарет на ввод данных в ячейку
        ip_address = QStandardItem(ip_address)
        ip_address.setEditable(False)
        port = QStandardItem(port)
        port.setEditable(False)
        connection_time = QStandardItem(connection_time)
        connection_time.setEditable(False)
        self.connected_users_list.appendRow([user_name, ip_address, port, connection_time])

    def update_connected_users_list(self):
        users = self.database.users_active_list()
        self.connected_users_list.clear()
        self.connected_users_list.setHorizontalHeaderLabels(['Name', 'IP', 'Port', 'Connection time'])

        for name, ip, port, time in users:
            self.add_connected_user(name, ip, str(port), time.strftime("%m/%d/%Y, %H:%M:%S"))

        #  Выравнивание колонки с датой
        self.connected_users_table.resizeColumnToContents(3)


class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()
        # self.init_ui()

    def init_ui(self):
        self.setFixedSize(500, 350)
        self.move(600, 400)

        self.setWindowTitle('Settings server')

        self.central_widget = QWidget(self)
        self.layout = QGridLayout(self.central_widget)
        self.db_path_label = QLabel('Path database: ', self)
        self.db_path_label.setFont(QtGui.QFont('Montserrat', 10))
        self.db_path_select = QPushButton('Select...', self)

        self.db_path_text = QLineEdit(self)
        self.db_path_text.setReadOnly(True)
        self.db_path_text.setFixedSize(300, 28)
        self.db_path_text.setFont(QtGui.QFont('Montserrat', 10))

        self.port_label = QLabel('Port number:', self)
        self.port_label.setFont(QtGui.QFont('Montserrat', 10))

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.setFixedSize(80, 28)
        self.port.setFont(QtGui.QFont('Montserrat', 10))

        self.ip_label = QLabel('IP address:', self)
        self.ip_label.setFont(QtGui.QFont('Montserrat', 10))

        self.ip = QLineEdit(self)
        self.ip.setFixedSize(120, 28)
        self.ip.setFont(QtGui.QFont('Montserrat', 10))

        self.ip_label_note = QLabel('Leave this field blank\n'
                                    'to accept connections from any addresses.', self)
        self.ip_label_note.setFixedSize(350, 50)
        self.ip_label_note.setFont(QtGui.QFont('Montserrat', 8))

        self.save_button = QPushButton('Save', self)
        self.save_button.setFixedSize(100, 30)

        self.close_button = QPushButton('Close', self)
        self.close_button.setFixedSize(100, 30)
        self.close_button.clicked.connect(self.close)

        self.layout.addWidget(self.db_path_label, 0, 0)
        self.layout.addWidget(self.db_path_text, 1, 0)
        self.layout.addWidget(self.db_path_select, 1, 1)
        self.layout.addWidget(self.port_label, 2, 0)
        self.layout.addWidget(self.port, 3, 0)
        self.layout.addWidget(self.ip_label, 4, 0)
        self.layout.addWidget(self.ip, 5, 0)
        self.layout.addWidget(self.ip_label_note, 6, 0)
        self.layout.addWidget(self.save_button, 7, 0, 2, 1)
        self.layout.addWidget(self.close_button, 7, 1)

        self.layout.setContentsMargins(20, 30, 0, 0)
        self.db_path_select.clicked.connect(self.open_file_select)

        self.show()

    def open_file_select(self):
        dialog = QFileDialog(self)
        path = dialog.getOpenFileName()
        path = path[0]
        self.db_path_text.insert(path)


class FakeDatabase:
    def __init__(self):
        self.count = 0

    def users_active_list(self):
        self.count = self.count + 1
        return [('maria4', '127.0.0.1', 7777, datetime.datetime(2019, 10, 20, 20, 9, 12, 605747)),
         ('maria' + str(self.count), '127.0.0.1', 7777, datetime.datetime(2019, 10, 20, 20, 9, 12, 711380)),
         ('maria6', '127.0.0.1', 7777, datetime.datetime(2019, 10, 20, 20, 9, 12, 818776))]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow(app, FakeDatabase())
    main_window.init_ui()
    # main_window.update_connected_users_list()
    app.exec_()
