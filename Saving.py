from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QCheckBox,
                             QProgressBar, QVBoxLayout, QGridLayout,
                             QFileDialog, QDialog, QSizePolicy)
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

    def __init__(self, files, filename, separate_cover, right_to_left, double_pages, to_grayscale=False, optimize=False):
        super(SavingRunnable, self).__init__()
        self.page_list = list()
        self.files = files
        self.filename = filename
        self.right_to_left = right_to_left
        self.separate_cover = separate_cover
        self.double_pages = double_pages
        self.to_grayscale = to_grayscale
        self.optimize = optimize
        self.compression_level = 6
        self.resolution = 300
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
        mode = 'RGB'
        if self.files:
            start_index = 0
            if self.separate_cover:
                start_index = 1
                page_list.append(self.files[0].crop())
            for i in range(start_index, len(self.files), 2):
                img1 = self.files[i].crop()
                if self.to_grayscale:
                    mode = 'L'
                    img1.convert('L')
                if i + 1 < len(self.files):
                    img2 = self.files[i + 1].crop()
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
        page_list[0].save(self.filename, 'PDF', optimize=self.optimize,
                          save_all=True, append_images=(p for p in page_list[1:]))
        self.signal.finished.emit()


class SaveDialog(QDialog):
    def __init__(self, files: list[ImageFile], parent=None):
        super(SaveDialog, self).__init__(parent)
        self.files = files
        self.save_path = os.path.dirname(self.files[0].absolute_path) + '/imagesTo.pdf'
        self.setWindowTitle('Save Options')

        self.to_grayscale = False
        self.optimize = True
        self.compression_level = 6
        self.resolution = 300

        self.warning_lbl = QLabel()
        self.warning_lbl.setStyleSheet('font-style: italic;')
        self.path_is_valid = True
        self.path_edt = QLineEdit()
        self.path_edt.setText(self.save_path)
        self.path_edt.textEdited.connect(self.set_save_path)

        bw_check = QCheckBox('convert to grayscale')
        bw_check.stateChanged.connect(self.set_grayscale)
        optimize_check = QCheckBox('optimize for file size')
        optimize_check.stateChanged.connect(self.set_optimize)
        save_btn = QPushButton('save')

        # set compression, resolution

        browse_btn = QPushButton('Browse...')
        browse_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        browse_btn.clicked.connect(self.select_file)

        layout = QGridLayout(self)
        layout.addWidget(self.path_edt, 0, 0, 1, 2)
        layout.addWidget(browse_btn, 0, 2, 1, 1)
        layout.addWidget(self.warning_lbl, 1, 0, 1, -1)
        layout.addWidget(bw_check, 2, 0)
        layout.addWidget(optimize_check, 2, 1)
        layout.addWidget(save_btn, 4, 0, 1, -1)

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
        #self.save_btn.clicked.connect(self.save_pdf)
        self.save_btn.clicked.connect(self.test)

    def test(self):
        if self.files:
            dialog = SaveDialog(self.files)
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

    @pyqtSlot()
    def save_pdf(self):
        """
        get save location through QFileDialog and start Saving process
        :return:
        """
        if self.files:
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'PDF Files  (*.pdf)')[0]
            if filename:
                self.activate_progress_view()
                saving = SavingRunnable(self.files, filename, self.separate_cover, self.right_to_left, self.double_pages)
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
