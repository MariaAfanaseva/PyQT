import sys
import os
import numpy as np
from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from gui_client.image_config import Ui_Form


class ImageAddForm(QDialog):
    """Create window for add image."""
    def __init__(self, database):
        self.database = database
        self.pix_img_size = None
        self.convert_pix_img_size = None
        self.image = None
        self.path = 'img/my_img.jpg'
        self.user_interface = Ui_Form()
        super().__init__()

    def init_ui(self):
        self.user_interface.setupUi(self)
        self.buttons_blocking()
        self.user_interface.openButton.clicked.\
            connect(self.open_image)
        self.user_interface.sepiaButton.clicked.connect(self.set_sepia)
        self.user_interface.negativeButton.clicked.connect(self.set_negative)
        self.user_interface.grayButton.clicked.connect(self.set_gray)
        self.user_interface.defaultButton.clicked.connect(self.set_default)
        self.user_interface.bwButton.clicked.connect(self.set_black_white)
        self.user_interface.cutButton.clicked.connect(self.center_crop)
        self.user_interface.cancelButton.clicked.connect(self.close)
        self.user_interface.saveButton.clicked.connect(self.save_img)

        if os.path.exists(self.path):
            self.show_img()
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
        self.show_img()

    def show_img(self):
        pix_img = QPixmap(self.path)
        self.pix_img_size = pix_img.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(self.pix_img_size)
        self.user_interface.imageLabel.setAlignment(Qt.AlignCenter)
        self.buttons_unlock()
        self.image = Image.open(self.path)

    def convert_img_show(self, image):
        # image = image.resize((300, 300), Image.NEAREST)
        img_tmp = ImageQt(image.convert('RGBA'))
        convert_pix_img = QPixmap.fromImage(img_tmp)
        self.convert_pix_img_size = convert_pix_img.scaled(300, 300, Qt.KeepAspectRatio)
        self.user_interface.imageLabel.setPixmap(self.convert_pix_img_size)

    def set_sepia(self):
        """
        Optimization on the sepia filter using numpy
        """
        # Load the image as an array so cv knows how to work with it
        img = np.array(self.image)

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
        img_invert = ImageOps.invert(self.image)
        self.convert_img_show(img_invert)

    def set_gray(self):
        img = self.image.convert('LA')
        self.convert_img_show(img)

    def set_black_white(self):
        thresh = 150
        img_convert = self.image.convert('L').point(lambda x: 255 if x > thresh else 0, mode='1')
        self.convert_img_show(img_convert)

    def set_default(self):
        self.user_interface.imageLabel.setPixmap(self.pix_img_size)

    def cut_image(self):
        img = self.image.crop((50, 50, 200, 200))
        self.convert_img_show(img)

    def center_crop(self):
        """Crop the center of the image."""
        width, height = self.image.size
        new_width = width // 2
        new_height = height // 2
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        center_cropped_img = self.image.crop((left, top, right, bottom))

        self.convert_img_show(center_cropped_img)

    def save_img(self):
        path = 'img/my_img.jpg'
        if self.convert_pix_img_size:
            self.convert_pix_img_size.save('img/my_img.jpg')
        else:
            self.pix_img_size.save('img/my_img.jpg')
        self.database.add_image(path)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ImageAddForm()
    main_window.init_ui()
    sys.exit(app.exec_())
