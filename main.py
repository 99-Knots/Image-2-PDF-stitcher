import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from MainWindow import MainWindow


if __name__ == '__main__':
    appID = 'PDFStitcher-v0.2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
