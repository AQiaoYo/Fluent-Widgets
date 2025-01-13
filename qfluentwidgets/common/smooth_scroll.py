# coding:utf-8
# 标准库导入
from enum import Enum
from math import pi, cos
from collections import deque

# 第三方库导入
from PySide6.QtGui import QWheelEvent
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime
from PySide6.QtWidgets import QScrollArea, QApplication, QAbstractScrollArea


class SmoothMode(Enum):
    """平滑模式枚举"""

    NO_SMOOTH = 0  # 不平滑
    CONSTANT = 1  # 恒定速度
    LINEAR = 2  # 线性平滑
    QUADRATI = 3  # 二次平滑
    COSINE = 4  # 余弦平滑


class SmoothScroll:
    """平滑滚动类, 实现平滑滚动效果"""

    def __init__(self, widget: QScrollArea, orient: Qt.Orientation = Qt.Vertical):
        """
        初始化平滑滚动设置

        Parameters
        ----------
        widget: QScrollArea
            需要进行平滑滚动的滚动区域控件

        orient: Qt.Orientation, optional
            滚动方向, 默认为垂直方向 (Qt.Vertical)
        """
        self.widget = widget  # 滚动区域控件
        self.orient = orient  # 滚动方向
        self.fps: int = 60  # 帧率, 默认为每秒60帧
        self.duration: int = 400  # 滚动持续时间, 单位毫秒
        self.stepsTotal: int = 0  # 总步数
        self.stepRatio: float = 1.5  # 步长比
        self.acceleration: float = 1  # 加速度
        self.lastWheelEvent = None  # 上次的滚轮事件
        self.scrollStamps: deque = deque()  # 存储滚轮事件时间戳的队列
        self.stepsLeftQueue: deque = deque()  # 存储剩余步骤的队列
        self.smoothMoveTimer: QTimer = QTimer(widget)  # 平滑滚动定时器
        self.smoothMode: SmoothMode = SmoothMode(SmoothMode.LINEAR)  # 平滑滚动模式, 默认线性模式
        self.smoothMoveTimer.timeout.connect(self.__smoothMove)  # 定时器超时连接到平滑移动函数

    def setSmoothMode(self, smoothMode: SmoothMode) -> None:
        """设置平滑模式

        Parameters
        ----------
        smoothMode: SmoothMode
            要设置的平滑模式
        """
        self.smoothMode = smoothMode

    def wheelEvent(self, e: QWheelEvent) -> None:
        """处理滚轮事件并启动平滑滚动

        仅处理通过鼠标触发的滚轮事件

        Parameters
        ----------
        e: QWheelEvent
            滚轮事件对象
        """
        delta: int = e.angleDelta().y() if e.angleDelta().y() != 0 else e.angleDelta().x()

        # 如果不需要平滑滚动或者滚轮事件的delta值不是120的倍数, 直接调用默认的wheelEvent
        if self.smoothMode == SmoothMode.NO_SMOOTH or abs(delta) % 120 != 0:
            QAbstractScrollArea.wheelEvent(self.widget, e)
            return

        # 将当前时间戳加入队列
        now: int = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)

        # 清理超过500毫秒的旧时间戳
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        # 根据未处理的事件数量调整加速度比例
        accerationRatio: float = min(len(self.scrollStamps) / 15, 1)
        self.lastWheelPos = e.position()  # 获取滚轮当前位置
        self.lastWheelGlobalPos = e.globalPosition()  # 获取滚轮全局位置

        # 计算总步数
        self.stepsTotal = self.fps * self.duration / 1000

        # 根据每个事件的delta计算移动的距离
        delta *= self.stepRatio
        if self.acceleration > 0:
            delta += delta * self.acceleration * accerationRatio

        # 将计算得到的移动距离和步数加入队列
        self.stepsLeftQueue.append([delta, self.stepsTotal])

        # 启动平滑滚动定时器, 定时器的超时时间为每帧1000ms/fps
        self.smoothMoveTimer.start(int(1000 / self.fps))

    def __smoothMove(self) -> None:
        """定时器超时后执行平滑滚动

        平滑滚动在定时器每次超时时减少剩余的步骤数, 逐步处理所有事件
        """
        totalDelta: float = 0  # 记录累计的滚动距离

        # 计算所有未处理事件的滚动距离, 每次定时器超时时减少步骤
        for i in self.stepsLeftQueue:
            totalDelta += self.__subDelta(i[0], i[1])
            i[1] -= 1  # 减少剩余的步骤数

        # 如果事件已处理完毕, 将其从队列中移除
        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        # 根据滚动方向构建滚轮事件
        if self.orient == Qt.Vertical:
            pixelDelta = QPoint(round(totalDelta), 0)
            bar = self.widget.verticalScrollBar()  # 获取垂直滚动条
        else:
            pixelDelta = QPoint(0, round(totalDelta))
            bar = self.widget.horizontalScrollBar()  # 获取水平滚动条

        e = QWheelEvent(
            self.lastWheelPos,
            self.lastWheelGlobalPos,
            pixelDelta,
            QPoint(round(totalDelta), 0),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollBegin,
            False,
        )

        # 发送滚轮事件给滚动条
        QApplication.sendEvent(bar, e)

        # 如果队列为空, 停止定时器, 结束滚动
        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def __subDelta(self, delta: float, stepsLeft: int) -> float:
        """计算每个步骤的插值, 决定平滑滚动的方式

        根据不同的平滑模式计算每个步骤的滚动距离

        Parameters
        ----------
        delta: float
            事件的总滚动距离
        stepsLeft: int
            剩余的步骤数

        Returns
        -------
        float
            当前步骤的滚动距离
        """
        m: int = self.stepsTotal / 2  # 总步数的一半
        x: int = abs(self.stepsTotal - stepsLeft - m)  # 当前步骤与中点的距离

        res: float = 0  # 最终计算得到的滚动距离
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0  # 不平滑
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal  # 恒定速度
        elif self.smoothMode == SmoothMode.LINEAR:
            res = 2 * delta / self.stepsTotal * (m - x) / m  # 线性平滑
        elif self.smoothMode == SmoothMode.QUADRATI:
            res = 3 / 4 / m * (1 - x * x / m / m) * delta  # 二次平滑
        elif self.smoothMode == SmoothMode.COSINE:
            res = (cos(x * pi / m) + 1) / (2 * m) * delta  # 余弦平滑

        return res
