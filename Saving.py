from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QCheckBox, QSlider, QSpacerItem,
                             QProgressBar, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QFileDialog, QDialog, QSizePolicy)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from PIL import Image
import os.path

from structures import ImageFile


class SavingRunnable(QRunnable):
    """
    QRunnable instance to prepare the PDF pages and save the file without blocking the GUI-thread
    """
    class SavingSignal(QObject):
        finished = pyqtSignal()
        progress = pyqtSignal(int)

    def __init__(self, files, filename, separate_cover, right_to_left, double_pages, to_grayscale=False, optimize=False, compress_lvl=0, res=300, img_scale=1.0):
        super(SavingRunnable, self).__init__()
        self.page_list = list()
        self.files = files
        self.filename = filename
        self.right_to_left = right_to_left
        self.separate_cover = separate_cover
        self.double_pages = double_pages
        self.to_grayscale = to_grayscale
        self.optimize = optimize
        self.compression_level = compress_lvl
        self.resolution = res
        self.img_scale = img_scale
        self.signal = SavingRunnable.SavingSignal()

    @staticmethod
    def create_double_page(img_left: Image = None, img_right: Image = None, to_grayscale: bool = False):
        width = 0
        height = 0

        if img_left is not None:
            width += img_left.width if img_right is not None else img_left.width * 2
            height = max(height, img_left.height)
        if img_right is not None:
            width += img_right.width if img_left is not None else img_right.width * 2
            height = max(height, img_right.height)

        if to_grayscale:
            page = Image.new('L', (width, height), 255)
        else:
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
                img = img.resize((int(img.width*self.img_scale), int(img.height*self.img_scale)))
                if self.to_grayscale:
                    img = img.convert('L')
                    page = Image.new('L', (img.width, img.height))
                else:
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
                img1 = img1.resize((img1.width*self.img_scale, img1.height*self.img_scale))
                if self.to_grayscale:
                    img1.convert('L')
                if i + 1 < len(self.files):
                    img2 = self.files[i + 1].crop()
                    img2 = img2.resize((img2.width*self.img_scale, img2.height*self.img_scale))
                    if self.to_grayscale:
                        img2.convert('L')
                    if self.right_to_left:
                        page_list.append(self.create_double_page(img2, img1, self.to_grayscale))
                    else:
                        page_list.append(self.create_double_page(img1, img2, self.to_grayscale))
                else:
                    if self.right_to_left:
                        page_list.append(self.create_double_page(img_right=img1, to_grayscale=self.to_grayscale))
                    else:
                        page_list.append(self.create_double_page(img_left=img1, to_grayscale=self.to_grayscale))

                self.signal.progress.emit(i)
        return page_list

    def run(self):
        if self.double_pages:
            page_list = self.create_double_page_list()
        else:
            page_list = self.create_single_page_list()
        page_list[0].save(self.filename, 'PDF', optimize=self.optimize, dpi=(self.resolution, self.resolution),
                          compress_level=self.compression_level, save_all=True, append_images=(p for p in page_list[1:]))
        self.signal.finished.emit()


