# -*- coding: utf-8 -*-
"""
配置管理页面

表格式编辑器展示所有配置项，支持编辑/保存/恢复默认。
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox, QFileDialog,
                              QAbstractItemView)
from PyQt6.QtCore import Qt

from core.config_manager import ConfigManager, CONFIG_DESCRIPTIONS, CONFIG_TYPES


class ConfigPage(QWidget):
    """配置管理页面"""

    def __init__(self, config_mgr: ConfigManager = None, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 标题
        title = QLabel("配置管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("管理常用参数（屏幕分辨率、角度范围、步长、输出路径等）。修改后点击「保存」生效。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 8px;")
        layout.addWidget(desc)

        # 配置表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["配置项", "当前值", "类型", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 按钮栏
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("  保存配置  ")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        self.btn_reset = QPushButton("恢复默认")
        self.btn_reset.setObjectName("btn_danger")
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._load_config)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_config(self):
        """加载配置到表格"""
        if not self._config_mgr:
            return

        flat = self._config_mgr.get_flat()
        self.table.setRowCount(len(flat))

        for row, (key, value) in enumerate(sorted(flat.items())):
            # 配置项名
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, key_item)

            # 当前值（可编辑）
            val_item = QTableWidgetItem(str(value))
            self.table.setItem(row, 1, val_item)

            # 类型
            type_str = CONFIG_TYPES.get(key, 'string')
            type_item = QTableWidgetItem(type_str)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

            # 描述
            desc = CONFIG_DESCRIPTIONS.get(key, '')
            desc_item = QTableWidgetItem(desc)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, desc_item)

    def showEvent(self, event):
        """页面显示时刷新配置"""
        super().showEvent(event)
        self._load_config()

    def _on_save(self):
        """保存配置"""
        if not self._config_mgr:
            return

        try:
            for row in range(self.table.rowCount()):
                key = self.table.item(row, 0).text()
                value_str = self.table.item(row, 1).text()
                type_str = CONFIG_TYPES.get(key, 'string')

                # 类型转换
                if type_str == 'int':
                    value = int(value_str)
                elif type_str == 'float':
                    value = float(value_str)
                elif type_str == 'bool':
                    value = value_str.lower() in ('true', '1', 'yes')
                elif type_str == 'tuple':
                    # "[1, 2]" or "(1, 2)" → list
                    import json
                    value = json.loads(value_str.replace('(', '[').replace(')', ']'))
                else:
                    value = value_str

                self._config_mgr.set(key, value)

            self._config_mgr.save()

            if self._log_panel:
                self._log_panel.append_log("配置已保存", "SUCCESS")
            QMessageBox.information(self, "成功", "配置已保存")

        except Exception as e:
            if self._log_panel:
                self._log_panel.append_log(f"保存配置失败: {e}", "ERROR")
            QMessageBox.critical(self, "错误", f"保存失败:\n{e}")

    def _on_reset(self):
        """恢复默认配置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要恢复所有配置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self._config_mgr.reset()
            self._load_config()
            if self._log_panel:
                self._log_panel.append_log("配置已恢复默认", "WARNING")
