# coding: utf-8
# 标准库导入
from enum import Enum

# 第三方库导入
from PySide6.QtGui import QColor


class FluentThemeColor(Enum):
    """Fluent 主题颜色

    Refer to: https://www.figma.com/file/iM7EPX8Jn37zjeSezb43cF
    """

    YELLOW_GOLD = "#FFB900"  # 黄色金
    GOLD = "#FF8C00"  # 金色
    ORANGE_BRIGHT = "#F7630C"  # 明亮橙色
    ORANGE_DARK = "#CA5010"  # 深橙色
    RUST = "#DA3B01"  # 铁锈红
    PALE_RUST = "#EF6950"  # 浅铁锈红
    BRICK_RED = "#D13438"  # 砖红色
    MOD_RED = "#FF4343"  # 模拟红
    PALE_RED = "#E74856"  # 浅红色
    RED = "#E81123"  # 红色
    ROSE_BRIGHT = "#EA005E"  # 明亮玫瑰红
    ROSE = "#C30052"  # 玫瑰红
    PLUM_LIGHT = "#E3008C"  # 浅李子紫
    PLUM = "#BF0077"  # 李子紫
    ORCHID_LIGHT = "#BF0077"  # 浅兰花紫
    ORCHID = "#9A0089"  # 兰花紫
    DEFAULT_BLUE = "#0078D7"  # 默认蓝
    NAVY_BLUE = "#0063B1"  # 海军蓝
    PURPLE_SHADOW = "#8E8CD8"  # 紫影色
    PURPLE_SHADOW_DARK = "#6B69D6"  # 深紫影色
    IRIS_PASTEL = "#8764B8"  # 鸢尾花淡紫
    IRIS_SPRING = "#744DA9"  # 春天鸢尾紫
    VIOLET_RED_LIGHT = "#B146C2"  # 浅紫红
    VIOLET_RED = "#881798"  # 紫红色
    COOL_BLUE_BRIGHT = "#0099BC"  # 明亮冷蓝
    COOL_BLUR = "#2D7D9A"  # 冷蓝
    SEAFOAM = "#00B7C3"  # 海沫蓝
    SEAFOAM_TEAL = "#038387"  # 海沫青
    MINT_LIGHT = "#00B294"  # 浅薄荷绿
    MINT_DARK = "#018574"  # 深薄荷绿
    TURF_GREEN = "#00CC6A"  # 草坪绿
    SPORT_GREEN = "#10893E"  # 运动绿
    GRAY = "#7A7574"  # 灰色
    GRAY_BROWN = "#5D5A58"  # 灰棕色
    STEAL_BLUE = "#68768A"  # 钢蓝色
    METAL_BLUE = "#515C6B"  # 金属蓝
    PALE_MOSS = "#567C73"  # 浅苔绿
    MOSS = "#486860"  # 苔绿色
    MEADOW_GREEN = "#498205"  # 草地绿
    GREEN = "#107C10"  # 绿色
    OVERCAST = "#767676"  # 阴云灰
    STORM = "#4C4A48"  # 暴风灰
    BLUE_GRAY = "#69797E"  # 蓝灰色
    GRAY_DARK = "#4A5459"  # 深灰色
    LIDDY_GREEN = "#647C64"  # 莲叶绿
    SAGE = "#525E54"  # 鼠尾草绿
    CAMOUFLAGE_DESERT = "#847545"  # 沙漠迷彩色
    CAMOUFLAGE = "#7E735F"  # 迷彩色

    def color(self):
        return QColor(self.value)