class SaveDialog(QDialog):
    # emits path, if grayscale, if optimize, compression level, resolution and resize factor
    confirmedOptions = pyqtSignal(str, bool, bool, int, int, float)

    def __init__(self, default_path: str, parent=None):
        super(SaveDialog, self).__init__(parent)
        self.setWindowTitle('Save Options')

        self.save_path = default_path + '/imagesTo.pdf'
        self.to_grayscale = False
        self.optimize = False
        self.compression_level = 6
        self.resolution = 300
        self.img_scale = 1.0

        self.warning_lbl = QLabel()
        self.warning_lbl.setStyleSheet('font-style: italic;')
        self.path_is_valid = True
        self.path_edt = QLineEdit()
        self.path_edt.setText(self.save_path)
        self.path_edt.textEdited.connect(self.set_save_path)

        bw_check = QCheckBox('convert to grayscale')
        bw_check.stateChanged.connect(self.set_grayscale)
        bw_check.setChecked(self.to_grayscale)

        optimize_check = QCheckBox('optimize for file size')
        optimize_check.stateChanged.connect(self.set_optimize)
        optimize_check.setChecked(self.optimize)

        compression_slider = CustomSlider(0, 10, self.compression_level)
        compression_slider.set_extrema_label_text('no\ncompression', 'max\ncompression')
        compression_slider.valueChanged.connect(self.set_compression)

        resolution_edt = CustomIntEdit(self.resolution, 'dpi')
        resolution_edt.valueChanged.connect(self.set_resolution)

        scale_edt = CustomIntEdit(int(self.img_scale*100), '%')
        scale_edt.valueChanged.connect(self.set_img_scale)

        save_btn = QPushButton('save')
        save_btn.clicked.connect(self.on_save_press)

        browse_btn = QPushButton('Browse...')
        browse_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        browse_btn.clicked.connect(self.select_file)

        layout = QGridLayout(self)
        layout.addWidget(QLabel('path: '), 0, 0)
        layout.addWidget(self.path_edt, 0, 1, 1, 2)
        layout.addWidget(browse_btn, 0, 3)
        layout.addWidget(self.warning_lbl, 1, 1, 1, -1)

        layout.addWidget(QLabel('compression level: '), 2, 0)
        layout.addWidget(compression_slider, 2, 1)

        layout.addWidget(QLabel('resolution: '), 3, 0)
        layout.addWidget(resolution_edt, 3, 1)

        layout.addWidget(QLabel('image scale: '), 4, 0)
        layout.addWidget(scale_edt, 4, 1)

        layout.addWidget(bw_check, 5, 1, 1, -1)
        layout.addWidget(optimize_check, 6, 1, 1, -1)

        layout.addItem(QSpacerItem(15, 15), 7, 0)
        layout.addWidget(save_btn, 8, 0, 1, -1)

    def set_save_path(self, path):
        suffix = os.path.splitext(path)[1]
        if suffix.lower() == '.pdf':
            self.warning_lbl.setText('')
            self.save_path = path
            self.path_is_valid = True
            self.path_edt.setText(path)
        else:
            self.warning_lbl.setText('invalid path!')
            self.path_is_valid = False

    @pyqtSlot()
    def select_file(self):
        filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'PDF Files  (*.pdf)')[0]
        self.set_save_path(filename)

    @pyqtSlot(int)
    def set_grayscale(self, to_gray: int):
        self.to_grayscale = bool(to_gray)

    @pyqtSlot(int)
    def set_optimize(self, optimize: int):
        self.optimize = bool(optimize)

    @pyqtSlot(int)
    def set_compression(self, value: int):
        self.compression_level = value

    @pyqtSlot(int)
    def set_resolution(self, value: int):
        self.resolution = value

    @pyqtSlot(int)
    def set_img_scale(self, value: int):
        self.img_scale = value/100

    @pyqtSlot()
    def on_save_press(self):
        self.confirmedOptions.emit(self.save_path,
                                   self.to_grayscale,
                                   self.optimize,
                                   self.compression_level,
                                   self.resolution,
                                   self.img_scale)
        self.close()


class CustomSlider(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum: int, maximum: int, default: int, step_size: int = 1):
        super(CustomSlider, self).__init__()
        validator = QIntValidator(minimum, maximum)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setValue(default)
        self.slider.setSingleStep(step_size)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        edt = QLineEdit(str(default))
        edt.setValidator(validator)
        edt.setFixedWidth(edt.fontMetrics().horizontalAdvance('0') * (len(str(validator.top()))+2))
        edt.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.min_lbl = QLabel('')
        self.min_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_lbl = QLabel('')
        self.max_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_font_size = self.min_lbl.font().pointSize()
        self.min_lbl.setStyleSheet(f'font-size: {default_font_size*0.7}pt;')
        self.max_lbl.setStyleSheet(f'font-size: {default_font_size*0.7}pt;')

        edt.textEdited.connect(self.set_value)
        self.slider.valueChanged.connect(lambda v: edt.setText(str(v)))
        self.slider.valueChanged.connect(self.valueChanged.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edt)
        layout.addWidget(self.min_lbl)
        layout.addWidget(self.slider)
        layout.addWidget(self.max_lbl)

    def set_extrema_label_text(self, min_txt: str = None, max_txt: str = None):
        if min_txt is not None:
            self.min_lbl.setText(min_txt)
        if max_txt is not None:
            self.max_lbl.setText(max_txt)

    @pyqtSlot(str)
    def set_value(self, text: str):
        if text:
            value = max(self.slider.minimum(), min(int(text), self.slider.maximum()))
            self.slider.setValue(value)
        else:
            self.slider.setValue(self.slider.minimum())


