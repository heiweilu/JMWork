# -*- coding: utf-8 -*-
"""
Analysis 功能页

选择分析类型 → 配置参数 → 选择输入文件 → 执行 → 图表内嵌显示
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                              QComboBox, QLabel, QPushButton, QGroupBox,
                              QMessageBox, QFileDialog, QScrollArea,
                              QTabWidget, QSizePolicy, QTextBrowser, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

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
        self._last_output_path = ''   # 记录最近一次成功输出路径
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

        # 模块描述信息（富文本卡片）
        self.txt_description = QTextBrowser()
        self.txt_description.setReadOnly(True)
        self.txt_description.setOpenExternalLinks(False)
        self.txt_description.setFrameShape(QFrame.Shape.NoFrame)
        self.txt_description.setFixedHeight(150)
        self.txt_description.setStyleSheet(
            "QTextBrowser { background: rgba(248, 251, 255, 0.72);"
            "border: 1px solid rgba(123, 168, 228, 0.10);"
            "border-radius: 12px; padding: 8px; }"
        )
        type_layout.addWidget(self.txt_description)
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

        # 参数配置（可展开填充剩余空间）
        param_group = QGroupBox("参数配置")
        param_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setMinimumHeight(80)
        param_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.param_editor = ParamEditor()
        param_scroll.setWidget(self.param_editor)
        param_layout = QVBoxLayout(param_group)
        param_layout.setContentsMargins(8, 4, 8, 8)
        param_layout.addWidget(param_scroll)
        left_layout.addWidget(param_group, 1)  # stretch=1，填充剩余空间

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

        self.btn_open_output = QPushButton("📂 打开结果目录")
        self.btn_open_output.setObjectName("btn_open_output")
        self.btn_open_output.setMinimumWidth(140)
        self.btn_open_output.setEnabled(False)
        self.btn_open_output.setToolTip("在文件管理器中打开分析结果所在目录")
        self.btn_open_output.clicked.connect(self._on_open_output)
        btn_layout.addWidget(self.btn_open_output)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        # 进度条
        self.progress = ProgressWidget()
        left_layout.addWidget(self.progress)

        left_panel.setMinimumWidth(430)
        left_panel.setMaximumWidth(500)

        # ======= 右侧: Tab(参考结果 | 分析结果) =======
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet(
            "QTabBar::tab { padding: 6px 18px; font-size: 12px; }"
            "QTabBar::tab:selected { font-weight: bold; color: #2A64D6; }"
        )

        # Tab0: 参考结果
        self.ref_scroll = QScrollArea()
        self.ref_scroll.setWidgetResizable(True)
        self.ref_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_content = QWidget()
        self.ref_layout = QVBoxLayout(self.ref_content)
        self.ref_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_image_label = QLabel()
        self.ref_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_image_label.setScaledContents(False)
        self.ref_text_label = QLabel()
        self.ref_text_label.setWordWrap(True)
        self.ref_text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.ref_text_label.setStyleSheet(
            "font-size: 13px; color: #4B6387; padding: 16px; line-height: 1.8;"
        )
        self.ref_layout.addWidget(self.ref_image_label)
        self.ref_layout.addWidget(self.ref_text_label)
        self.ref_layout.addStretch()
        self.ref_scroll.setWidget(self.ref_content)
        self.right_tabs.addTab(self.ref_scroll, "📷  参考结果")

        # Tab1: 分析结果
        self.plot_widget = PlotWidget()
        self.right_tabs.addTab(self.plot_widget, "📈  分析结果")

        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 模块ID列表（与 combo 索引对应）
        self._module_ids = []

    # 参考图所在目录
    ASSETS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'assets', 'reference_images'
    )

    def refresh_modules(self):
        """刷新模块列表（从 task_registry 获取）"""
        self.combo_type.clear()
        self._module_ids.clear()

        modules = task_registry.get_modules('analysis')
        for mid, mdata in modules.items():
            info = mdata['info']
            if not info.get('enabled', True):
                continue
            script = info.get('script_file', '')
            # 显示格式："模块名  -  script.py"
            label = f"{info['name']}  —  {script}" if script else info['name']
            self.combo_type.addItem(label)
            self._module_ids.append(mid)

        if not self._module_ids:
            self.combo_type.addItem("（无可用分析模块）")
        else:
            # 触发初始模块的描述及参数显示
            self._on_type_changed(0)

    def _build_desc_html(self, info: dict) -> str:
        """将模块信息构建为富文本 HTML"""
        desc = info.get('description', '').replace('\n', '<br>')
        input_type = info.get('input_type', 'N/A').upper()
        input_desc = info.get('input_description', '').replace('\n', '<br>')
        output_type = info.get('output_type', 'N/A').upper()
        script = info.get('script_file', '')

        output_colors = {
            'IMAGE': ('#E8F5E9', '#4CAF50', '#2E7D32', '#1B5E20'),
            'CSV': ('#FFF8E1', '#FF8F00', '#E65100', '#BF360C'),
            'EXCEL': ('#F3E5F5', '#9C27B0', '#6A1B9A', '#4A148C'),
            'HTML': ('#FCE4EC', '#E91E63', '#880E4F', '#880E4F'),
        }
        oc = output_colors.get(output_type, ('#E3F2FD', '#2196F3', '#0D47A1', '#1565C0'))

        script_html = ''
        if script:
            script_html = (
                f"<div style='background:#F8F9FA; border-left:3px solid #9E9E9E; "
                f"border-radius:3px; padding:4px 10px; margin:4px 0;'>"
                f"<span style='color:#546E7A; font-size:11px;'>💻 脚本文件: "
                f"<b>{script}</b></span></div>"
            )

        return (
            f"<div style='font-family:\"Microsoft YaHei\",sans-serif; padding:4px 0;'>"
            f"<p style='color:#1565C0; font-size:13px; font-weight:bold; margin:0 0 6px 0;'>"
            f"📋 模块说明</p>"
            f"<p style='color:#37474F; font-size:12px; line-height:1.65; margin:0 0 8px 0;'>"
            f"{desc}</p>"
            f"<div style='background:#E8F5E9; border-left:3px solid #4CAF50; "
            f"border-radius:3px; padding:5px 10px; margin:3px 0;'>"
            f"<span style='color:#2E7D32; font-weight:bold; font-size:12px;'>📂 输入格式: "
            f"<span style='background:#C8E6C9; border-radius:3px; padding:1px 5px;'>{input_type}</span></span>"
            f"<br><span style='color:#388E3C; font-size:11px;'>{input_desc}</span>"
            f"</div>"
            f"<div style='background:{oc[0]}; border-left:3px solid {oc[1]}; "
            f"border-radius:3px; padding:5px 10px; margin:3px 0;'>"
            f"<span style='color:{oc[2]}; font-weight:bold; font-size:12px;'>📊 输出格式: "
            f"<span style='background:{oc[0]}; border-radius:3px; padding:1px 5px; "
            f"color:{oc[3]};'>{output_type}</span></span>"
            f"</div>"
            f"{script_html}"
            f"</div>"
        )

    def _on_type_changed(self, index):
        """分析类型切换"""
        if index < 0 or index >= len(self._module_ids):
            return

        mid = self._module_ids[index]
        mdata = task_registry.get_module(mid)
        if not mdata:
            return

        info = mdata['info']

        # 更新描述（富文本 HTML）
        self.txt_description.setHtml(self._build_desc_html(info))

        # 更新参考结果面板
        self._update_reference_panel(info)

        # 更新文件选择器可见性：none 隐藏，其他类型（含 optional）展示
        input_type = info.get('input_type', 'csv')
        needs_file = input_type != 'none'
        self.file_selector.setVisible(needs_file)
        filters = {
            'csv': "CSV文件 (*.csv);;所有文件 (*)",
            'txt': "文本文件 (*.txt);;所有文件 (*)",
            'data': "数据文件 (*.csv *.txt);;CSV (*.csv);;TXT (*.txt);;所有文件 (*)",
            'optional': "数据文件 (*.csv *.txt *.dat);;所有文件 (*)",
            'directory': "",
        }
        self.file_selector._file_filter = filters.get(input_type, "所有文件 (*)")
        self.file_selector._select_dir = (input_type == 'directory')

        # 更新参数表单
        params = info.get('params', [])
        self.param_editor.set_params(params)
        self.plot_widget.clear()
        self.btn_export.setEnabled(False)
        self.btn_open_output.setEnabled(False)
        self._last_output_path = ''

    def _update_reference_panel(self, info: dict):
        """根据模块信息更新参考结果面板"""
        ref_img = info.get('reference_image', '')
        ref_desc = info.get('reference_output_desc', '')

        # 隐藏两个元素
        self.ref_image_label.clear()
        self.ref_image_label.hide()
        self.ref_text_label.clear()
        self.ref_text_label.hide()

        if ref_img:
            img_path = os.path.join(self.ASSETS_DIR, ref_img)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                # 自适应缩放：限制最大宽/高为 900x600
                pixmap = pixmap.scaled(
                    900, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.ref_image_label.setPixmap(pixmap)
                self.ref_image_label.show()
                # 显示图片来源说明
                script = info.get('script_file', '')
                hint = f"参考图来自历史分析结果，对应脚本: {script}" if script else "参考图"
                self.ref_text_label.setText(hint)
                self.ref_text_label.setStyleSheet(
                    "font-size: 11px; color: #888; padding: 4px 16px;"
                )
                self.ref_text_label.show()
            else:
                self.ref_text_label.setText(f"未找到参考图\n路径: {img_path}")
                self.ref_text_label.setStyleSheet(
                    "font-size: 12px; color: #999; padding: 24px;"
                )
                self.ref_text_label.show()
        elif ref_desc:
            script = info.get('script_file', '')
            output_type = info.get('output_type', '').upper()
            text = (
                f"📄  输出类型: {output_type}\n\n"
                f"📝  预期结果说明:\n{ref_desc}"
            )
            if script:
                text += f"\n\n💻  对应脚本: {script}"
            self.ref_text_label.setText(text)
            self.ref_text_label.setStyleSheet(
                "font-size: 13px; color: #444; padding: 24px; line-height: 1.8;"
            )
            self.ref_text_label.show()
        else:
            self.ref_text_label.setText("该模块暂无参考结果图")
            self.ref_text_label.setStyleSheet(
                "font-size: 12px; color: #aaa; padding: 24px;"
            )
            self.ref_text_label.show()

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
        input_type = mdata['info'].get('input_type', 'csv')
        input_path = self.file_selector.get_path()
        # optional 类型模块可以不选文件；none 类型无文件选择器；csv/txt 类型必须选文件
        if input_type not in ('none', 'optional'):
            if not input_path or not os.path.exists(input_path):
                QMessageBox.warning(self, "输入错误",
                                    "请选择有效的输入文件或目录")
                return

        # 获取输出目录
        project_root = ''
        if self._config_mgr:
            project_root = self._config_mgr.get_project_root()
        if not project_root:
            if input_path and os.path.exists(input_path):
                project_root = os.path.dirname(os.path.dirname(input_path))
            else:
                # gen 模式无输入文件，使用默认工程目录
                project_root = os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))))

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

            output_path = result.get('output_path', '')
            output_files = result.get('output_files', []) or []
            if output_path:
                self._last_output_path = output_path
                self.btn_open_output.setEnabled(True)

            # 显示图表，并自动切换到"分析结果" Tab
            fig = result.get('figure')
            if fig:
                self.plot_widget.display_figure(fig)
                self.btn_export.setEnabled(True)
                self.right_tabs.setCurrentIndex(1)  # 切到"分析结果"Tab
            else:
                image_paths = output_files or self._collect_result_images(output_path)
                if image_paths:
                    self.plot_widget.display_image_paths(image_paths)
                    self.btn_export.setEnabled(True)
                    self.right_tabs.setCurrentIndex(1)
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

    def _on_open_output(self):
        """在文件管理器中打开输出目录"""
        import subprocess
        path = self._last_output_path
        if not path:
            return
        # 若路径是文件，打开其所在目录并选中该文件；若是目录直接打开
        if os.path.isfile(path):
            folder = os.path.dirname(path)
            subprocess.Popen(f'explorer /select,"{path}"')
        elif os.path.isdir(path):
            os.startfile(path)
        else:
            # 尝试父目录
            folder = os.path.dirname(path)
            if os.path.isdir(folder):
                os.startfile(folder)
            else:
                if self._log_panel:
                    self._log_panel.append_log(f"输出路径不存在: {path}", "WARNING")

    def _collect_result_images(self, output_path: str) -> list:
        """从输出文件或目录中收集可显示的图片文件。"""
        if not output_path:
            return []
        exts = {'.png', '.jpg', '.jpeg', '.bmp'}
        images = []
        if os.path.isfile(output_path):
            if os.path.splitext(output_path)[1].lower() in exts:
                images.append(output_path)
        elif os.path.isdir(output_path):
            for root, _, files in os.walk(output_path):
                for name in files:
                    if os.path.splitext(name)[1].lower() in exts:
                        images.append(os.path.join(root, name))
        images.sort(key=lambda p: (os.path.dirname(p), os.path.basename(p)))
        return images
