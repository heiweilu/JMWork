# -*- coding: utf-8 -*-
"""配置管理页面。"""

import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QScrollArea, QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QFrame
)

from core.config_manager import ConfigManager, CONFIG_DESCRIPTIONS, CONFIG_TYPES


GROUP_TITLES = {
    'general': '基础设置',
    'screen': '屏幕参数',
    'angle': '角度参数',
    'test': '测试行为',
    'visualization': '可视化输出',
    'paths': '目录路径',
}


class ConfigPage(QWidget):
    """配置管理页面。"""

    def __init__(self, config_mgr: ConfigManager = None, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._editors = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel('配置管理')
        title.setStyleSheet('font-size: 16px; font-weight: bold;')
        layout.addWidget(title)

        desc = QLabel(
            '按功能分组管理常用配置。界面只展示中文说明，保存时会自动写回内部配置键。'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet('color: #666; margin-bottom: 8px;')
        layout.addWidget(desc)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll, 1)

        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton('  保存配置  ')
        self.btn_save.setObjectName('btn_primary')
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        self.btn_reset = QPushButton('恢复默认')
        self.btn_reset.setObjectName('btn_danger')
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)

        self.btn_refresh = QPushButton('刷新')
        self.btn_refresh.clicked.connect(self._load_config)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _create_editor(self, key: str, value):
        type_str = CONFIG_TYPES.get(key, 'string')
        if type_str == 'int':
            editor = QSpinBox()
            editor.setRange(-1_000_000, 1_000_000)
            editor.setValue(int(value))
            return editor
        if type_str == 'float':
            editor = QDoubleSpinBox()
            editor.setRange(-1_000_000.0, 1_000_000.0)
            editor.setDecimals(4)
            editor.setValue(float(value))
            return editor
        if type_str == 'bool':
            editor = QCheckBox('启用')
            editor.setChecked(bool(value))
            return editor
        if type_str == 'tuple':
            editor = QLineEdit(json.dumps(list(value), ensure_ascii=False))
            editor.setPlaceholderText('例如: [ -42, 42 ]')
            return editor
        if type_str == 'path':
            editor = QLineEdit(str(value))
            editor.setPlaceholderText('支持相对路径或绝对路径')
            return editor
        if isinstance(value, str) and len(value) > 60:
            editor = QTextEdit()
            editor.setFixedHeight(72)
            editor.setPlainText(value)
            return editor
        editor = QLineEdit(str(value))
        return editor

    def _get_editor_value(self, key: str, editor):
        type_str = CONFIG_TYPES.get(key, 'string')
        if isinstance(editor, QSpinBox):
            return int(editor.value())
        if isinstance(editor, QDoubleSpinBox):
            return float(editor.value())
        if isinstance(editor, QCheckBox):
            return bool(editor.isChecked())
        if isinstance(editor, QTextEdit):
            value_str = editor.toPlainText().strip()
        else:
            value_str = editor.text().strip()
        if type_str == 'tuple':
            return json.loads(value_str.replace('(', '[').replace(')', ']'))
        if type_str == 'int':
            return int(value_str)
        if type_str == 'float':
            return float(value_str)
        if type_str == 'bool':
            return value_str.lower() in ('true', '1', 'yes')
        return value_str

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _load_config(self):
        if not self._config_mgr:
            return
        self._clear_content()
        self._editors.clear()

        flat = self._config_mgr.get_flat()
        grouped = {}
        for key, value in sorted(flat.items()):
            group = key.split('.', 1)[0]
            grouped.setdefault(group, []).append((key, value))

        for group, items in grouped.items():
            box = QGroupBox(GROUP_TITLES.get(group, group))
            form = QFormLayout(box)
            form.setContentsMargins(12, 12, 12, 12)
            form.setSpacing(10)
            for key, value in items:
                editor = self._create_editor(key, value)
                editor.setToolTip(CONFIG_DESCRIPTIONS.get(key, ''))
                label = QLabel(CONFIG_DESCRIPTIONS.get(key, key))
                label.setToolTip(key)
                form.addRow(label, editor)
                self._editors[key] = editor
            self._content_layout.addWidget(box)

        self._content_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_config()

    def _on_save(self):
        if not self._config_mgr:
            return
        try:
            for key, editor in self._editors.items():
                self._config_mgr.set(key, self._get_editor_value(key, editor))
            self._config_mgr.save()
            if self._log_panel:
                self._log_panel.append_log('配置已保存', 'SUCCESS')
            QMessageBox.information(self, '成功', '配置已保存')
        except Exception as e:
            if self._log_panel:
                self._log_panel.append_log(f'保存配置失败: {e}', 'ERROR')
            QMessageBox.critical(self, '错误', f'保存失败:\n{e}')

    def _on_reset(self):
        reply = QMessageBox.question(
            self,
            '确认',
            '确定要恢复所有配置为默认值吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config_mgr.reset()
            self._load_config()
            if self._log_panel:
                self._log_panel.append_log('配置已恢复默认', 'WARNING')
