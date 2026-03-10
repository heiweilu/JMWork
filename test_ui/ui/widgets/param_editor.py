# -*- coding: utf-8 -*-
"""
参数编辑面板组件

根据模块的 MODULE_INFO['params'] 定义动态生成参数表单。
"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox,
                              QDoubleSpinBox, QCheckBox, QComboBox,
                              QLabel, QGroupBox, QVBoxLayout)
from PyQt6.QtCore import Qt
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
        self._form_layout = QFormLayout()
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
            label = param.get('label', key)
            ptype = param.get('type', 'string')
            default = param.get('default', '')

            widget = self._create_widget(param)
            self._widgets[key] = widget
            self._form_layout.addRow(f"{label}:", widget)

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

        elif ptype == 'choice':
            w = QComboBox()
            choices = param.get('choices', [])
            w.addItems(choices)
            if default in choices:
                w.setCurrentText(str(default))
            return w

        elif ptype == 'tuple':
            # 两个输入框表示范围
            container = QWidget()
            layout = __import__('PyQt6.QtWidgets', fromlist=['QHBoxLayout']).QHBoxLayout(container)
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
            elif ptype == 'choice':
                result[key] = widget.currentText()
            elif ptype == 'tuple':
                result[key] = (widget._spin1.value(), widget._spin2.value())
            else:
                result[key] = widget.text()

        return result

    def _clear(self):
        """清除所有控件"""
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._widgets.clear()
        self._params_def.clear()
