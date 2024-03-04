from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QDoubleSpinBox,
                             QComboBox, QCheckBox, QPushButton, QFileDialog, QMessageBox,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy)
from PyQt6.QtGui import QPixmap, QIntValidator, QImage, QPainter, QIcon
from PyQt6.QtCore import Qt, QDir, QFileInfo, QSize, pyqtSignal

from enum import Enum
from PIL import Image


class SortKeys(Enum):
    CREATE_DATE = 'create date'
    LAST_MODIFIED = 'last modified'
    NAME = 'name'


class PageLayout(Enum):
    SINGLE_PAGE = 'single page'
    DOUBLE_PAGE_LEFT_RIGHT = 'double page — left to right'
    DOUBLE_PAGE_RIGHT_LEFT = 'double page — right to left'


class ImageFile:
    def __init__(self, file_info: QFileInfo):
        self.name = file_info.fileName()
        self.suffix = file_info.suffix().lower()
        self.create_timestamp = file_info.birthTime()
        self.absolute_path = file_info.absoluteFilePath()
        self.last_modified = file_info.lastModified()
        self.width = 0
        self.height = 0
        self.left_margin, self.right_margin, self.top_margin, self.bottom_margin = 0, 0, 0, 0
        self.__set_size()

    def __set_size(self):
        img = Image.open(self.absolute_path, 'r')
        self.width, self.height = img.size
        img.close()

    def q_image(self):
        return QImage(self.absolute_path)

    def pil_image(self):
        return Image.open(self.absolute_path, 'r')

    def set_crop_margins(self, left, top, right, bottom):
        self.left_margin = left
        self.right_margin = right
        self.top_margin = top
        self.bottom_margin = bottom

    def crop(self):
        img = Image.open(self.absolute_path, 'r')
        img = img.crop((self.left_margin, self.top_margin, self.right_margin, self.bottom_margin))
        return img


class IconAttribute:
    def __init__(self, icon_path, attribute):
        self.icon_path = icon_path
        self.attribute = attribute


class IconSelector(QWidget):
    attributeChanged = pyqtSignal(PageLayout)

    def __init__(self, icon_attributes, parent=None):
        super().__init__(parent)
        self.selected_index = None
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.buttons = list()

        for i, attribute in enumerate(icon_attributes):
            button = QPushButton()
            button.setIcon(QIcon(attribute.icon_path))
            button.setIconSize(QSize(32, 32))
            button.setCheckable(True)
            button.clicked.connect(lambda x, index=i: self.select_index(index))
            button.clicked.connect(lambda x, atr=attribute.attribute: self.emit_attribute_signal(atr))
            layout.addWidget(button)
            self.buttons.append(button)

        if self.buttons:
            self.select_index(0)

    def emit_attribute_signal(self, attribute):
        self.attributeChanged.emit(attribute)

    def select_index(self, index):
        if self.selected_index is not None:
            self.buttons[self.selected_index].setChecked(False)

        self.selected_index = index
        self.buttons[self.selected_index].setChecked(True)


