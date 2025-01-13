# coding:utf-8
# 标准库导入
from typing import Dict, List
from itertools import groupby

# 第三方库导入
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QStackedWidget


class RouteItem:
    """
    表示路由项的类

    Attributes
    ----------
    stacked : QStackedWidget
        当前的堆叠小部件
    routeKey : str
        路由的关键字, 表示子界面的唯一标识
    """

    def __init__(self, stacked: QStackedWidget, routeKey: str):
        """
        初始化路由项

        Parameters
        ----------
        stacked : QStackedWidget
            当前的堆叠小部件
        routeKey : str
            路由的关键字, 表示子界面的唯一标识
        """
        self.stacked = stacked
        self.routeKey = routeKey

    def __eq__(self, other: object) -> bool:
        """
        判断两个RouteItem是否相等

        Parameters
        ----------
        other : object
            另一个RouteItem对象

        Returns
        -------
        bool
            如果两个RouteItem相等, 返回True, 否则返回False
        """
        if other is None:
            return False

        return other.stacked is self.stacked and other.routeKey == self.routeKey


class StackedHistory:
    """
    管理堆叠小部件历史记录的类

    Attributes
    ----------
    stacked : QStackedWidget
        当前的堆叠小部件
    defaultRouteKey : str
        默认的路由关键字
    history : List[str]
        存储历史路由关键字的列表
    """

    def __init__(self, stacked: QStackedWidget):
        """
        初始化堆叠历史

        Parameters
        ----------
        stacked : QStackedWidget
            当前的堆叠小部件
        """
        self.stacked = stacked
        self.defaultRouteKey = None  # type: str
        self.history = [self.defaultRouteKey]  # type: List[str]

    def __len__(self) -> int:
        """
        获取历史记录的长度

        Returns
        -------
        int
            历史记录的条数
        """
        return len(self.history)

    def isEmpty(self) -> bool:
        """
        判断历史记录是否为空

        Returns
        -------
        bool
            如果历史记录为空, 返回True, 否则返回False
        """
        return len(self) <= 1

    def push(self, routeKey: str) -> bool:
        """
        推送新的路由到历史记录中

        Parameters
        ----------
        routeKey : str
            要推送的路由关键字

        Returns
        -------
        bool
            如果推送成功, 返回True, 否则返回False
        """
        if self.history[-1] == routeKey:
            return False

        self.history.append(routeKey)
        return True

    def pop(self):
        """
        弹出历史记录中的最后一个路由, 并跳转到顶部
        """
        if self.isEmpty():
            return

        self.history.pop()
        self.goToTop()

    def remove(self, routeKey: str):
        """
        从历史记录中移除指定的路由

        Parameters
        ----------
        routeKey : str
            要移除的路由关键字
        """
        if routeKey not in self.history:
            return

        # 删除历史记录中的所有指定路由关键字
        self.history[1:] = [i for i in self.history[1:] if i != routeKey]
        self.history = [k for k, g in groupby(self.history)]  # 合并重复项
        self.goToTop()

    def top(self) -> str:
        """
        获取历史记录栈顶的路由关键字

        Returns
        -------
        str
            历史记录栈顶的路由关键字
        """
        return self.history[-1]

    def setDefaultRouteKey(self, routeKey: str):
        """
        设置默认路由关键字

        Parameters
        ----------
        routeKey : str
            默认路由关键字
        """
        self.defaultRouteKey = routeKey
        self.history[0] = routeKey

    def goToTop(self):
        """
        跳转到顶部路由对应的界面
        """
        w = self.stacked.findChild(QWidget, self.top())
        if w:
            self.stacked.setCurrentWidget(w)


class Router(QObject):
    """
    路由管理器类

    Attributes
    ----------
    emptyChanged : Signal
        路由栈是否为空的信号
    history : List[RouteItem]
        路由项的历史记录
    stackHistories : Dict[QStackedWidget, StackedHistory]
        存储每个堆叠小部件对应的历史记录
    """

    emptyChanged = Signal(bool)

    def __init__(self, parent: QObject = None):
        """
        初始化路由管理器

        Parameters
        ----------
        parent : QObject, optional
            父对象, 默认为None
        """
        super().__init__(parent=parent)
        self.history = []  # type: List[RouteItem]
        self.stackHistories = {}  # type: Dict[QStackedWidget, StackedHistory]

    def setDefaultRouteKey(self, stacked: QStackedWidget, routeKey: str):
        """
        设置堆叠小部件的默认路由关键字

        Parameters
        ----------
        stacked : QStackedWidget
            堆叠小部件
        routeKey : str
            默认路由关键字
        """
        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        self.stackHistories[stacked].setDefaultRouteKey(routeKey)

    def push(self, stacked: QStackedWidget, routeKey: str):
        """
        推送路由历史记录

        Parameters
        ----------
        stacked : QStackedWidget
            堆叠小部件
        routeKey : str
            子界面的路由关键字, 通常是子界面的对象名称
        """
        item = RouteItem(stacked, routeKey)

        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        # 如果历史记录中没有相同的路由项, 才加入
        success = self.stackHistories[stacked].push(routeKey)
        if success:
            self.history.append(item)

        # 发出空栈状态变化的信号
        self.emptyChanged.emit(not bool(self.history))

    def pop(self):
        """
        弹出历史记录并回到上一个路由
        """
        if not self.history:
            return

        item = self.history.pop()
        self.emptyChanged.emit(not bool(self.history))
        self.stackHistories[item.stacked].pop()

    def remove(self, routeKey: str):
        """
        移除指定路由的历史记录

        Parameters
        ----------
        routeKey : str
            要移除的路由关键字
        """
        self.history = [i for i in self.history if i.routeKey != routeKey]
        self.history = [list(g)[0] for k, g in groupby(self.history, lambda i: i.routeKey)]
        self.emptyChanged.emit(not bool(self.history))

        # 在所有堆叠小部件中移除指定路由
        for stacked, history in self.stackHistories.items():
            w = stacked.findChild(QWidget, routeKey)
            if w:
                return history.remove(routeKey)


qrouter = Router()
