from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject


class TextEdit(QTextEdit, QObject):
    send_enter_signal = pyqtSignal()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return and e.modifiers() != Qt.ShiftModifier:
            self.send()
        else:
            super().keyPressEvent(e)

    def send(self):
        self.send_enter_signal.emit()
