"""
语法高亮器模块
用于对Warframe元数据格式进行语法着色
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PySide6.QtWidgets import QApplication
import re


class WarframeSyntaxHighlighter(QSyntaxHighlighter):
    """Warframe元数据格式语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 初始化格式规则
        self.highlighting_rules = []

        # 定义颜色方案
        self._setup_colors()

        # 设置高亮规则
        self._setup_rules()

    def _setup_colors(self):
        """设置颜色方案"""
        # 注释 - 灰色
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(128, 128, 128))  # 灰色

        # 键名 - 蓝色
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor(86, 156, 214))  # 蓝色
        self.key_format.setFontWeight(QFont.Bold)

        # 字符串值 - 浅绿色
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(206, 145, 120))  # 浅棕色（字符串值）

        # 数字值 - 绿色
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(181, 206, 168))  # 浅绿色

        # 布尔值/特殊值 - 紫色
        self.special_value_format = QTextCharFormat()
        self.special_value_format.setForeground(QColor(197, 134, 192))  # 紫色

        # 路径 - 青色
        self.path_format = QTextCharFormat()
        self.path_format.setForeground(QColor(78, 201, 176))  # 青色

        # 结构标记 - 深灰色
        self.struct_format = QTextCharFormat()
        self.struct_format.setForeground(QColor(220, 220, 170))  # 浅黄色

        # 等号 - 白色
        self.equal_format = QTextCharFormat()
        self.equal_format.setForeground(QColor(212, 212, 212))  # 浅灰色

    def _setup_rules(self):
        """设置高亮规则"""
        # 清空规则列表
        self.highlighting_rules = []

        # 规则顺序很重要：更具体的规则应该先应用

        # 规则1: 注释 (以#开头) - 最具体
        comment_pattern = r'#[^\n]*'
        self.highlighting_rules.append((comment_pattern, 0, self.comment_format))

        # 规则2: 带引号的字符串 - 应该优先于其他规则
        quoted_string_pattern = r'"[^"\\]*(\\.[^"\\]*)*"'
        self.highlighting_rules.append((quoted_string_pattern, 0, self.string_format))

        # 规则3: 路径 (以/开头，包含路径字符)
        path_pattern = r'\/[a-zA-Z0-9_/\.\-\+]+'
        self.highlighting_rules.append((path_pattern, 0, self.path_format))

        # 规则4: 键名 (等号左边的部分)
        # 匹配键名，后面跟着等号，但不包括等号
        key_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*=)'
        self.highlighting_rules.append((key_pattern, 1, self.key_format))

        # 规则5: 数字值 (整数或浮点数)
        number_pattern = r'\b\d+\.?\d*\b'
        self.highlighting_rules.append((number_pattern, 0, self.number_format))

        # 规则6: 特殊值/枚举 (大写单词，可能包含下划线)
        # 注意：这个规则应该放在数字后面，避免匹配到纯数字
        special_value_pattern = r'\b[A-Z_][A-Z0-9_]+\b'
        self.highlighting_rules.append((special_value_pattern, 0, self.special_value_format))

        # 规则7: 结构标记 ({ } , =)
        struct_pattern = r'[{}()]|,'
        self.highlighting_rules.append((struct_pattern, 0, self.struct_format))

        # 规则8: 等号 - 单独处理，使用不同的颜色
        equal_pattern = r'='
        self.highlighting_rules.append((equal_pattern, 0, self.equal_format))

    def highlightBlock(self, text):
        """高亮文本块"""
        # 应用所有规则
        for pattern, group, format in self.highlighting_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start = match.start(group)
                length = match.end(group) - start
                self.setFormat(start, length, format)

        # 处理多行注释或特殊结构
        self.setCurrentBlockState(0)