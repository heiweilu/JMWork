# -*- coding: utf-8 -*-
"""
串口交互界面页面

功能:
  - 串口连接/断开，支持 COM 端口、波特率、数据位、校验位、停止位配置
  - 彩色终端显示（收/发/系统/错误分色）
  - 快捷指令面板（固件升级流程、角度采集、系统工具）
  - 自定义快捷指令（可添加/删除，持久化到 JSON）
  - 日志下载（保存终端内容）

极米角度采集测试说明:
  流程:
    1. 准备 libxgimi.so（已内置于 assets/firmware/）
    2. 通过 U 盘将 libxgimi.so 拷贝到投影仪并升级固件（见「固件升级」区）
    3. 连接串口，执行角度采集指令
    4. 执行完成后将 CSV 数据拷贝到 U 盘取回

  测试指令说明(batchGetDisplayPointByAngle):
    gmpfUnit externDisplay kst_dev batchGetDisplayPointByAngle
        "yaw;pitch;0;-40;40;-40;40;{step};/data/vendor"
    参数解析:
      axis1=yaw, axis2=pitch  → 遍历 Yaw × Pitch 二维网格
      fixed=0                 → Roll 固定为 0°
      start1=-40, end1=40     → Yaw 范围 [-40°, 40°]
      start2=-40, end2=40     → Pitch 范围 [-40°, 40°]
      step                    → 角度步进（度），可选 0.1/0.5/1
      /data/vendor            → CSV 输出目录（设备内部）
    输出:
      每行含: Yaw,Pitch,Roll,TL_X,TL_Y,TR_X,TR_Y,BL_X,BL_Y,BR_X,BR_Y
      文件名: ak_scan_yaw_pitch_step{step}_{timestamp}.csv
"""

import os
import re
import json
import time
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QComboBox, QTextEdit, QLineEdit, QGroupBox, QScrollArea, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QSizePolicy,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFrame, QTabWidget, QToolButton,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QTextCursor, QFont, QTextCharFormat

# ──────────────── 配置文件路径 ────────────────
_ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'assets'
)
_FIRMWARE_PATH = os.path.join(_ASSETS_DIR, 'firmware', 'libxgimi.so')
_CUSTOM_CMDS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'config', 'serial_quick_cmds.json'
)

# ──────────────── 主题配色 ────────────────
_DARK = {
    'bar_bg':        '#1E222D',
    'bar_label':     '#8A98A5',
    'combo_bg':      '#2A303C',
    'combo_text':    '#FFFFFF',
    'terminal_bg':   '#0D1117',
    'terminal_text': '#C9D1D9',
    'terminal_bdr':  '#30363D',
    'terminal_sel':  '#264F78',
    'input_bg':      '#161B22',
    'input_text':    '#C9D1D9',
    'input_bdr':     '#30363D',
    'input_focus':   '#388BFD',
    'nl_bg':         '#161B22',
    'nl_text':       '#cccccc',
    'nl_bdr':        '#30363D',
    'rx':            '#C9D1D9',
    'tx':            '#56D364',
    'sys':           '#F0C040',
    'sys_err':       '#FF6B6B',
    'scroll_bg':     '#0D1117',
    'grp_bg':        '#161B22',
    'grp_bdr':       '#30363D',
    'grp_title':     '#7A8895',
    'btn_bg':        '#1C2128',
    'btn_text':      '#C9D1D9',
    'btn_bdr':       '#30363D',
    'btn_hover':     '#21262D',
    'btn_hover_bdr': '#58A6FF',
    'util_lbl':      '#546E7A',
}
_LIGHT = {
    'bar_bg':        '#DDE6F0',
    'bar_label':     '#475569',
    'combo_bg':      '#FFFFFF',
    'combo_text':    '#1E293B',
    'terminal_bg':   '#FAFBFC',
    'terminal_text': '#24292F',
    'terminal_bdr':  '#C8D1DB',
    'terminal_sel':  '#B6D7FF',
    'input_bg':      '#FFFFFF',
    'input_text':    '#24292F',
    'input_bdr':     '#C8D1DB',
    'input_focus':   '#0969DA',
    'nl_bg':         '#F6F8FA',
    'nl_text':       '#24292F',
    'nl_bdr':        '#C8D1DB',
    'rx':            '#1F2328',
    'tx':            '#0550AE',
    'sys':           '#7D4E00',
    'sys_err':       '#CF222E',
    'scroll_bg':     '#EEF2F7',
    'grp_bg':        '#FFFFFF',
    'grp_bdr':       '#C8D1DB',
    'grp_title':     '#475569',
    'btn_bg':        '#F0F4F8',
    'btn_text':      '#1E293B',
    'btn_bdr':       '#C8D1DB',
    'btn_hover':     '#E2EAF4',
    'btn_hover_bdr': '#0969DA',
    'util_lbl':      '#475569',
}

# ──────────────── 默认自定义命令 ────────────────
_DEFAULT_CUSTOM_CMDS = [
    {"name": "打印GM调试日志",     "cmd": "logcat | grep GM_DISP_DBG"},
    {"name": "关闭AVB",           "cmd": "avb init 0;avb set-devicestate 0;avb set-verity disable;save;reset"},
    {"name": "调整休眠(24h)",      "cmd": "settings put system screen_off_timeout 86400000"},
    {"name": "查看U盘挂载",        "cmd": "ls /mnt/media_rw/"},
    {"name": "查看vendor目录",     "cmd": "ls /vendor/lib/ | grep xgimi"},
]

# ──────────────── 固件升级流程指令 ────────────────
_UPGRADE_STEPS = [
    ("① su",           "su",
     "切换到超级用户（root）"),
    ("② remount",      "remount",
     "重新挂载文件系统为可读写（允许修改 /vendor）"),
    ("③ 备份原始so",   "cp /vendor/lib/libxgimi.so /data/",
     "将原始 libxgimi.so 备份到 /data/ 目录，防止升级失败无法恢复"),
    ("④ 升级新so",     "cp /mnt/media_rw/0182-0265/libxgimi.so /vendor/lib/",
     "从 U 盘（UUID: 0182-0265）拷贝新的 libxgimi.so 到 /vendor/lib"),
    ("⑤ sync",         "sync",
     "同步文件系统缓冲区，确保写入完成"),
    ("⑥ reboot",       "reboot",
     "重启投影仪，新固件生效"),
]

# ──────────────── 可选步进值 ────────────────
_STEP_OPTIONS = ["0.1", "0.5", "1", "2", "5"]


# ══════════════════════════════════════════════════════════════════════════════
#  自定义指令编辑对话框
# ══════════════════════════════════════════════════════════════════════════════
class CmdEditDialog(QDialog):
    def __init__(self, name="", cmd="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑快捷指令")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.edit_name = QLineEdit(name)
        self.edit_name.setPlaceholderText("显示名称，如「查看进程」")
        layout.addRow("名称:", self.edit_name)

        self.edit_cmd = QLineEdit(cmd)
        self.edit_cmd.setPlaceholderText("串口指令内容")
        layout.addRow("指令:", self.edit_cmd)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_accept(self):
        if not self.edit_name.text().strip() or not self.edit_cmd.text().strip():
            QMessageBox.warning(self, "提示", "名称和指令不能为空")
            return
        self.accept()

    def get_values(self):
        return self.edit_name.text().strip(), self.edit_cmd.text().strip()


