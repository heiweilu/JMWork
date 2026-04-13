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
    QComboBox, QTextEdit, QPlainTextEdit, QLineEdit, QGroupBox, QScrollArea, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QSizePolicy,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFrame, QTabWidget, QToolButton,
    QInputDialog, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QColor, QTextCursor, QFont, QTextCharFormat, QPainter

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
    'util_lbl':      '#8EA8B8',
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
#  可拖拽排序列表
# ══════════════════════════════════════════════════════════════════════════════
class _ReorderableList(QListWidget):
    """支持拖拽排序并在 drop 后发出信号的 QListWidget"""
    orderChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


# ══════════════════════════════════════════════════════════════════════════════
#  自定义指令编辑对话框
# ══════════════════════════════════════════════════════════════════════════════
class CmdEditDialog(QDialog):
    def __init__(self, name="", cmd="", desc="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑快捷指令")
        self.resize(860, 380)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.edit_name = QLineEdit(name)
        self.edit_name.setPlaceholderText("显示名称，如「查看进程」")
        form.addRow("名称:", self.edit_name)

        self.edit_desc = QTextEdit()
        self.edit_desc.setPlainText(desc)
        self.edit_desc.setAcceptRichText(False)
        self.edit_desc.setPlaceholderText("可选，简要说明指令用途（支持多行）")
        self.edit_desc.setMinimumHeight(60)
        self.edit_desc.setMaximumHeight(100)
        form.addRow("注释:", self.edit_desc)

        self.edit_cmd = QTextEdit()
        self.edit_cmd.setPlainText(cmd)
        self.edit_cmd.setAcceptRichText(False)
        self.edit_cmd.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.edit_cmd.setFont(QFont("Consolas", 10))
        self.edit_cmd.setMinimumHeight(150)
        self.edit_cmd.setPlaceholderText("这里编辑的是单条快捷指令。命令很长也不要手工拆行，直接保持一条完整命令即可。")
        form.addRow("指令:", self.edit_cmd)
        layout.addLayout(form)

        hint = QLabel("说明：这是单条快捷指令编辑器。长命令会横向显示，不需要为了视觉换行而拆成多条。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_accept(self):
        if not self.edit_name.text().strip() or not self.edit_cmd.toPlainText().strip():
            QMessageBox.warning(self, "提示", "名称和指令不能为空")
            return
        self.accept()

    def get_values(self):
        return (self.edit_name.text().strip(),
                self.edit_cmd.toPlainText().strip(),
                self.edit_desc.toPlainText().strip())


# ══════════════════════════════════════════════════════════════════════════════
#  可见光标输入框（在光标处绘制亮色宽条，方便在长命令中定位光标）
# ══════════════════════════════════════════════════════════════════════════════
class _VisibleCursorLineEdit(QLineEdit):
    """在光标位置叠加绘制一条 4px 宽彩色条。
    深色主题使用亮蓝 #4fc3f7，浅色主题使用深蓝 #1565C0，两者均与对应背景形成高对比。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dark: bool = True

    def set_theme(self, is_dark: bool):
        """by _apply_theme（主题切换时）调用，号主题上光标颜色并触发重绘。"""
        self._is_dark = is_dark
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        super().paintEvent(event)
        if not self.hasFocus():
            return
        cr = self.cursorRect()
        color = QColor('#4fc3f7') if self._is_dark else QColor('#1565C0')
        p = QPainter(self)
        p.fillRect(cr.x() - 1, 1, 4, self.height() - 2, color)
        p.end()


class _TerminalTextEdit(QTextEdit):
    """终端显示区：不设 ReadOnly 以显示原生可见、可移动光标（4px 宽闪烁）。
    - 光标在末尾：外层 eventFilter 路由，触发内联输入模式（发往串口）。
    - 光标不在末尾：可打印字符在当前位置直接插入（文本编辑模式），方向键移动光标。
    - insertFromMimeData 阻止右键粘贴直接修改终端。
    """
    _NAV_KEYS = frozenset({
        Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
        Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
    })

    def __init__(self, parent=None):
        super().__init__(parent)
        # 在 viewport 上安装自己的事件过滤，用于 Ctrl+滚轮缩放
        self.viewport().installEventFilter(self)

    def keyPressEvent(self, event):
        """方向键/翻页键放行；可打印字符/退格/删除在当前位置操作；
        → 键不允许进入幽灵段落；Enter 在非末尾时回滚到终端末尾（不插入空行）。
        """
        if event.key() == Qt.Key.Key_Right:
            # 防止光标经 → 键进入幽灵段落（视觉上像"跳到下一行"）
            cur_pos = self.textCursor().position()
            doc_end = self.document().characterCount() - 1
            if cur_pos >= doc_end - 1:
                event.accept()   # 已到达最后可见字符，不再往右
                return
            super().keyPressEvent(event)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # 文本编辑模式下 Enter 不插入空行，而是滚动回末尾（回到终端命令行）
            cur_pos = self.textCursor().position()
            doc_end = self.document().characterCount() - 1
            if cur_pos < doc_end:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                event.accept()
                return
            # 在末尾：Enter 由 eventFilter 的 _terminal_input_mode 分支处理，
            # 不应到达此处；保险起见 accept 掉避免插入
            event.accept()
            return
        if event.key() in self._NAV_KEYS:
            super().keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            super().keyPressEvent(event)
        elif event.text() and event.text().isprintable():
            # 兜底：若首个字符未被外层 eventFilter 捕获，避免写入历史行。
            # 在非直通模式下，统一改为移到底部并进入内联输入。
            cur_pos = self.textCursor().position()
            doc_end = self.document().characterCount() - 1
            if cur_pos < doc_end:
                owner = self.parentWidget()
                try:
                    if (owner is not None
                            and hasattr(owner, '_is_tab_passthrough_enabled')
                            and hasattr(owner, '_terminal_enter_input_mode')
                            and hasattr(owner, '_move_terminal_cursor_to_visible_end')
                            and not owner._is_tab_passthrough_enabled()):
                        owner._move_terminal_cursor_to_visible_end()
                        owner._terminal_enter_input_mode(event.text())
                        event.accept()
                        return
                except Exception:
                    pass
            # 其余情况按 QTextEdit 默认行为处理
            super().keyPressEvent(event)
        else:
            event.accept()   # 消化事件，不插入文字

    def wheelEvent(self, event):
        """Ctrl+滚轮由 viewport eventFilter 统一处理，此处仅传递普通滚动。"""
        super().wheelEvent(event)

    def eventFilter(self, obj, event):
        """viewport 事件过滤：拦截 Ctrl+滚轮缩放（必须 return True 阻止 QAbstractScrollArea 消费）。"""
        from PyQt6.QtCore import QEvent
        if obj is self.viewport() and event.type() == QEvent.Type.Wheel:
            ctrl = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            if not ctrl:
                ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if ctrl:
                delta = event.angleDelta().y()
                font = self.font()
                cur_size = font.pointSize()
                if cur_size < 1:
                    cur_size = getattr(self, '_zoom_pt', 10)  # fallback
                new_size = max(6, min(60, cur_size + (2 if delta > 0 else -2)))
                self._zoom_pt = new_size  # 存储供插入时引用
                font.setPointSize(new_size)
                self.setFont(font)
                self.document().setDefaultFont(font)  # 显式更新文档默认字体
                # 用全新空格式（只设字号）avoid 颜色污染
                from PyQt6.QtGui import QTextCursor as _TC
                cursor = self.textCursor()
                cursor.select(_TC.SelectionType.Document)
                _size_fmt = QTextCharFormat()
                _size_fmt.setFontPointSize(new_size)
                cursor.mergeCharFormat(_size_fmt)
                self.update()
                event.accept()
                return True  # 必须 True：阻止 QAbstractScrollArea 的内置 filter 消费事件
        return super().eventFilter(obj, event)

    def insertFromMimeData(self, source):
        """禁止右键粘贴或拖拽直接修改终端内容（Ctrl+V 由 eventFilter 转发至串口）。"""
        pass


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
        self._collapsed = False
        self._arrow.setText("▼")
        self._sep.setVisible(True)
        self._body.setMinimumHeight(0)
        self._body.setVisible(True)
        self._body.setMaximumHeight(16_777_215)

    def _do_collapse(self):
        self._collapsed = True
        self._arrow.setText("▶")
        self._body.setVisible(False)
        self._sep.setVisible(False)
        self._body.setMaximumHeight(0)

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
        # VT100 行缓冲（直发模式下追踪当前行内容和光标位置）
        self._vt_line: list[str] = []   # 当前行字符列表
        self._vt_cursor: int = 0        # 当前行光标位置
        self._syntax_scheme = 'Linux'   # 语法高亮方案: Linux / CMD
        # 初始化数据加载相关属性
        self._custom_cmds = list(_DEFAULT_CUSTOM_CMDS)  # 自定义快捷指令
        self._saved_dynamic_sections = []  # 保存的动态板块数据
        # 初始化时加载所有数据
        self._load_all_data()
        # 主题状态
        self._dark_mode = bool(self._serial_state.get('theme', {}).get('dark_mode', True))
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
        self._quick_panel_loaded = False
        self._quick_filter_buttons = {}
        self._quick_filter = 'common'
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
        # ── 逐行批量发送状态 ──
        self._batch_lines: list = []        # 待发命令列表
        self._batch_index: int = 0          # 当前行索引
        self._batch_repeat_total: int = 1   # 总重复次数
        self._batch_repeat_done: int = 0    # 已完成重复次数
        self._batch_timer = QTimer(self)
        self._batch_timer.timeout.connect(self._on_batch_send_tick)
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
        self._main_splitter = splitter

        # 左：终端区
        terminal_widget = QWidget()
        term_layout = QVBoxLayout(terminal_widget)
        term_layout.setContentsMargins(0, 0, 0, 0)
        term_layout.setSpacing(4)
        # 搜索栏（Ctrl+F 切换显示）
        self._search_bar = self._build_search_bar()
        term_layout.addWidget(self._search_bar)
        term_layout.addWidget(self._build_terminal(), stretch=1)
        self._input_bar = self._build_input_bar()
        self._input_bar.setVisible(False)  # 终端内联模式，底部输入栏不需要
        term_layout.addWidget(self._input_bar)

        # 右：快捷指令区
        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setMinimumWidth(460)
        self._right_scroll.setMaximumWidth(680)
        self._right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._quick_panel_placeholder = QWidget()
        self._right_scroll.setWidget(self._quick_panel_placeholder)

        splitter.addWidget(terminal_widget)
        splitter.addWidget(self._right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        self._set_right_panel_visible(False)
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

        # RX 高亮开关
        self.chk_highlight = QCheckBox("🎨 高亮")
        self.chk_highlight.setChecked(True)
        self.chk_highlight.setToolTip("根据关键字对接收内容高亮显示")
        self.chk_highlight.toggled.connect(lambda v: setattr(self, '_highlight_rx', v))
        layout.addWidget(self.chk_highlight)

        # 语法方案选择
        self.combo_syntax = QComboBox()
        self.combo_syntax.addItems(['Linux', 'CMD'])
        self.combo_syntax.setToolTip("终端语法高亮方案")
        self.combo_syntax.setFixedWidth(70)
        self.combo_syntax.currentTextChanged.connect(self._on_syntax_changed)
        layout.addWidget(self.combo_syntax)

        self.chk_tab_passthrough = QCheckBox("Tab直发")
        self.chk_tab_passthrough.setChecked(True)
        self.chk_tab_passthrough.setVisible(False)  # 默认启用直发，不需要显示
        self.chk_tab_passthrough.setToolTip("启用后，所有按键直接发送到设备（含退格/方向键/Enter），不再触发本地补全")
        self.chk_tab_passthrough.toggled.connect(self._on_tab_passthrough_toggled)
        layout.addWidget(self.chk_tab_passthrough)

        self.btn_toggle_quick_panel = QToolButton()
        self.btn_toggle_quick_panel.setText("快捷面板")
        self.btn_toggle_quick_panel.setCheckable(True)
        self.btn_toggle_quick_panel.setChecked(False)
        self.btn_toggle_quick_panel.setToolTip("显示或收起右侧快捷面板")
        self.btn_toggle_quick_panel.toggled.connect(self._set_right_panel_visible)
        layout.addWidget(self.btn_toggle_quick_panel)

        # 连接/断开
        self.btn_connect = QPushButton("  连接  ")
        self.btn_connect.setObjectName("btn_primary")
        self.btn_connect.clicked.connect(self._on_toggle_connect)
        layout.addWidget(self.btn_connect)

        # 状态指示
        self.lbl_status = QLabel("● 未连接")
        layout.addWidget(self.lbl_status)

        return bar

    def _set_right_panel_visible(self, visible: bool):
        if visible:
            self._ensure_quick_panel_loaded()
        self._right_scroll.setVisible(bool(visible))
        if hasattr(self, 'btn_toggle_quick_panel'):
            self.btn_toggle_quick_panel.blockSignals(True)
            self.btn_toggle_quick_panel.setChecked(bool(visible))
            self.btn_toggle_quick_panel.blockSignals(False)
            self.btn_toggle_quick_panel.setText("收起面板" if visible else "快捷面板")
        if hasattr(self, '_main_splitter'):
            if visible:
                self._main_splitter.setSizes([760, 580])
            else:
                self._main_splitter.setSizes([1340, 0])

    def _ensure_quick_panel_loaded(self):
        if self._quick_panel_loaded:
            return
        right_content = self._build_quick_panel()
        self._right_scroll.setWidget(right_content)
        self._quick_panel_loaded = True
        self._load_saved_dynamic_sections()
        self._apply_theme()

    def _build_terminal(self) -> QTextEdit:
        self.terminal = _TerminalTextEdit()
        self.terminal.setFont(QFont("Microsoft YaHei", 10))
        self.terminal.setMinimumHeight(300)
        self.terminal.installEventFilter(self)   # 键盘输入路由 + Ctrl+F
        self.terminal.viewport().installEventFilter(self)   # Ctrl+滚轮缩放
        # 设置光标样式，让用户知道可以在此直接输入
        self.terminal.setCursorWidth(4)
        self.terminal.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # 用于内嵌输入模式的内部状态
        self._terminal_input_mode = False   # 是否处于终端内输入模式
        self._terminal_input_anchor = -1    # 输入区起始位置
        self._terminal_input_buf  = ''      # 已输入内容
        self._nav_paused = False            # 是否暂停自动滚动
        self._freeze_view_on_rx = False     # Tab 补全期间冻结视图
        # 光标高亮 & 搜索高亮分离管理
        self._search_extra_sels: list = []
        self._cursor_extra_sel:  list = []
        self.terminal.cursorPositionChanged.connect(self._update_cursor_highlight)
        return self.terminal

    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.input_line = _VisibleCursorLineEdit()
        self.input_line.setPlaceholderText("输入指令，按 Enter 发送 | ↑↓ 历史 | Tab 补全...")
        self.input_line.setFont(QFont("Microsoft YaHei", 10))
        self.input_line.returnPressed.connect(self._on_send)
        self.input_line.installEventFilter(self)   # Tab/上下键拦截
        layout.addWidget(self.input_line, stretch=1)

        # 默认非直通模式：方向键在终端内移动光标，Enter 在输入框内发送
        self._passthrough_mode: bool = False
        # 保留按钮对象供 _apply_theme hasattr 检查，但不添加到布局（无直通切换需求）
        self._btn_passthrough = QPushButton("✏")
        self._btn_passthrough.setCheckable(True)
        self._btn_passthrough.setChecked(False)
        self._btn_passthrough.setFixedWidth(34)
        self._btn_passthrough.clicked.connect(self._on_toggle_passthrough)

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

    # ── 光标/搜索高亮管理 ──────────────────────────────────────────────────
    def _refresh_extra_sels(self):
        """合并搜索高亮与光标块高亮后写入终端。"""
        self.terminal.setExtraSelections(
            self._search_extra_sels + self._cursor_extra_sel
        )

    def _update_cursor_highlight(self):
        """光标位置变化时维护自动滚动状态（蓝色方块已移除，仅依赖原生 4px 光标）。"""
        if getattr(self, '_freeze_view_on_rx', False):
            self._nav_paused = True
            return
        # 兼容“可见末尾”光标（位于最后一个可见字符，尾随 '\n' 之前）
        cur_pos = self.terminal.textCursor().position()
        doc_end = self.terminal.document().characterCount() - 1
        at_end = cur_pos >= max(0, doc_end - 1)
        self._maybe_pause_autoscroll(at_end=at_end)

    def _maybe_pause_autoscroll(self, at_end: bool):
        """光标离开文档末尾时暂停自动滚动，回到末尾时恢复。
        - 光标在内联输入缓冲区内（cursor >= anchor）→ 保持输入模式，不暂停
        - 鼠标点击导致光标移走 → 仅暂停自动滚动，不取消输入（Bug3修复）
        - 键盘导航到缓冲区之前 → 静默取消输入模式并暂停
        """
        if not at_end:
            if getattr(self, '_terminal_input_mode', False):
                anchor = getattr(self, '_terminal_input_anchor', -1)
                if anchor >= 0 and self.terminal.textCursor().position() >= anchor:
                    # 光标在输入缓冲区内（← 在蓝字中导航）→ 保持输入模式
                    self._nav_paused = False
                    return
                # Bug3修复：鼠标点击时不取消内联输入，仅暂停自动滚动
                if QApplication.mouseButtons() != Qt.MouseButton.NoButton:
                    self._nav_paused = True
                    return
                # 键盘导航到缓冲区起点之前 → 静默取消（不触发嵌套信号）
                self._terminal_cancel_input_silent()
        self._nav_paused = not at_end

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
        self.search_edit.setFont(QFont("Microsoft YaHei", 10))
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
        # 清除搜索高亮（保留光标高亮）
        self._search_extra_sels = []
        self._refresh_extra_sels()
        self._search_count_lbl.setText("")
        self.input_line.setFocus()

    def _on_search_text_changed(self, text: str):
        self._search_count_lbl.setText("")
        self._search_extra_sels = []
        self._refresh_extra_sels()
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
        self._search_extra_sels = selections
        self._refresh_extra_sels()
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

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(6)
        for text, category in [
            ("常用", "common"),
            ("KST", "kst"),
            ("工具", "tools"),
            ("自定义", "custom"),
            ("全部", "all"),
        ]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, c=category: self._apply_quick_filter(c))
            filter_row.addWidget(btn)
            self._quick_filter_buttons[category] = btn
        outer_layout.addLayout(filter_row)

        # ── 板块容器（用单独 layout 便于重排）──
        sec_widget = QWidget()
        self._sections_layout = QVBoxLayout(sec_widget)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(10)
        outer_layout.addWidget(sec_widget)

        # ── 构建各板块 ──
        built_in_secs = [
            (self._build_batch_send_group(), "common"),
            (self._build_firmware_group(), "common"),
            (self._build_angle_test_group(), "common"),
            (self._build_kst_angle_group(), "kst"),
            (self._build_kst_coord_group(), "kst"),
            (self._build_sysutil_group(), "tools"),
            (self._build_custom_group(), "custom"),
        ]
        self._quick_sections_list = [sec for sec, _category in built_in_secs]
        for sec, category in built_in_secs:
            sec._quick_category = category
            self._sections_layout.addWidget(sec)

        self._refresh_section_controls()
        self._apply_quick_filter(self._quick_filter)

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
        self._apply_quick_filter(self._quick_filter)

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

    def _apply_quick_filter(self, category: str):
        self._quick_filter = category
        for key, btn in self._quick_filter_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(key == category)
            btn.blockSignals(False)
        for sec in self._quick_sections_list:
            sec_category = getattr(sec, '_quick_category', 'custom')
            visible = category == 'all' or sec_category == category
            sec.setVisible(visible)
        if self._btn_add_section is not None:
            self._btn_add_section.setVisible(category in {'custom', 'all'})

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
            if not hasattr(sec, '_dyn_cmds'):
                sec._dyn_cmds = []
            sec._dyn_cmds.append({"name": name, "cmd": cmd})
            self._save_all_data()  # 保存更改
            self._refresh_dyn_buttons(sec)

    def _refresh_dyn_buttons(self, sec: '_CollapsibleSection'):
        t = _DARK if self._dark_mode else _LIGHT
        if not hasattr(sec, '_dyn_btns_layout'):
            return
        if not hasattr(sec, '_dyn_cmds'):
            sec._dyn_cmds = []
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
        
        for i, item in enumerate(sec._dyn_cmds):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(3)

            # 超长名称截断显示，tooltip 保留完整内容
            _MAX_NAME = 20
            display_name = (item['name'] if len(item['name']) <= _MAX_NAME
                            else item['name'][:_MAX_NAME - 1] + '…')
            btn = QPushButton(f"  {display_name}")
            btn.setToolTip(f"<b>{item['name']}</b><br><code>{item['cmd']}</code>")
            btn.setStyleSheet(_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, c=item['cmd']: self._send_command(c))
            row.addWidget(btn, stretch=1)
            
            btn_edit = QToolButton()
            btn_edit.setText("✏")
            btn_edit.setToolTip("编辑")
            btn_edit.setStyleSheet(f"color:{t['grp_title']};background:transparent;border:none;font-size:12px;")
            btn_edit.clicked.connect(lambda checked=False, s=sec, c_idx=i: self._on_edit_dyn_cmd(s, c_idx))
            row.addWidget(btn_edit)
            
            btn_del = QToolButton()
            btn_del.setText("✕")
            btn_del.setStyleSheet("color:#E74C3C;background:transparent;border:none;")
            btn_del.clicked.connect(lambda checked=False, s=sec, c_idx=i: self._on_delete_dyn_cmd(s, c_idx))
            row.addWidget(btn_del)
            
            container = QWidget()
            container.setLayout(row)
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            sec._dyn_btns_layout.addWidget(container)

        sec._dyn_btns_layout.addStretch()

    def _on_edit_dyn_cmd(self, sec: '_CollapsibleSection', cmd_idx: int):
        """编辑动态板块中的命令"""
        dyn_cmds = getattr(sec, '_dyn_cmds', None)
        if dyn_cmds is None:
            return
        if not (0 <= cmd_idx < len(dyn_cmds)):
            return

        item = dyn_cmds[cmd_idx]
        dlg = CmdEditDialog(name=item['name'], cmd=item['cmd'],
                            desc=item.get('desc', ''), parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd, desc = dlg.get_values()
            dyn_cmds[cmd_idx] = {"name": name, "cmd": cmd, "desc": desc}
            self._save_all_data()
            self._refresh_dyn_buttons(sec)

    def _on_delete_dyn_cmd(self, sec: '_CollapsibleSection', cmd_idx: int):
        dyn_cmds = getattr(sec, '_dyn_cmds', None)
        if dyn_cmds is None or not (0 <= cmd_idx < len(dyn_cmds)):
            return
        dyn_cmds.pop(cmd_idx)
        self._refresh_dyn_buttons(sec)
        self._save_all_data()

    def _build_batch_send_group(self) -> '_CollapsibleSection':
        """逐行批量发送面板（WindTerm 风格）"""
        sec = _CollapsibleSection("📋 逐行批量发送", collapsed=False)
        layout = sec.body_layout

        # ── 命令文本区 ──
        hint = QLabel("每行一条命令，按顺序逐行发送到串口")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._batch_edit = QPlainTextEdit()
        self._batch_edit.setFont(QFont("Microsoft YaHei", 10))
        self._batch_edit.setPlaceholderText(
            "每行输入一条命令，例如：\n"
            "su\n"
            "remount\n"
            "sync"
        )
        self._batch_edit.setMinimumHeight(120)
        self._batch_edit.setMaximumHeight(200)
        layout.addWidget(self._batch_edit)

        # ── 控制行：间隔 + 重复 + 进度 ──
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        ctrl_row.addWidget(QLabel("间隔(s):"))
        self._batch_interval_spin = QDoubleSpinBox()
        self._batch_interval_spin.setRange(0.05, 60.0)
        self._batch_interval_spin.setSingleStep(0.5)
        self._batch_interval_spin.setValue(1.0)
        self._batch_interval_spin.setDecimals(2)
        self._batch_interval_spin.setFixedWidth(70)
        ctrl_row.addWidget(self._batch_interval_spin)

        ctrl_row.addWidget(QLabel("重复:"))
        self._batch_repeat_spin = QSpinBox()
        self._batch_repeat_spin.setRange(1, 999)
        self._batch_repeat_spin.setValue(1)
        self._batch_repeat_spin.setFixedWidth(55)
        ctrl_row.addWidget(self._batch_repeat_spin)

        ctrl_row.addStretch()

        self._lbl_batch_progress = QLabel("就绪")
        self._lbl_batch_progress.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ctrl_row.addWidget(self._lbl_batch_progress)

        layout.addLayout(ctrl_row)

        # ── 发送 / 停止 按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._btn_batch_start = QPushButton("▶ 逐行发送")
        self._btn_batch_start.setObjectName("btn_primary")
        self._btn_batch_start.clicked.connect(self._start_batch_send)
        btn_row.addWidget(self._btn_batch_start, stretch=1)

        self._btn_batch_stop = QPushButton("■ 停止")
        self._btn_batch_stop.setObjectName("btn_danger")
        self._btn_batch_stop.setEnabled(False)
        self._btn_batch_stop.clicked.connect(self._stop_batch_send)
        btn_row.addWidget(self._btn_batch_stop)

        layout.addLayout(btn_row)

        self._batch_send_sec = sec
        return sec

    def _start_batch_send(self):
        """开始逐行批量发送"""
        if not (self._serial and self._serial.is_open):
            self._sys_msg("⚠ 串口未连接，无法发送", error=True)
            return
        text = self._batch_edit.toPlainText()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            self._sys_msg("⚠ 批量发送：命令列表为空", error=True)
            return
        self._batch_lines = lines
        self._batch_index = 0
        self._batch_repeat_total = max(1, self._batch_repeat_spin.value())
        self._batch_repeat_done = 0
        interval_ms = max(50, int(self._batch_interval_spin.value() * 1000))
        self._batch_timer.setInterval(interval_ms)
        self._btn_batch_start.setEnabled(False)
        self._btn_batch_stop.setEnabled(True)
        self._lbl_batch_progress.setText("发送中…")
        # 立即发送第一条，再启动定时器
        self._on_batch_send_tick()

    def _stop_batch_send(self):
        """停止逐行批量发送"""
        self._batch_timer.stop()
        self._batch_lines = []
        self._batch_index = 0
        self._btn_batch_start.setEnabled(True)
        self._btn_batch_stop.setEnabled(False)
        self._lbl_batch_progress.setText("已停止")

    def _on_batch_send_tick(self):
        """定时器回调：发送当前行，推进索引"""
        if not (self._serial and self._serial.is_open):
            self._stop_batch_send()
            self._sys_msg("⚠ 批量发送中串口断开，已停止", error=True)
            return
        if not self._batch_lines:
            self._stop_batch_send()
            return
        total = len(self._batch_lines)
        if self._batch_index >= total:
            # 当前遍结束
            self._batch_repeat_done += 1
            if self._batch_repeat_done >= self._batch_repeat_total:
                # 全部完成
                self._batch_timer.stop()
                self._batch_lines = []
                self._batch_index = 0
                self._btn_batch_start.setEnabled(True)
                self._btn_batch_stop.setEnabled(False)
                self._lbl_batch_progress.setText(
                    f"✅ 完成 {self._batch_repeat_done}/{self._batch_repeat_total} 遍"
                )
                return
            # 重新开始下一遍
            self._batch_index = 0

        cmd = self._batch_lines[self._batch_index]
        # 高亮当前行：在批量输入框中选中对应行
        try:
            cur = self._batch_edit.textCursor()
            doc = self._batch_edit.document()
            block = doc.findBlockByLineNumber(self._batch_index)
            cur.setPosition(block.position())
            cur.movePosition(
                QTextCursor.MoveOperation.EndOfBlock,
                QTextCursor.MoveMode.KeepAnchor
            )
            self._batch_edit.setTextCursor(cur)
        except Exception:
            pass

        self._send_command(cmd)
        total_r = self._batch_repeat_total
        done_r = self._batch_repeat_done
        idx = self._batch_index + 1
        self._lbl_batch_progress.setText(
            f"第{idx}/{total}行 | 第{done_r + 1}/{total_r}遍"
        )
        self._batch_index += 1
        # 如果还有下一条，启动定时器；否则在定时器回调中处理
        if self._batch_index < total or (self._batch_repeat_done + 1) < total_r:
            if not self._batch_timer.isActive():
                self._batch_timer.start()
        else:
            # 最后一条已发，下一 tick 完成收尾
            if not self._batch_timer.isActive():
                self._batch_timer.start()

    def _build_firmware_group(self) -> _CollapsibleSection:
        """固件升级准备区"""
        sec = _CollapsibleSection("📦 固件升级准备", collapsed=True)
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
        sec = _CollapsibleSection("🔧 角度测试", collapsed=True)
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
        sec = _CollapsibleSection("⚙️ 系统工具", collapsed=True)
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
        sec = _CollapsibleSection("📝 自定义命令", collapsed=True)
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
        sec._quick_category = 'custom'
        self._quick_sections_list.append(sec)
        self._sections_layout.addWidget(sec)
        self._refresh_section_controls()
        self._apply_quick_filter(self._quick_filter)
        self._apply_theme()   # 应用当前主题样式到新板块
        self._save_all_data()  # 保存更改

    def _build_dynamic_section(self, name: str) -> _CollapsibleSection:
        """动态板块"""
        sec = _CollapsibleSection(name, collapsed=True)
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
        sec = _CollapsibleSection("🧪 角度采集测试", collapsed=True)
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
        sec = _CollapsibleSection("📝 自定义快捷指令", collapsed=True)
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
            # 连接后重置输入/滚动状态，避免首次输入受历史状态影响
            self._terminal_input_mode = False
            self._terminal_input_anchor = -1
            self._terminal_input_buf = ''
            self._nav_paused = False
            self._freeze_view_on_rx = False
            self._passthrough_mode = False
            if hasattr(self, '_btn_passthrough'):
                self._btn_passthrough.setChecked(False)
                self._btn_passthrough.setText("✏")
            if hasattr(self, 'input_line'):
                self.input_line.setPlaceholderText("编辑模式：方向键移动光标，Enter 发送命令")
            if hasattr(self, 'terminal'):
                self.terminal.setFocus()
                QTimer.singleShot(0, lambda: self._terminal_enter_input_mode(''))
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
        """拆分 buffer 中完整的行并输出"""
        tab_mode = self._is_tab_passthrough_enabled()

        # ── 直发模式：交给 VT100 行处理器 ─────────────────────────────
        if tab_mode:
            data = bytes(self._rx_buffer)
            self._rx_buffer.clear()
            if data:
                self._process_vt_data(data)
            return

        # ── 普通模式：按行拆分 ─────────────────────────────────────────
        normalized = self._rx_buffer.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        if b'\n' in normalized:
            lines = normalized.split(b'\n')
            for line_bytes in lines[:-1]:
                line = line_bytes.decode('utf-8', errors='replace')
                if line:
                    clean = self._strip_rx_control(line)
                    if clean:
                        self._append_terminal(clean, color=self._detect_rx_color(clean))
                    self._log_lines.append(f"[RX] {line}")
            remainder = lines[-1]
            self._rx_buffer = bytearray(remainder)
        else:
            self._rx_buffer = bytearray(normalized)

    def _flush_rx_buffer(self):
        """定期将 buffer 中没有换行字符的内容刷入终端（如 shell 提示符）"""
        if self._rx_buffer:
            if self._is_tab_passthrough_enabled():
                # VT 模式下交给 VT 处理器
                data = bytes(self._rx_buffer)
                self._rx_buffer.clear()
                self._process_vt_data(data)
            else:
                line = self._rx_buffer.decode('utf-8', errors='replace')
                self._rx_buffer.clear()
                if line.strip():
                    clean = self._strip_rx_control(line)
                    if clean.strip():
                        self._append_terminal(clean, color=self._detect_rx_color(clean))
                    self._log_lines.append(f"[RX] {line}")

    def _on_send(self):
        if self._is_tab_passthrough_enabled():
            return  # 直发模式下键盘已实时直发，不走普通发送路径
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
                # 非空命令：显示发送记录；空回车：静默发送，不污染终端
                if cmd:
                    self._append_terminal(f"▶ {cmd}", color=self._tx_color)
                self._log_lines.append(f"[TX] {cmd}" if cmd else "[TX] ↵")
                # clear/cls：延迟清空本地终端（等设备处理后效果更自然）
                if cmd.strip().lower() in ('clear', 'cls'):
                    QTimer.singleShot(120, self._on_clear)
            except Exception as e:
                self._sys_msg(f"发送失败: {e}", error=True)
        else:
            self._sys_msg("⚠ 串口未连接，无法发送指令", error=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  终端内联输入（WindTerm 风格）
    # ──────────────────────────────────────────────────────────────────────────
    def _terminal_enter_input_mode(self, first_char: str = ''):
        """进入内联输入模式：在最后一个非空行末尾输入，不换行、不变色。"""
        self._terminal_input_mode = True
        self._nav_paused = False
        self._freeze_view_on_rx = False
        self._terminal_input_buf = first_char
        cur = self.terminal.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        doc_text = self.terminal.toPlainText()
        if not doc_text.endswith('\n'):
            # 末尾无换行，先补一个确保有 \n 分隔
            fmt_nl = QTextCharFormat()
            fmt_nl.setForeground(QColor('#C9D1D9'))
            cur.insertText('\n', fmt_nl)
            doc_text = self.terminal.toPlainText()
        # 找到最后一个非空行末尾位置：
        # 先去掉尾部所有 \n，再去掉该行末尾多余空白，避免 Tab 补全的空格对齐
        stripped = doc_text.rstrip('\n')
        # 逐行找最后一行，去掉行尾空格
        last_newline = stripped.rfind('\n')
        last_line = stripped[last_newline + 1:] if last_newline >= 0 else stripped
        anchor_pos = last_newline + 1 + len(last_line.rstrip())
        cur.setPosition(anchor_pos)
        self._terminal_input_anchor = anchor_pos
        # 插入第一个字符（加粗+白色高亮，与历史输出区分）
        if first_char:
            fmt_input = QTextCharFormat()
            fmt_input.setForeground(QColor(self._inline_input_color))
            fmt_input.setFontWeight(700)
            _pt = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
            if _pt > 0:
                fmt_input.setFontPointSize(_pt)
            cur.insertText(first_char, fmt_input)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()

    def _terminal_commit_input(self):
        """提交内联输入：移除已输字符（保留末尾 \\n），清除状态。"""
        if self._terminal_input_anchor >= 0:
            buf_len = len(self._terminal_input_buf)
            cur = self.terminal.textCursor()
            cur.setPosition(self._terminal_input_anchor)
            cur.movePosition(QTextCursor.MoveOperation.Right,
                             QTextCursor.MoveMode.KeepAnchor, buf_len)
            cur.removeSelectedText()
            self.terminal.setTextCursor(cur)
        self._terminal_input_mode = False
        self._terminal_input_anchor = -1
        self._terminal_input_buf = ''

    def _move_terminal_cursor_to_visible_end(self):
        """将终端光标放在最后一个可见字符处，避免停在尾部空段落闪烁。"""
        cur = self.terminal.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        txt = self.terminal.toPlainText()
        if txt.endswith('\n') and cur.position() > 0:
            cur.movePosition(QTextCursor.MoveOperation.PreviousCharacter)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()

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
        # 删除已输字符（从 anchor 精确选中 old_len 个），追加 new_text（加粗白色）
        cur = self.terminal.textCursor()
        cur.setPosition(self._terminal_input_anchor)
        cur.movePosition(QTextCursor.MoveOperation.Right,
                         QTextCursor.MoveMode.KeepAnchor, old_len)
        cur.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._inline_input_color))
        fmt.setFontWeight(700)
        _ptc = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
        if _ptc > 0:
            fmt.setFontPointSize(_ptc)
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
        cur.setPosition(self._terminal_input_anchor)
        cur.movePosition(QTextCursor.MoveOperation.Right,
                         QTextCursor.MoveMode.KeepAnchor, old_len)
        cur.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._inline_input_color))
        fmt.setFontWeight(700)
        _pth = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
        if _pth > 0:
            fmt.setFontPointSize(_pth)
        cur.insertText(new_text, fmt)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()
        self._terminal_input_buf = new_text

    def _terminal_cancel_input(self):
        """取消内联输入：删除已输字符（保留末尾 \\n）。"""
        if self._terminal_input_anchor >= 0:
            cur = self.terminal.textCursor()
            cur.setPosition(self._terminal_input_anchor)
            cur.movePosition(QTextCursor.MoveOperation.End,
                             QTextCursor.MoveMode.KeepAnchor)
            cur.movePosition(QTextCursor.MoveOperation.PreviousCharacter,
                             QTextCursor.MoveMode.KeepAnchor)
            cur.removeSelectedText()
            self.terminal.setTextCursor(cur)
        self._terminal_input_mode = False
        self._terminal_input_anchor = -1
        self._terminal_input_buf = ''

    def _terminal_cancel_input_silent(self):
        """静默取消内联输入：删除已输字符（保留末尾 \\n），不调用 setTextCursor。"""
        if self._terminal_input_anchor >= 0:
            buf_len = len(self._terminal_input_buf)
            cur = QTextCursor(self.terminal.document())
            cur.setPosition(self._terminal_input_anchor)
            cur.movePosition(QTextCursor.MoveOperation.Right,
                             QTextCursor.MoveMode.KeepAnchor, buf_len)
            cur.removeSelectedText()
        self._terminal_input_mode = False
        self._terminal_input_anchor = -1
        self._terminal_input_buf = ''

    # ──────────────────────────────────────────────────────────────────────────
    #  输入框事件拦截（Tab补全 / 上下键历史）
    # ──────────────────────────────────────────────────────────────────────────
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        # ── Ctrl+滚轮缩放：返回 False 让事件自然流经到 _TerminalTextEdit.wheelEvent ──
        if (event.type() == QEvent.Type.Wheel
                and hasattr(self, 'terminal')
                and obj is self.terminal.viewport()):
            return False  # 不消费，递归到 wheelEvent
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            # 去掉 NumLock/GroupSwitch 等干扰标志，确保 Ctrl 组合键在任何键盘
            # 状态下都能正确匹配
            _STRIP = (Qt.KeyboardModifier.KeypadModifier
                      | Qt.KeyboardModifier.GroupSwitchModifier)
            modifiers = event.modifiers() & ~_STRIP

            # ── 搜索栏 Esc 关闭 ──────────────────────────────────────────
            if hasattr(self, 'search_edit') and obj is self.search_edit:
                if key == Qt.Key.Key_Escape:
                    self._close_search()
                    return True
            _is_terminal_target = (
                obj is self.terminal
                or (hasattr(self, 'terminal') and obj is self.terminal.viewport())
            )
            if _is_terminal_target:
                # Ctrl+F：切换搜索栏
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_F):
                    self._toggle_search()
                    return True

                # Ctrl+C：有选中 → 复制到剪贴板；内联输入中 → 取消；否则发送控制字符
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_C):
                    if self.terminal.textCursor().hasSelection():
                        self.terminal.copy()     # 显式复制，避免 ReadOnly 吞掉快捷键
                        return True
                    if self._terminal_input_mode:
                        self._terminal_cancel_input()
                    # 发送 Ctrl+C 控制字符
                    if self._serial and self._serial.is_open:
                        try:
                            self._serial.write(b'\x03')
                            # 重置 VT 行缓冲（Ctrl+C 会中断当前行）
                            self._vt_line = []
                            self._vt_cursor = 0
                        except Exception:
                            pass
                    return True

                # Ctrl+V：粘贴
                # 统一行为：粘贴到本地内联输入，按 Enter 再发送
                if (modifiers == Qt.KeyboardModifier.ControlModifier
                        and key == Qt.Key.Key_V):
                    clipboard = QApplication.clipboard()
                    text = clipboard.text() if clipboard else ''
                    if not text:
                        return True
                    # 过滤换行符（只保留可打印内容，换行由 Enter 按键发送）
                    text = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                    if not self._terminal_input_mode:
                        self._terminal_enter_input_mode('')
                    # 追加到当前 buf 并显示在终端
                    offset = len(self._terminal_input_buf)
                    self._terminal_input_buf += text
                    insert_pos = self._terminal_input_anchor + offset
                    cur = self.terminal.textCursor()
                    cur.setPosition(insert_pos)
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(self._inline_input_color))
                    fmt.setFontWeight(700)
                    _pt4 = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
                    if _pt4 > 0:
                        fmt.setFontPointSize(_pt4)
                    cur.insertText(text, fmt)
                    self.terminal.setTextCursor(cur)
                    self.terminal.ensureCursorVisible()
                    return True

                # Ctrl+字母 → 直接发送控制字符（与原 input_line 中的逻辑一致）
                if modifiers == Qt.KeyboardModifier.ControlModifier:
                    _CTRL_MAP = {
                        Qt.Key.Key_Z:          ('\x1a', 'Ctrl+Z  (挂起)'),
                        Qt.Key.Key_D:          ('\x04', 'Ctrl+D  (EOF)'),
                        Qt.Key.Key_L:          ('\x0c', 'Ctrl+L  (清屏)'),
                        Qt.Key.Key_Backslash:  ('\x1c', 'Ctrl+\\  (SIGQUIT)'),
                        Qt.Key.Key_X:          ('\x18', 'Ctrl+X'),
                        Qt.Key.Key_W:          ('\x17', 'Ctrl+W  (删除前一个词)'),
                        Qt.Key.Key_A:          ('\x01', 'Ctrl+A  (行首)'),
                        Qt.Key.Key_E:          ('\x05', 'Ctrl+E  (行尾)'),
                        Qt.Key.Key_K:          ('\x0b', 'Ctrl+K  (剔除到行尾)'),
                        Qt.Key.Key_U:          ('\x15', 'Ctrl+U  (剔除到行首)'),
                        Qt.Key.Key_R:          ('\x12', 'Ctrl+R  (反向搜索)'),
                        Qt.Key.Key_P:          ('\x10', 'Ctrl+P  (上一条)'),
                        Qt.Key.Key_N:          ('\x0e', 'Ctrl+N  (下一条)'),
                    }
                    if key in _CTRL_MAP:
                        char, label = _CTRL_MAP[key]
                        if self._serial and self._serial.is_open:
                            try:
                                self._serial.write(char.encode('latin-1'))
                                self._log_lines.append(f'[CTRL] {label}')
                            except Exception as e:
                                self._sys_msg(f'发送失败: {e}', error=True)
                        else:
                            self._sys_msg('⚠ 串口未连接', error=True)
                        return True

                if self._is_tab_passthrough_enabled():
                    arrow_map = {
                        Qt.Key.Key_Up: b'\x1b[A',
                        Qt.Key.Key_Down: b'\x1b[B',
                        Qt.Key.Key_Left: b'\x1b[D',
                        Qt.Key.Key_Right: b'\x1b[C',
                        Qt.Key.Key_Home: b'\x1b[H',
                        Qt.Key.Key_End: b'\x1b[F',
                    }
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        self._send_live_newline()
                        return True
                    if key == Qt.Key.Key_Backspace:
                        self._send_live_backspace()
                        return True
                    if key == Qt.Key.Key_Tab:
                        self._send_tab_character()
                        return True
                    if key == Qt.Key.Key_Delete:
                        self._send_live_escape_sequence(b'\x1b[3~')
                        return True
                    if key == Qt.Key.Key_Escape:
                        self._send_live_escape_sequence(b'\x1b')
                        return True
                    if key == Qt.Key.Key_Space:
                        self._send_live_text(' ')
                        return True
                    if key in arrow_map:
                        self._send_live_escape_sequence(arrow_map[key])
                        return True
                    char = event.text()
                    if char and (char.isprintable() or char == ' ') and modifiers in (
                            Qt.KeyboardModifier.NoModifier,
                            Qt.KeyboardModifier.ShiftModifier):
                        self._send_live_text(char)
                        return True

                # ── 内联输入模式：已有活跃输入 ──────────────────────────────
                if self._terminal_input_mode:
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        cmd = self._terminal_input_buf
                        self._terminal_commit_input()
                        # commit 后重置 nav_paused，确保 _append_terminal 能移动光标到末尾
                        self._nav_paused = False
                        # 只有 buf 非空才发送（空 buf 直接退出内联模式，不发送空回车）
                        if cmd:
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
                            cur_pos = self.terminal.textCursor().position()
                            offset = cur_pos - self._terminal_input_anchor
                            # 限定在 [1, len(buf)] 范围：删光标前一个字符
                            if 1 <= offset <= len(self._terminal_input_buf):
                                self._terminal_input_buf = (
                                    self._terminal_input_buf[:offset - 1]
                                    + self._terminal_input_buf[offset:])
                                cur = self.terminal.textCursor()
                                cur.setPosition(cur_pos)
                                cur.deletePreviousChar()
                                self.terminal.setTextCursor(cur)
                        return True

                    # ← 方向键：防止光标越过 anchor（否则触发 cancel）
                    if key == Qt.Key.Key_Left:
                        cur_pos = self.terminal.textCursor().position()
                        if cur_pos <= self._terminal_input_anchor:
                            return True  # 已到达最左端，不再左移
                        return False  # 放行，让 QTextEdit 处理光标移动

                    # → 方向键：防止光标越过输入范围末尾
                    if key == Qt.Key.Key_Right:
                        cur_pos = self.terminal.textCursor().position()
                        max_pos = self._terminal_input_anchor + len(self._terminal_input_buf)
                        if cur_pos >= max_pos:
                            return True  # 已到达最右端
                        return False

                    # Home：跳到输入起始
                    if key == Qt.Key.Key_Home:
                        cur = self.terminal.textCursor()
                        cur.setPosition(self._terminal_input_anchor)
                        self.terminal.setTextCursor(cur)
                        return True

                    # End：跳到输入末尾
                    if key == Qt.Key.Key_End:
                        end_pos = self._terminal_input_anchor + len(self._terminal_input_buf)
                        cur = self.terminal.textCursor()
                        cur.setPosition(end_pos)
                        self.terminal.setTextCursor(cur)
                        return True

                    if key == Qt.Key.Key_Up:
                        self._terminal_history_cycle(-1)
                        return True

                    if key == Qt.Key.Key_Down:
                        self._terminal_history_cycle(1)
                        return True

                    if key == Qt.Key.Key_Tab:
                        # 内联输入模式 Tab：将已输内容 + \t 一起发给设备，
                        # 由设备回显补全结果，退出本地 inline input 状态
                        if self._serial and self._serial.is_open:
                            buf = self._terminal_input_buf
                            self._terminal_commit_input()   # 清除终端里已输字符
                            # Tab 补全输出时保持当前位置，不自动跳到后续新行
                            self._nav_paused = True
                            self._freeze_view_on_rx = True
                            try:
                                payload = buf.encode('utf-8') + b'\t'
                                self._serial.write(payload)
                                self._log_lines.append(f'[TX] {buf}\\t')
                            except Exception as e:
                                self._sys_msg(f'发送 Tab 失败: {e}', error=True)
                        return True

                    if key == Qt.Key.Key_Escape:
                        self._terminal_cancel_input()
                        return True

                    char = event.text()
                    if char and (char.isprintable() or char == ' ') and modifiers in (
                            Qt.KeyboardModifier.NoModifier,
                            Qt.KeyboardModifier.ShiftModifier):
                        # 光标位置插入（支持在已输内容中间插入）
                        cur_pos = self.terminal.textCursor().position()
                        offset = cur_pos - self._terminal_input_anchor
                        offset = max(0, min(offset, len(self._terminal_input_buf)))
                        self._terminal_input_buf = (
                            self._terminal_input_buf[:offset]
                            + char
                            + self._terminal_input_buf[offset:])
                        insert_pos = self._terminal_input_anchor + offset
                        cur = self.terminal.textCursor()
                        cur.setPosition(insert_pos)
                        fmt = QTextCharFormat()
                        fmt.setForeground(QColor(self._inline_input_color))  # 加粗高亮
                        fmt.setFontWeight(700)
                        _pt3 = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
                        if _pt3 > 0:
                            fmt.setFontPointSize(_pt3)
                        cur.insertText(char, fmt)
                        self.terminal.setTextCursor(cur)
                        self.terminal.ensureCursorVisible()
                        return True

                    # 其他键（翻页、方向键）保留给终端滚动
                    return False

                # ── 非输入模式按 Enter → 移到末尾并静默发空回车（刷新设备提示符）──
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    # 无论光标位置，先移末尾再发，避免"第一次回车无反应"问题
                    self._freeze_view_on_rx = False
                    self._move_terminal_cursor_to_visible_end()
                    self._send_command('')
                    self._move_terminal_cursor_to_visible_end()
                    return True

                # ── 非直通模式：终端内打字进入内联输入（CMD 风格） ──────────
                char = event.text()
                if char and char.isprintable() and modifiers in (
                        Qt.KeyboardModifier.NoModifier,
                        Qt.KeyboardModifier.ShiftModifier):
                    cur_pos = self.terminal.textCursor().position()
                    doc_end = self.terminal.document().characterCount() - 1
                    if cur_pos >= doc_end:
                        self._terminal_enter_input_mode(char)
                        return True
                    # Bug2修复：光标不在末尾（鼠标点击中间后打字）→ 强制移到末尾再输入
                    cur = self.terminal.textCursor()
                    cur.movePosition(QTextCursor.MoveOperation.End)
                    self.terminal.setTextCursor(cur)
                    self._terminal_enter_input_mode(char)
                    return True

                # 方向键/翻页键等放行（QTextEdit 原生移动光标 → ExtraSelection 跟随）
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
                                self._log_lines.append(f'[CTRL] {label}')
                            except Exception as e:
                                self._sys_msg(f'发送失败: {e}', error=True)
                        else:
                            self._sys_msg('⚠ 串口未连接', error=True)
                        return True

                if self._is_tab_passthrough_enabled():
                    arrow_map = {
                        Qt.Key.Key_Up: b'\x1b[A',
                        Qt.Key.Key_Down: b'\x1b[B',
                        Qt.Key.Key_Left: b'\x1b[D',
                        Qt.Key.Key_Right: b'\x1b[C',
                        Qt.Key.Key_Home: b'\x1b[H',
                        Qt.Key.Key_End: b'\x1b[F',
                    }
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        self._send_live_newline()
                        return True
                    if key == Qt.Key.Key_Backspace:
                        self._send_live_backspace()
                        return True
                    if key == Qt.Key.Key_Tab:
                        self._send_tab_character()
                        return True
                    if key == Qt.Key.Key_Escape:
                        self._send_live_escape_sequence(b'\x1b')
                        return True
                    if key == Qt.Key.Key_Space:
                        self._send_live_text(' ')
                        return True
                    if key in arrow_map:
                        self._send_live_escape_sequence(arrow_map[key])
                        return True
                    char = event.text()
                    if char and (char.isprintable() or char == ' ') and modifiers in (
                            Qt.KeyboardModifier.NoModifier,
                            Qt.KeyboardModifier.ShiftModifier):
                        self._send_live_text(char)
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
    # MobaXterm 风格配色方案
    _KW_RULES_LINUX = [
        # 错误 — MobaXterm 红
        ('#FF5555', '#CC0000', [
            'error', 'err:', ' err ', 'fail', 'failed', 'failure',
            'fatal', 'exception', 'crash', 'panic', 'abort', 'assert',
            'traceback', 'stacktrace', 'undefined', 'invalid', 'illegal',
            'denied', 'permission denied', 'no such file', 'not found',
            'cannot', "can't", 'unable to', 'refused', 'rejected',
            'segfault', 'sigsegv', 'killed', 'out of memory', 'oom',
            'timed out', 'connection refused', 'bad address',
        ]),
        # 警告 — MobaXterm 黄
        ('#FFFF55', '#AA5500', [
            'warn', 'warning', 'deprecated', 'caution', 'attention',
            'skip', 'timeout', 'retry', 'slow', 'skipped',
            'incomplete', 'partial', 'miss', 'not support', 'fallback',
            'deprecated', 'disabled', 'offline',
        ]),
        # 成功 — MobaXterm 绿
        ('#55FF55', '#00AA00', [
            'success', 'succeed', 'completed', 'done', 'finish', 'ok:',
            'passed', '[ ok ]', '[  ok  ]', 'started', 'ready',
            'connected', 'enabled', 'loaded', 'initialized', 'mount',
            'install', 'update complete', 'write ok', 'read ok',
        ]),
        # 信息 — MobaXterm 青
        ('#55FFFF', '#0055AA', [
            'info:', 'debug:', 'verbose:', 'notice:', '>>> ', '<<< ',
            'i/', 'd/', 'v/', 'begin', 'start', 'init', 'open',
            'sending', 'receiving', 'connecting',
        ]),
        # 特殊命令 — MobaXterm 紫
        ('#FF55FF', '#AA00AA', [
            'gmpfunit', 'externDisplay', 'kst_dev', 'batchget',
            'ak_scan', '/data/vendor', '/mnt/media_rw',
        ]),
        # 危险操作 — MobaXterm 橙(亮红)
        ('#FFAA55', '#CC4400', [
            'reboot', 'poweroff', 'shutdown', 'reset', 'factory reset',
            'wipe', 'format', 'erase', 'delete', 'remove', 'rm -rf',
        ]),
        # 路径/目录 — MobaXterm 蓝
        ('#5555FF', '#0000AA', [
            '/system/', '/vendor/', '/data/', '/mnt/', '/proc/', '/sys/',
            '/dev/', '/tmp/', '/etc/', '/home/', '/usr/', '/bin/',
        ]),
        # shell 提示符 — MobaXterm 亮绿
        ('#55FF55', '#00AA00', [
            '# ', '$ ', ':/ #', ':/ $',
        ]),
    ]

    _KW_RULES_CMD = [
        # CMD 错误
        ('#FF5555', '#CC0000', [
            'error', 'err:', 'fail', 'failed', 'denied', 'not found',
            'not recognized', 'is not recognized', 'cannot find',
            'access denied', 'invalid', 'illegal',
        ]),
        # CMD 警告
        ('#FFFF55', '#AA5500', [
            'warn', 'warning', 'skip', 'timeout', 'deprecated',
        ]),
        # CMD 成功
        ('#55FF55', '#00AA00', [
            'success', 'completed', 'done', 'ok', 'ready', 'copied',
        ]),
        # CMD 信息
        ('#55FFFF', '#0055AA', [
            'volume', 'directory', 'dir ', 'file(s)', 'bytes',
            'c:\\', 'd:\\', 'e:\\',
        ]),
    ]

    def _on_syntax_changed(self, scheme: str):
        """切换语法高亮方案"""
        self._syntax_scheme = scheme
        if self._config_mgr:
            self._config_mgr.set('serial.syntax_scheme', scheme)
            self._config_mgr.save()

    def _detect_rx_color(self, line: str) -> str:
        """根据行内容推断高亮颜色（MobaXterm 风格，支持 Linux/CMD 方案）"""
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
        kw_rules = self._KW_RULES_CMD if self._syntax_scheme == 'CMD' else self._KW_RULES_LINUX
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
        # 内联输入高亮色：深色主题白色，浅色主题深蓝（白底可见）
        self._inline_input_color = '#FFFFFF' if self._dark_mode else '#0550AE'

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
        # 光标高亮条颜色随主题更新
        if isinstance(getattr(self, 'input_line', None), _VisibleCursorLineEdit):
            self.input_line.set_theme(self._dark_mode)
        self.combo_newline.setStyleSheet(
            f"color:{t['nl_text']};background:{t['nl_bg']};"
            f"border:1px solid {t['nl_bdr']};border-radius:6px;padding:2px;"
        )
        # 直通/编辑切换按钮
        if hasattr(self, '_btn_passthrough'):
            _checked_bg = t['input_focus']
            self._btn_passthrough.setStyleSheet(
                f"QPushButton{{color:{t['btn_text']};background:{t['btn_bg']};"
                f"border:1px solid {t['btn_bdr']};border-radius:6px;padding:2px;}}"
                f"QPushButton:checked{{background:{_checked_bg};color:#ffffff;border-color:{_checked_bg};}}"
                f"QPushButton:hover{{background:{t['btn_hover']};border-color:{t['btn_hover_bdr']};}}"
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
        # 批量发送区：QPlainTextEdit + SpinBox 单独设置样式
        if hasattr(self, '_batch_edit'):
            self._batch_edit.setStyleSheet(
                f"QPlainTextEdit{{background:{t['input_bg']};color:{t['input_text']};"
                f"border:1px solid {t['input_bdr']};border-radius:4px;padding:4px;}}"
            )
        _spin_qss = (
            f"QDoubleSpinBox,QSpinBox{{background:{t['combo_bg']};color:{t['combo_text']};"
            f"border:1px solid {t['btn_bdr']};border-radius:4px;padding:2px 4px;}}"
        )
        for w in ('_batch_interval_spin', '_batch_repeat_spin'):
            if hasattr(self, w):
                getattr(self, w).setStyleSheet(_spin_qss)
        if hasattr(self, '_lbl_batch_progress'):
            self._lbl_batch_progress.setStyleSheet(
                f"font-size:11px; color:{t['sys']}; font-weight:bold;"
            )
        # 树状导航栏 QTreeWidget 深色主题
        if hasattr(self, '_quick_section_nav'):
            self._quick_section_nav.setStyleSheet(
                f"QTreeWidget {{"
                f"  background:{t['grp_bg']}; color:{t['combo_text']};"
                f"  border:1px solid {t['grp_bdr']}; border-radius:4px;"
                f"  outline:none;"
                f"}}"
                f"QTreeWidget::item {{"
                f"  padding:4px 6px; border-radius:3px;"
                f"}}"
                f"QTreeWidget::item:selected {{"
                f"  background:{t['terminal_sel']}; color:{t['combo_text']};"
                f"}}"
                f"QTreeWidget::item:hover:!selected {{"
                f"  background:{t['btn_hover']};"
                f"}}"
                f"QTreeWidget::branch {{"
                f"  background:{t['grp_bg']};"
                f"}}"
            )

    # Tab直发模式：ANSI CSI 序列匹配正则（一次性编译）
    _ANSI_ESCAPE_RE = re.compile(r'\x1b(?:\[[0-9;?]*[A-Za-z]|\][^\x07]*(?:\x07|\x1b\\)|[()][A-Z0-1]|\x1b)')

    def _strip_rx_control(self, text: str) -> str:
        """Tab直发 RX 预处理：去除 BEL、ANSI 转义序列、退格控制符（\x08）。"""
        text = self._ANSI_ESCAPE_RE.sub('', text)
        text = text.replace('\x07', '')   # BEL
        text = text.replace('\x08', '')   # backspace 控制符（由本地逻辑处理）
        # 移除其余不可见控制字符（保留 \t \n）
        text = re.sub(r'[\x00-\x06\x0e-\x1f\x7f]', '', text)
        return text

    def _append_terminal_inline(self, text: str, color: str = '#C9D1D9'):
        """在终端末尾追加文本（不加时间戳和前缀换行），Tab直发模式专用。"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        if self._auto_scroll:
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        if self._auto_scroll:
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()

    # ──────────────────────────────────────────────────────────────────────
    #  VT100 行级终端处理（直发模式专用）
    # ──────────────────────────────────────────────────────────────────────
    def _vt_replace_current_line(self, text: str, color: str = '#C9D1D9'):
        """替换终端最后一个文本块（段落）的内容，用于 VT 行刷新。"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock,
                            QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(text, fmt)
        if self._auto_scroll:
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()

    def _vt_flush_line(self):
        """输出当前 VT 行并换行，重置行缓冲。"""
        line_text = ''.join(self._vt_line)
        if line_text:
            color = self._detect_rx_color(line_text)
            self._vt_replace_current_line(line_text, color)
            self._log_lines.append(f'[RX] {line_text}')
        # 追加换行，开始新的文本块
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText('\n')
        if self._auto_scroll:
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()
        self._vt_line = []
        self._vt_cursor = 0

    def _process_vt_data(self, data: bytes):
        """处理收到的原始字节，维护 VT 行缓冲。

        支持基础 VT100 序列：
          \\r        回车（光标移至行首）
          \\n        换行（输出当前行，开始新行）
          \\x08      退格（光标左移一格）
          \\x1b[nD   光标左移 n 格
          \\x1b[nC   光标右移 n 格
          \\x1b[K    擦除至行尾
          \\x1b[2K   擦除整行
          \\x1b[nP   删除 n 个字符
          其他 ANSI/控制字符  → 忽略
        """
        text = data.decode('utf-8', errors='replace')
        i = 0
        length = len(text)
        while i < length:
            ch = text[i]

            if ch == '\n':
                self._vt_flush_line()
                i += 1
                continue

            if ch == '\r':
                self._vt_cursor = 0
                i += 1
                continue

            if ch == '\x08':
                self._vt_cursor = max(0, self._vt_cursor - 1)
                i += 1
                continue

            if ch == '\x1b':
                # 解析 CSI 序列 \x1b[ ... <letter>
                if i + 1 < length and text[i + 1] == '[':
                    j = i + 2
                    while j < length and text[j] in '0123456789;?':
                        j += 1
                    if j >= length:
                        # 不完整的转义序列，放回 buffer 等下一包
                        self._rx_buffer.extend(text[i:].encode('utf-8', errors='replace'))
                        break
                    params_str = text[i + 2:j]
                    cmd = text[j]
                    i = j + 1

                    param = int(params_str) if params_str.isdigit() else 1

                    if cmd == 'D':       # 光标左移
                        self._vt_cursor = max(0, self._vt_cursor - param)
                    elif cmd == 'C':     # 光标右移
                        self._vt_cursor = min(len(self._vt_line), self._vt_cursor + param)
                    elif cmd == 'K':     # 擦除行
                        p = int(params_str) if params_str.isdigit() else 0
                        if p == 0:
                            self._vt_line = self._vt_line[:self._vt_cursor]
                        elif p == 1:
                            self._vt_line[:self._vt_cursor] = [' '] * self._vt_cursor
                        elif p == 2:
                            self._vt_line = []
                            self._vt_cursor = 0
                    elif cmd == 'P':     # 删除字符
                        del self._vt_line[self._vt_cursor:self._vt_cursor + param]
                    elif cmd == 'G':     # 光标移到列 n
                        col = max(1, int(params_str) if params_str.isdigit() else 1)
                        self._vt_cursor = min(len(self._vt_line), col - 1)
                    # 其他 CSI 序列忽略
                    continue
                # OSC 或其他转义序列 → 跳过
                j = i + 1
                if j < length and text[j] == ']':
                    while j < length and text[j] not in ('\x07', '\x1b'):
                        j += 1
                    i = j + (2 if j < length and text[j] == '\x1b' else 1)
                elif j < length:
                    while j < length and not text[j].isalpha():
                        j += 1
                    i = j + 1 if j < length else j
                else:
                    # 不完整 ESC
                    self._rx_buffer.extend(b'\x1b')
                    break
                continue

            # 跳过其他控制字符（保留可打印字符和空格）
            if ch != '\t' and (ord(ch) < 32 or ord(ch) == 0x7f):
                i += 1
                continue

            # 普通可打印字符 / Tab → 写入行缓冲
            if self._vt_cursor >= len(self._vt_line):
                self._vt_line.extend([' '] * (self._vt_cursor - len(self._vt_line)))
                self._vt_line.append(ch)
            else:
                self._vt_line[self._vt_cursor] = ch
            self._vt_cursor += 1
            i += 1

        # 批量处理完成后刷新当前行显示
        if self._vt_line:
            line_text = ''.join(self._vt_line)
            self._vt_replace_current_line(line_text,
                                          self._detect_rx_color(line_text))

    def _append_terminal(self, text: str, color: str = '#C9D1D9'):
        ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
        new_line = f"[{ts}] {text}\n"
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        freeze_view = bool(getattr(self, '_freeze_view_on_rx', False) or getattr(self, '_nav_paused', False))
        _scroll_value = None
        if freeze_view:
            _vbar = self.terminal.verticalScrollBar()
            _scroll_value = _vbar.value()
        # 携带当前字号，确保缩放后新插入文字与已有文字一致
        _pt = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
        if _pt > 0:
            fmt.setFontPointSize(_pt)

        if self._terminal_input_mode and self._terminal_input_anchor >= 0:
            # 内联输入模式：新数据插入已输内容之前，保留已输内容（不换行、不变色）
            saved_buf = self._terminal_input_buf
            # 1. 精确删除已输字符：从 anchor 向右 len(buf) 个字符（保留末尾 \n）
            cursor = self.terminal.textCursor()
            cursor.setPosition(self._terminal_input_anchor)
            cursor.movePosition(QTextCursor.MoveOperation.Right,
                                QTextCursor.MoveMode.KeepAnchor, len(saved_buf))
            cursor.removeSelectedText()
            # 2. 移到 End（跨过保留的 \n），再插入新设备数据
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(new_line, fmt)  # new_line 以 \n 结尾
            # 3. 锚点设在新行末尾 \n 之前
            cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter)
            self._terminal_input_anchor = cursor.position()
            # 4. 不变色重新插入已输内容
            if saved_buf:
                fmt_input = QTextCharFormat()
                fmt_input.setForeground(QColor(self._inline_input_color))
                fmt_input.setFontWeight(700)
                _pt2 = getattr(self.terminal, '_zoom_pt', 0) or self.terminal.font().pointSize()
                if _pt2 > 0:
                    fmt_input.setFontPointSize(_pt2)
                cursor.insertText(saved_buf, fmt_input)
            self._terminal_input_buf = saved_buf
            if not getattr(self, '_nav_paused', False):
                self.terminal.setTextCursor(cursor)
                self.terminal.ensureCursorVisible()
        else:
            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(new_line, fmt)
            if self._auto_scroll and not getattr(self, '_nav_paused', False):
                self._move_terminal_cursor_to_visible_end()

        if freeze_view and _scroll_value is not None:
            self.terminal.verticalScrollBar().setValue(_scroll_value)

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
                sec._quick_category = 'custom'
                self._quick_sections_list.append(sec)
                self._sections_layout.addWidget(sec)
                self._refresh_dyn_buttons(sec)
        self._apply_quick_filter(self._quick_filter)

    def _refresh_custom_buttons(self):
        # 清空旧按钮
        while self._custom_btns_layout.count():
            w = self._custom_btns_layout.takeAt(0)
            if w.widget():
                w.widget().setParent(None)

        t = _DARK if self._dark_mode else _LIGHT
        _STYLE = (
            f"QPushButton{{background:{t['btn_bg']};color:{t['btn_text']};"
            f"border:1px solid {t['btn_bdr']};border-radius:5px;"
            f"padding:4px 8px;font-size:12px;text-align:left;}}"
            f"QPushButton:hover{{background:{t['btn_hover']};"
            f"border-color:{t['btn_hover_bdr']};color:{t['combo_text']};}}"
        )
        _ARROW_STYLE = (
            f"QToolButton{{color:{t['grp_title']};background:transparent;"
            f"border:none;font-size:10px;padding:0 1px;}}"
            f"QToolButton:hover{{color:{t['combo_text']};}}"
        )

        total = len(self._custom_cmds)
        for i, item in enumerate(self._custom_cmds):
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            # ↑↓ 排序按钮
            btn_up = QToolButton()
            btn_up.setText("▲")
            btn_up.setToolTip("上移")
            btn_up.setStyleSheet(_ARROW_STYLE)
            btn_up.setFixedSize(16, 16)
            btn_up.setEnabled(i > 0)
            btn_up.clicked.connect(lambda checked, idx=i: self._move_custom(idx, -1))
            row_layout.addWidget(btn_up)

            btn_down = QToolButton()
            btn_down.setText("▼")
            btn_down.setToolTip("下移")
            btn_down.setStyleSheet(_ARROW_STYLE)
            btn_down.setFixedSize(16, 16)
            btn_down.setEnabled(i < total - 1)
            btn_down.clicked.connect(lambda checked, idx=i: self._move_custom(idx, 1))
            row_layout.addWidget(btn_down)

            # 按钮（名称 + 注释）
            desc = item.get('desc', '')
            btn_text = f"  {item['name']}"
            if desc:
                btn_text += f"  ({desc})"
            btn = QPushButton(btn_text)
            tooltip = f"<code>{item['cmd']}</code>"
            if desc:
                tooltip = f"<b>{desc}</b><br/>{tooltip}"
            btn.setToolTip(tooltip)
            btn.setStyleSheet(_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, c=item['cmd']: self._send_command(c))
            row_layout.addWidget(btn, stretch=1)

            btn_edit = QToolButton()
            btn_edit.setText("✏")
            btn_edit.setToolTip("编辑")
            btn_edit.setStyleSheet(f"color:{t['grp_title']};background:transparent;border:none;font-size:12px;")
            btn_edit.clicked.connect(lambda checked, idx=i: self._on_edit_custom(idx))
            row_layout.addWidget(btn_edit)

            btn_del = QToolButton()
            btn_del.setText("✕")
            btn_del.setToolTip("删除")
            btn_del.setStyleSheet("color:#E74C3C;background:transparent;border:none;font-size:12px;")
            btn_del.clicked.connect(lambda checked, idx=i: self._on_delete_custom(idx))
            row_layout.addWidget(btn_del)

            container = QWidget()
            container.setLayout(row_layout)
            self._custom_btns_layout.addWidget(container)

        if not self._custom_cmds:
            lbl = QLabel("暂无自定义指令，点击「＋ 添加」新建")
            lbl.setStyleSheet(f"color:{t['grp_title']};font-size:11px;padding:4px;")
            self._custom_btns_layout.addWidget(lbl)

    def _move_custom(self, idx: int, direction: int):
        """移动快捷指令位置，direction: -1=上移, 1=下移"""
        new_idx = idx + direction
        if 0 <= new_idx < len(self._custom_cmds):
            self._custom_cmds[idx], self._custom_cmds[new_idx] = \
                self._custom_cmds[new_idx], self._custom_cmds[idx]
            self._save_all_data()
            self._refresh_custom_buttons()

    def _on_add_custom(self):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd, desc = dlg.get_values()
            self._custom_cmds.append({"name": name, "cmd": cmd, "desc": desc})
            self._save_all_data()
            self._refresh_custom_buttons()

    def _on_edit_custom(self, idx: int):
        item = self._custom_cmds[idx]
        dlg = CmdEditDialog(name=item['name'], cmd=item['cmd'],
                            desc=item.get('desc', ''), parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd, desc = dlg.get_values()
            self._custom_cmds[idx] = {"name": name, "cmd": cmd, "desc": desc}
            self._save_all_data()
            self._refresh_custom_buttons()

    def _on_add_dyn_cmd(self, sec: '_CollapsibleSection'):
        dlg = CmdEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, cmd, desc = dlg.get_values()
            sec._dyn_cmds.append({"name": name, "cmd": cmd, "desc": desc})
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

    def _on_tab_passthrough_toggled(self, enabled: bool):
        if enabled:
            self.input_line.clear()
            self.input_line.setReadOnly(True)
            self.input_line.setPlaceholderText("Tab直发模式：键盘直通串口 | 退格/方向键/Enter均直发")
            if getattr(self, '_terminal_input_mode', False):
                self._terminal_cancel_input()
        else:
            self.input_line.setReadOnly(False)
            self.input_line.setPlaceholderText("输入指令，按 Enter 发送 | ↑↓ 历史 | Tab 补全...")

    def _is_tab_passthrough_enabled(self) -> bool:
        # 以按钮状态为准，避免内部状态与 UI 不一致导致误入直发模式
        if hasattr(self, '_btn_passthrough'):
            return bool(self._btn_passthrough.isChecked())
        return bool(getattr(self, '_passthrough_mode', False))

    def _on_toggle_passthrough(self, checked: bool):
        """切换直通/编辑模式，并更新输入框占位文字与按钮图标。"""
        self._passthrough_mode = checked
        if checked:
            self._btn_passthrough.setText("📡")
            self.input_line.setPlaceholderText("直通模式：方向键/退格/Enter 直接发往串口")
        else:
            self._btn_passthrough.setText("✏")
            self.input_line.setPlaceholderText("编辑模式：方向键移动光标，Enter 发送命令")

    def _write_serial_bytes(self, payload: bytes) -> bool:
        if not (self._serial and self._serial.is_open):
            return False
        try:
            self._serial.write(payload)
            return True
        except Exception as e:
            self._sys_msg(f'发送失败: {e}', error=True)
            return False

    def _flush_tab_passthrough_pending_input(self):
        if not (self._serial and self._serial.is_open):
            self._sys_msg('⚠ 串口未连接，无法发送 Tab', error=True)
            return False

        if getattr(self, '_terminal_input_mode', False) and self._terminal_input_buf:
            pending = self._terminal_input_buf
            if not self._write_serial_bytes(pending.encode('utf-8')):
                return False
            self._log_lines.append(f'[TX-LIVE] {pending}')
            self._terminal_cancel_input()
            self._tab_candidates = []
            self._tab_idx = -1
            return True

        if hasattr(self, 'input_line'):
            pending = self.input_line.text()
            if pending:
                if not self._write_serial_bytes(pending.encode('utf-8')):
                    return False
                self._log_lines.append(f'[TX-LIVE] {pending}')
                self.input_line.clear()
                self._tab_candidates = []
                self._tab_idx = -1
        return True

    def _send_live_text(self, text: str) -> bool:
        if not text:
            return True
        return self._write_serial_bytes(text.encode('utf-8'))

    def _send_live_backspace(self) -> bool:
        return self._write_serial_bytes(b'\x7f')

    def _send_live_escape_sequence(self, sequence: bytes) -> bool:
        return self._write_serial_bytes(sequence)

    def _send_live_newline(self) -> bool:
        nl_map = {"\\r\\n": b'\r\n', "\\n": b'\n', "\\r": b'\r', "无": b''}
        nl = nl_map.get(self.combo_newline.currentText(), b'\r\n')
        if not self._write_serial_bytes(nl):
            return False
        # VT 模式：不做本地显示，设备回显会由 VT 处理器处理
        # 回车后重置 VT 行缓冲（新命令行）
        self._vt_line = []
        self._vt_cursor = 0
        self._log_lines.append('[TX] ↵')
        return True

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

        self._icon_hint_lbl = QLabel('左侧目录选择板块，右侧显示当前板块内容。')
        self._icon_hint_lbl.setWordWrap(True)
        outer_layout.addWidget(self._icon_hint_lbl)

        self._quick_panel_search = QLineEdit()
        self._quick_panel_search.setPlaceholderText('搜索板块标题或命令关键字，例如 reboot / KST / CSV')
        self._quick_panel_search.textChanged.connect(lambda _text: self._apply_quick_filter('tree'))
        outer_layout.addWidget(self._quick_panel_search)

        self._quick_filter_meta = QLabel('匹配板块: 0')
        self._quick_filter_meta.setWordWrap(True)
        outer_layout.addWidget(self._quick_filter_meta)

        tree_actions = QHBoxLayout()
        tree_actions.setContentsMargins(0, 0, 0, 0)
        tree_actions.setSpacing(6)
        btn_add_root = QPushButton('新建顶层')
        btn_add_root.clicked.connect(self._on_add_root_section)
        btn_add_child = QPushButton('新建子板块')
        btn_add_child.clicked.connect(self._on_add_child_section)
        btn_rename_node = QPushButton('重命名')
        btn_rename_node.clicked.connect(self._on_rename_tree_section)
        btn_delete_node = QPushButton('删除')
        btn_delete_node.clicked.connect(self._on_delete_tree_section)
        tree_actions.addWidget(btn_add_root)
        tree_actions.addWidget(btn_add_child)
        tree_actions.addWidget(btn_rename_node)
        tree_actions.addWidget(btn_delete_node)
        tree_actions.addStretch(1)
        outer_layout.addLayout(tree_actions)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        self._quick_section_nav = QTreeWidget()
        self._quick_section_nav.setHeaderHidden(True)
        self._quick_section_nav.setMinimumWidth(220)
        self._quick_section_nav.setMaximumWidth(300)
        self._quick_section_nav.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._quick_section_nav.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._quick_section_nav.currentItemChanged.connect(self._focus_quick_section)
        self._quick_section_nav.model().rowsMoved.connect(self._on_quick_tree_rows_moved)
        content_split.addWidget(self._quick_section_nav)

        content_wrap = QWidget()
        content_wrap_layout = QVBoxLayout(content_wrap)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.setSpacing(8)
        self._quick_selected_title = QLabel('请选择板块')
        content_wrap_layout.addWidget(self._quick_selected_title)

        sec_widget = QWidget()
        self._sections_layout = QVBoxLayout(sec_widget)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(10)
        content_wrap_layout.addWidget(sec_widget, 1)
        content_split.addWidget(content_wrap)
        content_split.setSizes([220, 620])
        outer_layout.addWidget(content_split, 1)

        self._built_in_sections = {}
        built_in_defs = [
            ('batch_send', self._build_batch_send_group()),
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
            sec._parent_persist_id = ''
            self._built_in_sections[persist_id] = sec
            self._quick_sections_list.append(sec)
            self._sections_layout.addWidget(sec)

        self._refresh_section_controls()
        self._refresh_quick_section_nav()

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
        self._apply_quick_filter('tree')

        outer_layout.addStretch()
        return panel

    def _apply_quick_filter(self, category: str):
        self._quick_filter = 'tree'
        keyword = ''
        if hasattr(self, '_quick_panel_search'):
            keyword = self._quick_panel_search.text().strip().lower()
        for sec in self._quick_sections_list:
            search_blob = [sec._title_lbl.text().lower()]
            for item in getattr(sec, '_dyn_cmds', []):
                search_blob.append(str(item.get('name', '')).lower())
                search_blob.append(str(item.get('cmd', '')).lower())
            if hasattr(sec, '_hint_text'):
                search_blob.append(str(getattr(sec, '_hint_text', '')).lower())
            sec.setProperty('_tree_match', (not keyword or keyword in ' '.join(search_blob)))
        if getattr(self, '_btn_add_section', None) is not None:
            self._btn_add_section.setVisible(True)
        self._refresh_quick_section_nav()

    def _plain_section_title(self, title: str) -> str:
        return re.sub(r'^[^\w\u4e00-\u9fff]+', '', title or '').strip() or title or '未命名板块'

    def _refresh_quick_section_nav(self):
        if not hasattr(self, '_quick_section_nav'):
            return
        self._quick_section_nav.blockSignals(True)
        self._quick_section_nav.clear()
        visible_count = 0
        first_leaf = None
        children_map = {}
        for sec in self._quick_sections_list:
            parent_id = getattr(sec, '_parent_persist_id', '') or ''
            children_map.setdefault(parent_id, []).append(sec)

        def _append_children(parent_item, parent_id):
            nonlocal visible_count, first_leaf
            for sec in children_map.get(parent_id, []):
                if not bool(sec.property('_tree_match')):
                    sec.setVisible(False)
                    continue
                item = QTreeWidgetItem([self._plain_section_title(sec._title_lbl.text())])
                item.setData(0, Qt.ItemDataRole.UserRole, getattr(sec, '_persist_id', ''))
                if parent_item is None:
                    self._quick_section_nav.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                item.setExpanded(True)
                visible_count += 1
                if first_leaf is None:
                    first_leaf = item
                _append_children(item, getattr(sec, '_persist_id', ''))

        _append_children(None, '')
        self._quick_section_nav.blockSignals(False)
        if hasattr(self, '_quick_filter_meta'):
            suffix = ' | 搜索中' if self._quick_panel_search.text().strip() else ''
            self._quick_filter_meta.setText(f'匹配板块: {visible_count}{suffix}')
        if first_leaf is not None:
            self._quick_section_nav.setCurrentItem(first_leaf)
        else:
            for sec in self._quick_sections_list:
                sec.setVisible(False)
            if hasattr(self, '_quick_selected_title'):
                self._quick_selected_title.setText('未找到匹配板块')

    def _focus_quick_section(self, current, _previous):
        if current is None:
            if hasattr(self, '_quick_selected_title'):
                self._quick_selected_title.setText('请选择板块')
            return
        section_id = current.data(0, Qt.ItemDataRole.UserRole)
        for sec in self._quick_sections_list:
            if getattr(sec, '_persist_id', '') == section_id:
                if hasattr(self, '_quick_selected_title'):
                    self._quick_selected_title.setText(self._plain_section_title(sec._title_lbl.text()))
                sec._header.setVisible(False)  # 树形导航模式无需折叠/展开 header
                sec.setVisible(True)
                if getattr(sec, '_collapsed', False):
                    sec._do_expand()
            else:
                sec._header.setVisible(True)
                sec.setVisible(False)
                if not getattr(sec, '_collapsed', False):
                    sec._do_collapse()

    def _current_tree_section(self):
        item = self._quick_section_nav.currentItem() if hasattr(self, '_quick_section_nav') else None
        if item is None:
            return None
        section_id = item.data(0, Qt.ItemDataRole.UserRole)
        for sec in self._quick_sections_list:
            if getattr(sec, '_persist_id', '') == section_id:
                return sec
        return None

    def _on_add_root_section(self):
        self._create_tree_section(parent_section=None)

    def _on_add_child_section(self):
        self._create_tree_section(parent_section=self._current_tree_section())

    def _create_tree_section(self, parent_section=None):
        name, ok = QInputDialog.getText(self, '新建板块', '输入板块名称:')
        if not ok or not name.strip():
            return
        parent_id = getattr(parent_section, '_persist_id', '') if parent_section else ''
        sec = self._build_dynamic_section(name.strip(), persist_id=f'dyn:{int(time.time() * 1000)}', parent_id=parent_id)
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
        self._apply_quick_filter('tree')
        self._save_all_data()

    def _on_rename_tree_section(self):
        sec = self._current_tree_section()
        if sec is None:
            return
        new_name, ok = QInputDialog.getText(self, '重命名板块', '输入新名称:', text=self._plain_section_title(sec._title_lbl.text()))
        if ok and new_name.strip():
            sec.update_title(new_name.strip())
            self._apply_quick_filter('tree')
            self._save_all_data()

    def _on_delete_tree_section(self):
        sec = self._current_tree_section()
        if sec is None:
            return
        if not getattr(sec, '_persist_id', '').startswith('dyn:'):
            QMessageBox.information(self, '无法删除', '内置板块暂不支持删除，可重命名或在其下新增子板块。')
            return
        self._delete_dynamic_section(sec)

    def _on_quick_tree_rows_moved(self, *_args):
        self._sync_tree_structure_from_nav()

    def _sync_tree_structure_from_nav(self):
        if not hasattr(self, '_quick_section_nav'):
            return
        order = []

        def _walk(item, parent_id=''):
            section_id = item.data(0, Qt.ItemDataRole.UserRole)
            for sec in self._quick_sections_list:
                if getattr(sec, '_persist_id', '') == section_id:
                    sec._parent_persist_id = parent_id
                    order.append(sec)
                    break
            for index in range(item.childCount()):
                _walk(item.child(index), section_id)

        for index in range(self._quick_section_nav.topLevelItemCount()):
            _walk(self._quick_section_nav.topLevelItem(index), '')

        remaining = [sec for sec in self._quick_sections_list if sec not in order]
        self._quick_sections_list = order + remaining
        self._save_all_data()

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

        target_ids = {getattr(sec, '_persist_id', '')}
        changed = True
        while changed:
            changed = False
            for item in list(self._quick_sections_list):
                parent_id = getattr(item, '_parent_persist_id', '') or ''
                item_id = getattr(item, '_persist_id', '')
                if item_id and item_id not in target_ids and parent_id in target_ids:
                    target_ids.add(item_id)
                    changed = True

        for item in list(self._quick_sections_list):
            if getattr(item, '_persist_id', '') not in target_ids:
                continue
            self._quick_sections_list.remove(item)
            self._sections_layout.removeWidget(item)
            item.deleteLater()

        self._refresh_section_controls()
        self._apply_quick_filter('tree')
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
        sec = _CollapsibleSection('📦 固件升级准备', collapsed=True)
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

    def _build_dynamic_section(self, name: str, persist_id: str = '', parent_id: str = '') -> _CollapsibleSection:
        sec = _CollapsibleSection(name, collapsed=True)
        sec._persist_id = persist_id or f'dyn:{int(time.time() * 1000)}'
        sec._parent_persist_id = parent_id or ''
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
        sec = _CollapsibleSection('🔧 系统工具', collapsed=True)
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
        self._on_add_root_section()

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
                    'parent_id': getattr(sec, '_parent_persist_id', ''),
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
            'theme': {'dark_mode': True},
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
                bool(self._config_mgr.get('serial.dark_mode', True)),
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
                parent_id=sec_data.get('parent_id', ''),
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
            # 未在保存列表的内置板块（非 dyn:）排最前，动态板块排最后
            missing_builtins = [
                sec for sec in self._quick_sections_list
                if sec not in ordered and not getattr(sec, '_persist_id', '').startswith('dyn:')
            ]
            missing_dynamics = [
                sec for sec in self._quick_sections_list
                if sec not in ordered and getattr(sec, '_persist_id', '').startswith('dyn:')
            ]
            ordered = missing_builtins + ordered + missing_dynamics
            self._quick_sections_list = ordered
            for sec in ordered:
                self._sections_layout.removeWidget(sec)
            for sec in ordered:
                self._sections_layout.addWidget(sec)
                sec.show()

        self._refresh_section_controls()
        self._refresh_custom_buttons()
        self._apply_quick_filter(getattr(self, '_quick_filter', 'common'))
