# 第三方库导入
from PySide6.QtGui import QCursor, QScreen
from PySide6.QtCore import QRect, QPoint
from PySide6.QtWidgets import QApplication


def getCurrentScreen() -> QScreen | None:
    """获取当前屏幕"""
    # 获取鼠标位置
    cursorPos: QPoint = QCursor.pos()

    # 遍历所有屏幕
    screen: QScreen
    for screen in QApplication.screens():

        # 如果鼠标在屏幕内, 则返回该屏幕
        if screen.geometry().contains(cursorPos):
            return screen

    # 如果没有找到, 则返回None
    return None


def getCurrentScreenGeometry(avaliable: bool = True) -> QRect:
    """获取当前屏幕几何图形

    Parameters
    ----------
    avaliable : bool, optional
        是否返回可用几何图形, by default True
    """
    screen: QScreen = getCurrentScreen() or QApplication.primaryScreen()

    # 理论上不会出现没有屏幕的情况
    if not screen:
        return QRect(0, 0, 1920, 1080)

    return screen.availableGeometry() if avaliable else screen.geometry()
