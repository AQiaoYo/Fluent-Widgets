# coding:utf-8
# 标准库导入
from io import BytesIO
from math import floor
from typing import Union

# 第三方库导入
import numpy as np
from PIL import Image
from colorthief import ColorThief
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QBuffer, QIODevice
from scipy.ndimage.filters import gaussian_filter

from .exception_handler import exceptionHandler


def gaussianBlur(
    image: Union[str, QPixmap], blurRadius: int = 18, brightFactor: float = 1, blurPicSize: Union[tuple, None] = None
) -> QPixmap:
    """
    对图像应用高斯模糊, 返回一个模糊后的QPixmap对象

    参数
    ----------
    image: str or QPixmap
        输入的图像, 可以是图像路径字符串或QPixmap对象
    blurRadius: int, optional
        高斯模糊的半径, 默认值为18
    brightFactor: float, optional
        控制图像亮度的因子, 默认值为1
    blurPicSize: tuple, optional
        用于调整图像大小的目标尺寸, 默认为None

    返回
    -------
    QPixmap
        返回应用高斯模糊后的QPixmap对象
    """
    # 如果输入是路径字符串, 打开图像
    if isinstance(image, str) and not image.startswith(":"):
        image = Image.open(image)
    else:
        image = fromqpixmap(QPixmap(image))

    # 如果指定了图像大小, 调整图像尺寸以减少计算量
    if blurPicSize:
        w, h = image.size
        ratio = min(blurPicSize[0] / w, blurPicSize[1] / h)
        w_, h_ = w * ratio, h * ratio

        if w_ < w:
            image = image.resize((int(w_), int(h_)), Image.ANTIALIAS)

    image = np.array(image)

    # 如果是灰度图像, 将其转为RGB图像
    if len(image.shape) == 2:
        image = np.stack([image, image, image], axis=-1)

    # 对每个通道应用高斯模糊
    for i in range(3):
        image[:, :, i] = gaussian_filter(image[:, :, i], blurRadius) * brightFactor

    # 将ndarray转换为QPixmap
    h, w, c = image.shape
    if c == 3:
        format = QImage.Format_RGB888
    else:
        format = QImage.Format_RGBA8888

    return QPixmap.fromImage(QImage(image.data, w, h, c * w, format))


def fromqpixmap(im: Union[QImage, QPixmap]) -> Image:
    """
    将QImage或QPixmap对象转换为PIL Image对象

    参数
    ----------
    im: QImage or QPixmap
        输入的QImage或QPixmap对象

    返回
    -------
    Image
        返回转换后的PIL Image对象
    """
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)

    # 如果图像有Alpha通道, 保存为PNG, 否则保存为PPM格式
    if im.hasAlphaChannel():
        im.save(buffer, "png")
    else:
        im.save(buffer, "ppm")

    b = BytesIO()
    b.write(buffer.data())
    buffer.close()
    b.seek(0)

    return Image.open(b)


class DominantColor:
    """提取图像主色的类"""

    @classmethod
    @exceptionHandler((24, 24, 24))
    def getDominantColor(cls, imagePath: str) -> tuple[int, int, int]:
        """
        提取图像的主色

        参数
        ----------
        imagePath: str
            图像的路径

        返回
        -------
        r, g, b: int
            主色的RGB值
        """
        # 如果路径以 ":" 开头, 返回默认的深色值
        if imagePath.startswith(":"):
            return (24, 24, 24)

        colorThief = ColorThief(imagePath)

        # 如果图像尺寸大于400, 缩小图像以加快计算速度
        if max(colorThief.image.size) > 400:
            colorThief.image = colorThief.image.resize((400, 400))

        # 获取调色板
        palette = colorThief.get_palette(quality=9)

        # 调整调色板的亮度
        palette = cls.__adjustPaletteValue(palette)

        # 移除色调值较低的颜色
        for rgb in palette[:]:
            h, s, v = cls.rgb2hsv(rgb)
            if h < 0.02:
                palette.remove(rgb)
                if len(palette) <= 2:
                    break

        palette = palette[:5]
        # 按颜色的鲜艳度排序, 选择最鲜艳的颜色
        palette.sort(key=lambda rgb: cls.colorfulness(*rgb), reverse=True)

        return palette[0]

    @classmethod
    def __adjustPaletteValue(cls, palette: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
        """
        调整调色板中每个颜色的亮度

        参数
        ----------
        palette: list of tuple
            调色板中的RGB值列表

        返回
        -------
        list of tuple
            调整后的调色板
        """
        newPalette = []
        for rgb in palette:
            h, s, v = cls.rgb2hsv(rgb)
            # 根据亮度调整色值
            if v > 0.9:
                factor = 0.8
            elif 0.8 < v <= 0.9:
                factor = 0.9
            elif 0.7 < v <= 0.8:
                factor = 0.95
            else:
                factor = 1
            v *= factor
            newPalette.append(cls.hsv2rgb(h, s, v))

        return newPalette

    @staticmethod
    def rgb2hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """
        将RGB颜色值转换为HSV

        参数
        ----------
        rgb: tuple of int
            输入的RGB值

        返回
        -------
        tuple of float
            转换后的HSV值
        """
        r, g, b = [i / 255 for i in rgb]
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        s = 0 if mx == 0 else df / mx
        v = mx
        return (h, s, v)

    @staticmethod
    def hsv2rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
        """
        将HSV颜色值转换为RGB

        参数
        ----------
        h: float
            色调值
        s: float
            饱和度值
        v: float
            亮度值

        返回
        -------
        tuple of int
            转换后的RGB值
        """
        h60 = h / 60.0
        h60f = floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0:
            r, g, b = v, t, p
        elif hi == 1:
            r, g, b = q, v, p
        elif hi == 2:
            r, g, b = p, v, t
        elif hi == 3:
            r, g, b = p, q, v
        elif hi == 4:
            r, g, b = t, p, v
        elif hi == 5:
            r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return (r, g, b)

    @staticmethod
    def colorfulness(r: int, g: int, b: int) -> float:
        """
        计算颜色的鲜艳度

        参数
        ----------
        r: int
            红色通道值
        g: int
            绿色通道值
        b: int
            蓝色通道值

        返回
        -------
        float
            鲜艳度值
        """
        rg = np.absolute(r - g)
        yb = np.absolute(0.5 * (r + g) - b)

        # 计算`rg`和`yb`的均值和标准差
        rg_mean, rg_std = (np.mean(rg), np.std(rg))
        yb_mean, yb_std = (np.mean(yb), np.std(yb))

        # 结合均值和标准差
        std_root = np.sqrt((rg_std**2) + (yb_std**2))
        mean_root = np.sqrt((rg_mean**2) + (yb_mean**2))

        return std_root + (0.3 * mean_root)
