# coding:utf-8
# 标准库导入
from copy import deepcopy
from typing import Any, Tuple, Union, Callable


def exceptionHandler(*default: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """用于异常处理的装饰器。

    当被装饰的函数抛出异常时，返回预设的默认值。

    Parameters
    ----------
    *default : Any
    - 当函数抛出异常时返回的默认值, 可以是多个值：
        1. 如果没有提供默认值, 返回 `None`
        2. 如果提供一个默认值, 返回该值
        3. 如果提供多个默认值, 返回包含这些值的元组

    Returns
    -------
    Callable: Callable[[Callable[..., Any]], Callable[..., Any]]
        返回一个装饰器, 该装饰器包装了被装饰的函数.
    """

    def outer(func: Callable[..., Any]) -> Callable[..., Any]:
        def inner(*args: Any, **kwargs: Any) -> Union[Any, None, Tuple[Any, ...]]:
            try:
                return func(*args, **kwargs)
            except BaseException:
                # 复制默认值，避免原值被修改
                value = deepcopy(default)
                # 根据提供的默认值个数返回对应结果
                if len(value) == 0:
                    return None
                elif len(value) == 1:
                    return value[0]
                return tuple(value)  # 返回元组以支持多个默认值

        return inner

    return outer
