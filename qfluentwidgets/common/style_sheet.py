# coding:utf-8
# 标准库导入
import weakref
from enum import Enum
from string import Template
from typing import Any, Dict, List, Self

# 第三方库导入
from PySide6.QtGui import QColor
from PySide6.QtCore import QFile, QEvent, QObject, QDynamicPropertyChangeEvent
from PySide6.QtWidgets import QWidget

from .file import QFluentFile
from .config import Theme, qconfig, isDarkTheme


class StyleSheetBase:
    """样式表基类"""

    def path(self, theme: Theme = Theme.AUTO) -> str:
        """获取样式表的路径"""
        raise NotImplementedError

    def content(self, theme: Theme = Theme.AUTO) -> str:
        """获取样式表的内容"""
        return getStyleSheetFromFile(self.path(theme))

    def apply(self, widget: QWidget, theme: Theme = Theme.AUTO) -> None:
        """应用样式表于组件"""
        setStyleSheet(widget, self, theme)


class StyleSheetCompose(StyleSheetBase):
    """样式表组合"""

    def __init__(self, sources: List[StyleSheetBase]) -> None:
        super().__init__()
        self.sources = sources

    def content(self, theme: Theme = Theme.AUTO) -> str:
        """获取样式表的内容"""
        return "\n".join([i.content(theme) for i in self.sources])

    def add(self, source: StyleSheetBase) -> None:
        """添加样式表源"""
        if source is self or source in self.sources:
            # 如果是自身或者已经存在, 则不添加
            return

        # 添加样式表源
        self.sources.append(source)

    def remove(self, source: StyleSheetBase) -> None:
        """删除样式表源"""
        if source not in self.sources:
            # 如果不存在, 则不删除
            return

        # 删除样式表源
        self.sources.remove(source)


class StyleSheetManager(QObject):
    """样式管理器"""

    def __init__(self) -> None:
        # 创建弱引用字典
        self.widgets = weakref.WeakKeyDictionary()

    def register(self, source: str | StyleSheetBase, widget: QWidget, reset=True) -> None:
        """将组件注册到管理器

        Parameters
        ----------
        source: str | StyleSheetBase
            QSS 源，则可能是:
            * `str`: QSS 文件路径
            * `StyleSheetBase`: 样式表实例

        widget: QWidget
            用于设置样式表的组件

        reset: bool
            是否重置 QSS 源
        """
        if isinstance(source, str):
            # 如果是字符串, 则表示传入的是路径, 包装为 StyleSheetFile 实例
            source = StyleSheetFile(source)

        # 如果组件不属于管理器, 则注册组件
        if widget not in self.widgets:

            # 组件销毁时, 从管理器中注销
            widget.destroyed.connect(self.deregister)
            # 安装事件过滤器 (自定义样式表监视器)
            widget.installEventFilter(CustomStyleSheetWatcher(widget))
            # 安装事件过滤器 (更新样式表监视器)
            widget.installEventFilter(DirtyStyleSheetWatcher(widget))
            # 添加到管理器
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

        # 如果不重置, 则添加样式表源, 否则重置样式表源
        if not reset:
            self.source(widget).add(source)
        else:
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

    def deregister(self, widget: QWidget) -> None:
        """从 Manager 取消注册小组件"""
        if widget not in self.widgets:
            return

        # 移除组件
        self.widgets.pop(widget)

    def items(self) -> List[tuple]:
        """获取管理器中的所有项目"""
        return self.widgets.items()

    def source(self, widget: QWidget) -> StyleSheetCompose:
        """获取小组件的 QSS 源"""
        return self.widgets.get(widget, StyleSheetCompose([]))


# 创建样式表管理器
styleSheetManager = StyleSheetManager()


class QssTemplate(Template):
    """样式表模板"""

    delimiter = "--"


def applyThemeTemplate(qss: str) -> str:
    """将主题颜色与字体应用于样式表

    Parameters
    ----------
    qss: str
        要应用主题颜色的样式表字符串
        替换变量应 'ThemeColor' 的值, 前缀为 '--'，如 '--ThemeColorPrimary'
    """
    # 创建样式表模板
    template = QssTemplate(qss)
    # 获取主题颜色的映射
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    # 获取字体的映射
    mappings.update({f"FontFamily": qconfig.get(qconfig.fontFamily)})

    # 返回应用主题颜色后的样式表
    return template.safe_substitute(mappings)


