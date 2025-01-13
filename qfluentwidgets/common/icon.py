# coding:utf-8
# 标准库导入
from enum import Enum
from typing import List, Union, Optional

# 第三方库导入
from PySide6.QtGui import QIcon, QColor, QImage, QAction, QPixmap, QPainter, QIconEngine
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtXml import QDomDocument
from PySide6.QtCore import Qt, QFile, QRect, QSize, QRectF, QObject

from .file import QFluentFile
from .config import Theme, isDarkTheme
from .overload import singledispatchmethod


class FluentIconEngine(QIconEngine):
    """Fluent icon engine, 用于渲染 Fluent 图标"""

    def __init__(self, icon: Union[QIcon, "Icon", "FluentIconBase"], reverse: bool = False):
        """
        初始化 FluentIconEngine

        Parameters
        ----------
        icon : QIcon | Icon | FluentIconBase
            要绘制的图标
        reverse : bool, optional
            是否反转图标的主题, 默认为 False
        """
        super().__init__()
        self.icon = icon
        self.isThemeReversed = reverse

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State) -> None:
        """
        绘制图标

        Parameters
        ----------
        painter : QPainter
            用于绘制的画家对象
        rect : QRect
            绘制图标的区域
        mode : QIcon.Mode
            图标的绘制模式
        state : QIcon.State
            图标的状态（如选中或禁用）
        """
        painter.save()

        if mode == QIcon.Disabled:
            painter.setOpacity(0.5)
        elif mode == QIcon.Selected:
            painter.setOpacity(0.7)

        # 根据主题调整图标颜色
        icon = self.icon
        if not self.isThemeReversed:
            theme = Theme.AUTO
        else:
            theme = Theme.LIGHT if isDarkTheme() else Theme.DARK

        if isinstance(self.icon, Icon):
            icon = self.icon.fluentIcon.icon(theme)
        elif isinstance(self.icon, FluentIconBase):
            icon = self.icon.icon(theme)

        # 调整图标区域, 修正位置
        if rect.x() == 19:
            rect = rect.adjusted(-1, 0, 0, 0)

        icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, state)
        painter.restore()


class SvgIconEngine(QIconEngine):
    """Svg icon engine, 用于渲染 SVG 格式图标"""

    def __init__(self, svg: str):
        """
        初始化 SvgIconEngine

        Parameters
        ----------
        svg : str
            SVG 图标的路径或内容
        """
        super().__init__()
        self.svg = svg

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State) -> None:
        """
        绘制 SVG 图标

        Parameters
        ----------
        painter : QPainter
            用于绘制的画家对象
        rect : QRect
            绘制图标的区域
        mode : QIcon.Mode
            图标的绘制模式
        state : QIcon.State
            图标的状态（如选中或禁用）
        """
        drawSvgIcon(self.svg.encode(), painter, rect)

    def clone(self) -> QIconEngine:
        """
        克隆当前图标引擎

        Returns
        -------
        QIconEngine
            克隆的图标引擎
        """
        return SvgIconEngine(self.svg)

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        """
        获取图标的 QPixmap

        Parameters
        ----------
        size : QSize
            图标的大小
        mode : QIcon.Mode
            图标的绘制模式
        state : QIcon.State
            图标的状态（如选中或禁用）

        Returns
        -------
        QPixmap
            图标的 QPixmap 表示
        """
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        self.paint(painter, rect, mode, state)
        return pixmap


def getIconColor(theme: Theme = Theme.AUTO, reverse: bool = False) -> str:
    """根据主题获取图标颜色

    Parameters
    ----------
    theme : Theme, optional
        图标的主题, 默认为 Theme.AUTO
    reverse : bool, optional
        是否反转颜色, 默认为 False

    Returns
    -------
    str
        图标的颜色（黑色或白色）
    """
    if not reverse:
        lc, dc = "black", "white"
    else:
        lc, dc = "white", "black"

    if theme == Theme.AUTO:
        color = dc if isDarkTheme() else lc
    else:
        color = dc if theme == Theme.DARK else lc

    return color


