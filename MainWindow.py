from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


from structures import SortKeys, ImageFile
from Preview import ImagePreview
from Menus import CropMenu, LoadMenu, SaveMenu, SortMenu, LayoutMenu


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Images to PDF Stitcher')
        self.setWindowIcon(QIcon('images/icon.png'))

        # properties
        self.files = list()     # all loaded image files; passed to widgets by reference
        self.current_image = None
        self.max_image_width, self.max_image_height = 0, 0
        self.sort_key = SortKeys.CREATE_DATE

        # widgets
        self.preview = ImagePreview(self.files)

        self.load_menu = LoadMenu()
        self.save_menu = SaveMenu(self.files)
        self.layout_menu = LayoutMenu()
        self.sort_menu = SortMenu()
        self.crop_options = CropMenu()

        # setup signal/slot interaction between widgets
        self.preview.previewChanged.connect(self.set_current_image)
        self.preview.previewChanged.connect(self.crop_options.load_margins)

        self.load_menu.loadedFiles.connect(self.load_files)
        self.sort_menu.selectionChanged.connect(self.sort_files)

        self.crop_options.marginsChanged.connect(self.set_crop_margins)
        self.crop_options.marginsChanged.connect(self.preview.update_preview)

        self.layout_menu.selectionChanged.connect(self.save_menu.set_pdf_layout)
        self.layout_menu.coverChecked.connect(self.save_menu.set_separate_cover)

        self.__setup_layout()

    def __setup_layout(self):
        center_widget = QWidget(self)
        main_layout = QHBoxLayout(center_widget)
        main_layout.addWidget(self.preview)

        option_layout = QVBoxLayout()
        option_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        option_layout.addWidget(self.load_menu)
        option_layout.addWidget(self.sort_menu)
        option_layout.addWidget(self.crop_options)
        option_layout.addWidget(self.layout_menu)
        option_layout.addWidget(self.save_menu)

        main_layout.addLayout(option_layout)
        self.setCentralWidget(center_widget)

    def set_current_image(self, file: ImageFile):
        self.current_image = file

    def sort_files(self, key: SortKeys):
        self.sort_key = key
        if key == SortKeys.NAME:
            self.files.sort(key=lambda f: f.name)
        if key == SortKeys.CREATE_DATE:
            self.files.sort(key=lambda f: f.create_timestamp)
        if key == SortKeys.LAST_MODIFIED:
            self.files.sort(key=lambda f: f.last_modified)
        self.preview.go_to_index(0)

    def set_crop_margins(self, left, top, right, bottom, for_all):
        if self.files:
            if for_all:
                for file in self.files:
                    file.set_crop_margins(left, top, right, bottom)
            else:
                self.current_image.set_crop_margins(left, top, right, bottom)

    def load_files(self, files: list[ImageFile]):
        self.reset_files()
        self.files.extend(files)
        self.sort_files(self.sort_key)
        for f in self.files:
            if f.width > self.max_image_width:
                self.max_image_width = f.width
            if f.height > self.max_image_height:
                self.max_image_height = f.height
        self.crop_options.set_limits(self.max_image_width-1, self.max_image_height-1)

    def reset_files(self):
        self.files.clear()
        self.max_image_width, self.max_image_height = 0, 0
