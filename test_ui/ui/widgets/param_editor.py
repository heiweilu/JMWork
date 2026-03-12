# -*- coding: utf-8 -*-
"""
参数编辑面板组件

根据模块的 MODULE_INFO['params'] 定义动态生成参数表单。
"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox,
                              QDoubleSpinBox, QCheckBox, QComboBox,
                              QLabel, QVBoxLayout, QHBoxLayout,
                              QPlainTextEdit, QToolButton, QFileDialog)
from PyQt6.QtCore import Qt
from typing import Any, Dict, List


class _PathWidget(QWidget):
    """文件/目录路径输入控件，支持拖拽 + 浏览按钮。"""

    def __init__(self, default: str = '', is_dir: bool = False, parent=None):
        super().__init__(parent)
        self._is_dir = is_dir
        self.setAcceptDrops(True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._edit = QLineEdit(str(default) if default else '')
        if is_dir:
            self._edit.setPlaceholderText('拖入目录或点击 📂 浏览…')
        else:
            self._edit.setPlaceholderText('拖入文件或点击 📂 浏览…')
        lay.addWidget(self._edit, stretch=1)

        btn = QToolButton()
        btn.setText('📂')
        btn.setFixedWidth(30)
        btn.setToolTip('浏览选择…')
        btn.clicked.connect(self._browse)
        lay.addWidget(btn)

    # ----- 公共 API（模仿 QLineEdit） -----
    def text(self) -> str:
        return self._edit.text()

    def setText(self, t: str):
        self._edit.setText(t)

    def setToolTip(self, tip: str):  # noqa: N802
        self._edit.setToolTip(tip)

    # ----- 浏览 -----
    def _browse(self):
        if self._is_dir:
            p = QFileDialog.getExistingDirectory(self, '选择目录')
        else:
            p, _ = QFileDialog.getOpenFileName(
                self, '选择文件', '',
                'CSV / TXT (*.csv *.txt);;All Files (*)'
            )
        if p:
            self._edit.setText(p.replace('\\', '/'))

    # ----- 拖拽 -----
    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            self._edit.setText(urls[0].toLocalFile().replace('\\', '/'))


class ParamEditor(QWidget):
    """
    动态参数编辑面板。

    根据参数定义列表自动生成对应的输入控件:
    - string   → QLineEdit（单行文本）
    - textarea → QPlainTextEdit（多行文本，支持粘贴多行坐标）
    - int      → QSpinBox
    - float    → QDoubleSpinBox
    - bool     → QCheckBox
    - tuple    → 两个 QDoubleSpinBox（范围）
    - choice / combo → QComboBox
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets: Dict[str, QWidget] = {}
        self._params_def: List[dict] = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._form_layout = QFormLayout()
        self._form_layout.setSpacing(10)
        self._form_layout.setContentsMargins(4, 4, 4, 4)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._layout.addLayout(self._form_layout)
        self._layout.addStretch()

    def set_params(self, params_def: List[dict]):
        """
        设置参数定义并生成表单。

        Args:
            params_def: 参数定义列表，每项格式:
                {"key": "name", "label": "显示名", "type": "float",
                 "default": 1.0, "tooltip": "说明文字"}
        """
        self._clear()
        # 使用副本，避免在切换模块时误修改原始 MODULE_INFO['params'] 列表
        self._params_def = [dict(p) for p in params_def]

        for param in self._params_def:
            key = param['key']
            label_text = param.get('label', key)
            tooltip = param.get('tooltip', '')

            widget = self._create_widget(param)

            if tooltip and hasattr(widget, 'setToolTip'):
                widget.setToolTip(tooltip)

            if tooltip:
                label_widget = QLabel(
                    f"{label_text} <span style='color:#2196F3; font-size:10px'>ⓘ</span>:"
                )
                label_widget.setTextFormat(Qt.TextFormat.RichText)
                label_widget.setToolTip(tooltip)
                self._form_layout.addRow(label_widget, widget)
            else:
                self._form_layout.addRow(f"{label_text}:", widget)

            self._widgets[key] = widget

        self.adjustSize()
        self.updateGeometry()
        self.repaint()

    def _create_widget(self, param: dict) -> QWidget:
        """根据参数类型创建控件"""
        ptype   = param.get('type', 'string')
        default = param.get('default', '')

        if ptype == 'int':
            w = QSpinBox()
            w.setRange(param.get('min', -999999), param.get('max', 999999))
            w.setValue(int(default) if default != '' else 0)
            return w

        if ptype == 'float':
            w = QDoubleSpinBox()
            w.setRange(param.get('min', -999999.0), param.get('max', 999999.0))
            w.setDecimals(param.get('decimals', 2))
            w.setValue(float(default) if default != '' else 0.0)
            return w

        if ptype == 'bool':
            w = QCheckBox()
            w.setChecked(bool(default))
            return w

        if ptype in ('choice', 'combo'):
            w = QComboBox()
            choices = param.get('options', param.get('choices', []))
            values  = param.get('values', choices)
            options_str = [str(c) for c in choices]
            w.addItems(options_str)
            default_str = str(default)
            try:
                default_idx = [str(v) for v in values].index(default_str)
                w.setCurrentIndex(default_idx)
            except ValueError:
                if options_str:
                    w.setCurrentIndex(0)
            w._values = [str(v) for v in values]
            return w

        if ptype == 'tuple':
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            w1 = QDoubleSpinBox()
            w1.setRange(-999, 999)
            w2 = QDoubleSpinBox()
            w2.setRange(-999, 999)
            if isinstance(default, (list, tuple)) and len(default) == 2:
                w1.setValue(float(default[0]))
                w2.setValue(float(default[1]))
            layout.addWidget(w1)
            layout.addWidget(QLabel("~"))
            layout.addWidget(w2)
            container._spin1 = w1
            container._spin2 = w2
            return container

        if ptype == 'textarea':
            w = QPlainTextEdit()
            w.setPlainText(str(default))
            w.setFixedHeight(72)
            w.setStyleSheet(
                "QPlainTextEdit { font-family: Consolas, monospace; font-size: 12px; }"
            )
            return w

        # string (default) —— 如果 key/tooltip 涉及路径，用 _PathWidget
        key = param.get('key', '')
        tooltip_lc = param.get('tooltip', '').lower()
        is_path = (
            key.endswith(('_path', '_file', '_dir'))
            or param.get('subtype') in ('path', 'file', 'dir')
            or '路径' in param.get('tooltip', '')
            or 'path' in tooltip_lc
            or 'file' in tooltip_lc
        )
        if is_path:
            is_dir = key.endswith('_dir') or param.get('subtype') == 'dir'
            return _PathWidget(default=str(default) if default else '', is_dir=is_dir)
        w = QLineEdit()
        w.setText(str(default))
        return w

    def get_values(self) -> Dict[str, Any]:
        """
        获取当前所有参数值。

        Returns:
            {key: value} 字典
        """
        result = {}
        for param in self._params_def:
            key    = param['key']
            ptype  = param.get('type', 'string')
            widget = self._widgets.get(key)
            if widget is None:
                continue

            if ptype == 'int':
                result[key] = widget.value()
            elif ptype == 'float':
                result[key] = widget.value()
            elif ptype == 'bool':
                result[key] = widget.isChecked()
            elif ptype in ('choice', 'combo'):
                if hasattr(widget, '_values'):
                    idx = widget.currentIndex()
                    result[key] = (widget._values[idx]
                                   if 0 <= idx < len(widget._values)
                                   else widget.currentText())
                else:
                    result[key] = widget.currentText()
            elif ptype == 'tuple':
                result[key] = (widget._spin1.value(), widget._spin2.value())
            elif ptype == 'textarea':
                result[key] = widget.toPlainText()
            elif isinstance(widget, _PathWidget):
                result[key] = widget.text()
            else:
                result[key] = widget.text()

        return result

    def _clear(self):
        """清除所有控件"""
        while self._form_layout.rowCount() > 0:
            self._form_layout.removeRow(0)
        self._widgets.clear()
        self._params_def = []
