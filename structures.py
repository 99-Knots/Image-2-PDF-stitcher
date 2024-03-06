from PyQt6.QtGui import QImage
from PyQt6.QtCore import QFileInfo

from PIL import Image
from enum import Enum


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
