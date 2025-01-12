# coding:utf-8
# 标准库导入
import json
from copy import deepcopy
from enum import Enum
from typing import Any, List, Tuple, Optional
from pathlib import Path

# 第三方库导入
import darkdetect
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal, QObject

from .exception_handler import exceptionHandler


class Theme(Enum):
    """主题枚举类"""

    LIGHT = "Light"
    DARK = "Dark"
    AUTO = "Auto"


class ConfigValidator:
    """配置验证器"""

    def validate(self, value: Any) -> bool:
        """验证该值是否合法

        具体实现类需要重写该方法
        """
        return True

    def correct(self, value: Any) -> Any:
        """更正非法值

        具体实现类需要重写该方法
        """
        return value


class RangeValidator(ConfigValidator):
    """范围验证器"""

    def __init__(self, min: int, max: int) -> None:
        self.min: int = min
        self.max: int = max
        self.range: Tuple[int, int] = (min, max)

    def validate(self, value: int) -> bool:
        """验证该值是否在范围内"""
        return self.min <= value <= self.max

    def correct(self, value: int) -> int:
        """更正非法值, 使其在范围内"""
        return min(max(self.min, value), self.max)


class OptionsValidator(ConfigValidator):
    """选项验证器"""

    def __init__(self, options: Enum | List[Any]) -> None:
        if not options:
            # 不存在则抛出异常
            raise ValueError("The `options` can't be empty.")

        if isinstance(options, Enum):
            # 如果是枚举类, 则获取枚举值
            options = options._member_map_.values()

        # 不论是枚举值还是直接的列表, 都转换为列表
        self.options = list(options)

    def validate(self, value: Any) -> bool:
        """验证该值是否在选项中"""
        return value in self.options

    def correct(self, value: Any) -> Any:
        """更正非法值, 使其在选项中"""
        return value if self.validate(value) else self.options[0]


class BoolValidator(OptionsValidator):
    """布尔验证器"""

    def __init__(self) -> None:
        super().__init__([True, False])


class FolderValidator(ConfigValidator):
    """文件夹验证器"""

    def validate(self, value: str) -> bool:
        """验证该值是否为文件夹"""
        return Path(value).exists()

    def correct(self, value: str) -> str:
        """更正非法值, 使其为文件夹"""
        path = Path(value)
        path.mkdir(exist_ok=True, parents=True)
        return str(path.absolute()).replace("\\", "/")


class FolderListValidator(ConfigValidator):
    """文件夹列表验证器"""

    def validate(self, value: List[str]) -> bool:
        """验证该值是否为文件夹列表"""
        return all(Path(item).exists() for item in value)

    def correct(self, value: List[str]) -> List[str]:
        """更正非法值, 使其为文件夹列表"""
        return [str(path.absolute()).replace("\\", "/") for folder in value if (path := Path(folder)).exists()]


class ColorValidator(ConfigValidator):
    """RGB 颜色验证器"""

    def __init__(self, default) -> None:
        """初始化颜色验证器

        Parameters
        ----------
        default: str | int | tuple | QColor | QRgba64 | Qt.GlobalColor
            默认颜色
        """
        self.default = QColor(default)

    def validate(self, color) -> bool:
        """验证该值是否为合法颜色

        Parameters
        ----------
        color: str | int | tuple | QColor | QRgba64 | Qt.GlobalColor
            颜色值

        Returns
        -------
        bool
            是否为合法颜色
        """
        try:
            return QColor(color).isValid()
        except:
            return False

    def correct(self, value) -> QColor:
        """更正非法值, 使其为合法颜色

        Parameters
        ----------
        value: str | int | tuple | QColor | QRgba64 | Qt.GlobalColor
            颜色值

        Returns
        -------
        QColor
            合法颜色
        """
        return QColor(value) if self.validate(value) else self.default


class ConfigSerializer:
    """配置序列化器"""

    def serialize(self, value):
        """序列化配置值

        具体实现类需要重写该方法
        """
        return value

    def deserialize(self, value):
        """从配置文件的值反序列化配置

        具体实现类需要重写该方法
        """
        return value


class EnumSerializer(ConfigSerializer):
    """枚举类序列化器"""

    def __init__(self, enumClass: Enum):
        self.enumClass = enumClass

    def serialize(self, value: Enum) -> str:
        """序列化枚举值"""
        return value.value

    def deserialize(self, value: Any) -> Enum:
        """反序列化枚举值"""
        return self.enumClass(value)


class ColorSerializer(ConfigSerializer):
    """QColor 序列化器"""

    def serialize(self, value: QColor) -> str:
        """序列化颜色值"""
        return value.name(QColor.HexArgb)

    def deserialize(self, value: Any) -> QColor:
        """反序列化颜色值"""
        if isinstance(value, list):
            return QColor(*value)

        return QColor(value)


