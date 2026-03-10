# -*- coding: utf-8 -*-
"""
Analysis 功能页

选择分析类型 → 配置参数 → 选择输入文件 → 执行 → 图表内嵌显示
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                              QComboBox, QLabel, QPushButton, QGroupBox,
                              QMessageBox, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt

from ui.widgets.file_selector import FileSelector
from ui.widgets.param_editor import ParamEditor
from ui.widgets.matplotlib_canvas import PlotWidget
from ui.widgets.progress_bar import ProgressWidget
from workers.task_worker import TaskWorker
from core import task_registry


class AnalysisPage(QWidget):
    """分析执行页面"""

    def __init__(self, log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ======= 左侧控制面板 =======
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)

        # 分析类型选择
        type_group = QGroupBox("分析类型")
        type_layout = QVBoxLayout(type_group)
        self.combo_type = QComboBox()
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.combo_type)

        self.lbl_description = QLabel("")
        self.lbl_description.setWordWrap(True)
        self.lbl_description.setStyleSheet("color: #666; font-size: 12px;")
        type_layout.addWidget(self.lbl_description)
        left_layout.addWidget(type_group)

        # 输入文件选择
        file_group = QGroupBox("输入数据")
        file_layout = QVBoxLayout(file_group)
        self.file_selector = FileSelector(
            label="",
            description="请选择对应格式的数据文件"
        )
        file_layout.addWidget(self.file_selector)
        left_layout.addWidget(file_group)

        # 参数配置
        param_group = QGroupBox("参数配置")
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        self.param_editor = ParamEditor()
        param_scroll.setWidget(self.param_editor)
        param_layout = QVBoxLayout(param_group)
        param_layout.addWidget(param_scroll)
        left_layout.addWidget(param_group)

        # 执行按钮
        btn_layout = QHBoxLayout()
        self.btn_execute = QPushButton("  执行分析  ")
        self.btn_execute.setObjectName("btn_primary")
        self.btn_execute.clicked.connect(self._on_execute)
        btn_layout.addWidget(self.btn_execute)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("btn_danger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_export = QPushButton("导出图片")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(self.btn_export)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        # 进度条
        self.progress = ProgressWidget()
        left_layout.addWidget(self.progress)

        left_layout.addStretch()
        left_panel.setMaximumWidth(420)

        # ======= 右侧图表显示区 =======
        self.plot_widget = PlotWidget()

        splitter.addWidget(left_panel)
        splitter.addWidget(self.plot_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 模块ID列表（与 combo 索引对应）
        self._module_ids = []

    def refresh_modules(self):
        """刷新模块列表（从 task_registry 获取）"""
        self.combo_type.clear()
        self._module_ids.clear()

        modules = task_registry.get_modules('analysis')
        for mid, mdata in modules.items():
            info = mdata['info']
            self.combo_type.addItem(info['name'])
            self._module_ids.append(mid)

        if not self._module_ids:
            self.combo_type.addItem("（无可用分析模块）")

    def _on_type_changed(self, index):
        """分析类型切换"""
        if index < 0 or index >= len(self._module_ids):
            return

        mid = self._module_ids[index]
        mdata = task_registry.get_module(mid)
        if not mdata:
            return

        info = mdata['info']

        # 更新描述
        self.lbl_description.setText(
            f"{info.get('description', '')}\n\n"
            f"输入格式: {info.get('input_type', 'N/A').upper()}\n"
            f"{info.get('input_description', '')}\n\n"
            f"输出格式: {info.get('output_type', 'N/A').upper()}"
        )

        # 更新文件选择器过滤
        input_type = info.get('input_type', 'csv')
        filters = {
            'csv': "CSV文件 (*.csv);;所有文件 (*)",
            'txt': "文本文件 (*.txt);;所有文件 (*)",
            'directory': "",
        }
        self.file_selector._file_filter = filters.get(input_type, "所有文件 (*)")
        self.file_selector._select_dir = (input_type == 'directory')

        # 更新参数表单
        params = info.get('params', [])
        self.param_editor.set_params(params)

    def _on_execute(self):
        """执行分析"""
        if not self._module_ids:
            QMessageBox.warning(self, "提示", "没有可用的分析模块")
            return

        index = self.combo_type.currentIndex()
        if index < 0 or index >= len(self._module_ids):
            return

        mid = self._module_ids[index]
        mdata = task_registry.get_module(mid)
        if not mdata:
            return

        # 获取输入路径
        input_path = self.file_selector.get_path()
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "输入错误",
                                "请选择有效的输入文件或目录")
            return

        # 获取输出目录
        project_root = ''
        if self._config_mgr:
            project_root = self._config_mgr.get_project_root()
        if not project_root:
            project_root = os.path.dirname(os.path.dirname(input_path))

        output_dir = os.path.join(project_root, 'reports')

        # 获取参数
        params = self.param_editor.get_values()
        params['project_root'] = project_root

        # 日志
        if self._log_panel:
            self._log_panel.append_log(
                f"开始执行: {mdata['info']['name']}", "INFO")
            self._log_panel.append_log(f"输入: {input_path}", "INFO")

        # 创建工作线程
        self.btn_execute.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_export.setEnabled(False)
        self.progress.set_running()

        self._worker = TaskWorker(
            run_func=mdata['module'].run,
            input_path=input_path,
            output_dir=output_dir,
            params=params,
        )
        self._worker.progress.connect(self.progress.update_progress)
        self._worker.log_message.connect(self._on_worker_log)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_cancel(self):
        """取消执行"""
        if self._worker:
            self._worker.cancel()
        self.progress.set_cancelled()
        self.btn_execute.setEnabled(True)
        self.btn_cancel.setEnabled(False)

    def _on_worker_log(self, message, level):
        """工作线程日志"""
        if self._log_panel:
            self._log_panel.append_log(message, level)

    def _on_worker_finished(self, result):
        """工作线程完成"""
        self.btn_execute.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        status = result.get('status', 'error')
        if status == 'success':
            self.progress.set_success()

            # 显示图表
            fig = result.get('figure')
            if fig:
                self.plot_widget.display_figure(fig)
                self.btn_export.setEnabled(True)

            output_path = result.get('output_path', '')
            if self._log_panel:
                self._log_panel.append_log(
                    f"执行成功! 输出: {output_path}", "SUCCESS")

            QMessageBox.information(self, "完成",
                                    f"分析执行成功\n输出: {output_path}")

        elif status == 'cancelled':
            self.progress.set_cancelled()
            if self._log_panel:
                self._log_panel.append_log("任务已取消", "WARNING")

        else:
            self.progress.set_error()
            msg = result.get('message', '未知错误')
            if self._log_panel:
                self._log_panel.append_log(f"执行失败: {msg}", "ERROR")
            QMessageBox.critical(self, "错误", f"执行失败:\n{msg}")

    def _on_worker_error(self, error_msg):
        """工作线程异常"""
        self.btn_execute.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress.set_error()
        if self._log_panel:
            self._log_panel.append_log(f"异常: {error_msg}", "ERROR")
        QMessageBox.critical(self, "异常", f"执行异常:\n{error_msg}")

    def _on_export(self):
        """导出当前图表"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出图片", "",
            "PNG图片 (*.png);;SVG矢量图 (*.svg);;PDF文档 (*.pdf)")
        if filepath:
            dpi = 150
            if self._config_mgr:
                dpi = self._config_mgr.get('visualization.dpi', 150)
            self.plot_widget.save_figure(filepath, dpi)
            if self._log_panel:
                self._log_panel.append_log(f"图片已导出: {filepath}", "SUCCESS")
