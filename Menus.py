from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QLabel, QPushButton, QCheckBox,
                             QGridLayout, QHBoxLayout, QSizePolicy)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt, pyqtSignal

from structures import PageLayout


class IconAttribute:
    def __init__(self, icon_path, attribute):
        self.icon = QIcon(icon_path)
        self.attribute = attribute


class IconSelector(QWidget):
    attributeChanged = pyqtSignal(PageLayout)

    def __init__(self, icon_attributes: list[IconAttribute], parent=None):
        super().__init__(parent)
        self.selected_index = None
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.buttons = list()

        for i, attribute in enumerate(icon_attributes):
            button = QPushButton()
            button.setIcon(attribute.icon)
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
        layout.addWidget(QLabel('Set crop Margins:'), 0, 0, 1, 2)

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
