# -*- coding: utf-8 -*-
"""通用树状工作区容器。"""

from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TreeWorkspace(QWidget):
    """左侧树导航 + 右侧页面栈的通用工作区。"""

    def __init__(self, title: str, description: str = '', parent=None):
        super().__init__(parent)
        self._items: Dict[str, QTreeWidgetItem] = {}
        self._pages: Dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
            layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet('color: #666;')
            layout.addWidget(desc_label)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)

        nav_wrap = QFrame()
        nav_layout = QVBoxLayout(nav_wrap)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)
        nav_hint = QLabel('左侧选择父节点或子节点，右侧显示对应工作区。')
        nav_hint.setWordWrap(True)
        nav_hint.setStyleSheet('color: #667085; font-size: 12px;')
        nav_layout.addWidget(nav_hint)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._on_current_changed)
        self.tree.setMinimumWidth(220)
        self.tree.setMaximumWidth(320)
        nav_layout.addWidget(self.tree, 1)
        self._splitter.addWidget(nav_wrap)

        self.stack = QStackedWidget()
        self._splitter.addWidget(self.stack)
        self._splitter.setSizes([240, 960])
        layout.addWidget(self._splitter, 1)

    def clear(self):
        self.tree.clear()
        self._items.clear()
        self._pages.clear()
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def add_page(self, key: str, label: str, widget: QWidget, parent_key: str = ''):
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.ItemDataRole.UserRole, key)
        self._items[key] = item
        self._pages[key] = widget
        self.stack.addWidget(widget)

        if parent_key and parent_key in self._items:
            self._items[parent_key].addChild(item)
            self._items[parent_key].setExpanded(True)
        else:
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
        return item

    def select_page(self, key: str):
        item = self._items.get(key)
        if item is None:
            return
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.tree.setCurrentItem(item)

    def first_key(self) -> str:
        item = self.tree.topLevelItem(0)
        if item is None:
            return ''
        return str(item.data(0, Qt.ItemDataRole.UserRole) or '')

    def _on_current_changed(self, current: Optional[QTreeWidgetItem], _previous: Optional[QTreeWidgetItem]):
        if current is None:
            return
        key = str(current.data(0, Qt.ItemDataRole.UserRole) or '')
        widget = self._pages.get(key)
        if widget is not None:
            self.stack.setCurrentWidget(widget)