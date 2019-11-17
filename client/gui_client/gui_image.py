import sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
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
        self.buttons_blocking()
        self.user_interface.openButton.clicked.\
            connect(self.open_image)
        self.user_interface.sepiaButton.clicked.connect(self.set_sepia)
        self.user_interface.negativeButton.clicked.connect(self.set_negative)
        self.user_interface.grayButton.clicked.connect(self.set_gray)
        self.user_interface.defaultButton.clicked.connect(self.set_default)
        self.user_interface.bwButton.clicked.connect(self.set_black_white)
        self.show()

    def buttons_unlock(self):
        self.user_interface.sepiaButton.setDisabled(False)
        self.user_interface.negativeButton.setDisabled(False)
        self.user_interface.grayButton.setDisabled(False)
        self.user_interface.bwButton.setDisabled(False)
        self.user_interface.defaultButton.setDisabled(False)
        self.user_interface.cutButton.setDisabled(False)
        self.user_interface.saveButton.setDisabled(False)
        self.user_interface.cancelButton.setDisabled(False)

    def buttons_blocking(self):
        self.user_interface.sepiaButton.setDisabled(True)
        self.user_interface.negativeButton.setDisabled(True)
        self.user_interface.grayButton.setDisabled(True)
        self.user_interface.bwButton.setDisabled(True)
        self.user_interface.defaultButton.setDisabled(True)
        self.user_interface.cutButton.setDisabled(True)
        self.user_interface.saveButton.setDisabled(True)
        self.user_interface.cancelButton.setDisabled(True)

    def open_image(self):
        self.path = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
        self.pixmap = QPixmap(self.path)
        self.pixmap_size = self.pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(self.pixmap_size)
        self.buttons_unlock()

    def convert_img_show(self, image):
        img_tmp = ImageQt(image.convert('RGBA'))
        convert_pixmap = QPixmap.fromImage(img_tmp)
        convert_pixmap_size = convert_pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(convert_pixmap_size)

    def set_sepia(self):
        """
        Optimization on the sepia filter using numpy
        """

        image = Image.open(self.path)

        # Load the image as an array so cv knows how to work with it
        img = np.array(image)

        # Apply a transformation where we multiply each pixel
        # rgb with the matrix transformation for the sepia

        lmap = np.matrix([[0.393, 0.769, 0.189],
                          [0.349, 0.686, 0.168],
                          [0.272, 0.534, 0.131]
                          ])

        filt = np.array([x * lmap.T for x in img])

        # Check wich entries have a value greather than 255 and set it to 255
        filt[np.where(filt > 255)] = 255

        # Create an image from the array
        self.convert_img_show(Image.fromarray(filt.astype('uint8')))

    def set_negative(self):
        img = Image.open(self.path)
        img_invert = ImageOps.invert(img)
        self.convert_img_show(img_invert)

    def set_gray(self):
        img = Image.open(self.path).convert('LA')
        self.convert_img_show(img)

    def set_black_white(self):
        img = Image.open(self.path)
        thresh = 150
        img_convert = img.convert('L').point(lambda x: 255 if x > thresh else 0, mode='1')
        self.convert_img_show(img_convert)

    def set_default(self):
        self.user_interface.imageLabel.setPixmap(self.pixmap_size)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ImageAddForm()
    main_window.init_ui()
    sys.exit(app.exec_())
