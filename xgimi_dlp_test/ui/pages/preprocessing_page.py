# -*- coding: utf-8 -*-
"""
数据预处理页面

三个预处理功能以 Tab 展示：CSV拆分象限 / CSV转TXT / ErrorCode提取
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QGroupBox,
                              QPushButton, QLabel, QHBoxLayout, QMessageBox,
                              QScrollArea, QFrame)
from PyQt6.QtCore import Qt

from ui.widgets.file_selector import FileSelector
from ui.widgets.param_editor import ParamEditor
from ui.widgets.progress_bar import ProgressWidget
from workers.task_worker import TaskWorker
from core import task_registry


class PreprocessingCard(QWidget):
    """单个预处理功能卡片"""

    def __init__(self, module_id: str, module_info: dict, module_obj,
                 log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self._module_id = module_id
        self._module_info = module_info
        self._module_obj = module_obj
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 描述
        desc = QLabel(self._module_info.get('description', ''))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # 输入格式说明
        input_desc = self._module_info.get('input_description', '')
        if input_desc:
            fmt_label = QLabel(f"输入格式: {input_desc}")
            fmt_label.setWordWrap(True)
            fmt_label.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(fmt_label)

        # 文件选择
        input_type = self._module_info.get('input_type', 'csv')
        filters_map = {
            'csv':      "CSV文件 (*.csv);;所有文件 (*)",
            'txt':      "文本文件 (*.txt);;所有文件 (*)",
            'data':     "数据文件 (*.csv *.txt);;所有文件 (*)",
            'optional': "数据文件 (*.csv *.txt);;所有文件 (*)",
            'directory': "",
        }
        self._needs_file = input_type not in ('none',)
        if self._needs_file:
            self.file_selector = FileSelector(
                label="输入文件",
                file_filter=filters_map.get(input_type, "所有文件 (*)"),
                select_dir=(input_type == 'directory'),
            )
            layout.addWidget(self.file_selector)
        else:
            self.file_selector = None

        # 参数（带滚动区域，防止参数过多时控件重叠）
        params = self._module_info.get('params', [])
        if params:
            param_group = QGroupBox("参数")
            param_scroll = QScrollArea()
            param_scroll.setWidgetResizable(True)
            param_scroll.setFrameShape(QFrame.Shape.NoFrame)
            param_scroll.setMinimumHeight(180)
            self.param_editor = ParamEditor()
            self.param_editor.set_params(params)
            param_scroll.setWidget(self.param_editor)
            param_layout = QVBoxLayout(param_group)
            param_layout.setContentsMargins(4, 4, 4, 4)
            param_layout.addWidget(param_scroll)
            layout.addWidget(param_group, 1)  # stretch=1，填充剩余空间
        else:
            self.param_editor = None

        # 执行按钮 + 状态
        btn_layout = QHBoxLayout()
        self.btn_execute = QPushButton("  执行  ")
        self.btn_execute.setObjectName("btn_primary")
        self.btn_execute.clicked.connect(self._on_execute)
        btn_layout.addWidget(self.btn_execute)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #999; font-size: 18px;")
        self.status_indicator.setToolTip("待执行")
        btn_layout.addWidget(self.status_indicator)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 进度条
        self.progress = ProgressWidget()
        layout.addWidget(self.progress)

        layout.addStretch()

    def _on_execute(self):
        """执行预处理"""
        input_path = self.file_selector.get_path() if self.file_selector else ''
        if self._needs_file and (not input_path or not os.path.exists(input_path)):
            QMessageBox.warning(self, "输入错误", "请选择有效的输入文件或目录")
            return

        project_root = ''
        if self._config_mgr:
            project_root = self._config_mgr.get_project_root()
        if project_root:
            output_dir = os.path.join(project_root, 'data')
        elif input_path:
            output_dir = os.path.dirname(input_path)
        else:
            # input_type=none 时使用应用目录下的 reports
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))),
                'reports', 'preprocessed'
            )

        params = self.param_editor.get_values() if self.param_editor else {}
        params['project_root'] = project_root

        self.btn_execute.setEnabled(False)
        self.progress.set_running()
        self.status_indicator.setStyleSheet("color: #FFC107; font-size: 18px;")
        self.status_indicator.setToolTip("执行中")

        if self._log_panel:
            self._log_panel.append_log(
                f"开始预处理: {self._module_info['name']}", "INFO")

        self._worker = TaskWorker(
            run_func=self._module_obj.run,
            input_path=input_path,
            output_dir=output_dir,
            params=params,
        )
        self._worker.progress.connect(self.progress.update_progress)
        self._worker.log_message.connect(self._on_log)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_log(self, message, level):
        if self._log_panel:
            self._log_panel.append_log(message, level)

    def _on_finished(self, result):
        self.btn_execute.setEnabled(True)
        status = result.get('status', 'error')
        if status == 'success':
            self.progress.set_success()
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 18px;")
            self.status_indicator.setToolTip("成功")
            if self._log_panel:
                self._log_panel.append_log(
                    f"预处理完成: {result.get('output_path', '')}", "SUCCESS")
        else:
            self.progress.set_error()
            self.status_indicator.setStyleSheet("color: #F44336; font-size: 18px;")
            self.status_indicator.setToolTip("失败")
            if self._log_panel:
                self._log_panel.append_log(
                    f"预处理失败: {result.get('message', '')}", "ERROR")

    def _on_error(self, error_msg):
        self.btn_execute.setEnabled(True)
        self.progress.set_error()
        self.status_indicator.setStyleSheet("color: #F44336; font-size: 18px;")
        if self._log_panel:
            self._log_panel.append_log(f"异常: {error_msg}", "ERROR")


class PreprocessingPage(QWidget):
    """数据预处理页面"""

    def __init__(self, log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._cards = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("数据预处理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

    def refresh_modules(self):
        """刷新预处理模块列表"""
        self.tab_widget.clear()
        self._cards.clear()

        modules = task_registry.get_modules('preprocessing')
        for mid, mdata in modules.items():
            info = mdata['info']
            if not info.get('enabled', True):
                continue
            card = PreprocessingCard(
                module_id=mid,
                module_info=info,
                module_obj=mdata['module'],
                log_panel=self._log_panel,
                config_mgr=self._config_mgr,
            )
            self.tab_widget.addTab(card, info['name'])
            self._cards.append(card)

        if not modules:
            placeholder = QLabel("暂无预处理模块")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tab_widget.addTab(placeholder, "无模块")
