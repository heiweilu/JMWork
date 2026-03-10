# -*- coding: utf-8 -*-
"""
参数编辑面板组件

根据模块的 MODULE_INFO['params'] 定义动态生成参数表单。
"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox,
                              QDoubleSpinBox, QCheckBox, QComboBox,
                              QLabel, QGroupBox, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Any, Dict, List


class ParamEditor(QWidget):
    """
    动态参数编辑面板。

    根据参数定义列表自动生成对应的输入控件:
    - string → QLineEdit
    - int → QSpinBox
    - float → QDoubleSpinBox
    - bool → QCheckBox
    - tuple → 两个 QDoubleSpinBox（范围）
    - choice → QComboBox
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
                {"key": "yaw_range", "label": "Yaw范围", "type": "tuple",
                 "default": (-42, 42), "choices": [...], "min": 0, "max": 100}
        """
        # 清除现有控件
        self._clear()
        self._params_def = params_def

        for param in params_def:
            key = param['key']
            label_text = param.get('label', key)
            ptype = param.get('type', 'string')
            default = param.get('default', '')
            tooltip = param.get('tooltip', '')

            widget = self._create_widget(param)

            # 为控件设置 tooltip
            if tooltip and hasattr(widget, 'setToolTip'):
                widget.setToolTip(tooltip)

            # 构建标签：如有 tooltip 则显示提示图标
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

        # 通知父级布局重新计算尺寸（updateGeometry 比 adjustSize 更安全，
        # 不会在 QScrollArea 内强制覆盖 size manager 的管理）
        self.updateGeometry()

    def _create_widget(self, param: dict) -> QWidget:
        """根据参数类型创建控件"""
        ptype = param.get('type', 'string')
        default = param.get('default', '')

        if ptype == 'int':
            w = QSpinBox()
            w.setRange(param.get('min', -999999), param.get('max', 999999))
            w.setValue(int(default) if default != '' else 0)
            return w

        elif ptype == 'float':
            w = QDoubleSpinBox()
            w.setRange(param.get('min', -999999.0), param.get('max', 999999.0))
            w.setDecimals(param.get('decimals', 2))
            w.setValue(float(default) if default != '' else 0.0)
            return w

        elif ptype == 'bool':
            w = QCheckBox()
            w.setChecked(bool(default))
            return w

        elif ptype in ('choice', 'combo'):
            w = QComboBox()
            # 同时兑容 'options' 和 'choices' 两种键名
            choices = param.get('options', param.get('choices', []))
            # values 存储实际小，缺省等于显示标签本身
            values = param.get('values', choices)
            options_str = [str(c) for c in choices]
            w.addItems(options_str)
            # 按实际値匹配默认选中项
            default_str = str(default)
            try:
                default_idx = [str(v) for v in values].index(default_str)
                w.setCurrentIndex(default_idx)
            except ValueError:
                if options_str:
                    w.setCurrentIndex(0)
            # 把 values 存到 widget 上，起値时用实际値
            w._values = [str(v) for v in values]
            return w

        elif ptype == 'tuple':
            # 两个输入框表示范围
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

        else:  # string
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
            key = param['key']
            ptype = param.get('type', 'string')
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
                # 如果有 _values，返回实际値；否则返回显示文本
                if hasattr(widget, '_values'):
                    idx = widget.currentIndex()
                    result[key] = widget._values[idx] if 0 <= idx < len(widget._values) else widget.currentText()
                else:
                    result[key] = widget.currentText()
            elif ptype == 'tuple':
                result[key] = (widget._spin1.value(), widget._spin2.value())
            else:
                result[key] = widget.text()

        return result

    def _clear(self):
        """清除所有控件（立即删除，避免 deleteLater 异步导致显示异常）"""
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # 立即移除，而非 deleteLater
        self._widgets.clear()
        self._params_def.clear()
