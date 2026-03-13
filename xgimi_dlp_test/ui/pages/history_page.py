# -*- coding: utf-8 -*-
"""
历史结果浏览页面

左侧: reports/ 目录树形浏览
右侧: PNG 图片预览 / CSV-TXT 表格预览 / Excel 预览
"""

import os
import pandas as pd
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                              QTreeView, QLabel, QTableView, QPushButton,
                              QHeaderView, QAbstractItemView, QScrollArea,
                              QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFileSystemModel, QPixmap, QDesktopServices
from PyQt6.QtCore import Qt, QModelIndex, QUrl, QAbstractTableModel


class PandasTableModel(QAbstractTableModel):
    """将 pandas DataFrame 适配为 Qt TableModel"""

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            return str(val)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(section + 1)
        return None


class HistoryPage(QWidget):
    """历史结果浏览页面"""

    def __init__(self, config_mgr=None, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 标题 + 按钮
        header_layout = QHBoxLayout()
        title = QLabel("历史结果浏览")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_open_external = QPushButton("用系统程序打开")
        self.btn_open_external.clicked.connect(self._open_external)
        self.btn_open_external.setEnabled(False)
        header_layout.addWidget(self.btn_open_external)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._refresh_tree)
        header_layout.addWidget(self.btn_refresh)

        layout.addLayout(header_layout)

        # 左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧文件树
        self.tree_view = QTreeView()
        self.fs_model = QFileSystemModel()
        self.fs_model.setReadOnly(True)
        self.fs_model.setNameFilters(['*.png', '*.csv', '*.txt', '*.xlsx', '*.xls'])
        self.fs_model.setNameFilterDisables(False)
        self.tree_view.setModel(self.fs_model)

        # 只显示名称列
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setMinimumWidth(250)
        self.tree_view.selectionModel()
        self.tree_view.clicked.connect(self._on_file_clicked)
        splitter.addWidget(self.tree_view)

        # 右侧预览区
        self.preview_stack = QStackedWidget()

        # 空白提示
        self.lbl_placeholder = QLabel("请选择文件预览")
        self.lbl_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_placeholder.setStyleSheet("color: #999; font-size: 14px;")
        self.preview_stack.addWidget(self.lbl_placeholder)

        # 图片预览
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll.setWidget(self.lbl_image)
        self.preview_stack.addWidget(self.image_scroll)

        # 表格预览
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.preview_stack.addWidget(self.table_view)

        splitter.addWidget(self.preview_stack)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        self._current_file = ''
        self._refresh_tree()

    def _refresh_tree(self):
        """刷新目录树"""
        root_path = ''
        if self._config_mgr:
            root_path = os.path.join(
                self._config_mgr.get_project_root(), 'reports')
        if not root_path or not os.path.isdir(root_path):
            # 回退到上级 reports 目录搜索
            code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            root_path = os.path.join(code_dir, '..', '202602027_dlp_auto', 'reports')
            root_path = os.path.normpath(root_path)

        if os.path.isdir(root_path):
            self.fs_model.setRootPath(root_path)
            self.tree_view.setRootIndex(self.fs_model.index(root_path))

    def _on_file_clicked(self, index: QModelIndex):
        """文件点击预览"""
        filepath = self.fs_model.filePath(index)
        if not os.path.isfile(filepath):
            return

        self._current_file = filepath
        self.btn_open_external.setEnabled(True)
        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == '.png':
                self._preview_image(filepath)
            elif ext in ('.csv', '.txt'):
                self._preview_table(filepath)
            elif ext in ('.xlsx', '.xls'):
                self._preview_excel(filepath)
            else:
                self.preview_stack.setCurrentIndex(0)
                self.lbl_placeholder.setText(f"不支持预览此文件格式: {ext}")
        except Exception as e:
            self.preview_stack.setCurrentIndex(0)
            self.lbl_placeholder.setText(f"预览失败: {e}")
            if self._log_panel:
                self._log_panel.append_log(f"预览失败 {filepath}: {e}", "ERROR")

    def _preview_image(self, filepath: str):
        """预览 PNG 图片"""
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            self.lbl_placeholder.setText("图片加载失败")
            self.preview_stack.setCurrentIndex(0)
            return

        # 缩放到合适大小
        max_w = self.image_scroll.viewport().width() - 20
        max_h = self.image_scroll.viewport().height() - 20
        if max_w > 100 and max_h > 100:
            pixmap = pixmap.scaled(max_w, max_h,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        self.lbl_image.setPixmap(pixmap)
        self.preview_stack.setCurrentIndex(1)

    def _preview_table(self, filepath: str):
        """预览 CSV/TXT 表格"""
        from core.data_loader import detect_separator
        sep = detect_separator(filepath)
        df = pd.read_csv(filepath, sep=sep, encoding='utf-8-sig',
                         nrows=1000, on_bad_lines='skip')
        model = PandasTableModel(df)
        self.table_view.setModel(model)
        self.preview_stack.setCurrentIndex(2)

    def _preview_excel(self, filepath: str):
        """预览 Excel 文件"""
        df = pd.read_excel(filepath, nrows=1000)
        model = PandasTableModel(df)
        self.table_view.setModel(model)
        self.preview_stack.setCurrentIndex(2)

    def _open_external(self):
        """用系统程序打开当前文件"""
        if self._current_file and os.path.exists(self._current_file):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._current_file))