def drawSvgIcon(icon: Union[str, bytes], painter: QPainter, rect: QRect) -> None:
    """绘制 SVG 图标

    Parameters
    ----------
    icon : str | bytes
        SVG 图标的路径或内容
    painter : QPainter
        用于绘制的画家对象
    rect : QRect
        绘制图标的区域
    """
    renderer = QSvgRenderer(icon)
    renderer.render(painter, QRectF(rect))


def writeSvg(iconPath: str, indexes: Optional[List[int]] = None, **attributes) -> str:
    """根据指定属性生成 SVG 图标代码

    Parameters
    ----------
    iconPath : str
        SVG 图标文件路径
    indexes : List[int], optional
        需要修改的路径索引, 默认为 None
    **attributes :
        要应用于路径的属性

    Returns
    -------
    str
        修改后的 SVG 图标代码
    """
    if not iconPath.lower().endswith(".svg"):
        return ""

    with QFluentFile(iconPath, QFile.OpenModeFlag.ReadOnly) as file:
        dom = QDomDocument()
        dom.setContent(file.readAll())

    # 修改每个路径的颜色
    pathNodes = dom.elementsByTagName("path")
    indexes = range(pathNodes.length()) if not indexes else indexes
    for i in indexes:
        element = pathNodes.at(i).toElement()

        for k, v in attributes.items():
            element.setAttribute(k, v)

    return dom.toString()


def drawIcon(
    icon: Union[str, QIcon, "FluentIconBase"],
    painter: QPainter,
    rect: QRect,
    state: QIcon.State = QIcon.Off,
    **attributes,
) -> None:
    """绘制图标

    Parameters
    ----------
    icon : str | QIcon | FluentIconBase
        要绘制的图标
    painter : QPainter
        用于绘制的画家对象
    rect : QRect
        绘制图标的区域
    state : QIcon.State, optional
        图标的状态, 默认为 QIcon.Off
    **attributes :
        图标的附加属性
    """
    if isinstance(icon, FluentIconBase):
        icon.render(painter, rect, **attributes)
    elif isinstance(icon, Icon):
        icon.fluentIcon.render(painter, rect, **attributes)
    else:
        icon = QIcon(icon)
        icon.paint(painter, QRectF(rect).toRect(), Qt.AlignCenter, state=state)


class FluentIconBase:
    """Fluent 图标基础类"""

    def path(self, theme: Theme = Theme.AUTO) -> str:
        """获取图标的路径

        Parameters
        ----------
        theme : Theme, optional
            图标的主题, 默认为 Theme.AUTO

        Returns
        -------
        str
            图标的文件路径
        """
        raise NotImplementedError

    def icon(self, theme: Theme = Theme.AUTO, color: Optional[QColor] = None) -> QIcon:
        """创建 Fluent 图标

        Parameters
        ----------
        theme : Theme, optional
            图标的主题, 默认为 Theme.AUTO
        color : QColor | Qt.GlobalColor | str, optional
            图标颜色, 只有 SVG 图标适用, 默认为 None

        Returns
        -------
        QIcon
            创建的 QIcon 图标
        """
        path = self.path(theme)

        if not (path.endswith(".svg") and color):
            return QIcon(self.path(theme))

        color = QColor(color).name()
        return QIcon(SvgIconEngine(writeSvg(path, fill=color)))

    def colored(self, lightColor: QColor, darkColor: QColor) -> "ColoredFluentIcon":
        """创建带颜色的 Fluent 图标

        Parameters
        ----------
        lightColor : QColor | Qt.GlobalColor | str
            图标在亮色模式下的颜色
        darkColor : QColor | Qt.GlobalColor | str
            图标在暗色模式下的颜色

        Returns
        -------
        ColoredFluentIcon
            创建的带颜色的 Fluent 图标
        """
        return ColoredFluentIcon(self, lightColor, darkColor)

    def qicon(self, reverse: bool = False) -> QIcon:
        """将 Fluent 图标转换为 QIcon

        Parameters
        ----------
        reverse : bool, optional
            是否反转图标主题, 默认为 False

        Returns
        -------
        QIcon
            转换后的 QIcon
        """
        return QIcon(FluentIconEngine(self, reverse))

    def render(
        self,
        painter: QPainter,
        rect: QRect,
        theme: Theme = Theme.AUTO,
        indexes: Optional[List[int]] = None,
        **attributes,
    ) -> None:
        """渲染 SVG 图标

        Parameters
        ----------
        painter : QPainter
            用于绘制的画家对象
        rect : QRect
            绘制图标的区域
        theme : Theme, optional
            图标的主题, 默认为 Theme.AUTO
        indexes : List[int], optional
            需要修改的路径索引, 默认为 None
        **attributes :
            图标路径的修改属性
        """
        icon = self.path(theme)

        if icon.endswith(".svg"):
            if attributes:
                icon = writeSvg(icon, indexes, **attributes).encode()

            drawSvgIcon(icon, painter, rect)
        else:
            icon = QIcon(icon)
            rect = QRectF(rect).toRect()
            painter.drawPixmap(rect, icon.pixmap(QRectF(rect).toRect().size()))


