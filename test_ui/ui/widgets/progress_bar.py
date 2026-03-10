# -*- coding: utf-8 -*-
"""
进度条 + 状态文字组件
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QLabel
from PyQt6.QtCore import pyqtSlot, Qt


class ProgressWidget(QWidget):
    """
    进度条 + 状态文字。

    显示格式: [████████░░░░] 75% (7500 / 10000) - 正在执行...
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.status_label = QLabel("就绪")
        self.status_label.setFixedWidth(100)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        self.detail_label = QLabel("")
        self.detail_label.setFixedWidth(160)
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.detail_label)

    @pyqtSlot(int, int)
    def update_progress(self, current: int, total: int):
        """更新进度"""
        if total > 0:
            pct = int(current * 100 / total)
            self.progress_bar.setValue(pct)
            self.detail_label.setText(f"{current} / {total}")
        else:
            self.progress_bar.setRange(0, 0)  # 不确定进度模式
            self.detail_label.setText("")

    def set_status(self, text: str, color: str = '#333'):
        """设置状态文字"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def reset(self):
        """重置进度条"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet("color: #333;")
        self.detail_label.setText("")

    def set_running(self):
        """设置为运行中状态"""
        self.set_status("执行中...", '#2196F3')

    def set_success(self):
        """设置为成功状态"""
        self.progress_bar.setValue(100)
        self.set_status("完成", '#4CAF50')

    def set_error(self):
        """设置为错误状态"""
        self.set_status("错误", '#F44336')

    def set_cancelled(self):
        """设置为已取消状态"""
        self.set_status("已取消", '#FF9800')
