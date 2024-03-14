from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from structures import ImageFile
from Preview import ImagePreview
from Menus import CropMenu, LoadMenu, SortMenu, LayoutMenu
from Saving import SaveMenu


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Images to PDF Stitcher')
        self.setWindowIcon(QIcon('images/icon.png'))

        # properties
        self.files = list()     # all loaded image files; passed to widgets by reference
        self.current_image = None
        self.max_image_width, self.max_image_height = 0, 0
        self.page_list = list()

        # widgets
        self.preview = ImagePreview(self.files)

        self.load_menu = LoadMenu()
        self.save_menu = SaveMenu(self.files)
        self.layout_menu = LayoutMenu()
        self.sort_menu = SortMenu(self.files)
        self.crop_menu = CropMenu()

        # setup signal/slot interaction between widgets
        self.preview.previewChanged.connect(self.set_current_image)
        self.preview.previewChanged.connect(self.crop_menu.load_margins)
        self.preview.previewChanged.connect(self.save_menu.hide_progress)

        self.load_menu.loadedFiles.connect(self.load_files)
        self.load_menu.loadedFiles.connect(lambda: self.sort_menu.sort_files())
        self.load_menu.loadedFiles.connect(lambda: self.crop_menu.set_limits(self.max_image_width - 1,
                                                                             self.max_image_height - 1))
        self.load_menu.loadedFiles.connect(lambda: self.preview.go_to_index())

        self.sort_menu.selectionChanged.connect(self.preview.update_preview)
        self.save_menu.started.connect(lambda: self.toggle_menu_enabled(False))
        self.save_menu.finished.connect(lambda: self.toggle_menu_enabled(True))

        self.crop_menu.marginsChanged.connect(self.set_crop_margins)
        self.crop_menu.marginsChanged.connect(self.preview.update_preview)

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
        option_layout.addWidget(self.crop_menu)
        option_layout.addWidget(self.layout_menu)
        option_layout.addWidget(self.save_menu)

        main_layout.addLayout(option_layout)
        self.setCentralWidget(center_widget)

    def toggle_menu_enabled(self, enabled):
        self.preview.setEnabled(enabled)
        self.load_menu.setEnabled(enabled)
        self.sort_menu.setEnabled(enabled)
        self.layout_menu.setEnabled(enabled)
        self.crop_menu.setEnabled(enabled)
        self.save_menu.setEnabled(enabled)

    def set_current_image(self, file: ImageFile):
        self.current_image = file

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
        for f in self.files:
            if f.width > self.max_image_width:
                self.max_image_width = f.width
            if f.height > self.max_image_height:
                self.max_image_height = f.height

    def reset_files(self):
        self.files.clear()
        self.max_image_width, self.max_image_height = 0, 0
