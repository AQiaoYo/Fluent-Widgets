# coding: utf-8
# 第三方库导入
from PySide6.QtCore import QLocale, QObject, QTranslator


class FluentTranslator(QTranslator):
    """Fluent 小部件的翻译"""

    def __init__(self, locale: QLocale = None, parent: QObject | None = None) -> None:
        """初始化翻译器"""
        super().__init__(parent=parent)

        # 如果没有指定语言，则使用系统语言
        self.load(locale or QLocale())

    def load(self, locale: QLocale) -> None:
        """加载翻译文件"""
        super().load(f":/qfluentwidgets/i18n/qfluentwidgets.{locale.name()}.qm")
