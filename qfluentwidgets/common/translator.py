# coding: utf-8
# 第三方库导入
from PySide6.QtCore import QLocale, QTranslator


class FluentTranslator(QTranslator):
    """ Translator of fluent widgets """

    def __init__(self, locale: QLocale = None, parent=None):
        super().__init__(parent=parent)
        self.load(locale or QLocale())

    def load(self, locale: QLocale):
        """ load translation file """
        super().load(f":/qfluentwidgets/i18n/qfluentwidgets.{locale.name()}.qm")