from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QLabel, QPushButton, QCheckBox, QComboBox,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDir, QFileInfo, QSize, Qt, pyqtSignal

from PIL import Image

from structures import SortKeys, PageLayout, ImageFile


class IconAttribute:
    def __init__(self, icon_path, attribute):
        self.icon = QIcon(icon_path)
        self.attribute = attribute


class LayoutMenu(QWidget):
    selectionChanged = pyqtSignal(PageLayout)
    coverChecked = pyqtSignal(bool)

    def __init__(self):
        super(LayoutMenu, self).__init__()
        lbl = QLabel('PDF layout: ')
        attributes = [IconAttribute('images/singlePageIcon.png', PageLayout.SINGLE_PAGE),
                      IconAttribute('images/doublePageIcon1.png', PageLayout.DOUBLE_PAGE_LEFT_RIGHT),
                      IconAttribute('images/doublePageIcon2.png', PageLayout.DOUBLE_PAGE_RIGHT_LEFT)]
        self.buttons = list()
        self.selected_index = 0

        cover_checkbox = QCheckBox('first image as separate cover')
        cover_checkbox.stateChanged.connect(lambda b: self.coverChecked.emit(b))
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(lbl)
        layout.addLayout(btn_layout)
        layout.addWidget(cover_checkbox)

        for i, attr in enumerate(attributes):
            btn = QPushButton()
            btn.setIcon(attr.icon)
            btn.setIconSize(QSize(32, 32))
            btn.setCheckable(True)
            btn.clicked.connect(lambda x, index=i: self.select_index(index))
            btn.clicked.connect(lambda x, a=attr.attribute: self.selectionChanged.emit(a))
            btn_layout.addWidget(btn)
            self.buttons.append(btn)

        if self.buttons:
            self.buttons[0].click()

    def select_index(self, index=0):
        if self.buttons:
            self.buttons[self.selected_index].setChecked(False)
            self.selected_index = index
            self.buttons[self.selected_index].setChecked(True)


