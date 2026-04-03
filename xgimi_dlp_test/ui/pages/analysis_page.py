# -*- coding: utf-8 -*-
"""
Analysis 功能页

选择分析类型 → 配置参数 → 选择输入文件 → 执行 → 图表内嵌显示
"""

import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                              QComboBox, QLabel, QPushButton, QGroupBox,
                              QMessageBox, QFileDialog, QScrollArea,
                              QSizePolicy, QTextBrowser, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from ui.widgets.file_selector import FileSelector
from ui.widgets.param_editor import ParamEditor
from ui.widgets.matplotlib_canvas import PlotWidget
from ui.widgets.progress_bar import ProgressWidget
from ui.widgets.tree_workspace import TreeWorkspace
from workers.task_worker import TaskWorker
from core import task_registry


class AnalysisPage(QWidget):
    """分析执行页面"""

    # 快捷跳转信号：深度敏感的应用内导航逻辑由 MainWindow 监听
    send_to_preprocessing = pyqtSignal(str)  # 发送到数据预处理页（角度扩圆坐标生成）
    send_to_svm = pyqtSignal(str)            # 发送到 SVM 训练页
    send_to_angle_test = pyqtSignal(str)     # 发送到角度测试(硬件)

    def __init__(self, log_panel=None, config_mgr=None, category='analysis', parent=None):
        super().__init__(parent)
        self._log_panel = log_panel
        self._config_mgr = config_mgr
        self._category = category
        self._worker = None
        self._last_output_path = ''   # 记录最近一次成功输出路径
        self._last_data_path   = ''   # 结构化数据路径（TSV，供下游）
        self._last_angle_test_path = ''
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        page_title = 'SVM训练' if self._category == 'svm' else '分析执行'
        page_desc = (
            '通过树状导航切换执行控制、参考结果、分析结果和分析报告。'
            if self._category != 'svm' else
            '通过树状导航切换训练控制、参考结果、训练结果和训练报告。'
        )
        self.workspace = TreeWorkspace(page_title, page_desc)
        main_layout.addWidget(self.workspace, 1)

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
        param_group.setMinimumHeight(220)
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setMinimumHeight(180)
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

        # 快捷跳转按钮（执行成功后才显示）
        self._btn_send_to_expand = QPushButton("→ 发送到角度扩圆坐标生成")
        self._btn_send_to_expand.setObjectName("btn_success")
        self._btn_send_to_expand.setToolTip("将输出的结构化 TXT 文件直接填入《角度扩圆坐标生成》模块的输入路径")
        self._btn_send_to_expand.setVisible(False)
        self._btn_send_to_expand.clicked.connect(self._on_btn_send_to_preprocess)
        left_layout.addWidget(self._btn_send_to_expand)

        self._btn_send_to_svm = QPushButton("→ 导入到 SVM 模型训练")
        self._btn_send_to_svm.setObjectName("btn_success")
        self._btn_send_to_svm.setToolTip("将输出的 TXT 文件直接发送到《SVM 模型训练》页面")
        self._btn_send_to_svm.setVisible(False)
        self._btn_send_to_svm.clicked.connect(self._on_btn_send_to_svm)
        left_layout.addWidget(self._btn_send_to_svm)

        self._btn_send_to_angle_test = QPushButton("→ 导入到角度测试(硬件)")
        self._btn_send_to_angle_test.setObjectName("btn_success")
        self._btn_send_to_angle_test.setToolTip("将输出的失败点测试文件直接发送到《角度测试(硬件)》页面")
        self._btn_send_to_angle_test.setVisible(False)
        self._btn_send_to_angle_test.clicked.connect(self._on_btn_send_to_angle_test)
        left_layout.addWidget(self._btn_send_to_angle_test)

        # 进度条
        self.progress = ProgressWidget()
        left_layout.addWidget(self.progress)

        self.ref_scroll = QScrollArea()
        self.ref_scroll.setWidgetResizable(True)
        self.ref_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_content = QWidget()
        self.ref_layout = QVBoxLayout(self.ref_content)
        self.ref_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 参考图操作栏
        _ref_bar = QHBoxLayout()
        _ref_bar.setContentsMargins(8, 4, 8, 0)
        self._btn_import_ref = QPushButton("📂 导入参考图")
        self._btn_import_ref.setToolTip("从本地文件导入参考图片，叠加展示与分析结果对比")
        self._btn_import_ref.setFixedHeight(26)
        self._btn_import_ref.setStyleSheet(
            "QPushButton{font-size:11px;padding:2px 10px;border-radius:5px;}")
        self._btn_import_ref.clicked.connect(self._on_import_ref_image)
        self._btn_clear_ref = QPushButton("✕ 清除")
        self._btn_clear_ref.setToolTip("清除手动导入的参考图，恢复模块默认参考图")
        self._btn_clear_ref.setFixedHeight(26)
        self._btn_clear_ref.setStyleSheet(
            "QPushButton{font-size:11px;padding:2px 8px;border-radius:5px;}")
        self._btn_clear_ref.setVisible(False)
        self._btn_clear_ref.clicked.connect(self._on_clear_ref_image)
        _ref_bar.addWidget(self._btn_import_ref)
        _ref_bar.addWidget(self._btn_clear_ref)
        _ref_bar.addStretch()
        self.ref_layout.addLayout(_ref_bar)

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

        self.plot_widget = PlotWidget()

        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        report_layout.setContentsMargins(8, 6, 8, 8)
        report_layout.setSpacing(6)
        _rpt_bar = QHBoxLayout()
        _rpt_bar.setContentsMargins(0, 0, 0, 0)
        self._btn_export_report = QPushButton("💾 导出报告为 TXT")
        self._btn_export_report.setEnabled(False)
        self._btn_export_report.setFixedHeight(28)
        self._btn_export_report.setStyleSheet(
            "QPushButton{font-size:12px;padding:2px 12px;border-radius:5px;}")
        self._btn_export_report.clicked.connect(self._on_export_report)
        _rpt_label = QLabel("执行含报告输出的模块后，结果会显示在此处")
        _rpt_label.setStyleSheet("color:#888;font-size:11px;")
        _rpt_bar.addWidget(self._btn_export_report)
        _rpt_bar.addSpacing(10)
        _rpt_bar.addWidget(_rpt_label)
        _rpt_bar.addStretch()
        report_layout.addLayout(_rpt_bar)
        self._report_text = QTextEdit()
        self._report_text.setReadOnly(True)
        self._report_text.setFontFamily("Consolas")
        self._report_text.setFontPointSize(10)
        self._report_text.setStyleSheet(
            "QTextEdit{background:#1E1E2E; color:#CDD6F4; border-radius:8px;"
            " padding:10px; line-height:1.6;}")
        self._report_text.setPlaceholderText("（执行后，含报告的模块输出会自动显示在此处）")
        report_layout.addWidget(self._report_text, 1)

        overview = QLabel('请选择左侧工作区。执行控制页负责选择模块、输入和参数；结果页负责查看参考图、输出图表和报告。')
        overview.setWordWrap(True)
        overview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        overview.setStyleSheet('padding: 16px; color: #445; font-size: 13px;')
        self.workspace.add_page('analysis_overview', page_title, overview)
        self.workspace.add_page('analysis_execute', '执行控制', left_panel, parent_key='analysis_overview')
        self.workspace.add_page('analysis_reference', '参考结果', self.ref_scroll, parent_key='analysis_overview')
        self.workspace.add_page('analysis_plot', '分析结果', self.plot_widget, parent_key='analysis_overview')
        self.workspace.add_page('analysis_report', '分析报告', report_tab, parent_key='analysis_overview')
        self.workspace.select_page('analysis_execute')

        # 模块ID列表（与 combo 索引对应）
        self._module_ids = []

    def _select_workspace_page(self, key: str):
        self.workspace.select_page(key)

    # 参考图所在目录
    ASSETS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'assets', 'reference_images'
    )

    def _get_current_module_id(self) -> str:
        index = self.combo_type.currentIndex()
        if 0 <= index < len(self._module_ids):
            return self._module_ids[index]
        return ''

    def _get_manual_ref_images(self) -> dict:
        if not self._config_mgr:
            return {}
        data = self._config_mgr.get('analysis.reference_images', {})
        return data if isinstance(data, dict) else {}

    def _get_manual_ref_path(self, module_id: str) -> str:
        if not module_id:
            return ''
        return str(self._get_manual_ref_images().get(module_id, '') or '')

    def _set_manual_ref_path(self, module_id: str, image_path: str):
        if not self._config_mgr or not module_id:
            return
        images = dict(self._get_manual_ref_images())
        if image_path:
            images[module_id] = image_path
        else:
            images.pop(module_id, None)
        self._config_mgr.set('analysis.reference_images', images)
        self._config_mgr.save()

    def refresh_modules(self):
        """刷新模块列表（从 task_registry 获取）"""
        self.combo_type.clear()
        self._module_ids.clear()

        modules = task_registry.get_modules(self._category)
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
        self._last_data_path = ''
        self._last_angle_test_path = ''
        self._btn_send_to_expand.setVisible(False)
        self._btn_send_to_svm.setVisible(False)
        self._btn_send_to_angle_test.setVisible(False)

    def _update_reference_panel(self, info: dict):
        """根据模块信息更新参考结果面板"""
        module_id = self._get_current_module_id()
        manual_ref_path = self._get_manual_ref_path(module_id)
        ref_img = info.get('reference_image', '')
        ref_desc = info.get('reference_output_desc', '')

        # 隐藏两个元素
        self.ref_image_label.clear()
        self.ref_image_label.hide()
        self.ref_text_label.clear()
        self.ref_text_label.hide()

        if manual_ref_path and os.path.isfile(manual_ref_path):
            pixmap = QPixmap(manual_ref_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    900, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.ref_image_label.setPixmap(pixmap)
                self.ref_image_label.show()
                self.ref_text_label.setText(f"手动导入参考图: {os.path.basename(manual_ref_path)}")
                self.ref_text_label.setStyleSheet(
                    "font-size: 11px; color: #888; padding: 4px 16px;"
                )
                self.ref_text_label.show()
                self._btn_clear_ref.setVisible(True)
                return
            self._set_manual_ref_path(module_id, '')

        self._btn_clear_ref.setVisible(False)

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

        # 获取输出目录：每个模块独立命名子文件夹 reports/{模块py文件名}/{YYYYMMDD}/
        _app_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        project_root = ''
        if self._config_mgr:
            project_root = self._config_mgr.get_project_root()
        if not project_root:
            project_root = _app_root

        py_modname = mid.split('.')[-1]           # e.g. "angle_boundary_stats"
        date_str   = datetime.now().strftime('%Y%m%d')
        output_dir = os.path.join(project_root, 'reports', py_modname, date_str)
        os.makedirs(output_dir, exist_ok=True)

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

            # 快捷跳转按钮（按当前模块名称显示）
            self._btn_send_to_expand.setVisible(False)
            self._btn_send_to_svm.setVisible(False)
            self._btn_send_to_angle_test.setVisible(False)
            cur_idx = self.combo_type.currentIndex()
            cur_mid = self._module_ids[cur_idx] if 0 <= cur_idx < len(self._module_ids) else ""
            cur_name = ""
            if cur_mid:
                mdata_cur = task_registry.get_module(cur_mid)
                if mdata_cur:
                    cur_name = mdata_cur['info'].get('name', '')
            if "角度边界统计" in cur_name and "FAIL" in cur_name:
                # 保存结构化 TSV 路径（extra 字段）
                extra = result.get('extra', {})
                self._last_data_path = extra.get('data_path', output_path)
                self._btn_send_to_expand.setVisible(bool(self._last_data_path))
            elif "角度扩圆坐标生成" in cur_name:
                self._btn_send_to_svm.setVisible(bool(output_path))
            extra = result.get('extra', {}) or {}
            self._last_angle_test_path = extra.get('angle_test_import_path', '')
            self._btn_send_to_angle_test.setVisible(bool(self._last_angle_test_path))

            # 分析报告：若模块返回 report_text，显示在"分析报告"Tab
            report_text = result.get('report_text', '')
            if report_text:
                self._report_text.setPlainText(report_text)
                self._btn_export_report.setEnabled(True)
                self._current_report_text = report_text
                self._select_workspace_page('analysis_report')
            else:
                self._current_report_text = ''
                self._btn_export_report.setEnabled(False)

            # 显示图表：优先用已保存 PNG（支持旋转/缩放），无文件时降级用 Figure
            fig = result.get('figure')
            _img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            image_paths = [p for p in (output_files or []) if p and p.lower().endswith(_img_exts)]
            if not image_paths:
                image_paths = self._collect_result_images(output_path)
            if image_paths:
                self.plot_widget.display_image_paths(image_paths)
                self.btn_export.setEnabled(True)
                self._select_workspace_page('analysis_plot')
            elif fig:
                self.plot_widget.display_figure(fig)
                self.btn_export.setEnabled(True)
                self._select_workspace_page('analysis_plot')
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
            subprocess.Popen(f'explorer /select,"{path}"')
        elif os.path.isdir(path):
            os.startfile(path)
        else:
            folder = os.path.dirname(path)
            if os.path.isdir(folder):
                os.startfile(folder)
            else:
                if self._log_panel:
                    self._log_panel.append_log(f"输出路径不存在: {path}", "WARNING")

    def _send_to_module(self, target_module_name: str, file_path: str):
        """切换到目标模块并预填输入文件路径。"""
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "发送失败",
                                f"找不到文件:\n{file_path}")
            return
        # 在 combo 中找目标模块
        target_idx = -1
        for i, mid in enumerate(self._module_ids):
            mdata = task_registry.get_module(mid)
            if mdata and target_module_name in mdata['info'].get('name', ''):
                target_idx = i
                break
        if target_idx < 0:
            QMessageBox.warning(self, "发送失败",
                                f"未找到模块《{target_module_name}》，请确认已正确加载。")
            return
        self.combo_type.setCurrentIndex(target_idx)
        self.file_selector.set_path(file_path)
        if self._log_panel:
            self._log_panel.append_log(
                f"已切换到《{target_module_name}》并填入输入文件: {file_path}", "INFO")

    def set_input_file(self, file_path: str):
        """外部调用：预填输入文件路径（供主窗口快捷跳转使用）"""
        self.file_selector.set_path(file_path)

    def _on_btn_send_to_preprocess(self):
        """→ 发送到角度扩圆坐标生成（在预处理页面打开）"""
        p = self._last_data_path
        if p and os.path.isfile(p):
            self.send_to_preprocessing.emit(p)
        else:
            QMessageBox.warning(self, "发送失败", f"找不到输出文件:\n{p}")

    def _on_btn_send_to_svm(self):
        """→ 导入到 SVM 模型训练页面"""
        p = self._last_output_path
        if p and os.path.isfile(p):
            self.send_to_svm.emit(p)
        else:
            QMessageBox.warning(self, "发送失败", f"找不到输出文件:\n{p}")

    def _on_btn_send_to_angle_test(self):
        """→ 导入到角度测试(硬件)页面"""
        p = self._last_angle_test_path
        if p and os.path.isfile(p):
            self.send_to_angle_test.emit(p)
        else:
            QMessageBox.warning(self, "发送失败", f"找不到输出文件:\n{p}")

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

    def _on_import_ref_image(self):
        """手动导入参考图片，显示在"参考结果"Tab 中供对比分析。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择参考图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)")
        if not path or not os.path.isfile(path):
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "导入失败", f"无法加载图片:\n{path}")
            return
        # 自适应缩放显示
        scaled = pixmap.scaled(
            900, 600,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.ref_image_label.setPixmap(scaled)
        self.ref_image_label.show()
        self.ref_text_label.setText(f"手动导入参考图: {os.path.basename(path)}")
        self.ref_text_label.setStyleSheet("font-size:11px; color:#888; padding:4px 16px;")
        self.ref_text_label.show()
        self._btn_clear_ref.setVisible(True)
        self._set_manual_ref_path(self._get_current_module_id(), path)
        # 切换到参考结果 Tab
        self._select_workspace_page('analysis_reference')
        if self._log_panel:
            self._log_panel.append_log(f"已导入参考图: {path}", "INFO")

    def _on_clear_ref_image(self):
        """清除手动导入的参考图，恢复当前模块的默认参考图。"""
        self._btn_clear_ref.setVisible(False)
        self._set_manual_ref_path(self._get_current_module_id(), '')
        idx = self.combo_type.currentIndex()
        if 0 <= idx < len(self._module_ids):
            mdata = task_registry.get_module(self._module_ids[idx])
            if mdata:
                self._update_reference_panel(mdata['info'])

    def _on_export_report(self):
        """将分析报告导出为 TXT 文件。"""
        text = getattr(self, '_current_report_text', '')
        if not text:
            return
        default_name = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出分析报告", default_name,
            "文本文件 (*.txt);;所有文件 (*)")
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            if self._log_panel:
                self._log_panel.append_log(f"报告已导出: {filepath}", "SUCCESS")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"无法写入文件:\n{e}")
