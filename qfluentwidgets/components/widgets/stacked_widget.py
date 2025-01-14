# coding:utf-8

# 标准库导入
from typing import List

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


class PopUpAniInfo:
    """
    弹出动画信息类

    Parameters
    ----------
    widget : QWidget
        需要执行动画的部件

    deltaX : int
        动画过程中 x 轴方向的位移量

    deltaY : int
        动画过程中 y 轴方向的位移量

    ani : QPropertyAnimation
        控制部件位置的动画对象
    """

    def __init__(self, widget: QWidget, deltaX: int, deltaY: int, ani: QPropertyAnimation) -> None:
        self.widget = widget
        self.deltaX = deltaX
        self.deltaY = deltaY
        self.ani = ani


class PopUpAniStackedWidget(QStackedWidget):
    """
    带有弹出动画效果的堆叠窗口部件

    Attributes
    ----------
    aniFinished : Signal
        动画完成时发出的信号

    aniStart : Signal
        动画开始时发出的信号

    aniInfos : List[PopUpAniInfo]
        存储每个子窗口动画信息的列表

    _nextIndex : int
        即将显示的窗口索引

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
        self.aniInfos: List[PopUpAniInfo] = []
        self._nextIndex: int | None = None
        self._ani: QPropertyAnimation | None = None

    def addWidget(self, widget: QWidget, deltaX: int = 0, deltaY: int = 64) -> None:
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
        self.aniInfos.append(
            PopUpAniInfo(
                widget=widget,
                deltaX=deltaX,
                deltaY=deltaY,
                ani=QPropertyAnimation(widget, b"pos"),
            )
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
        self,
        index: int,
        needPopOut: bool = False,
        showNextWidgetDirectly: bool = True,
        duration: int = 250,
        easingCurve: QEasingCurve = QEasingCurve.Type.OutQuad,
    ) -> None:
        """
        设置当前显示的窗口索引, 并执行相应的动画

        Parameters
        ----------
        index : int
            要显示的窗口索引

        needPopOut : bool, optional
            是否需要执行弹出动画, 默认为 False

        showNextWidgetDirectly : bool, optional
            动画过程中是否直接显示下一个窗口, 默认为 True

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

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        # 保存下一个窗口索引
        self._nextIndex = index

        # 获取当前和下一个窗口的动画信息
        nextAniInfo = self.aniInfos[index]
        currentAniInfo = self.aniInfos[self.currentIndex()]

        # 获取当前和下一个窗口
        currentWidget = self.currentWidget()
        nextWidget = nextAniInfo.widget
        ani = currentAniInfo.ani if needPopOut else nextAniInfo.ani
        self._ani = ani

        if needPopOut:
            deltaX, deltaY = currentAniInfo.deltaX, currentAniInfo.deltaY
            pos = currentWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, currentWidget.pos(), pos, duration, easingCurve)
            nextWidget.setVisible(showNextWidgetDirectly)
        else:
            deltaX, deltaY = nextAniInfo.deltaX, nextAniInfo.deltaY
            pos = nextWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, pos, QPoint(nextWidget.x(), 0), duration, easingCurve)
            super().setCurrentIndex(index)

        ani.finished.connect(self.__onAniFinished)
        ani.start()
        self.aniStart.emit()

    def setCurrentWidget(
        self,
        widget: QWidget,
        needPopOut: bool = False,
        showNextWidgetDirectly: bool = True,
        duration: int = 250,
        easingCurve: QEasingCurve = QEasingCurve.OutQuad,
    ) -> None:
        """
        设置当前显示的窗口部件, 并执行动画

        Parameters
        ----------
        widget : QWidget
            要显示的窗口部件

        needPopOut : bool, optional
            是否需要执行弹出动画, 默认为 False

        showNextWidgetDirectly : bool, optional
            动画过程中是否直接显示下一个窗口, 默认为 True

        duration : int, optional
            动画持续时间（毫秒）, 默认为 250

        easingCurve : QEasingCurve, optional
            动画的插值模式, 默认为 QEasingCurve.OutQuad
        """
        self.setCurrentIndex(self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __setAnimation(
        self,
        ani: QPropertyAnimation,
        startValue: QPoint,
        endValue: QPoint,
        duration: int,
        easingCurve: QEasingCurve = QEasingCurve.Linear,
    ) -> None:
        """
        配置动画属性

        Parameters
        ----------
        ani : QPropertyAnimation
            动画对象

        startValue : QPoint
            动画起始位置

        endValue : QPoint
            动画结束位置

        duration : int
            动画持续时间（毫秒）

        easingCurve : QEasingCurve, optional
            动画的插值模式, 默认为 QEasingCurve.Linear
        """
        ani.setEasingCurve(easingCurve)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)

    def __onAniFinished(self) -> None:
        """
        动画完成后的槽函数, 用于更新状态
        """
        self._ani.finished.disconnect()
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()
