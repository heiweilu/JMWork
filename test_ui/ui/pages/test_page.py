# -*- coding: utf-8 -*-
"""
硬件测试页面

DLP 硬件连接 + 角度测试 / 梯形坐标测试
通过 DLPC843x SDK 直接控制投影仪执行测试。
"""

import os
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QGroupBox, QPushButton, QComboBox, QTextBrowser,
                              QSplitter, QFileDialog, QMessageBox, QFrame,
                              QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.widgets.param_editor import ParamEditor
from ui.widgets.file_selector import FileSelector
from ui.widgets.progress_bar import ProgressWidget
from workers.task_worker import TaskWorker
from core import task_registry


class TestPage(QWidget):
    """硬件测试页面"""

    def __init__(self, log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._worker = None
        self._dlp_manager = None
        self._status_timer = QTimer()
        self._status_timer.setInterval(3000)
        self._status_timer.timeout.connect(self._refresh_device_status)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ========== 1. 设备连接栏 ==========
        conn_group = QGroupBox("🔌 DLP 设备连接")
        conn_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px; font-weight: bold;
                color: #294469;
                background-color: #FBFDFF;
                border: 1px solid rgba(79, 140, 255, 0.14); border-radius: 12px;
                margin-top: 10px; padding-top: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px; padding: 0 6px;
                color: #2A64D6;
            }
        """)
        conn_layout = QHBoxLayout(conn_group)
        conn_layout.setSpacing(10)

        # 状态指示灯
        self._status_dot = QLabel("●")
        self._status_dot.setFixedWidth(20)
        self._status_dot.setStyleSheet("color: #999; font-size: 18px;")
        conn_layout.addWidget(self._status_dot)

        # 设备信息
        self._device_label = QLabel("未连接")
        self._device_label.setStyleSheet("color: #617A9D; font-size: 13px;")
        conn_layout.addWidget(self._device_label, 1)

        # 连接/断开按钮
        self._btn_connect = QPushButton("  连接设备  ")
        self._btn_connect.setObjectName("btn_connect")
        self._btn_connect.setStyleSheet("""
            QPushButton#btn_connect {
                background-color: #00B894; color: white;
                font-size: 13px; font-weight: bold;
                border: none; border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton#btn_connect:hover { background-color: #00A381; }
            QPushButton#btn_connect:pressed { background-color: #009070; }
            QPushButton#btn_connect:disabled { background-color: #ccc; }
        """)
        self._btn_connect.clicked.connect(self._on_connect)
        conn_layout.addWidget(self._btn_connect)

        self._btn_disconnect = QPushButton("  断开  ")
        self._btn_disconnect.setObjectName("btn_disconnect")
        self._btn_disconnect.setStyleSheet("""
            QPushButton#btn_disconnect {
                background-color: #E17055; color: white;
                font-size: 13px; font-weight: bold;
                border: none; border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton#btn_disconnect:hover { background-color: #D35400; }
        """)
        self._btn_disconnect.setEnabled(False)
        self._btn_disconnect.clicked.connect(self._on_disconnect)
        conn_layout.addWidget(self._btn_disconnect)

        # 检测按钮
        self._btn_detect = QPushButton("🔍 检测")
        self._btn_detect.setStyleSheet("""
            QPushButton {
                background-color: #74B9FF; color: white;
                font-size: 12px; border: none; border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover { background-color: #0984E3; }
        """)
        self._btn_detect.clicked.connect(self._on_detect)
        conn_layout.addWidget(self._btn_detect)

        main_layout.addWidget(conn_group)

        # ========== 2. 主内容区 ==========
        content_splitter = QSplitter(Qt.Orientation.Vertical)

        # ---- 左侧: 测试配置 ----
        left_panel = QWidget()
        left_panel.setMinimumWidth(540)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 测试类型选择
        type_group = QGroupBox("测试类型")
        type_layout = QVBoxLayout(type_group)
        self._combo_type = QComboBox()
        self._combo_type.setMinimumHeight(32)
        self._combo_type.setStyleSheet("font-size: 13px; padding: 4px;")
        self._combo_type.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self._combo_type)
        left_layout.addWidget(type_group)

        # 模块描述
        self._desc_browser = QTextBrowser()
        self._desc_browser.setMinimumHeight(96)
        self._desc_browser.setMaximumHeight(128)
        self._desc_browser.setOpenExternalLinks(False)
        self._desc_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #F8FBFF;
                border: 1px solid rgba(79, 140, 255, 0.12);
                border-radius: 12px;
                padding: 8px;
                font-size: 12px;
                color: #294469;
            }
        """)
        left_layout.addWidget(self._desc_browser)

        # 输入文件选择
        self._file_group = QGroupBox("输入文件")
        file_layout = QVBoxLayout(self._file_group)
        self._file_selector = FileSelector(label="")
        self._file_selector.file_selected.connect(lambda _p: self._update_run_state())
        file_layout.addWidget(self._file_selector)
        left_layout.addWidget(self._file_group)

        # 参数配置
        param_group = QGroupBox("参数配置")
        param_group.setMinimumHeight(240)
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setFrameShape(QFrame.Shape.NoFrame)
        param_scroll.setMinimumHeight(200)
        param_scroll.setStyleSheet("""
            QScrollArea { background-color: #FFFFFF; border: none; }
            QScrollArea > QWidget > QWidget { background-color: #FFFFFF; }
        """)
        self._param_editor = ParamEditor()
        self._param_editor.setStyleSheet("background-color: #FFFFFF;")
        param_scroll.setWidget(self._param_editor)
        param_layout = QVBoxLayout(param_group)
        param_layout.setContentsMargins(6, 4, 6, 6)
        param_layout.addWidget(param_scroll)
        left_layout.addWidget(param_group, 1)

        # 输出目录
        out_group = QGroupBox("输出目录")
        out_layout = QHBoxLayout(out_group)
        self._output_label = QLabel("")
        self._output_label.setStyleSheet("color: #617A9D; font-size: 12px;")
        self._output_label.setWordWrap(True)
        out_layout.addWidget(self._output_label, 1)
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self._browse_output)
        out_layout.addWidget(btn_browse)
        left_layout.addWidget(out_group)

        # 设置默认输出路径
        default_out = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "reports", "HW_Test_Results")
        self._output_dir = default_out
        self._output_label.setText(default_out)

        # 执行按钮区
        btn_row = QHBoxLayout()

        self._btn_run = QPushButton("▶  开始测试")
        self._btn_run.setObjectName("btn_run_test")
        self._btn_run.setMinimumHeight(42)
        self._btn_run.setStyleSheet("""
            QPushButton#btn_run_test {
                background-color: #0984E3; color: white;
                font-size: 15px; font-weight: bold;
                border: none; border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton#btn_run_test:hover { background-color: #0770C2; }
            QPushButton#btn_run_test:pressed { background-color: #065BA1; }
            QPushButton#btn_run_test:disabled { background-color: #B0BEC5; }
        """)
        self._btn_run.setEnabled(False)
        self._btn_run.clicked.connect(self._on_run)
        btn_row.addWidget(self._btn_run)

        self._btn_stop = QPushButton("■  停止")
        self._btn_stop.setObjectName("btn_stop_test")
        self._btn_stop.setMinimumHeight(42)
        self._btn_stop.setStyleSheet("""
            QPushButton#btn_stop_test {
                background-color: #E17055; color: white;
                font-size: 14px; font-weight: bold;
                border: none; border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton#btn_stop_test:hover { background-color: #D35400; }
            QPushButton#btn_stop_test:disabled { background-color: #ccc; }
        """)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self._btn_stop)

        left_layout.addLayout(btn_row)

        # 进度条
        self._progress = ProgressWidget()
        left_layout.addWidget(self._progress)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setWidget(left_panel)

        content_splitter.addWidget(left_scroll)

        # ---- 底部: 实时日志 ----
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        log_header = QLabel("📋 测试日志")
        log_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #32598E;")
        bottom_layout.addWidget(log_header)

        self._log_browser = QTextBrowser()
        self._log_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #0D1117;
                color: #C8D6E5;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid rgba(56, 139, 253, 0.25);
                border-radius: 12px;
                padding: 8px;
            }
            QScrollBar:vertical {
                background: #161B22;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #30363D;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #484F58;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self._log_browser.setMinimumHeight(180)
        bottom_layout.addWidget(self._log_browser, 1)

        # 结果摘要
        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet("""
            QLabel {
                background-color: #F8FBFF;
                color: #294469;
                border: 1px solid rgba(79, 140, 255, 0.12);
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self._result_label.setVisible(False)
        bottom_layout.addWidget(self._result_label)

        content_splitter.addWidget(bottom_panel)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStretchFactor(0, 7)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([620, 250])

        main_layout.addWidget(content_splitter, 1)

        # 初始化模块列表
        self.refresh_modules()

    # ──────────── 模块管理 ────────────

    def refresh_modules(self):
        """刷新测试模块列表"""
        self._module_ids = []
        modules = task_registry.get_modules("test")
        self._combo_type.blockSignals(True)
        self._combo_type.clear()
        for mid, mdata in modules.items():
            info = mdata['info']
            if info.get('enabled', True):
                self._combo_type.addItem(info['name'])
                self._module_ids.append(mid)
        self._combo_type.blockSignals(False)

        if self._module_ids:
            self._on_type_changed(0)

    def _on_type_changed(self, index):
        """切换测试类型"""
        if index < 0 or index >= len(self._module_ids):
            return

        mid = self._module_ids[index]
        entry = task_registry.get_module(mid)
        if not entry:
            return
        info = entry['info']

        # 更新描述
        self._desc_browser.setHtml(self._build_desc_html(info))

        # 更新参数
        self._param_editor.set_params(info.get('params', []))

        # 更新文件选择器可见性及过滤器
        _itype = info.get('input_type', 'none')
        needs_file = _itype != 'none'
        self._file_group.setVisible(needs_file)
        _filters = {
            'csv':      "CSV文件 (*.csv);;所有文件 (*)",
            'txt':      "文本文件 (*.txt);;所有文件 (*)",
            'data':     "数据文件 (*.csv *.txt);;CSV (*.csv);;TXT (*.txt);;所有文件 (*)",
            'optional': "数据文件 (*.csv *.txt *.dat);;所有文件 (*)",
        }
        self._file_selector._file_filter = _filters.get(_itype, "所有文件 (*)")

        # 更新运行按钮状态
        self._update_run_state()

    def _build_desc_html(self, info: dict) -> str:
        """构建模块描述 HTML"""
        desc = info.get('description', '').replace('\n', '<br>')
        inp = info.get('input_description', '')
        out_type = info.get('output_type', '')

        html = f"""
        <div style="font-family: 'Microsoft YaHei'; line-height: 1.6;">
            <div style="color: #294469; font-size: 13px; margin-bottom: 8px;">{desc}</div>
            <div style="margin-top: 6px;">
                <span style="background: #EEF5FF; color: #3561A8; padding: 2px 8px;
                       border-radius: 4px; font-size: 11px;">
                    📥 输入: {inp or '无'}
                </span>
                <span style="background: #EEF5FF; color: #3561A8; padding: 2px 8px;
                       border-radius: 4px; font-size: 11px; margin-left: 6px;">
                    📤 输出: {out_type.upper()}
                </span>
            </div>
        </div>
        """
        return html

    # ──────────── 设备连接 ────────────

    def _get_manager(self):
        """延迟导入并获取 DLPManager"""
        if self._dlp_manager is None:
            try:
                from dlpc_sdk import DLPManager
                self._dlp_manager = DLPManager()
            except ImportError:
                self._log_msg("dlpc_sdk 模块导入失败", "ERROR")
                return None
        return self._dlp_manager

    def _on_connect(self):
        """连接设备"""
        self._btn_connect.setEnabled(False)
        self._btn_connect.setText("  连接中...  ")
        self._log_msg("正在连接 DLPC8430...", "INFO")

        # 使用 QTimer 避免阻塞 UI
        QTimer.singleShot(100, self._do_connect)

    def _do_connect(self):
        """执行连接 (通过 QTimer 延迟调用)"""
        try:
            mgr = self._get_manager()
            if mgr is None:
                self._update_conn_ui(False, "SDK 初始化失败")
                return

            res = mgr.connect()
            if res['success']:
                self._update_conn_ui(True, res['message'])
                self._log_msg(res['message'], "SUCCESS")
                self._status_timer.start()

                # 尝试读取版本
                try:
                    ver = mgr.read_version()
                    if ver['success']:
                        self._log_msg(f"固件版本: {ver['version']}", "INFO")
                except Exception:
                    pass
            else:
                self._update_conn_ui(False, res['message'])
                self._log_msg(f"连接失败: {res['message']}", "ERROR")
        except Exception as e:
            import traceback
            self._update_conn_ui(False, str(e))
            self._log_msg(f"连接异常: {traceback.format_exc()}", "ERROR")

    def _on_disconnect(self):
        """断开连接"""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "提示", "测试执行中不可直接断开设备，请先停止测试")
            return
        mgr = self._get_manager()
        if mgr:
            mgr.disconnect()
        self._status_timer.stop()
        self._update_conn_ui(False, "已断开")
        self._log_msg("设备已断开", "INFO")

    def _on_detect(self):
        """检测设备"""
        self._log_msg("检测 DLPC8430 设备...", "INFO")
        try:
            from dlpc_sdk.usb_connection import USBBulkConnection
            result = USBBulkConnection.find_device()
            if result['found']:
                self._log_msg(f"✅ 发现设备: {result['desc']}", "SUCCESS")
                self._device_label.setText(f"已发现: {result['desc']}")
            else:
                self._log_msg(f"❌ 未发现设备: {result['desc']}", "WARNING")
                self._device_label.setText(f"未发现: {result['desc']}")
        except Exception as e:
            self._log_msg(f"检测异常: {e}", "ERROR")

    def _update_conn_ui(self, connected: bool, message: str):
        """更新连接 UI 状态"""
        if connected:
            self._status_dot.setStyleSheet("color: #00B894; font-size: 18px;")
            self._device_label.setText(message)
            self._device_label.setStyleSheet("color: #00B894; font-size: 13px;")
            self._btn_connect.setEnabled(False)
            self._btn_connect.setText("  已连接  ")
            self._btn_disconnect.setEnabled(True)
        else:
            self._status_dot.setStyleSheet("color: #E17055; font-size: 18px;")
            self._device_label.setText(message)
            self._device_label.setStyleSheet("color: #666; font-size: 13px;")
            self._btn_connect.setEnabled(True)
            self._btn_connect.setText("  连接设备  ")
            self._btn_disconnect.setEnabled(False)

        self._update_run_state()

    def _refresh_device_status(self):
        """定时刷新设备状态"""
        mgr = self._get_manager()
        if mgr and not mgr.connected:
            self._status_timer.stop()
            self._update_conn_ui(False, "连接已丢失")
            self._log_msg("⚠ 设备连接已丢失", "WARNING")

    def _update_run_state(self):
        """更新运行按钮可用状态"""
        mgr = self._get_manager()
        connected = mgr.connected if mgr else False
        running = self._worker is not None and self._worker.isRunning()

        # 需要文件的模块检查文件是否已选（optional 类型文件为可选，不阻塞按钮）
        file_ok = True
        _itype = ''
        if self._module_ids:
            idx = self._combo_type.currentIndex()
            if 0 <= idx < len(self._module_ids):
                entry = task_registry.get_module(self._module_ids[idx])
                if entry:
                    _itype = entry['info'].get('input_type', 'none')
        if self._file_group.isVisible() and _itype not in ('none', 'optional'):
            file_ok = bool(self._resolve_input_path(self._file_selector.get_path()))

        self._btn_run.setEnabled(connected and not running and file_ok)
        self._btn_stop.setEnabled(running)
        self._btn_disconnect.setEnabled(connected and not running)

    def _resolve_input_path(self, raw_path: str) -> str:
        """支持绝对路径与相对路径解析。"""
        raw_path = (raw_path or '').strip().strip('"')
        if not raw_path:
            return ''
        if os.path.exists(raw_path):
            return os.path.abspath(raw_path)

        candidates = []

        if self._config_mgr:
            project_root = self._config_mgr.get_project_root()
            if project_root:
                candidates.append(os.path.join(project_root, raw_path))

        # test_ui 根目录 / code 根目录 / code 下各项目目录
        test_ui_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        code_root = os.path.dirname(test_ui_root)
        candidates.append(os.path.join(test_ui_root, raw_path))
        candidates.append(os.path.join(code_root, raw_path))

        try:
            for name in os.listdir(code_root):
                sub = os.path.join(code_root, name)
                if os.path.isdir(sub):
                    candidates.append(os.path.join(sub, raw_path))
        except OSError:
            pass

        for path in candidates:
            if os.path.exists(path):
                return os.path.abspath(path)
        return ''

    # ──────────── 测试执行 ────────────

    def _browse_output(self):
        """选择输出目录"""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录", self._output_dir)
        if path:
            self._output_dir = path
            self._output_label.setText(path)

    def _on_run(self):
        """开始测试"""
        idx = self._combo_type.currentIndex()
        if idx < 0 or idx >= len(self._module_ids):
            return

        mid = self._module_ids[idx]
        entry = task_registry.get_module(mid)
        if not entry:
            return
        info = entry['info']
        mod = entry['module']

        # 获取参数
        params = self._param_editor.get_values()

        # 获取输入文件
        input_path = ""
        _input_type = info.get('input_type', 'none')
        if _input_type not in ('none', 'optional'):
            input_path = self._resolve_input_path(self._file_selector.get_path())
            if not input_path:
                QMessageBox.warning(self, "提示", "请先选择输入文件")
                return
        elif _input_type == 'optional':
            input_path = self._resolve_input_path(self._file_selector.get_path()) or self._file_selector.get_path()

        # 确保输出目录存在
        os.makedirs(self._output_dir, exist_ok=True)

        # 清空日志
        self._log_browser.clear()
        self._result_label.setVisible(False)

        self._log_msg(f"启动测试: {info['name']}", "INFO")
        self._log_msg(f"参数: {params}", "INFO")

        # 启动 Worker
        self._worker = TaskWorker(
            run_func=mod.run,
            input_path=input_path,
            output_dir=self._output_dir,
            params=params,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.log_message.connect(self._on_worker_log)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self._btn_run.setEnabled(False)
        self._btn_stop.setEnabled(True)

    def _on_stop(self):
        """停止测试"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()  # 触发 cancel_event，供 run() 函数检测
            self._btn_stop.setEnabled(False)
            self._log_msg("正在停止测试...", "WARNING")

    def _on_progress(self, current, total):
        """进度更新"""
        if total > 0:
            pct = int(current * 100 / total)
            self._progress.set_value(pct)

    def _on_worker_log(self, message, level):
        """Worker 日志"""
        self._log_msg(message, level)

    def _on_finished(self, result: dict):
        """测试完成/停止"""
        self._btn_run.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._progress.set_value(100)
        self._worker = None

        status = result.get('status', 'error')
        message = result.get('message', '')
        output = result.get('output_path', '')

        if status == 'cancelled':
            self._log_msg("测试已停止", "WARNING")
            if output:
                self._log_msg(f"已保存结果: {output}", "INFO")
            self._update_run_state()
            return

        # 显示结果摘要
        summary = result.get('summary', {})
        if summary:
            passed = summary.get('passed', 0)
            failed = summary.get('failed', summary.get('fail_count', 0))
            elapsed = summary.get('elapsed_sec', 0)

            color = '#27AE60' if failed == 0 else '#E74C3C'
            self._result_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color}22;
                    border: 1px solid {color};
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                    color: #333;
                }}
            """)
            self._result_label.setText(
                f"{'✅' if failed == 0 else '⚠️'} {message}\n"
                f"⏱ 耗时: {elapsed}秒"
            )
            self._result_label.setVisible(True)

        if output:
            self._log_msg(f"结果文件: {output}", "SUCCESS")

        if self._log_panel:
            self._log_panel.append_log(
                f"测试完成 [{status.upper()}]: {message}", 
                "SUCCESS" if status == 'success' else "WARNING")

        self._update_run_state()

    def _on_error(self, msg):
        """测试异常"""
        self._log_msg(f"测试异常: {msg}", "ERROR")
        self._btn_run.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._progress.set_value(0)
        self._worker = None

        if self._log_panel:
            self._log_panel.append_log(f"测试异常: {msg}", "ERROR")

        self._update_run_state()

    # ──────────── 日志工具 ────────────

    def _log_msg(self, message: str, level: str = "INFO"):
        """向测试日志区写入消息"""
        colors = {
            "INFO": "#C8D6E5",
            "SUCCESS": "#55EFC4",
            "WARNING": "#FDCB6E",
            "ERROR": "#FF7675",
            "DEBUG": "#74B9FF",
        }
        color = colors.get(level, "#C8D6E5")
        ts = time.strftime("%H:%M:%S")
        self._log_browser.append(
            f'<span style="color:#636E72">[{ts}]</span> '
            f'<span style="color:{color}">{message}</span>'
        )
        # 滚动到底部
        bar = self._log_browser.verticalScrollBar()
        bar.setValue(bar.maximum())