class ConfigItem(QObject):
    """配置项"""

    # 值改变信号
    valueChanged = Signal(object)

    def __init__(
        self,
        group: str,
        name: str,
        default: Any,
        validator: ConfigValidator = None,
        serializer: ConfigSerializer = None,
        restart: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        group: str
            配置组名称

        name: str
            配置项名称，可以为空

        default: Any
            默认值

        validator: ConfigValidator
            配置验证器

        serializer: ConfigSerializer
            配置序列化器

        restart: bool
            更新值后是否重启应用程序
        """
        super().__init__()
        self.group = group
        self.name = name
        self.validator = validator or ConfigValidator()
        self.serializer = serializer or ConfigSerializer()
        self.__value = default
        self.value = default
        self.restart = restart
        self.defaultValue = self.validator.correct(default)

    @property
    def value(self) -> Any:
        """获取 config item 的值"""
        return self.__value

    @value.setter
    def value(self, value: Any) -> None:
        """设置 config item 的值

        - 原逻辑
        1. 验证新值是否合法
        2. 将旧值赋值给old_value
        3. 将value赋值给__value(是不管是否一样都会赋值)
        4. 如果old_value和value不一样, 则发射valueChanged信号

        ```python
        value = self.validator.correct(value)
        old_value = self.__value
        self.__value = value
        if old_value != value:
        self.valueChanged.emit(value)
        ```
        - 现逻辑
        1. 直接判断old_value和value(使用表达式确保了value是经过验证的)
        2. 如果不一样, 则发射valueChanged信号, 并且更新__value
        3. 如果一样, 则不发射valueChanged信号, __value还是原样

        Parameters
        ----------
        value: Any
            新值
        """
        if self.__value != (value := self.validator.correct(value)):
            self.__value = value
            self.valueChanged.emit(value)

    @property
    def key(self) -> str:
        """获取以 '.' 分隔的配置键"""
        return self.group + "." + self.name if self.name else self.group

    def __str__(self) -> str:
        """返回配置项的字符串表示"""
        return f"{self.__class__.__name__}[value={self.value}]"

    def serialize(self) -> Any:
        """序列化配置值"""
        return self.serializer.serialize(self.value)

    def deserializeFrom(self, value: Any) -> None:
        """从配置文件的值反序列化配置"""
        self.value = self.serializer.deserialize(value)


class RangeConfigItem(ConfigItem):
    """范围配置项"""

    validator: RangeValidator

    @property
    def range(self) -> Tuple[int, int]:
        """获取配置项的可用范围"""
        return self.validator.range

    def __str__(self) -> str:
        """返回配置项的字符串表示"""
        return f"{self.__class__.__name__}[range={self.range}, value={self.value}]"


class OptionsConfigItem(ConfigItem):
    """选项配置项"""

    validator: OptionsValidator

    @property
    def options(self) -> List[Any]:
        """获取配置项的可用选项"""
        return self.validator.options

    def __str__(self) -> str:
        """返回配置项的字符串表示"""
        return f"{self.__class__.__name__}[options={self.options}, value={self.value}]"


class ColorConfigItem(ConfigItem):
    """颜色配置项"""

    def __init__(self, group, name, default, restart=False) -> None:
        super().__init__(group, name, QColor(default), ColorValidator(default), ColorSerializer(), restart)

    def __str__(self) -> str:
        """返回配置项的字符串表示"""
        return f"{self.__class__.__name__}[value={self.value.name()}]"


class QConfig(QObject):
    """App 配置类"""

    # 信号定义
    appRestartSig = Signal()
    themeChanged = Signal(Theme)
    themeChangedFinished = Signal()
    themeColorChanged = Signal(QColor)

    # 配置项定义
    themeMode = OptionsConfigItem(
        group="Personalized",
        name="ThemeMode",
        default=Theme.LIGHT,
        validator=OptionsValidator(Theme),
        serializer=EnumSerializer(Theme),
    )
    themeColor = ColorConfigItem(
        group="Personalized",
        name="ThemeColor",
        default="#009faa",
    )

    def __init__(self) -> None:
        super().__init__()
        self.file = Path("config/config.json")
        self._theme = Theme.LIGHT
        self._cfg = self  # 托管配置对象

    def get(self, item: ConfigItem) -> Any:
        """获取配置项的值"""
        return item.value

    def set(self, item: ConfigItem, value: Any, save: bool = True, copy: bool = True) -> None:
        """设置配置项的值

        Parameters
        ----------
        item: ConfigItem
            配置项

        value:
            配置项的新值

        save: bool
            是否保存对配置文件的更改

        copy: bool
            是否深度复制新值, 隔离新值和旧值
        """
        if item.value == value:
            # 如果新值和旧值一样, 则直接返回
            return

        # 深度复制新值
        try:
            item.value = deepcopy(value) if copy else value
        except:
            item.value = value

        if save:
            self.save()

        if item.restart:
            # 如果配置项需要重启应用程序, 则发射重启信号
            self._cfg.appRestartSig.emit()

        if item is self._cfg.themeMode:
            # 如果是主题模式配置项, 则发射主题改变信号
            self.theme = value
            self._cfg.themeChanged.emit(value)

        if item is self._cfg.themeColor:
            # 如果是主题颜色配置项, 则发射主题颜色改变信号
            self._cfg.themeColorChanged.emit(value)

    def toDict(self, serialize: bool = True) -> dict:
        """将配置项转换为字典形式 (dict)

        Parameters
        ----------
        serialize (bool): 是否对配置项进行序列化处理, 默认为 True


        Returns
        -------
        dict: 配置项的字典形式
        """
        items = {}  # 初始化存储配置项的字典。

        # 遍历 `self._cfg.__class__` 的所有属性名称。
        for name in dir(self._cfg.__class__):
            # 获取当前属性值。
            item = getattr(self._cfg.__class__, name)

            # 如果属性不是 ConfigItem 类型，则跳过当前循环。
            if not isinstance(item, ConfigItem):
                continue

            # 如果需要序列化配置项，则调用其 serialize 方法。
            # 否则，直接获取配置项的值。
            value = item.serialize() if serialize else item.value

            # ### 配置项分类操作 ###
            # 检查 `item` 的分组 (group) 和名称 (name)，并将配置项存入对应的分组。

            # 如果当前配置项的分组 (group) 在 `items` 中不存在：
            if not items.get(item.group):
                # 如果配置项没有具体名称 (name 为 None)，直接将值赋给该分组。
                # 否则，为该分组初始化一个空字典，准备存储具体配置项。
                items[item.group] = value if not item.name else {}

            # 如果配置项有名称 (name 不为 None)：
            if item.name:
                # 将配置项的值存入对应分组的字典中，键为配置项名称，值为具体值。
                items[item.group][item.name] = value

        return items

    def save(self) -> None:
        """保存配置"""
        self._cfg.file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cfg.file, "w", encoding="utf-8") as f:
            json.dump(self._cfg.toDict(), f, ensure_ascii=False, indent=4)

    @exceptionHandler()
    def load(self, file: Optional[str | Path] = None, config=None) -> None:
        """加载配置

        Parameters
        ----------
        file: str or Path
            json 配置文件的路径

        config: Config
            要初始化的 config 对象
        """

        # ### 形参处理 ###
        if isinstance(config, QConfig):
            self._cfg = config
            self._cfg.themeChanged.connect(self.themeChanged)

        if isinstance(file, (str, Path)):
            self._cfg.file = Path(file)

        # ### 读取配置文件 ###
        try:
            with open(self._cfg.file, encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            cfg = {}

        # ### 将配置项的键映射到项 ###
        items: dict[str, ConfigItem] = {}

        for name in dir(self._cfg.__class__):
            # 遍历 `self._cfg.__class__` 的所有属性名称
            if isinstance((item := getattr(self._cfg.__class__), name), ConfigItem):
                # 如果属性是 ConfigItem 类型，则将其存入 `items` 字典中
                items[item.key] = item

            # ### 更新配置项 ###

            # 遍历配置文件中的所有配置项 (cfg 为配置文件的字典形式)。
            for cfg_key, cfg_value in cfg.items():

                # 如果配置值不是字典，并且配置项存在于 items 中：
                if not isinstance(cfg_value, dict) and items.get(cfg_key) is not None:
                    # 直接反序列化配置项，将配置文件中的值应用到对应的配置项中。
                    items[cfg_key].deserializeFrom(cfg_value)

                # 如果配置值是一个字典：
                elif isinstance(cfg_value, dict):
                    # 遍历该字典中的键值对。
                    for key, value in cfg_value.items():

                        # 生成完整的配置项路径 (格式为 "分组.名称")。
                        key = cfg_key + "." + key

                        # 如果生成的配置项路径存在于 items 中：
                        if items.get(key) is not None:
                            # 对该配置项进行反序列化，将子配置的值应用到对应的配置项中。
                            items[key].deserializeFrom(value)

        self.theme = self.get(self._cfg.themeMode)

    @property
    def theme(self) -> Theme:
        """获取主题模式，可以是 'Theme.Light' 或 'Theme.Dark'"""
        return self._cfg._theme

    @theme.setter
    def theme(self, theme: Theme) -> None:
        """在不修改配置文件的情况下更改主题"""
        if theme == Theme.AUTO:
            theme = darkdetect.theme()
            theme = Theme(theme) if theme else Theme.LIGHT

        self._cfg._theme = theme


qconfig = QConfig()


def isDarkTheme():
    """判断主题是否为深色模式"""
    return qconfig.theme == Theme.DARK


def theme():
    """获取主题模式"""
    return qconfig.theme