class LoadMenu(QWidget):
    loadedFiles = pyqtSignal(list)

    def __init__(self):
        super(LoadMenu, self).__init__()
        load_dir_btn = QPushButton('load from folder')
        load_files_btn = QPushButton('load from files')

        load_dir_btn.clicked.connect(self.load_by_dir)
        load_files_btn.clicked.connect(self.load_by_files)

        layout = QVBoxLayout(self)
        layout.addWidget(load_dir_btn)
        layout.addWidget(load_files_btn)

    def load_by_dir(self):
        selected_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if selected_path:
            files = list()
            directory = QDir(selected_path)
            file_infos = directory.entryInfoList(['*.jpg', '*.png', '*.bmp'], QDir.Filter.Files)
            for file in file_infos:
                files.append(ImageFile(file))
            self.loadedFiles.emit(files)

    def load_by_files(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Select individual Files', '', 'Image Files (*.png *.jpg *.bmp)')
        if filenames[0]:
            files = list()
            for file in filenames[0]:
                files.append(ImageFile(QFileInfo(file)))
            self.loadedFiles.emit(files)


class SaveMenu(QWidget):
    def __init__(self, files: list[ImageFile],
                 page_layout: PageLayout = PageLayout.SINGLE_PAGE,
                 separate_cover: bool = True):
        super(SaveMenu, self).__init__()
        self.files = files
        self.left_to_right = True
        self.double_pages = True
        self.separate_cover = separate_cover
        self.set_pdf_layout(page_layout)
        save_btn = QPushButton('create PDF')
        layout = QVBoxLayout(self)
        layout.addWidget(save_btn)
        save_btn.clicked.connect(self.create_pdf)

    def set_separate_cover(self, separate_cover: bool):
        self.separate_cover = separate_cover

    def set_pdf_layout(self, layout: PageLayout):
        if layout == PageLayout.SINGLE_PAGE:
            self.left_to_right = True
            self.double_pages = False
        elif layout == PageLayout.DOUBLE_PAGE_LEFT_RIGHT:
            self.left_to_right = True
            self.double_pages = True
        elif layout == PageLayout.DOUBLE_PAGE_RIGHT_LEFT:
            self.left_to_right = False
            self.double_pages = True

    def create_pdf(self):
        if self.files:
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'PDF Files  (*.pdf)')[0]
            if filename:
                if self.double_pages:
                    page_list = self.create_double_page_list()
                else:
                    page_list = self.create_single_page_list()
                if page_list:
                    page_list[0].save(filename, 'PDF', save_all=True, append_images=page_list[1:])

    def create_single_page_list(self):
        page_list = list()
        if self.files:
            for file in self.files:
                page_list.append(file.crop())
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
                if i+1 < len(self.files):
                    img2 = self.files[i+1].crop()
                    if self.left_to_right:
                        page_list.append(self.create_double_page(img1, img2))
                    else:
                        page_list.append(self.create_double_page(img2, img1))
                else:
                    if self.left_to_right:
                        page_list.append(self.create_double_page(img_left=img1))
                    else:
                        page_list.append(self.create_double_page(img_right=img1))
        return page_list

    @staticmethod
    def create_double_page(img_left: Image = None, img_right: Image = None):
        width = 0
        height = 0

        if img_left is not None:
            width += img_left.width if img_right is not None else img_left.width*2
            height = max(height, img_left.height)
        if img_right is not None:
            width += img_right.width if img_left is not None else img_right.width*2
            height = max(height, img_right.height)

        page = Image.new('RGB', (width, height), (255, 255, 255))

        if img_left is not None:
            page.paste(img_left, (0, (height-img_left.height)//2))    # place img on left edge, centered horizontally
        if img_right is not None:
            page.paste(img_right, (width-img_right.width, (height-img_right.height)//2))

        return page


class SortMenu(QWidget):
    selectionChanged = pyqtSignal(SortKeys)

    def __init__(self):
        super(SortMenu, self).__init__()
        lbl = QLabel('sort by: ')
        selection = QComboBox()
        for key in SortKeys:
            selection.addItem(key.value)
        selection.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        selection.currentTextChanged.connect(lambda t: self.selectionChanged.emit(SortKeys(t)))

        layout = QHBoxLayout(self)
        layout.addWidget(lbl)
        layout.addWidget(selection)


class CropMenu(QWidget):
    marginsChanged = pyqtSignal(int, int, int, int, bool)

    def __init__(self):
        super(CropMenu, self).__init__()
        # create the Edit Fields for input and initialize their values and functionalities
        self.left_margin = 0
        self.left_edt = QDoubleSpinBox()
        self.left_edt.setRange(0, 0)
        self.left_edt.setDecimals(0)
        self.left_edt.setWrapping(True)
        self.left_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.left_edt.valueChanged.connect(self.__set_crop_margins)

        self.right_margin = 0
        self.right_edt = QDoubleSpinBox()
        self.right_edt.setRange(0, 0)
        self.right_edt.setDecimals(0)
        self.right_edt.setWrapping(True)
        self.right_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.right_edt.valueChanged.connect(self.__set_crop_margins)

        self.top_margin = 0
        self.top_edt = QDoubleSpinBox()
        self.top_edt.setRange(0, 0)
        self.top_edt.setDecimals(0)
        self.top_edt.setWrapping(True)
        self.top_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.top_edt.valueChanged.connect(self.__set_crop_margins)

        self.bottom_margin = 0
        self.bottom_edt = QDoubleSpinBox()
        self.bottom_edt.setRange(0, 0)
        self.bottom_edt.setDecimals(0)
        self.bottom_edt.setWrapping(True)
        self.bottom_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bottom_edt.textChanged.connect(self.__set_crop_margins)

        self.same_crop_for_all = True   # whether the margin values should be applied to all or only the current image
        self.__setup_layout()

    def __setup_layout(self):
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QLabel('set crop margins:'), 0, 0, 1, 2)

        same_crop_btn = QCheckBox('use same crop margins for all')
        same_crop_btn.setChecked(self.same_crop_for_all)
        same_crop_btn.stateChanged.connect(self.__toggle_same_for_all)
        layout.addWidget(same_crop_btn, 1, 0, 1, 2)

        left_lbl = QLabel('Left: ')
        left_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        right_lbl = QLabel('Right: ')
        right_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        top_lbl = QLabel('Top: ')
        top_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        bottom_lbl = QLabel('Bottom: ')
        bottom_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        layout.addWidget(left_lbl, 2, 0)
        layout.addWidget(self.left_edt, 2, 1)
        layout.addWidget(right_lbl, 3, 0)
        layout.addWidget(self.right_edt, 3, 1)
        layout.addWidget(top_lbl, 4, 0)
        layout.addWidget(self.top_edt, 4, 1)
        layout.addWidget(bottom_lbl, 5, 0)
        layout.addWidget(self.bottom_edt, 5, 1)

    def __toggle_same_for_all(self, new_value):
        self.same_crop_for_all = new_value
        self.marginsChanged.emit(self.left_margin, self.top_margin,
                                 self.right_margin, self.bottom_margin,
                                 self.same_crop_for_all)

    def __set_crop_margins(self):
        left = int(self.left_edt.value())
        right = int(self.right_edt.value())
        top = int(self.top_edt.value())
        bottom = int(self.bottom_edt.value())

        self.left_margin = min(left, right)
        self.right_margin = max(left, right)
        self.top_margin = min(top, bottom)
        self.bottom_margin = max(top, bottom)

        self.marginsChanged.emit(self.left_margin, self.top_margin,
                                 self.right_margin, self.bottom_margin,
                                 self.same_crop_for_all)

    def set_limits(self, width, height):
        self.left_edt.setMaximum(width)
        self.left_edt.setValue(0)
        self.right_edt.setMaximum(width)
        self.right_edt.setValue(width)

        self.top_edt.setMaximum(height)
        self.top_edt.setValue(0)
        self.bottom_edt.setMaximum(height)
        self.bottom_edt.setValue(height)

    def set_edt_text(self, left, top, right, bottom):
        self.left_edt.setValue(left)
        self.top_edt.setValue(top)
        self.right_edt.setValue(right)
        self.bottom_edt.setValue(bottom)

    def load_margins(self, image: ImageFile):
        self.left_edt.setValue(image.left_margin)
        self.right_edt.setValue(image.right_margin)
        self.top_edt.setValue(image.top_margin)
        self.bottom_edt.setValue(image.bottom_margin)
