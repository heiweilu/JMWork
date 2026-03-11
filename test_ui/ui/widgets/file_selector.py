# -*- coding: utf-8 -*-
"""
文件/目录选择器组件

支持文件拖拽、系统对话框选择、格式提示。
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                              QFileDialog, QLabel, QVBoxLayout, QApplication)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import os


class FileSelector(QWidget):
    """
    文件选择器组件。

    功能:
    - 路径输入框 + 浏览按钮
    - 拖拽文件到输入框
    - 格式描述提示
    - 信号: file_selected(str)

    Signals:
        file_selected(str): 文件选择完成时发射
    """

    file_selected = pyqtSignal(str)

    def __init__(self,
                 label: str = "选择文件",
                 file_filter: str = "所有文件 (*);;CSV文件 (*.csv);;文本文件 (*.txt)",
                 description: str = "",
                 select_dir: bool = False,
                 parent=None):
        """
        Args:
            label: 标签文字
            file_filter: 文件类型过滤器
            description: 格式描述提示
            select_dir: True 选择目录，False 选择文件
            parent: 父组件
        """
        super().__init__(parent)
        self._file_filter = file_filter
        self._select_dir = select_dir
        self._init_ui(label, description)
        self.setAcceptDrops(True)

    def _init_ui(self, label: str, description: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # 标签行
        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #2E538D;")
            main_layout.addWidget(lbl)

        # 输入框 + 按钮行
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("可直接输入文件/目录路径，或拖拽到此处...")
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.setSizePolicy(
            self.path_edit.sizePolicy().horizontalPolicy(),
            self.path_edit.sizePolicy().verticalPolicy()
        )
        self.path_edit.textChanged.connect(self._on_text_changed)
        row_layout.addWidget(self.path_edit)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.setFixedWidth(70)
        self.btn_browse.clicked.connect(self._on_browse)
        row_layout.addWidget(self.btn_browse)

        self.btn_paste = QPushButton("粘贴")
        self.btn_paste.setFixedWidth(54)
        self.btn_paste.setToolTip("从剪贴板粘贴完整路径")
        self.btn_paste.clicked.connect(self._on_paste)
        row_layout.addWidget(self.btn_paste)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.setFixedWidth(54)
        self.btn_clear.clicked.connect(self.path_edit.clear)
        row_layout.addWidget(self.btn_clear)

        main_layout.addLayout(row_layout)

        # 格式描述提示
        hint_text = "支持：直接输入完整路径 / 拖拽文件 / 点击浏览选择"
        if description:
            hint_text = f"{description}\n{hint_text}"
        desc_label = QLabel(hint_text)
        desc_label.setStyleSheet("color: #87A0C3; font-size: 11px;")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

    def _on_browse(self):
        """打开系统文件对话框"""
        if self._select_dir:
            path = QFileDialog.getExistingDirectory(self, "选择目录")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", self._file_filter)
        if path:
            self.path_edit.setText(path)
            self.file_selected.emit(path)

    def _on_text_changed(self, text: str):
        """输入框文字改变"""
        if os.path.exists(text):
            self.path_edit.setStyleSheet(
                "border: 1px solid rgba(73, 205, 171, 0.9);"
                "background-color: rgba(244, 255, 252, 0.95);"
            )
        elif text.strip():
            self.path_edit.setStyleSheet(
                "border: 1px solid rgba(244, 108, 122, 0.82);"
                "background-color: rgba(255, 247, 248, 0.96);"
            )
        else:
            self.path_edit.setStyleSheet("")
        self.file_selected.emit(text.strip())

    def _on_paste(self):
        """从剪贴板粘贴路径"""
        text = QApplication.clipboard().text().strip().strip('"')
        if text:
            self.path_edit.setText(text)
            self.file_selected.emit(text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.path_edit.setText(path)
            self.file_selected.emit(path)

    def get_path(self) -> str:
        """获取当前路径"""
        return self.path_edit.text().strip()

    def set_path(self, path: str):
        """设置路径"""
        self.path_edit.setText(path)
