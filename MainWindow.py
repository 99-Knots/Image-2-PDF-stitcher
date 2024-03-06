from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QComboBox, QCheckBox, QPushButton,
                             QFileDialog, QMessageBox, QHBoxLayout, QVBoxLayout, QSizePolicy)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt6.QtCore import Qt, QDir, QFileInfo

from PIL import Image

from structures import PageLayout, SortKeys, ImageFile
from Menus import CropOptions, IconSelector, IconAttribute


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Images to PDF Stitcher')
        self.setWindowIcon(QIcon('images/icon.png'))

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
        page_layout_selection = IconSelector([IconAttribute('images/singlePageIcon.png', PageLayout.SINGLE_PAGE),
                                              IconAttribute('images/doublePageIcon1.png', PageLayout.DOUBLE_PAGE_LEFT_RIGHT),
                                              IconAttribute('images/doublePageIcon2.png', PageLayout.DOUBLE_PAGE_RIGHT_LEFT)])
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
                msg.setWindowIcon(QIcon('images/icon.png'))
                msg.setText('Finished Saving!')
                msg.exec()

    def set_crop_margins(self, left, top, right, bottom, for_all):
        if self.files:
            if for_all:
                for file in self.files:
                    file.set_crop_margins(left, top, right, bottom)
            else:
                self.files[self.img_index].set_crop_margins(left, top, right, bottom)
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