class CustomIntEdit(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, default: int, unit: str):
        super(CustomIntEdit, self).__init__()
        edt = QLineEdit(str(default))
        edt.setValidator(QIntValidator(0, 999))
        edt.setFixedWidth(edt.fontMetrics().horizontalAdvance('0')*8)
        edt.setAlignment(Qt.AlignmentFlag.AlignRight)
        unit_lbl = QLabel(unit)
        unit_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edt)
        layout.addWidget(unit_lbl)

        edt.textChanged.connect(lambda t: self.valueChanged.emit(int(t)))


class SaveWidget(QWidget):
    """
    Menu that handles the PDF formatting and saving Progress
    """
    startedSaving = pyqtSignal()
    finishedSaving = pyqtSignal()

    def __init__(self, files: list[ImageFile]):
        super(SaveWidget, self).__init__()
        self.files = files
        self.right_to_left = False
        self.double_pages = False
        self.separate_cover = False

        self.save_btn = QPushButton('create PDF')
        self.progress_bar = QProgressBar()
        self.progress_lbl = QLabel('Saving...')
        self.progress_bar.setHidden(True)
        self.progress_lbl.setHidden(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_lbl)
        self.save_btn.clicked.connect(self.open_save_dialog)

    def open_save_dialog(self):
        if self.files:
            dialog = SaveDialog(os.path.dirname(self.files[0].absolute_path))
            dialog.confirmedOptions.connect(self.save_pdf)
            dialog.exec()

    @pyqtSlot(bool)
    def set_separate_cover(self, separate_cover: bool):
        self.separate_cover = separate_cover

    @pyqtSlot(bool, bool)
    def set_pdf_layout(self, double_pages: bool, right_to_left: bool):
        self.double_pages = double_pages
        self.right_to_left = right_to_left

    @pyqtSlot()
    def hide_progress(self):
        if self.progress_bar.value() >= self.progress_bar.maximum():    # don't hide progress view while saving
            self.progress_bar.setHidden(True)
            self.progress_lbl.setHidden(True)

    @pyqtSlot(str, bool, bool, int, int, float)
    def save_pdf(self, filename, to_gray, optimize, compress_lvl, res, img_scale):
        """
        get save location through QFileDialog and start Saving process
        :return:
        """
        if self.files:
            self.activate_progress_view()
            saving = SavingRunnable(self.files, filename, self.separate_cover, self.right_to_left, self.double_pages,
                                    to_gray, optimize, compress_lvl, res, img_scale)
            saving.signal.progress.connect(self.progress)
            saving.signal.finished.connect(lambda: self.progress(len(self.files)))
            QThreadPool.globalInstance().start(saving)
            self.startedSaving.emit()

    @pyqtSlot(int)
    def set_progress_max(self, new_max: int):
        self.progress_bar.setMaximum(new_max)

    @pyqtSlot(int)
    def progress(self, value: int):
        """
        advance the progress bar and if finished emit signal for that
        :param value: new value for progress bar
        :return:
        """
        self.progress_bar.setValue(value)
        if value == self.progress_bar.maximum():
            self.progress_lbl.setText('Saving Completed!')
            self.finishedSaving.emit()

    def activate_progress_view(self):
        self.progress_bar.setHidden(False)
        self.progress_lbl.setHidden(False)
        self.set_progress_max(len(self.files))
        self.progress_bar.setValue(0)
        self.progress_lbl.setText('Saving...')
