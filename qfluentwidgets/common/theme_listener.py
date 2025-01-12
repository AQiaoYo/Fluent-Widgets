# coding:utf-8
# 第三方库导入
import darkdetect
from PySide6.QtCore import Signal, QObject, QThread

from .config import Theme, qconfig


class SystemThemeListener(QThread):
    """系统主题监听器"""

    systemThemeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent=parent)

    def run(self) -> None:
        # 使用 darkdetect 模块监听系统主题变化, 并连接到槽函数
        darkdetect.listener(self._onThemeChanged)

    def _onThemeChanged(self, theme: str) -> None:
        """主题变化时的槽函数"""

        # 根据传入的 theme 参数判断系统主题
        theme = Theme.DARK if theme.lower() == "dark" else Theme.LIGHT

        # 如果当前主题模式为自动, 则根据系统主题自动切换主题
        if qconfig.themeMode.value != Theme.AUTO or theme == qconfig.theme:
            return

        # 切换主题
        qconfig.theme = Theme.AUTO
        qconfig._cfg.themeChanged.emit(Theme.AUTO)
        self.systemThemeChanged.emit()
