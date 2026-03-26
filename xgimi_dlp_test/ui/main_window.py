# -*- coding: utf-8 -*-
"""
主窗口

布局: 左侧导航栏 + 中间页面区 + 右侧可隐藏日志面板
"""

import os

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QTreeWidget, QTreeWidgetItem, QStackedWidget,
                              QSplitter, QStatusBar, QMessageBox, QFrame,
                              QLabel, QPushButton, QInputDialog, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from ui.styles import MAIN_STYLE
from ui.widgets.log_panel import LogPanel
from ui.widgets.progress_bar import ProgressWidget
from ui.widgets.particle_bg import ParticleBg
from ui.pages.analysis_page import AnalysisPage
from ui.pages.preprocessing_page import PreprocessingPage
from ui.pages.config_page import ConfigPage
from ui.pages.history_page import HistoryPage
from ui.pages.test_page import TestPage
from ui.pages.docs_page import DocsPage
from ui.pages.bug_tracking_page import MtkBugTrackingPage
from ui.pages.device_lab_page import DeviceLabPage
from ui.pages.serial_page import SerialPage
from core.app_meta import APP_NAME, APP_AUTHOR_EMAIL, APP_SIGNATURE, APP_VERSION, full_app_title
from core.admin_console_store import AdminConsoleStore
from core.config_manager import ConfigManager
from ui.dialogs.admin_console_dialog import AdminConsoleDialog
from ui.animations import UIAnimator, TypewriterEffect, NeonPulse


# 导航项定义
NAV_ITEMS = [
    {"name": "数据预处理", "icon": "📁", "enabled": True},
    {"name": "分析执行",   "icon": "📊", "enabled": True},
    {"name": "SVM训练",     "icon": "🤖", "enabled": True},
    {"name": "配置管理",   "icon": "⚙",  "enabled": True},
    {"name": "历史浏览",   "icon": "📋", "enabled": True},
    {"name": "开发文档",   "icon": "📖", "enabled": True},
    {"name": "串口调试",   "icon": "🔌", "enabled": True},
    {"name": "设备联调台", "icon": "🎛", "enabled": True},
    {"name": "硬件测试",   "icon": "🔧", "enabled": True},
    {"name": "MTK问题跟踪", "icon": "🐛", "enabled": True},
]

