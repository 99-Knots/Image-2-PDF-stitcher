from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox, QPushButton)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject

from PIL import Image

from structures import SortKeys, PageLayout, ImageFile
from Preview import ImagePreview
from Menus import CropMenu, LoadMenu, SaveMenu, SortMenu, LayoutMenu


class SavingRunnable(QRunnable):
    class SavingSignal(QObject):
        finished = pyqtSignal()
        progress = pyqtSignal(int)

    def __init__(self, files, filename, separate_cover, right_to_left, double_pages):
        super(SavingRunnable, self).__init__()
        self.page_list = list()
        self.files = files
        self.filename = filename
        self.right_to_left = right_to_left
        self.separate_cover = separate_cover
        self.double_pages = double_pages
        self.signal = SavingRunnable.SavingSignal()

    @staticmethod
    def create_double_page(img_left: Image = None, img_right: Image = None):
        width = 0
        height = 0

        if img_left is not None:
            width += img_left.width if img_right is not None else img_left.width * 2
            height = max(height, img_left.height)
        if img_right is not None:
            width += img_right.width if img_left is not None else img_right.width * 2
            height = max(height, img_right.height)

        page = Image.new('RGB', (width, height), (255, 255, 255))

        if img_left is not None:
            page.paste(img_left,
                       (0, (height - img_left.height) // 2))  # place img on left edge, centered horizontally
        if img_right is not None:
            page.paste(img_right, (width - img_right.width, (height - img_right.height) // 2))

        return page

    def create_single_page_list(self):
        page_list = list()
        if self.files:
            for i, f in enumerate(self.files):
                img = f.crop()
                page = Image.new('RGB', (img.width, img.height))
                page.paste(img, (0, 0))
                page_list.append(page)
                self.signal.progress.emit(i)
        return page_list

    def create_double_page_list(self):
        page_list = list()
        if self.files:
            start_index = 0
            if self.separate_cover:
                start_index = 1
                page_list.append(self.files[0].crop())
            for i in range(start_index, len(self.files), 2):
                img1 = self.files[i].crop()
                if i + 1 < len(self.files):
                    img2 = self.files[i + 1].crop()
                    if self.right_to_left:
                        page_list.append(self.create_double_page(img2, img1))
                    else:
                        page_list.append(self.create_double_page(img1, img2))
                else:
                    if self.right_to_left:
                        page_list.append(self.create_double_page(img_right=img1))
                    else:
                        page_list.append(self.create_double_page(img_left=img1))

                self.signal.progress.emit(i)
        return page_list

    def run(self):
        if self.double_pages:
            page_list = self.create_double_page_list()
        else:
            page_list = self.create_single_page_list()
        page_list[0].save(self.filename, 'PDF', save_all=True, append_images=(p for p in page_list[1:]))
        self.signal.finished.emit()


class MainWindow(QMainWindow):
    saveProgress = pyqtSignal(int)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Images to PDF Stitcher')
        self.setWindowIcon(QIcon('images/icon.png'))

        # properties
        self.files = list()     # all loaded image files; passed to widgets by reference
        self.current_image = None
        self.max_image_width, self.max_image_height = 0, 0
        self.right_to_left = False
        self.double_pages = False
        self.separate_cover = False
        self.sort_key = SortKeys.CREATE_DATE
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
        self.save_menu.startSaving.connect(self.create_pdf)
        self.saveProgress.connect(self.save_menu.progress)

        self.crop_menu.marginsChanged.connect(self.set_crop_margins)
        self.crop_menu.marginsChanged.connect(self.preview.update_preview)

        #self.layout_menu.selectionChanged.connect(self.save_menu.set_pdf_layout)
        #self.layout_menu.coverChecked.connect(self.save_menu.set_separate_cover)

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

    def create_pdf(self):
        self.page_list.clear()
        #self.save_menu.hide_progress()
        self.save_menu.set_progress_max(len(self.files))
        if self.files:
            file_name = QFileDialog.getSaveFileName(self, 'Save File', '', 'PDF Files  (*.pdf)')[0]
            if file_name:
                self.toggle_menu_enabled(False)
                paging = SavingRunnable(self.files, file_name, self.separate_cover, self.right_to_left, self.double_pages)
                paging.signal.finished.connect(lambda: self.toggle_menu_enabled(True))
                paging.signal.finished.connect(lambda: self.saveProgress.emit(len(self.files)))
                paging.signal.progress.connect(lambda i: self.saveProgress.emit(i))
                QThreadPool.globalInstance().start(paging)

    def set_separate_cover(self, separate_cover: bool):
        self.separate_cover = separate_cover

    def set_pdf_layout(self, layout: PageLayout):
        if layout == PageLayout.SINGLE_PAGE:
            self.right_to_left = False
            self.double_pages = False
        elif layout == PageLayout.DOUBLE_PAGE_LEFT_RIGHT:
            self.right_to_left = False
            self.double_pages = True
        elif layout == PageLayout.DOUBLE_PAGE_RIGHT_LEFT:
            self.right_to_left = True
            self.double_pages = True

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
