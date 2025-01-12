# coding: utf-8
# 第三方库导入
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget


def setFont(widget: QWidget, fontSize: int = 14, weight: QFont.Weight = QFont.Weight.Normal) -> None:
    """set the font of widget

    Parameters
    ----------
    widget: QWidget
        用于设置字体的小部件

    fontSize: int
        字体像素大小

    weight: `QFont.Weight`
        字体粗细
    """
    widget.setFont(getFont(fontSize, weight))


def getFont(fontSize: int = 14, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """创建字体

    Parameters
    ----------
    fontSize: int
        字体像素大小

    weight: `QFont.Weight`
        字体粗细
    """
    font = QFont()
    font.setFamilies(["Segoe UI", "Microsoft YaHei", "PingFang SC"])
    font.setPixelSize(fontSize)
    font.setWeight(weight)
    return font
