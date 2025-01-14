# coding:utf-8

# 标准库导入
from copy import deepcopy
from typing import List, Tuple

# 第三方库导入
from PySide6.QtCore import QPoint, Signal, QEasingCurve, QAbstractAnimation, QPropertyAnimation, QParallelAnimationGroup
from PySide6.QtWidgets import QWidget, QStackedWidget, QGraphicsOpacityEffect


class OpacityAniStackedWidget(QStackedWidget):
    """Stacked widget with fade in and fade out animation"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__nextIndex = 0
        self.__effects = []  # type:List[QPropertyAnimation]
        self.__anis = []  # type:List[QPropertyAnimation]

    def addWidget(self, w: QWidget):
        super().addWidget(w)

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        ani = QPropertyAnimation(effect, b"opacity", self)
        ani.setDuration(220)
        ani.finished.connect(self.__onAniFinished)
        self.__anis.append(ani)
        self.__effects.append(effect)
        w.setGraphicsEffect(effect)

    def setCurrentIndex(self, index: int):
        index_ = self.currentIndex()
        if index == index_:
            return

        if index > index_:
            ani = self.__anis[index]
            ani.setStartValue(0)
            ani.setEndValue(1)
            super().setCurrentIndex(index)
        else:
            ani = self.__anis[index_]
            ani.setStartValue(1)
            ani.setEndValue(0)

        self.widget(index_).show()
        self.__nextIndex = index
        ani.start()

    def setCurrentWidget(self, w: QWidget):
        self.setCurrentIndex(self.indexOf(w))

    def __onAniFinished(self):
        super().setCurrentIndex(self.__nextIndex)


class PopUpAniStackedWidget(QStackedWidget):
    """
    带有弹出动画效果的堆叠窗口部件

    Attributes
    ----------
    aniFinished : Signal
        动画完成时发出的信号

    aniStart : Signal
        动画开始时发出的信号

    _ani : QPropertyAnimation
        当前正在执行的动画对象
    """

    aniFinished = Signal()
    aniStart = Signal()

    def __init__(self, parent=None) -> None:
        """
        初始化弹出动画堆叠窗口

        Parameters
        ----------
        parent : QWidget, optional
            父窗口, 默认为 None
        """
        super().__init__(parent)
        self._aniInfos: List[Tuple[QPropertyAnimation,]] = []
        self._nextIndex: int = 0
        self._ani: QParallelAnimationGroup | QPropertyAnimation | None = None
        self._deltaX: int = 0
        self._deltaY: int = 64

    def addWidget(self, widget: QWidget) -> None:
        """
        添加一个新的子窗口, 并设置其动画属性

        Parameters
        ----------
        widget : QWidget
            要添加的窗口部件

        deltaX : int, optional
            动画过程中 x 轴方向的位移量, 默认为 0

        deltaY : int, optional
            动画过程中 y 轴方向的位移量, 默认为 64
        """
        super().addWidget(widget)

        # 添加透明度效果
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        widget.setGraphicsEffect(effect)

        # 添加动画
        self._aniInfos.append(
            (QPropertyAnimation(widget, b"pos", widget), QPropertyAnimation(effect, b"opacity", widget))
        )

    def removeWidget(self, widget: QWidget) -> None:
        """
        移除指定的子窗口及其对应的动画信息

        Parameters
        ----------
        widget : QWidget
            要移除的窗口部件
        """
        index = self.indexOf(widget)
        if index == -1:
            return

        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setCurrentIndex(
        self, index: int, duration: int = 500, easingCurve: QEasingCurve = QEasingCurve.Type.OutQuad
    ) -> None:
        """
        设置当前显示的窗口索引, 并执行相应的动画

        Parameters
        ----------
        index : int
            要显示的窗口索引

        duration : int, optional
            动画持续时间（毫秒）, 默认为 250

        easingCurve : QEasingCurve, optional
            动画的插值模式, 默认为 QEasingCurve.OutQuad

        Raises
        ------
        Exception
            如果提供的索引非法
        """
        if index < 0 or index >= self.count():
            raise Exception(f"The index `{index}` is illegal")

        if index == self.currentIndex():
            return

        if self._ani and self._ani.state() == QAbstractAnimation.State.Running:
            self._ani.stop()
            self._ani.finished.disconnect()

        # 保存下一个索引
        self._nextIndex = index

        # 执行当前页面的退出动画
        exit_ani = self.__exitAni()
        self._ani = exit_ani
        exit_ani.finished.connect(self.__onExitAniFinished)
        exit_ani.start()

    def setCurrentWidget(
        self, widget: QWidget, duration: int = 500, easingCurve: QEasingCurve = QEasingCurve.OutQuad
    ) -> None:
        """
        设置当前显示的窗口部件, 并执行动画

        Parameters
        ----------
        widget : QWidget
            要显示的窗口部件

        duration : int, optional
            动画持续时间（毫秒）, 默认为 250

        easingCurve : QEasingCurve, optional
            动画的插值模式, 默认为 QEasingCurve.OutQuad
        """
        self.setCurrentIndex(self.indexOf(widget), duration, easingCurve)

    def __onExitAniFinished(self) -> None:
        """页面退出动画结束时的槽函数"""
        # 断开信号连接
        self._ani.finished.disconnect()

        # 设置下一个页面的位置
        super().setCurrentIndex(self._nextIndex)
        enter_ani = self.__enterAni(self._deltaX, self._deltaY)
        self._ani = enter_ani
        enter_ani.finished.connect(lambda: (self._ani.finished.disconnect(), self.aniFinished.emit()))
        enter_ani.start()

    def __exitAni(self) -> QPropertyAnimation:
        """页面退出动画"""
        ani: QPropertyAnimation = self._aniInfos[self.currentIndex()][1]
        ani.setStartValue(1)
        ani.setEndValue(0)
        ani.setDuration((int(300 / 2)))
        ani.setEasingCurve(QEasingCurve.Type.Linear)

        return ani

    def __enterAni(self, deltaX: int, deltaY: int) -> QParallelAnimationGroup:
        """页面进入动画"""
        # 创建动画组和位置动画以及透明度动画
        aniGroup = QParallelAnimationGroup(self)
        pos_ani: QPropertyAnimation = self._aniInfos[self._nextIndex][0]
        opacity_ani: QPropertyAnimation = self._aniInfos[self._nextIndex][1]

        # 设置位置动画
        pos_ani.setStartValue(self.widget(self._nextIndex).pos() + QPoint(deltaX, deltaY))
        pos_ani.setEndValue(self.widget(self._nextIndex).pos())
        pos_ani.setDuration(300)
        pos_ani.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 设置透明度动画
        opacity_ani.setStartValue(0)
        opacity_ani.setEndValue(1)
        opacity_ani.setDuration(int(300 / 2))
        opacity_ani.setEasingCurve(QEasingCurve.Type.Linear)

        # 添加动画到动画组
        aniGroup.addAnimation(pos_ani)
        aniGroup.addAnimation(opacity_ani)

        return aniGroup