# ══════════════════════════════════════════════════════════════════════════════
#  可折叠面板组件
# ══════════════════════════════════════════════════════════════════════════════
class _CollapsibleSection(QFrame):
    """带平滑动画的可折叠面板，替代 QGroupBox 用于串口调试右侧快捷面板"""

    def __init__(self, title: str, collapsed: bool = False, parent=None):
        super().__init__(parent)
        self._collapsed = collapsed
        self._anim = None
        self.setObjectName("cs_outer")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 2)
        outer.setSpacing(0)

        # ─── 标题栏（点击折叠 / 展开）
        self._header = QFrame()
        self._header.setObjectName("cs_header")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(36)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(10, 0, 6, 0)
        h_lay.setSpacing(4)

        self._arrow = QLabel("▶" if collapsed else "▼")
        self._arrow.setFixedWidth(14)
        h_lay.addWidget(self._arrow)

        self._title_lbl = QLabel(title)
        h_lay.addWidget(self._title_lbl, stretch=1)

        # ─── 头部右侧控制按钮（默认隐藏，调用 set_controls 后显示）
        _ctrl_qss = (
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:3px;font-size:10px;padding:0;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )
        self._ctrl_ren = QToolButton(); self._ctrl_ren.setText("✏")
        self._ctrl_ren.setToolTip("重命名板块")
        self._ctrl_up  = QToolButton(); self._ctrl_up.setText("↑")
        self._ctrl_up.setToolTip("向上移动")
        self._ctrl_dn  = QToolButton(); self._ctrl_dn.setText("↓")
        self._ctrl_dn.setToolTip("向下移动")
        self._ctrl_del = QToolButton(); self._ctrl_del.setText("✕")
        self._ctrl_del.setToolTip("删除板块")
        for b in (self._ctrl_ren, self._ctrl_up, self._ctrl_dn, self._ctrl_del):
            b.setFixedSize(22, 22)
            b.setStyleSheet(_ctrl_qss)
            b.hide()
            h_lay.addWidget(b)

        outer.addWidget(self._header)

        # ─── 分隔线
        self._sep = QFrame()
        self._sep.setObjectName("cs_sep")
        self._sep.setFrameShape(QFrame.Shape.HLine)
        self._sep.setFixedHeight(1)
        if collapsed:
            self._sep.setVisible(False)
        outer.addWidget(self._sep)

        # ─── 内容体
        self._body = QFrame()
        self._body.setObjectName("cs_body")
        self.body_layout = QVBoxLayout(self._body)
        self.body_layout.setContentsMargins(8, 8, 8, 10)
        self.body_layout.setSpacing(6)
        outer.addWidget(self._body)

        if collapsed:
            self._body.setMaximumHeight(0)
            self._body.setVisible(False)

        self._header.mousePressEvent = self._on_header_press

    def _on_header_press(self, event):
        """点击标题栏时折叠/展开（但不拦截头部控制按钮的点击）"""
        child = self._header.childAt(event.pos())
        if isinstance(child, QToolButton):
            return
        self.toggle()

    def set_controls(self, *, up_cb=None, down_cb=None,
                     delete_cb=None, rename_cb=None):
        """启用头部控制按钮（可传 None 表示不开启该按钮）"""
        def _bind(btn, cb):
            if cb:
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(cb)
                btn.show()
            else:
                btn.hide()
        _bind(self._ctrl_up,  up_cb)
        _bind(self._ctrl_dn,  down_cb)
        _bind(self._ctrl_del, delete_cb)
        _bind(self._ctrl_ren, rename_cb)

    def update_title(self, title: str):
        self._title_lbl.setText(title)

    def toggle(self):
        if self._collapsed:
            self._do_expand()
        else:
            self._do_collapse()

    def _do_expand(self):
        if self._anim and self._anim.state() == self._anim.State.Running:
            self._anim.stop()
            self._body.setMaximumHeight(16_777_215)
        self._collapsed = False
        self._arrow.setText("▼")
        self._sep.setVisible(True)
        # 先将 body 不可见且高度为 0，延迟一帧再开始展开动画，
        # 避免 setVisible(True) 后立即渲染导致闪屏
        self._body.setMaximumHeight(0)
        self._body.setMinimumHeight(0)
        # 注意：不在此处 setVisible(True)，而在 _start() 里才显示，
        # 避免 Qt 在动画还未开始时就渲染一帧零高度的闪屏
        self._body.setVisible(False)

        from PyQt6.QtCore import QTimer as _QTimer

        def _start():
            self._body.setVisible(True)
            layout = self._body.layout()
            if layout:
                layout.activate()
                target = layout.totalSizeHint().height()
            else:
                self._body.adjustSize()
                target = self._body.sizeHint().height()
            target = max(target, 48)
            # 以 self 为父对象，防止 body 动画期间析构引发崩溃
            anim = QPropertyAnimation(self._body, b"maximumHeight", self)
            anim.setDuration(200)
            anim.setStartValue(0)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _done():
                self._body.setMaximumHeight(16_777_215)
                self._body.setMinimumHeight(0)

            anim.finished.connect(_done)
            anim.start()
            self._anim = anim

        _QTimer.singleShot(0, _start)

    def _do_collapse(self):
        if self._anim and self._anim.state() == self._anim.State.Running:
            self._anim.stop()
        self._collapsed = True
        self._arrow.setText("▶")
        cur = self._body.height()
        if cur == 0:
            # 已经是折叠状态，直接置隐
            self._body.setVisible(False)
            self._sep.setVisible(False)
            return
        # 以 self 为父对象，防止析构
        anim = QPropertyAnimation(self._body, b"maximumHeight", self)
        anim.setDuration(180)
        anim.setStartValue(cur)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def _done():
            self._body.setVisible(False)
            self._sep.setVisible(False)
            self._body.setMaximumHeight(0)

        anim.finished.connect(_done)
        anim.start()
        self._anim = anim

    def apply_colors(self, hdr_bg: str, hdr_bdr: str, body_bg: str,
                     body_bdr: str, title_c: str, sep_c: str, arrow_c: str):
        self.setStyleSheet("QFrame#cs_outer { background: transparent; }")
        self._header.setStyleSheet(
            f"QFrame#cs_header {{ background: {hdr_bg}; border: 1px solid {hdr_bdr}; "
            f"border-radius: 6px 6px 0 0; }}"
            f"QFrame#cs_header:hover {{ background: {hdr_bg}; border-color: {arrow_c}; }}"
        )
        self._title_lbl.setStyleSheet(
            f"color: {title_c}; font-weight: bold; font-size: 13px;"
        )
        self._arrow.setStyleSheet(f"color: {arrow_c}; font-size: 11px;")
        self._sep.setStyleSheet(f"background: {sep_c};")
        self._body.setStyleSheet(
            f"QFrame#cs_body {{ background: {body_bg}; border: 1px solid {body_bdr}; "
            f"border-top: none; border-radius: 0 0 6px 6px; }}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  串口页面主体
# ══════════════════════════════════════════════════════════════════════════════
class SerialPage(QWidget):
    """串口交互界面"""

    def __init__(self, config_mgr=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._serial_state = {}
        self._serial = None
        self._reader_thread = None
        self._rx_buffer = bytearray()
        self._auto_scroll = True
        self._log_lines = []            # 纯文本日志缓存
        # 初始化数据加载相关属性
        self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)  # 自定义快捷指令
        self._saved_dynamic_sections = []  # 保存的动态板块数据
        # 初始化时加载所有数据
        self._load_all_data()
        # 主题状态
        self._dark_mode = bool(self._serial_state.get('theme', {}).get('dark_mode', False))
        self._sys_err_color = _DARK['sys_err']
        self._port_bar_labels = []   # 端口栏标签引用（主题更新用）
        # 命令历史与 Tab 补全
        self._cmd_history   = []   # 历史列表（第 0 = 最早）
        self._history_idx   = -1   # 浏览中的位置，-1 表示未在历史模式
        self._live_input    = ''   # 历史导航前用户正在输入的内容
        self._tab_candidates = []  # Tab 待选列表
        self._tab_idx       = -1   # 当前 Tab 候选索引
        self._pre_tab_text  = ''   # 按 Tab 前的原始文本
        self._highlight_rx  = True # RX 内容高亮开关
        self._rx_path_cache: list = []   # 从终端输出中收集的 Unix 路径（Tab 补全用）
        # 可编辑快捷指令
        self._upgrade_steps  = [list(s) for s in _UPGRADE_STEPS]    # 可变副本
        self._fw_step_buttons: list = []                             # 固件升级按钮引用
        self._scan_cmd_template = (
            'gmpfUnit externDisplay kst_dev batchGetDisplayPointByAngle '
            '"yaw;pitch;{resolution};{yaw_min};{yaw_max};{pitch_min};{pitch_max};{step};/data/vendor"'
        )
        self._scan_resolution = '0'   # 分辨率参数：0=默认/4K，1=2K
        self._scan_yaw_min    = '-40'
        self._scan_yaw_max    = '40'
        self._scan_pitch_min  = '-40'
        self._scan_pitch_max  = '40'
        self._copy_csv_cmd = 'cp /data/vendor/ak_scan_*.csv /mnt/media_rw/0182-0265/'
        # 系统工具指令（可编辑）
        self._sysutil_tools: list = [
            ["📜 监听 GM 调试日志",
             "logcat | grep GM_DISP_DBG",
             "实时监听 GM_DISP_DBG 标签的 Logcat 日志（Ctrl+C 停止）"],
            ["🔒 关闭 AVB 验证",
             "avb init 0;avb set-devicestate 0;avb set-verity disable;save;reset",
             "关闭 Android Verified Boot，允许修改系统分区\n执行后设备会自动重启"],
            ["⏱ 调整休眠时间(24h)",
             "settings put system screen_off_timeout 86400000",
             "将屏幕休眠时间设为 24 小时（86400000 毫秒），测试时防止屏幕熄灭"],
            ["📂 查看 U 盘挂载",
             "ls /mnt/media_rw/",
             "列出 U 盘挂载目录，确认 U 盘 UUID"],
            ["📁 查看 vendor lib",
             "ls /vendor/lib/ | grep xgimi",
             "查看 /vendor/lib 中的 xgimi 相关动态库"],
            ["🔍 查看设备信息",
             "getprop ro.product.model && getprop ro.build.version.release",
             "打印设备型号和 Android 版本"],
        ]
        self._sysutil_btns: list = []  # QPushButton 引用列表
        # ── 快捷板块有序列表（用于 ↑↓ 重排）
        self._quick_sections_list: list = []
        self._sections_layout     = None   # set in _build_quick_panel
        self._btn_add_section     = None   # "+ 新建板块" 按钮引用
        self._built_in_sections = {}
        # ── 搜索状态
        self._search_visible = False
        self._search_last_pos = None  # QTextCursor position for incremental find
        self._workflow_timer = QTimer(self)
        self._workflow_timer.setInterval(180)
        self._workflow_timer.timeout.connect(self._process_workflow_queue)
        self._workflow_active = False
        self._workflow_name = ''
        self._workflow_queue = []
        self._workflow_current = ''
        self._workflow_last_rx_ts = 0.0
        self._workflow_sent_ts = 0.0
        self._workflow_cmd_started = False
        self._workflow_idle_ms = 900
        self._workflow_silent_ms = 1800
        self._init_ui()
        self._refresh_ports()

        # 定期将未换行的残留数据刷入终端（处理少 shell 提示符)
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(80)   # 80ms 刷新一次
        self._flush_timer.timeout.connect(self._flush_rx_buffer)
        self._flush_timer.start()

    # ──────────────────────────────────────────────────────────────────────────
    #  UI 构建
    # ──────────────────────────────────────────────────────────────────────────
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ── 顶部：串口配置栏 ──
        main_layout.addWidget(self._build_port_bar())

        # ── 主体：终端 + 快捷指令 ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：终端区
        terminal_widget = QWidget()
        term_layout = QVBoxLayout(terminal_widget)
        term_layout.setContentsMargins(0, 0, 0, 0)
        term_layout.setSpacing(4)
        # 搜索栏（Ctrl+F 切换显示）
        self._search_bar = self._build_search_bar()
        term_layout.addWidget(self._search_bar)
        term_layout.addWidget(self._build_terminal(), stretch=1)
        term_layout.addWidget(self._build_input_bar())

        # 右：快捷指令区
        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setMinimumWidth(320)
        self._right_scroll.setMaximumWidth(440)
        self._right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_content = self._build_quick_panel()
        self._right_scroll.setWidget(right_content)

        splitter.addWidget(terminal_widget)
        splitter.addWidget(self._right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        main_layout.addWidget(splitter, stretch=1)

        self._apply_theme()  # 所有控件创建完毕后初始化样式
        self._load_saved_dynamic_sections()  # 加载保存的动态板块（在 UI 初始化完成后）

    def _build_port_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("port_bar")
        self._port_bar = bar
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        def _lbl(text):
            l = QLabel(text)
            self._port_bar_labels.append(l)
            return l

        # 串口号
        layout.addWidget(_lbl("端口:"))
        self.combo_port = QComboBox()
        self.combo_port.setMinimumWidth(90)
        layout.addWidget(self.combo_port)

        self._btn_refresh = QToolButton()
        self._btn_refresh.setText("🔄")
        self._btn_refresh.setToolTip("刷新可用串口列表")
        self._btn_refresh.clicked.connect(self._refresh_ports)
        layout.addWidget(self._btn_refresh)

        # 波特率
        layout.addWidget(_lbl("波特率:"))
        self.combo_baud = QComboBox()
        for b in ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]:
            self.combo_baud.addItem(b)
        self.combo_baud.setCurrentText("115200")
        layout.addWidget(self.combo_baud)

        # 数据位
        layout.addWidget(_lbl("数据位:"))
        self.combo_data = QComboBox()
        for d in ["5", "6", "7", "8"]:
            self.combo_data.addItem(d)
        self.combo_data.setCurrentText("8")
        layout.addWidget(self.combo_data)

        # 校验位
        layout.addWidget(_lbl("校验:"))
        self.combo_parity = QComboBox()
        self.combo_parity.addItems(["None", "Even", "Odd", "Mark", "Space"])
        layout.addWidget(self.combo_parity)

        # 停止位
        layout.addWidget(_lbl("停止位:"))
        self.combo_stop = QComboBox()
        self.combo_stop.addItems(["1", "1.5", "2"])
        layout.addWidget(self.combo_stop)

        layout.addStretch()

        # 自动滚动
        self.chk_autoscroll = QCheckBox("自动滚动")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.toggled.connect(lambda v: setattr(self, '_auto_scroll', v))
        layout.addWidget(self.chk_autoscroll)

        # 清空
        self._btn_clear = QPushButton("清空")
        self._btn_clear.setFixedWidth(52)
        self._btn_clear.clicked.connect(self._on_clear)
        layout.addWidget(self._btn_clear)

        # 主题切换
        self._btn_theme = QToolButton()
        self._btn_theme.setToolTip("切换浅色/深色主题")
        self._btn_theme.setFixedWidth(32)
        self._btn_theme.clicked.connect(self._toggle_theme)
        layout.addWidget(self._btn_theme)

        # RX 高亮开关
        self.chk_highlight = QCheckBox("🎨 高亮")
        self.chk_highlight.setChecked(True)
        self.chk_highlight.setToolTip("根据关键字对接收内容高亮显示")
        self.chk_highlight.toggled.connect(lambda v: setattr(self, '_highlight_rx', v))
        layout.addWidget(self.chk_highlight)

        self.chk_tab_passthrough = QCheckBox("Tab直发")
        self.chk_tab_passthrough.setChecked(False)
        self.chk_tab_passthrough.setToolTip("启用后，Tab 会直接发送到设备，不再触发本地补全")
        layout.addWidget(self.chk_tab_passthrough)

        # 连接/断开
        self.btn_connect = QPushButton("  连接  ")
        self.btn_connect.setObjectName("btn_primary")
        self.btn_connect.clicked.connect(self._on_toggle_connect)
        layout.addWidget(self.btn_connect)

        # 状态指示
        self.lbl_status = QLabel("● 未连接")
        layout.addWidget(self.lbl_status)

        return bar

    def _build_terminal(self) -> QTextEdit:
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setMinimumHeight(300)
        self.terminal.installEventFilter(self)   # 键盘输入路由 + Ctrl+F
        # 显示光标，让用户知道可以在此直接输入
        self.terminal.setTextInteractionFlags(
            self.terminal.textInteractionFlags()
            | Qt.TextInteractionFlag.TextEditable
        )
        # 用于内嵌输入模式的内部状态
        self._terminal_input_mode = False   # 是否处于终端内输入模式
        self._terminal_input_anchor = -1    # 输入区起始位置
        self._terminal_input_buf  = ''      # 已输入内容
        return self.terminal

    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入指令，按 Enter 发送 | ↑↓ 历史 | Tab 补全...")
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.returnPressed.connect(self._on_send)
        self.input_line.installEventFilter(self)   # Tab/上下键拦截
        layout.addWidget(self.input_line, stretch=1)

        # 换行模式（发送时带 \r\n 还是只 \n）
        self.combo_newline = QComboBox()
        self.combo_newline.addItems(["\\r\\n", "\\n", "\\r", "无"])
        self.combo_newline.setCurrentText("\\r\\n")
        self.combo_newline.setToolTip("发送时附加的换行符")
        self.combo_newline.setFixedWidth(64)
        layout.addWidget(self.combo_newline)

        self._btn_send = QPushButton("发送")
        self._btn_send.setObjectName("btn_primary")
        self._btn_send.setFixedWidth(60)
        self._btn_send.clicked.connect(self._on_send)
        layout.addWidget(self._btn_send)

        self._btn_log = QPushButton("💾 下载日志")
        self._btn_log.setToolTip("将终端内容保存为 .log 文件")
        self._btn_log.clicked.connect(self._on_save_log)
        layout.addWidget(self._btn_log)

        return bar

    def _build_search_bar(self) -> 'QWidget':
        """构建终端搜索栏（Ctrl+F 切换显示）"""
        from PyQt6.QtWidgets import QToolBar
        bar = QFrame()
        bar.setObjectName("search_frame")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(4)

        lbl = QLabel("🔍 搜索:")
        lbl.setFixedWidth(52)
        layout.addWidget(lbl)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词，Enter 搜索下一个...")
        self.search_edit.setFont(QFont("Consolas", 10))
        self.search_edit.returnPressed.connect(self._on_search_next)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_edit, stretch=1)

        btn_prev = QPushButton("↑ 上一个")
        btn_prev.setFixedWidth(70)
        btn_prev.clicked.connect(self._on_search_prev)
        layout.addWidget(btn_prev)

        btn_next = QPushButton("↓ 下一个")
        btn_next.setFixedWidth(70)
        btn_next.clicked.connect(self._on_search_next)
        layout.addWidget(btn_next)

        self._search_count_lbl = QLabel("")
        self._search_count_lbl.setFixedWidth(80)
        layout.addWidget(self._search_count_lbl)

        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(28)
        btn_close.setToolTip("关闭搜索 (Esc)")
        btn_close.clicked.connect(self._close_search)
        layout.addWidget(btn_close)

        bar.setVisible(False)
        # 安装 Esc 过滤
        self.search_edit.installEventFilter(self)
        return bar

    def _toggle_search(self):
        self._search_visible = not self._search_visible
        self._search_bar.setVisible(self._search_visible)
        if self._search_visible:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        else:
            self.input_line.setFocus()

    def _close_search(self):
        self._search_visible = False
        self._search_bar.setVisible(False)
        # 清除高亮
        self.terminal.setExtraSelections([])
        self._search_count_lbl.setText("")
        self.input_line.setFocus()

    def _on_search_text_changed(self, text: str):
        self._search_count_lbl.setText("")
        self.terminal.setExtraSelections([])
        if not text:
            return
        self._do_search(text, forward=True, wrap=True, count_only=True)

    def _on_search_next(self):
        txt = self.search_edit.text()
        if txt:
            self._do_search(txt, forward=True, wrap=True)

    def _on_search_prev(self):
        txt = self.search_edit.text()
        if txt:
            self._do_search(txt, forward=False, wrap=True)

    def _do_search(self, text: str, forward: bool = True,
                   wrap: bool = True, count_only: bool = False):
        from PyQt6.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
        from PyQt6.QtWidgets import QTextEdit

        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward

        # 高亮所有匹配
        doc = self.terminal.document()
        cursor = QTextCursor(doc)
        hi_fmt = QTextCharFormat()
        hi_fmt.setBackground(QColor('#F0C040'))
        hi_fmt.setForeground(QColor('#000000'))
        selections = []
        count = 0
        c = doc.find(text, 0)
        while not c.isNull():
            sel = QTextEdit.ExtraSelection()
            sel.cursor = c
            sel.format = hi_fmt
            selections.append(sel)
            count += 1
            c = doc.find(text, c)
        self.terminal.setExtraSelections(selections)
        self._search_count_lbl.setText(f"{count} 处")

        if count_only or count == 0:
            return

        # 移动到下一个匹配
        cur = self.terminal.textCursor()
        found = self.terminal.find(text, flags)
        if not found and wrap:
            # 回绕
            tmp = QTextCursor(doc)
            if forward:
                tmp.movePosition(QTextCursor.MoveOperation.Start)
            else:
                tmp.movePosition(QTextCursor.MoveOperation.End)
            self.terminal.setTextCursor(tmp)
            self.terminal.find(text, flags)

    def _build_quick_panel(self) -> QWidget:
        """构建右侧快捷指令面板（支持板块重排/新建）"""
        panel = QWidget()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(6)

        # ── 图标说明提示 ──
        icon_lbl = QLabel(
            "💡 板块标题可用 Emoji 图标，常用: "
            "📦🔧🧪📝🔍⚙️✅🔑📡🚀💾🔄"
        )
        icon_lbl.setWordWrap(True)
        icon_lbl.setToolTip(
            "在创建新板块时，标题直接输入 Emoji 即可使用图标\n"
            "快速参考:\n"
            "  📦 固件/包   🔧 工具/维修   🧪 测试\n"
            "  📝 命令/记录  🔍 搜索/查询   ⚙️ 设置\n"
            "  ✅ 完成/正确  🔑 权限/root   📡 通信\n"
            "  🚀 启动/执行  💾 保存/下载   🔄 刷新"
        )
        self._icon_hint_lbl = icon_lbl
        outer_layout.addWidget(icon_lbl)

        # ── 板块容器（用单独 layout 便于重排）──
        sec_widget = QWidget()
        self._sections_layout = QVBoxLayout(sec_widget)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(10)
        outer_layout.addWidget(sec_widget)

        # ── 构建各板块 ──
        built_in_secs = [
            self._build_firmware_group(),
            self._build_angle_test_group(),
            self._build_kst_angle_group(),
            self._build_kst_coord_group(),
            self._build_sysutil_group(),
            self._build_custom_group(),
        ]
        self._quick_sections_list = built_in_secs[:]
        for sec in built_in_secs:
            self._sections_layout.addWidget(sec)

        self._refresh_section_controls()

        # ── 新建板块按钮 ──
        btn_add = QPushButton("＋ 新建板块")
        btn_add.setObjectName("btn_add_section")
        btn_add.setStyleSheet(
            "QPushButton{color:#58A6FF;background:#1A2233;"
            "border:1px dashed #335577;border-radius:5px;padding:4px 8px;"
            "font-size:12px;}"
            "QPushButton:hover{background:#1E2D44;border-color:#58A6FF;}"
        )
        btn_add.clicked.connect(self._on_add_section)
        self._btn_add_section = btn_add
        outer_layout.addWidget(btn_add)

        outer_layout.addStretch()
        return panel

    def _refresh_section_controls(self):
        """更新所有板块的 ↑↓ 按钮可用状态"""
        n = len(self._quick_sections_list)
        for i, sec in enumerate(self._quick_sections_list):
            sec.set_controls(
                up_cb=(lambda checked, s=sec: self._move_section(s, -1)) if i > 0 else None,
                down_cb=(lambda checked, s=sec: self._move_section(s, +1)) if i < n - 1 else None,
                rename_cb=(lambda checked, s=sec: self._on_rename_section(s)),
            )

    def _move_section(self, sec: '_CollapsibleSection', direction: int):
        """在快捷面板内将板块上移（-1）或下移（+1）"""
        idx = self._quick_sections_list.index(sec)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._quick_sections_list):
            return
        self._quick_sections_list.insert(new_idx, self._quick_sections_list.pop(idx))
        # 从 layout 中移除全部再按新顺序插入
        for s in self._quick_sections_list:
            self._sections_layout.removeWidget(s)
        for s in self._quick_sections_list:
            self._sections_layout.addWidget(s)
            s.show()
        self._refresh_section_controls()

    def _on_rename_section(self, sec: '_CollapsibleSection'):
        new_name, ok = QInputDialog.getText(
            self, "重命名板块", "输入新名称（可直接输入 Emoji 图标）:",
            text=sec._title_lbl.text()
        )
        if ok and new_name.strip():
            sec.update_title(new_name.strip())
            self._save_all_data()  # 保存标题修改

    def _on_add_dyn_cmd(self, sec: '_CollapsibleSection'):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            sec._dyn_cmds.append({"name": name, "cmd": cmd})
            self._save_all_data()  # 保存更改
            self._refresh_dyn_buttons(sec)

    def _refresh_dyn_buttons(self, sec: '_CollapsibleSection'):
        t = _DARK if self._dark_mode else _LIGHT
        while sec._dyn_btns_layout.count():
            item = sec._dyn_btns_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        _STYLE = (
            f"QPushButton{{background:{t['btn_bg']};color:{t['btn_text']};"  
            f"border:1px solid {t['btn_bdr']};border-radius:5px;"
            f"padding:4px 8px;font-size:12px;text-align:left;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};"
            f"border-color:{t['btn_hover_bdr']};color:{t['combo_text']};}}"
        )
        
        # 获取动态板块在列表中的索引，用于编辑命令时定位
        sec_idx = None
        for idx, s in enumerate(self._quick_sections_list):
            if s is sec:
                sec_idx = idx
                break
        
        for i, item in enumerate(sec._dyn_cmds):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)
            
            btn = QPushButton(f"  {item['name']}")
            btn.setToolTip(f"<code>{item['cmd']}</code>")
            btn.setStyleSheet(_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, c=item['cmd']: self._send_command(c))
            row.addWidget(btn, stretch=1)
            
            btn_edit = QToolButton()
            btn_edit.setText("✏")
            btn_edit.setToolTip("编辑")
            btn_edit.setStyleSheet(f"color:{t['grp_title']};background:transparent;border:none;font-size:12px;")
            btn_edit.clicked.connect(lambda checked, s_idx=sec_idx, c_idx=i: self._on_edit_dyn_cmd(s_idx, c_idx))
            row.addWidget(btn_edit)
            
            btn_del = QToolButton()
            btn_del.setText("✕")
            btn_del.setStyleSheet("color:#E74C3C;background:transparent;border:none;")
            # 使用列表推导式避免闭包陷阱
            btn_del.clicked.connect((lambda s_idx, c_idx: lambda: (
                self._quick_sections_list[s_idx]._dyn_cmds.pop(c_idx),
                self._refresh_dyn_buttons(self._quick_sections_list[s_idx]),
                self._save_all_data()
            ))(sec_idx, i))
            row.addWidget(btn_del)
            
            container = QWidget()
            container.setLayout(row)
            sec._dyn_btns_layout.addWidget(container)
    
    def _on_edit_dyn_cmd(self, sec_idx: int, cmd_idx: int):
        """编辑动态板块中的命令"""
        if not (0 <= sec_idx < len(self._quick_sections_list)):
            return
        sec = self._quick_sections_list[sec_idx]
        if not (0 <= cmd_idx < len(sec._dyn_cmds)):
            return
        
        item = sec._dyn_cmds[cmd_idx]
        dlg = CmdEditDialog(name=item['name'], cmd=item['cmd'], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            sec._dyn_cmds[cmd_idx] = {"name": name, "cmd": cmd}
            self._save_all_data()
            self._refresh_dyn_buttons(sec)

    def _build_firmware_group(self) -> _CollapsibleSection:
        """固件升级准备区"""
        sec = _CollapsibleSection("📦 固件升级准备")
        layout = sec.body_layout

        # 说明文字（可编辑）
        self._fw_hint_text = (
            "💡 <b>固件升级流程说明</b><br>"
            "1. 将 <code>libxgimi.so</code> 拷贝到 U 盘根目录<br>"
            "2. U 盘插入投影仪，确认挂载路径<br>"
            "3. 按顺序执行以下步骤（建议每步确认结果后再点下一步）<br>"
            "4. 升级完成后记得备份原始 so 文件到安全位置"
        )
        self._fw_hint_lbl = QLabel(self._fw_hint_text)
        self._fw_hint_lbl.setWordWrap(True)
        self._fw_hint_lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(self._fw_hint_lbl)

        # 编辑说明按钮
        hint_row = QHBoxLayout()
        hint_row.addStretch()
        btn_edit_hint = QToolButton()
        btn_edit_hint.setText("✏")
        btn_edit_hint.setToolTip("编辑说明文字")
        btn_edit_hint.setFixedWidth(22)
        btn_edit_hint.setStyleSheet(
            "QToolButton{color:#8A98A5;background:transparent;border:none;font-size:11px;}"
            "QToolButton:hover{color:#58A6FF;}"
        )
        btn_edit_hint.clicked.connect(self._on_edit_fw_hint)
        hint_row.addWidget(btn_edit_hint)
        layout.addLayout(hint_row)

        # firmware 文件路径提示
        fw_exists = os.path.exists(_FIRMWARE_PATH)
        fw_color = '#4CAF50' if fw_exists else '#E74C3C'
        fw_icon = '✅' if fw_exists else '❌'
        fw_path_text = 'assets/firmware/libxgimi_MTK9660_GTV_4K.so' if fw_exists else '未找到，请手动放置'
        fw_label = QLabel(
            f"<span style='color:{fw_color};font-size:11px;'>"
            f"{fw_icon} 内置 so 文件: {fw_path_text}</span>"
        )
        fw_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(fw_label)

        self._fw_step_buttons = []
        self._fw_sec_layout = layout   # 保留引用，新增/删除步骤时用
        self._fw_sec = sec
        self._fw_step_rows: list = []  # QWidget 容器引用

        for i, step in enumerate(self._upgrade_steps):
            layout.addWidget(self._build_fw_step_row(i))

        # 添加步骤按钮
        btn_add_step = QPushButton("＋ 添加步骤")
        btn_add_step.setStyleSheet(
            "QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;"
            "border-radius:4px;padding:3px 8px;font-size:11px;}"
            "QPushButton:hover{background:#1B3D2A;}"
        )
        btn_add_step.clicked.connect(self._on_add_fw_step)
        layout.addWidget(btn_add_step)
        self._fw_add_step_btn = btn_add_step

        return sec

    def _build_angle_test_group(self) -> _CollapsibleSection:
        """角度测试"""
        sec = _CollapsibleSection("🔧 角度测试")
        layout = sec.body_layout

        # 说明文字
        lbl = QLabel(
            "💡 <b>角度测试说明</b><br>"
            "1. 将投影仪放置在合适位置<br>"
            "2. 按顺序执行以下步骤<br>"
            "3. 每步完成后观察投影仪角度变化"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 测试按钮
        btn = QPushButton("开始测试")
        btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #2A303C,stop:1 #1E2433);color:#C9D1D9;border:1px solid #444;"
            "border-radius:5px;padding:5px 8px;font-size:12px;}"
            "QPushButton:hover{background:#2D3748;border-color:#58A6FF;color:#fff;}"
            "QPushButton:pressed{background:#1E253A;padding-top:6px;}"
        )
        btn.clicked.connect(self._on_angle_test)
        layout.addWidget(btn)

        return sec

    def _build_kst_angle_group(self) -> _CollapsibleSection:
        """KST 角度校准"""
        sec = _CollapsibleSection("🔧 KST 角度校准")
        layout = sec.body_layout

        # 说明文字
        lbl = QLabel(
            "💡 <b>KST 角度校准说明</b><br>"
            "1. 将投影仪放置在合适位置<br>"
            "2. 按顺序执行以下步骤<br>"
            "3. 每步完成后观察投影仪角度变化"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 测试按钮
        btn = QPushButton("开始校准")
        btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #2A303C,stop:1 #1E2433);color:#C9D1D9;border:1px solid #444;"
            "border-radius:5px;padding:5px 8px;font-size:12px;}"
            "QPushButton:hover{background:#2D3748;border-color:#58A6FF;color:#fff;}"
            "QPushButton:pressed{background:#1E253A;padding-top:6px;}"
        )
        btn.clicked.connect(self._on_kst_angle)
        layout.addWidget(btn)

        return sec

    def _build_kst_coord_group(self) -> _CollapsibleSection:
        """KST 坐标校准"""
        sec = _CollapsibleSection("🔧 KST 坐标校准")
        layout = sec.body_layout

        # 说明文字
        lbl = QLabel(
            "💡 <b>KST 坐标校准说明</b><br>"
            "1. 将投影仪放置在合适位置<br>"
            "2. 按顺序执行以下步骤<br>"
            "3. 每步完成后观察投影仪角度变化"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 测试按钮
        btn = QPushButton("开始校准")
        btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #2A303C,stop:1 #1E2433);color:#C9D1D9;border:1px solid #444;"
            "border-radius:5px;padding:5px 8px;font-size:12px;}"
            "QPushButton:hover{background:#2D3748;border-color:#58A6FF;color:#fff;}"
            "QPushButton:pressed{background:#1E253A;padding-top:6px;}"
        )
        btn.clicked.connect(self._on_kst_coord)
        layout.addWidget(btn)

        return sec

    def _build_sysutil_group(self) -> _CollapsibleSection:
        """系统工具"""
        sec = _CollapsibleSection("⚙️ 系统工具")
        layout = sec.body_layout

        # 说明文字
        lbl = QLabel(
            "💡 <b>系统工具说明</b><br>"
            "1. 选择需要执行的命令<br>"
            "2. 点击按钮执行"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 动态命令按钮
        sec._dyn_btns_layout = QVBoxLayout()
        sec._dyn_btns_layout.setContentsMargins(0, 0, 0, 0)
        sec._dyn_btns_layout.setSpacing(3)
        sec._dyn_cmds = [
            {"name": "重启", "cmd": "reboot"},
            {"name": "关机", "cmd": "poweroff"},
            {"name": "进入 root shell", "cmd": "su"},
            {"name": "查看日志", "cmd": "logcat"},
            {"name": "查看分区", "cmd": "df -h"},
            {"name": "查看内存", "cmd": "free -h"},
            {"name": "查看进程", "cmd": "ps"},
            {"name": "查看网络", "cmd": "ifconfig"},
            {"name": "查看存储", "cmd": "ls /storage"},
            {"name": "查看系统信息", "cmd": "cat /proc/cpuinfo"},
        ]
        self._refresh_dyn_buttons(sec)

        # 添加命令按钮
        btn_add = QPushButton("＋ 添加命令")
        btn_add.setStyleSheet(
            "QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;"
            "border-radius:4px;padding:3px 8px;font-size:11px;}"
            "QPushButton:hover{background:#1B3D2A;}"
        )
        btn_add.clicked.connect(lambda checked, s=sec: self._on_add_dyn_cmd(s))
        layout.addWidget(btn_add)

        layout.addLayout(sec._dyn_btns_layout)

        return sec

    def _build_custom_group(self) -> _CollapsibleSection:
        """自定义命令"""
        sec = _CollapsibleSection("📝 自定义命令")
        layout = sec.body_layout

        # 说明文字
        lbl = QLabel(
            "💡 <b>自定义命令说明</b><br>"
            "1. 选择需要执行的命令<br>"
            "2. 点击按钮执行"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 动态命令按钮
        sec._dyn_btns_layout = QVBoxLayout()
        sec._dyn_btns_layout.setContentsMargins(0, 0, 0, 0)
        sec._dyn_btns_layout.setSpacing(3)
        sec._dyn_cmds = []

        # 添加命令按钮
        btn_add = QPushButton("＋ 添加命令")
        btn_add.setStyleSheet(
            "QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;"
            "border-radius:4px;padding:3px 8px;font-size:11px;}"
            "QPushButton:hover{background:#1B3D2A;}"
        )
        btn_add.clicked.connect(lambda checked, s=sec: self._on_add_dyn_cmd(s))
        layout.addWidget(btn_add)

        layout.addLayout(sec._dyn_btns_layout)

        return sec

    def _on_add_section(self):
        name, ok = QInputDialog.getText(
            self, "新建板块",
            "板块名称（可直接输入 Emoji，如 '🔑 Root操作'）："
        )
        if not ok or not name.strip():
            return
        sec = self._build_dynamic_section(name.strip())
        self._quick_sections_list.append(sec)
        self._sections_layout.addWidget(sec)
        self._refresh_section_controls()
        self._apply_theme()   # 应用当前主题样式到新板块
        self._save_all_data()  # 保存更改

    def _build_dynamic_section(self, name: str) -> _CollapsibleSection:
        """动态板块"""
        sec = _CollapsibleSection(name)
        layout = sec.body_layout

        # 说明文字（可编辑）
        lbl = QLabel("```\n\n```")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(lbl)

        # 编辑说明按钮
        hint_row = QHBoxLayout()
        hint_row.addStretch()
        btn_edit_hint = QToolButton()
        btn_edit_hint.setText("✏")
        btn_edit_hint.setToolTip("编辑说明文字")
        btn_edit_hint.setFixedWidth(22)
        btn_edit_hint.setStyleSheet(
            "QToolButton{color:#8A98A5;background:transparent;border:none;font-size:11px;}"
            "QToolButton:hover{color:#58A6FF;}"
        )
        # 获取当前动态板块的索引，传给编辑方法
        btn_edit_hint.clicked.connect(lambda checked, s=sec: self._on_edit_dyn_hint(s))
        hint_row.addWidget(btn_edit_hint)
        layout.addLayout(hint_row)

        # 动态命令按钮
        sec._dyn_btns_layout = QVBoxLayout()
        sec._dyn_btns_layout.setContentsMargins(0, 0, 0, 0)
        sec._dyn_btns_layout.setSpacing(3)
        sec._dyn_cmds = []

        # 添加命令按钮
        btn_add = QPushButton("＋ 添加命令")
        btn_add.setStyleSheet(
            "QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;"
            "border-radius:4px;padding:3px 8px;font-size:11px;}"
            "QPushButton:hover{background:#1B3D2A;}"
        )
        btn_add.clicked.connect(lambda checked, s=sec: self._on_add_dyn_cmd(s))
        layout.addWidget(btn_add)

        layout.addLayout(sec._dyn_btns_layout)

        return sec
    
    def _on_edit_dyn_hint(self, sec: '_CollapsibleSection'):
        """编辑动态板块的说明文字"""
        text, ok = QInputDialog.getMultiLineText(
            self, "编辑说明",
            "输入说明文本（支持Markdown）:",
            "```\n\n```"
        )
        if ok:
            # 这里可以保存说明文字到板块（需要添加属性）
            pass

    def _build_fw_step_row(self, i: int) -> QWidget:
        """构建单条固件升级步骤行"""
        _EDIT_QSS = (
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:4px;font-size:11px;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )
        step = self._upgrade_steps[i]
        btn_text, cmd, tip = step[0], step[1], step[2]

        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        btn = QPushButton(btn_text)
        btn.setToolTip(f"<b>指令:</b> <code>{cmd}</code><br><br>{tip}")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if "reboot" in cmd:
            btn.setObjectName("btn_danger")
        else:
            btn.setStyleSheet(
                "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #2A303C,stop:1 #1E2433);color:#C9D1D9;border:1px solid #444;"
                "border-radius:5px;padding:5px 8px;font-size:12px;}"
                "QPushButton:hover{background:#2D3748;border-color:#58A6FF;color:#fff;}"
                "QPushButton:pressed{background:#1E253A;padding-top:6px;}"
            )
        btn.clicked.connect(lambda checked, idx=i: self._send_command(self._upgrade_steps[idx][1]))
        if i < len(self._fw_step_buttons):
            self._fw_step_buttons[i] = btn
        else:
            self._fw_step_buttons.append(btn)
        row.addWidget(btn, stretch=1)

        btn_edit = QToolButton(); btn_edit.setText("✏")
        btn_edit.setToolTip("编辑指令"); btn_edit.setFixedWidth(24)
        btn_edit.setStyleSheet(_EDIT_QSS)
        btn_edit.clicked.connect(lambda checked, idx=i: self._on_edit_fw_step(idx))
        row.addWidget(btn_edit)

        btn_del = QToolButton(); btn_del.setText("✕")
        btn_del.setToolTip("删除此步骤"); btn_del.setFixedWidth(24)
        btn_del.setStyleSheet("QToolButton{color:#E74C3C;background:transparent;border:none;}"
                              "QToolButton:hover{color:#FF6B6B;}")
        btn_del.clicked.connect(lambda checked, idx=i, c=container: self._on_delete_fw_step(idx, c))
        row.addWidget(btn_del)

        if len(self._fw_step_rows) > i:
            self._fw_step_rows[i] = container
        else:
            self._fw_step_rows.append(container)
        return container

    def _on_edit_fw_hint(self):
        new_text, ok = QInputDialog.getMultiLineText(
            self, "编辑固件升级说明", "说明文字:", self._fw_hint_text
        )
        if ok:
            self._fw_hint_text = new_text
            self._fw_hint_lbl.setText(new_text)

    def _on_edit_fw_step(self, idx: int):
        step = self._upgrade_steps[idx]
        new_cmd, ok = QInputDialog.getText(
            self, f"编辑固件准备步骤 [{step[0]}]",
            "指令内容：",
            text=step[1]
        )
        if ok:
            self._upgrade_steps[idx][1] = new_cmd
            if idx < len(self._fw_step_buttons):
                self._fw_step_buttons[idx].setToolTip(
                    f"<b>指令:</b> <code>{new_cmd}</code><br><br>{step[2]}"
                )

    def _on_delete_fw_step(self, idx: int, container: QWidget):
        step = self._upgrade_steps[idx]
        reply = QMessageBox.question(
            self, "确认删除", f"删除步骤「{step[0]}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._upgrade_steps.pop(idx)
        container.setParent(None)
        if idx < len(self._fw_step_buttons):
            self._fw_step_buttons.pop(idx)
        if idx < len(self._fw_step_rows):
            self._fw_step_rows.pop(idx)

    def _on_add_fw_step(self):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            new_step = [name, cmd, ""]
            self._upgrade_steps.append(new_step)
            i = len(self._upgrade_steps) - 1
            row_widget = self._build_fw_step_row(i)
            # 在"添加步骤"按钮前插入
            add_btn_idx = self._fw_sec_layout.indexOf(self._fw_add_step_btn)
            self._fw_sec_layout.insertWidget(add_btn_idx, row_widget)

    def _build_angle_test_group(self) -> _CollapsibleSection:
        """角度采集测试区（含分辨率和范围参数）"""
        sec = _CollapsibleSection("🧪 角度采集测试")
        layout = sec.body_layout

        # 说明（可编辑）
        self._angle_desc_text = (
            "遍历 Yaw × Pitch 二维网格，调用 batchGetDisplayPointByAngle "
            "将每个角度对应的四角坐标写入 CSV（位于设备 /data/vendor/）。\n"
            "完成后需将 CSV 文件拷贝回 U 盘取走分析。"
        )
        desc_row = QHBoxLayout()
        self._angle_desc_lbl = QLabel(self._angle_desc_text)
        self._angle_desc_lbl.setWordWrap(True)
        self._angle_desc_lbl.setStyleSheet("font-size:11px;color:#546E7A;")
        desc_row.addWidget(self._angle_desc_lbl, stretch=1)
        btn_edit_desc = QToolButton(); btn_edit_desc.setText("✏")
        btn_edit_desc.setToolTip("编辑说明文字"); btn_edit_desc.setFixedWidth(22)
        btn_edit_desc.setStyleSheet(
            "QToolButton{color:#8A98A5;background:transparent;border:none;font-size:11px;}"
            "QToolButton:hover{color:#58A6FF;}"
        )
        btn_edit_desc.clicked.connect(self._on_edit_angle_desc)
        desc_row.addWidget(btn_edit_desc)
        layout.addLayout(desc_row)

        _COMBO_W = 60

        # ── 分辨率行 ──
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("分辨率:"))
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(["0 (默认/4K)", "1 (2K)", "2", "3"])
        self.combo_resolution.setFixedWidth(100)
        self.combo_resolution.setToolTip(
            "传入 batchGetDisplayPointByAngle 的第3个参数（分辨率/模式标识）\n"
            "0=默认(4K), 1=2K; 具体含义取决于固件版本"
        )
        self.combo_resolution.currentTextChanged.connect(
            lambda t: setattr(self, '_scan_resolution', t.split()[0])
        )
        res_row.addWidget(self.combo_resolution)
        res_row.addStretch()
        layout.addLayout(res_row)

        # ── Yaw 范围行 ──
        yaw_row = QHBoxLayout()
        yaw_row.addWidget(QLabel("Yaw 范围:"))
        self._spin_yaw_min = QDoubleSpinBox()
        self._spin_yaw_min.setRange(-180, 0); self._spin_yaw_min.setValue(-40)
        self._spin_yaw_min.setFixedWidth(_COMBO_W)
        self._spin_yaw_min.valueChanged.connect(
            lambda v: setattr(self, '_scan_yaw_min', str(int(v)))
        )
        yaw_row.addWidget(self._spin_yaw_min)
        yaw_row.addWidget(QLabel("~"))
        self._spin_yaw_max = QDoubleSpinBox()
        self._spin_yaw_max.setRange(0, 180); self._spin_yaw_max.setValue(40)
        self._spin_yaw_max.setFixedWidth(_COMBO_W)
        self._spin_yaw_max.valueChanged.connect(
            lambda v: setattr(self, '_scan_yaw_max', str(int(v)))
        )
        yaw_row.addWidget(self._spin_yaw_max)
        yaw_row.addStretch()
        layout.addLayout(yaw_row)

        # ── Pitch 范围行 ──
        pitch_row = QHBoxLayout()
        pitch_row.addWidget(QLabel("Pitch 范围:"))
        self._spin_pitch_min = QDoubleSpinBox()
        self._spin_pitch_min.setRange(-180, 0); self._spin_pitch_min.setValue(-40)
        self._spin_pitch_min.setFixedWidth(_COMBO_W)
        self._spin_pitch_min.valueChanged.connect(
            lambda v: setattr(self, '_scan_pitch_min', str(int(v)))
        )
        pitch_row.addWidget(self._spin_pitch_min)
        pitch_row.addWidget(QLabel("~"))
        self._spin_pitch_max = QDoubleSpinBox()
        self._spin_pitch_max.setRange(0, 180); self._spin_pitch_max.setValue(40)
        self._spin_pitch_max.setFixedWidth(_COMBO_W)
        self._spin_pitch_max.valueChanged.connect(
            lambda v: setattr(self, '_scan_pitch_max', str(int(v)))
        )
        pitch_row.addWidget(self._spin_pitch_max)
        pitch_row.addStretch()
        layout.addLayout(pitch_row)

        # ── 角度步进 ──
        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("步进:"))
        self.combo_step = QComboBox()
        self.combo_step.addItems(_STEP_OPTIONS)
        self.combo_step.setCurrentText("0.1")
        self.combo_step.setToolTip(
            "0.1° → ~(range/0.1)² 个点（慢）\n"
            "0.5° / 1° → 更快速验证"
        )
        self.combo_step.setFixedWidth(70)
        step_row.addWidget(self.combo_step)
        step_row.addStretch()
        layout.addLayout(step_row)

        _EDIT_QSS = (
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:4px;font-size:11px;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )

        # ── 发送采集指令 ──
        scan_row = QHBoxLayout()
        btn_scan = QPushButton("▶ 发送角度采集指令")
        btn_scan.setObjectName("btn_primary")
        btn_scan.setToolTip(
            "<b>执行角度坐标批量采集</b><br>"
            f"指令模板: <code>{self._scan_cmd_template}</code><br>"
            "占位符会自动替换为当前 UI 参数值"
        )
        btn_scan.clicked.connect(self._on_send_scan_cmd)
        self._btn_scan = btn_scan
        scan_row.addWidget(btn_scan, stretch=1)

        btn_edit_scan = QToolButton(); btn_edit_scan.setText("✏")
        btn_edit_scan.setToolTip("编辑采集指令模板")
        btn_edit_scan.setFixedWidth(26)
        btn_edit_scan.setStyleSheet(_EDIT_QSS)
        btn_edit_scan.clicked.connect(self._on_edit_scan_cmd)
        scan_row.addWidget(btn_edit_scan)
        layout.addLayout(scan_row)

        # ── 拷贝数据到 U 盘 ──
        copy_row = QHBoxLayout()
        btn_copy = QPushButton("📋 拷贝 CSV 到 U 盘")
        btn_copy.setToolTip(self._copy_csv_cmd)
        btn_copy.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #1D3557,stop:1 #152744);color:#90CAF9;border:1px solid #1565C0;"
            "border-radius:5px;padding:5px 8px;}"
            "QPushButton:hover{background:#1A4480;border-color:#42A5F5;color:#fff;}"
        )
        btn_copy.clicked.connect(lambda: self._send_command(self._copy_csv_cmd))
        self._btn_copy = btn_copy
        copy_row.addWidget(btn_copy, stretch=1)

        btn_edit_copy = QToolButton(); btn_edit_copy.setText("✏")
        btn_edit_copy.setToolTip("编辑 CSV 拷贝命令")
        btn_edit_copy.setFixedWidth(26)
        btn_edit_copy.setStyleSheet(_EDIT_QSS)
        btn_edit_copy.clicked.connect(self._on_edit_copy_cmd)
        copy_row.addWidget(btn_edit_copy)
        layout.addLayout(copy_row)

        return sec

    def _on_edit_angle_desc(self):
        new_text, ok = QInputDialog.getMultiLineText(
            self, "编辑角度采集说明", "说明文字:", self._angle_desc_text
        )
        if ok:
            self._angle_desc_text = new_text
            self._angle_desc_lbl.setText(new_text)

    def _build_kst_angle_group(self) -> _CollapsibleSection:
        """set_kst_by_angle 快捷设置区"""
        sec = _CollapsibleSection("📐 set_kst_by_angle", collapsed=True)
        layout = sec.body_layout

        desc = QLabel(
            "输入 Yaw、Pitch 角度和分辨率，发送 set_kst_by_angle 指令\n"
            "设置当前角度对应的 KST 梯形校正参数。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(desc)

        _COMBO_W = 80
        grid = QHBoxLayout()
        grid.addWidget(QLabel("Yaw:"))
        self._kst_yaw_spin = QDoubleSpinBox()
        self._kst_yaw_spin.setRange(-90, 90); self._kst_yaw_spin.setValue(0)
        self._kst_yaw_spin.setDecimals(1); self._kst_yaw_spin.setFixedWidth(_COMBO_W)
        grid.addWidget(self._kst_yaw_spin)

        grid.addWidget(QLabel("Pitch:"))
        self._kst_pitch_spin = QDoubleSpinBox()
        self._kst_pitch_spin.setRange(-90, 90); self._kst_pitch_spin.setValue(0)
        self._kst_pitch_spin.setDecimals(1); self._kst_pitch_spin.setFixedWidth(_COMBO_W)
        grid.addWidget(self._kst_pitch_spin)

        grid.addWidget(QLabel("Res:"))
        self._kst_angle_res = QComboBox()
        self._kst_angle_res.addItems(["0", "1", "2"])
        self._kst_angle_res.setFixedWidth(50)
        self._kst_angle_res.setToolTip("分辨率参数: 0=4K, 1=2K")
        grid.addWidget(self._kst_angle_res)
        grid.addStretch()
        layout.addLayout(grid)

        tpl_row = QHBoxLayout()
        self._kst_angle_tpl = (
            'gmpfUnit externDisplay kst_dev set_kst_by_angle '
            '"{yaw};{pitch};{resolution}"'
        )
        btn_send = QPushButton("▶ 发送 set_kst_by_angle")
        btn_send.setObjectName("btn_primary")
        btn_send.clicked.connect(self._on_send_kst_angle)
        tpl_row.addWidget(btn_send, stretch=1)

        btn_edit = QToolButton(); btn_edit.setText("✏")
        btn_edit.setToolTip("编辑命令模板")
        btn_edit.setFixedWidth(26)
        btn_edit.setStyleSheet(
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:4px;font-size:11px;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )
        btn_edit.clicked.connect(self._on_edit_kst_angle_tpl)
        tpl_row.addWidget(btn_edit)
        layout.addLayout(tpl_row)

        return sec

    def _on_send_kst_angle(self):
        yaw   = self._kst_yaw_spin.value()
        pitch = self._kst_pitch_spin.value()
        res   = self._kst_angle_res.currentText()
        cmd = (self._kst_angle_tpl
               .replace('{yaw}', str(yaw))
               .replace('{pitch}', str(pitch))
               .replace('{resolution}', res))
        self._send_command(cmd)

    def _on_edit_kst_angle_tpl(self):
        new_tpl, ok = QInputDialog.getText(
            self, "编辑 set_kst_by_angle 模板",
            "模板（{yaw}/{pitch}/{resolution} 会被替换）:",
            text=self._kst_angle_tpl
        )
        if ok and new_tpl.strip():
            self._kst_angle_tpl = new_tpl.strip()

    def _build_kst_coord_group(self) -> _CollapsibleSection:
        """set_kst_by_coord 快捷设置区"""
        sec = _CollapsibleSection("📌 set_kst_by_coord", collapsed=True)
        layout = sec.body_layout

        desc = QLabel(
            "输入四角坐标（像素），发送 set_kst_by_coord 指令\n"
            "直接按坐标设置 KST 梯形校正参数。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size:11px;color:#546E7A;")
        layout.addWidget(desc)

        _W = 90
        def _coord_row(label_text, attr_name):
            r = QHBoxLayout()
            r.addWidget(QLabel(label_text))
            ln = QLineEdit("0,0")
            ln.setPlaceholderText("x,y")
            ln.setFixedWidth(_W)
            setattr(self, attr_name, ln)
            r.addWidget(ln)
            r.addStretch()
            return r

        layout.addLayout(_coord_row("TL (左上):", '_kst_coord_tl'))
        layout.addLayout(_coord_row("TR (右上):", '_kst_coord_tr'))
        layout.addLayout(_coord_row("BL (左下):", '_kst_coord_bl'))
        layout.addLayout(_coord_row("BR (右下):", '_kst_coord_br'))

        self._kst_coord_tpl = (
            'gmpfUnit externDisplay kst_dev set_kst_by_coord '
            '"{tl};{tr};{bl};{br}"'
        )
        btn_row = QHBoxLayout()
        btn_send = QPushButton("▶ 发送 set_kst_by_coord")
        btn_send.setObjectName("btn_primary")
        btn_send.clicked.connect(self._on_send_kst_coord)
        btn_row.addWidget(btn_send, stretch=1)

        btn_edit = QToolButton(); btn_edit.setText("✏")
        btn_edit.setToolTip("编辑命令模板")
        btn_edit.setFixedWidth(26)
        btn_edit.setStyleSheet(
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:4px;font-size:11px;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )
        btn_edit.clicked.connect(self._on_edit_kst_coord_tpl)
        btn_row.addWidget(btn_edit)
        layout.addLayout(btn_row)

        return sec

    def _on_send_kst_coord(self):
        tl = self._kst_coord_tl.text().strip() or '0,0'
        tr = self._kst_coord_tr.text().strip() or '0,0'
        bl = self._kst_coord_bl.text().strip() or '0,0'
        br = self._kst_coord_br.text().strip() or '0,0'
        cmd = (self._kst_coord_tpl
               .replace('{tl}', tl)
               .replace('{tr}', tr)
               .replace('{bl}', bl)
               .replace('{br}', br))
        self._send_command(cmd)

    def _on_edit_kst_coord_tpl(self):
        new_tpl, ok = QInputDialog.getText(
            self, "编辑 set_kst_by_coord 模板",
            "模板（{tl}/{tr}/{bl}/{br} 会被替换为 x,y 形式）:",
            text=self._kst_coord_tpl
        )
        if ok and new_tpl.strip():
            self._kst_coord_tpl = new_tpl.strip()

    def _on_edit_scan_cmd(self):
        new_tpl, ok = QInputDialog.getText(
            self, "编辑角度采集指令模板",
            "模板（{resolution}/{yaw_min}/{yaw_max}/{pitch_min}/{pitch_max}/{step} 会被替换）：",
            text=self._scan_cmd_template
        )
        if ok and new_tpl.strip():
            self._scan_cmd_template = new_tpl.strip()
            self._btn_scan.setToolTip(
                "<b>指令模板:</b><br><code>" + self._scan_cmd_template + "</code>"
            )

    def _on_edit_copy_cmd(self):
        new_cmd, ok = QInputDialog.getText(
            self, "编辑 CSV 拷贝命令",
            "指令内容：",
            text=self._copy_csv_cmd
        )
        if ok and new_cmd.strip():
            self._copy_csv_cmd = new_cmd.strip()
            self._btn_copy.setToolTip(self._copy_csv_cmd)

    def _build_sysutil_group(self) -> _CollapsibleSection:
        """系统工具区（指令可手动编辑）"""
        sec = _CollapsibleSection("🔧 系统工具")
        layout = sec.body_layout
        self._sysutil_btns = []

        _EDIT_BTN_QSS = (
            "QToolButton{color:#8A98A5;background:transparent;"
            "border:1px solid #444;border-radius:4px;font-size:11px;}"
            "QToolButton:hover{color:#fff;border-color:#58A6FF;}"
        )

        for i, tool in enumerate(self._sysutil_tools):
            name, cmd, tip = tool[0], tool[1], tool[2]
            row = QHBoxLayout()
            btn = QPushButton(f"  {name}")
            btn.setToolTip(f"<b>指令:</b><br><code>{cmd}</code><br><br>{tip}")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, idx=i: self._send_command(self._sysutil_tools[idx][1]))
            self._sysutil_btns.append(btn)
            row.addWidget(btn, stretch=1)

            btn_edit = QToolButton()
            btn_edit.setText("✏")
            btn_edit.setToolTip("编辑该工具指令")
            btn_edit.setFixedWidth(26)
            btn_edit.setStyleSheet(_EDIT_BTN_QSS)
            btn_edit.clicked.connect(lambda checked, idx=i: self._on_edit_sysutil(idx))
            row.addWidget(btn_edit)
            layout.addLayout(row)

        return sec

    def _on_edit_sysutil(self, idx: int):
        tool = self._sysutil_tools[idx]
        new_cmd, ok = QInputDialog.getText(
            self, f"编辑系统工具指令 [{tool[0]}]",
            "指令内容：",
            text=tool[1]
        )
        if ok:
            self._sysutil_tools[idx][1] = new_cmd
            self._sysutil_btns[idx].setToolTip(
                f"<b>指令:</b><br><code>{new_cmd}</code><br><br>{tool[2]}"
            )

    def _build_custom_group(self) -> _CollapsibleSection:
        """自定义快捷指令区"""
        sec = _CollapsibleSection("📝 自定义快捷指令")
        self._custom_group = sec
        layout = sec.body_layout

        # 工具栏
        tool_row = QHBoxLayout()
        btn_add = QPushButton("＋ 添加")
        btn_add.setStyleSheet(
            "QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;"
            "border-radius:4px;padding:3px 8px;font-size:11px;}"
            "QPushButton:hover{background:#1B3D2A;}"
        )
        btn_add.clicked.connect(self._on_add_custom)
        tool_row.addWidget(btn_add)
        tool_row.addStretch()
        layout.addLayout(tool_row)

        # 指令按钮容器
        self._custom_btns_widget = QWidget()
        self._custom_btns_layout = QVBoxLayout(self._custom_btns_widget)
        self._custom_btns_layout.setContentsMargins(0, 0, 0, 0)
        self._custom_btns_layout.setSpacing(4)
        layout.addWidget(self._custom_btns_widget)

        self._refresh_custom_buttons()
        return sec

    # ──────────────────────────────────────────────────────────────────────────
    #  串口操作
    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_ports(self):
        try:
            import serial.tools.list_ports
            ports = [p.device for p in serial.tools.list_ports.comports()]
        except ImportError:
            ports = []
        self.combo_port.clear()
        if ports:
            self.combo_port.addItems(ports)
        else:
            self.combo_port.addItem("（无可用端口）")

    def _on_toggle_connect(self):
        if self._serial and self._serial.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        try:
            import serial
        except ImportError:
            QMessageBox.critical(self, "缺少依赖", "请先安装 pyserial:\n  pip install pyserial")
            return

        port = self.combo_port.currentText()
        if not port or "（" in port:
            QMessageBox.warning(self, "提示", "请先选择有效的串口端口")
            return

        baud = int(self.combo_baud.currentText())
        data_bits_map = {"5": 5, "6": 6, "7": 7, "8": 8}
        parity_map = {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}
        stop_map = {"1": 1, "1.5": 1.5, "2": 2}

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=data_bits_map[self.combo_data.currentText()],
                parity=parity_map[self.combo_parity.currentText()],
                stopbits=stop_map[self.combo_stop.currentText()],
                timeout=0.1,
            )
            self._sys_msg(f"已连接 {port} @ {baud}bps")
            self._set_connected(True)
            self._start_reader()
        except Exception as e:
            QMessageBox.critical(self, "连接失败", str(e))
            self._sys_msg(f"连接失败: {e}", error=True)

    def _disconnect(self):
        self._stop_reader()
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        self._set_connected(False)
        self._sys_msg("串口已断开")

    def _start_reader(self):
        from workers.serial_worker import SerialReaderThread
        self._reader_thread = SerialReaderThread(self._serial)
        self._reader_thread.data_received.connect(self._on_data_received)
        self._reader_thread.error_occurred.connect(self._on_serial_error)
        self._reader_thread.disconnected.connect(self._on_serial_disconnected)
        self._reader_thread.start()

    def _stop_reader(self):
        if self._reader_thread:
            self._reader_thread.stop()
            self._reader_thread = None

    def _set_connected(self, connected: bool):
        self._connected = connected
        if connected:
            self.btn_connect.setText("  断开  ")
            self.btn_connect.setObjectName("btn_danger")
            self.lbl_status.setText("● 已连接")
            self.lbl_status.setStyleSheet("color:#4CAF50; font-size:12px; font-weight:bold;")
        else:
            self.btn_connect.setText("  连接  ")
            self.btn_connect.setObjectName("btn_primary")
            self.lbl_status.setText("● 未连接")
            self.lbl_status.setStyleSheet("color:#E74C3C; font-size:12px; font-weight:bold;")
        # 重新应用样式
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)

    # ──────────────────────────────────────────────────────────────────────────
    #  数据收发
    # ──────────────────────────────────────────────────────────────────────────
    def _on_data_received(self, data: bytes):
        """处理接收到的原始数据
        
        支持 \r\n / \n / \r 三种行尾，并定期刷出无换行的 shell 提示符。
        """
        if self._workflow_active:
            self._workflow_last_rx_ts = time.monotonic()
            self._workflow_cmd_started = True
        self._rx_buffer.extend(data)
        self._process_rx_buffer()

    def _process_rx_buffer(self):
        """\u62c6分 buffer 中完整的行（\n 或 \r）\u5e76输出"""
        # 统一把 \r\n 变为 \n，再把单独 \r 变为 \n
        normalized = self._rx_buffer.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        if b'\n' in normalized:
            lines = normalized.split(b'\n')
            # 最后一块可能是不完整的行，保留在 buffer
            for line_bytes in lines[:-1]:
                line = line_bytes.decode('utf-8', errors='replace')
                if line:  # 跳过空行
                    self._append_terminal(line, color=self._detect_rx_color(line))
                    self._log_lines.append(f"[RX] {line}")
            # 将未完成的残余写回 buffer
            remainder = lines[-1]
            self._rx_buffer = bytearray(remainder)
        else:
            self._rx_buffer = bytearray(normalized)

    def _flush_rx_buffer(self):
        """定期将 buffer 中没有换行字符的内容刷入终端（如 shell 提示符）"""
        if self._rx_buffer:
            line = self._rx_buffer.decode('utf-8', errors='replace')
            self._rx_buffer.clear()
            if line.strip():
                self._append_terminal(line, color=self._detect_rx_color(line))
                self._log_lines.append(f"[RX] {line}")

    def _on_send(self):
        # 不移除内容，支持发送空白行
        cmd = self.input_line.text()
        self._send_command(cmd)
        # 加入历史（不记录纯空白、不重复尾部）
        cmd_stripped = cmd.strip()
        if cmd_stripped:
            if not self._cmd_history or self._cmd_history[-1] != cmd_stripped:
                self._cmd_history.append(cmd_stripped)
        # 重置历史导航和 Tab 状态
        self._history_idx   = -1
        self._tab_candidates = []
        self._tab_idx       = -1
        self.input_line.clear()

    def _send_command(self, cmd: str):
        nl_map = {"\\r\\n": b'\r\n', "\\n": b'\n', "\\r": b'\r', "无": b''}
        nl = nl_map.get(self.combo_newline.currentText(), b'\r\n')

        if self._serial and self._serial.is_open:
            try:
                self._serial.write(cmd.encode('utf-8') + nl)
                self._append_terminal(f"▶ {cmd}" if cmd else "▶ ␍", color=self._tx_color)
                self._log_lines.append(f"[TX] {cmd}")
            except Exception as e:
                self._sys_msg(f"发送失败: {e}", error=True)
        else:
            self._sys_msg("⚠ 串口未连接，无法发送指令", error=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  终端内联输入（WindTerm 风格）
    # ──────────────────────────────────────────────────────────────────────────
    def _terminal_enter_input_mode(self, first_char: str = ''):
        """进入内联输入模式：在终端末尾插入提示符，允许直接在日志区域输入指令。"""
        self._terminal_input_mode = True
        self._terminal_input_buf = first_char
        cur = self.terminal.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        # 若末尾不是换行，先补一个
        doc_text = self.terminal.toPlainText()
        fmt_prompt = QTextCharFormat()
        fmt_prompt.setForeground(QColor('#58A6FF'))   # 蓝色提示符
        if doc_text and not doc_text.endswith('\n'):
            cur.insertText('\n', fmt_prompt)
        cur.insertText('➤ ', fmt_prompt)
        self._terminal_input_anchor = cur.position()
        # 插入第一个字符
        if first_char:
            fmt_input = QTextCharFormat()
            fmt_input.setForeground(QColor('#79C0FF'))
            cur.insertText(first_char, fmt_input)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()

    def _terminal_commit_input(self):
        """提交内联输入：清除状态。"""
        self._terminal_input_mode = False
        self._terminal_input_anchor = -1
        self._terminal_input_buf = ''

    def _terminal_tab_complete(self):
        """内联输入模式下的 Tab 补全：借用 input_line 的补全逻辑。"""
        old_text = self.input_line.text()
        # 将当前内联 buf 同步到 input_line，让 _on_tab_complete() 可以操作
        self.input_line.setText(self._terminal_input_buf)
        self._on_tab_complete()
        new_text = self.input_line.text()
        self.input_line.setText(old_text)   # 恢复 input_line

        if new_text == self._terminal_input_buf:
            return   # 无补全结果

        # 计算需要在终端末尾替换的字符数
        old_len = len(self._terminal_input_buf)
        new_len = len(new_text)
        # 删除末尾 old_len 个字符（已输入内容），追加 new_text
        cur = self.terminal.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        for _ in range(old_len):
            cur.deletePreviousChar()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor('#79C0FF'))
        cur.insertText(new_text, fmt)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()
        self._terminal_input_buf = new_text

    def _terminal_history_cycle(self, direction: int):
        """内联输入模式下的上/下键历史导航（direction=-1上一条, +1下一条）。"""
        if not self._cmd_history:
            return
        old_text = self.input_line.text()
        self.input_line.setText(self._terminal_input_buf)
        if direction == -1:
            self._history_prev()
        else:
            self._history_next()
        new_text = self.input_line.text()
        self.input_line.setText(old_text)

        if new_text == self._terminal_input_buf:
            return

        old_len = len(self._terminal_input_buf)
        cur = self.terminal.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        for _ in range(old_len):
            cur.deletePreviousChar()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor('#79C0FF'))
        cur.insertText(new_text, fmt)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()
        self._terminal_input_buf = new_text

    def _terminal_cancel_input(self):
        """取消内联输入：删除已输入的文字和提示符。"""
        if self._terminal_input_anchor >= 0:
            # 提示符 '➤ ' 占 2 字符，anchor 指向第一个输入字符位置
            remove_from = max(0, self._terminal_input_anchor - 2)
            cur = self.terminal.textCursor()
            cur.setPosition(remove_from)
            cur.movePosition(QTextCursor.MoveOperation.End,
                             QTextCursor.MoveMode.KeepAnchor)
            cur.removeSelectedText()
            self.terminal.setTextCursor(cur)
        self._terminal_input_mode = False
        self._terminal_input_anchor = -1
        self._terminal_input_buf = ''

    # ──────────────────────────────────────────────────────────────────────────
    #  输入框事件拦截（Tab补全 / 上下键历史）
    # ──────────────────────────────────────────────────────────────────────────
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # ── 搜索栏 Esc 关闭 ──────────────────────────────────────────
            if hasattr(self, 'search_edit') and obj is self.search_edit:
                if key == Qt.Key.Key_Escape:
                    self._close_search()
                    return True
            if obj is self.terminal:
                # Ctrl+F：切换搜索栏
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_F):
                    self._toggle_search()
                    return True

                # Ctrl+C：有选中 → 复制；内联输入中 → 取消；否则静默
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_C):
                    if self.terminal.textCursor().hasSelection():
                        return False   # 让 Qt 处理复制
                    if self._terminal_input_mode:
                        self._terminal_cancel_input()
                    return True

                # ── 内联输入模式：已有活跃输入 ──────────────────────────────
                if self._terminal_input_mode:
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        cmd = self._terminal_input_buf
                        self._terminal_commit_input()
                        # 无论 cmd 是否为空都调用 _send_command（空回车也要发送）
                        self._send_command(cmd)
                        stripped = cmd.strip()
                        if stripped:
                            if not self._cmd_history or self._cmd_history[-1] != stripped:
                                self._cmd_history.append(stripped)
                            self._history_idx = -1
                            self._tab_candidates = []
                            self._tab_idx = -1
                        return True

                    if key == Qt.Key.Key_Backspace:
                        if self._terminal_input_buf:
                            self._terminal_input_buf = self._terminal_input_buf[:-1]
                            cur = self.terminal.textCursor()
                            cur.movePosition(QTextCursor.MoveOperation.End)
                            cur.deletePreviousChar()
                            self.terminal.setTextCursor(cur)
                        return True

                    if key == Qt.Key.Key_Up:
                        self._terminal_history_cycle(-1)
                        return True

                    if key == Qt.Key.Key_Down:
                        self._terminal_history_cycle(1)
                        return True

                    if key == Qt.Key.Key_Tab:
                        if self._is_tab_passthrough_enabled():
                            self._send_tab_character()
                        else:
                            self._terminal_tab_complete()
                        return True

                    if key == Qt.Key.Key_Escape:
                        self._terminal_cancel_input()
                        return True

                    char = event.text()
                    if char and (char.isprintable() or char == ' ') and modifiers in (
                            Qt.KeyboardModifier.NoModifier,
                            Qt.KeyboardModifier.ShiftModifier):
                        self._terminal_input_buf += char
                        cur = self.terminal.textCursor()
                        cur.movePosition(QTextCursor.MoveOperation.End)
                        fmt = QTextCharFormat()
                        fmt.setForeground(QColor('#79C0FF'))
                        cur.insertText(char, fmt)
                        self.terminal.setTextCursor(cur)
                        self.terminal.ensureCursorVisible()
                        return True

                    # 其他键（翻页、方向键）保留给终端滚动
                    return False

                # ── 非内联输入模式 ────────────────────────────────────────────
                # 直接回车：发送空命令（相当于在终端按 Enter）
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and modifiers == Qt.KeyboardModifier.NoModifier:
                    self._send_command('')
                    return True

                # 可打印字符 → 进入内联输入
                char = event.text()
                if char and char.isprintable() and modifiers in (
                        Qt.KeyboardModifier.NoModifier,
                        Qt.KeyboardModifier.ShiftModifier):
                    self._terminal_enter_input_mode(char)
                    return True

                # 上下翻页键保留给终端滚动
                return False

            # ── 输入框焦点时 ──────────────────────────────────────────────
            if obj is self.input_line:
                # Ctrl+F：切换搜索栏
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_F):
                    self._toggle_search()
                    return True

                # ── Ctrl+字母 → 直接发送控制字符 ──
                if modifiers == Qt.KeyboardModifier.ControlModifier:
                    _CTRL_MAP = {
                        Qt.Key.Key_C:          ('\x03', 'Ctrl+C  (中断)'),
                        Qt.Key.Key_Z:          ('\x1a', 'Ctrl+Z  (挂起)'),
                        Qt.Key.Key_D:          ('\x04', 'Ctrl+D  (EOF)'),
                        Qt.Key.Key_L:          ('\x0c', 'Ctrl+L  (清屏)'),
                        Qt.Key.Key_Backslash:  ('\x1c', 'Ctrl+\\  (SIGQUIT)'),
                        Qt.Key.Key_X:          ('\x18', 'Ctrl+X'),
                        Qt.Key.Key_A:          ('\x01', 'Ctrl+A  (行首)'),
                        Qt.Key.Key_E:          ('\x05', 'Ctrl+E  (行尾)'),
                        Qt.Key.Key_K:          ('\x0b', 'Ctrl+K  (剔除到行尾)'),
                        Qt.Key.Key_U:          ('\x15', 'Ctrl+U  (剔除到行首)'),
                    }
                    if key in _CTRL_MAP:
                        char, label = _CTRL_MAP[key]
                        if key == Qt.Key.Key_C and self.input_line.hasSelectedText():
                            return super().eventFilter(obj, event)
                        if self._serial and self._serial.is_open:
                            try:
                                self._serial.write(char.encode('latin-1'))
                                self._append_terminal(f'  [{label}]', color=self._sys_color)
                                self._log_lines.append(f'[CTRL] {label}')
                            except Exception as e:
                                self._sys_msg(f'发送失败: {e}', error=True)
                        else:
                            self._sys_msg('⚠ 串口未连接', error=True)
                        return True

                if key == Qt.Key.Key_Tab:
                    if self._is_tab_passthrough_enabled():
                        self._send_tab_character()
                    else:
                        self._on_tab_complete()
                    return True
                elif key == Qt.Key.Key_Up:
                    self._history_prev()
                    return True
                elif key == Qt.Key.Key_Down:
                    self._history_next()
                    return True
                else:
                    self._tab_candidates = []
                    self._tab_idx = -1

        return super().eventFilter(obj, event)

    def _on_tab_complete(self):
        current = self.input_line.text()

        # 首次按 Tab：构建候选列表
        if not self._tab_candidates:
            self._pre_tab_text = current

            # 分析当前输入：拳陔最后一个「词」作为补全前缀
            # 例： "ls /vendor/li" → prefix_word="/vendor/li"， base="ls "
            parts = current.rsplit(' ', 1)
            if len(parts) == 2:
                base_text   = parts[0] + ' '   # 保留前半段
                prefix_word = parts[1].lower()  # 要补全的尾巴
            else:
                base_text   = ''
                prefix_word = current.lower()

            seen: set = set()
            candidates = []

            def _add(text: str, keep_base: bool):
                """insert candidate; keep_base=True 表示返回 base_text + text"""
                full = (base_text + text) if keep_base else text
                if full not in seen:
                    seen.add(full)
                    candidates.append(full)

            # 1. 尾巴匹配路径缓存（优先）
            if prefix_word.startswith('/'):
                for p in self._rx_path_cache:
                    if p.lower().startswith(prefix_word):
                        _add(p, keep_base=True)

            # 2. 尾巴匹配历史指令 —— 如果 base 为空，则作为完整指令匹配
            all_cmds = self._get_all_known_cmds()
            for c in all_cmds:
                if base_text == '':
                    # 全匹配模式（无空格前缀）
                    if c.lower().startswith(prefix_word):
                        _add(c, keep_base=False)
                else:
                    # 指令结尾词匹配模式
                    c_last = c.split(' ')[-1] if ' ' in c else c
                    if c_last.lower().startswith(prefix_word) and c_last not in seen:
                        _add(c_last, keep_base=True)
                    # 就整个历史指令匹配
                    if c.lower().startswith(current.lower()):
                        _add(c, keep_base=False)

            if not candidates:
                return
            self._tab_candidates = candidates
            self._tab_idx = -1

        # 循环切换候选
        self._tab_idx = (self._tab_idx + 1) % len(self._tab_candidates)
        candidate = self._tab_candidates[self._tab_idx]
        self.input_line.setText(candidate)
        self.input_line.setCursorPosition(len(candidate))

    def _get_all_known_cmds(self) -> list:
        """返回所有可用于 Tab 补全的命令（历史优先，再加内置快捷命令）"""
        cmds = list(reversed(self._cmd_history))   # 最近的在前
        # 追加内置升级步骤
        for step in self._upgrade_steps:
            cmds.append(step[1])
        # 追加系统工具指令
        for tool in self._sysutil_tools:
            cmds.append(tool[1])
        # 追加角度采集命令（带当前参数展开）
        step_val = getattr(self, 'combo_step', None)
        step_str = step_val.currentText() if step_val else '0.1'
        scan_expanded = (self._scan_cmd_template
                         .replace('{resolution}', getattr(self, '_scan_resolution', '0'))
                         .replace('{yaw_min}',    getattr(self, '_scan_yaw_min',   '-40'))
                         .replace('{yaw_max}',    getattr(self, '_scan_yaw_max',   '40'))
                         .replace('{pitch_min}',  getattr(self, '_scan_pitch_min', '-40'))
                         .replace('{pitch_max}',  getattr(self, '_scan_pitch_max', '40'))
                         .replace('{step}',       step_str))
        cmds.append(scan_expanded)
        cmds.append(self._copy_csv_cmd)
        # KST 命令模板
        if hasattr(self, '_kst_angle_tpl'):
            cmds.append(self._kst_angle_tpl)
        if hasattr(self, '_kst_coord_tpl'):
            cmds.append(self._kst_coord_tpl)
        # 追加自定义命令
        for item in self._custom_cmds:
            cmds.append(item['cmd'])
        # 追加动态板块命令
        for sec in self._quick_sections_list:
            if hasattr(sec, '_dyn_cmds'):
                for item in sec._dyn_cmds:
                    cmds.append(item['cmd'])
        return cmds

    def _history_prev(self):
        """上键：向更早的历史移动"""
        if not self._cmd_history:
            return
        if self._history_idx == -1:
            self._live_input = self.input_line.text()
            self._history_idx = len(self._cmd_history) - 1
        elif self._history_idx > 0:
            self._history_idx -= 1
        cmd = self._cmd_history[self._history_idx]
        self.input_line.setText(cmd)
        self.input_line.setCursorPosition(len(cmd))

    def _history_next(self):
        """下键：向更新的历史移动，回到末尾时恢复实时输入"""
        if self._history_idx == -1:
            return
        self._history_idx += 1
        if self._history_idx >= len(self._cmd_history):
            self._history_idx = -1
            self.input_line.setText(self._live_input)
            self.input_line.setCursorPosition(len(self._live_input))
        else:
            cmd = self._cmd_history[self._history_idx]
            self.input_line.setText(cmd)
            self.input_line.setCursorPosition(len(cmd))

    # ──────────────────────────────────────────────────────────────────────────
    #  RX 内容颜色检测（语法高亮）
    # ──────────────────────────────────────────────────────────────────────────
    # Android 日志级别颜色表（深色主题）
    _LOGCAT_COLORS_DARK = {
        'V': '#8A8A8A',   # Verbose  → 灰
        'D': '#74B9FF',   # Debug    → 淡蓝
        'I': '#C9D1D9',   # Info     → 默认白
        'W': '#F0C040',   # Warning  → 黄
        'E': '#FF6B6B',   # Error    → 红
        'F': '#FF4757',   # Fatal    → 深红
    }
    _LOGCAT_COLORS_LIGHT = {
        'V': '#888888',
        'D': '#0550AE',
        'I': '#1F2328',
        'W': '#7D4E00',
        'E': '#CF222E',
        'F': '#A40000',
    }

    # 关键词规则列表：(颜色_dark, 颜色_light, [关键词...])
    _KW_RULES = [
        ('#FF6B6B', '#CF222E', [
            'error', 'err:', ' err ', 'fail', 'failed', 'failure',
            'fatal', 'exception', 'crash', 'panic', 'abort', 'assert',
            'traceback', 'stacktrace', 'undefined', 'invalid', 'illegal',
            'denied', 'permission denied', 'no such file', 'not found',
            'cannot', "can't", 'unable to', 'refused', 'rejected',
            'segfault', 'sigsegv', 'killed', 'out of memory', 'oom',
            'timed out', 'connection refused', 'bad address',
        ]),
        ('#F0C040', '#7D4E00', [
            'warn', 'warning', 'deprecated', 'caution', 'attention',
            'skip', 'timeout', 'retry', 'slow', 'skipped',
            'incomplete', 'partial', 'miss', 'not support', 'fallback',
            'deprecated', 'disabled', 'offline',
        ]),
        ('#56D364', '#1A7F37', [
            'success', 'succeed', 'completed', 'done', 'finish', 'ok:',
            'passed', '[ ok ]', '[  ok  ]', 'started', 'ready',
            'connected', 'enabled', 'loaded', 'initialized', 'mount',
            'install', 'update complete', 'write ok', 'read ok',
        ]),
        ('#74B9FF', '#0550AE', [
            'info:', 'debug:', 'verbose:', 'notice:', '>>> ', '<<< ',
            'i/', 'd/', 'v/', 'begin', 'start', 'init', 'open',
            'sending', 'receiving', 'connecting',
        ]),
        ('#BD93F9', '#6F4297', [
            'gmpfunit', 'externDisplay', 'kst_dev', 'batchget',
            'ak_scan', '/data/vendor', '/mnt/media_rw',
        ]),
        ('#FFB86C', '#C2410C', [
            'reboot', 'poweroff', 'shutdown', 'reset', 'factory reset',
            'wipe', 'format', 'erase', 'delete', 'remove', 'rm -rf',
        ]),
    ]

    def _detect_rx_color(self, line: str) -> str:
        """根据行内容推断高亮颜色（高亮关闭时返回默认 RX 颜色）"""
        if not self._highlight_rx:
            return self._rx_color
        t_lc = self._LOGCAT_COLORS_DARK if self._dark_mode else self._LOGCAT_COLORS_LIGHT
        # ── logcat: "MM-DD HH:MM:SS.sss  pid  tid  L/Tag:" (verbose logcat)
        m = re.match(r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+([VDIWEF])\s', line)
        if m:
            return t_lc.get(m.group(1), self._rx_color)
        # ── logcat: "L/Tag: msg"  or "L Tag : msg"
        m = re.match(r'^([VDIWEF])/\S', line)
        if m:
            return t_lc.get(m.group(1), self._rx_color)
        # ── 通用关键词匹配
        ll = line.lower()
        kw_rules = self._KW_RULES
        for dark_c, light_c, keywords in kw_rules:
            if any(kw in ll for kw in keywords):
                return dark_c if self._dark_mode else light_c
        return self._rx_color

    # ──────────────────────────────────────────────────────────────────────────
    #  终端输出
    # ──────────────────────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────────────────────
    #  主题切换
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()
        if self._config_mgr:
            self._config_mgr.set('serial.dark_mode', self._dark_mode)
            self._config_mgr.save()

    def _apply_theme(self):
        t = _DARK if self._dark_mode else _LIGHT
        # 更新运行时颜色
        self._rx_color      = t['rx']
        self._tx_color      = t['tx']
        self._sys_color     = t['sys']
        self._sys_err_color = t['sys_err']

        # 端口栏
        self._port_bar.setStyleSheet(
            f"QFrame#port_bar {{ background: {t['bar_bg']}; border-radius: 8px; padding: 4px; }}"
        )
        for lbl in self._port_bar_labels:
            lbl.setStyleSheet(f"color:{t['bar_label']}; font-size:12px;")
        _combo_qss = (f"color:{t['combo_text']}; background:{t['combo_bg']};"
                      f" border:1px solid {t['btn_bdr']}; border-radius:4px; padding:2px 4px;")
        for cb in (self.combo_port, self.combo_baud, self.combo_data,
                   self.combo_parity, self.combo_stop):
            cb.setStyleSheet(_combo_qss)
        self._btn_refresh.setStyleSheet(
            f"color:{t['combo_text']}; background:{t['combo_bg']}; border:none; font-size:14px; padding:2px 4px;"
        )
        self._btn_clear.setStyleSheet(
            f"QPushButton{{color:{t['btn_text']};background:{t['btn_bg']};"
            f"border:1px solid {t['btn_bdr']};border-radius:4px;padding:3px 6px;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};}}"
        )
        self.chk_autoscroll.setStyleSheet(f"color:{t['bar_label']}; font-size:12px;")
        self.chk_highlight.setStyleSheet(f"color:{t['bar_label']}; font-size:12px;")
        self._btn_theme.setText("☀️" if self._dark_mode else "🌙")
        self._btn_theme.setStyleSheet(
            f"color:{t['combo_text']}; background:{t['combo_bg']}; border:none; font-size:14px;"
        )
        self.lbl_status.setStyleSheet(
            f"color:#E74C3C; font-size:12px; font-weight:bold;"
            if not getattr(self, '_connected', False) else
            f"color:#4CAF50; font-size:12px; font-weight:bold;"
        )

        # 终端
        self.terminal.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {t['terminal_bg']};"
            f"  color: {t['terminal_text']};"
            f"  border: 1px solid {t['terminal_bdr']};"
            f"  border-radius: 6px;"
            f"  padding: 6px;"
            f"  selection-background-color: {t['terminal_sel']};"
            f"}}"
        )

        # 输入行
        self.input_line.setStyleSheet(
            f"QLineEdit{{background:{t['input_bg']};color:{t['input_text']};"
            f"border:1px solid {t['input_bdr']};border-radius:6px;padding:6px 10px;}}"
            f"QLineEdit:focus{{border:1px solid {t['input_focus']};}}"
        )
        self.combo_newline.setStyleSheet(
            f"color:{t['nl_text']};background:{t['nl_bg']};"
            f"border:1px solid {t['nl_bdr']};border-radius:6px;padding:2px;"
        )
        self._btn_log.setStyleSheet(
            f"QPushButton{{color:{t['btn_text']};background:{t['btn_bg']};"
            f"border:1px solid {t['btn_bdr']};border-radius:6px;padding:5px 10px;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};border-color:{t['btn_hover_bdr']};}}"
        )

        # 搜索栏样式
        if hasattr(self, 'search_edit'):
            self._search_bar.setStyleSheet(
                f"QFrame#search_frame {{background:{t['bar_bg']};border-radius:6px;padding:2px;}}"
            )
            self.search_edit.setStyleSheet(
                f"QLineEdit{{background:{t['input_bg']};color:{t['input_text']};"
                f"border:1px solid {t['input_bdr']};border-radius:4px;padding:3px 6px;}}"
                f"QLineEdit:focus{{border:1px solid {t['input_focus']};}}"
            )
            _sbtn_qss = (
                f"QPushButton{{color:{t['btn_text']};background:{t['btn_bg']};"
                f"border:1px solid {t['btn_bdr']};border-radius:4px;padding:2px 6px;font-size:11px;}}"
                f"QPushButton:hover{{background:{t['btn_hover']};}}"
            )
            if hasattr(self, '_search_count_lbl'):
                self._search_count_lbl.setStyleSheet(f"color:{t['bar_label']};font-size:11px;")

        # 右侧面板：更新滚动区域及可折叠区块样式
        self._right_scroll.setStyleSheet(
            f"QScrollArea {{ background: {t['scroll_bg']}; border: none; }}"
        )
        _arrow_c = '#58A6FF' if self._dark_mode else '#0969DA'
        # 快捷指令面板内所有按钮（不含 btn_primary/btn_danger，它们通过全局 qss 设置）
        _btn_qss = (
            f"QPushButton{{background:{t['btn_bg']};color:{t['btn_text']};"
            f"border:1px solid {t['btn_bdr']};border-radius:5px;"
            f"padding:5px 8px;font-size:12px;text-align:left;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};"
            f"border-color:{t['btn_hover_bdr']};color:{t['combo_text']};}}"
            f"QPushButton:pressed{{padding-top:6px;}}"
        )
        right_widget = self._right_scroll.widget()
        if right_widget:
            for btn in right_widget.findChildren(QPushButton):
                nm = btn.objectName()
                if nm not in ('btn_primary', 'btn_danger'):
                    btn.setStyleSheet(_btn_qss)
            for lbl in right_widget.findChildren(QLabel):
                lbl.setStyleSheet(
                    f"font-size:11px; color:{t['util_lbl']};"
                )
            # 可折叠区块标题/背景（覆盖上面的通用 label 样式）
            for sec in right_widget.findChildren(_CollapsibleSection):
                sec.apply_colors(
                    hdr_bg=t['grp_bg'], hdr_bdr=t['grp_bdr'],
                    body_bg=t['grp_bg'], body_bdr=t['grp_bdr'],
                    title_c=t['grp_title'], sep_c=t['grp_bdr'],
                    arrow_c=_arrow_c,
                )
        right_widget and right_widget.setStyleSheet(
            f"background: {t['scroll_bg']};"
        )

    def _append_terminal(self, text: str, color: str = '#C9D1D9'):
        ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
        new_line = f"[{ts}] {text}\n"
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        if self._terminal_input_mode and self._terminal_input_anchor >= 0:
            # 内联输入模式：将新数据插入到提示符"上方"，保留已输入内容
            saved_buf = self._terminal_input_buf
            # 删除 '➤ ' + 已输入内容（从 anchor-2 到末尾）
            remove_from = max(0, self._terminal_input_anchor - 2)
            cursor = self.terminal.textCursor()
            cursor.setPosition(remove_from)
            cursor.movePosition(QTextCursor.MoveOperation.End,
                                QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            # 插入新数据
            cursor.insertText(new_line, fmt)
            # 重新插入提示符和已输入内容
            fmt_prompt = QTextCharFormat()
            fmt_prompt.setForeground(QColor('#58A6FF'))
            cursor.insertText('➤ ', fmt_prompt)
            self._terminal_input_anchor = cursor.position()
            if saved_buf:
                fmt_input = QTextCharFormat()
                fmt_input.setForeground(QColor('#79C0FF'))
                cursor.insertText(saved_buf, fmt_input)
            self._terminal_input_buf = saved_buf
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()
        else:
            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(new_line, fmt)
            if self._auto_scroll:
                self.terminal.setTextCursor(cursor)
                self.terminal.ensureCursorVisible()

        # 从接收行中提取路径（Unix 绝对路径）缓入补全库
        if text and not text.startswith('▶') and not text.startswith('  ['):
            for tok in re.split(r'[\s,;]+', text):
                if len(tok) > 2 and tok.startswith('/') and tok not in self._rx_path_cache:
                    self._rx_path_cache.append(tok)
                    if len(self._rx_path_cache) > 400:
                        self._rx_path_cache = self._rx_path_cache[-400:]

    def _sys_msg(self, text: str, error: bool = False):
        """系统消息（提示 / 错误，颜色跟随当前主题）"""
        color = self._sys_err_color if error else self._sys_color
        self._append_terminal(f"  {text}", color=color)
        self._log_lines.append(f"[SYS{'_ERR' if error else ''}] {text}")

    def _on_clear(self):
        self.terminal.clear()
        self._log_lines.clear()

    # ──────────────────────────────────────────────────────────────────────────
    #  串口事件
    # ──────────────────────────────────────────────────────────────────────────
    @pyqtSlot(str)
    def _on_serial_error(self, err: str):
        self._sys_msg(f"串口错误: {err}", error=True)
        self._set_connected(False)
        self._serial = None

    @pyqtSlot()
    def _on_serial_disconnected(self):
        if self._serial:
            self._set_connected(False)
            self._sys_msg("串口连接已断开")

    # ──────────────────────────────────────────────────────────────────────────
    #  角度采集
    # ──────────────────────────────────────────────────────────────────────────
    def _on_send_scan_cmd(self):
        step      = self.combo_step.currentText()
        res       = getattr(self, '_scan_resolution', '0')
        yaw_min   = getattr(self, '_scan_yaw_min',   '-40')
        yaw_max   = getattr(self, '_scan_yaw_max',   '40')
        pitch_min = getattr(self, '_scan_pitch_min', '-40')
        pitch_max = getattr(self, '_scan_pitch_max', '40')
        cmd = (self._scan_cmd_template
               .replace('{resolution}', res)
               .replace('{yaw_min}',    yaw_min)
               .replace('{yaw_max}',    yaw_max)
               .replace('{pitch_min}',  pitch_min)
               .replace('{pitch_max}',  pitch_max)
               .replace('{step}',       step))
        self._send_command(cmd)

    # ──────────────────────────────────────────────────────────────────────────
    #  日志保存
    # ──────────────────────────────────────────────────────────────────────────
    def _on_save_log(self):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"serial_log_{ts}.log"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存日志", default_name,
            "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# 串口日志\n# 导出时间: {ts}\n\n")
                f.write('\n'.join(self._log_lines))
            self._sys_msg(f"日志已保存: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  自定义指令管理
    # ──────────────────────────────────────────────────────────────────────────
    def _load_custom_cmds(self) -> list:
        if os.path.exists(_CUSTOM_CMDS_PATH):
            try:
                with open(_CUSTOM_CMDS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 加载自定义命令
                    if isinstance(data, list) and len(data) > 0:
                        if isinstance(data[0], dict) and 'name' in data[0] and 'cmd' in data[0]:
                            return data
                        # 如果是旧格式，兼容处理
                        elif isinstance(data[0], list):
                            # 旧格式：[[section_name, [commands]], ...]
                            custom_commands = []
                            dynamic_sections = []
                            for item in data:
                                if len(item) == 2:
                                    section_name, commands = item[0], item[1]
                                    if isinstance(commands, list):
                                        # 存储动态板块信息
                                        dynamic_sections.append({
                                            "type": "dynamic_section",
                                            "title": section_name,
                                            "commands": commands
                                        })
                                    else:
                                        # 单个命令
                                        if isinstance(commands, dict) and 'name' in commands and 'cmd' in commands:
                                            custom_commands.append(commands)
                            # 保存动态板块信息到实例变量
                            self._saved_dynamic_sections = dynamic_sections
                            return custom_commands
            except Exception:
                pass
        return list(_DEFAULT_CUSTOM_CMDS)

    def _save_all_data(self):
        """保存所有自定义数据，包括自定义命令和动态板块"""
        os.makedirs(os.path.dirname(_CUSTOM_CMDS_PATH), exist_ok=True)
        # 收集所有动态板块的信息（包括空板块）
        dynamic_sections = []
        for sec in self._quick_sections_list:
            if hasattr(sec, '_dyn_cmds'):  # 只要有 _dyn_cmds 属性就是动态板块
                dynamic_sections.append({
                    "type": "dynamic_section",
                    "title": sec._title_lbl.text(),
                    "commands": sec._dyn_cmds
                })
        
        # 保存自定义命令和动态板块
        save_data = {
            "custom_commands": self._custom_cmds,
            "dynamic_sections": dynamic_sections
        }
        with open(_CUSTOM_CMDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

    def _load_all_data(self):
        """加载自定义命令和动态板块信息（仅加载数据，不构建UI）"""
        self._saved_dynamic_sections = []  # 临时存储动态板块数据
        
        if os.path.exists(_CUSTOM_CMDS_PATH):
            try:
                with open(_CUSTOM_CMDS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # 新格式：包含自定义命令和动态板块
                        self._custom_cmds = data.get("custom_commands", [])
                        self._saved_dynamic_sections = data.get("dynamic_sections", [])
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        # 旧格式：只有自定义命令
                        self._custom_cmds = data
                        self._saved_dynamic_sections = []
            except Exception:
                self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)
                self._saved_dynamic_sections = []
        else:
            self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)
            self._saved_dynamic_sections = []
    
    def _load_saved_dynamic_sections(self):
        """加载保存的动态板块到 UI（在 _init_ui() 完成后调用）"""
        for sec_data in self._saved_dynamic_sections:
            if sec_data.get("type") == "dynamic_section":
                sec = self._build_dynamic_section(sec_data.get("title", "未命名板块"))
                sec._dyn_cmds = sec_data.get("commands", [])
                self._quick_sections_list.append(sec)
                self._sections_layout.addWidget(sec)
                self._refresh_dyn_buttons(sec)

    def _refresh_custom_buttons(self):
        # 清空旧按钮
        while self._custom_btns_layout.count():
            item = self._custom_btns_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        t = _DARK if self._dark_mode else _LIGHT
        _STYLE = (
            f"QPushButton{{background:{t['btn_bg']};color:{t['btn_text']};"
            f"border:1px solid {t['btn_bdr']};border-radius:5px;"
            f"padding:4px 8px;font-size:12px;text-align:left;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};"
            f"border-color:{t['btn_hover_bdr']};color:{t['combo_text']};}}"
        )

        for i, item in enumerate(self._custom_cmds):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)

            btn = QPushButton(f"  {item['name']}")
            btn.setToolTip(f"<code>{item['cmd']}</code>")
            btn.setStyleSheet(_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, c=item['cmd']: self._send_command(c))
            row.addWidget(btn, stretch=1)

            btn_edit = QToolButton()
            btn_edit.setText("✏")
            btn_edit.setToolTip("编辑")
            btn_edit.setStyleSheet(f"color:{t['grp_title']};background:transparent;border:none;font-size:12px;")
            btn_edit.clicked.connect(lambda checked, idx=i: self._on_edit_custom(idx))
            row.addWidget(btn_edit)

            btn_del = QToolButton()
            btn_del.setText("✕")
            btn_del.setToolTip("删除")
            btn_del.setStyleSheet("color:#E74C3C;background:transparent;border:none;font-size:12px;")
            btn_del.clicked.connect(lambda checked, idx=i: self._on_delete_custom(idx))
            row.addWidget(btn_del)

            container = QWidget()
            container.setLayout(row)
            self._custom_btns_layout.addWidget(container)

        if not self._custom_cmds:
            lbl = QLabel("暂无自定义指令，点击「＋ 添加」新建")
            lbl.setStyleSheet(f"color:{t['grp_title']};font-size:11px;padding:4px;")
            self._custom_btns_layout.addWidget(lbl)

    def _on_add_custom(self):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._custom_cmds.append({"name": name, "cmd": cmd})
            self._save_all_data()
            self._refresh_custom_buttons()

    def _on_edit_custom(self, idx: int):
        item = self._custom_cmds[idx]
        dlg = CmdEditDialog(name=item['name'], cmd=item['cmd'], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._custom_cmds[idx] = {"name": name, "cmd": cmd}
            self._save_all_data()
            self._refresh_custom_buttons()

    def _on_add_dyn_cmd(self, sec: '_CollapsibleSection'):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            sec._dyn_cmds.append({"name": name, "cmd": cmd})
            self._save_all_data()  # 保存更改
            self._refresh_dyn_buttons(sec)

    def _on_delete_custom(self, idx: int):
        name = self._custom_cmds[idx]['name']
        reply = QMessageBox.question(
            self, "确认删除", f"删除快捷指令「{name}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._custom_cmds.pop(idx)
            self._save_all_data()
            self._refresh_custom_buttons()

    def _is_tab_passthrough_enabled(self) -> bool:
        return hasattr(self, 'chk_tab_passthrough') and self.chk_tab_passthrough.isChecked()

    def _send_tab_character(self):
        if self._serial and self._serial.is_open:
            try:
                self._serial.write(b'\t')
                self._append_terminal('  [Tab]', color=self._sys_color)
                self._log_lines.append('[CTRL] Tab')
            except Exception as e:
                self._sys_msg(f'发送 Tab 失败: {e}', error=True)
        else:
            self._sys_msg('⚠ 串口未连接，无法发送 Tab', error=True)

    def _queue_workflow(self, name: str, commands: list):
        cmds = [str(cmd).strip() for cmd in commands if str(cmd).strip()]
        if not cmds:
            return
        if not (self._serial and self._serial.is_open):
            QMessageBox.warning(self, '提示', '请先连接串口，再执行组合流程')
            return
        self._workflow_name = name
        self._workflow_queue = cmds
        self._workflow_active = True
        self._workflow_current = ''
        self._workflow_last_rx_ts = 0.0
        self._workflow_sent_ts = 0.0
        self._workflow_cmd_started = False
        self._workflow_timer.start()
        self._sys_msg(f'开始执行组合流程: {name}')
        self._send_next_workflow_command()

    def _send_next_workflow_command(self):
        if not self._workflow_queue:
            self._workflow_timer.stop()
            self._workflow_active = False
            self._sys_msg(f'组合流程完成: {self._workflow_name}')
            return
        self._workflow_current = self._workflow_queue.pop(0)
        self._workflow_sent_ts = time.monotonic()
        self._workflow_last_rx_ts = 0.0
        self._workflow_cmd_started = False
        self._send_command(self._workflow_current)

    def _process_workflow_queue(self):
        if not self._workflow_active:
            return
        now = time.monotonic()
        if self._workflow_cmd_started:
            if self._workflow_last_rx_ts and (now - self._workflow_last_rx_ts) * 1000 >= self._workflow_idle_ms:
                self._send_next_workflow_command()
        elif (now - self._workflow_sent_ts) * 1000 >= self._workflow_silent_ms:
            self._send_next_workflow_command()

    def _build_quick_panel(self) -> QWidget:
        panel = QWidget()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(6)

        icon_lbl = QLabel(
            '💡 板块标题可用 Emoji 图标，常用: '
            '📦🔧🧪📝🔍⚙️✅🔑📡🚀💾🔄'
        )
        icon_lbl.setWordWrap(True)
        self._icon_hint_lbl = icon_lbl
        outer_layout.addWidget(icon_lbl)

        sec_widget = QWidget()
        self._sections_layout = QVBoxLayout(sec_widget)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(10)
        outer_layout.addWidget(sec_widget)

        self._built_in_sections = {}
        built_in_defs = [
            ('firmware', self._build_firmware_group()),
            ('angle_collect', self._build_angle_test_group()),
            ('kst_angle', self._build_kst_angle_group()),
            ('kst_coord', self._build_kst_coord_group()),
            ('system_tools', self._build_sysutil_group()),
            ('custom_commands', self._build_custom_group()),
        ]
        self._quick_sections_list = []
        for persist_id, sec in built_in_defs:
            sec._persist_id = persist_id
            self._built_in_sections[persist_id] = sec
            self._quick_sections_list.append(sec)
            self._sections_layout.addWidget(sec)

        self._refresh_section_controls()

        btn_add = QPushButton('＋ 新建板块')
        btn_add.setObjectName('btn_add_section')
        btn_add.setStyleSheet(
            'QPushButton{color:#58A6FF;background:#1A2233;'
            'border:1px dashed #335577;border-radius:5px;padding:4px 8px;'
            'font-size:12px;}'
            'QPushButton:hover{background:#1E2D44;border-color:#58A6FF;}'
        )
        btn_add.clicked.connect(self._on_add_section)
        self._btn_add_section = btn_add
        outer_layout.addWidget(btn_add)

        outer_layout.addStretch()
        return panel

    def _refresh_section_controls(self):
        n = len(self._quick_sections_list)
        for i, sec in enumerate(self._quick_sections_list):
            delete_cb = None
            if getattr(sec, '_persist_id', '').startswith('dyn:'):
                delete_cb = (lambda checked=False, s=sec: self._delete_dynamic_section(s))
            sec.set_controls(
                up_cb=(lambda checked=False, s=sec: self._move_section(s, -1)) if i > 0 else None,
                down_cb=(lambda checked=False, s=sec: self._move_section(s, +1)) if i < n - 1 else None,
                delete_cb=delete_cb,
                rename_cb=(lambda checked=False, s=sec: self._on_rename_section(s)),
            )

    def _move_section(self, sec: '_CollapsibleSection', direction: int):
        idx = self._quick_sections_list.index(sec)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._quick_sections_list):
            return
        self._quick_sections_list.pop(idx)
        self._quick_sections_list.insert(new_idx, sec)
        self._sections_layout.removeWidget(sec)
        self._sections_layout.insertWidget(new_idx, sec)
        self._refresh_section_controls()
        self._save_all_data()

    def _delete_dynamic_section(self, sec: '_CollapsibleSection'):
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'删除板块「{sec._title_lbl.text()}」？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if sec in self._quick_sections_list:
            self._quick_sections_list.remove(sec)
        self._sections_layout.removeWidget(sec)
        sec.deleteLater()
        self._refresh_section_controls()
        self._save_all_data()

    def _on_rename_section(self, sec: '_CollapsibleSection'):
        new_name, ok = QInputDialog.getText(
            self,
            '重命名板块',
            '输入新名称（可直接输入 Emoji 图标）:',
            text=sec._title_lbl.text(),
        )
        if ok and new_name.strip():
            sec.update_title(new_name.strip())
            self._save_all_data()

    def _build_firmware_group(self) -> _CollapsibleSection:
        sec = _CollapsibleSection('📦 固件升级准备')
        self._firmware_section = sec
        layout = sec.body_layout

        self._fw_hint_text = (
            '💡 <b>固件升级流程说明</b><br>'
            '1. 将 <code>libxgimi.so</code> 拷贝到 U 盘根目录<br>'
            '2. U 盘插入投影仪，确认挂载路径<br>'
            '3. 按顺序执行以下步骤（建议每步确认结果后再点下一步）<br>'
            '4. 升级完成后记得备份原始 so 文件到安全位置'
        )
        self._fw_hint_lbl = QLabel(self._fw_hint_text)
        self._fw_hint_lbl.setWordWrap(True)
        self._fw_hint_lbl.setStyleSheet('font-size:11px;color:#546E7A;')
        layout.addWidget(self._fw_hint_lbl)

        hint_row = QHBoxLayout()
        hint_row.addStretch()
        btn_edit_hint = QToolButton()
        btn_edit_hint.setText('✏')
        btn_edit_hint.setToolTip('编辑说明文字')
        btn_edit_hint.setFixedWidth(22)
        btn_edit_hint.setStyleSheet(
            'QToolButton{color:#8A98A5;background:transparent;border:none;font-size:11px;}'
            'QToolButton:hover{color:#58A6FF;}'
        )
        btn_edit_hint.clicked.connect(self._on_edit_fw_hint)
        hint_row.addWidget(btn_edit_hint)
        layout.addLayout(hint_row)

        fw_exists = os.path.exists(_FIRMWARE_PATH)
        fw_color = '#4CAF50' if fw_exists else '#E74C3C'
        fw_icon = '✅' if fw_exists else '❌'
        fw_path_text = 'assets/firmware/libxgimi_MTK9660_GTV_4K.so' if fw_exists else '未找到，请手动放置'
        fw_label = QLabel(
            f"<span style='color:{fw_color};font-size:11px;'>"
            f'{fw_icon} 内置 so 文件: {fw_path_text}</span>'
        )
        fw_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(fw_label)

        self._fw_step_buttons = []
        self._fw_sec_layout = layout
        self._fw_step_rows = []

        self._fw_steps_container = QWidget()
        self._fw_steps_layout = QVBoxLayout(self._fw_steps_container)
        self._fw_steps_layout.setContentsMargins(0, 0, 0, 0)
        self._fw_steps_layout.setSpacing(4)
        layout.addWidget(self._fw_steps_container)
        self._rebuild_firmware_steps()

        workflow_btn = QPushButton('▶ 执行整个流程')
        workflow_btn.setObjectName('btn_primary')
        workflow_btn.setToolTip('按步骤依次发送指令，并在串口输出稳定后自动进入下一步')
        workflow_btn.clicked.connect(
            lambda: self._queue_workflow('固件升级准备', [step[1] for step in self._upgrade_steps])
        )
        layout.addWidget(workflow_btn)

        btn_add_step = QPushButton('＋ 添加步骤')
        btn_add_step.setStyleSheet(
            'QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;'
            'border-radius:4px;padding:3px 8px;font-size:11px;}'
            'QPushButton:hover{background:#1B3D2A;}'
        )
        btn_add_step.clicked.connect(self._on_add_fw_step)
        layout.addWidget(btn_add_step)
        self._fw_add_step_btn = btn_add_step
        return sec

    def _rebuild_firmware_steps(self):
        if not hasattr(self, '_fw_steps_layout'):
            return
        while self._fw_steps_layout.count():
            item = self._fw_steps_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._fw_step_buttons = []
        self._fw_step_rows = []
        for i, _step in enumerate(self._upgrade_steps):
            self._fw_steps_layout.addWidget(self._build_fw_step_row(i))

    def _on_edit_fw_hint(self):
        new_text, ok = QInputDialog.getMultiLineText(
            self, '编辑固件升级说明', '说明文字:', self._fw_hint_text
        )
        if ok:
            self._fw_hint_text = new_text
            self._fw_hint_lbl.setText(new_text)
            self._save_all_data()

    def _on_edit_fw_step(self, idx: int):
        step = self._upgrade_steps[idx]
        dlg = CmdEditDialog(name=step[0], cmd=step[1], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._upgrade_steps[idx][0] = name
            self._upgrade_steps[idx][1] = cmd
            self._rebuild_firmware_steps()
            self._save_all_data()

    def _on_delete_fw_step(self, idx: int, container: QWidget = None):
        step = self._upgrade_steps[idx]
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'删除步骤「{step[0]}」？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._upgrade_steps.pop(idx)
        self._rebuild_firmware_steps()
        self._save_all_data()

    def _on_add_fw_step(self):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._upgrade_steps.append([name, cmd, ''])
            self._rebuild_firmware_steps()
            self._save_all_data()

    def _build_dynamic_section(self, name: str, persist_id: str = '') -> _CollapsibleSection:
        sec = _CollapsibleSection(name)
        sec._persist_id = persist_id or f'dyn:{int(time.time() * 1000)}'
        layout = sec.body_layout

        sec._hint_text = ''
        sec._hint_label = QLabel('')
        sec._hint_label.setWordWrap(True)
        sec._hint_label.setStyleSheet('font-size:11px;color:#546E7A;')
        sec._hint_label.hide()
        layout.addWidget(sec._hint_label)

        hint_row = QHBoxLayout()
        hint_row.addStretch()
        btn_edit_hint = QToolButton()
        btn_edit_hint.setText('✏')
        btn_edit_hint.setToolTip('编辑说明文字')
        btn_edit_hint.setFixedWidth(22)
        btn_edit_hint.setStyleSheet(
            'QToolButton{color:#8A98A5;background:transparent;border:none;font-size:11px;}'
            'QToolButton:hover{color:#58A6FF;}'
        )
        btn_edit_hint.clicked.connect(lambda checked=False, s=sec: self._on_edit_dyn_hint(s))
        hint_row.addWidget(btn_edit_hint)
        layout.addLayout(hint_row)

        sec._dyn_btns_layout = QVBoxLayout()
        sec._dyn_btns_layout.setContentsMargins(0, 0, 0, 0)
        sec._dyn_btns_layout.setSpacing(3)
        sec._dyn_cmds = []

        btn_add = QPushButton('＋ 添加命令')
        btn_add.setStyleSheet(
            'QPushButton{color:#4CAF50;background:#1C2128;border:1px solid #4CAF50;'
            'border-radius:4px;padding:3px 8px;font-size:11px;}'
            'QPushButton:hover{background:#1B3D2A;}'
        )
        btn_add.clicked.connect(lambda checked=False, s=sec: self._on_add_dyn_cmd(s))
        layout.addWidget(btn_add)
        layout.addLayout(sec._dyn_btns_layout)
        return sec

    def _build_sysutil_group(self) -> _CollapsibleSection:
        sec = _CollapsibleSection('🔧 系统工具')
        layout = sec.body_layout

        lbl = QLabel(
            '💡 <b>系统工具说明</b><br>'
            '1. 常用系统命令统一放在这里<br>'
            '2. 支持修改名称和指令内容，修改后会持久化'
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet('font-size:11px;color:#546E7A;')
        layout.addWidget(lbl)

        sec._dyn_btns_layout = QVBoxLayout()
        sec._dyn_btns_layout.setContentsMargins(0, 0, 0, 0)
        sec._dyn_btns_layout.setSpacing(3)
        sec._dyn_cmds = [{'name': item[0], 'cmd': item[1]} for item in self._sysutil_tools]
        layout.addLayout(sec._dyn_btns_layout)
        self._refresh_dyn_buttons(sec)
        return sec

    def _on_add_section(self):
        name, ok = QInputDialog.getText(
            self,
            '新建板块',
            "板块名称（可直接输入 Emoji，如 '🔑 Root操作'）：",
        )
        if not ok or not name.strip():
            return
        sec = self._build_dynamic_section(name.strip(), persist_id=f'dyn:{int(time.time() * 1000)}')
        self._quick_sections_list.append(sec)
        self._sections_layout.addWidget(sec)
        sec.apply_colors(
            hdr_bg=(_DARK if self._dark_mode else _LIGHT)['grp_bg'],
            hdr_bdr=(_DARK if self._dark_mode else _LIGHT)['grp_bdr'],
            body_bg=(_DARK if self._dark_mode else _LIGHT)['grp_bg'],
            body_bdr=(_DARK if self._dark_mode else _LIGHT)['grp_bdr'],
            title_c=(_DARK if self._dark_mode else _LIGHT)['grp_title'],
            sep_c=(_DARK if self._dark_mode else _LIGHT)['grp_bdr'],
            arrow_c='#58A6FF' if self._dark_mode else '#0969DA',
        )
        self._refresh_section_controls()
        self._save_all_data()

    def _on_edit_dyn_hint(self, sec: '_CollapsibleSection'):
        text, ok = QInputDialog.getMultiLineText(
            self,
            '编辑说明',
            '输入说明文本:',
            getattr(sec, '_hint_text', ''),
        )
        if ok:
            sec._hint_text = text.strip()
            sec._hint_label.setText(sec._hint_text)
            sec._hint_label.setVisible(bool(sec._hint_text))
            self._save_all_data()

    def _on_edit_angle_desc(self):
        new_text, ok = QInputDialog.getMultiLineText(
            self, '编辑角度采集说明', '说明文字:', self._angle_desc_text
        )
        if ok:
            self._angle_desc_text = new_text
            self._angle_desc_lbl.setText(new_text)
            self._save_all_data()

    def _on_edit_scan_cmd(self):
        new_tpl, ok = QInputDialog.getText(
            self,
            '编辑角度采集指令模板',
            '模板（{resolution}/{yaw_min}/{yaw_max}/{pitch_min}/{pitch_max}/{step} 会被替换）：',
            text=self._scan_cmd_template,
        )
        if ok and new_tpl.strip():
            self._scan_cmd_template = new_tpl.strip()
            self._btn_scan.setToolTip(
                '<b>指令模板:</b><br><code>' + self._scan_cmd_template + '</code>'
            )
            self._save_all_data()

    def _on_edit_copy_cmd(self):
        new_cmd, ok = QInputDialog.getText(
            self, '编辑 CSV 拷贝命令', '指令内容：', text=self._copy_csv_cmd
        )
        if ok and new_cmd.strip():
            self._copy_csv_cmd = new_cmd.strip()
            self._btn_copy.setToolTip(self._copy_csv_cmd)
            self._save_all_data()

    def _on_edit_sysutil(self, idx: int):
        tool = self._sysutil_tools[idx]
        dlg = CmdEditDialog(name=tool[0], cmd=tool[1], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._sysutil_tools[idx][0] = name
            self._sysutil_tools[idx][1] = cmd
            self._refresh_dyn_buttons(self._built_in_sections.get('system_tools'))
            self._save_all_data()

    def _collect_builtin_state(self) -> dict:
        sysutil_section = self._built_in_sections.get('system_tools')
        sysutil_cmds = []
        if sysutil_section and hasattr(sysutil_section, '_dyn_cmds'):
            sysutil_cmds = [
                [item.get('name', ''), item.get('cmd', ''), '']
                for item in sysutil_section._dyn_cmds
            ]
            self._sysutil_tools = [list(item) for item in sysutil_cmds]
        return {
            'firmware': {
                'title': self._firmware_section._title_lbl.text(),
                'hint': self._fw_hint_text,
                'commands': self._upgrade_steps,
            },
            'angle_collect': {
                'title': self._built_in_sections['angle_collect']._title_lbl.text(),
                'hint': self._angle_desc_text,
                'scan_cmd_template': self._scan_cmd_template,
                'copy_csv_cmd': self._copy_csv_cmd,
            },
            'kst_angle': {
                'title': self._built_in_sections['kst_angle']._title_lbl.text(),
                'template': getattr(self, '_kst_angle_tpl', ''),
            },
            'kst_coord': {
                'title': self._built_in_sections['kst_coord']._title_lbl.text(),
                'template': getattr(self, '_kst_coord_tpl', ''),
            },
            'system_tools': {
                'title': self._built_in_sections['system_tools']._title_lbl.text(),
                'commands': sysutil_cmds or self._sysutil_tools,
            },
            'custom_commands': {
                'title': self._built_in_sections['custom_commands']._title_lbl.text(),
            },
        }

    def _save_all_data(self):
        os.makedirs(os.path.dirname(_CUSTOM_CMDS_PATH), exist_ok=True)
        dynamic_sections = []
        for sec in self._quick_sections_list:
            if getattr(sec, '_persist_id', '').startswith('dyn:'):
                dynamic_sections.append({
                    'id': sec._persist_id,
                    'title': sec._title_lbl.text(),
                    'hint': getattr(sec, '_hint_text', ''),
                    'commands': list(getattr(sec, '_dyn_cmds', [])),
                })
        save_data = {
            'version': 2,
            'theme': {'dark_mode': self._dark_mode},
            'custom_commands': self._custom_cmds,
            'fixed_sections': self._collect_builtin_state(),
            'dynamic_sections': dynamic_sections,
            'section_order': [getattr(sec, '_persist_id', '') for sec in self._quick_sections_list],
        }
        with open(_CUSTOM_CMDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

    def _load_all_data(self):
        self._serial_state = {
            'version': 2,
            'theme': {'dark_mode': False},
            'custom_commands': list(_DEFAULT_CUSTOM_CMDS),
            'fixed_sections': {},
            'dynamic_sections': [],
            'section_order': [],
        }
        self._saved_dynamic_sections = []
        self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)
        if os.path.exists(_CUSTOM_CMDS_PATH):
            try:
                with open(_CUSTOM_CMDS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._serial_state.update(data)
                    self._custom_cmds = data.get('custom_commands', list(_DEFAULT_CUSTOM_CMDS))
                    self._saved_dynamic_sections = data.get('dynamic_sections', [])
                elif isinstance(data, list):
                    self._custom_cmds = data
                    self._serial_state['custom_commands'] = data
            except Exception:
                self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)
        if self._config_mgr:
            self._serial_state.setdefault('theme', {})
            self._serial_state['theme'].setdefault(
                'dark_mode',
                bool(self._config_mgr.get('serial.dark_mode', False)),
            )

    def _apply_builtin_state(self, fixed_sections: dict):
        firmware = fixed_sections.get('firmware', {})
        if firmware:
            self._firmware_section.update_title(firmware.get('title', self._firmware_section._title_lbl.text()))
            self._fw_hint_text = firmware.get('hint', self._fw_hint_text)
            self._fw_hint_lbl.setText(self._fw_hint_text)
            commands = firmware.get('commands')
            if isinstance(commands, list) and commands:
                self._upgrade_steps = [list(item) for item in commands]
                self._rebuild_firmware_steps()

        angle_collect = fixed_sections.get('angle_collect', {})
        if angle_collect:
            self._built_in_sections['angle_collect'].update_title(
                angle_collect.get('title', self._built_in_sections['angle_collect']._title_lbl.text())
            )
            self._angle_desc_text = angle_collect.get('hint', self._angle_desc_text)
            self._angle_desc_lbl.setText(self._angle_desc_text)
            self._scan_cmd_template = angle_collect.get('scan_cmd_template', self._scan_cmd_template)
            self._copy_csv_cmd = angle_collect.get('copy_csv_cmd', self._copy_csv_cmd)
            self._btn_scan.setToolTip(
                '<b>执行角度坐标批量采集</b><br>'
                f'指令模板: <code>{self._scan_cmd_template}</code><br>'
                '占位符会自动替换为当前 UI 参数值'
            )
            self._btn_copy.setToolTip(self._copy_csv_cmd)

        kst_angle = fixed_sections.get('kst_angle', {})
        if kst_angle:
            self._built_in_sections['kst_angle'].update_title(
                kst_angle.get('title', self._built_in_sections['kst_angle']._title_lbl.text())
            )
            self._kst_angle_tpl = kst_angle.get('template', getattr(self, '_kst_angle_tpl', ''))

        kst_coord = fixed_sections.get('kst_coord', {})
        if kst_coord:
            self._built_in_sections['kst_coord'].update_title(
                kst_coord.get('title', self._built_in_sections['kst_coord']._title_lbl.text())
            )
            self._kst_coord_tpl = kst_coord.get('template', getattr(self, '_kst_coord_tpl', ''))

        system_tools = fixed_sections.get('system_tools', {})
        if system_tools:
            self._built_in_sections['system_tools'].update_title(
                system_tools.get('title', self._built_in_sections['system_tools']._title_lbl.text())
            )
            commands = system_tools.get('commands')
            if isinstance(commands, list) and commands:
                self._sysutil_tools = [list(item) for item in commands]
                sec = self._built_in_sections['system_tools']
                sec._dyn_cmds = [{'name': item[0], 'cmd': item[1]} for item in self._sysutil_tools]
                self._refresh_dyn_buttons(sec)

        custom_group = fixed_sections.get('custom_commands', {})
        if custom_group:
            self._built_in_sections['custom_commands'].update_title(
                custom_group.get('title', self._built_in_sections['custom_commands']._title_lbl.text())
            )

    def _load_saved_dynamic_sections(self):
        self._apply_builtin_state(self._serial_state.get('fixed_sections', {}))
        for sec_data in self._saved_dynamic_sections:
            sec = self._build_dynamic_section(
                sec_data.get('title', '未命名板块'),
                persist_id=sec_data.get('id', f'dyn:{int(time.time() * 1000)}'),
            )
            sec._hint_text = sec_data.get('hint', '')
            sec._hint_label.setText(sec._hint_text)
            sec._hint_label.setVisible(bool(sec._hint_text))
            sec._dyn_cmds = sec_data.get('commands', [])
            self._quick_sections_list.append(sec)
            self._sections_layout.addWidget(sec)
            self._refresh_dyn_buttons(sec)

        order = self._serial_state.get('section_order', [])
        if order:
            order_map = {getattr(sec, '_persist_id', ''): sec for sec in self._quick_sections_list}
            ordered = [order_map[item] for item in order if item in order_map]
            for sec in self._quick_sections_list:
                if sec not in ordered:
                    ordered.append(sec)
            self._quick_sections_list = ordered
            for sec in ordered:
                self._sections_layout.removeWidget(sec)
            for sec in ordered:
                self._sections_layout.addWidget(sec)
                sec.show()

        self._refresh_section_controls()
        self._refresh_custom_buttons()
