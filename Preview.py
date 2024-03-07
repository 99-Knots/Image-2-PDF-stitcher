from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt, pyqtSignal

from structures import ImageFile


class ImagePreview(QWidget):
    previewChanged = pyqtSignal(ImageFile)

    def __init__(self, files: list[ImageFile]):
        super(ImagePreview, self).__init__()
        self.preview_img = None
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet('background-color: rgb(192, 192, 192)')
        self.preview_lbl.setFixedSize(375, 500)
        self.files = files
        self._index = 0
        self._page_count = 0

        next_btn = QPushButton('>')
        next_btn.clicked.connect(lambda: self.go_to_index(self.index + 1))
        prev_btn = QPushButton('<')
        prev_btn.clicked.connect(lambda: self.go_to_index(self.index - 1))

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(prev_btn)
        self.layout.addWidget(self.preview_lbl)
        self.layout.addWidget(next_btn)

    @property
    def index(self):
        return self._index

    @index.setter   # setters allow for signals to be emitted on changes to variable -> link with labels
    def index(self, index):
        self._index = index
        if self.files:
            self.update_preview()
            self.previewChanged.emit(self.files[self.index])

    @property
    def page_count(self):
        return self._page_count

    @page_count.setter
    def page_count(self, i: int):
        self._page_count = i

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
