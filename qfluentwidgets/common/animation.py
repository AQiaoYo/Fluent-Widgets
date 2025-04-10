# coding: utf-8
# 标准库导入
from enum import Enum
from typing import Self

# 第三方库导入
from PySide6.QtGui import QColor, QEnterEvent, QFocusEvent, QMouseEvent
from PySide6.QtCore import QEvent, QPoint, Signal, QObject, QPointF, Property, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QWidget, QLineEdit, QGraphicsDropShadowEffect

from .config import qconfig


class AnimationBase(QObject):
    """Animation 基类(动画基类)"""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        # 为父类添加事件过滤器
        parent.installEventFilter(self)

    def _onHover(self, event: QEnterEvent) -> None:
        """鼠标悬停事件"""
        pass

    def _onLeave(self, event: QEvent) -> None:
        """鼠标离开事件"""
        pass

    def _onPress(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        pass

    def _onRelease(self, event: QMouseEvent) -> None:
        """鼠标释放事件"""
        pass

    def eventFilter(self, obj, event: QEvent.Type) -> bool:
        if obj is self.parent():
            if event.type() == QEvent.Type.MouseButtonPress:
                self._onPress(event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._onRelease(event)
            elif event.type() == QEvent.Type.Enter:
                self._onHover(event)
            elif event.type() == QEvent.Type.Leave:
                self._onLeave(event)

        return super().eventFilter(obj, event)


class TranslateYAnimation(AnimationBase):
    """平滑 Y 轴动画"""

    # 信号
    valueChanged = Signal(int)

    def __init__(self, parent: QWidget, offset: float | int = 2) -> None:
        super().__init__(parent)
        self._y = 0
        self.maxOffset = offset
        self.ani = QPropertyAnimation(self, b"y", self)

    def getY(self) -> int | float:
        return self._y

    def setY(self, y: int | float) -> None:
        self._y = y
        self.parent().update()
        self.valueChanged.emit(y)

    def _onPress(self, event: QMouseEvent) -> None:
        """向下运动"""
        self.ani.setEndValue(self.maxOffset)
        self.ani.setDuration(150)
        # 弹性动画
        self.ani.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.ani.start()

    def _onRelease(self, event: QMouseEvent) -> None:
        """向上回弹"""
        self.ani.setEndValue(0)
        self.ani.setDuration(500)
        # 弹性动画
        self.ani.setEasingCurve(QEasingCurve.Type.OutElastic)
        self.ani.start()

    # 定义属性 类型为 float 读取函数为 getY 写入函数为 setY
    y = Property(float, getY, setY)


class BackgroundAnimationWidget:
    """背景动画"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.isHover = False  # 是否悬停
        self.isPressed = False  # 是否按下

        # 背景颜色对象
        self.bgColorObject = BackgroundColorObject(self)

        # 背景颜色动画
        self.backgroundColorAni = QPropertyAnimation(self.bgColorObject, b"backgroundColor", self)
        self.backgroundColorAni.setDuration(120)

        # 为自身添加事件过滤器
        self.installEventFilter(self)

        # 主题改变时更新背景颜色
        qconfig.themeChanged.connect(self._updateBackgroundColor)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """事件过滤器"""

        # 根据事件类型更新背景颜色
        if obj is self and event.type() == QEvent.Type.EnabledChange:
            self.setBackgroundColor(
                self._normalBackgroundColor() if self.isEnabled() else self._disabledBackgroundColor()
            )

        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件(更新背景颜色)"""
        self.isPressed = True
        self._updateBackgroundColor()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件(更新背景颜色)"""
        self.isPressed = False
        self._updateBackgroundColor()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        """鼠标进入事件(更新背景颜色)"""
        self.isHover = True
        self._updateBackgroundColor()

    def leaveEvent(self, event: QEvent) -> None:
        """鼠标离开事件(更新背景颜色)"""
        self.isHover = False
        self._updateBackgroundColor()

    def focusInEvent(self, event: QFocusEvent) -> None:
        """焦点进入事件(更新背景颜色)"""
        super().focusInEvent(event)
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        """正常背景颜色"""
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self) -> QColor:
        """悬停背景颜色"""
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self) -> QColor:
        """按下背景颜色"""
        return self._normalBackgroundColor()

    def _focusInBackgroundColor(self) -> QColor:
        """焦点进入背景颜色"""
        return self._normalBackgroundColor()

    def _disabledBackgroundColor(self) -> QColor:
        """禁用背景颜色"""
        return self._normalBackgroundColor()

    def _updateBackgroundColor(self) -> None:
        """更新背景颜色"""

        # 根据状态设置背景颜色
        if not self.isEnabled():
            color = self._disabledBackgroundColor()
        elif isinstance(self, QLineEdit) and self.hasFocus():
            # 如果是 QLineEdit 并且有焦点
            color = self._focusInBackgroundColor()
        elif self.isPressed:
            color = self._pressedBackgroundColor()
        elif self.isHover:
            color = self._hoverBackgroundColor()
        else:
            color = self._normalBackgroundColor()

        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def getBackgroundColor(self) -> QColor:
        """获取背景颜色"""
        return self.bgColorObject.backgroundColor

    def setBackgroundColor(self, color: QColor) -> None:
        """设置背景颜色"""
        self.bgColorObject.backgroundColor = color

    @property
    def backgroundColor(self):
        """背景颜色"""
        return self.getBackgroundColor()


class BackgroundColorObject(QObject):
    """背景色对象"""

    def __init__(self, parent: BackgroundAnimationWidget):
        super().__init__(parent)
        self._backgroundColor = parent._normalBackgroundColor()

    @Property(QColor)
    def backgroundColor(self) -> QColor:
        """背景颜色"""
        return self._backgroundColor

    @backgroundColor.setter
    def backgroundColor(self, color: QColor) -> None:
        """设置背景颜色"""
        self._backgroundColor = color
        self.parent().update()


class DropShadowAnimation(QPropertyAnimation):
    """投影动画"""

    def __init__(
        self, parent: QWidget, normalColor: QColor = QColor(0, 0, 0, 0), hoverColor: QColor = QColor(0, 0, 0, 75)
    ):
        super().__init__(parent=parent)
        # 属性定义
        self.normalColor: QColor = normalColor
        self.hoverColor: QColor = hoverColor
        self.offset: QPoint = QPoint(0, 0)
        self.blurRadius: int = 38
        self.isHover: bool = False

        # 阴影效果
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setColor(self.normalColor)

        parent.installEventFilter(self)

    def setBlurRadius(self, radius: int) -> None:
        """设置模糊半径"""
        self.blurRadius = radius

    def setOffset(self, dx: int, dy: int) -> None:
        """设置偏移量"""
        self.offset = QPoint(dx, dy)

    def setNormalColor(self, color: QColor) -> None:
        """设置正常颜色"""
        self.normalColor = color

    def setHoverColor(self, color: QColor) -> None:
        """设置悬停颜色"""
        self.hoverColor = color

    def setColor(self, color: QColor) -> None:
        """设置颜色(未实现)"""
        pass

    def _createShadowEffect(self) -> QGraphicsDropShadowEffect:
        """创建阴影效果"""
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setOffset(self.offset)
        self.shadowEffect.setBlurRadius(self.blurRadius)
        self.shadowEffect.setColor(self.normalColor)

        # 设置动画属性
        self.setTargetObject(self.shadowEffect)
        self.setStartValue(self.shadowEffect.color())
        self.setPropertyName(b"color")
        self.setDuration(150)

        return self.shadowEffect

    def eventFilter(self, obj, event: QEvent) -> bool:
        """事件过滤器"""

        # 如果是父类并且启用
        if obj is self.parent() and self.parent().isEnabled():

            # 如果是鼠标进入事件
            if event.type() in [QEvent.Type.Enter]:
                self.isHover = True

                if self.state() != QPropertyAnimation.State.Running:
                    self.parent().setGraphicsEffect(self._createShadowEffect())

                self.setEndValue(self.hoverColor)
                self.start()

            # 如果是鼠标离开事件或者鼠标按下事件
            elif event.type() in [QEvent.Type.Leave, QEvent.Type.MouseButtonPress]:
                self.isHover = False
                if self.parent().graphicsEffect():
                    self.finished.connect(self._onAniFinished)
                    self.setEndValue(self.normalColor)
                    self.start()

        return super().eventFilter(obj, event)

    def _onAniFinished(self):
        """动画结束事件"""
        self.finished.disconnect()
        self.shadowEffect = None
        self.parent().setGraphicsEffect(None)


class FluentAnimationSpeed(Enum):
    """流畅的动画速度"""

    FAST = 0  # 快速
    MEDIUM = 1  # 均衡
    SLOW = 2  # 优雅


class FluentAnimationType(Enum):
    """Fluent 动画类型"""

    FAST_INVOKE = 0
    STRONG_INVOKE = 1
    FAST_DISMISS = 2
    SOFT_DISMISS = 3
    POINT_TO_POINT = 4
    FADE_IN_OUT = 5


class FluentAnimationProperty(Enum):
    """Fluent 动画属性"""

    POSITION = "position"
    SCALE = "scale"
    ANGLE = "angle"
    OPACITY = "opacity"


class FluentAnimationProperObject(QObject):
    """Fluent 动画属性对象"""

    objects = {}

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    def getValue(self) -> int:
        """获取值"""
        return 0

    def setValue(self) -> None:
        """设置值"""
        pass

    @classmethod
    def register(cls, name):
        """register menu animation manager

        Parameters
        ----------
        name: Any
            注册到管理器的名称, 该名称应该是唯一的
        """

        def wrapper(manager):
            if name not in cls.objects:
                cls.objects[name] = manager

            return manager

        return wrapper

    @classmethod
    def create(cls, propertyType: FluentAnimationProperty, parent=None) -> Self:
        """创建属性对象"""

        # 如果属性类型不在对象中则抛出异常
        if propertyType not in cls.objects:
            raise ValueError(f"`{propertyType}` has not been registered")

        # 创建对象
        return cls.objects[propertyType](parent)


@FluentAnimationProperObject.register(FluentAnimationProperty.POSITION)
class PositionObject(FluentAnimationProperObject):
    """位置对象"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._position = QPoint()

    def getValue(self) -> QPoint:
        return self._position

    def setValue(self, pos: QPoint) -> None:
        self._position = pos
        self.parent().update()

    position = Property(QPoint, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.SCALE)
class ScaleObject(FluentAnimationProperObject):
    """Scale object"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scale: float = 1

    def getValue(self) -> float:
        return self._scale

    def setValue(self, scale: float) -> None:
        self._scale = scale
        self.parent().update()

    scale = Property(float, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.ANGLE)
class AngleObject(FluentAnimationProperObject):
    """Angle object"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._angle = 0

    def getValue(self) -> float:
        return self._angle

    def setValue(self, angle: float) -> None:
        self._angle = angle
        self.parent().update()

    angle = Property(float, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.OPACITY)
class OpacityObject(FluentAnimationProperObject):
    """Opacity object"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._opacity = 0

    def getValue(self) -> float:
        return self._opacity

    def setValue(self, opacity: float) -> None:
        self._opacity = opacity
        self.parent().update()

    opacity = Property(float, getValue, setValue)


class FluentAnimation(QPropertyAnimation):
    """Fluent 动画库"""

    animations = {}

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setSpeed(FluentAnimationSpeed.FAST)
        self.setEasingCurve(self.curve())

    @classmethod
    def createBezierCurve(cls, x1: float, y1: float, x2: float, y2: float) -> QEasingCurve:
        """创建贝塞尔曲线"""
        curve = QEasingCurve(QEasingCurve.BezierSpline)
        curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))
        return curve

    @classmethod
    def curve(cls) -> QEasingCurve:
        """获取曲线"""
        return cls.createBezierCurve(0, 0, 1, 1)

    def setSpeed(self, speed: FluentAnimationSpeed) -> None:
        """设置动画速度"""
        self.setDuration(self.speedToDuration(speed))

    def speedToDuration(self, speed: FluentAnimationSpeed) -> int:
        """速度转换为持续时间"""
        return 100

    def startAnimation(self, endValue, startValue=None) -> None:
        """开始动画

        Parameters
        ----------
        endValue: Any
            结束值
        startValue: Any
            开始值
        """
        self.stop()

        if startValue is None:
            self.setStartValue(self.value())
        else:
            self.setStartValue(startValue)

        self.setEndValue(endValue)
        self.start()

    def value(self):
        """获取值"""
        return self.targetObject().getValue()

    def setValue(self, value):
        """设置值"""
        self.targetObject().setValue(value)

    @classmethod
    def register(cls, name):
        """register menu animation manager

        Parameters
        ----------
        name: Any
            注册到管理器的名称, 该名称应该是唯一的
        """

        def wrapper(manager):
            if name not in cls.animations:
                cls.animations[name] = manager

            return manager

        return wrapper

    @classmethod
    def create(
        cls,
        aniType: FluentAnimationType,
        propertyType: FluentAnimationProperty,
        speed=FluentAnimationSpeed.FAST,
        value=None,
        parent=None,
    ) -> Self:
        """创建动画

        Parameters
        ----------
        aniType: FluentAnimationType
            动画类型
        propertyType: FluentAnimationProperty
            动画属性
        speed: FluentAnimationSpeed
            动画速度
        value: Any
            动画值
        parent: Any
            父类对象

        Returns
        -------
        Self
            动画对象

        """

        # 如果动画类型不在动画中则抛出异常
        if aniType not in cls.animations:
            raise ValueError(f"`{aniType}` has not been registered.")

        # 创建属性对象
        obj = FluentAnimationProperObject.create(propertyType, parent)
        ani = cls.animations[aniType](parent)

        # 设置动画属性
        ani.setSpeed(speed)
        ani.setTargetObject(obj)
        ani.setPropertyName(propertyType.value.encode())

        if value is not None:
            ani.setValue(value)

        return ani


@FluentAnimation.register(FluentAnimationType.FAST_INVOKE)
class FastInvokeAnimation(FluentAnimation):
    """Fast invoke animation"""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0, 0, 0, 1)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        if speed == FluentAnimationSpeed.FAST:
            return 187
        if speed == FluentAnimationSpeed.MEDIUM:
            return 333

        return 500


@FluentAnimation.register(FluentAnimationType.STRONG_INVOKE)
class StrongInvokeAnimation(FluentAnimation):
    """Strong invoke animation"""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.13, 1.62, 0, 0.92)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 667


@FluentAnimation.register(FluentAnimationType.FAST_DISMISS)
class FastDismissAnimation(FastInvokeAnimation):
    """Fast dismiss animation"""


@FluentAnimation.register(FluentAnimationType.SOFT_DISMISS)
class SoftDismissAnimation(FluentAnimation):
    """Soft dismiss animation"""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(1, 0, 1, 1)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 167


@FluentAnimation.register(FluentAnimationType.POINT_TO_POINT)
class PointToPointAnimation(FastDismissAnimation):
    """Point to point animation"""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.55, 0.55, 0, 1)


@FluentAnimation.register(FluentAnimationType.FADE_IN_OUT)
class FadeInOutAnimation(FluentAnimation):
    """Fade in/out animation"""

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 83
