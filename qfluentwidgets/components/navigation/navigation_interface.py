# coding:utf-8
# 标准库导入
from typing import Union

# 第三方库导入
from PySide6.QtGui import QIcon, QResizeEvent
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtWidgets import QWidget

from ...common.icon import FluentIconBase
from .navigation_panel import NavigationPanel, NavigationWidget, NavigationDisplayMode, NavigationItemPosition
from .navigation_widget import NavigationTreeWidget


class NavigationInterface(QWidget):
    """Navigation interface"""

    displayModeChanged = Signal(NavigationDisplayMode)

    def __init__(self, parent=None, showMenuButton=True, showReturnButton=False, collapsible=True) -> None:
        """
        Parameters
        ----------
        parent: QWidget
            父级窗口小部件

        showMenuButton: bool
            是否显示菜单按钮

        showReturnButton: bool
            是否显示返回按钮

        collapsible: bool
            导航界面是否可折叠
        """
        super().__init__(parent=parent)
        self.panel = NavigationPanel(self)
        self.panel.setMenuButtonVisible(showMenuButton and collapsible)
        self.panel.setReturnButtonVisible(showReturnButton)
        self.panel.setCollapsible(collapsible)
        self.panel.installEventFilter(self)
        self.panel.displayModeChanged.connect(self.displayModeChanged)

        self.resize(48, self.height())
        self.setMinimumWidth(48)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def addItem(
        self,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=NavigationItemPosition.TOP,
        tooltip: str = None,
        parentRouteKey: str = None,
    ) -> NavigationTreeWidget:
        """添加导航项

        Parameters
        ----------
        routeKey: str
            项的唯一标识

        icon: str | QIcon | FluentIconBase
            导航项的图标

        text: str
            导航项的文本

        onClick: callable, optional
            点击信号连接的槽函数

        selectable: bool
            项是否可选

        position: NavigationItemPosition
            按钮添加的位置

        tooltip: str, optional
            项的工具提示

        parentRouteKey: str, optional
            父项的路由键，父项应为 `NavigationTreeWidgetBase`
        """
        return self.insertItem(-1, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)

    def addWidget(
        self,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=NavigationItemPosition.TOP,
        tooltip: str = None,
        parentRouteKey: str = None,
    ) -> NavigationTreeWidget:
        """添加自定义组件

        Parameters
        ----------
        routKey: str
            项的唯一标识

        widget: NavigationWidget
            要添加的自定义组件

        onClick: callable
            链接到项点击信号的槽函数

        position: NavigationItemPosition
            自定义组件添加的位置

        tooltip: str
            提示信息

        parentRouteKey: str
            父项的路由键，父项应为 'NavigationTreeWidgetBase'
        """
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip, parentRouteKey)

    def insertItem(
        self,
        index: int,
        routeKey: str,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        onClick=None,
        selectable=True,
        position=NavigationItemPosition.TOP,
        tooltip: str = None,
        parentRouteKey: str = None,
    ) -> NavigationTreeWidget:
        """插入导航项

        Parameters
        ----------
        index: int
            插入位置

        routKey: str
            项的唯一标识

        icon: str | QIcon | FluentIconBase
            导航项的图标

        text: str
            导航项的文本

        onClick: callable
            链接到项点击信号的槽函数

        selectable: bool
            项目是否可选

        position: NavigationItemPosition
            项的添加位置

        tooltip: str
            项的提示

        parentRouteKey: str
            父项的路由键，父项应为 'NavigationTreeWidgetBase'
        """
        w = self.panel.insertItem(index, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())
        return w

    def insertWidget(
        self,
        index: int,
        routeKey: str,
        widget: NavigationWidget,
        onClick=None,
        position=NavigationItemPosition.TOP,
        tooltip: str = None,
        parentRouteKey: str = None,
    ) -> None:
        """插入自定义组件

        Parameters
        ----------
        index: int
            插入位置

        routKey: str
            项的唯一标识

        widget: NavigationWidget
            要添加的自定义组件

        onClick: callable
            链接到项点击信号的槽函数

        position: NavigationItemPosition
            自定义组件添加的位置

        tooltip: str
            提示信息

        parentRouteKey: str
            父项的路由键，父项应为 'NavigationTreeWidgetBase'
        """
        self.panel.insertWidget(index, routeKey, widget, onClick, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def addSeparator(self, position: NavigationItemPosition = NavigationItemPosition.TOP) -> None:
        """添加分隔线

        Parameters
        ----------
        position: NavigationItemPosition
            分隔线组件添加的位置
        """
        self.insertSeparator(-1, position)

    def insertSeparator(self, index: int, position: NavigationItemPosition = NavigationItemPosition.TOP) -> None:
        """插入分隔线

        Parameters
        ----------
        index: int
            插入位置

        position: NavigationItemPosition
            分隔线组件添加的位置
        """
        self.panel.insertSeparator(index, position)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def removeWidget(self, routeKey: str) -> None:
        """删除组件

        Parameters
        ----------
        routKey: str
            项的唯一名称
        """
        self.panel.removeWidget(routeKey)

    def setCurrentItem(self, name: str) -> None:
        """设置当前所选项

        Parameters
        ----------
        name: str
            项的唯一名称
        """
        self.panel.setCurrentItem(name)

    def expand(self, useAni=True):
        """expand navigation panel"""
        self.panel.expand(useAni)

    def toggle(self):
        """toggle navigation panel"""
        self.panel.toggle()

    def setExpandWidth(self, width: int):
        """set the maximum width"""
        self.panel.setExpandWidth(width)

    def setMinimumExpandWidth(self, width: int):
        """Set the minimum window width that allows panel to be expanded"""
        self.panel.setMinimumExpandWidth(width)

    def setMenuButtonVisible(self, isVisible: bool):
        """set whether the menu button is visible"""
        self.panel.setMenuButtonVisible(isVisible)

    def setReturnButtonVisible(self, isVisible: bool):
        """set whether the return button is visible"""
        self.panel.setReturnButtonVisible(isVisible)

    def setCollapsible(self, collapsible: bool):
        self.panel.setCollapsible(collapsible)

    def isAcrylicEnabled(self):
        return self.panel.isAcrylicEnabled()

    def setAcrylicEnabled(self, isEnabled: bool):
        """set whether the acrylic background effect is enabled"""
        self.panel.setAcrylicEnabled(isEnabled)

    def widget(self, routeKey: str):
        return self.panel.widget(routeKey)

    def eventFilter(self, obj, e: QEvent):
        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        if self.panel.displayMode != NavigationDisplayMode.MENU:
            event = QResizeEvent(e)
            if event.oldSize().width() != event.size().width():
                self.setFixedWidth(event.size().width())

        return super().eventFilter(obj, e)

    def resizeEvent(self, e: QResizeEvent):
        if e.oldSize().height() != self.height():
            self.panel.setFixedHeight(self.height())
