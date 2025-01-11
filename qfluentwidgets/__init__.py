"""
Fluent-Widgets
==============
A fluent design widgets library based on PySide6.

This project is derived from the original PySide6-Fluent-Widgets library
created by zhiyiYo. Fluent-Widgets builds upon it with additional features
and enhancements.

Original project: PySide6-Fluent-Widgets by zhiyiYo  
Documentation is available online at https://qfluentwidgets.com.

Examples are available at https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6/examples.

:copyright: (c) 2021 by zhiyiYo.  
:modified: (c) 2025 by QIAO.  
:license: GPLv3 for non-commercial project, see README for more details.
"""

__version__ = "1.0.0"
__author__ = "zhiyiYo, modified by QIAO"


from ._rc import resource
from .common import *
from .window import *
from .components import *
from .multimedia import *