NAV_GROUPS = [
    ("数据处理", ["数据预处理", "分析执行", "SVM训练"]),
    ("系统管理", ["配置管理", "历史浏览", "开发文档"]),
    ("设备工作台", ["串口调试", "设备联调台", "硬件测试"]),
    ("BUG追踪",   ["MTK问题跟踪"]),
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
        self._nav_items_by_name = {}
        self._admin_store = AdminConsoleStore(self._config_mgr._config_dir)
        self.setWindowTitle(full_app_title())
        self.setMinimumSize(1200, 750)
        self.resize(1400, 900)

        # 应用样式
        self.setStyleSheet(MAIN_STYLE)

        self._init_ui()
        self._init_status_bar()
        # 粒子背景层（置于最顶层䯕袍，WA_TransparentForMouseEvents 确保交互不受影响）
        central = self.centralWidget()
        self._particle_bg = ParticleBg(parent=central)
        self._particle_bg.resize(central.size())
        self._particle_bg.raise_()  # 置顶层覆盖全屏
        # 导航栏霓虹脉冲光晕
        self._nav_neon = NeonPulse(
            self.nav_list,
            r=37, g=99, b=235,
            blur_min=4, blur_max=18,
            alpha_min=12, alpha_max=55,
            period=3000,
        )
        self._nav_neon.start()
        # 页面容器顶部光条脉冲
        self._glow_neon = NeonPulse(
            self._page_glow_bar,
            r=37, g=99, b=235,
            blur_min=5, blur_max=16,
            alpha_min=80, alpha_max=255,
            period=1800,
        )
        self._glow_neon.start()
        # 默认收起日志面板（无动画）
        self._collapse_log_immediately()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 0)   # 边距让粒子背景在边缘可见
        main_layout.setSpacing(6)

        # ====== 左侧导航栏 ======
        self.nav_list = QTreeWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFixedWidth(160)
        self.nav_list.setFont(QFont("Microsoft YaHei", 12))
        self.nav_list.setIconSize(QSize(20, 20))
        self.nav_list.setHeaderHidden(True)

        item_defs = {item['name']: item for item in NAV_ITEMS}
        for group_name, child_names in NAV_GROUPS:
            root_item = QTreeWidgetItem([group_name])
            root_item.setData(0, Qt.ItemDataRole.UserRole, -1)
            self.nav_list.addTopLevelItem(root_item)
            root_item.setExpanded(True)
            for child_name in child_names:
                item_def = item_defs.get(child_name, {'enabled': True})
                child_item = QTreeWidgetItem([child_name])
                child_item.setData(0, Qt.ItemDataRole.UserRole, self._nav_index_by_name(child_name))
                if not item_def.get('enabled', True):
                    child_item.setDisabled(True)
                    child_item.setToolTip(0, '需要硬件 SDK 支持')
                root_item.addChild(child_item)
                self._nav_items_by_name[child_name] = child_item

        first_item = self._nav_items_by_name.get(NAV_ITEMS[0]['name'])
        if first_item is not None:
            self.nav_list.setCurrentItem(first_item)
        self.nav_list.currentItemChanged.connect(self._on_nav_changed)
        main_layout.addWidget(self.nav_list)
        
        # 给导航栏添加立体阴影
        UIAnimator.add_soft_shadow(self.nav_list, blur_radius=18, x_offset=2, y_offset=0, alpha=20)

        # ====== 右侧内容区 ======
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        self._header_title = QLabel(APP_NAME)
        self._header_title.setStyleSheet('font-size:18px;font-weight:bold;color:#1f2937;')
        self._header_meta = QLabel('')
        self._header_meta.setStyleSheet('color:#617A9D; font-size:12px;')
        self._btn_admin_console = QPushButton('管理员控制台')
        self._btn_admin_console.clicked.connect(self._open_admin_console)
        header_layout.addWidget(self._header_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self._header_meta)
        header_layout.addSpacing(8)
        header_layout.addWidget(self._btn_admin_console)
        right_layout.addWidget(header)

        # 左右分割: 页面 + 日志
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 页面堆栈容器 — 用 CSS 模拟卡片阴影效果，不用 QGraphicsEffect
        # （QGraphicsDropShadowEffect 会把整个容器放入离屏缓冲区，
        #   与切换动画的 QGraphicsOpacityEffect 嵌套后必然引发重叠/错位）
        self.page_stack_container = QFrame()
        self.page_stack_container.setObjectName("page_stack_container")
        self.page_stack_container.setStyleSheet(
            "QFrame#page_stack_container { "
            "background-color: rgba(255,255,255,0.96); "
            "border-radius: 14px; "
            "border: 1px solid rgba(37,99,235,0.18); "
            "}")
        
        container_layout = QVBoxLayout(self.page_stack_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)

        page_glow_wrap = QHBoxLayout()
        page_glow_wrap.setContentsMargins(0, 0, 0, 0)
        self._page_glow_bar = QFrame()
        self._page_glow_bar.setObjectName("card_top_glow")
        self._page_glow_bar.setFixedHeight(3)
        self._page_glow_bar.setMaximumWidth(9999)  # 全宽霓虹光条
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
            "background-color: rgba(248,250,255,0.96); "
            "border-radius: 14px; "
            "border: 1px solid rgba(37,99,235,0.16); "
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
        self.svm_page = AnalysisPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr,
            category='svm')
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

        self.page_stack.addWidget(self.preprocessing_page)
        self.page_stack.addWidget(self.analysis_page)
        self.page_stack.addWidget(self.svm_page)
        self.page_stack.addWidget(self.config_page)
        self.page_stack.addWidget(self.history_page)
        self.docs_page = DocsPage(admin_store=self._admin_store)
        self.page_stack.addWidget(self.docs_page)
        self.serial_page = SerialPage(config_mgr=self._config_mgr)
        self.page_stack.addWidget(self.serial_page)
        self.device_lab_page = DeviceLabPage(
            config_mgr=self._config_mgr,
            log_panel=self.log_panel,
        )
        self.page_stack.addWidget(self.device_lab_page)
        self.page_stack.addWidget(self.test_page)
        self.bug_tracking_page = MtkBugTrackingPage()
        self.page_stack.addWidget(self.bug_tracking_page)
        # 预处理页"导入至梯形测试"信号 → 切换至硬件测试并设置文件
        self.preprocessing_page.import_to_test.connect(self._on_import_to_test)        # 分析页快捷跳转信号
        self.analysis_page.send_to_preprocessing.connect(self._on_send_to_preprocess_expand)
        self.analysis_page.send_to_svm.connect(self._on_send_to_svm)
        self.analysis_page.send_to_angle_test.connect(self._on_send_to_angle_test)
        self.splitter.addWidget(self.page_stack_container)
        self.splitter.addWidget(self.log_panel_container)
        self.splitter.setHandleWidth(8)

        # 设置分割比例 (页面区 : 日志区 = 5 : 2)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([980, self._last_log_width])

        right_layout.addWidget(self.splitter)
        main_layout.addWidget(right_panel)

        self._refresh_app_meta_ui()

        for button in self.findChildren(QPushButton):
            UIAnimator.install_button_hover(button)

    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        self._status_app_meta = QLabel('')
        self._status_app_meta.setStyleSheet('color:#617A9D; padding:0 8px;')
        self.status_bar.addPermanentWidget(self._status_app_meta)

        self._status_toggle_log = QPushButton("收起日志")
        self._status_toggle_log.setObjectName("btn_status_log_toggle")
        self._status_toggle_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self._status_toggle_log.clicked.connect(self._toggle_log_panel)
        self.status_bar.addPermanentWidget(self._status_toggle_log)
        UIAnimator.install_button_hover(self._status_toggle_log)

        # 全局进度条
        self.global_progress = ProgressWidget()
        self.status_bar.addPermanentWidget(self.global_progress)
        self._refresh_app_meta_ui()

    def _current_app_version(self) -> str:
        return self._admin_store.get_app_version() or APP_VERSION

    def _current_author_email(self) -> str:
        return self._admin_store.get_author_email() or APP_AUTHOR_EMAIL

    def _refresh_app_meta_ui(self):
        version = self._current_app_version()
        email = self._current_author_email()
        self.setWindowTitle(f'{APP_NAME} {version} {APP_SIGNATURE}')
        if hasattr(self, '_header_meta'):
            self._header_meta.setText(f'{version} | {APP_SIGNATURE} | {email}')
        if hasattr(self, '_status_app_meta'):
            self._status_app_meta.setText(f'{APP_NAME} {version} | {APP_SIGNATURE} | {email}')

    def _open_admin_console(self):
        password, ok = QInputDialog.getText(
            self,
            '管理员验证',
            '请输入管理员密码',
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if not self._admin_store.verify_password(password):
            QMessageBox.warning(self, '验证失败', '管理员密码不正确')
            return
        dialog = AdminConsoleDialog(
            app_version=self._current_app_version(),
            author_email=self._current_author_email(),
            docs=[dict(item) for item in getattr(self.docs_page, '_docs', [])],
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        self._admin_store.set_app_version(data.get('app_version', APP_VERSION))
        self._admin_store.set_author_email(data.get('author_email', APP_AUTHOR_EMAIL))
        self._admin_store.set_docs(data.get('docs', []))
        self._admin_store.save()
        self.docs_page.refresh_docs()
        self._refresh_app_meta_ui()

    def _collapse_log_immediately(self):
        """首次启动时无动画收起日志面板"""
        self.log_panel_container.setMinimumWidth(0)
        self.log_panel_container.hide()
        total = self.splitter.sizes()
        all_width = sum(total)
        self.splitter.setSizes([all_width, 0])
        self._log_panel_visible = False
        self._btn_toggle_log.setText("展开")
        self._status_toggle_log.setText("展开日志")

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

    def _nav_index_by_name(self, name: str) -> int:
        return next((i for i, item in enumerate(NAV_ITEMS) if item['name'] == name), -1)

    def _select_nav_page_by_name(self, name: str):
        item = self._nav_items_by_name.get(name)
        if item is not None:
            parent = item.parent()
            if parent is not None:
                parent.setExpanded(True)
            self.nav_list.setCurrentItem(item)

    def _on_nav_changed(self, current, _previous):
        """导航切换，附带淡入动效 + 打字机状态栏。"""
        if current is None:
            return
        index = current.data(0, Qt.ItemDataRole.UserRole)
        if index is None or int(index) < 0:
            if current.childCount() > 0:
                self.nav_list.setCurrentItem(current.child(0))
            return
        index = int(index)
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)
            # 当前页面淡入
            page = self.page_stack.currentWidget()
            if page:
                self._current_animation = UIAnimator.fade_in(page, duration=200)
            # NeonPulse 已在 _page_glow_bar 上持续运行，不再额外 pulse_widget（避免 setGraphicsEffect 冲突）

            name = NAV_ITEMS[index]['name'] if index < len(NAV_ITEMS) else ''
            msg = f"◈  当前模块: {name}"
            self.status_bar.showMessage(msg)

    def resizeEvent(self, event):  # noqa: N802
        """窗口大小变化时同步调整粒子背景层"""
        super().resizeEvent(event)
        if hasattr(self, "_particle_bg"):
            central = self.centralWidget()
            if central:
                self._particle_bg.resize(central.size())
                self._particle_bg.raise_()  # 始终保持顶层

    def refresh_modules(self):
        """刷新所有页面的模块列表"""
        self.analysis_page.refresh_modules()
        self.svm_page.refresh_modules()
        self.preprocessing_page.refresh_modules()
        self.test_page.refresh_modules()
        self.log_panel.append_log("模块列表已刷新", "SUCCESS")

    def _on_import_to_test(self, file_path: str):
        """预处理页导入信号 → 切换至硬件测试并设置梯形测试文件"""
        # 找到"硬件测试"导航项索引（固定为 6）
        hw_nav_index = next(
            (i for i, item in enumerate(NAV_ITEMS) if item['name'] == '硬件测试'), 7)
        _ = hw_nav_index
        self._select_nav_page_by_name('硬件测试')
        self.test_page.set_input_file_for_trapezoid(file_path)
        self.log_panel.append_log(
            f"已导入坐标文件至梯形坐标测试: {file_path}", "INFO")

    def _on_send_to_preprocess_expand(self, file_path: str):
        """分析页快捷跳转：发送到数据预处理→角度扩圆坐标生成"""
        if not file_path or not os.path.isfile(file_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "发送失败", f"找不到文件:\n{file_path}")
            return
        preproc_idx = next(
            (i for i, item in enumerate(NAV_ITEMS) if item['name'] == '数据预处理'), 2)
        _ = preproc_idx
        self._select_nav_page_by_name('数据预处理')
        self.preprocessing_page.set_module_input("角度扩圆坐标生成", file_path)
        self.log_panel.append_log(f"已发送至角度扩圆坐标生成: {file_path}", "INFO")

    def _on_send_to_svm(self, file_path: str):
        """分析页快捷跳转：发送到 SVM 训练页面"""
        if not file_path or not os.path.isfile(file_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "发送失败", f"找不到文件:\n{file_path}")
            return
        svm_idx = next(
            (i for i, item in enumerate(NAV_ITEMS) if item['name'] == 'SVM训练'), 1)
        _ = svm_idx
        self._select_nav_page_by_name('SVM训练')
        self.svm_page.set_input_file(file_path)
        self.log_panel.append_log(f"已导入到 SVM 模型训练: {file_path}", "INFO")

    def _on_send_to_angle_test(self, file_path: str):
        """分析页快捷跳转：发送到硬件测试→角度测试(硬件)"""
        if not file_path or not os.path.isfile(file_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "发送失败", f"找不到文件:\n{file_path}")
            return
        hw_nav_index = next(
            (i for i, item in enumerate(NAV_ITEMS) if item['name'] == '硬件测试'), 7)
        _ = hw_nav_index
        self._select_nav_page_by_name('硬件测试')
        self.test_page.set_input_file_for_angle_test(file_path)
        self.log_panel.append_log(f"已导入到角度测试(硬件): {file_path}", "INFO")

    def closeEvent(self, event):
        """关闭窗口确认"""
        reply = QMessageBox.question(
            self, "退出确认",
            "确定要退出 DLP 自动化测试系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'device_lab_page'):
                self.device_lab_page.cleanup()
            event.accept()
        else:
            event.ignore()