class CropOptions(QWidget):
    marginsChanged = pyqtSignal(int, int, int, int, bool)

    def __init__(self):
        super(CropOptions, self).__init__()
        self.width_validator = QIntValidator(0, 0)
        self.height_validator = QIntValidator(0, 0)

        # create the Edit Fields for input and initialize their values and functionalities
        self.left_margin = 0
        self.left_edt = QDoubleSpinBox()
        self.left_edt.setRange(0, 0)
        self.left_edt.setDecimals(0)
        self.left_edt.setWrapping(True)
        self.left_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.left_edt.valueChanged.connect(self.set_crop_margins)

        self.right_margin = 0
        self.right_edt = QDoubleSpinBox()
        self.right_edt.setRange(0, 0)
        self.right_edt.setDecimals(0)
        self.right_edt.setWrapping(True)
        self.right_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.right_edt.valueChanged.connect(self.set_crop_margins)

        self.top_margin = 0
        self.top_edt = QDoubleSpinBox()
        self.top_edt.setRange(0, 0)
        self.top_edt.setDecimals(0)
        self.top_edt.setWrapping(True)
        self.top_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.top_edt.valueChanged.connect(self.set_crop_margins)

        self.bottom_margin = 0
        self.bottom_edt = QDoubleSpinBox()
        self.bottom_edt.setRange(0, 0)
        self.bottom_edt.setDecimals(0)
        self.bottom_edt.setWrapping(True)
        self.bottom_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bottom_edt.textChanged.connect(self.set_crop_margins)

        self.same_crop_for_all = True   # whether the margin values should be applied to all or only the current image
        self.__setup_layout()

    def __setup_layout(self):
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QLabel('Set crop Margins:'), 0, 0, 1, 2)

        same_crop_btn = QCheckBox('use same crop margins for all')
        same_crop_btn.setChecked(self.same_crop_for_all)
        same_crop_btn.stateChanged.connect(self.toggle_same_for_all)
        layout.addWidget(same_crop_btn, 1, 0, 1, 2)

        layout.addWidget(QLabel('Left:'), 2, 0)
        layout.addWidget(self.left_edt, 2, 1)
        layout.addWidget(QLabel('Right:'), 3, 0)
        layout.addWidget(self.right_edt, 3, 1)
        layout.addWidget(QLabel('Top:'), 4, 0)
        layout.addWidget(self.top_edt, 4, 1)
        layout.addWidget(QLabel('Bottom'), 5, 0)
        layout.addWidget(self.bottom_edt, 5, 1)

    def toggle_same_for_all(self, new_value):
        self.same_crop_for_all = new_value
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

    def set_crop_margins(self):
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


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Image to PDF Stitcher')
        self.setWindowIcon(QIcon('icon.png'))

        self.preview_lbl = QLabel(self)
        self.preview_lbl.setStyleSheet('background-color: rgb(192, 192, 192)')
        self.preview_lbl.setFixedSize(375, 500)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_img = QImage()

        self.img_index = 0
        self.files = list()

        self.max_image_width, self.max_image_height = 0, 0
        self.left_to_right = True
        self.double_pages = False
        self.separate_cover = False
        self.sort_key = SortKeys.CREATE_DATE

        self.crop_options = CropOptions()
        self.crop_options.marginsChanged.connect(self.set_crop_margins)
        self.__setup_layout()

    def __setup_layout(self):
        center_widget = QWidget(self)
        hbox_layout = QHBoxLayout(center_widget)
        prev_btn = QPushButton('<')
        prev_btn.clicked.connect(lambda: self.go_to_image(self.img_index - 1))
        next_btn = QPushButton('>')
        next_btn.clicked.connect(lambda: self.go_to_image(self.img_index + 1))
        hbox_layout.addWidget(prev_btn)
        hbox_layout.addWidget(self.preview_lbl)
        hbox_layout.addWidget(next_btn)

        option_layout = QVBoxLayout()
        option_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        load_directory_btn = QPushButton('load from directory')
        load_files_btn = QPushButton('load from files')
        load_directory_btn.clicked.connect(self.select_by_directory)
        load_files_btn.clicked.connect(self.select_by_files)

        option_layout.addWidget(load_directory_btn)
        option_layout.addWidget(load_files_btn)

        sort_layout = QHBoxLayout()
        sort_selection = QComboBox()
        for key in SortKeys:
            sort_selection.addItem(key.value)
        sort_selection.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        sort_selection.currentTextChanged.connect(lambda t: self.sort_files(SortKeys(t)))

        sort_lbl = QLabel('sort by: ')
        sort_layout.addWidget(sort_lbl)
        sort_layout.addWidget(sort_selection)
        option_layout.addLayout(sort_layout)
        option_layout.addSpacing(20)
        option_layout.addWidget(QLabel('page layout: '))
        page_layout_selection = IconSelector([IconAttribute('singlePageIcon.png', PageLayout.SINGLE_PAGE),
                                              IconAttribute('doublePageIcon1.png', PageLayout.DOUBLE_PAGE_LEFT_RIGHT),
                                              IconAttribute('doublePageIcon2.png', PageLayout.DOUBLE_PAGE_RIGHT_LEFT)])
        page_layout_selection.attributeChanged.connect(self.set_pdf_layout)
        option_layout.addWidget(page_layout_selection)

        cover_check = QCheckBox('create separate cover page')
        cover_check.setChecked(self.separate_cover)
        cover_check.stateChanged.connect(self.set_cover_slot)
        option_layout.addWidget(cover_check)

        option_layout.addSpacing(20)
        option_layout.addWidget(self.crop_options)

        option_layout.addSpacing(20)
        create_pdf_btn = QPushButton('create PDF')
        option_layout.addWidget(create_pdf_btn)
        create_pdf_btn.clicked.connect(self.create_pdf)

        hbox_layout.addLayout(option_layout)
        self.setCentralWidget(center_widget)

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

    def set_cover_slot(self, separate_cover):
        self.separate_cover = separate_cover

    def sort_files(self, key: SortKeys):
        self.sort_key = key
        if key == SortKeys.NAME:
            self.files = sorted(self.files, key=lambda f: f.name)
        if key == SortKeys.CREATE_DATE:
            self.files = sorted(self.files, key=lambda f: f.create_timestamp)
        if key == SortKeys.LAST_MODIFIED:
            self.files = sorted(self.files, key=lambda f: f.last_modified)
        self.go_to_image(0)

    def create_pdf(self):
        if self.files:
            file_name = QFileDialog.getSaveFileName(self, 'Save File', '', 'PDF Files  (*.pdf)')[0]
            if file_name:
                page_list = list()
                if self.double_pages:
                    page_list = self.create_double_page_list()
                else:
                    page_list = self.create_single_page_list()
                page_list[0].save(file_name, 'PDF', save_all=True, append_images=page_list[1:])
                msg = QMessageBox()
                msg.setWindowTitle('Saving PDF')
                msg.setWindowIcon(QIcon('icon.png'))
                msg.setText('Finished Saving!')
                msg.exec()

    def set_crop_margins(self, left, top, right, bottom, for_all):
        if self.files:
            # limit the margin values, because QValidator only affects magnitude
            l = min(left, self.max_image_width-1)
            r = min(right, self.max_image_width-1)
            t = min(top, self.max_image_height-1)
            b = min(bottom, self.max_image_height-1)

            if for_all:
                for file in self.files:
                    file.set_crop_margins(l, t, r, b)
            else:
                self.files[self.img_index].set_crop_margins(l, t, r, b)
        self.show_preview()

    def draw_crop(self):
        width = self.preview_img.width()
        height = self.preview_img.height()
        file = self.files[self.img_index]

        # todo: since this is only for display, do these conversions on the pixmap or a scaled version?

        grayscale_img = file.pil_image().convert('L')   # grayscale image in background to show discarded area
        grayscale_img = grayscale_img.point(lambda p: p*0.5)
        cropped_img = file.crop()   # cropped color version to draw over grayscale

        img = grayscale_img.convert('RGB')  # new color image with grayscale as background
        img.paste(cropped_img, (file.left_margin, file.top_margin))     # paste cropped image atop grayscale

        img = img.convert('RGBA').tobytes('raw', 'RGBA')
        self.preview_img = QImage(img, width, height, QImage.Format.Format_RGBA8888)

        painter = QPainter(self.preview_img)
        painter.setPen(Qt.GlobalColor.cyan)

        painter.drawLine(file.left_margin, 0, file.left_margin, height)
        painter.drawLine(file.right_margin, 0, file.right_margin, height)
        painter.drawLine(0, file.top_margin, width, file.top_margin)
        painter.drawLine(0, file.bottom_margin, width, file.bottom_margin)

    def create_single_page_list(self):
        page_list = list()
        for index, file in enumerate(self.files):
            img = file.crop()
            page = Image.new('RGB', (img.width, img.height))
            page.paste(img, (0, 0))
            page_list.append(page)
        return page_list

    def create_double_page_list(self):
        def double_page(img_left=None, img_right=None):
            width = 0
            height = 0

            if img_left:
                width += img_left.width if img_right else img_left.width*2
                height = max(height, img_left.height)
            if img_right:
                width += img_right.width if img_left else img_right.width*2
                height = max(height, img_right.height)

            page = Image.new('RGB', (width, height), (255, 255, 255))

            if img_left:
                page.paste(img_left, (0, 0))
            if img_right:
                page.paste(img_right, (width-img_right.width, 0))
            return page

        if self.files:
            page_list = list()
            start_index = 0

            if self.separate_cover:
                start_index = 1
                page_list.append(self.files[0].crop())
            for i in range(start_index, len(self.files), 2):
                img1 = self.files[i].crop()
                if i+1 < len(self.files):
                    img2 = self.files[i+1].crop()
                    if self.left_to_right:
                        page_list.append(double_page(img1, img2))
                    else:
                        page_list.append(double_page(img2, img1))
                else:
                    if self.left_to_right:
                        page_list.append(double_page(img1))
                    else:
                        page_list.append(double_page(img_right=img1))
            return page_list

    def update_preview_img(self):
        if self.files:
            file = self.files[self.img_index]
            self.preview_img = file.q_image()
            self.crop_options.set_edt_text(file.left_margin, file.top_margin, file.right_margin, file.bottom_margin)

    def show_preview(self):
        if self.files:
            self.draw_crop()
            pixmap = QPixmap.fromImage(self.preview_img)
            pixmap = pixmap.scaled(self.preview_lbl.size(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.preview_lbl.setPixmap(pixmap)

    def go_to_image(self, index):
        if self.files:
            self.img_index = (len(self.files) + index) % len(self.files)
            self.update_preview_img()
            self.show_preview()

    def select_by_directory(self):
        self.reset_files()
        selected_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if selected_path:
            directory = QDir(selected_path)
            file_infos = directory.entryInfoList(['*.jpg', '*.png', '*.bmp'],
                                                 QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
            for file in file_infos:
                self.add_file(file)
            self.sort_files(self.sort_key)
            self.crop_options.set_limits(self.max_image_width-1, self.max_image_height-1)
            self.go_to_image(0)

    def select_by_files(self):
        self.reset_files()
        filenames = QFileDialog.getOpenFileNames(self, 'Select individual Files', '', 'Image Files (*.png *.jpg *.bmp)')
        if filenames[0]:
            self.files = list()
            for file in filenames[0]:
                self.add_file(QFileInfo(file))
            self.sort_files(self.sort_key)
            self.crop_options.set_limits(self.max_image_width-1, self.max_image_height-1)
            self.go_to_image(0)

    def add_file(self, file_info):
        img_file = ImageFile(file_info)
        if self.max_image_width < img_file.width:
            self.max_image_width = img_file.width
        if self.max_image_height < img_file.height:
            self.max_image_height = img_file.height
        self.files.append(img_file)

    def reset_files(self):
        self.files = list()
        self.img_index = 0
        self.max_image_width, self.max_image_height = 0, 0
