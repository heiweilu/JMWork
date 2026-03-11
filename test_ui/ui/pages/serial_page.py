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
import json
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QComboBox, QTextEdit, QLineEdit, QGroupBox, QScrollArea, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QSizePolicy,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFrame, QTabWidget, QToolButton,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
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
#  串口页面主体
# ══════════════════════════════════════════════════════════════════════════════
class SerialPage(QWidget):
    """串口交互界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._reader_thread = None
        self._rx_buffer = bytearray()
        self._auto_scroll = True
        self._log_lines = []            # 纯文本日志缓存
        self._custom_cmds = self._load_custom_cmds()
        # 主题状态
        self._dark_mode = True
        self._rx_color    = _DARK['rx']
        self._tx_color    = _DARK['tx']
        self._sys_color   = _DARK['sys']
        self._sys_err_color = _DARK['sys_err']
        self._port_bar_labels = []   # 端口栏标签引用（主题更新用）
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
        term_layout.addWidget(self._build_terminal(), stretch=1)
        term_layout.addWidget(self._build_input_bar())

        # 右：快捷指令区
        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setMinimumWidth(300)
        self._right_scroll.setMaximumWidth(380)
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
        return self.terminal

    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入指令，按 Enter 发送...")
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.returnPressed.connect(self._on_send)
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

    def _build_quick_panel(self) -> QWidget:
        """构建右侧快捷指令面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        # ── 区域1：固件升级 ──
        layout.addWidget(self._build_firmware_group())

        # ── 区域2：角度采集测试 ──
        layout.addWidget(self._build_angle_test_group())

        # ── 区域3：系统工具 ──
        layout.addWidget(self._build_sysutil_group())

        # ── 区域4：自定义指令 ──
        layout.addWidget(self._build_custom_group())

        layout.addStretch()
        return panel

    def _build_firmware_group(self) -> QGroupBox:
        """固件升级流程区"""
        grp = QGroupBox("📦 固件升级流程")
        layout = QVBoxLayout(grp)
        layout.setSpacing(6)

        # 说明
        hint = QLabel(
            "<html><body style='font-size:11px;color:#546E7A;'>"
            "升级前准备：将 <b>libxgimi.so</b> 放入 U 盘根目录，"
            "U 盘插入投影仪，连接串口后依次点击以下按钮："
            "</body></html>"
        )
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(hint)

        # firmware 文件路径提示
        fw_exists = os.path.exists(_FIRMWARE_PATH)
        fw_color = '#4CAF50' if fw_exists else '#E74C3C'
        fw_icon = '✅' if fw_exists else '❌'
        fw_path_text = 'assets/firmware/libxgimi.so' if fw_exists else '未找到，请手动放置'
        fw_label = QLabel(
            f"<span style='color:{fw_color};font-size:11px;'>"
            f"{fw_icon} 内置 so 文件: {fw_path_text}</span>"
        )
        fw_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(fw_label)

        # 按钮网格（每行2个）
        for i, (btn_text, cmd, tip) in enumerate(_UPGRADE_STEPS):
            row = QHBoxLayout()
            btn = QPushButton(btn_text)
            btn.setToolTip(f"<b>指令:</b> <code>{cmd}</code><br><br>{tip}")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            # 特殊颜色：reboot 用红色
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

            btn.clicked.connect(lambda checked, c=cmd: self._send_command(c))
            row.addWidget(btn)
            layout.addLayout(row)

        return grp

    def _build_angle_test_group(self) -> QGroupBox:
        """角度采集测试区"""
        grp = QGroupBox("🧪 角度采集测试")
        layout = QVBoxLayout(grp)
        layout.setSpacing(7)

        # 说明
        desc = QLabel(
            "<html><body style='font-size:11px;color:#546E7A;'>"
            "遍历 Yaw × Pitch [-40°,40°] 二维网格，调用 <code>batchGetDisplayPointByAngle</code> "
            "将每个角度对应的四角坐标写入 CSV（位于设备 /data/vendor/）。"
            "<br><br>"
            "完成后需将 CSV 文件拷贝回 U 盘取走分析。"
            "</body></html>"
        )
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(desc)

        # 步进选择
        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("角度步进:"))
        self.combo_step = QComboBox()
        self.combo_step.addItems(_STEP_OPTIONS)
        self.combo_step.setCurrentText("0.1")
        self.combo_step.setToolTip(
            "步进值越小，采集点越密，耗时越长。\n"
            "0.1° → 约 161×161=25921 个点（约 30 分钟）\n"
            "0.5° → 约 33×33=1089 个点（较快）\n"
            "1°   → 约 17×17=289 个点（快速验证）"
        )
        self.combo_step.setFixedWidth(70)
        step_row.addWidget(self.combo_step)
        step_row.addStretch()
        layout.addLayout(step_row)

        # 发送采集指令
        btn_scan = QPushButton("▶ 发送角度采集指令")
        btn_scan.setObjectName("btn_primary")
        btn_scan.setToolTip(
            "<b>执行角度坐标批量采集</b><br>"
            "指令格式:<br>"
            "<code>gmpfUnit externDisplay kst_dev batchGetDisplayPointByAngle</code><br>"
            "<code>&quot;yaw;pitch;0;-40;40;-40;40;{step};/data/vendor&quot;</code><br><br>"
            "参数说明:<br>"
            "• axis1=yaw, axis2=pitch（二维扫描轴）<br>"
            "• fixed=0（Roll 固定为 0°）<br>"
            "• [-40,40] × [-40,40]（扫描范围，度）<br>"
            "• step（步进间隔，由上方选择框决定）<br>"
            "• /data/vendor（CSV 输出目录）"
        )
        btn_scan.clicked.connect(self._on_send_scan_cmd)
        layout.addWidget(btn_scan)

        # 拷贝数据到 U 盘
        btn_copy = QPushButton("📋 拷贝 CSV 到 U 盘")
        btn_copy.setToolTip(
            "将设备内 /data/vendor/ak_scan_*.csv 拷贝到 U 盘:\n"
            "cp /data/vendor/ak_scan_*.csv /mnt/media_rw/0182-0265/"
        )
        btn_copy.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #1D3557,stop:1 #152744);color:#90CAF9;border:1px solid #1565C0;"
            "border-radius:5px;padding:5px 8px;}"
            "QPushButton:hover{background:#1A4480;border-color:#42A5F5;color:#fff;}"
        )
        btn_copy.clicked.connect(
            lambda: self._send_command("cp /data/vendor/ak_scan_*.csv /mnt/media_rw/0182-0265/")
        )
        layout.addWidget(btn_copy)

        return grp

    def _build_sysutil_group(self) -> QGroupBox:
        """系统工具区"""
        grp = QGroupBox("🔧 系统工具")
        layout = QVBoxLayout(grp)
        layout.setSpacing(5)

        tools = [
            ("📜 监听 GM 调试日志",
             "logcat | grep GM_DISP_DBG",
             "实时监听 GM_DISP_DBG 标签的 Logcat 日志（Ctrl+C 停止）"),
            ("🔒 关闭 AVB 验证",
             "avb init 0;avb set-devicestate 0;avb set-verity disable;save;reset",
             "关闭 Android Verified Boot，允许修改系统分区\n执行后设备会自动重启"),
            ("⏱ 调整休眠时间(24h)",
             "settings put system screen_off_timeout 86400000",
             "将屏幕休眠时间设为 24 小时（86400000 毫秒），测试时防止屏幕熄灭"),
            ("📂 查看 U 盘挂载",
             "ls /mnt/media_rw/",
             "列出 U 盘挂载目录，确认 U 盘 UUID"),
            ("📁 查看 vendor lib",
             "ls /vendor/lib/ | grep xgimi",
             "查看 /vendor/lib 中的 xgimi 相关动态库"),
            ("🔍 查看设备信息",
             "getprop ro.product.model && getprop ro.build.version.release",
             "打印设备型号和 Android 版本"),
        ]

        _TOOL_STYLE = (
            "QPushButton{background:#1C2128;color:#C9D1D9;border:1px solid #30363D;"
            "border-radius:5px;padding:5px 8px;font-size:12px;text-align:left;}"
            "QPushButton:hover{background:#21262D;border-color:#58A6FF;color:#fff;}"
            "QPushButton:pressed{background:#161B22;}"
        )

        for name, cmd, tip in tools:
            btn = QPushButton(f"  {name}")
            btn.setToolTip(f"<b>指令:</b><br><code>{cmd}</code><br><br>{tip}")
            btn.setStyleSheet(_TOOL_STYLE)
            btn.clicked.connect(lambda checked, c=cmd: self._send_command(c))
            layout.addWidget(btn)

        return grp

    def _build_custom_group(self) -> QGroupBox:
        """自定义快捷指令区"""
        grp = QGroupBox("📝 自定义快捷指令")
        self._custom_group = grp
        layout = QVBoxLayout(grp)
        layout.setSpacing(5)

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
        return grp

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
                    self._append_terminal(line, color=self._rx_color)
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
                self._append_terminal(line, color=self._rx_color)
                self._log_lines.append(f"[RX] {line}")

    def _on_send(self):
        cmd = self.input_line.text().strip()
        if not cmd:
            return
        self._send_command(cmd)
        self.input_line.clear()

    def _send_command(self, cmd: str):
        nl_map = {"\\r\\n": b'\r\n', "\\n": b'\n', "\\r": b'\r', "无": b''}
        nl = nl_map.get(self.combo_newline.currentText(), b'\r\n')

        if self._serial and self._serial.is_open:
            try:
                self._serial.write(cmd.encode('utf-8') + nl)
                self._append_terminal(f"▶ {cmd}", color=self._tx_color)
                self._log_lines.append(f"[TX] {cmd}")
            except Exception as e:
                self._sys_msg(f"发送失败: {e}", error=True)
        else:
            self._sys_msg("⚠ 串口未连接，无法发送指令", error=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  终端输出
    # ──────────────────────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────────────────────
    #  主题切换
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

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

        # 右侧面板：更新滚动区域及其 QGroupBox 样式
        self._right_scroll.setStyleSheet(
            f"QScrollArea {{ background: {t['scroll_bg']}; border: none; }}"
            f"QGroupBox {{"
            f"  background: {t['grp_bg']};"
            f"  border: 1px solid {t['grp_bdr']};"
            f"  border-radius: 6px;"
            f"  margin-top: 8px;"
            f"  font-weight: bold; color: {t['grp_title']};"
            f"}}"
            f"QGroupBox::title {{"
            f"  subcontrol-origin: margin; left: 8px; padding: 0 4px;"
            f"  color: {t['grp_title']};"
            f"}}"
        )
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
        right_widget and right_widget.setStyleSheet(
            f"background: {t['scroll_bg']};"
        )

    def _append_terminal(self, text: str, color: str = '#C9D1D9'):
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
        cursor.insertText(f"[{ts}] {text}\n", fmt)
        if self._auto_scroll:
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()

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
        step = self.combo_step.currentText()
        cmd = (
            f'gmpfUnit externDisplay kst_dev batchGetDisplayPointByAngle '
            f'"yaw;pitch;0;-40;40;-40;40;{step};/data/vendor"'
        )
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
                    return json.load(f)
            except Exception:
                pass
        return list(_DEFAULT_CUSTOM_CMDS)

    def _save_custom_cmds(self):
        os.makedirs(os.path.dirname(_CUSTOM_CMDS_PATH), exist_ok=True)
        with open(_CUSTOM_CMDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._custom_cmds, f, ensure_ascii=False, indent=2)

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
            self._save_custom_cmds()
            self._refresh_custom_buttons()

    def _on_edit_custom(self, idx: int):
        item = self._custom_cmds[idx]
        dlg = CmdEditDialog(name=item['name'], cmd=item['cmd'], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd = dlg.get_values()
            self._custom_cmds[idx] = {"name": name, "cmd": cmd}
            self._save_custom_cmds()
            self._refresh_custom_buttons()

    def _on_delete_custom(self, idx: int):
        name = self._custom_cmds[idx]['name']
        reply = QMessageBox.question(
            self, "确认删除", f"删除快捷指令「{name}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._custom_cmds.pop(idx)
            self._save_custom_cmds()
            self._refresh_custom_buttons()

    # ──────────────────────────────────────────────────────────────────────────
    #  页面关闭时断开串口
    # ──────────────────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)

    def hideEvent(self, event):
        """切换到其他页面时停止但不断开"""
        super().hideEvent(event)

    def showEvent(self, event):
        """切换回本页面时刷新串口列表"""
        self._refresh_ports()
        super().showEvent(event)
