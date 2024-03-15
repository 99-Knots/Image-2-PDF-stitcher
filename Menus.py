from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QLabel, QPushButton, QCheckBox, QComboBox,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDir, QFileInfo, QSize, Qt, pyqtSignal, pyqtSlot


from structures import SortKeys, PageLayout, ImageFile


class LayoutMenu(QWidget):
    """
    Menu for the selection of the PDF files page layout
    """
    selectionChanged = pyqtSignal(PageLayout)   # emits new Layout
    coverChecked = pyqtSignal(bool)     # emits state of separate cover checkbox

    def __init__(self):
        super(LayoutMenu, self).__init__()
        lbl = QLabel('PDF layout: ')

        # define the image-layout pairs for the selection buttons
        attributes = [('images/singlePageIcon.png', PageLayout.SINGLE_PAGE),
                      ('images/doublePageIcon1.png', PageLayout.DOUBLE_PAGE_LEFT_RIGHT),
                      ('images/doublePageIcon2.png', PageLayout.DOUBLE_PAGE_RIGHT_LEFT)]
        self.buttons = list()
        self.selected_index = 0

        cover_checkbox = QCheckBox('first image as separate cover')
        cover_checkbox.stateChanged.connect(lambda b: self.coverChecked.emit(b))

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout = QVBoxLayout(self)
        layout.addWidget(lbl)
        layout.addLayout(btn_layout)
        layout.addWidget(cover_checkbox)

        # create corresponding icon buttons for all attributes
        for i, attr in enumerate(attributes):
            btn = QPushButton()
            btn.setIcon(QIcon(attr[0]))
            btn.setIconSize(QSize(32, 32))
            btn.setCheckable(True)
            btn.clicked.connect(lambda x, index=i: self.select_index(index))
            btn.clicked.connect(lambda x, a=attr[1]: self.selectionChanged.emit(a))
            btn_layout.addWidget(btn)
            self.buttons.append(btn)

        if self.buttons:
            self.buttons[0].click()     # ensure first button is selected and all necessary signals are send

    def select_index(self, index):
        """
        uncheck the last selected button and check the new one
        :param index: index of button to be checked
        :return:
        """
        if self.buttons:
            self.buttons[self.selected_index].setChecked(False)
            self.selected_index = index
            self.buttons[self.selected_index].setChecked(True)


class LoadMenu(QWidget):
    """
    Menu for loading the images from files
    """
    loadedFiles = pyqtSignal(list)  # emits ImageFile list of new loaded files

    def __init__(self):
        super(LoadMenu, self).__init__()
        load_dir_btn = QPushButton('load from folder')
        load_files_btn = QPushButton('load from files')

        load_dir_btn.clicked.connect(self.load_by_dir)
        load_files_btn.clicked.connect(self.load_by_files)

        layout = QVBoxLayout(self)
        layout.addWidget(load_dir_btn)
        layout.addWidget(load_files_btn)

    @pyqtSlot()
    def load_by_dir(self):
        """
        get a directory and load all image files (jpg, png, bmp) from it in ImageFile format
        :return:
        """
        selected_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if selected_path:
            files = list()
            directory = QDir(selected_path)
            file_infos = directory.entryInfoList(['*.jpg', '*.png', '*.bmp'], QDir.Filter.Files)
            for file in file_infos:
                files.append(ImageFile(file))
            self.loadedFiles.emit(files)

    @pyqtSlot()
    def load_by_files(self):
        """
        get a selection of image files through a QFileDialog and load them as ImageFile format
        :return:
        """
        filenames = QFileDialog.getOpenFileNames(self, 'Select individual Files', '', 'Image Files (*.png *.jpg *.bmp)')
        if filenames[0]:
            files = list()
            for file in filenames[0]:
                files.append(ImageFile(QFileInfo(file)))
            self.loadedFiles.emit(files)


class SortMenu(QWidget):
    """
    Menu for setting the order of loaded files for PDF creation
    """
    selectionChanged = pyqtSignal(SortKeys)     # emits new SortKey

    def __init__(self, files):
        super(SortMenu, self).__init__()
        self.files = files
        self.sort_key = SortKeys.CREATE_DATE
        lbl = QLabel('sort by: ')
        selection = QComboBox()
        for key in SortKeys:
            selection.addItem(key.value)
        selection.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        selection.currentTextChanged.connect(lambda t: self.sort_files(SortKeys(t)))

        layout = QHBoxLayout(self)
        layout.addWidget(lbl)
        layout.addWidget(selection)

        self.sort_key = SortKeys(selection.itemText(0))     # set sort key to default of selection

    @pyqtSlot(SortKeys)
    def sort_files(self, key: SortKeys = None):
        if key is not None:
            self.sort_key = key
        if self.sort_key == SortKeys.NAME:
            self.files.sort(key=lambda f: f.name)
        if self.sort_key == SortKeys.CREATE_DATE:
            self.files.sort(key=lambda f: f.create_timestamp)
        if self.sort_key == SortKeys.LAST_MODIFIED:
            self.files.sort(key=lambda f: f.last_modified)
        self.selectionChanged.emit(self.sort_key)


class CropMenu(QWidget):
    """
    Menu for setting the individual margins for cropping an image
    """
    # emits left, top, right, bottom margin and whether they should be applied to all files
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

    @pyqtSlot(int)
    def __toggle_same_for_all(self, new_value: int):    # int because a QPushButtons state is given as int
        self.same_crop_for_all = new_value
        self.marginsChanged.emit(self.left_margin, self.top_margin,
                                 self.right_margin, self.bottom_margin,
                                 self.same_crop_for_all)

    @pyqtSlot()
    def __set_crop_margins(self):
        """
        read the LineEdit values and format them before emitting a signal with the new values
        :return:
        """
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

    @pyqtSlot(int, int)
    def set_limits(self, width: int, height: int):
        """
        set new maximum limits for the edit fields and reset current inputs
        :param width: new maximum width
        :param height: new maximum height
        :return:
        """
        self.left_edt.setMaximum(width)
        self.left_edt.setValue(0)
        self.right_edt.setMaximum(width)
        self.right_edt.setValue(width)

        self.top_edt.setMaximum(height)
        self.top_edt.setValue(0)
        self.bottom_edt.setMaximum(height)
        self.bottom_edt.setValue(height)

    @pyqtSlot(ImageFile)
    def load_margins(self, image: ImageFile):
        """
        load the margins saved in a selected ImageFile into the LineEdits;
        :param image: ImageFile
        :return:
        """
        self.left_edt.setValue(image.left_margin)
        self.right_edt.setValue(image.right_margin)
        self.top_edt.setValue(image.top_margin)
        self.bottom_edt.setValue(image.bottom_margin)