class FluentStyleSheet(StyleSheetBase, Enum):
    """Fluent 样式表"""

    MENU = "menu"
    LABEL = "label"
    PIVOT = "pivot"
    BUTTON = "button"
    DIALOG = "dialog"
    SLIDER = "slider"
    INFO_BAR = "info_bar"
    SPIN_BOX = "spin_box"
    TAB_VIEW = "tab_view"
    TOOL_TIP = "tool_tip"
    CHECK_BOX = "check_box"
    COMBO_BOX = "combo_box"
    FLIP_VIEW = "flip_view"
    LINE_EDIT = "line_edit"
    LIST_VIEW = "list_view"
    TREE_VIEW = "tree_view"
    INFO_BADGE = "info_badge"
    PIPS_PAGER = "pips_pager"
    TABLE_VIEW = "table_view"
    CARD_WIDGET = "card_widget"
    TIME_PICKER = "time_picker"
    COLOR_DIALOG = "color_dialog"
    MEDIA_PLAYER = "media_player"
    SETTING_CARD = "setting_card"
    TEACHING_TIP = "teaching_tip"
    FLUENT_WINDOW = "fluent_window"
    SWITCH_BUTTON = "switch_button"
    MESSAGE_DIALOG = "message_dialog"
    STATE_TOOL_TIP = "state_tool_tip"
    CALENDAR_PICKER = "calendar_picker"
    FOLDER_LIST_DIALOG = "folder_list_dialog"
    SETTING_CARD_GROUP = "setting_card_group"
    EXPAND_SETTING_CARD = "expand_setting_card"
    NAVIGATION_INTERFACE = "navigation_interface"

    def path(self, theme: Theme = Theme.AUTO) -> str:
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/qfluentwidgets/qss/{theme.value.lower()}/{self.value}.qss"


class StyleSheetFile(StyleSheetBase):
    """样式表文件"""

    def __init__(self, path: str) -> None:
        super().__init__()
        self.filePath = path

    def path(self, theme: Theme = Theme.AUTO) -> str:
        return self.filePath


class CustomStyleSheet(StyleSheetBase):
    """自定义样式表"""

    # 自定义样式表键
    DARK_QSS_KEY = "darkCustomQss"
    LIGHT_QSS_KEY = "lightCustomQss"

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        # 创建弱引用
        self._widget = weakref.ref(widget)

    def path(self, theme: Theme = Theme.AUTO):
        """此方法意义不明"""
        return ""

    @property
    def widget(self):
        """获取组件"""
        return self._widget()

    def __eq__(self, other: object) -> bool:
        """判断是否相等"""
        if not isinstance(other, CustomStyleSheet):
            # 类型都不同则直接返回 False
            return False

        return other.widget is self.widget

    def setCustomStyleSheet(self, lightQss: str, darkQss: str) -> Self:
        """在浅色和深色主题模式下设置自定义样式表"""
        self.setLightStyleSheet(lightQss)
        self.setDarkStyleSheet(darkQss)
        return self

    def setLightStyleSheet(self, qss: str) -> Self:
        """将样式表设置为浅色模式"""
        if self.widget:
            self.widget.setProperty(self.LIGHT_QSS_KEY, qss)

        return self

    def setDarkStyleSheet(self, qss: str) -> Self:
        """将样式表设置为深色模式"""
        if self.widget:
            self.widget.setProperty(self.DARK_QSS_KEY, qss)

        return self

    def lightStyleSheet(self) -> str:
        """获取浅色模式下的样式表"""
        if not self.widget:
            return ""

        # 获取浅色模式下的样式表 如果没有则返回空字符串
        return self.widget.property(self.LIGHT_QSS_KEY) or ""

    def darkStyleSheet(self) -> str:
        """获取深色模式下的样式表"""
        if not self.widget:
            return ""

        # 获取深色模式下的样式表 如果没有则返回空字符串
        return self.widget.property(self.DARK_QSS_KEY) or ""

    def content(self, theme: Theme = Theme.AUTO) -> str:
        """获取样式表的内容"""
        # 判断主题模式
        theme = qconfig.theme if theme == Theme.AUTO else theme

        # 根据主题模式返回对应的样式表
        if theme == Theme.LIGHT:
            return self.lightStyleSheet()

        return self.darkStyleSheet()


