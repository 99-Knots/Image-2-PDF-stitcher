from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSlot

from structures import ImageFile
from Preview import ImagePreview
from Menus import CropMenu, LoadMenu, SortMenu, LayoutMenu
from Saving import SaveWidget


class MainWindow(QMainWindow):
    """
    MainWindow for the Image-to-PDF application. Inherits from QMainWindow
    Handles the loaded images and the application of different settings as well as
    communication between the individual parts
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Images to PDF Stitcher')
        self.setWindowIcon(QIcon('images/icon.png'))

        # properties
        self.files = list()     # all loaded image files; passed to widgets by reference
        self.current_image = None
        self.max_image_width, self.max_image_height = 0, 0

        # widgets
        self.preview = ImagePreview(self.files)
        self.load_menu = LoadMenu()
        self.save_widget = SaveWidget(self.files)
        self.layout_menu = LayoutMenu()
        self.sort_menu = SortMenu(self.files)
        self.crop_menu = CropMenu()

        # setup signal/slot interaction between widgets
        self.preview.previewChanged.connect(self.set_current_image)
        self.preview.previewChanged.connect(self.crop_menu.load_margins)
        self.preview.previewChanged.connect(self.save_widget.hide_progress)

        self.load_menu.loadedFiles.connect(self.load_files)
        self.load_menu.loadedFiles.connect(lambda: self.sort_menu.sort_files())
        self.load_menu.loadedFiles.connect(lambda: self.crop_menu.set_limits(self.max_image_width - 1,
                                                                             self.max_image_height - 1))
        self.load_menu.loadedFiles.connect(lambda: self.preview.go_to_index())

        self.sort_menu.selectionChanged.connect(self.preview.update_preview)
        self.save_widget.started.connect(lambda: self.toggle_menu_enabled(False))
        self.save_widget.finished.connect(lambda: self.toggle_menu_enabled(True))

        self.crop_menu.marginsChanged.connect(self.set_crop_margins)
        self.crop_menu.marginsChanged.connect(self.preview.update_preview)

        self.layout_menu.selectionChanged.connect(self.save_widget.set_pdf_layout)
        self.layout_menu.coverChecked.connect(self.save_widget.set_separate_cover)

        self.__setup_layout()

    def __setup_layout(self):
        center_widget = QWidget(self)
        main_layout = QHBoxLayout(center_widget)
        main_layout.addWidget(self.preview)

        option_layout = QVBoxLayout()
        option_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        option_layout.addWidget(self.load_menu)
        option_layout.addWidget(self.sort_menu)
        option_layout.addWidget(self.crop_menu)
        option_layout.addWidget(self.layout_menu)
        option_layout.addWidget(self.save_widget)

        main_layout.addLayout(option_layout)
        self.setCentralWidget(center_widget)

    @pyqtSlot(bool)
    def toggle_menu_enabled(self, enabled):
        """
        sets the responsiveness of the individual menu parts
        :param enabled: whether menus should be enabled or not
        :return:
        """
        self.preview.setEnabled(enabled)
        self.load_menu.setEnabled(enabled)
        self.sort_menu.setEnabled(enabled)
        self.layout_menu.setEnabled(enabled)
        self.crop_menu.setEnabled(enabled)
        self.save_widget.setEnabled(enabled)

    @pyqtSlot(ImageFile)
    def set_current_image(self, file: ImageFile):
        self.current_image = file

    @pyqtSlot(int, int, int, int, bool)
    def set_crop_margins(self, left: int, top: int, right: int, bottom: int, for_all: bool):
        """
        apply the crop margins set in the crop menu to the loaded files
        :param left: index of first pixel-row of image
        :param top: index of first pixel-column
        :param right: index of last pixel-row
        :param bottom: index of last pixel-column
        :param for_all: whether the new margins should be applied to all images or only the current preview one
        :return:
        """
        if self.files:
            if for_all:
                for file in self.files:
                    file.set_crop_margins(left, top, right, bottom)
            else:
                self.current_image.set_crop_margins(left, top, right, bottom)

    @pyqtSlot(list)
    def load_files(self, files: list[ImageFile]):
        """
        assign the loaded files and determine the maximum width and height among them
        :param files: loaded files as ImageFile objects
        :return:
        """
        self.reset_files()
        self.files.extend(files)
        for f in self.files:
            if f.width > self.max_image_width:
                self.max_image_width = f.width
            if f.height > self.max_image_height:
                self.max_image_height = f.height

    def reset_files(self):
        """
        clears the list of loaded files
        :return:
        """
        self.files.clear()
        self.max_image_width, self.max_image_height = 0, 0
