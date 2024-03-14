from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QProgressBar, QVBoxLayout, QFileDialog
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from PIL import Image

from structures import PageLayout, ImageFile


class SavingRunnable(QRunnable):
    """
    QRunnable instance to prepare the PDF pages and save the file without blocking the GUI-thread
    """
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


class SaveWidget(QWidget):
    """
    Menu that handles the PDF formatting and saving Progress
    """
    started = pyqtSignal()
    finished = pyqtSignal()

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
        self.save_btn.clicked.connect(self.save_pdf)

    @pyqtSlot(bool)
    def set_separate_cover(self, separate_cover: bool):
        self.separate_cover = separate_cover

    @pyqtSlot(PageLayout)
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

                self.started.emit()
                saving = SavingRunnable(self.files, filename, self.separate_cover, self.right_to_left, self.double_pages)
                saving.signal.progress.connect(self.progress)
                saving.signal.finished.connect(lambda: self.progress(len(self.files)))
                QThreadPool.globalInstance().start(saving)

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
            self.finished.emit()

    def activate_progress_view(self):
        self.progress_bar.setHidden(False)
        self.progress_lbl.setHidden(False)
        self.set_progress_max(len(self.files))
        self.progress_bar.setValue(0)
        self.progress_lbl.setText('Saving...')

    def setEnabled(self, a0: bool):
        self.save_btn.setEnabled(a0)

