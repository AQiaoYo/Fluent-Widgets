# 标准库导入
import math

# 第三方库导入
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPainterPath, QResizeEvent, QLinearGradient
from PySide6.QtCore import Qt, QEvent, QRectF, Signal, QPointF, Property, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout

from ...common.overload import singledispatchmethod
from ...components.widgets.stacked_widget import FadeEffectAniStackedWidget


class ShimmerWidget(QWidget):
    """高光效果控件"""

    def __init__(self, parent):
        super().__init__(parent)
        # 初始位置
        self._shimmer_pos = None

    def get_shimmer_pos(self):
        return self._shimmer_pos

    def set_shimmer_pos(self, pos: float):
        self._shimmer_pos = pos
        self.update()

    # 通过属性系统实现动画效果
    shimmer_pos = Property(float, get_shimmer_pos, set_shimmer_pos)

    def paintEvent(self, _) -> None:
        """绘制高光效果"""

        if not self.isVisible() or not self.parent():
            return

        # 如果初始位置未设置，根据父控件大小设置
        if self._shimmer_pos is None:
            self._shimmer_pos = -self.parent().width() * 2

        painter = QPainter(self)

        # 检查 painter 是否激活
        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.save()
        painter.translate(QPointF(self.width() / 2, self.height() / 2))
        painter.rotate(7)
        painter.setOpacity(0.9)

        # 高光宽度
        shimmer_width = self.parent().width() * 0.3

        # 让渐变的中心点跟随动画位置
        gradient_center = self._shimmer_pos
        gradient = QLinearGradient(
            QPointF(gradient_center - shimmer_width, 0), QPointF(gradient_center + shimmer_width, 0)
        )

        # 设置渐变颜色
        gradient.setColorAt(0.00, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.20, QColor(255, 255, 255, 20))
        gradient.setColorAt(0.35, QColor(255, 255, 255, 60))
        gradient.setColorAt(0.45, QColor(255, 255, 255, 100))
        gradient.setColorAt(0.50, QColor(255, 255, 255, 120))
        gradient.setColorAt(0.55, QColor(255, 255, 255, 90))
        gradient.setColorAt(0.65, QColor(255, 255, 255, 60))
        gradient.setColorAt(0.80, QColor(255, 255, 255, 20))
        gradient.setColorAt(1.00, QColor(255, 255, 255, 0))

        # 绘制高光矩形（要足够长以包含移动的高光）
        shimmer_rect = QRectF(
            self._shimmer_pos - shimmer_width,  # 左边界
            -self.height() * 2,  # 上边界
            shimmer_width * 2,  # 宽度（两边）
            self.height() * 6,  # 高度
        )
        painter.fillRect(shimmer_rect, gradient)
        painter.restore()


