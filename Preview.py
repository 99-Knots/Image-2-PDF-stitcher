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
        max_txt = '0' * (len(str(self.validator.top())) + 2)    # size widgets to fit page count plus some
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


class PreviewLabel(QLabel):
    def __init__(self, file: ImageFile = None):
        super(PreviewLabel, self).__init__()
        self.file = file
        self.img = QImage()
        self.setStyleSheet('background-color: rgb(192, 192, 192)')
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(375, 500)

    def resizeEvent(self, a0) -> None:
        super(PreviewLabel, self).resizeEvent(a0)
        self.update_pixmap()

    def update_pixmap(self):
        pixmap = QPixmap.fromImage(self.img)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(self.size(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(pixmap)

    def draw_crop(self):
        h = self.file.height
        w = self.file.width

        grayscale = self.file.pil_image().convert('L')
        grayscale = grayscale.point(lambda p: p * 0.5)  # darken grayscale
        cropped_img = self.file.crop()
        img = grayscale.convert('RGB')
        img.paste(cropped_img, (self.file.left_margin, self.file.top_margin))
        self.img = QImage(img.tobytes('raw', 'RGB'), w, h, QImage.Format.Format_RGB888)

        painter = QPainter(self.img)
        painter.setPen(Qt.GlobalColor.cyan)
        painter.drawLine(self.file.left_margin, 0, self.file.left_margin, h)
        painter.drawLine(self.file.right_margin, 0, self.file.right_margin, h)
        painter.drawLine(0, self.file.top_margin, w, self.file.top_margin)
        painter.drawLine(0, self.file.bottom_margin, w, self.file.bottom_margin)
        painter.end()

        self.update_pixmap()

    def set_image(self, file: ImageFile):
        self.file = file
        self.draw_crop()


class ImagePreview(QWidget):
    previewChanged = pyqtSignal(ImageFile, int)
    pageCountChanged = pyqtSignal(int)

    def __init__(self, files: list[ImageFile]):
        super(ImagePreview, self).__init__()
        self.files = files
        self._index = 0
        self._page_count = 0

        self.preview_img = QImage()
        self.preview_lbl = PreviewLabel()

        self.page_counter = PageCounter()
        self.previewChanged.connect(lambda x, i: self.page_counter.go_to_page(i+1))
        self.previewChanged.connect(self.preview_lbl.set_image)
        self.pageCountChanged.connect(self.page_counter.set_page_count)
        self.page_counter.pageChanged.connect(self.go_to_index)

        next_btn = QPushButton('>')
        next_btn.clicked.connect(lambda: self.go_to_index(self.index + 1))
        # next_btn.setMaximumWidth(next_btn.fontMetrics().averageCharWidth()*5)
        # next_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        prev_btn = QPushButton('<')
        prev_btn.clicked.connect(lambda: self.go_to_index(self.index - 1))
        # prev_btn.setMaximumWidth(next_btn.fontMetrics().averageCharWidth()*5)
        # prev_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

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
        if index != self._index:
            self._index = index
            self.update_preview()

    @property
    def page_count(self):
        return self._page_count

    @page_count.setter
    def page_count(self, i: int):
        if i != self.page_count:
            self._page_count = i
            self.pageCountChanged.emit(self.page_count)

    def go_to_index(self, index=0):
        if self.files:
            self.page_count = len(self.files)   # set here to ensure it's always up-to-date
            self.index = index % self.page_count

    def update_preview(self):
        if self.files:
            self.previewChanged.emit(self.files[self.index], self.index)

    def set_preview_lbl_height(self, h):
        self.preview_lbl.setMinimumHeight(h)
