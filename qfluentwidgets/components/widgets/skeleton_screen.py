# -*- coding: utf-8 -*-
# 第三方库导入
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPainterPath
from PySide6.QtCore import Property
from PySide6.QtWidgets import QLabel, QWidget

from ...common.config import isDarkTheme
from ...common.overload import singledispatchmethod
from ...components.widgets.stacked_widget import FadeEffectAniStackedWidget


class SkeletonPlaceholder(QLabel):
    """骨架屏占位控件"""

    @singledispatchmethod
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._darkBackgroundColor = QColor("#3F3F3F")
        self._lightBackgroundColor = QColor("#D2D1D5")
        self.setBorderRadius(0, 0, 0, 0)
        self._postInit()

    @__init__.register
    def _(self, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int, parent=None) -> None:
        self.__init__(parent=parent)
        self.setBorderRadius(topLeft, topRight, bottomRight, bottomLeft)

    @__init__.register
    def _(self, dark: QColor, light: QColor, parent=None) -> None:
        self.__init__(parent=parent)
        self.darkBackgroundColor = dark
        self.lightBackgroundColor = light

    @__init__.register
    def _(
        self, dark: QColor, light: QColor, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int, parent=None
    ) -> None:
        self.__init__(dark=dark, light=light, parent=parent)
        self.setBorderRadius(topLeft, topRight, bottomRight, bottomLeft)
        self.darkBackgroundColor = dark
        self.lightBackgroundColor = light

    def _postInit(self) -> None:
        """初始化"""
        pass

    @Property(QColor)
    def darkBackgroundColor(self) -> QColor:
        return self._darkBackgroundColor

    @darkBackgroundColor.setter
    def darkBackgroundColor(self, color: QColor) -> None:
        self._darkBackgroundColor = color
        self.update()

    @Property(QColor)
    def lightBackgroundColor(self) -> QColor:
        return self._lightBackgroundColor

    @lightBackgroundColor.setter
    def lightBackgroundColor(self, color: QColor) -> None:
        self._lightBackgroundColor = color
        self.update()

    def setBorderRadius(self, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int) -> None:
        """设置圆角"""
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomRightRadius = bottomRight
        self._bottomLeftRadius = bottomLeft
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制圆角矩形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        path = self._getRoundedRectPath()
        painter.fillPath(path, self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor)
        painter.end()

    def _getRoundedRectPath(self) -> QPainterPath:
        """获取圆角矩形路径"""

        # 使用 QPainterPath 绘制四个角不同圆角的矩形
        path = QPainterPath()
        rect = self.rect()

        # 左上角
        path.moveTo(rect.left() + self._topLeftRadius, rect.top())
        # 上边
        path.lineTo(rect.right() - self._topRightRadius, rect.top())
        # 右上角
        path.arcTo(
            rect.right() - 2 * self._topRightRadius,
            rect.top(),
            2 * self._topRightRadius,
            2 * self._topRightRadius,
            90,
            -90,
        )
        # 右边
        path.lineTo(rect.right(), rect.bottom() - self._bottomRightRadius)
        # 右下角
        path.arcTo(
            rect.right() - 2 * self._bottomRightRadius,
            rect.bottom() - 2 * self._bottomRightRadius,
            2 * self._bottomRightRadius,
            2 * self._bottomRightRadius,
            0,
            -90,
        )
        # 下边
        path.lineTo(rect.left() + self._bottomLeftRadius, rect.bottom())
        # 左下角
        path.arcTo(
            rect.left(),
            rect.bottom() - 2 * self._bottomLeftRadius,
            2 * self._bottomLeftRadius,
            2 * self._bottomLeftRadius,
            270,
            -90,
        )
        # 左边
        path.lineTo(rect.left(), rect.top() + self._topLeftRadius)
        # 左上角
        path.arcTo(rect.left(), rect.top(), 2 * self._topLeftRadius, 2 * self._topLeftRadius, 180, -90)

        return path

    @Property(int)
    def topLeftRadius(self) -> int:
        return self._topLeftRadius

    @topLeftRadius.setter
    def topLeftRadius(self, radius: int) -> None:
        self.setBorderRadius(radius, self.topRightRadius, self.bottomLeftRadius, self.bottomRightRadius)

    @Property(int)
    def topRightRadius(self) -> int:
        return self._topRightRadius

    @topRightRadius.setter
    def topRightRadius(self, radius: int) -> None:
        self.setBorderRadius(self.topLeftRadius, radius, self.bottomLeftRadius, self.bottomRightRadius)

    @Property(int)
    def bottomLeftRadius(self) -> int:
        return self._bottomLeftRadius

    @bottomLeftRadius.setter
    def bottomLeftRadius(self, radius: int) -> None:
        self.setBorderRadius(self.topLeftRadius, self.topRightRadius, radius, self.bottomRightRadius)

    @Property(int)
    def bottomRightRadius(self) -> int:
        return self._bottomRightRadius

    @bottomRightRadius.setter
    def bottomRightRadius(self, radius: int) -> None:
        self.setBorderRadius(self.topLeftRadius, self.topRightRadius, self.bottomLeftRadius, radius)


class SkeletonScreen(FadeEffectAniStackedWidget):
    """骨架屏组件"""

    @singledispatchmethod
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        # 骨架屏占位符页面以及加载完成后的页面
        self._skeletonWidgets = None
        self._contentWidget = None

    @__init__.register
    def _(self, skeletonWidgets: QWidget, parent=None) -> None:
        self.__init__(parent=parent)
        self.setSkeletonWidget(skeletonWidgets)

    @__init__.register
    def _(self, contentWidget: QWidget, parent=None) -> None:
        self.__init__(parent=parent)
        self.setContentWidget(contentWidget)

    @__init__.register
    def _(self, skeletonWidgets: QWidget, contentWidget: QWidget, parent=None) -> None:
        self.__init__(parent=parent)
        self.setSkeletonWidget(skeletonWidgets)
        self.setContentWidget(contentWidget)

    def _postInit(self) -> None:
        """初始化"""
        pass

    def setSkeletonWidget(self, skeletonWidgets: QWidget) -> None:
        """设置骨架屏占位符组件"""

        if self._skeletonWidgets is None:
            # 当骨架屏占位符组件为 None 时, 直接添加
            self._skeletonWidgets = skeletonWidgets
            self.addWidget(self._skeletonWidgets)
        else:
            # 当骨架屏占位符组件不为 None 时, 先移除再添加
            self.removeWidget(self._skeletonWidgets)
            self._skeletonWidgets = skeletonWidgets
            self.addWidget(self._skeletonWidgets)

    def setContentWidget(self, contentWidget: QWidget) -> None:
        """设置加载完成后的组件"""

        if self._contentWidget is None:
            # 当加载完成后的组件为 None 时, 直接添加
            self._contentWidget = contentWidget
            self.addWidget(self._contentWidget)
        else:
            # 当加载完成后的组件不为 None 时, 先移除再添加
            self.removeWidget(self._contentWidget)
            self._contentWidget = contentWidget
            self.addWidget(self._contentWidget)

    def skeletonWidget(self) -> QWidget:
        """获取骨架屏占位符组件"""
        return self._skeletonWidgets

    def contentWidget(self) -> QWidget:
        """获取加载完成后的组件"""
        return self._contentWidget

    def startSkeletonLoading(self) -> None:
        """开始加载"""
        self.setCurrentWidget(self._skeletonWidgets)

    def finishSkeletonLoading(self) -> None:
        """结束加载"""
        self.setCurrentWidget(self._contentWidget)
