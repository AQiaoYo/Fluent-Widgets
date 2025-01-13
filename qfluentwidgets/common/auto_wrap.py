# 标准库导入
from re import sub
from enum import Enum, auto
from typing import List, Tuple, Optional, Generator
from functools import lru_cache
from unicodedata import east_asian_width


class CharType(Enum):
    """字符类型枚举类"""

    SPACE = auto()  # 空格字符
    ASIAN = auto()  # 东亚宽字符（全角字符）
    LATIN = auto()  # 拉丁字符（半角字符）


class TextWrap:
    """文本自动换行处理"""

    # 字符宽度表，定义东亚宽字符和其他字符的宽度
    EAST_ASAIN_WIDTH_TABLE = {
        "F": 2,  # 全角字符
        "H": 1,  # 半角字符
        "W": 2,  # 宽字符
        "A": 1,  # 模糊宽度字符
        "N": 1,  # 非东亚字符
        "Na": 1,  # 非东亚字符
    }

    @classmethod
    @lru_cache(maxsize=128)
    def get_width(cls, char: str) -> int:
        """获取单个字符的显示宽度

        此方法使用了 lru_cache 装饰器，缓存最近 128 次的调用结果以提高性能。

        Parameters
        ----------
        char: str
            单个字符

        Returns
        -------
        int
            字符宽度
        """
        return cls.EAST_ASAIN_WIDTH_TABLE.get(east_asian_width(char), 1)

    @classmethod
    @lru_cache(maxsize=32)
    def get_text_width(cls, text: str) -> int:
        """获取字符串的总显示宽度

        此方法使用了 lru_cache 装饰器，缓存最近 32 次的调用结果以提高性能。

        Parameters
        ----------
        text: str
            输入字符串

        Returns
        -------
        int
            字符串总宽度
        """
        return sum(cls.get_width(char) for char in text)

    @classmethod
    @lru_cache(maxsize=128)
    def get_char_type(cls, char: str) -> CharType:
        """获取字符的类型

        此方法使用了 lru_cache 装饰器，缓存最近 128 次的调用结果以提高性能。

        Parameters
        ----------
        char: str
            单个字符

        Returns
        -------
        CharType
            字符类型（空格、东亚字符或拉丁字符）
        """
        if char.isspace():
            return CharType.SPACE

        if cls.get_width(char) == 1:
            return CharType.LATIN

        return CharType.ASIAN

    @classmethod
    def process_text_whitespace(cls, text: str) -> str:
        """处理字符串中的多余空格

        该方法会去除字符串中的多余空白字符，并移除首尾空格。

        Parameters
        ----------
        text: str
            输入字符串

        Returns
        -------
        str
            处理后的字符串
        """
        return sub(pattern=r"\s+", repl=" ", string=text).strip()

    @classmethod
    @lru_cache(maxsize=32)
    def split_long_token(cls, token: str, width: int) -> List[str]:
        """将超过指定宽度的单词分割为多个小段

        此方法使用了 lru_cache 装饰器，缓存最近 32 次的调用结果以提高性能。

        Parameters
        ----------
        token: str
            要分割的单词

        width: int
            最大允许宽度

        Returns
        -------
        List[str]
            分割后的单词列表
        """
        return [token[i : i + width] for i in range(0, len(token), width)]

    @classmethod
    def tokenizer(cls, text: str) -> Generator[str, None, None]:
        """对文本进行分词

        根据字符类型（空格、东亚字符或拉丁字符）对文本进行分词。

        Parameters
        ----------
        text: str
            输入文本

        Returns
        -------
        Generator[str, None, None]
            生成分割后的单词
        """
        buffer = ""
        last_char_type: Optional[CharType] = None

        for char in text:
            char_type = cls.get_char_type(char)

            # 如果当前缓冲区有内容，且当前字符类型与上一个字符类型不同，或当前字符不是拉丁字符
            if buffer and (char_type != last_char_type or char_type != CharType.LATIN):
                yield buffer
                buffer = ""

            buffer += char
            last_char_type = char_type

        yield buffer  # 处理最后的缓冲区内容

    @classmethod
    def wrap(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """根据指定宽度自动换行

        Parameters
        ----------
        text: str
            待处理文本

        width: int
            每行的最大宽度，东亚字符宽度为 2

        once: bool
            是否只换行一次

        Returns
        -------
        Tuple[str, bool]
            包含换行后的文本和是否发生换行的布尔值
        """
        width = int(width)
        lines = text.splitlines()  # 按行分割文本
        is_wrapped = False
        wrapped_lines = []

        for line in lines:
            line = cls.process_text_whitespace(line)

            # 如果行的宽度超过限制
            if cls.get_text_width(line) > width:
                wrapped_line, is_wrapped = cls._wrap_line(line, width, once)
                wrapped_lines.append(wrapped_line)

                if once:
                    # 如果只换行一次，处理剩余部分
                    wrapped_lines.append(text[len(wrapped_line) :].rstrip())
                    return "".join(wrapped_lines), is_wrapped
            else:
                wrapped_lines.append(line)

        return "\n".join(wrapped_lines), is_wrapped

    @classmethod
    def _wrap_line(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """处理单行文本的换行逻辑

        Parameters
        ----------
        text: str
            输入文本

        width: int
            最大宽度

        once: bool
            是否只换行一次

        Returns
        -------
        Tuple[str, bool]
            包含处理后的文本和是否发生换行的布尔值
        """
        line_buffer = ""
        wrapped_lines = []
        current_width = 0

        for token in cls.tokenizer(text):
            token_width = cls.get_text_width(token)

            # 跳过开头的空格
            if token == " " and current_width == 0:
                continue

            # 如果当前行剩余空间足够容纳当前单词
            if current_width + token_width <= width:
                line_buffer += token
                current_width += token_width

                # 当前宽度正好等于指定宽度时，换行
                if current_width == width:
                    wrapped_lines.append(line_buffer.rstrip())
                    line_buffer = ""
                    current_width = 0
            else:
                # 当前行剩余空间不足时，换行
                if current_width != 0:
                    wrapped_lines.append(line_buffer.rstrip())

                chunks = cls.split_long_token(token, width)

                # 分割后的所有段落，除了最后一段都直接换行
                for chunk in chunks[:-1]:
                    wrapped_lines.append(chunk.rstrip())

                # 最后一段保留到当前缓冲区
                line_buffer = chunks[-1]
                current_width = cls.get_text_width(chunks[-1])

        if current_width != 0:
            wrapped_lines.append(line_buffer.rstrip())

        if once:
            # 如果只换行一次，合并后返回
            return "\n".join([wrapped_lines[0], " ".join(wrapped_lines[1:])]), True

        return "\n".join(wrapped_lines), True
