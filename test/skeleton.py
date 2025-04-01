# 标准库导入
import math

# 第三方库导入
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient
from PySide6.QtCore import Qt, QRectF, QPointF, Property, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


class SkeletonElement(QWidget):
    """单个骨架元素基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation_progress = 0.0  # 动画进度 0.0~1.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def get_animation_progress(self):
        return self._animation_progress

    def set_animation_progress(self, value):
        self._animation_progress = value
        self.update()

    animation_progress = Property(float, get_animation_progress, set_animation_progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 绘制基础骨架
        self.draw_base(painter)

        # 2. 绘制高光效果
        if 0 <= self._animation_progress <= 1:
            self.draw_shimmer(painter)

    def draw_base(self, painter):
        """由子类实现具体骨架形状"""
        raise NotImplementedError

    def draw_shimmer(self, painter):
        """由子类实现高光效果"""
        raise NotImplementedError


class RectSkeleton(SkeletonElement):
    """矩形骨架元素"""

    def __init__(self, radius=4, parent=None):
        super().__init__(parent)
        self.radius = radius
        self.base_color = QColor(240, 240, 240)
        self.highlight_color = QColor(255, 255, 255)

    def draw_base(self, painter):
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), self.radius, self.radius)
        painter.fillPath(path, self.base_color)

    def draw_shimmer(self, painter):
        # 计算高光位置（从左到右移动）
        shimmer_pos = self._animation_progress * (self.width() + 200) - 100

        # 只在可见区域绘制
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), self.radius, self.radius)
        painter.setClipPath(clip_path)

        # 创建渐变
        gradient = QLinearGradient(QPointF(shimmer_pos - 50, 0), QPointF(shimmer_pos + 50, 0))
        gradient.setColorAt(0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.4, self.highlight_color)
        gradient.setColorAt(0.6, self.highlight_color)
        gradient.setColorAt(1, QColor(255, 255, 255, 0))

        # 绘制高光矩形（比实际元素高一些）
        shimmer_rect = QRectF(shimmer_pos - 50, -10, 100, self.height() + 20)
        painter.fillRect(shimmer_rect, gradient)


class CircleSkeleton(SkeletonElement):
    """圆形骨架元素"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_color = QColor(240, 240, 240)
        self.highlight_color = QColor(255, 255, 255)

    def draw_base(self, painter):
        diameter = min(self.width(), self.height())
        path = QPainterPath()
        path.addEllipse(0, 0, diameter, diameter)
        painter.fillPath(path, self.base_color)

    def draw_shimmer(self, painter):
        diameter = min(self.width(), self.height())
        shimmer_pos = self._animation_progress * (diameter + 100) - 50

        clip_path = QPainterPath()
        clip_path.addEllipse(0, 0, diameter, diameter)
        painter.setClipPath(clip_path)

        gradient = QLinearGradient(QPointF(shimmer_pos - 30, 0), QPointF(shimmer_pos + 30, 0))
        gradient.setColorAt(0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, self.highlight_color)
        gradient.setColorAt(1, QColor(255, 255, 255, 0))

        shimmer_rect = QRectF(shimmer_pos - 30, -10, 60, diameter + 20)
        painter.fillRect(shimmer_rect, gradient)


class SkeletonContainer(QWidget):
    """骨架屏容器，管理动画和布局"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("background: white;")

        # 创建布局和骨架元素
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 顶部头像区域
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        self.avatar = CircleSkeleton()
        self.avatar.setFixedSize(60, 60)
        top_layout.addWidget(self.avatar)

        # 右侧文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        self.line1 = RectSkeleton()
        self.line1.setFixedHeight(16)
        self.line2 = RectSkeleton()
        self.line2.setFixedHeight(12)
        self.line3 = RectSkeleton()
        self.line3.setFixedHeight(12)
        text_layout.addWidget(self.line1)
        text_layout.addWidget(self.line2)
        text_layout.addWidget(self.line3)
        top_layout.addLayout(text_layout)

        layout.addLayout(top_layout)

        # 内容卡片
        self.card1 = RectSkeleton(radius=8)
        self.card1.setFixedHeight(120)
        layout.addWidget(self.card1)

        self.card2 = RectSkeleton(radius=8)
        self.card2.setFixedHeight(80)
        layout.addWidget(self.card2)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        self.btn1 = RectSkeleton(radius=20)
        self.btn1.setFixedSize(100, 40)
        self.btn2 = RectSkeleton(radius=20)
        self.btn2.setFixedSize(100, 40)
        bottom_layout.addWidget(self.btn1)
        bottom_layout.addWidget(self.btn2)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

        # 创建动画
        self.animation = QPropertyAnimation(self, b"animation_progress")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.setLoopCount(-1)  # 无限循环
        self.animation.start()

    def get_animation_progress(self):
        return self.avatar.animation_progress  # 任意子元素的值

    def set_animation_progress(self, value):
        # 同步更新所有子元素的动画进度
        for child in self.findChildren(SkeletonElement):
            child.set_animation_progress(value)

    animation_progress = Property(float, get_animation_progress, set_animation_progress)


# 使用示例
if __name__ == "__main__":
    # 标准库导入
    import sys

    # 第三方库导入
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    skeleton = SkeletonContainer()
    skeleton.resize(400, 500)
    skeleton.show()

    sys.exit(app.exec())
