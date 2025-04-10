# -*- coding: utf-8 -*-

# 标准库导入
import sys

# 第三方库导入
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication

# 项目内模块导入
from qfluentwidgets import BodyLabel, ImageLabel, SkeletonScreen, StrongBodyLabel, SkeletonPlaceholder


class PlaceholderPage(QWidget):
    """骨架屏占位页面"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setFixedSize(420, 140)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.imgPlaceholder = SkeletonPlaceholder(4, 4, 4, 4, self)
        self.text_1_placeholder = SkeletonPlaceholder(4, 4, 4, 4, self)
        self.text_2_placeholder = SkeletonPlaceholder(4, 4, 4, 4, self)

        self.imgPlaceholder.setFixedSize(128, 128)
        self.text_1_placeholder.setFixedSize(80, 20)
        self.text_2_placeholder.setFixedSize(200, 20)

        self.vBoxLayout.setSpacing(8)
        self.vBoxLayout.addWidget(self.text_1_placeholder)
        self.vBoxLayout.addWidget(self.text_2_placeholder)
        self.vBoxLayout.addStretch(1)

        self.hBoxLayout.addWidget(self.imgPlaceholder)
        self.hBoxLayout.addLayout(self.vBoxLayout)


class ContentPage(QWidget):
    """内容页面"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setFixedHeight(100)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.img = ImageLabel(self)
        self.text_1_label = StrongBodyLabel("NapCatQQ", self)
        self.text_2_label = BodyLabel("111", self)

        self.img.scaledToWidth(64)
        self.text_1_label.setFixedSize(40, 16)
        self.text_2_label.setFixedSize(100, 16)

        self.vBoxLayout.addWidget(self.text_1_label)
        self.vBoxLayout.addWidget(self.text_2_label)
        self.vBoxLayout.addStretch(1)

        self.hBoxLayout.addWidget(self.img)
        self.hBoxLayout.addLayout(self.vBoxLayout)


class Window(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.resize(600, 500)

        self.placeholderPage = PlaceholderPage(self)
        self.contentPage = ContentPage(self)
        self.skeletonScreen = SkeletonScreen(self.placeholderPage, self.contentPage, self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.skeletonScreen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
