# -*- coding: utf-8 -*-
"""
主窗口

布局: 左侧导航栏 + 右侧 QStackedWidget 页面区 + 底部日志面板
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QListWidget, QListWidgetItem, QStackedWidget,
                              QSplitter, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from ui.styles import MAIN_STYLE
from ui.widgets.log_panel import LogPanel
from ui.widgets.progress_bar import ProgressWidget
from ui.pages.analysis_page import AnalysisPage
from ui.pages.preprocessing_page import PreprocessingPage
from ui.pages.config_page import ConfigPage
from ui.pages.history_page import HistoryPage
from ui.pages.test_page import TestPage
from core.config_manager import ConfigManager


# 导航项定义
NAV_ITEMS = [
    {"name": "分析执行",   "icon": "📊", "enabled": True},
    {"name": "数据预处理", "icon": "📁", "enabled": True},
    {"name": "配置管理",   "icon": "⚙",  "enabled": True},
    {"name": "历史浏览",   "icon": "📋", "enabled": True},
    {"name": "硬件测试",   "icon": "🔧", "enabled": False},
]


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self._config_mgr = config_mgr
        self.setWindowTitle("DLP 自动化测试系统")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 900)

        # 应用样式
        self.setStyleSheet(MAIN_STYLE)

        self._init_ui()
        self._init_status_bar()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ====== 左侧导航栏 ======
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFixedWidth(160)
        self.nav_list.setFont(QFont("Microsoft YaHei", 12))
        self.nav_list.setIconSize(QSize(20, 20))

        for item_def in NAV_ITEMS:
            item = QListWidgetItem(f" {item_def['icon']}  {item_def['name']}")
            if not item_def['enabled']:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setToolTip("需要硬件 SDK 支持")
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        main_layout.addWidget(self.nav_list)

        # ====== 右侧内容区 ======
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 上下分割: 页面 + 日志
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # 页面堆栈
        self.page_stack = QStackedWidget()

        # 日志面板
        self.log_panel = LogPanel()

        # 创建各页面
        self.analysis_page = AnalysisPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)
        self.preprocessing_page = PreprocessingPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)
        self.config_page = ConfigPage(
            config_mgr=self._config_mgr,
            log_panel=self.log_panel)
        self.history_page = HistoryPage(
            config_mgr=self._config_mgr,
            log_panel=self.log_panel)
        self.test_page = TestPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)

        self.page_stack.addWidget(self.analysis_page)
        self.page_stack.addWidget(self.preprocessing_page)
        self.page_stack.addWidget(self.config_page)
        self.page_stack.addWidget(self.history_page)
        self.page_stack.addWidget(self.test_page)

        self.splitter.addWidget(self.page_stack)
        self.splitter.addWidget(self.log_panel)

        # 设置分割比例 (页面区 : 日志区 = 7 : 2)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([600, 150])

        right_layout.addWidget(self.splitter)
        main_layout.addWidget(right_panel)

    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 全局进度条
        self.global_progress = ProgressWidget()
        self.status_bar.addPermanentWidget(self.global_progress)

    def _on_nav_changed(self, index: int):
        """导航切换"""
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)
            name = NAV_ITEMS[index]['name'] if index < len(NAV_ITEMS) else ''
            self.status_bar.showMessage(f"当前: {name}")

    def refresh_modules(self):
        """刷新所有页面的模块列表"""
        self.analysis_page.refresh_modules()
        self.preprocessing_page.refresh_modules()
        self.test_page.refresh_modules()
        self.log_panel.append_log("模块列表已刷新", "SUCCESS")

    def closeEvent(self, event):
        """关闭窗口确认"""
        reply = QMessageBox.question(
            self, "退出确认",
            "确定要退出 DLP 自动化测试系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
