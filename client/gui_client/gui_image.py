import sys
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from gui_client.image_config import Ui_Form


class ImageAddForm(QDialog):
    """Create window for add image."""
    def __init__(self):
        super().__init__()

    def init_ui(self):
        self.user_interface = Ui_Form()
        self.user_interface.setupUi(self)
        self.user_interface.openButton.clicked.\
            connect(self.open_image)
        self.user_interface.sepiaButton.clicked.connect(self.set_sepia)
        self.user_interface.negativeButton.clicked.connect(self.set_negative)
        self.user_interface.grayButton.clicked.connect(self.set_gray)
        self.user_interface.defaultButton.clicked.connect(self.set_default)
        self.show()

    def open_image(self):
        self.path = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
        pixmap = QPixmap(self.path)
        pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(pixmap)

    def load_img(self):
        image = Image.open(self.path)
        draw = ImageDraw.Draw(image)
        width = image.size[0]
        height = image.size[1]
        pix = image.load()
        return image, draw, width, height, pix

    def convert_img_show(self, image):
        img_tmp = ImageQt(image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img_tmp)
        pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(pixmap)

    def set_sepia(self):
        image, draw, width, height, pix = self.load_img()
        depth = 30
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                S = (a + b + c)
                a = S + depth * 2
                b = S + depth
                c = S
                if (a > 255):
                    a = 255
                if (b > 255):
                    b = 255
                if (c > 255):
                    c = 255
                draw.point((i, j), (a, b, c))

        self.convert_img_show(image)

    def set_negative(self):
        image, draw, width, height, pix = self.load_img()
        depth = 30
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                draw.point((i, j), (255 - a, 255 - b, 255 - c))

        self.convert_img_show(image)

    def set_gray(self):
        image, draw, width, height, pix = self.load_img()
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                S = (a + b + c) // 3
                draw.point((i, j), (S, S, S))

        self.convert_img_show(image)

    def set_default(self):
        pixmap = QPixmap(self.path)
        pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ImageAddForm()
    sys.exit(app.exec_())
