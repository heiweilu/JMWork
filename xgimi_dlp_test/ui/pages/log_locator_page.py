# -*- coding: utf-8 -*-
"""
日志定位页面

功能：
  1. 粘贴飞书/MTK 问题单  自动解析设备信息和问题时间
  2. 选择日志根文件夹，自动扫描并展示各 logcat 文件时间范围
  3. 按时间窗口 / 关键词提取日志片段
  4. 预览结果，保存为 txt / 复制到剪贴板，拿去外部 AI 工具分析
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from modules.log_locator import (
    parse_bug_report,
    scan_syslog_folder,
    find_relevant_files,
    extract_logs_by_time,
    extract_logs_by_keyword,
    format_output,
    infer_year_from_folder,
    list_log_root_folders,
    _fmt_size,
)


# 
# 后台工作线程
# 

class ScanWorker(QObject):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, syslog_path: str, year):
        super().__init__()
        self._syslog_path = syslog_path
        self._year = year

    def run(self):
        try:
            results = scan_syslog_folder(
                self._syslog_path,
                year=self._year,
                progress_callback=lambda c, t, n: self.progress.emit(c, t, n),
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ExtractWorker(QObject):
    finished = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, mode, syslog_path, year, target_time, before_min, after_min,
                 keyword, level_filter, tag_filter):
        super().__init__()
        self._mode = mode
        self._syslog_path = syslog_path
        self._year = year
        self._target_time = target_time
        self._before_min = before_min
        self._after_min = after_min
        self._keyword = keyword
        self._level_filter = level_filter   # set or None
        self._tag_filter = tag_filter       # str or None

    def run(self):
        try:
            if self._mode == 'time':
                lines, used = extract_logs_by_time(
                    syslog_path=self._syslog_path,
                    target_time=self._target_time,
                    before_min=self._before_min,
                    after_min=self._after_min,
                    keyword=self._keyword or None,
                    level_filter=self._level_filter,
                    tag_filter=self._tag_filter or None,
                    year=self._year,
                )
            else:
                lines, used = extract_logs_by_keyword(
                    syslog_path=self._syslog_path,
                    keyword=self._keyword,
                    context_before_min=self._before_min,
                    context_after_min=self._after_min,
                    year=self._year,
                )
            self.finished.emit(lines, used)
        except Exception as e:
            self.error.emit(str(e))


# 
# 主页面
# 

class LogLocatorPage(QWidget):

    def __init__(self, config_mgr=None, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._scan_results = []
        self._extracted_lines = []
        self._extracted_text = ''
        self._current_syslog_path = ''
        self._current_year = datetime.now().year
        self._scan_worker = None
        self._scan_thread = None
        self._extract_worker = None
        self._extract_thread = None
        self._bug_info = {}
        self._scan_gen = 0      # generation counter: 丢弃过期线程的结果
        self._extract_gen = 0
        self._tabs = None
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        title = QLabel("🔍 日志定位")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a5f; padding: 4px 0;")
        root_layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, 1)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        splitter.setSizes([480, 720])

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #e5e7eb; border-radius: 3px; }"
            "QProgressBar::chunk { background: #3b82f6; border-radius: 3px; }"
        )
        root_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("color: #6b7280; font-size: 12px; padding: 2px 0;")
        root_layout.addWidget(self._status_label)

    def _build_left_panel(self):
        # 外层容器：QScrollArea，防止内容太多时发生重叠
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 6, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)

        # 实际内容区
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 8)
        layout.setSpacing(10)
        scroll.setWidget(panel)

        # ── 问题单输入
        bug_group = QGroupBox("📋 问题单（粘贴飞书/MTK 内容）")
        bug_layout = QVBoxLayout(bug_group)
        bug_layout.setSpacing(6)
        self._bug_text = QPlainTextEdit()
        self._bug_text.setPlaceholderText(
            "粘贴完整问题单文本...\n\n"
            "自动提取：标题、固件版本、设备SN、平台、发生时间\n\n"
            "支持时间格式：\n"
            "  Fri Feb 27 14:43:00 EST 2026\n"
            "  2026-02-27 14:43:00\n"
            "  11:48左右（仅时分，日期需手动确认）"
        )
        self._bug_text.setFixedHeight(140)
        bug_layout.addWidget(self._bug_text)
        self._btn_parse = QPushButton("🔍 自动解析问题单")
        self._btn_parse.clicked.connect(self._on_parse_bug)
        bug_layout.addWidget(self._btn_parse)
        layout.addWidget(bug_group)

        # ── 解析结果
        parsed_group = QGroupBox("📌 解析结果（可手动修改）")
        pf = QVBoxLayout(parsed_group)
        pf.setSpacing(6)

        def _row(lbl_text):
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(lbl_text)
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("color: #374151; font-weight: bold; font-size: 12px;")
            edit = QLineEdit()
            edit.setFixedHeight(28)
            edit.setStyleSheet(
                "background: #f9fafb; border: 1px solid #d1d5db; "
                "border-radius: 4px; padding: 2px 6px; font-size: 12px;"
            )
            row.addWidget(lbl)
            row.addWidget(edit, 1)
            pf.addLayout(row)
            return edit

        self._edit_title = _row("标题:")
        self._edit_firmware = _row("固件版本:")
        self._edit_sn = _row("设备SN:")
        self._edit_platform = _row("平台/机型:")

        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        time_lbl = QLabel("发生时间:")
        time_lbl.setFixedWidth(70)
        time_lbl.setStyleSheet("color: #374151; font-weight: bold; font-size: 12px;")
        self._dt_occur = QDateTimeEdit()
        self._dt_occur.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._dt_occur.setDateTime(datetime.now())
        self._dt_occur.setCalendarPopup(True)
        self._dt_occur.setFixedHeight(28)
        self._dt_occur.setStyleSheet(
            "background: #f9fafb; border: 1px solid #d1d5db; "
            "border-radius: 4px; padding: 2px 4px; font-size: 12px;"
        )
        time_row.addWidget(time_lbl)
        time_row.addWidget(self._dt_occur, 1)
        pf.addLayout(time_row)
        layout.addWidget(parsed_group)

        # ── 日志路径
        path_group = QGroupBox("📁 日志路径")
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(8)

        dev_row = QHBoxLayout()
        dev_row.setSpacing(4)
        dev_row.addWidget(QLabel("设备日志:"))
        self._combo_dev_folder = QComboBox()
        self._combo_dev_folder.setEditable(True)
        self._combo_dev_folder.setFixedHeight(28)
        self._combo_dev_folder.lineEdit().setPlaceholderText(
            "选择或粘贴设备日志文件夹路径（含 syslog/）"
        )
        self._combo_dev_folder.currentTextChanged.connect(self._on_dev_folder_changed)
        dev_row.addWidget(self._combo_dev_folder, 1)
        btn_dev = QPushButton("浏览")
        btn_dev.setFixedSize(52, 28)
        btn_dev.clicked.connect(self._browse_dev_folder)
        dev_row.addWidget(btn_dev)
        path_layout.addLayout(dev_row)

        year_row = QHBoxLayout()
        year_row.setSpacing(4)
        year_row.addWidget(QLabel("日志年份:"))
        self._spin_year = QSpinBox()
        self._spin_year.setRange(2000, 2100)
        self._spin_year.setValue(datetime.now().year)
        self._spin_year.setFixedHeight(28)
        self._spin_year.setToolTip("从文件夹名自动推断，也可手动修改")
        year_row.addWidget(self._spin_year)
        year_row.addStretch(1)
        path_layout.addLayout(year_row)

        btn_scan = QPushButton("🔄 扫描日志文件")
        btn_scan.setFixedHeight(30)
        btn_scan.clicked.connect(self._on_scan)
        path_layout.addWidget(btn_scan)
        layout.addWidget(path_group)

        # ── 提取设置
        extract_group = QGroupBox("⚙ 提取设置")
        el = QVBoxLayout(extract_group)
        el.setSpacing(8)

        mode_row = QHBoxLayout()
        self._chk_mode_time = QCheckBox("按时间窗口")
        self._chk_mode_time.setChecked(True)
        self._chk_mode_kw = QCheckBox("按关键词定位")
        mode_row.addWidget(self._chk_mode_time)
        mode_row.addWidget(self._chk_mode_kw)
        mode_row.addStretch(1)
        el.addLayout(mode_row)

        window_row = QHBoxLayout()
        window_row.setSpacing(6)
        window_row.addWidget(QLabel("前:"))
        self._spin_before = QSpinBox()
        self._spin_before.setRange(0, 60)
        self._spin_before.setValue(2)
        self._spin_before.setSuffix(" 分钟")
        self._spin_before.setFixedHeight(28)
        window_row.addWidget(self._spin_before)
        window_row.addSpacing(8)
        window_row.addWidget(QLabel("后:"))
        self._spin_after = QSpinBox()
        self._spin_after.setRange(0, 60)
        self._spin_after.setValue(2)
        self._spin_after.setSuffix(" 分钟")
        self._spin_after.setFixedHeight(28)
        window_row.addWidget(self._spin_after)
        window_row.addStretch(1)
        el.addLayout(window_row)

        kw_row = QHBoxLayout()
        kw_row.setSpacing(4)
        kw_row.addWidget(QLabel("关键词:"))
        self._edit_keyword = QLineEdit()
        self._edit_keyword.setPlaceholderText("可选，留空不过滤（关键词模式时必填）")
        self._edit_keyword.setFixedHeight(28)
        kw_row.addWidget(self._edit_keyword, 1)
        el.addLayout(kw_row)

        # 日志级别过滤
        level_row = QHBoxLayout()
        level_row.setSpacing(4)
        level_row.addWidget(QLabel("级别过滤:"))
        self._combo_level = QComboBox()
        self._combo_level.setFixedHeight(28)
        self._combo_level.addItems([
            "全量（不过滤）",
            "仅 Error + Warning",
            "仅 Error",
            "仅 Fatal",
            "Error + Warning + Fatal",
        ])
        self._combo_level.setToolTip("精简日志时选「仅 Error + Warning」，适合投喂 AI 分析")
        level_row.addWidget(self._combo_level, 1)
        el.addLayout(level_row)

        # TAG 过滤
        tag_row = QHBoxLayout()
        tag_row.setSpacing(4)
        tag_row.addWidget(QLabel("TAG 过滤:"))
        self._edit_tag = QLineEdit()
        self._edit_tag.setPlaceholderText("可选，如: HDMI|display|video （支持正则）")
        self._edit_tag.setFixedHeight(28)
        tag_row.addWidget(self._edit_tag, 1)
        el.addLayout(tag_row)

        btn_extract = QPushButton("▶ 开始提取")
        btn_extract.setFixedHeight(36)
        btn_extract.setStyleSheet(
            "QPushButton { background: #2563eb; color: white; border-radius: 6px; "
            "font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #1d4ed8; }"
        )
        btn_extract.clicked.connect(self._on_extract)
        el.addWidget(btn_extract)
        layout.addWidget(extract_group)

        layout.addStretch(1)
        return outer

    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(8)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        # Tab1: 文件列表
        tab_files = QWidget()
        fl = QVBoxLayout(tab_files)
        self._table_files = QTableWidget()
        self._table_files.setColumnCount(5)
        self._table_files.setHorizontalHeaderLabels(['文件夹', '大小', '开始时间', '结束时间', '状态'])
        self._table_files.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_files.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table_files.horizontalHeader().setStretchLastSection(True)
        self._table_files.setColumnWidth(0, 160)
        self._table_files.setColumnWidth(1, 75)
        self._table_files.setColumnWidth(2, 145)
        self._table_files.setColumnWidth(3, 145)
        fl.addWidget(self._table_files)
        self._tabs.addTab(tab_files, "📂 文件列表")

        # Tab2: 提取结果
        tab_result = QWidget()
        rl = QVBoxLayout(tab_result)

        toolbar = QHBoxLayout()
        self._lbl_result_info = QLabel("尚未提取")
        self._lbl_result_info.setStyleSheet("color: #6b7280; font-size: 12px;")
        toolbar.addWidget(self._lbl_result_info, 1)

        btn_copy = QPushButton("📋 复制全部")
        btn_copy.setToolTip("复制到剪贴板，粘贴给 AI 工具（Claude / ChatGPT / 通义千问）分析")
        btn_copy.clicked.connect(self._on_copy)
        toolbar.addWidget(btn_copy)

        btn_save = QPushButton("💾 保存 txt")
        btn_save.clicked.connect(self._on_save)
        toolbar.addWidget(btn_save)

        rl.addLayout(toolbar)

        self._result_view = QPlainTextEdit()
        self._result_view.setReadOnly(True)
        self._result_view.setFont(QFont("Consolas", 9))
        self._result_view.setStyleSheet(
            "background: #1e1e1e; color: #d4d4d4; border-radius: 6px; "
            "selection-background-color: #264f78;"
        )
        self._result_view.setPlaceholderText(
            "提取结果将在此显示...\n\n"
            "提取完成后可点击「复制全部」，将报告粘贴给外部 AI 工具进行日志分析。"
        )
        rl.addWidget(self._result_view, 1)
        self._tabs.addTab(tab_result, "📄 提取结果")

        return panel

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _on_parse_bug(self):
        text = self._bug_text.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", "请先粘贴问题单内容。")
            return
        self._bug_info = parse_bug_report(text)
        self._edit_title.setText(self._bug_info.get('title', ''))
        self._edit_firmware.setText(self._bug_info.get('firmware', ''))
        self._edit_sn.setText(self._bug_info.get('sn', ''))
        self._edit_platform.setText(self._bug_info.get('platform', ''))

        from PyQt6.QtCore import QDateTime
        occur_dt = self._bug_info.get('occur_time')
        time_only = self._bug_info.get('occur_time_only')  # (h, m, s) 仅时分秒

        if occur_dt:
            # 完整日期+时间
            self._dt_occur.setDateTime(
                QDateTime(occur_dt.year, occur_dt.month, occur_dt.day,
                          occur_dt.hour, occur_dt.minute, occur_dt.second)
            )
            self._status_label.setText(
                f"✅ 解析成功 | 时间: {occur_dt.strftime('%Y-%m-%d %H:%M:%S')}"
                + (f' | SN: {self._bug_info["sn"]}' if self._bug_info.get('sn') else '')
            )
        elif time_only:
            # 仅有时分秒：保留 DateTimeEdit 当前日期，只更新时间部分
            h, mi, s = time_only
            cur = self._dt_occur.dateTime()
            self._dt_occur.setDateTime(
                QDateTime(cur.date().year(), cur.date().month(), cur.date().day(), h, mi, s)
            )
            raw = self._bug_info.get('occur_time_raw', '')
            self._status_label.setText(
                f"⚠ 仅识别到时间 {h:02d}:{mi:02d}:{s:02d}（原文: {raw[:40]}）"
                "，日期请手动确认"
            )
        else:
            raw = self._bug_info.get('occur_time_raw', '')
            self._status_label.setText(f"⚠ 未识别时间（{raw[:60]}），请手动设置")

    def _browse_dev_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择设备日志文件夹（含 syslog/）")
        if path:
            self._combo_dev_folder.setCurrentText(path)

    def _on_dev_folder_changed(self, text):
        if text:
            self._spin_year.setValue(infer_year_from_folder(text))

    def _on_scan(self):
        dev_path = self._combo_dev_folder.currentText().strip()
        if not dev_path:
            QMessageBox.warning(self, "提示", "请先选择设备日志文件夹。")
            return

        syslog_path = Path(dev_path) / 'syslog'
        if not syslog_path.exists():
            if Path(dev_path).name == 'syslog':
                syslog_path = Path(dev_path)
            else:
                QMessageBox.warning(self, "未找到 syslog",
                                    f"{dev_path}\n下没有 syslog/ 子目录。")
                return

        self._current_syslog_path = str(syslog_path)
        self._current_year = self._spin_year.value()
        self._scan_results = []
        self._table_files.setRowCount(0)
        # 清空旧提取结果，避免让用户误以为是新设备的数据
        self._extracted_text = ''
        self._extracted_lines = []
        self._result_view.setPlainText('')
        self._lbl_result_info.setText('')
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(True)
        self._status_label.setText("扫描中...")

        # generation counter：新扫描比旧扫描 ID 大，旧线程结果会被丢弃
        self._scan_gen += 1
        gen = self._scan_gen

        # 断开旧 worker 的信号，不阻塞 UI（不 wait）
        if self._scan_worker:
            try:
                self._scan_worker.finished.disconnect()
                self._scan_worker.progress.disconnect()
                self._scan_worker.error.disconnect()
            except RuntimeError:
                pass
        self._scan_worker = None
        self._scan_thread = None

        self._scan_worker = ScanWorker(self._current_syslog_path, self._current_year)
        self._scan_thread = QThread()
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(self._on_scan_progress)
        # 用闭包捕获 gen，只有最新一轮扫描的结果才被接受
        self._scan_worker.finished.connect(
            lambda results, g=gen: self._on_scan_finished(results) if g == self._scan_gen else None
        )
        self._scan_worker.error.connect(
            lambda msg, g=gen: self._on_scan_error(msg) if g == self._scan_gen else None
        )
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.error.connect(self._scan_thread.quit)
        self._scan_thread.start()

    def _on_scan_progress(self, current, total, dir_name):
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(current)
        self._status_label.setText(f"扫描 {current}/{total}: {dir_name}")

    def _on_scan_finished(self, results):
        self._scan_results = results
        self._progress_bar.setVisible(False)
        self._populate_file_table(results)
        self._status_label.setText(f"✅ 扫描完成，共 {len(results)} 个 logcat 文件")

    def _on_scan_error(self, msg):
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"❌ 扫描失败: {msg}")
        QMessageBox.critical(self, "扫描失败", msg)

    def _populate_file_table(self, results):
        self._table_files.setRowCount(len(results))
        target_dt = self._get_target_datetime()
        before_min = self._spin_before.value()
        after_min = self._spin_after.value()

        for row, item in enumerate(results):
            self._table_files.setItem(row, 0, QTableWidgetItem(item['dir']))
            self._table_files.setItem(row, 1, QTableWidgetItem(_fmt_size(item['size'])))
            st = item.get('start_time')
            et = item.get('end_time')
            self._table_files.setItem(row, 2, QTableWidgetItem(
                st.strftime('%m-%d %H:%M:%S') if st else ''))
            self._table_files.setItem(row, 3, QTableWidgetItem(
                et.strftime('%m-%d %H:%M:%S') if et else ''))

            if target_dt and st and et:
                ws = target_dt - timedelta(minutes=before_min)
                we = target_dt + timedelta(minutes=after_min)
                if st <= we and et >= ws:
                    si = QTableWidgetItem('✅ 命中')
                    si.setForeground(QColor('#059669'))
                else:
                    si = QTableWidgetItem('')
                    si.setForeground(QColor('#9ca3af'))
            else:
                si = QTableWidgetItem('')
            self._table_files.setItem(row, 4, si)

    def _get_target_datetime(self):
        qdt = self._dt_occur.dateTime()
        return datetime(qdt.date().year(), qdt.date().month(), qdt.date().day(),
                        qdt.time().hour(), qdt.time().minute(), qdt.time().second())

    def _on_extract(self):
        if not self._current_syslog_path:
            QMessageBox.warning(self, "提示", "请先扫描日志文件。")
            return

        mode = ('keyword'
                if self._chk_mode_kw.isChecked() and not self._chk_mode_time.isChecked()
                else 'time')
        keyword = self._edit_keyword.text().strip()
        before_min = self._spin_before.value()
        after_min = self._spin_after.value()
        target_dt = self._get_target_datetime()
        tag_filter = self._edit_tag.text().strip() or None

        # 解析级别过滤
        level_map = {
            "全量（不过滤）":            None,
            "仅 Error + Warning":        {'E', 'W'},
            "仅 Error":                  {'E'},
            "仅 Fatal":                  {'F'},
            "Error + Warning + Fatal":   {'E', 'W', 'F'},
        }
        level_filter = level_map.get(self._combo_level.currentText())

        if mode == 'keyword' and not keyword:
            QMessageBox.warning(self, "提示", "关键词模式下请填写关键词。")
            return

        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(True)
        self._status_label.setText("提取中...")
        self._result_view.setPlainText("⏳ 提取中，请稍候...")
        if self._tabs:
            self._tabs.setCurrentIndex(1)

        # generation counter：只接受最新提取的结果
        self._extract_gen += 1
        gen = self._extract_gen

        # 清理旧提取线程（不阻塞 UI）
        if self._extract_worker:
            try:
                self._extract_worker.finished.disconnect()
                self._extract_worker.error.disconnect()
            except RuntimeError:
                pass
        self._extract_worker = None
        self._extract_thread = None

        self._extract_worker = ExtractWorker(
            mode=mode,
            syslog_path=self._current_syslog_path,
            year=self._current_year,
            target_time=target_dt,
            before_min=before_min,
            after_min=after_min,
            keyword=keyword,
            level_filter=level_filter,
            tag_filter=tag_filter,
        )
        self._extract_thread = QThread()
        self._extract_worker.moveToThread(self._extract_thread)
        self._extract_thread.started.connect(self._extract_worker.run)
        self._extract_worker.finished.connect(
            lambda lines, used, g=gen: self._on_extract_finished(lines, used) if g == self._extract_gen else None
        )
        self._extract_worker.error.connect(
            lambda msg, g=gen: self._on_extract_error(msg) if g == self._extract_gen else None
        )
        self._extract_worker.finished.connect(self._extract_thread.quit)
        self._extract_worker.error.connect(self._extract_thread.quit)
        self._extract_thread.start()

    def _on_extract_finished(self, lines, used_files):
        self._extracted_lines = lines
        self._progress_bar.setVisible(False)

        bug_info = dict(self._bug_info)
        bug_info['title'] = self._edit_title.text() or bug_info.get('title', '')
        bug_info['firmware'] = self._edit_firmware.text() or bug_info.get('firmware', '')
        bug_info['sn'] = self._edit_sn.text() or bug_info.get('sn', '')
        bug_info['platform'] = self._edit_platform.text() or bug_info.get('platform', '')

        target_dt = self._get_target_datetime()
        before_min = self._spin_before.value()
        after_min = self._spin_after.value()
        keyword = self._edit_keyword.text().strip()
        mode = ('keyword'
                if self._chk_mode_kw.isChecked() and not self._chk_mode_time.isChecked()
                else 'time')

        ws = target_dt - timedelta(minutes=before_min)
        we = target_dt + timedelta(minutes=after_min)

        self._extracted_text = format_output(
            bug_info=bug_info,
            extracted_lines=lines,
            syslog_path=self._current_syslog_path,
            window_start=ws,
            window_end=we,
            extraction_mode=mode,
            keyword=keyword or None,
        )

        self._result_view.setPlainText(self._extracted_text)
        log_lines = sum(1 for ln in lines if not ln.startswith('=') and ln.strip())
        self._lbl_result_info.setText(
            f"✅ {log_lines} 行 | {len(used_files)} 个文件命中"
        )
        self._status_label.setText(
            f"✅ 提取完成 | {log_lines} 行 | {len(used_files)} 个文件"
        )
        if self._scan_results:
            self._populate_file_table(self._scan_results)

    def _on_extract_error(self, msg):
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"❌ 提取失败: {msg}")
        self._result_view.setPlainText(f'[错误]\n{msg}')
        QMessageBox.critical(self, "提取失败", msg)

    def _on_copy(self):
        if not self._extracted_text:
            QMessageBox.information(self, "提示", "请先执行提取。")
            return
        QApplication.clipboard().setText(self._extracted_text)
        self._status_label.setText("✅ 已复制到剪贴板，可直接粘贴给 AI 工具分析")

    def _on_save(self):
        if not self._extracted_text:
            QMessageBox.information(self, "提示", "请先执行提取。")
            return
        sn = self._edit_sn.text().strip() or 'unknown'
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path, _ = QFileDialog.getSaveFileName(
            self, "保存提取结果", f"log_extract_{sn}_{ts}.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._extracted_text)
            self._status_label.setText(f"✅ 已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