class SkeletonWidget(QWidget):
    """骨架屏基类，提供闪烁高光效果"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_skeletonWidget()
        self.installEventFilter(self)

    def _setup_skeletonWidget(self) -> None:
        """设置高光动画效果"""
        # 创建高光控件
        self.shimmer = ShimmerWidget(self)
        self.shimmer.resize(self.size())
        self.shimmer.raise_()

        # 计算对角线长度作为动画范围
        diagonal_length = math.sqrt(self.width() ** 2 + self.height() ** 2)
        extended_length = diagonal_length * 4
        print(extended_length)

        # 创建动画
        self.animation = QPropertyAnimation(self.shimmer, b"shimmer_pos")
        self.animation.setDuration(1000)
        self.animation.setStartValue(-extended_length)
        self.animation.setEndValue(extended_length)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.setLoopCount(-1)
        self.animation.start()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        # 重新设置高光控件大小
        if hasattr(self, "shimmer"):
            self.shimmer.resize(self.size())
            diagonal_length = math.sqrt(self.width() ** 2 + self.height() ** 2)
            self.animation.setEndValue(diagonal_length)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self.shimmer.resize(self.size())
            self.shimmer.raise_()
        elif event.type() == QEvent.ChildAdded:
            self.shimmer.raise_()
        return super().eventFilter(obj, event)


class SkeletonPlaceholder(QLabel):
    """骨架屏占位控件"""

    @singledispatchmethod
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor("#D2D1D5")
        self.setBorderRadius(0, 0, 0, 0)

    @__init__.register
    def _(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setBorderRadius(0, 0, 0, 0)

    @__init__.register
    def _(self, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor("#D2D1D5")
        self.setBorderRadius(topLeft, topRight, bottomRight, bottomLeft)

    @__init__.register
    def _(self, color: QColor, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int, parent=None) -> None:
        super().__init__(parent)
        self._color = color
        self.setBorderRadius(topLeft, topRight, bottomRight, bottomLeft)

    def setColor(self, color: QColor) -> None:
        self._color = color

    def getColor(self) -> QColor:
        return self._color

    def setBorderRadius(self, topLeft: int, topRight: int, bottomRight: int, bottomLeft: int) -> None:
        """设置圆角"""
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomRightRadius = bottomRight
        self._bottomLeftRadius = bottomLeft
        self.update()

    def scaledToWidth(self, width: int) -> None:
        """缩放到宽度"""
        self.setFixedSize(width, int(width / self.width() * self.height()))

    def scaledToHeight(self, height: int) -> None:
        """缩放到高度"""
        self.setFixedSize(int(height / self.height() * self.width()), height)

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制圆角矩形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)

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

        painter.drawPath(path)
        painter.end()

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

    skeletonLoadingStarted = Signal()
    skeletonLoadingFinished = Signal()

    def __init__(self, skeletonWidgets: SkeletonWidget, widget: QWidget, parent=None) -> None:
        super().__init__(parent=parent)
        # 骨架屏占位符组件以及加载完成后的组件
        self._skeletonWidgets = skeletonWidgets
        self._widget = widget

        # 添加到堆叠窗口
        self.addWidget(self._skeletonWidgets)
        self.addWidget(self._widget)

        # 链接信号
        self.skeletonLoadingStarted.connect(lambda: self.setCurrentIndex(0))
        self.skeletonLoadingFinished.connect(lambda: self.setCurrentIndex(1))

    def startSkeletonLoading(self) -> None:
        """开始加载"""
        self.skeletonLoadingStarted.emit()

    def finishSkeletonLoading(self) -> None:
        """结束加载"""
        self.skeletonLoadingFinished.emit()


class ArticleSkeleton(SkeletonScreen):
    """文章骨架屏"""

    def __init__(self, parent=None) -> None:

        # 创建骨架屏组件
        skeletonWidgets = SkeletonWidget()
        vBoxLayout = QVBoxLayout()
        hBoxLayout = QHBoxLayout()

        image_placeholder = SkeletonPlaceholder(4, 4, 4, 4)
        image_placeholder.scaledToWidth(144)

        title_placeholder_1 = SkeletonPlaceholder(4, 4, 4, 4)
        title_placeholder_1.setFixedSize(512, 24)
        subtitle_placeholder_1 = SkeletonPlaceholder(4, 4, 4, 4)
        subtitle_placeholder_1.setFixedSize(512, 24)

        title_placeholder_2 = SkeletonPlaceholder(4, 4, 4, 4)
        title_placeholder_2.setFixedSize(512, 24)
        subtitle_placeholder_2 = SkeletonPlaceholder(4, 4, 4, 4)
        subtitle_placeholder_2.setFixedSize(512, 24)

        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        vBoxLayout.addWidget(title_placeholder_1)
        vBoxLayout.addWidget(subtitle_placeholder_1)
        vBoxLayout.addSpacing(4)
        vBoxLayout.addWidget(title_placeholder_2)
        vBoxLayout.addWidget(subtitle_placeholder_2)

        hBoxLayout.setContentsMargins(16, 16, 16, 16)
        hBoxLayout.addWidget(image_placeholder)
        hBoxLayout.addLayout(vBoxLayout)

        skeletonWidgets.setLayout(hBoxLayout)

        widget = QWidget()

        super().__init__(skeletonWidgets, widget, parent=parent)
