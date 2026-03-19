# -*- coding: utf-8 -*-
"""设备联调台页面。"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
from PyQt6.QtCore import QPoint, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.device_lab_store import DeviceLabStore
from workers.serial_worker import SerialReaderThread


_PAGE_QSS = """
QWidget#device_lab_root {
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(251,248,242,1), stop:0.55 rgba(247,243,235,1), stop:1 rgba(236,240,245,1));
}
QGroupBox#lab_card {
    background: rgba(255,255,255,0.95);
    border: 1px solid rgba(148,163,184,0.28);
    border-radius: 16px;
    margin-top: 22px;
    padding-top: 18px;
    font-weight: bold;
    color: #243447;
}
QGroupBox#lab_card::title {
    subcontrol-origin: margin;
    left: 14px;
    top: 2px;
    padding: 4px 10px;
    background: #fff8ee;
    color: #a16207;
    border: 1px solid rgba(217,119,6,0.20);
    border-radius: 8px;
}
QFrame#remote_canvas {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(31,41,55,0.96), stop:1 rgba(15,23,42,0.98));
    border: 1px solid rgba(251,191,36,0.26);
    border-radius: 28px;
}
QPushButton#remote_btn {
    background: rgba(255,255,255,0.08);
    color: white;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    font-weight: bold;
}
QPushButton#remote_btn[selected="true"] {
    border: 2px solid rgba(251,191,36,0.95);
    background: rgba(251,191,36,0.24);
}
QLabel#hero_title {
    font-size: 22px;
    font-weight: bold;
    color: #1f2937;
}
QLabel#hero_subtitle {
    color: #64748b;
    font-size: 12px;
}
QLabel#status_chip {
    background: rgba(245,158,11,0.12);
    color: #92400e;
    border: 1px solid rgba(245,158,11,0.28);
    border-radius: 999px;
    padding: 4px 10px;
}
QLabel#camera_preview {
    background: #0f172a;
    color: #cbd5e1;
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 14px;
}
QPlainTextEdit#device_log {
    background: rgba(15,23,42,0.96);
    color: #dbeafe;
    border: 1px solid rgba(37,99,235,0.18);
    border-radius: 12px;
    font-family: "Cascadia Code","Consolas";
    font-size: 12px;
}
QPushButton#lab_primary {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f59e0b, stop:1 #d97706);
    color: white;
    border: 1px solid rgba(180,83,9,0.34);
    border-radius: 10px;
    font-weight: bold;
    padding: 6px 14px;
}
QPushButton#lab_secondary {
    background: #fff8ee;
    color: #92400e;
    border: 1px solid rgba(245,158,11,0.20);
    border-radius: 10px;
    padding: 6px 14px;
}
"""


class CommandItemDialog(QDialog):
    def __init__(self, title: str, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 360)

        values = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(values.get("name", ""))
        self.edit_desc = QLineEdit(values.get("description", ""))
        self.edit_commands = QTextEdit("\n".join(values.get("commands", [])))
        self.edit_commands.setPlaceholderText("每行一条串口指令")

        form.addRow("名称", self.edit_name)
        form.addRow("说明", self.edit_desc)
        form.addRow("指令", self.edit_commands)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "提示", "名称不能为空")
            return
        commands = [line.strip() for line in self.edit_commands.toPlainText().splitlines() if line.strip()]
        if not commands:
            QMessageBox.warning(self, "提示", "至少保留一条指令")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "name": self.edit_name.text().strip(),
            "description": self.edit_desc.text().strip(),
            "commands": [line.strip() for line in self.edit_commands.toPlainText().splitlines() if line.strip()],
        }


class ScriptDialog(QDialog):
    def __init__(self, title: str, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(620, 420)
        values = data or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_name = QLineEdit(values.get("name", ""))
        self.edit_desc = QLineEdit(values.get("description", ""))
        self.edit_steps = QTextEdit("\n".join(values.get("steps", [])))
        self.edit_steps.setPlaceholderText(
            "支持写法:\nsetting:关闭位移AK\nshortcut:主页键\nwait:1.5\ninput keyevent 23"
        )
        form.addRow("剧本名", self.edit_name)
        form.addRow("说明", self.edit_desc)
        form.addRow("步骤", self.edit_steps)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "提示", "剧本名不能为空")
            return
        steps = [line.strip() for line in self.edit_steps.toPlainText().splitlines() if line.strip()]
        if not steps:
            QMessageBox.warning(self, "提示", "请至少写一条步骤")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "name": self.edit_name.text().strip(),
            "description": self.edit_desc.text().strip(),
            "steps": [line.strip() for line in self.edit_steps.toPlainText().splitlines() if line.strip()],
        }


class RemoteButtonDialog(QDialog):
    def __init__(self, shortcuts: List[Dict[str, Any]], data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑遥控按键")
        self.resize(520, 260)
        self._shortcuts = shortcuts
        values = data or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(values.get("name", ""))
        self.combo_binding = QComboBox()
        self.combo_binding.addItems(["直接串口", "快捷指令"])
        self.edit_serial = QLineEdit(values.get("binding_value", ""))
        self.combo_shortcut = QComboBox()
        self.combo_shortcut.addItems([item["name"] for item in shortcuts])

        binding_type = values.get("binding_type", "serial")
        self.combo_binding.setCurrentIndex(1 if binding_type == "shortcut" else 0)
        if binding_type == "shortcut" and values.get("binding_value"):
            index = self.combo_shortcut.findText(values["binding_value"])
            if index >= 0:
                self.combo_shortcut.setCurrentIndex(index)
        self.edit_serial.setText(values.get("binding_value", "") if binding_type == "serial" else "")

        self.combo_binding.currentIndexChanged.connect(self._sync_binding_widgets)

        form.addRow("按键名", self.edit_name)
        form.addRow("绑定类型", self.combo_binding)
        form.addRow("串口指令", self.edit_serial)
        form.addRow("快捷指令", self.combo_shortcut)
        layout.addLayout(form)
        self._sync_binding_widgets()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sync_binding_widgets(self):
        is_shortcut = self.combo_binding.currentText() == "快捷指令"
        self.edit_serial.setVisible(not is_shortcut)
        self.combo_shortcut.setVisible(is_shortcut)

    def _on_accept(self):
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "提示", "按键名称不能为空")
            return
        if self.combo_binding.currentText() == "直接串口" and not self.edit_serial.text().strip():
            QMessageBox.warning(self, "提示", "串口指令不能为空")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        if self.combo_binding.currentText() == "快捷指令":
            binding_type = "shortcut"
            binding_value = self.combo_shortcut.currentText().strip()
        else:
            binding_type = "serial"
            binding_value = self.edit_serial.text().strip()
        return {
            "name": self.edit_name.text().strip(),
            "binding_type": binding_type,
            "binding_value": binding_value,
        }


class DraggableRemoteButton(QPushButton):
    activated = pyqtSignal(str)
    moved = pyqtSignal(str, int, int)
    selected = pyqtSignal(str)

    def __init__(self, button_id: str, get_edit_mode, parent=None):
        super().__init__(parent)
        self.button_id = button_id
        self._drag_origin: Optional[QPoint] = None
        self._start_pos: Optional[QPoint] = None
        self._dragged = False
        self._get_edit_mode = get_edit_mode
        self.setObjectName("remote_btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            self._start_pos = self.pos()
            self._dragged = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._get_edit_mode() or self._drag_origin is None or self._start_pos is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_origin
        if delta.manhattanLength() > 2:
            self._dragged = True
        parent = self.parentWidget()
        if parent is None:
            return
        new_x = max(8, min(parent.width() - self.width() - 8, self._start_pos.x() + delta.x()))
        new_y = max(8, min(parent.height() - self.height() - 8, self._start_pos.y() + delta.y()))
        self.move(new_x, new_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._get_edit_mode():
                self.selected.emit(self.button_id)
                if self._dragged:
                    self.moved.emit(self.button_id, self.x(), self.y())
            else:
                self.activated.emit(self.button_id)
        self._drag_origin = None
        self._start_pos = None
        super().mouseReleaseEvent(event)


class DeviceLabPage(QWidget):
    """设备联调台。"""

    def __init__(self, config_mgr=None, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._store = DeviceLabStore()
        self._profile = self._store.get_all()

        self._serial = None
        self._reader_thread: Optional[SerialReaderThread] = None
        self._command_queue: List[Tuple[Optional[str], float, str]] = []
        self._queue_timer = QTimer(self)
        self._queue_timer.setSingleShot(True)
        self._queue_timer.timeout.connect(self._process_next_queue_item)

        self._camera_capture = None
        self._camera_timer = QTimer(self)
        self._camera_timer.timeout.connect(self._update_camera_frame)
        self._camera_frame_counter = 0
        self._camera_fps_anchor = time.time()
        self._selected_remote_id: Optional[str] = None
        self._remote_buttons: Dict[str, DraggableRemoteButton] = {}

        self.setObjectName("device_lab_root")
        self.setStyleSheet(_PAGE_QSS)
        self._init_ui()
        self._load_profile_to_ui()
        self._refresh_serial_ports()
        self._scan_cameras()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        hero = QFrame()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(12, 6, 12, 6)

        title_box = QVBoxLayout()
        title = QLabel("设备联调台")
        title.setObjectName("hero_title")
        subtitle = QLabel("USB 相机、串口调试、快捷配置、遥控器模拟器、联调剧本统一入口")
        subtitle.setObjectName("hero_subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        hero_layout.addLayout(title_box, 1)

        self.lbl_serial_chip = QLabel("串口未连接")
        self.lbl_serial_chip.setObjectName("status_chip")
        self.lbl_camera_chip = QLabel("相机未连接")
        self.lbl_camera_chip.setObjectName("status_chip")
        hero_layout.addWidget(self.lbl_serial_chip)
        hero_layout.addWidget(self.lbl_camera_chip)
        root_layout.addWidget(hero)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter, 1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_wrap = QWidget()
        left_layout = QVBoxLayout(left_wrap)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        left_layout.addWidget(self._build_serial_card())
        left_layout.addWidget(self._build_quick_tabs_card())
        left_layout.addWidget(self._build_script_card())
        left_layout.addStretch(1)
        left_scroll.setWidget(left_wrap)
        splitter.addWidget(left_scroll)

        right_wrap = QWidget()
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(self._build_camera_card())
        right_layout.addWidget(self._build_remote_card())
        right_layout.addWidget(self._build_log_card(), 1)
        splitter.addWidget(right_wrap)
        splitter.setSizes([760, 540])

    def _build_serial_card(self) -> QGroupBox:
        card = QGroupBox("串口工作台")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)

        row1 = QHBoxLayout()
        self.combo_port = QComboBox()
        self.combo_port.setMinimumWidth(140)
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "57600", "115200", "230400", "460800"])
        self.combo_baud.setCurrentText("115200")
        btn_refresh = QPushButton("刷新端口")
        btn_refresh.setObjectName("lab_secondary")
        btn_refresh.clicked.connect(self._refresh_serial_ports)
        self.btn_serial_connect = QPushButton("连接串口")
        self.btn_serial_connect.setObjectName("lab_primary")
        self.btn_serial_connect.clicked.connect(self._toggle_serial_connection)
        row1.addWidget(QLabel("端口"))
        row1.addWidget(self.combo_port)
        row1.addWidget(QLabel("波特率"))
        row1.addWidget(self.combo_baud)
        row1.addWidget(btn_refresh)
        row1.addWidget(self.btn_serial_connect)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.chk_newline = QCheckBox("发送后追加回车")
        self.chk_auto_su = QCheckBox("连接后自动发送 su")
        row2.addWidget(self.chk_newline)
        row2.addWidget(self.chk_auto_su)
        row2.addStretch(1)
        layout.addLayout(row2)

        send_row = QHBoxLayout()
        self.edit_serial_cmd = QLineEdit()
        self.edit_serial_cmd.setPlaceholderText("输入串口指令，例如 input keyevent 23")
        btn_send = QPushButton("发送")
        btn_send.setObjectName("lab_primary")
        btn_send.clicked.connect(self._send_manual_serial_command)
        send_row.addWidget(self.edit_serial_cmd, 1)
        send_row.addWidget(btn_send)
        layout.addLayout(send_row)

        self.serial_terminal = QPlainTextEdit()
        self.serial_terminal.setObjectName("device_log")
        self.serial_terminal.setReadOnly(True)
        self.serial_terminal.setMaximumBlockCount(800)
        self.serial_terminal.setMinimumHeight(180)
        layout.addWidget(self.serial_terminal)
        return card

    def _build_quick_tabs_card(self) -> QGroupBox:
        card = QGroupBox("快捷配置与遥控指令库")
        card.setObjectName("lab_card")
        layout = QHBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(self._build_command_list_block(
            title="配置项2 快捷配置",
            list_attr="list_quick_settings",
            desc_attr="lbl_quick_desc",
            add_slot=self._add_quick_setting,
            edit_slot=self._edit_quick_setting,
            delete_slot=self._delete_quick_setting,
            run_slot=self._run_selected_quick_setting,
        ))
        layout.addWidget(self._build_command_list_block(
            title="遥控快捷指令",
            list_attr="list_shortcuts",
            desc_attr="lbl_shortcut_desc",
            add_slot=self._add_shortcut,
            edit_slot=self._edit_shortcut,
            delete_slot=self._delete_shortcut,
            run_slot=self._run_selected_shortcut,
        ))
        return card

    def _build_command_list_block(self, title, list_attr, desc_attr, add_slot, edit_slot, delete_slot, run_slot):
        box = QGroupBox(title)
        box.setObjectName("lab_card")
        layout = QVBoxLayout(box)
        list_widget = QListWidget()
        setattr(self, list_attr, list_widget)
        list_widget.currentItemChanged.connect(lambda _cur, _old, attr=desc_attr, lst=list_widget: self._sync_command_description(lst, attr))
        layout.addWidget(list_widget)

        desc = QLabel("请选择一项")
        desc.setWordWrap(True)
        setattr(self, desc_attr, desc)
        layout.addWidget(desc)

        row = QHBoxLayout()
        for text, slot, primary in [
            ("新增", add_slot, False),
            ("编辑", edit_slot, False),
            ("删除", delete_slot, False),
            ("执行", run_slot, True),
        ]:
            button = QPushButton(text)
            button.setObjectName("lab_primary" if primary else "lab_secondary")
            button.clicked.connect(slot)
            row.addWidget(button)
        layout.addLayout(row)
        return box

    def _build_script_card(self) -> QGroupBox:
        card = QGroupBox("联调剧本")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)

        project_row = QHBoxLayout()
        self.combo_project = QComboBox()
        self.combo_project.currentIndexChanged.connect(self._refresh_scripts)
        btn_add_project = QPushButton("新增项目")
        btn_add_project.setObjectName("lab_secondary")
        btn_add_project.clicked.connect(self._add_project)
        btn_rename_project = QPushButton("重命名项目")
        btn_rename_project.setObjectName("lab_secondary")
        btn_rename_project.clicked.connect(self._rename_project)
        btn_del_project = QPushButton("删除项目")
        btn_del_project.setObjectName("lab_secondary")
        btn_del_project.clicked.connect(self._delete_project)
        project_row.addWidget(QLabel("项目"))
        project_row.addWidget(self.combo_project, 1)
        project_row.addWidget(btn_add_project)
        project_row.addWidget(btn_rename_project)
        project_row.addWidget(btn_del_project)
        layout.addLayout(project_row)

        self.list_scripts = QListWidget()
        self.list_scripts.currentItemChanged.connect(self._sync_script_details)
        self.list_scripts.setMinimumHeight(140)
        layout.addWidget(self.list_scripts)

        self.lbl_script_desc = QLabel("请选择剧本")
        self.lbl_script_desc.setWordWrap(True)
        layout.addWidget(self.lbl_script_desc)

        self.edit_script_steps = QPlainTextEdit()
        self.edit_script_steps.setPlaceholderText("步骤将在这里显示。")
        self.edit_script_steps.setMinimumHeight(140)
        layout.addWidget(self.edit_script_steps)

        row = QHBoxLayout()
        for text, slot, primary in [
            ("新增剧本", self._add_script, False),
            ("编辑剧本", self._edit_script, False),
            ("删除剧本", self._delete_script, False),
            ("保存步骤", self._save_script_steps, False),
            ("执行剧本", self._run_selected_script, True),
        ]:
            button = QPushButton(text)
            button.setObjectName("lab_primary" if primary else "lab_secondary")
            button.clicked.connect(slot)
            row.addWidget(button)
        layout.addLayout(row)
        return card

    def _build_camera_card(self) -> QGroupBox:
        card = QGroupBox("USB 相机识别与调试")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)

        row = QHBoxLayout()
        self.combo_camera = QComboBox()
        self.combo_camera.setMinimumWidth(180)
        self.edit_scan_max = QLineEdit()
        self.edit_scan_max.setFixedWidth(60)
        btn_scan = QPushButton("扫描相机")
        btn_scan.setObjectName("lab_secondary")
        btn_scan.clicked.connect(self._scan_cameras)
        self.btn_camera_toggle = QPushButton("连接预览")
        self.btn_camera_toggle.setObjectName("lab_primary")
        self.btn_camera_toggle.clicked.connect(self._toggle_camera_preview)
        btn_snapshot = QPushButton("抓拍保存")
        btn_snapshot.setObjectName("lab_secondary")
        btn_snapshot.clicked.connect(self._save_camera_snapshot)
        row.addWidget(QLabel("相机"))
        row.addWidget(self.combo_camera, 1)
        row.addWidget(QLabel("扫描上限"))
        row.addWidget(self.edit_scan_max)
        row.addWidget(btn_scan)
        row.addWidget(self.btn_camera_toggle)
        row.addWidget(btn_snapshot)
        layout.addLayout(row)

        self.lbl_camera_meta = QLabel("等待扫描 USB 相机")
        layout.addWidget(self.lbl_camera_meta)

        self.lbl_camera_preview = QLabel("暂无视频流")
        self.lbl_camera_preview.setObjectName("camera_preview")
        self.lbl_camera_preview.setMinimumSize(360, 250)
        self.lbl_camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_camera_preview)
        return card

    def _build_remote_card(self) -> QGroupBox:
        card = QGroupBox("遥控器模拟器")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)

        top = QHBoxLayout()
        self.chk_remote_edit_mode = QCheckBox("布局编辑模式")
        self.chk_remote_edit_mode.toggled.connect(self._toggle_remote_edit_mode)
        btn_add = QPushButton("新增按键")
        btn_add.setObjectName("lab_secondary")
        btn_add.clicked.connect(self._add_remote_button)
        btn_edit = QPushButton("编辑选中")
        btn_edit.setObjectName("lab_secondary")
        btn_edit.clicked.connect(self._edit_selected_remote_button)
        btn_delete = QPushButton("删除选中")
        btn_delete.setObjectName("lab_secondary")
        btn_delete.clicked.connect(self._delete_selected_remote_button)
        btn_reset = QPushButton("重置布局")
        btn_reset.setObjectName("lab_secondary")
        btn_reset.clicked.connect(self._reset_remote_layout)
        top.addWidget(self.chk_remote_edit_mode)
        top.addStretch(1)
        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_delete)
        top.addWidget(btn_reset)
        layout.addLayout(top)

        self.lbl_remote_hint = QLabel("默认点击按键会直接发送，勾选布局编辑模式后可拖动和选择。")
        self.lbl_remote_hint.setWordWrap(True)
        layout.addWidget(self.lbl_remote_hint)

        self.remote_canvas = QFrame()
        self.remote_canvas.setObjectName("remote_canvas")
        self.remote_canvas.setFixedSize(300, 470)
        layout.addWidget(self.remote_canvas, 0, Qt.AlignmentFlag.AlignHCenter)
        return card

    def _build_log_card(self) -> QGroupBox:
        card = QGroupBox("联调事件")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)
        self.text_log = QPlainTextEdit()
        self.text_log.setObjectName("device_log")
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumBlockCount(500)
        layout.addWidget(self.text_log)
        return card

    def _load_profile_to_ui(self):
        serial_data = self._profile.get("serial", {})
        self.combo_baud.setCurrentText(str(serial_data.get("baudrate", 115200)))
        self.chk_newline.setChecked(bool(serial_data.get("newline", True)))
        self.chk_auto_su.setChecked(bool(serial_data.get("auto_su", False)))

        camera_data = self._profile.get("camera", {})
        self.edit_scan_max.setText(str(camera_data.get("scan_max_index", 5)))
        self.chk_remote_edit_mode.setChecked(bool(self._profile.get("remote", {}).get("edit_mode", False)))
        self._refresh_command_lists()
        self._refresh_projects()
        self._render_remote_buttons()

    def _refresh_command_lists(self):
        self._fill_command_list(self.list_quick_settings, self._profile.get("quick_settings", []))
        self._fill_command_list(self.list_shortcuts, self._profile.get("shortcuts", []))
        if self.list_quick_settings.count() > 0:
            self.list_quick_settings.setCurrentRow(0)
        if self.list_shortcuts.count() > 0:
            self.list_shortcuts.setCurrentRow(0)

    def _fill_command_list(self, widget: QListWidget, items: List[Dict[str, Any]]):
        widget.clear()
        for item in items:
            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            widget.addItem(list_item)

    def _sync_command_description(self, widget: QListWidget, label_attr: str):
        label: QLabel = getattr(self, label_attr)
        item = widget.currentItem()
        if item is None:
            label.setText("请选择一项")
            return
        data = self._find_item_by_id(self._get_list_source_for_widget(widget), item.data(Qt.ItemDataRole.UserRole))
        if not data:
            label.setText("请选择一项")
            return
        commands_text = " | ".join(data.get("commands", [])[:3])
        label.setText(f"{data.get('description', '无说明')}\n指令: {commands_text}")

    def _get_list_source_for_widget(self, widget: QListWidget) -> List[Dict[str, Any]]:
        if widget is self.list_quick_settings:
            return self._profile.get("quick_settings", [])
        return self._profile.get("shortcuts", [])

    def _refresh_projects(self):
        current_name = self.combo_project.currentText()
        self.combo_project.blockSignals(True)
        self.combo_project.clear()
        for project in self._profile.get("projects", []):
            self.combo_project.addItem(project["name"], project["id"])
        index = self.combo_project.findText(current_name)
        self.combo_project.setCurrentIndex(index if index >= 0 else 0)
        self.combo_project.blockSignals(False)
        self._refresh_scripts()

    def _refresh_scripts(self):
        self.list_scripts.clear()
        project = self._current_project()
        if not project:
            self.lbl_script_desc.setText("请先创建项目")
            self.edit_script_steps.clear()
            return
        for script in project.get("scripts", []):
            item = QListWidgetItem(script["name"])
            item.setData(Qt.ItemDataRole.UserRole, script["id"])
            self.list_scripts.addItem(item)
        if self.list_scripts.count() > 0:
            self.list_scripts.setCurrentRow(0)
        else:
            self.lbl_script_desc.setText("当前项目还没有联调剧本")
            self.edit_script_steps.clear()

    def _sync_script_details(self):
        script = self._current_script()
        if not script:
            self.lbl_script_desc.setText("请选择剧本")
            self.edit_script_steps.clear()
            return
        self.lbl_script_desc.setText(script.get("description", "无说明"))
        self.edit_script_steps.setPlainText("\n".join(script.get("steps", [])))

    def _refresh_serial_ports(self):
        ports: List[str] = []
        try:
            import serial.tools.list_ports

            ports = [port.device for port in serial.tools.list_ports.comports()]
        except Exception as exc:
            self._log(f"串口扫描失败: {exc}", "ERROR")
        self.combo_port.clear()
        self.combo_port.addItems(ports or ["（未发现串口）"])
        last_port = self._profile.get("serial", {}).get("last_port", "")
        index = self.combo_port.findText(last_port)
        if index >= 0:
            self.combo_port.setCurrentIndex(index)

    def _toggle_serial_connection(self):
        if self._serial and getattr(self._serial, "is_open", False):
            self._disconnect_serial()
        else:
            self._connect_serial()

    def _connect_serial(self):
        port = self.combo_port.currentText().strip()
        if not port or "（" in port:
            QMessageBox.warning(self, "提示", "请先选择有效串口")
            return
        try:
            import serial

            self._serial = serial.Serial(port=port, baudrate=int(self.combo_baud.currentText()), timeout=0.1)
        except Exception as exc:
            QMessageBox.critical(self, "串口连接失败", str(exc))
            self._log(f"串口连接失败: {exc}", "ERROR")
            return

        self._profile.setdefault("serial", {})["last_port"] = port
        self._profile["serial"]["baudrate"] = int(self.combo_baud.currentText())
        self._profile["serial"]["newline"] = self.chk_newline.isChecked()
        self._profile["serial"]["auto_su"] = self.chk_auto_su.isChecked()
        self._persist_profile()

        self.btn_serial_connect.setText("断开串口")
        self.lbl_serial_chip.setText(f"串口在线: {port}")
        self._log(f"串口已连接: {port} @ {self.combo_baud.currentText()}")
        self._reader_thread = SerialReaderThread(self._serial)
        self._reader_thread.data_received.connect(self._on_serial_data_received)
        self._reader_thread.error_occurred.connect(self._on_serial_error)
        self._reader_thread.disconnected.connect(self._on_serial_disconnected)
        self._reader_thread.start()
        if self.chk_auto_su.isChecked():
            self._queue_commands([( "su", 0.0, "连接自动初始化" )])

    def _disconnect_serial(self):
        self._queue_timer.stop()
        self._command_queue.clear()
        if self._reader_thread:
            self._reader_thread.stop()
            self._reader_thread = None
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        self.btn_serial_connect.setText("连接串口")
        self.lbl_serial_chip.setText("串口未连接")
        self._log("串口已断开")

    def _on_serial_data_received(self, data: bytes):
        text = data.decode("utf-8", errors="ignore")
        if text:
            self.serial_terminal.appendPlainText(text.rstrip())

    def _on_serial_error(self, message: str):
        self._log(f"串口读取异常: {message}", "ERROR")

    def _on_serial_disconnected(self):
        if self._serial and getattr(self._serial, "is_open", False):
            return
        self.btn_serial_connect.setText("连接串口")
        self.lbl_serial_chip.setText("串口未连接")

    def _send_manual_serial_command(self):
        command = self.edit_serial_cmd.text().strip()
        if not command:
            return
        self._send_serial_command(command, source="手工发送")
        self.edit_serial_cmd.clear()

    def _send_serial_command(self, command: str, source: str = "串口发送") -> bool:
        if not self._serial or not getattr(self._serial, "is_open", False):
            self._log("串口未连接，无法发送指令", "ERROR")
            return False
        payload = command + ("\r\n" if self.chk_newline.isChecked() else "")
        try:
            self._serial.write(payload.encode("utf-8", errors="ignore"))
            self.serial_terminal.appendPlainText(f">>> {command}")
            self._log(f"{source}: {command}")
            return True
        except Exception as exc:
            self._log(f"串口发送失败: {exc}", "ERROR")
            return False

    def _queue_commands(self, steps: List[Tuple[Optional[str], float, str]]):
        self._command_queue.extend(steps)
        if not self._queue_timer.isActive():
            self._process_next_queue_item()

    def _process_next_queue_item(self):
        if not self._command_queue:
            self._log("执行队列完成")
            return
        command, delay_seconds, source = self._command_queue.pop(0)
        if command:
            self._send_serial_command(command, source=source)
        self._queue_timer.start(max(0, int(delay_seconds * 1000)))

    def _scan_cameras(self):
        max_index_text = self.edit_scan_max.text().strip() or "5"
        try:
            max_index = max(0, int(max_index_text))
        except ValueError:
            QMessageBox.warning(self, "提示", "扫描上限必须是整数")
            return
        self._profile.setdefault("camera", {})["scan_max_index"] = max_index
        self._persist_profile()

        found: List[Tuple[int, str]] = []
        for index in range(max_index + 1):
            cap = self._open_camera(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    found.append((index, f"USB Camera {index} [{frame.shape[1]}x{frame.shape[0]}]"))
            cap.release()

        self.combo_camera.clear()
        if not found:
            self.combo_camera.addItem("（未发现相机）", -1)
            self.lbl_camera_meta.setText("未识别到可用 USB 相机")
            self._log("未识别到可用 USB 相机", "WARN")
            return
        for index, name in found:
            self.combo_camera.addItem(name, index)
        last_index = int(self._profile.get("camera", {}).get("last_index", 0))
        selected = next((row for row, item in enumerate(found) if item[0] == last_index), 0)
        self.combo_camera.setCurrentIndex(selected)
        self.lbl_camera_meta.setText(f"已发现 {len(found)} 路 USB 相机")
        self._log(f"扫描到 USB 相机: {', '.join(name for _, name in found)}")

    def _toggle_camera_preview(self):
        if self._camera_capture is not None:
            self._stop_camera_preview()
        else:
            self._start_camera_preview()

    def _start_camera_preview(self):
        camera_index = self.combo_camera.currentData()
        if camera_index is None or int(camera_index) < 0:
            QMessageBox.warning(self, "提示", "请先扫描并选择有效相机")
            return
        capture = self._open_camera(int(camera_index))
        if not capture.isOpened():
            QMessageBox.warning(self, "提示", "相机打开失败")
            return
        self._camera_capture = capture
        self._profile.setdefault("camera", {})["last_index"] = int(camera_index)
        self._persist_profile()
        interval = int(self._profile.get("camera", {}).get("preview_interval_ms", 33))
        self._camera_timer.start(max(15, interval))
        self.btn_camera_toggle.setText("断开预览")
        self.lbl_camera_chip.setText(f"相机在线: {self.combo_camera.currentText()}")
        self._camera_frame_counter = 0
        self._camera_fps_anchor = time.time()
        self._log(f"相机预览已连接: {self.combo_camera.currentText()}")

    def _stop_camera_preview(self):
        self._camera_timer.stop()
        if self._camera_capture is not None:
            self._camera_capture.release()
            self._camera_capture = None
        self.btn_camera_toggle.setText("连接预览")
        self.lbl_camera_chip.setText("相机未连接")
        self.lbl_camera_preview.setText("暂无视频流")
        self.lbl_camera_preview.setPixmap(QPixmap())
        self._log("相机预览已断开")

    def _update_camera_frame(self):
        if self._camera_capture is None:
            return
        ret, frame = self._camera_capture.read()
        if not ret or frame is None:
            self.lbl_camera_meta.setText("视频流读取失败")
            return
        self._camera_frame_counter += 1
        now = time.time()
        elapsed = max(now - self._camera_fps_anchor, 0.001)
        fps = self._camera_frame_counter / elapsed
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.lbl_camera_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.lbl_camera_preview.setPixmap(pixmap)
        self.lbl_camera_meta.setText(f"分辨率 {frame.shape[1]}x{frame.shape[0]} | 预览 FPS {fps:.1f}")

    def _save_camera_snapshot(self):
        if self._camera_capture is None:
            QMessageBox.warning(self, "提示", "请先连接相机预览")
            return
        ret, frame = self._camera_capture.read()
        if not ret or frame is None:
            QMessageBox.warning(self, "提示", "当前帧获取失败")
            return
        project_root = self._config_mgr.get_project_root() if self._config_mgr else os.getcwd()
        rel_dir = self._profile.get("camera", {}).get("snapshot_dir", "reports/device_lab_snapshots")
        snapshot_dir = self._store.resolve_path(rel_dir, project_root)
        os.makedirs(snapshot_dir, exist_ok=True)
        file_path = os.path.join(snapshot_dir, f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        cv2.imwrite(file_path, frame)
        self._log(f"相机抓拍已保存: {file_path}")
        QMessageBox.information(self, "抓拍成功", file_path)

    def _open_camera(self, index: int):
        logger = getattr(cv2, "utils", None)
        logging_api = getattr(logger, "logging", None)
        if logging_api is None:
            capture = cv2.VideoCapture(index)
            if capture.isOpened():
                return capture
            capture.release()
            return cv2.VideoCapture(index, cv2.CAP_DSHOW)

        old_level = logging_api.getLogLevel()
        logging_api.setLogLevel(logging_api.LOG_LEVEL_SILENT)
        try:
            capture = cv2.VideoCapture(index)
            if capture.isOpened():
                return capture
            capture.release()
            return cv2.VideoCapture(index, cv2.CAP_DSHOW)
        finally:
            logging_api.setLogLevel(old_level)

    def _render_remote_buttons(self):
        for button in self._remote_buttons.values():
            button.deleteLater()
        self._remote_buttons.clear()
        self._selected_remote_id = None
        for data in self._profile.get("remote", {}).get("buttons", []):
            button = DraggableRemoteButton(data["id"], self.chk_remote_edit_mode.isChecked, self.remote_canvas)
            button.setText(data["name"])
            button.setGeometry(data.get("x", 80), data.get("y", 80), data.get("w", 76), data.get("h", 34))
            button.activated.connect(self._on_remote_button_activated)
            button.moved.connect(self._on_remote_button_moved)
            button.selected.connect(self._select_remote_button)
            button.show()
            self._remote_buttons[data["id"]] = button

    def _toggle_remote_edit_mode(self, checked: bool):
        self._profile.setdefault("remote", {})["edit_mode"] = checked
        self._persist_profile()
        self.lbl_remote_hint.setText(
            "编辑模式下可拖动按键并选择后编辑。"
            if checked else
            "默认点击按键会直接发送，勾选布局编辑模式后可拖动和选择。"
        )

    def _on_remote_button_activated(self, button_id: str):
        button = self._find_item_by_id(self._profile.get("remote", {}).get("buttons", []), button_id)
        if not button:
            return
        steps = self._resolve_button_steps(button)
        if not steps:
            self._log(f"按键 {button.get('name')} 未绑定有效指令", "WARN")
            return
        self._queue_commands(steps)

    def _resolve_button_steps(self, button: Dict[str, Any]) -> List[Tuple[Optional[str], float, str]]:
        if button.get("binding_type") == "shortcut":
            shortcut = self._find_item_by_name(self._profile.get("shortcuts", []), button.get("binding_value", ""))
            if not shortcut:
                return []
            return [(command, 0.25, f"遥控快捷 {button['name']}") for command in shortcut.get("commands", [])]
        command = button.get("binding_value", "").strip()
        return [(command, 0.25, f"遥控按键 {button['name']}")] if command else []

    def _on_remote_button_moved(self, button_id: str, x: int, y: int):
        button = self._find_item_by_id(self._profile.get("remote", {}).get("buttons", []), button_id)
        if not button:
            return
        button["x"] = x
        button["y"] = y
        self._persist_profile()

    def _select_remote_button(self, button_id: str):
        self._selected_remote_id = button_id
        for current_id, widget in self._remote_buttons.items():
            widget.setProperty("selected", current_id == button_id)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _add_remote_button(self):
        dialog = RemoteButtonDialog(self._profile.get("shortcuts", []), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        data.update({
            "id": self._store.make_id("remote"),
            "x": 110,
            "y": 420,
            "w": 76,
            "h": 34,
        })
        self._profile.setdefault("remote", {}).setdefault("buttons", []).append(data)
        self._persist_profile()
        self._render_remote_buttons()

    def _edit_selected_remote_button(self):
        button = self._find_item_by_id(self._profile.get("remote", {}).get("buttons", []), self._selected_remote_id)
        if not button:
            QMessageBox.information(self, "提示", "请先在编辑模式下选择一个按键")
            return
        dialog = RemoteButtonDialog(self._profile.get("shortcuts", []), button, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dialog.get_data()
        button.update(updated)
        self._persist_profile()
        self._render_remote_buttons()
        self._select_remote_button(button["id"])

    def _delete_selected_remote_button(self):
        if not self._selected_remote_id:
            QMessageBox.information(self, "提示", "请先选择一个按键")
            return
        buttons = self._profile.get("remote", {}).get("buttons", [])
        buttons[:] = [item for item in buttons if item["id"] != self._selected_remote_id]
        self._persist_profile()
        self._render_remote_buttons()

    def _reset_remote_layout(self):
        reply = QMessageBox.question(self, "重置布局", "确定恢复默认遥控器布局吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        from core.device_lab_store import DEFAULT_REMOTE_BUTTONS

        self._profile.setdefault("remote", {})["buttons"] = [dict(item) for item in DEFAULT_REMOTE_BUTTONS]
        self._persist_profile()
        self._render_remote_buttons()

    def _current_project(self) -> Optional[Dict[str, Any]]:
        project_id = self.combo_project.currentData()
        return self._find_item_by_id(self._profile.get("projects", []), project_id)

    def _current_script(self) -> Optional[Dict[str, Any]]:
        current = self.list_scripts.currentItem()
        if current is None:
            return None
        project = self._current_project()
        if not project:
            return None
        return self._find_item_by_id(project.get("scripts", []), current.data(Qt.ItemDataRole.UserRole))

    def _add_project(self):
        name, ok = QInputDialog.getText(self, "新增项目", "项目名")
        if not ok or not name.strip():
            return
        self._profile.setdefault("projects", []).append({
            "id": self._store.make_id("project"),
            "name": name.strip(),
            "description": "",
            "scripts": [],
        })
        self._persist_profile()
        self._refresh_projects()
        self.combo_project.setCurrentText(name.strip())

    def _rename_project(self):
        project = self._current_project()
        if not project:
            return
        name, ok = QInputDialog.getText(self, "重命名项目", "项目名", text=project["name"])
        if not ok or not name.strip():
            return
        project["name"] = name.strip()
        self._persist_profile()
        self._refresh_projects()
        self.combo_project.setCurrentText(name.strip())

    def _delete_project(self):
        project = self._current_project()
        if not project:
            return
        reply = QMessageBox.question(self, "删除项目", f"确定删除项目 {project['name']} 吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        projects = self._profile.get("projects", [])
        projects[:] = [item for item in projects if item["id"] != project["id"]]
        self._persist_profile()
        self._refresh_projects()

    def _add_script(self):
        project = self._current_project()
        if not project:
            QMessageBox.information(self, "提示", "请先创建项目")
            return
        dialog = ScriptDialog("新增联调剧本", parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        data["id"] = self._store.make_id("script")
        project.setdefault("scripts", []).append(data)
        self._persist_profile()
        self._refresh_scripts()

    def _edit_script(self):
        script = self._current_script()
        if not script:
            return
        dialog = ScriptDialog("编辑联调剧本", script, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        script.update(dialog.get_data())
        self._persist_profile()
        self._refresh_scripts()

    def _delete_script(self):
        project = self._current_project()
        script = self._current_script()
        if not project or not script:
            return
        reply = QMessageBox.question(self, "删除剧本", f"确定删除剧本 {script['name']} 吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        scripts = project.get("scripts", [])
        scripts[:] = [item for item in scripts if item["id"] != script["id"]]
        self._persist_profile()
        self._refresh_scripts()

    def _save_script_steps(self):
        script = self._current_script()
        if not script:
            return
        script["steps"] = [line.strip() for line in self.edit_script_steps.toPlainText().splitlines() if line.strip()]
        self._persist_profile()
        self._log(f"剧本已保存: {script['name']}")

    def _run_selected_script(self):
        script = self._current_script()
        if not script:
            return
        steps = self._parse_script_steps(script.get("steps", []))
        if not steps:
            QMessageBox.warning(self, "提示", "当前剧本没有可执行步骤")
            return
        self._log(f"开始执行联调剧本: {script['name']}")
        self._queue_commands(steps)

    def _parse_script_steps(self, raw_steps: List[str]) -> List[Tuple[Optional[str], float, str]]:
        steps: List[Tuple[Optional[str], float, str]] = []
        for line in raw_steps:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("wait:"):
                try:
                    seconds = float(line.split(":", 1)[1].strip())
                except ValueError:
                    seconds = 0.5
                steps.append((None, seconds, f"等待 {seconds:.1f}s"))
                continue
            if line.startswith("setting:"):
                name = line.split(":", 1)[1].strip()
                item = self._find_item_by_name(self._profile.get("quick_settings", []), name)
                if item:
                    steps.extend((command, 0.25, f"快捷配置 {name}") for command in item.get("commands", []))
                continue
            if line.startswith("shortcut:"):
                name = line.split(":", 1)[1].strip()
                item = self._find_item_by_name(self._profile.get("shortcuts", []), name)
                if item:
                    steps.extend((command, 0.25, f"快捷指令 {name}") for command in item.get("commands", []))
                continue
            steps.append((line, 0.25, "联调剧本"))
        return steps

    def _add_quick_setting(self):
        self._edit_or_add_command_item("quick_settings", None, "新增快捷配置")

    def _edit_quick_setting(self):
        item = self._current_command_item(self.list_quick_settings, "quick_settings")
        if item:
            self._edit_or_add_command_item("quick_settings", item, "编辑快捷配置")

    def _delete_quick_setting(self):
        self._delete_command_item(self.list_quick_settings, "quick_settings", "快捷配置")

    def _run_selected_quick_setting(self):
        item = self._current_command_item(self.list_quick_settings, "quick_settings")
        if not item:
            return
        self._queue_commands([(command, 0.25, f"快捷配置 {item['name']}") for command in item.get("commands", [])])

    def _add_shortcut(self):
        self._edit_or_add_command_item("shortcuts", None, "新增快捷指令")

    def _edit_shortcut(self):
        item = self._current_command_item(self.list_shortcuts, "shortcuts")
        if item:
            self._edit_or_add_command_item("shortcuts", item, "编辑快捷指令")

    def _delete_shortcut(self):
        self._delete_command_item(self.list_shortcuts, "shortcuts", "快捷指令")

    def _run_selected_shortcut(self):
        item = self._current_command_item(self.list_shortcuts, "shortcuts")
        if not item:
            return
        self._queue_commands([(command, 0.25, f"快捷指令 {item['name']}") for command in item.get("commands", [])])

    def _edit_or_add_command_item(self, section: str, item: Optional[Dict[str, Any]], title: str):
        dialog = CommandItemDialog(title, item, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        target = self._profile.setdefault(section, [])
        if item is None:
            data["id"] = self._store.make_id("setting" if section == "quick_settings" else "shortcut")
            target.append(data)
        else:
            item.update(data)
        self._persist_profile()
        self._refresh_command_lists()
        self._render_remote_buttons()

    def _delete_command_item(self, widget: QListWidget, section: str, label: str):
        current = widget.currentItem()
        if current is None:
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        target = self._profile.get(section, [])
        target[:] = [item for item in target if item["id"] != item_id]
        self._persist_profile()
        self._refresh_command_lists()
        self._render_remote_buttons()
        self._log(f"已删除{label}")

    def _current_command_item(self, widget: QListWidget, section: str) -> Optional[Dict[str, Any]]:
        current = widget.currentItem()
        if current is None:
            return None
        return self._find_item_by_id(self._profile.get(section, []), current.data(Qt.ItemDataRole.UserRole))

    def _find_item_by_id(self, items: List[Dict[str, Any]], item_id: Optional[str]) -> Optional[Dict[str, Any]]:
        for item in items:
            if item.get("id") == item_id:
                return item
        return None

    def _find_item_by_name(self, items: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
        for item in items:
            if item.get("name") == name:
                return item
        return None

    def _persist_profile(self):
        self._store.set_all(self._profile)
        self._store.save()

    def _log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.text_log.appendPlainText(f"[{timestamp}] {level:<5} {message}")
        if self._log_panel is not None:
            panel_level = {
                "INFO": "INFO",
                "WARN": "WARNING",
                "ERROR": "ERROR",
            }.get(level, "INFO")
            self._log_panel.append_log(message, panel_level)

    def cleanup(self):
        self._stop_camera_preview()
        self._disconnect_serial()