class ColoredFluentIcon(FluentIconBase):
    """带颜色的 Fluent 图标"""

    def __init__(self, icon: FluentIconBase, lightColor: Union[str, QColor], darkColor: Union[str, QColor]):
        """
        初始化 ColoredFluentIcon

        Parameters
        ----------
        icon : FluentIconBase
            要上色的 Fluent 图标
        lightColor : str | QColor | Qt.GlobalColor
            亮色模式下的图标颜色
        darkColor : str | QColor | Qt.GlobalColor
            暗色模式下的图标颜色
        """
        super().__init__()
        self.fluentIcon = icon
        self.lightColor = QColor(lightColor)
        self.darkColor = QColor(darkColor)

    def path(self, theme: Theme = Theme.AUTO) -> str:
        return self.fluentIcon.path(theme)

    def render(
        self,
        painter: QPainter,
        rect: QRect,
        theme: Theme = Theme.AUTO,
        indexes: Optional[List[int]] = None,
        **attributes,
    ) -> None:
        icon = self.path(theme)

        if not icon.endswith(".svg"):
            return self.fluentIcon.render(painter, rect, theme, indexes, attributes)

        if theme == Theme.AUTO:
            color = self.darkColor if isDarkTheme() else self.lightColor
        else:
            color = self.darkColor if theme == Theme.DARK else self.lightColor

        attributes.update(fill=color.name())
        icon = writeSvg(icon, indexes, **attributes).encode()
        drawSvgIcon(icon, painter, rect)