class CustomStyleSheetWatcher(QObject):
    """自定义样式表监视器"""

    def eventFilter(self, obj: QWidget, e: QEvent) -> bool:
        """样式表动态类型变更事件过滤器"""
        if e.type() != QEvent.DynamicPropertyChange:
            # 如果事件类型不是动态属性更改, 则返回
            return super().eventFilter(obj, e)

        # 获取属性名称
        name = QDynamicPropertyChangeEvent(e).propertyName().data().decode()

        # 如果属性名称是自定义样式表键, 则添加样式表
        if name in [CustomStyleSheet.LIGHT_QSS_KEY, CustomStyleSheet.DARK_QSS_KEY]:
            addStyleSheet(obj, CustomStyleSheet(obj))

        return super().eventFilter(obj, e)


class DirtyStyleSheetWatcher(QObject):
    """更新样式表观察器"""

    def eventFilter(self, obj: QWidget, e: QEvent) -> bool:
        """事件过滤器"""

        # 如果事件类型不是绘制事件或者没有设置 dirty-qss 属性, 则返回
        if e.type() != QEvent.Type.Paint or not obj.property("dirty-qss"):
            return super().eventFilter(obj, e)

        # 设置 dirty-qss 属性为 False
        obj.setProperty("dirty-qss", False)

        # 如果组件在管理器中, 则更新样式表
        if obj in styleSheetManager.widgets:
            obj.setStyleSheet(getStyleSheet(styleSheetManager.source(obj)))

        return super().eventFilter(obj, e)


def getStyleSheetFromFile(file: str | QFile) -> str:
    """从 QSS 文件获取样式表"""
    with QFluentFile(file, QFile.ReadOnly) as file:
        return str(file.readAll(), encoding="utf-8")


def getStyleSheet(source: str | StyleSheetBase, theme: Theme = Theme.AUTO) -> str:
    """获取样式表

    Parameters
    ----------
    source: str | StyleSheetBase
        QSS 源，可能是:
          * `str`: QSS 文件路径
          * `StyleSheetBase`: 样式表实例

    theme: Theme
        样式表的主题
    """
    if isinstance(source, str):
        # 如果是字符串, 则表示传入的是路径, 包装为 StyleSheetFile 实例
        source = StyleSheetFile(source)

    # 获取样式表内容
    return applyThemeTemplate(source.content(theme))


def setStyleSheet(
    widget: QWidget, source: str | StyleSheetBase, theme: Theme = Theme.AUTO, register: bool = True
) -> None:
    """设置 Widget 的样式表

    Parameters
    ----------
    widget: QWidget
        用于设置样式表的组件

    source: str | StyleSheetBase
        QSS 源，可能是:
          * `str`: QSS 文件路径
          * `StyleSheetBase`: 样式表实例

    theme: Theme
        样式表的主题

    register: bool
        是否将微件注册到样式管理器。如果 'register=True'，则当主题更改时，组件将自动更新
    """
    if register:
        styleSheetManager.register(source, widget)

    widget.setStyleSheet(getStyleSheet(source, theme))


def setCustomStyleSheet(widget: QWidget, lightQss: str, darkQss: str) -> None:
    """设置自定义样式表

    Parameters
    ----------
    widget: QWidget
        用于设置样式表的组件

    lightQss: str
        浅色主题模式中使用的样式表

    darkQss: str
        浅色主题模式中使用的样式表
    """
    CustomStyleSheet(widget).setCustomStyleSheet(lightQss, darkQss)


def addStyleSheet(
    widget: QWidget, source: str | StyleSheetBase, theme: Theme = Theme.AUTO, register: bool = True
) -> None:
    """将样式表添加到组件

    Parameters
    ----------
    widget: QWidget
        用于设置样式表的组件

    source: str | StyleSheetBase
        QSS 源，可能是:
          * `str`: QSS 文件路径
          * `StyleSheetBase`: 样式表实例

    theme: Theme
        样式表的主题

    register: bool
        是否将微件注册到样式管理器。如果 'register=True'，则当主题更改时，组件将自动更新
    """
    if register:
        styleSheetManager.register(source, widget, reset=False)
        qss = getStyleSheet(styleSheetManager.source(widget), theme)
    else:
        qss = widget.styleSheet() + "\n" + getStyleSheet(source, theme)

    if qss.rstrip() != widget.styleSheet().rstrip():
        widget.setStyleSheet(qss)


def updateStyleSheet(lazy: bool = False) -> None:
    """更新所有 Fluent 小部件的样式表

    Parameters
    ----------
    lazy: bool
        是否懒更新样式表，设置为 True' 会加速主题切换
    """
    removes = []

    # 遍历样式表管理器中的所有项
    for widget, file in styleSheetManager.items():
        try:
            # 如果不是懒更新或者组件可见，则设置样式表
            if not (lazy and widget.visibleRegion().isNull()):
                setStyleSheet(widget, file, qconfig.theme)

            # 如果组件不可见，则设置 dirty-qss 属性为 True
            else:
                styleSheetManager.register(file, widget)
                widget.setProperty("dirty-qss", True)
        except RuntimeError:

            # 如果运行时错误，则添加到移除列表
            removes.append(widget)

    # 移除所有移除列表中的组件
    for widget in removes:
        styleSheetManager.deregister(widget)


