# -*- coding: utf-8 -*-
"""
日志面板组件

QTextEdit 只读日志显示，支持颜色分级、自动滚动、导出。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                              QPushButton, QFileDialog)
from PyQt6.QtGui import QTextCursor, QColor, QFont
from PyQt6.QtCore import pyqtSlot, Qt
from datetime import datetime


# 日志级别颜色映射
LEVEL_COLORS = {
    'DEBUG':    '#888888',
    'INFO':     '#D4D4D4',
    'SUCCESS':  '#4EC94E',
    'WARNING':  '#E5C07B',
    'ERROR':    '#E06C75',
    'CRITICAL': '#FF0000',
}


class LogPanel(QWidget):
    """
    日志面板组件。

    功能:
    - 颜色分级显示（INFO=灰白, WARNING=黄, ERROR=红, SUCCESS=绿）
    - 自动滚动到底部
    - 清除 / 复制 / 导出按钮
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 日志文本区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont('Consolas', 10))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #161A22;
                color: #CFD8DC;
                border: 1px solid #2B3342;
                border-radius: 8px;
                padding: 6px;
                selection-background-color: #3498DB;
            }
            QTextEdit QScrollBar:vertical {
                background: transparent; width: 6px; margin: 0px;
            }
            QTextEdit QScrollBar::handle:vertical {
                background: #4A5568; border-radius: 3px;
            }
        """)
        self.text_edit.setMinimumHeight(80)
        layout.addWidget(self.text_edit)

        # 日志面板局部暗色样式
        self.setStyleSheet("""
            QPushButton {
                background-color: #2A303C;
                color: #A0AAB2;
                border: 1px solid #3B4252;
                border-radius: 4px;
                padding: 4px 10px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #3B4252;
                color: #FFFFFF;
                border: 1px solid #4C566A;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
            QPushButton:disabled {
                background-color: transparent;
                border: none;
                color: #4C566A;
            }
        """)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_clear = QPushButton("清除")
        self.btn_clear.setFixedWidth(60)
        self.btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_copy = QPushButton("复制")
        self.btn_copy.setFixedWidth(60)
        self.btn_copy.clicked.connect(self.copy_all)
        btn_layout.addWidget(self.btn_copy)

        self.btn_export = QPushButton("导出日志")
        self.btn_export.setFixedWidth(80)
        self.btn_export.clicked.connect(self.export_log)
        btn_layout.addWidget(self.btn_export)

        btn_layout.addStretch()

        # 日志计数
        self.log_count_label = QPushButton("0 条日志")
        self.log_count_label.setFlat(True)
        self.log_count_label.setEnabled(False)
        btn_layout.addWidget(self.log_count_label)

        layout.addLayout(btn_layout)

        self._log_count = 0

    @pyqtSlot(str, str)
    def append_log(self, message: str, level: str = 'INFO'):
        """
        追加一条日志。

        Args:
            message: 日志内容
            level: 级别（DEBUG/INFO/SUCCESS/WARNING/ERROR/CRITICAL）
        """
        color = LEVEL_COLORS.get(level.upper(), LEVEL_COLORS['INFO'])
        timestamp = datetime.now().strftime('%H:%M:%S')
        html = (f'<span style="color:{color}">'
                f'[{timestamp}] [{level.upper():^8s}] {message}</span>')
        self.text_edit.append(html)

        # 自动滚动
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)

        self._log_count += 1
        self.log_count_label.setText(f"{self._log_count} 条日志")

    def clear(self):
        """清除所有日志"""
        self.text_edit.clear()
        self._log_count = 0
        self.log_count_label.setText("0 条日志")

    def copy_all(self):
        """复制所有日志到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        text = self.text_edit.toPlainText()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
        self.append_log("日志已复制到剪贴板", "SUCCESS")

    def export_log(self):
        """导出日志到文件"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出日志", f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)")
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            self.append_log(f"日志已导出到: {filepath}", "SUCCESS")