class FluentIcon(FluentIconBase, Enum):
    """Fluent 图标枚举"""

    UP = "Up"
    ADD = "Add"
    BUS = "Bus"
    CAR = "Car"
    CUT = "Cut"
    IOT = "IOT"
    PIN = "Pin"
    TAG = "Tag"
    VPN = "VPN"
    CAFE = "Cafe"
    CHAT = "Chat"
    COPY = "Copy"
    CODE = "Code"
    DOWN = "Down"
    EDIT = "Edit"
    FLAG = "Flag"
    FONT = "Font"
    GAME = "Game"
    HELP = "Help"
    HIDE = "Hide"
    HOME = "Home"
    INFO = "Info"
    LEAF = "Leaf"
    LINK = "Link"
    MAIL = "Mail"
    MENU = "Menu"
    MUTE = "Mute"
    MORE = "More"
    MOVE = "Move"
    PLAY = "Play"
    SAVE = "Save"
    SEND = "Send"
    SYNC = "Sync"
    UNIT = "Unit"
    VIEW = "View"
    WIFI = "Wifi"
    ZOOM = "Zoom"
    ALBUM = "Album"
    BRUSH = "Brush"
    BROOM = "Broom"
    CLOSE = "Close"
    CLOUD = "Cloud"
    EMBED = "Embed"
    GLOBE = "Globe"
    HEART = "Heart"
    LABEL = "Label"
    MEDIA = "Media"
    MOVIE = "Movie"
    MUSIC = "Music"
    ROBOT = "Robot"
    PAUSE = "Pause"
    PASTE = "Paste"
    PHOTO = "Photo"
    PHONE = "Phone"
    PRINT = "Print"
    SHARE = "Share"
    TILES = "Tiles"
    UNPIN = "Unpin"
    VIDEO = "Video"
    TRAIN = "Train"
    ADD_TO = "AddTo"
    ACCEPT = "Accept"
    CAMERA = "Camera"
    CANCEL = "Cancel"
    DELETE = "Delete"
    FOLDER = "Folder"
    FILTER = "Filter"
    MARKET = "Market"
    SCROLL = "Scroll"
    LAYOUT = "Layout"
    GITHUB = "GitHub"
    UPDATE = "Update"
    REMOVE = "Remove"
    RETURN = "Return"
    PEOPLE = "People"
    QRCODE = "QRCode"
    RINGER = "Ringer"
    ROTATE = "Rotate"
    SEARCH = "Search"
    VOLUME = "Volume"
    FRIGID = "Frigid"
    SAVE_AS = "SaveAs"
    ZOOM_IN = "ZoomIn"
    CONNECT = "Connect"
    HISTORY = "History"
    SETTING = "Setting"
    PALETTE = "Palette"
    MESSAGE = "Message"
    FIT_PAGE = "FitPage"
    ZOOM_OUT = "ZoomOut"
    AIRPLANE = "Airplane"
    ASTERISK = "Asterisk"
    CALORIES = "Calories"
    CALENDAR = "Calendar"
    FEEDBACK = "Feedback"
    LIBRARY = "BookShelf"
    MINIMIZE = "Minimize"
    CHECKBOX = "CheckBox"
    DOCUMENT = "Document"
    LANGUAGE = "Language"
    DOWNLOAD = "Download"
    QUESTION = "Question"
    SPEAKERS = "Speakers"
    DATE_TIME = "DateTime"
    FONT_SIZE = "FontSize"
    HOME_FILL = "HomeFill"
    PAGE_LEFT = "PageLeft"
    SAVE_COPY = "SaveCopy"
    SEND_FILL = "SendFill"
    SKIP_BACK = "SkipBack"
    SPEED_OFF = "SpeedOff"
    ALIGNMENT = "Alignment"
    BLUETOOTH = "Bluetooth"
    COMPLETED = "Completed"
    CONSTRACT = "Constract"
    HEADPHONE = "Headphone"
    MEGAPHONE = "Megaphone"
    PROJECTOR = "Projector"
    EDUCATION = "Education"
    LEFT_ARROW = "LeftArrow"
    ERASE_TOOL = "EraseTool"
    PAGE_RIGHT = "PageRight"
    PLAY_SOLID = "PlaySolid"
    BOOK_SHELF = "BookShelf"
    HIGHTLIGHT = "Highlight"
    FOLDER_ADD = "FolderAdd"
    PAUSE_BOLD = "PauseBold"
    PENCIL_INK = "PencilInk"
    PIE_SINGLE = "PieSingle"
    QUICK_NOTE = "QuickNote"
    SPEED_HIGH = "SpeedHigh"
    STOP_WATCH = "StopWatch"
    ZIP_FOLDER = "ZipFolder"
    BASKETBALL = "Basketball"
    BRIGHTNESS = "Brightness"
    DICTIONARY = "Dictionary"
    MICROPHONE = "Microphone"
    ARROW_DOWN = "ChevronDown"
    FULL_SCREEN = "FullScreen"
    MIX_VOLUMES = "MixVolumes"
    REMOVE_FROM = "RemoveFrom"
    RIGHT_ARROW = "RightArrow"
    QUIET_HOURS = "QuietHours"
    FINGERPRINT = "Fingerprint"
    APPLICATION = "Application"
    CERTIFICATE = "Certificate"
    TRANSPARENT = "Transparent"
    IMAGE_EXPORT = "ImageExport"
    SPEED_MEDIUM = "SpeedMedium"
    LIBRARY_FILL = "LibraryFill"
    MUSIC_FOLDER = "MusicFolder"
    POWER_BUTTON = "PowerButton"
    SKIP_FORWARD = "SkipForward"
    CARE_UP_SOLID = "CareUpSolid"
    ACCEPT_MEDIUM = "AcceptMedium"
    CANCEL_MEDIUM = "CancelMedium"
    CHEVRON_RIGHT = "ChevronRight"
    CLIPPING_TOOL = "ClippingTool"
    SEARCH_MIRROR = "SearchMirror"
    SHOPPING_CART = "ShoppingCart"
    FONT_INCREASE = "FontIncrease"
    BACK_TO_WINDOW = "BackToWindow"
    COMMAND_PROMPT = "CommandPrompt"
    CLOUD_DOWNLOAD = "CloudDownload"
    DICTIONARY_ADD = "DictionaryAdd"
    CARE_DOWN_SOLID = "CareDownSolid"
    CARE_LEFT_SOLID = "CareLeftSolid"
    CLEAR_SELECTION = "ClearSelection"
    DEVELOPER_TOOLS = "DeveloperTools"
    BACKGROUND_FILL = "BackgroundColor"
    CARE_RIGHT_SOLID = "CareRightSolid"
    CHEVRON_DOWN_MED = "ChevronDownMed"
    CHEVRON_RIGHT_MED = "ChevronRightMed"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"
    EXPRESSIVE_INPUT_ENTRY = "ExpressiveInputEntry"

    def path(self, theme: Theme = Theme.AUTO) -> str:
        return f":/qfluentwidgets/images/icons/{self.value}_{getIconColor(theme)}.svg"


