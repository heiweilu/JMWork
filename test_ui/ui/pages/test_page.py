# -*- coding: utf-8 -*-
"""
硬件测试页面（预留骨架）

角度测试 / 梯形坐标测试 — 需要 dlpc843x SDK，当前仅提供 UI 框架。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                              QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt


class TestPage(QWidget):
    """硬件测试页面（预留）"""

    def __init__(self, log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title = QLabel("硬件测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # 提示信息
        notice = QGroupBox("注意")
        notice_layout = QVBoxLayout(notice)
        notice_label = QLabel(
            "此功能需要连接 DLPC84xx Display Controller 硬件设备，\n"
            "并安装 dlpc843x Python SDK。\n\n"
            "当前环境未检测到硬件 SDK，功能暂时禁用。\n"
            "请联系开发人员完成硬件环境配置后使用。"
        )
        notice_label.setWordWrap(True)
        notice_label.setStyleSheet("color: #E65100; font-size: 13px; line-height: 1.6;")
        notice_layout.addWidget(notice_label)
        layout.addWidget(notice)

        # 预留功能入口
        for name, desc in [
            ("角度测试（Angle Test）",
             "从象限 TXT 文件读取 Yaw/Pitch + 梯形校正坐标，逐点下发到 DLP 硬件并回读验证。"
             "支持断点续传、范围过滤、步长配置。"),
            ("梯形坐标测试（Trapezoid Test）",
             "两种模式：file 模式从 TXT 读取四角像素坐标逐行下发；"
             "scan 模式按坐标范围逐步扫描。向硬件写入 KeystoneCorners 并回读比较。"),
        ]:
            group = QGroupBox(name)
            group_layout = QVBoxLayout(group)
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666;")
            group_layout.addWidget(desc_label)

            btn = QPushButton("  执行  ")
            btn.setEnabled(False)
            btn.setToolTip("需要硬件 SDK 支持")
            btn_row = QHBoxLayout()
            btn_row.addWidget(btn)
            btn_row.addStretch()
            group_layout.addLayout(btn_row)

            layout.addWidget(group)

        layout.addStretch()

    def refresh_modules(self):
        """刷新（预留）"""
        pass
