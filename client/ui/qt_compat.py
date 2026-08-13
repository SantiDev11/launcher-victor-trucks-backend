# Universal Qt6 Compatibility Layer for PySide6 and PyQt6

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Qt, Signal, QThread, QSize, QUrl
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QProgressBar, QScrollArea, QFrame,
        QStackedWidget, QDialog, QFileDialog, QMessageBox, QButtonGroup,
        QTextEdit, QGridLayout, QCheckBox, QSizePolicy
    )
    from PySide6.QtGui import QPixmap, QIcon, QDesktopServices
    QT_LIB = "PySide6"
except ImportError:
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QThread, QSize, QUrl
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QProgressBar, QScrollArea, QFrame,
        QStackedWidget, QDialog, QFileDialog, QMessageBox, QButtonGroup,
        QTextEdit, QGridLayout, QCheckBox, QSizePolicy
    )
    from PyQt6.QtGui import QPixmap, QIcon, QDesktopServices
    QT_LIB = "PyQt6"