class Icon(QIcon):
    """Fluent 图标的 QIcon 封装"""

    def __init__(self, fluentIcon: FluentIcon):
        """
        初始化 Icon

        Parameters
        ----------
        fluentIcon : FluentIcon
            Fluent 图标枚举
        """
        super().__init__(fluentIcon.path())
        self.fluentIcon = fluentIcon


def toQIcon(icon: Union[QIcon, FluentIconBase, str]) -> QIcon:
    """将 icon 转换为 QIcon

    Parameters
    ----------
    icon : QIcon | FluentIconBase | str
        要转换的图标

    Returns
    -------
    QIcon
        转换后的 QIcon 对象
    """
    if isinstance(icon, str):
        return QIcon(icon)

    if isinstance(icon, FluentIconBase):
        return icon.icon()

    return icon


class Action(QAction):
    """Fluent 动作"""

    @singledispatchmethod
    def __init__(self, parent: Optional[QObject] = None, **kwargs):
        """
        初始化 Fluent 动作

        Parameters
        ----------
        parent : QObject, optional
            父对象, 默认为 None
        **kwargs :
            其他参数
        """
        super().__init__(parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, text: str, parent: Optional[QObject] = None, **kwargs):
        """
        初始化带文本的 Fluent 动作

        Parameters
        ----------
        text : str
            动作文本
        parent : QObject, optional
            父对象, 默认为 None
        **kwargs :
            其他参数
        """
        super().__init__(text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: Optional[QObject] = None, **kwargs):
        """
        初始化带图标的 Fluent 动作

        Parameters
        ----------
        icon : QIcon
            图标
        text : str
            动作文本
        parent : QObject, optional
            父对象, 默认为 None
        **kwargs :
            其他参数
        """
        super().__init__(icon, text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: Optional[QObject] = None, **kwargs):
        """
        初始化带 Fluent 图标的动作

        Parameters
        ----------
        icon : FluentIconBase
            Fluent 图标
        text : str
            动作文本
        parent : QObject, optional
            父对象, 默认为 None
        **kwargs :
            其他参数
        """
        super().__init__(icon.icon(), text, parent, **kwargs)
        self.fluentIcon = icon

    def icon(self) -> QIcon:
        """获取动作的图标

        Returns
        -------
        QIcon
            动作的图标
        """
        if self.fluentIcon:
            return Icon(self.fluentIcon)

        return super().icon()

    def setIcon(self, icon: Union[FluentIconBase, QIcon]) -> None:
        """设置动作的图标

        Parameters
        ----------
        icon : FluentIconBase | QIcon
            设置的图标
        """
        if isinstance(icon, FluentIconBase):
            self.fluentIcon = icon
            icon = icon.icon()

        super().setIcon(icon)
