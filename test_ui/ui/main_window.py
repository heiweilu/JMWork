# -*- coding: utf-8 -*-
"""
主窗口

布局: 左侧导航栏 + 中间页面区 + 右侧可隐藏日志面板
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QListWidget, QListWidgetItem, QStackedWidget,
                              QSplitter, QStatusBar, QMessageBox, QFrame,
                              QLabel, QPushButton)
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
from ui.pages.docs_page import DocsPage
from ui.pages.serial_page import SerialPage
from core.config_manager import ConfigManager
from ui.animations import UIAnimator


# 导航项定义
NAV_ITEMS = [
    {"name": "分析执行",   "icon": "📊", "enabled": True},
    {"name": "数据预处理", "icon": "📁", "enabled": True},
    {"name": "配置管理",   "icon": "⚙",  "enabled": True},
    {"name": "历史浏览",   "icon": "📋", "enabled": True},
    {"name": "开发文档",   "icon": "📖", "enabled": True},
    {"name": "串口调试",   "icon": "🔌", "enabled": True},
    {"name": "硬件测试",   "icon": "🔧", "enabled": True},
]


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self._config_mgr = config_mgr
        self._current_animation = None  # 初始化，避免 hasattr 检查
        self._log_panel_animation = None
        self._log_fade_animation = None
        self._log_panel_visible = True
        self._last_log_width = 360
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
        
        # 给导航栏添加立体阴影
        UIAnimator.add_soft_shadow(self.nav_list, blur_radius=20, x_offset=2, y_offset=0, alpha=30)

        # ====== 右侧内容区 ======
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # 左右分割: 页面 + 日志
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 页面堆栈容器 — 用 CSS 模拟卡片阴影效果，不用 QGraphicsEffect
        # （QGraphicsDropShadowEffect 会把整个容器放入离屏缓冲区，
        #   与切换动画的 QGraphicsOpacityEffect 嵌套后必然引发重叠/错位）
        self.page_stack_container = QFrame()
        self.page_stack_container.setObjectName("page_stack_container")
        self.page_stack_container.setStyleSheet(
            "QFrame#page_stack_container { "
            "background-color: rgba(255, 255, 255, 0.92); "
            "border-radius: 14px; "
            "border: 1px solid rgba(106, 168, 255, 0.12); "
            "}")
        
        container_layout = QVBoxLayout(self.page_stack_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)

        page_glow_wrap = QHBoxLayout()
        page_glow_wrap.setContentsMargins(0, 0, 0, 0)
        self._page_glow_bar = QFrame()
        self._page_glow_bar.setObjectName("card_top_glow")
        self._page_glow_bar.setFixedHeight(4)
        self._page_glow_bar.setMaximumWidth(160)
        page_glow_wrap.addWidget(self._page_glow_bar)
        page_glow_wrap.addStretch(1)
        container_layout.addLayout(page_glow_wrap)

        # 页面堆栈
        self.page_stack = QStackedWidget()
        container_layout.addWidget(self.page_stack)

        # 日志面板容器 — 同样用 CSS，不用 QGraphicsEffect
        self.log_panel_container = QFrame()
        self.log_panel_container.setObjectName("log_panel_container")
        self.log_panel_container.setMinimumWidth(300)
        self.log_panel_container.setStyleSheet(
            "QFrame#log_panel_container { "
            "background-color: rgba(255, 255, 255, 0.88); "
            "border-radius: 14px; "
            "border: 1px solid rgba(106, 168, 255, 0.14); "
            "}")
        
        log_layout = QVBoxLayout(self.log_panel_container)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_layout.setSpacing(8)

        log_glow_wrap = QHBoxLayout()
        log_glow_wrap.setContentsMargins(0, 0, 0, 0)
        self._log_glow_bar = QFrame()
        self._log_glow_bar.setObjectName("log_top_glow")
        self._log_glow_bar.setFixedHeight(4)
        self._log_glow_bar.setMaximumWidth(120)
        log_glow_wrap.addWidget(self._log_glow_bar)
        log_glow_wrap.addStretch(1)
        log_layout.addLayout(log_glow_wrap)

        log_header = QFrame()
        log_header.setObjectName("log_dock_header")
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(10, 8, 10, 8)

        log_title = QLabel("系统日志中心")
        log_title.setObjectName("log_dock_title")
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch(1)

        self._btn_toggle_log = QPushButton("隐藏")
        self._btn_toggle_log.setObjectName("btn_log_toggle")
        self._btn_toggle_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_toggle_log.clicked.connect(self._toggle_log_panel)
        log_header_layout.addWidget(self._btn_toggle_log)

        log_layout.addWidget(log_header)

        # 日志面板
        self.log_panel = LogPanel()
        log_layout.addWidget(self.log_panel)

        UIAnimator.add_soft_shadow(self.page_stack_container, blur_radius=32, x_offset=0, y_offset=8, alpha=18)
        UIAnimator.add_soft_shadow(self.log_panel_container, blur_radius=26, x_offset=0, y_offset=8, alpha=15)

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
        self.docs_page = DocsPage()
        self.page_stack.addWidget(self.docs_page)
        self.serial_page = SerialPage()
        self.page_stack.addWidget(self.serial_page)
        self.page_stack.addWidget(self.test_page)

        self.splitter.addWidget(self.page_stack_container)
        self.splitter.addWidget(self.log_panel_container)
        self.splitter.setHandleWidth(8)

        # 设置分割比例 (页面区 : 日志区 = 5 : 2)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([980, self._last_log_width])

        right_layout.addWidget(self.splitter)
        main_layout.addWidget(right_panel)

        for button in self.findChildren(QPushButton):
            UIAnimator.install_button_hover(button)

    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        self._status_toggle_log = QPushButton("收起日志")
        self._status_toggle_log.setObjectName("btn_status_log_toggle")
        self._status_toggle_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self._status_toggle_log.clicked.connect(self._toggle_log_panel)
        self.status_bar.addPermanentWidget(self._status_toggle_log)
        UIAnimator.install_button_hover(self._status_toggle_log)

        # 全局进度条
        self.global_progress = ProgressWidget()
        self.status_bar.addPermanentWidget(self.global_progress)

    def _toggle_log_panel(self):
        """切换右侧日志面板显示状态"""
        sizes = self.splitter.sizes()
        if self._log_panel_visible:
            if len(sizes) > 1 and sizes[1] > 0:
                self._last_log_width = sizes[1]
            current_width = max(self.log_panel_container.width(), self._last_log_width)
            self.log_panel_container.setMinimumWidth(0)
            self._log_panel_animation = UIAnimator.animate_width(
                self.log_panel_container, current_width, 0, duration=220)

            def _finish_hide():
                self.log_panel_container.hide()
                self.splitter.setSizes([sum(self.splitter.sizes()), 0])
                self.log_panel_container.setMaximumWidth(16777215)

            self._log_panel_animation.finished.connect(_finish_hide)
            self._btn_toggle_log.setText("展开")
            self._status_toggle_log.setText("展开日志")
            self._log_panel_visible = False
        else:
            target_width = max(300, self._last_log_width)
            self.log_panel_container.show()
            self.log_panel_container.setMinimumWidth(0)
            self.log_panel_container.setMaximumWidth(0)
            total = max(self.width() - 220, 900)
            self.splitter.setSizes([max(620, total - target_width), target_width])
            self._log_panel_animation = UIAnimator.animate_width(
                self.log_panel_container, 0, target_width, duration=260)

            def _finish_show():
                self.log_panel_container.setMaximumWidth(16777215)
                self.log_panel_container.setMinimumWidth(300)

            self._log_panel_animation.finished.connect(_finish_show)
            self._log_fade_animation = UIAnimator.fade_in(self.log_panel_container, duration=220)
            UIAnimator.pulse_widget(self._log_glow_bar, duration=260)
            self._btn_toggle_log.setText("隐藏")
            self._status_toggle_log.setText("收起日志")
            self._log_panel_visible = True

    def _on_nav_changed(self, index: int):
        """导航切换。"""
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)
            self._current_animation = UIAnimator.pulse_widget(self._page_glow_bar, duration=240)

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
