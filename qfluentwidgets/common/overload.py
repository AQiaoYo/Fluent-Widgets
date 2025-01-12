# coding: utf-8
# 标准库导入
from typing import Any, Type, Callable, Optional
from functools import singledispatch, update_wrapper


class singledispatchmethod:
    """单分派通用方法描述符
    这个类用于实现单分派（根据参数类型选择具体实现）的功能

    - 它支持以下两种情况：
        1. 能够包装已有的描述符（如类方法 `classmethod` 或静态方法 `staticmethod`），并使其支持单分派
        2. 能够将普通的函数包装成类的实例方法，并支持单分派。
    """

    def __init__(self, func: Callable[..., Any]) -> None:

        # 检查传入的参数是否是一个可调用对象或者描述符
        if not callable(func) and not hasattr(func, "__get__"):
            raise TypeError(f"{func!r} is not callable or a descriptor")

        # 创建一个新的单分派对象
        self.dispatcher = singledispatch(func)
        self.func = func

    def register(self, cls: Type, method: Optional[Callable[..., Any]] = None) -> Callable[..., Any]:
        """为指定的类型注册一个方法实现

        这个方法允许在单分派方法中, 根据传入参数的类型动态选择调用不同的实现
        在实际应用中, 比如初始化方法 `__init__`, 可以根据参数类型提供多种构造方式


        Parameters:
        ----------
        cls : Type
            要注册方法的类型, 例如 `str`、`QIcon` 或自定义类
        method : Optional[Callable[..., Any]]
            对应类型的处理方法, 如果为 `None`, 使用默认逻辑

        Returns:
        -------
        Callable[..., Any]
            注册的方法本身, 方便后续链式调用.
        """
        return self.dispatcher.register(cls, func=method)

    def __get__(self, obj: Optional[Any], cls: Optional[Type] = None) -> Callable[..., Any]:
        """描述符的获取方法，用于为实例或类返回单分派的方法

        - 获取方法时，根据调用方式返回不同的方法：
            1. 如果是通过实例访问，返回一个绑定到该实例的方法
            2. 如果是通过类访问，返回一个未绑定的方法

        Parameters:
        ----------
        obj : Optional[Any]
            调用方法的实例对象
        cls : Optional[Type]
            调用方法的类对象

        Returns:
        -------
        Callable[..., Any]
            返回一个新的方法，用于根据参数类型选择
        """

        def _method(*args, **kwargs):
            """根据参数类型选择具体的方法实现"""
            if args:
                # 如果传入的第一个参数是实例对象，则根据实例对象的类型选择具体的方法
                method = self.dispatcher.dispatch(args[0].__class__)
            else:
                # 如果传入的参数是关键字参数，则根据关键字参数的类型选择具体的方法
                method = self.func
                for v in kwargs.values():
                    if v.__class__ in self.dispatcher.registry:
                        method = self.dispatcher.dispatch(v.__class__)
                        if method is not self.func:
                            break

            return method.__get__(obj, cls)(*args, **kwargs)

        # 为新方法添加属性
        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.register = self.register
        update_wrapper(_method, self.func)
        return _method

    @property
    def __isabstractmethod__(self) -> bool:
        """检查该方法是否是抽象方法"""
        return getattr(self.func, "__isabstractmethod__", False)
