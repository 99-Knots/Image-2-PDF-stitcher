from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt6.QtGui import QImage, QPixmap, QPainter, QIntValidator
from PyQt6.QtCore import Qt, pyqtSignal

from structures import ImageFile


class PageCounter(QWidget):
    pageChanged = pyqtSignal(int)

    def __init__(self):
        super(PageCounter, self).__init__()
        self.validator = QIntValidator(1, 1)

        self.current_edt = QLineEdit('0')
        self.current_edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.current_edt.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.current_edt.setValidator(self.validator)
        self.current_edt.textEdited.connect(self.emit_page_change)

        slash_lbl = QLabel('/')
        slash_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.page_nr_lbl = QLabel('0')

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_edt)
        layout.addWidget(slash_lbl)
        layout.addWidget(self.page_nr_lbl)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.resize_labels()

    def emit_page_change(self, text: str):
        if text:
            i = max(self.validator.bottom(), min(self.validator.top(), int(text)))
            self.pageChanged.emit(i-1)
        else:
            self.pageChanged.emit(0)

    def resize_labels(self):
        max_txt = '0' * (len(str(self.validator.top())) + 2)
        width = self.current_edt.fontMetrics().horizontalAdvance(max_txt)
        self.current_edt.setFixedWidth(width)
        self.page_nr_lbl.setFixedWidth(width)

    def set_page_count(self, nr: int):
        self.page_nr_lbl.setText(str(nr))
        self.validator.setTop(nr)
        self.resize_labels()

    def go_to_page(self, i: int):
        if i != 0 and self.current_edt.text() != '':
            self.current_edt.setText(str(i))


class ImagePreview(QWidget):
    previewChanged = pyqtSignal(ImageFile, int)
    pageCountChanged = pyqtSignal(int)

    def __init__(self, files: list[ImageFile]):
        super(ImagePreview, self).__init__()
        self.files = files
        self._index = 0
        self._page_count = 0

        self.preview_img = None
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet('background-color: rgb(192, 192, 192)')
        self.preview_lbl.setFixedSize(375, 500)

        self.page_counter = PageCounter()
        self.previewChanged.connect(lambda x, i: self.page_counter.go_to_page(i+1))
        self.pageCountChanged.connect(self.page_counter.set_page_count)
        self.page_counter.pageChanged.connect(self.go_to_index)

        next_btn = QPushButton('>')
        next_btn.clicked.connect(lambda: self.go_to_index(self.index + 1))
        prev_btn = QPushButton('<')
        prev_btn.clicked.connect(lambda: self.go_to_index(self.index - 1))

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(prev_btn)
        preview_layout.addWidget(self.preview_lbl)
        preview_layout.addWidget(next_btn)
        layout.addLayout(preview_layout)
        layout.addWidget(self.page_counter)

    @property
    def index(self):
        return self._index

    @index.setter   # setters allow for signals to be emitted on changes to variable -> link with labels
    def index(self, index):
        self._index = index
        if self.files:
            self.update_preview()
            self.previewChanged.emit(self.files[self.index], self.index)

    @property
    def page_count(self):
        return self._page_count

    @page_count.setter
    def page_count(self, i: int):
        if i != self.page_count:
            self._page_count = i
            self.pageCountChanged.emit(self.page_count)
            #self.page_counter.set_page_count(self.page_count)

    def assign_files(self, file_list: list[ImageFile]):
        self.files = file_list  # reference to file list
        self.page_count = len(self.files)
        self.go_to_index()

    def go_to_index(self, index=0):
        if self.files:
            self.page_count = len(self.files)   # set here to ensure it's always up to date
            self.index = (self.page_count + index) % self.page_count

    def draw_crop_preview(self):
        file = self.files[self.index]
        h = file.height
        w = file.width

        grayscale = file.pil_image().convert('L')
        grayscale = grayscale.point(lambda p: p*0.5)    # darken grayscale
        cropped_img = file.crop()
        img = grayscale.convert('RGBA')
        img.paste(cropped_img, (file.left_margin, file.top_margin))
        q_img = QImage(img.tobytes('raw', 'RGBA'), w, h, QImage.Format.Format_RGBA8888)

        # todo: since this is only for display, do these conversions on the pixmap or a scaled version?

        painter = QPainter(q_img)
        painter.setPen(Qt.GlobalColor.cyan)
        painter.drawLine(file.left_margin, 0, file.left_margin, h)
        painter.drawLine(file.right_margin, 0, file.right_margin, h)
        painter.drawLine(0, file.top_margin, w, file.top_margin)
        painter.drawLine(0, file.bottom_margin, w, file.bottom_margin)
        painter.end()

        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaled(self.preview_lbl.size(),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.preview_lbl.setPixmap(pixmap)

    def update_preview(self):
        if self.files:
            self.preview_img = self.files[self.index]
            self.draw_crop_preview()