def setTheme(theme: Theme, save: bool = False, lazy: bool = False) -> None:
    """设置应用程序主题

    Parameters
    ----------
    theme: Theme
        主题模式

    save: bool
        是否保存对配置文件的更改

    lazy: bool
        是否懒惰更新样式表，设置为 True' 会加速主题切换
    """
    qconfig.set(qconfig.themeMode, theme, save)
    updateStyleSheet(lazy)
    qconfig.themeChangedFinished.emit()


def toggleTheme(save: bool = False, lazy: bool = False) -> None:
    """切换应用程序主题

    Parameters
    ----------
    save: bool
        是否保存对配置文件的更改

    lazy: bool
        是否懒惰更新样式表，设置为 True' 会加速主题切换
    """
    theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
    setTheme(theme, save, lazy)


class ThemeColor(Enum):
    """主题颜色类型"""

    PRIMARY = "ThemeColorPrimary"
    DARK_1 = "ThemeColorDark1"
    DARK_2 = "ThemeColorDark2"
    DARK_3 = "ThemeColorDark3"
    LIGHT_1 = "ThemeColorLight1"
    LIGHT_2 = "ThemeColorLight2"
    LIGHT_3 = "ThemeColorLight3"

    def name(self):
        """获取主题颜色名称"""
        return self.color().name()

    def color(self) -> QColor:
        """根据当前主题和类型返回调整后的颜色

        - 原逻辑：
        1. 通过 if-elif 的多层判断结构，根据 self 的值调整饱和度 (saturation) 和亮度 (value)
        2. 暗色主题和亮色主题分别有独立的判断逻辑

        - 新逻辑：
        1. 使用字典存储调整参数，将条件判断的逻辑改为查表结构
        2. 提高代码可读性和维护性，同时减少重复代码
        """

        # 获取主题颜色
        base_color: QColor = qconfig.get(qconfig._cfg.themeColor)

        # 获取 HSV 分量
        hue: float  # 色相
        saturation: float  # 饱和度
        value: float  # 亮度
        hue, saturation, value, _ = base_color.getHsvF()

        # 根据主题设置颜色调整参数
        adjustments: Dict[ThemeColor, Dict[str, Any]]
        if isDarkTheme():
            adjustments = {
                self.DARK_1: {"saturation": 0.84, "value": 0.9},
                self.DARK_2: {"saturation": 0.82 * 0.977, "value": 0.82},
                self.DARK_3: {"saturation": 0.84 * 0.95, "value": 0.7},
                self.LIGHT_1: {"saturation": 0.84 * 0.92},
                self.LIGHT_2: {"saturation": 0.84 * 0.78},
                self.LIGHT_3: {"saturation": 0.84 * 0.65},
            }
        else:
            adjustments = {
                self.DARK_1: {"value": 0.75},
                self.DARK_2: {"saturation": 1.05, "value": 0.5},
                self.DARK_3: {"saturation": 1.1, "value": 0.4},
                self.LIGHT_1: {"value": 1.05},
                self.LIGHT_2: {"saturation": 0.75, "value": 1.05},
                self.LIGHT_3: {"saturation": 0.65, "value": 1.05},
            }

        # 获取当前主题颜色的调整参数
        adjustment: Dict[str, Any] = adjustments.get(self, {})

        # 应用调整
        adjusted_saturation: float = min(saturation * adjustment.get("saturation", 1), 1)
        adjusted_value: float = min(value * adjustment.get("value", 1), 1)

        # 返回调整后的颜色
        return QColor.fromHsvF(hue, adjusted_saturation, adjusted_value)


def themeColor():
    """获取主题颜色"""
    return ThemeColor.PRIMARY.color()


def setThemeColor(color, save=False, lazy=False):
    """设置主题颜色

    Parameters
    ----------
    color: QColor | Qt.GlobalColor | str
        主题颜色

    save: bool
        是否保存以更改为配置文件

    lazy: bool
        是否延迟更新样式表
    """
    color = QColor(color)
    qconfig.set(qconfig.themeColor, color, save=save)
    updateStyleSheet(lazy)
