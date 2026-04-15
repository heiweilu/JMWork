# -*- coding: utf-8 -*-
"""设备联调台页面。"""

import ast
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PyQt6.QtCore import QEvent, QPoint, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QDesktopServices, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.device_lab_store import DeviceLabStore
from core.image_compare import compare_with_reference_set, detect_green_screen
from workers.serial_worker import SerialReaderThread


def _load_serial_quick_cmds() -> list:
    """从 serial_quick_cmds.json 加载所有快捷指令，返回 [(显示名, 命令)] 列表。"""
    import json
    from pathlib import Path
    cfg_path = Path(__file__).parent.parent.parent / 'config' / 'serial_quick_cmds.json'
    result = []
    try:
        if not cfg_path.exists():
            return result
        with cfg_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        # 自定义指令
        for item in data.get('custom_commands', []):
            name = item.get('name', '')
            cmd = item.get('cmd', '')
            if name and cmd:
                result.append((f"[自定义] {name}", cmd))
        # 固定板块
        for sec_key, sec in data.get('fixed_sections', {}).items():
            sec_title = sec.get('title', sec_key)
            for cmd_item in sec.get('commands', []):
                if isinstance(cmd_item, list) and len(cmd_item) >= 2:
                    result.append((f"[{sec_title}] {cmd_item[0]}", cmd_item[1]))
                elif isinstance(cmd_item, dict):
                    n = cmd_item.get('name', '')
                    c = cmd_item.get('cmd', '')
                    if n and c:
                        result.append((f"[{sec_title}] {n}", c))
        # 动态板块
        for sec in data.get('dynamic_sections', []):
            sec_title = sec.get('title', '')
            for cmd_item in sec.get('commands', []):
                if isinstance(cmd_item, dict):
                    n = cmd_item.get('name', '')
                    c = cmd_item.get('cmd', '')
                    if n and c:
                        result.append((f"[{sec_title}] {n}", c))
    except Exception:
        pass
    return result


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
QScrollArea#camera_preview_scroll {
    background: #0f172a;
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


def _parse_preview_roi_text(roi_text: str) -> Optional[Tuple[float, float, float, float]]:
    text = (roi_text or "").strip()
    if not text:
        return None
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 4:
        return None
    try:
        values = [float(part) for part in parts]
    except ValueError:
        return None
    if all(0.0 <= value <= 100.0 for value in values) and any(value > 1.0 for value in values):
        values = [value / 100.0 for value in values]
    x, y, w, h = values
    if w <= 0.0 or h <= 0.0 or x < 0.0 or y < 0.0 or x + w > 1.0 or y + h > 1.0:
        return None
    return x, y, w, h


def _build_green_preview_pixmap(
    roi_text: str,
    green_ratio_threshold: float,
    green_area_threshold: float,
    green_check_frames: int,
    green_margin: int,
    saturation_threshold: int,
    value_threshold: int,
) -> QPixmap:
    width = 360
    height = 180
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#f8fafc"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    frame_x, frame_y, frame_w, frame_h = 16, 18, 180, 104
    painter.setPen(QPen(QColor("#cbd5e1"), 1))
    painter.drawRoundedRect(frame_x, frame_y, frame_w, frame_h, 8, 8)
    for offset in range(1, 4):
        x = frame_x + int(frame_w * offset / 4)
        y = frame_y + int(frame_h * offset / 4)
        painter.drawLine(x, frame_y, x, frame_y + frame_h)
        painter.drawLine(frame_x, y, frame_x + frame_w, y)

    roi = _parse_preview_roi_text(roi_text)
    if roi is None and roi_text.strip():
        painter.setPen(QPen(QColor("#dc2626"), 2))
        painter.drawText(frame_x, frame_y + frame_h + 18, "ROI 格式无效，需填 x,y,w,h，范围 0-1 或 0-100")
    elif roi is None:
        painter.setPen(QPen(QColor("#0f172a"), 1))
        painter.drawText(frame_x, frame_y + frame_h + 18, "留空表示全图检测")
    else:
        roi_x, roi_y, roi_w, roi_h = roi
        rx = frame_x + int(frame_w * roi_x)
        ry = frame_y + int(frame_h * roi_y)
        rw = max(8, int(frame_w * roi_w))
        rh = max(8, int(frame_h * roi_h))
        painter.fillRect(rx, ry, rw, rh, QColor(34, 197, 94, 70))
        painter.setPen(QPen(QColor("#16a34a"), 2))
        painter.drawRect(rx, ry, rw, rh)
        painter.drawText(frame_x, frame_y + frame_h + 18, f"ROI: x={roi_x:.2f}, y={roi_y:.2f}, w={roi_w:.2f}, h={roi_h:.2f}")

    text_x = 214
    painter.setPen(QPen(QColor("#0f172a"), 1))
    painter.drawText(text_x, 28, "绿屏检测参数预览")
    painter.drawText(text_x, 56, f"绿像素占比阈值: {green_ratio_threshold:.2f}")
    painter.drawText(text_x, 76, f"最大连通域阈值: {green_area_threshold:.2f}")
    painter.drawText(text_x, 96, f"连续命中帧数: {int(green_check_frames)}")
    painter.drawText(text_x, 116, f"绿色通道领先值: {int(green_margin)}")
    painter.drawText(text_x, 136, f"饱和度/亮度下限: {int(saturation_threshold)} / {int(value_threshold)}")
    painter.drawText(text_x, 160, "建议先缩 ROI，再逐步收紧占比和连通域阈值")
    painter.end()
    return pixmap


def _green_help_text() -> str:
    return (
        "ROI 区域按 x,y,w,h 填写，支持 0-1 或 0-100 百分比；留空表示全图。\n"
        "绿像素占比阈值越高，要求绿色区域越大；最大连通域阈值越高，要求连续整片绿区越大。\n"
        "绿色通道领先值、饱和度下限、亮度下限用于过滤偏灰、偏暗或杂色噪声；连续命中帧数用于过滤视频瞬时闪帧。"
    )


def _cv_image_to_pixmap(image, max_width: int = 680, max_height: int = 320) -> QPixmap:
    if image is None:
        pixmap = QPixmap(max_width, max_height)
        pixmap.fill(QColor("#f8fafc"))
        return pixmap
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    qimage = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage).scaled(
        max_width,
        max_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )


def _set_form_row_visible(form: QFormLayout, field, visible: bool):
    label = form.labelForField(field)
    if label is not None:
        label.setVisible(visible)
    field.setVisible(visible)


def _green_preset_values(preset_key: str) -> Dict[str, Any]:
    presets = {
        "rookie": {
            "green_ratio_threshold": 0.22,
            "green_area_threshold": 0.10,
            "green_margin": 18,
            "green_saturation_threshold": 35,
            "green_value_threshold": 30,
            "green_check_frames": 2,
            "green_check_interval_ms": 200,
        },
        "balanced": {
            "green_ratio_threshold": 0.30,
            "green_area_threshold": 0.18,
            "green_margin": 25,
            "green_saturation_threshold": 45,
            "green_value_threshold": 40,
            "green_check_frames": 3,
            "green_check_interval_ms": 250,
        },
        "strict": {
            "green_ratio_threshold": 0.40,
            "green_area_threshold": 0.28,
            "green_margin": 40,
            "green_saturation_threshold": 75,
            "green_value_threshold": 65,
            "green_check_frames": 3,
            "green_check_interval_ms": 300,
        },
    }
    return dict(presets.get(preset_key, presets["balanced"]))


def _build_green_analysis_text(detection: Optional[Dict[str, Any]], check_frames: int) -> str:
    if not detection:
        return (
            "调参顺序建议:\n"
            "1. 先缩 ROI，只框住投影画面本体，不要把黑边和外壳也算进去。\n"
            "2. 先用‘新手宽松’，确认能命中明显绿屏后，再逐步提高阈值。\n"
            "3. 预览页只分析当前单帧；连续命中帧数只在剧本运行时生效。"
        )

    ratio = float(detection.get("green_ratio", 0.0))
    area = float(detection.get("largest_component_ratio", 0.0))
    excess = float(detection.get("mean_green_excess", 0.0))
    thresholds = detection.get("thresholds", {})
    ratio_threshold = float(thresholds.get("green_ratio", 0.0))
    area_threshold = float(thresholds.get("area_ratio", 0.0))
    margin_threshold = int(thresholds.get("green_margin", 0))
    saturation_threshold = int(thresholds.get("saturation_threshold", 0))
    value_threshold = int(thresholds.get("value_threshold", 0))

    lines = []
    if detection.get("detected", False):
        lines.append("当前单帧判定: 已命中绿屏。")
    else:
        lines.append("当前单帧判定: 未命中绿屏。")

    lines.append(
        f"核心指标: 绿像素占比 {ratio:.4f} / 阈值 {ratio_threshold:.4f}，最大连通域 {area:.4f} / 阈值 {area_threshold:.4f}。"
    )

    failed_reasons = []
    if ratio < ratio_threshold:
        failed_reasons.append("绿像素占比还没过线，说明绿色覆盖面积不够大，或 ROI 把太多非绿色区域也算进来了。")
    if area < area_threshold:
        failed_reasons.append("最大连通域还没过线，说明绿色区域被黑边、文字、高亮或反光切碎了。")
    if excess < max(0.08, margin_threshold / 255.0 * 0.7):
        failed_reasons.append("绿色领先度偏低，绿色虽然多，但和红蓝通道拉不开差距。")

    if failed_reasons:
        lines.append("未命中原因:")
        for item in failed_reasons:
            lines.append(f"- {item}")

    suggestions = []
    if ratio < ratio_threshold:
        suggestions.append("先把 ROI 缩到屏幕主体，再把‘绿像素占比阈值’往下调到接近当前值上方一点。")
    if area < area_threshold:
        suggestions.append("把‘最大连通域阈值’调低一些；你图里这种大面积绿色但未命中，通常就是这个阈值偏高。")
    if excess < max(0.08, margin_threshold / 255.0 * 0.7):
        suggestions.append("把‘绿色通道领先值’先降到 15-25，再观察遮罩是否更完整。")
    if saturation_threshold >= 70 or value_threshold >= 60:
        suggestions.append("如果画面发灰或偏暗，可把‘饱和度下限/亮度下限’适当下调，先保证能抓到绿区。")
    if not suggestions and detection.get("detected", False):
        suggestions.append("当前参数已经能命中；下一步可只略微提高阈值，避免正常彩色画面误判。")

    lines.append("调参建议:")
    for item in suggestions[:3]:
        lines.append(f"- {item}")
    lines.append(f"剧本运行时还会叠加‘连续命中帧数={int(check_frames)}’判断；预览只看单帧。")
    return "\n".join(lines)


def _compose_source_and_overlay(source_image, overlay_image):
    if source_image is None:
        return overlay_image
    if overlay_image is None:
        return source_image
    source = source_image.copy()
    overlay = overlay_image.copy()
    height = 280
    source_width = max(1, int(source.shape[1] * height / max(1, source.shape[0])))
    overlay_width = max(1, int(overlay.shape[1] * height / max(1, overlay.shape[0])))
    source = cv2.resize(source, (source_width, height), interpolation=cv2.INTER_AREA)
    overlay = cv2.resize(overlay, (overlay_width, height), interpolation=cv2.INTER_AREA)
    source = cv2.copyMakeBorder(source, 0, 36, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    overlay = cv2.copyMakeBorder(overlay, 0, 36, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(source, "Source", (10, height + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (15, 23, 42), 2, cv2.LINE_AA)
    cv2.putText(overlay, "Mask Preview", (10, height + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (15, 23, 42), 2, cv2.LINE_AA)
    gap = cv2.copyMakeBorder(
        cv2.resize(source[:, :1], (12, source.shape[0]), interpolation=cv2.INTER_NEAREST),
        0,
        0,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )
    return cv2.hconcat([source, gap, overlay])


class CommandItemDialog(QDialog):
    def __init__(self, title: str, data: Optional[Dict[str, Any]] = None, allow_camera_actions: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1240, 860)

        values = data or {}
        self._allow_camera_actions = allow_camera_actions
        self._green_preview_image = None
        self._green_preview_path = values.get("green_preview_image", "")
        layout = QVBoxLayout(self)
        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(body_splitter, 1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_wrap = QWidget()
        left_layout = QVBoxLayout(left_wrap)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(10)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        self._form = form

        self.edit_name = QLineEdit(values.get("name", ""))
        self.edit_desc = QTextEdit(values.get("description", ""))
        self.edit_desc.setMinimumHeight(80)
        self.edit_desc.setMaximumHeight(160)
        self.edit_desc.setPlaceholderText("可填写前置条件、测试步骤、注意事项等说明")
        self.edit_desc.setStyleSheet("font-family:'Microsoft YaHei','Segoe UI'; font-size:13px;")
        self.combo_action_type = QComboBox()
        self.combo_action_type.addItem("串口指令集", "serial_bundle")
        if allow_camera_actions:
            self.combo_action_type.addItem("抓拍保存", "camera_snapshot")
            self.combo_action_type.addItem("加入参考图库", "append_reference")
            self.combo_action_type.addItem("检查指定正常照片", "compare_reference")
            self.combo_action_type.addItem("绿屏检测", "green_screen_detect")
        self.edit_commands = QTextEdit("\n".join(values.get("commands", [])))
        self.edit_commands.setPlaceholderText("每行一条串口指令；长命令仍然只算一条，可直接横向查看，不需要手工拆成多行")
        self.edit_commands.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.edit_commands.setMinimumHeight(140)
        self.edit_commands.setStyleSheet("font-family:'Cascadia Code','Consolas';")
        self.spin_capture_count = QSpinBox()
        self.spin_capture_count.setRange(1, 999)
        self.spin_capture_count.setValue(int(values.get("capture_count", 1) or 1))
        self.spin_capture_interval = QSpinBox()
        self.spin_capture_interval.setRange(100, 600000)
        self.spin_capture_interval.setSingleStep(100)
        self.spin_capture_interval.setValue(int(values.get("capture_interval_ms", 1000) or 1000))
        self.spin_capture_interval.setSuffix(" ms")
        self.edit_reference_category = QLineEdit(values.get("reference_category", "default"))
        self.edit_reference_category.setPlaceholderText("例如 default / boot / menu")
        self.edit_reference_dir = QLineEdit(values.get("reference_dir", ""))
        self.edit_reference_dir.setPlaceholderText("参考图库目录，留空时走剧本输出目录或右侧手动目录")
        self.spin_reference_pool_size = QSpinBox()
        self.spin_reference_pool_size.setRange(1, 50)
        self.spin_reference_pool_size.setValue(int(values.get("reference_pool_size", 5) or 5))
        self.chk_save_diff_heatmap = QCheckBox("保存差异/掩码图")
        self.chk_save_diff_heatmap.setChecked(bool(values.get("save_diff_heatmap", True)))
        self.edit_roi_text = QLineEdit(values.get("roi_text", ""))
        self.edit_roi_text.setPlaceholderText("例如 0.10,0.10,0.80,0.60，按 x,y,w,h 填 0-1")
        self.spin_green_ratio_threshold = QDoubleSpinBox()
        self.spin_green_ratio_threshold.setRange(0.01, 1.0)
        self.spin_green_ratio_threshold.setDecimals(2)
        self.spin_green_ratio_threshold.setSingleStep(0.01)
        self.spin_green_ratio_threshold.setValue(float(values.get("green_ratio_threshold", 0.35) or 0.35))
        self.spin_green_area_threshold = QDoubleSpinBox()
        self.spin_green_area_threshold.setRange(0.01, 1.0)
        self.spin_green_area_threshold.setDecimals(2)
        self.spin_green_area_threshold.setSingleStep(0.01)
        self.spin_green_area_threshold.setValue(float(values.get("green_area_threshold", 0.18) or 0.18))
        self.spin_green_margin = QSpinBox()
        self.spin_green_margin.setRange(0, 255)
        self.spin_green_margin.setValue(int(values.get("green_margin", 35) or 35))
        self.spin_green_saturation_threshold = QSpinBox()
        self.spin_green_saturation_threshold.setRange(0, 255)
        self.spin_green_saturation_threshold.setValue(int(values.get("green_saturation_threshold", 70) or 70))
        self.spin_green_value_threshold = QSpinBox()
        self.spin_green_value_threshold.setRange(0, 255)
        self.spin_green_value_threshold.setValue(int(values.get("green_value_threshold", 60) or 60))
        self.spin_green_check_frames = QSpinBox()
        self.spin_green_check_frames.setRange(1, 10)
        self.spin_green_check_frames.setValue(int(values.get("green_check_frames", 3) or 3))
        self.spin_green_check_interval = QSpinBox()
        self.spin_green_check_interval.setRange(50, 10000)
        self.spin_green_check_interval.setSingleStep(50)
        self.spin_green_check_interval.setValue(int(values.get("green_check_interval_ms", 250) or 250))
        self.spin_green_check_interval.setSuffix(" ms")
        self.lbl_action_hint = QLabel()
        self.lbl_action_hint.setWordWrap(True)
        self.lbl_green_help = QLabel(_green_help_text())
        self.lbl_green_help.setWordWrap(True)
        self.lbl_green_help.setStyleSheet("background:#f8fafc; border:1px solid rgba(148,163,184,0.25); border-radius:10px; padding:10px;")
        preview_row = QHBoxLayout()
        self.btn_pick_green_preview = QPushButton("导入参考图")
        self.btn_pick_green_preview.clicked.connect(self._pick_green_preview_image)
        self.btn_green_preset_rookie = QPushButton("新手宽松")
        self.btn_green_preset_rookie.clicked.connect(lambda: self._apply_green_preset("rookie"))
        self.btn_green_preset_balanced = QPushButton("默认推荐")
        self.btn_green_preset_balanced.clicked.connect(lambda: self._apply_green_preset("balanced"))
        self.btn_green_preset_strict = QPushButton("严格复检")
        self.btn_green_preset_strict.clicked.connect(lambda: self._apply_green_preset("strict"))
        self.lbl_green_preview_info = QLabel("未导入参考图时，显示 ROI 和阈值示意图。")
        self.lbl_green_preview_info.setWordWrap(True)
        preview_row.addWidget(self.btn_pick_green_preview)
        preview_row.addWidget(self.btn_green_preset_rookie)
        preview_row.addWidget(self.btn_green_preset_balanced)
        preview_row.addWidget(self.btn_green_preset_strict)
        preview_row.addWidget(self.lbl_green_preview_info, 1)
        self.lbl_green_preview = QLabel()
        self.lbl_green_preview.setMinimumHeight(380)
        self.lbl_green_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_green_preview.setStyleSheet("background:#ffffff; border:1px solid rgba(148,163,184,0.25); border-radius:12px; padding:8px;")
        self.lbl_green_analysis = QLabel(_build_green_analysis_text(None, int(self.spin_green_check_frames.value())))
        self.lbl_green_analysis.setWordWrap(True)
        self.lbl_green_analysis.setStyleSheet("background:#fff8ee; border:1px solid rgba(245,158,11,0.22); border-radius:10px; padding:10px;")

        current_action_type = values.get("action_type", "serial_bundle")
        index = self.combo_action_type.findData(current_action_type)
        self.combo_action_type.setCurrentIndex(index if index >= 0 else 0)
        self.combo_action_type.currentIndexChanged.connect(self._sync_action_type)

        form.addRow("名称", self.edit_name)
        form.addRow("说明", self.edit_desc)
        if allow_camera_actions:
            form.addRow("动作类型", self.combo_action_type)
        form.addRow("指令", self.edit_commands)
        form.addRow("抓拍张数", self.spin_capture_count)
        form.addRow("抓拍间隔", self.spin_capture_interval)
        form.addRow("参考分类", self.edit_reference_category)
        form.addRow("参考图库目录", self.edit_reference_dir)
        form.addRow("图库样本上限", self.spin_reference_pool_size)
        form.addRow("ROI 区域", self.edit_roi_text)
        form.addRow("产物开关", self.chk_save_diff_heatmap)
        form.addRow("绿像素占比阈值", self.spin_green_ratio_threshold)
        form.addRow("最大连通域阈值", self.spin_green_area_threshold)
        form.addRow("绿色通道领先值", self.spin_green_margin)
        form.addRow("饱和度下限", self.spin_green_saturation_threshold)
        form.addRow("亮度下限", self.spin_green_value_threshold)
        form.addRow("连续命中帧数", self.spin_green_check_frames)
        form.addRow("取样间隔", self.spin_green_check_interval)
        left_layout.addLayout(form)
        left_layout.addWidget(self.lbl_action_hint)
        left_layout.addStretch(1)
        left_scroll.setWidget(left_wrap)
        body_splitter.addWidget(left_scroll)

        right_wrap = QWidget()
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self.lbl_green_help)
        right_layout.addLayout(preview_row)
        right_layout.addWidget(self.lbl_green_analysis)
        right_layout.addWidget(self.lbl_green_preview, 1)
        body_splitter.addWidget(right_wrap)
        body_splitter.setSizes([460, 760])
        self._sync_action_type()

        self.edit_roi_text.textChanged.connect(self._refresh_green_preview)
        self.spin_green_ratio_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_area_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_check_frames.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_margin.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_saturation_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_value_threshold.valueChanged.connect(self._refresh_green_preview)
        if self._green_preview_path:
            self._load_green_preview_image(self._green_preview_path)

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
        if self.combo_action_type.currentData() != "serial_bundle":
            self.accept()
            return
        commands = [line.strip() for line in self.edit_commands.toPlainText().splitlines() if line.strip()]
        if not commands:
            QMessageBox.warning(self, "提示", "至少保留一条指令")
            return
        self.accept()

    def _sync_action_type(self):
        use_commands = self.combo_action_type.currentData() == "serial_bundle"
        use_capture_config = self.combo_action_type.currentData() in {"camera_snapshot", "compare_reference"}
        use_append_reference = self.combo_action_type.currentData() == "append_reference"
        use_compare_config = self.combo_action_type.currentData() == "compare_reference"
        use_green_config = self.combo_action_type.currentData() == "green_screen_detect"
        _set_form_row_visible(self._form, self.edit_commands, use_commands)
        _set_form_row_visible(self._form, self.spin_capture_count, use_capture_config)
        _set_form_row_visible(self._form, self.spin_capture_interval, use_capture_config)
        _set_form_row_visible(self._form, self.edit_reference_category, use_compare_config or use_append_reference)
        _set_form_row_visible(self._form, self.edit_reference_dir, use_compare_config or use_append_reference)
        _set_form_row_visible(self._form, self.spin_reference_pool_size, use_compare_config or use_append_reference)
        _set_form_row_visible(self._form, self.edit_roi_text, use_compare_config or use_green_config)
        _set_form_row_visible(self._form, self.chk_save_diff_heatmap, use_compare_config or use_green_config)
        _set_form_row_visible(self._form, self.spin_green_ratio_threshold, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_area_threshold, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_margin, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_saturation_threshold, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_value_threshold, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_check_frames, use_green_config)
        _set_form_row_visible(self._form, self.spin_green_check_interval, use_green_config)
        self.lbl_green_help.setVisible(use_green_config)
        self.btn_pick_green_preview.setVisible(use_green_config)
        self.btn_green_preset_rookie.setVisible(use_green_config)
        self.btn_green_preset_balanced.setVisible(use_green_config)
        self.btn_green_preset_strict.setVisible(use_green_config)
        self.lbl_green_preview_info.setVisible(use_green_config)
        self.lbl_green_analysis.setVisible(use_green_config)
        self.lbl_green_preview.setVisible(use_green_config)
        if self.combo_action_type.currentData() == "camera_snapshot":
            self.lbl_action_hint.setText("抓拍保存会按张数和间隔连续留档，适合做批量过程记录。")
        elif self.combo_action_type.currentData() == "append_reference":
            self.lbl_action_hint.setText("加入参考图库会把当前画面保存到指定分类目录，可配合剧本循环和等待步做周期性参考更新。")
        elif self.combo_action_type.currentData() == "compare_reference":
            self.lbl_action_hint.setText("检查指定正常照片会先抓拍留档，再到所选参考分类里按 ROI 和阈值自动检图，并输出差异热图。")
        elif self.combo_action_type.currentData() == "green_screen_detect":
            self.lbl_action_hint.setText("绿屏检测会在 ROI 内连续取样，按绿像素占比和最大连通域判断是否出现大面积绿屏；命中后会按失败处理。")
        else:
            self.lbl_action_hint.setText("串口指令集会按每行一条顺序发送到设备。")
        self._refresh_green_preview()

    def _apply_green_preset(self, preset_key: str):
        values = _green_preset_values(preset_key)
        self.spin_green_ratio_threshold.setValue(float(values["green_ratio_threshold"]))
        self.spin_green_area_threshold.setValue(float(values["green_area_threshold"]))
        self.spin_green_margin.setValue(int(values["green_margin"]))
        self.spin_green_saturation_threshold.setValue(int(values["green_saturation_threshold"]))
        self.spin_green_value_threshold.setValue(int(values["green_value_threshold"]))
        self.spin_green_check_frames.setValue(int(values["green_check_frames"]))
        self.spin_green_check_interval.setValue(int(values["green_check_interval_ms"]))
        self._refresh_green_preview()

    def _refresh_green_preview(self):
        if self._green_preview_image is not None:
            detection = detect_green_screen(
                self._green_preview_image,
                _parse_preview_roi_text(self.edit_roi_text.text().strip()),
                green_ratio_threshold=float(self.spin_green_ratio_threshold.value()),
                area_ratio_threshold=float(self.spin_green_area_threshold.value()),
                green_margin=int(self.spin_green_margin.value()),
                saturation_threshold=int(self.spin_green_saturation_threshold.value()),
                value_threshold=int(self.spin_green_value_threshold.value()),
            )
            combined_preview = _compose_source_and_overlay(self._green_preview_image, detection.get("heatmap"))
            self.lbl_green_preview.setPixmap(_cv_image_to_pixmap(combined_preview, 820, 420))
            self.lbl_green_preview_info.setText(
                f"参考图: {os.path.basename(self._green_preview_path)} | 绿像素占比={float(detection.get('green_ratio', 0.0)):.4f} | "
                f"最大连通域={float(detection.get('largest_component_ratio', 0.0)):.4f} | 判定={'命中绿屏' if detection.get('detected', False) else '未命中'}"
            )
            self.lbl_green_analysis.setText(_build_green_analysis_text(detection, int(self.spin_green_check_frames.value())))
            return
        self.lbl_green_preview.setPixmap(
            _build_green_preview_pixmap(
                self.edit_roi_text.text().strip(),
                float(self.spin_green_ratio_threshold.value()),
                float(self.spin_green_area_threshold.value()),
                int(self.spin_green_check_frames.value()),
                int(self.spin_green_margin.value()),
                int(self.spin_green_saturation_threshold.value()),
                int(self.spin_green_value_threshold.value()),
            )
        )
        self.lbl_green_preview_info.setText("未导入参考图时，显示 ROI 和阈值示意图。")
        self.lbl_green_analysis.setText(_build_green_analysis_text(None, int(self.spin_green_check_frames.value())))

    def _load_green_preview_image(self, file_path: str):
        image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            self._green_preview_image = None
            self._green_preview_path = ""
            self.lbl_green_preview_info.setText("参考图读取失败，请重新选择。")
            self._refresh_green_preview()
            return
        self._green_preview_image = image
        self._green_preview_path = file_path
        self._refresh_green_preview()

    def _pick_green_preview_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择绿屏预览参考图", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not file_path:
            return
        self._load_green_preview_image(file_path)

    def get_data(self) -> Dict[str, Any]:
        action_type = self.combo_action_type.currentData()
        return {
            "name": self.edit_name.text().strip(),
            "description": self.edit_desc.toPlainText().strip(),
            "commands": [line for line in self.edit_commands.toPlainText().strip().splitlines()] if action_type == "serial_bundle" else [],
            "action_type": action_type,
            "capture_count": int(self.spin_capture_count.value()),
            "capture_interval_ms": int(self.spin_capture_interval.value()),
            "reference_category": self.edit_reference_category.text().strip() or "default",
            "reference_dir": self.edit_reference_dir.text().strip(),
            "reference_pool_size": int(self.spin_reference_pool_size.value()),
            "save_diff_heatmap": self.chk_save_diff_heatmap.isChecked(),
            "roi_text": self.edit_roi_text.text().strip(),
            "green_preview_image": self._green_preview_path,
            "green_ratio_threshold": float(self.spin_green_ratio_threshold.value()),
            "green_area_threshold": float(self.spin_green_area_threshold.value()),
            "green_margin": int(self.spin_green_margin.value()),
            "green_saturation_threshold": int(self.spin_green_saturation_threshold.value()),
            "green_value_threshold": int(self.spin_green_value_threshold.value()),
            "green_check_frames": int(self.spin_green_check_frames.value()),
            "green_check_interval_ms": int(self.spin_green_check_interval.value()),
        }


class ScriptDialog(QDialog):
    def __init__(self, title: str, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 220)
        values = data or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_name = QLineEdit(values.get("name", ""))
        self.edit_desc = QLineEdit(values.get("description", ""))
        self.spin_run_count = QSpinBox()
        self.spin_run_count.setRange(1, 9999)
        self.spin_run_count.setValue(int(values.get("run_count", 1)))
        self.spin_cycle_interval = QSpinBox()
        self.spin_cycle_interval.setRange(0, 600000)
        self.spin_cycle_interval.setSingleStep(100)
        self.spin_cycle_interval.setValue(int(values.get("cycle_interval_ms", 0)))
        self.spin_cycle_interval.setSuffix(" ms")
        self.chk_stop_on_fail = QCheckBox("步骤失败时暂停整个剧本")
        self.chk_stop_on_fail.setChecked(bool(values.get("stop_on_fail", True)))
        form.addRow("剧本名", self.edit_name)
        form.addRow("说明", self.edit_desc)
        form.addRow("循环次数", self.spin_run_count)
        form.addRow("轮次间隔", self.spin_cycle_interval)
        form.addRow("失败策略", self.chk_stop_on_fail)
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
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "name": self.edit_name.text().strip(),
            "description": self.edit_desc.text().strip(),
            "run_count": int(self.spin_run_count.value()),
            "cycle_interval_ms": int(self.spin_cycle_interval.value()),
            "stop_on_fail": self.chk_stop_on_fail.isChecked(),
        }


class ScriptStepDialog(QDialog):
    _TYPE_LABELS = {
        "setting": "快捷配置",
        "shortcut": "快捷指令",
        "serial": "串口指令",
        "serial_check": "条件检查",
        "wait": "等待",
        "set_variable": "变量赋值",
        "capture_snapshot": "抓拍保存",
        "append_reference": "加入参考图库",
        "compare_reference": "检查参考图",
        "green_screen_detect": "绿屏检测",
        "compound": "复合步骤",
    }

    _TYPE_HELP = {
        "setting": "按名称引用左侧“配置项2 快捷配置”，适合复用一组稳定配置。",
        "shortcut": "按名称引用左侧“遥控快捷指令”，适合复用按键或相机动作。",
        "serial": "直接写要发给设备的原始串口命令。",
        "serial_check": "发送串口指令后，等待设备回发内容并与参考值比较，根据匹配结果决定是否继续后续步骤。",
        "wait": "仅等待，不发串口；适合留给系统加载或界面切换。",
        "set_variable": "给剧本变量赋值，后续指令和条件表达式都可以引用。",
        "capture_snapshot": "保存当前相机画面到设备联调抓拍目录。",
        "append_reference": "把当前画面加入指定参考分类目录，可用于剧本内定时刷新稳定参考图。",
        "compare_reference": "把当前画面与指定参考分类对比；支持 ROI、变量回写和失败恢复。",
        "green_screen_detect": "连续检测当前画面是否出现大面积绿屏；支持 ROI、结果变量、失败恢复和重试。",
        "compound": "一个步骤内包含多个子动作序列，按顺序执行。适合将一组相关操作打包为一个逻辑单元。",
    }

    def __init__(self, quick_settings: List[Dict[str, Any]], shortcuts: List[Dict[str, Any]], data: Optional[Dict[str, Any]] = None, serial_check_presets: Optional[List[Dict[str, Any]]] = None, on_presets_changed=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑剧本步骤")
        self.resize(1280, 900)
        values = data or {}
        self._green_preview_image = None
        self._green_preview_path = values.get("green_preview_image", "")
        self._serial_check_presets: List[Dict[str, Any]] = serial_check_presets if serial_check_presets is not None else []
        self._on_presets_changed = on_presets_changed

        layout = QVBoxLayout(self)
        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(body_splitter, 1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_wrap = QWidget()
        left_layout = QVBoxLayout(left_wrap)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(10)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        self._form = form

        self.combo_type = QComboBox()
        for key, label in self._TYPE_LABELS.items():
            self.combo_type.addItem(label, key)

        self.combo_setting = QComboBox()
        self.combo_setting.addItems([item.get("name", "") for item in quick_settings])

        self.combo_shortcut = QComboBox()
        self.combo_shortcut.addItems([item.get("name", "") for item in shortcuts])

        self.edit_command = QLineEdit(values.get("command", ""))
        self.edit_command.setPlaceholderText("例如 input keyevent 23")

        # 快捷指令选择器（从串口测试的快捷指令配置中加载）
        self._serial_quick_cmds = _load_serial_quick_cmds()
        serial_cmd_row = QHBoxLayout()
        serial_cmd_row.setSpacing(4)
        serial_cmd_row.addWidget(self.edit_command, 1)
        self.combo_serial_quick = QComboBox()
        self.combo_serial_quick.setFixedWidth(260)
        self.combo_serial_quick.addItem("选择快捷指令…")
        for display_name, _ in self._serial_quick_cmds:
            self.combo_serial_quick.addItem(display_name)
        self.combo_serial_quick.currentIndexChanged.connect(self._on_serial_quick_selected)
        serial_cmd_row.addWidget(self.combo_serial_quick)
        self._serial_cmd_widget = QWidget()
        self._serial_cmd_widget.setLayout(serial_cmd_row)

        self.edit_condition = QLineEdit(values.get("condition", ""))
        self.edit_condition.setPlaceholderText("例如 boot_ok == True and retry_count < 2")

        self.edit_variable_name = QLineEdit(values.get("variable_name", ""))
        self.edit_variable_name.setPlaceholderText("例如 boot_ok")

        self.edit_variable_value = QLineEdit(values.get("variable_value", ""))
        self.edit_variable_value.setPlaceholderText("例如 true / 3 / ready / ${last_compare_score}")

        self.spin_wait = QDoubleSpinBox()
        self.spin_wait.setRange(0.0, 3600.0)
        self.spin_wait.setDecimals(2)
        self.spin_wait.setSingleStep(0.1)
        self.spin_wait.setValue(float(values.get("seconds", 0.5) or 0.5))
        self.spin_wait.setSuffix(" s")

        self.chk_pause_on_fail = QCheckBox("不通过时暂停后续执行")
        self.chk_pause_on_fail.setChecked(bool(values.get("pause_on_fail", True)))

        self.chk_notify_on_fail = QCheckBox("失败/暂停时发送飞书通知")
        self.chk_notify_on_fail.setChecked(bool(values.get("notify_on_fail", False)))

        self.spin_capture_count = QSpinBox()
        self.spin_capture_count.setRange(1, 999)
        self.spin_capture_count.setValue(int(values.get("capture_count", 1) or 1))

        self.spin_capture_interval = QSpinBox()
        self.spin_capture_interval.setRange(100, 600000)
        self.spin_capture_interval.setSingleStep(100)
        self.spin_capture_interval.setValue(int(values.get("capture_interval_ms", 1000) or 1000))
        self.spin_capture_interval.setSuffix(" ms")

        self.spin_retry_count = QSpinBox()
        self.spin_retry_count.setRange(0, 20)
        self.spin_retry_count.setValue(int(values.get("retry_count", 0) or 0))

        self.spin_retry_interval = QSpinBox()
        self.spin_retry_interval.setRange(100, 600000)
        self.spin_retry_interval.setSingleStep(100)
        self.spin_retry_interval.setValue(int(values.get("retry_interval_ms", 1000) or 1000))
        self.spin_retry_interval.setSuffix(" ms")

        self.edit_result_variable = QLineEdit(values.get("result_variable", ""))
        self.edit_result_variable.setPlaceholderText("例如 boot_ok，检图结果会写入 true/false")

        # --- 条件检查专用控件 ---
        self.edit_check_reference = QLineEdit(values.get("check_reference", ""))
        self.edit_check_reference.setPlaceholderText("例如 getactparam: 1985560818，设备回发中包含该文本则视为匹配")

        self.combo_check_mode = QComboBox()
        self.combo_check_mode.addItem("包含（回发中含有参考值）", "contains")
        self.combo_check_mode.addItem("不包含（回发中不含参考值）", "not_contains")
        self.combo_check_mode.addItem("精确匹配（某行完全等于参考值）", "exact")
        self.combo_check_mode.addItem("正则匹配（按正则表达式匹配回发）", "regex")
        check_mode_index = self.combo_check_mode.findData(values.get("check_mode", "contains"))
        self.combo_check_mode.setCurrentIndex(check_mode_index if check_mode_index >= 0 else 0)

        self.combo_check_fail_action = QComboBox()
        self.combo_check_fail_action.addItem("停止剧本（不匹配则停止）", "stop")
        self.combo_check_fail_action.addItem("继续执行（不匹配也继续）", "continue")
        fail_action_index = self.combo_check_fail_action.findData(values.get("check_fail_action", "stop"))
        self.combo_check_fail_action.setCurrentIndex(fail_action_index if fail_action_index >= 0 else 0)

        self.spin_check_timeout = QSpinBox()
        self.spin_check_timeout.setRange(500, 60000)
        self.spin_check_timeout.setSingleStep(500)
        self.spin_check_timeout.setValue(int(values.get("check_timeout_ms", 3000) or 3000))
        self.spin_check_timeout.setSuffix(" ms")

        # --- 条件检查预设控件 ---
        self.combo_check_preset = QComboBox()
        self.combo_check_preset.setMinimumWidth(200)
        self._fill_preset_combo()
        self.combo_check_preset.currentIndexChanged.connect(self._on_check_preset_selected)
        _btn_save_preset = QPushButton("保存为预设")
        _btn_save_preset.setFixedWidth(96)
        _btn_save_preset.clicked.connect(self._save_check_preset)
        _btn_del_preset = QPushButton("删除预设")
        _btn_del_preset.setFixedWidth(76)
        _btn_del_preset.clicked.connect(self._delete_check_preset)
        _preset_row_layout = QHBoxLayout()
        _preset_row_layout.setContentsMargins(0, 0, 0, 0)
        _preset_row_layout.setSpacing(6)
        _preset_row_layout.addWidget(self.combo_check_preset, 1)
        _preset_row_layout.addWidget(_btn_save_preset)
        _preset_row_layout.addWidget(_btn_del_preset)
        self._check_preset_widget = QWidget()
        self._check_preset_widget.setLayout(_preset_row_layout)

        self.combo_recovery_shortcut = QComboBox()
        self.combo_recovery_shortcut.addItem("（无）", "")
        for item in shortcuts:
            self.combo_recovery_shortcut.addItem(item.get("name", ""), item.get("name", ""))
        recovery_index = self.combo_recovery_shortcut.findData(values.get("recovery_target", ""))
        self.combo_recovery_shortcut.setCurrentIndex(recovery_index if recovery_index >= 0 else 0)

        self.edit_reference_category = QLineEdit(values.get("reference_category", "default"))
        self.edit_reference_category.setPlaceholderText("例如 default / boot / menu")

        self.edit_reference_dir = QLineEdit(values.get("reference_dir", ""))
        self.edit_reference_dir.setPlaceholderText("参考图库目录，留空时走剧本输出目录或右侧手动目录")

        self.spin_reference_pool_size = QSpinBox()
        self.spin_reference_pool_size.setRange(1, 50)
        self.spin_reference_pool_size.setValue(int(values.get("reference_pool_size", 5) or 5))

        self.chk_save_diff_heatmap = QCheckBox("保存差异/掩码图")
        self.chk_save_diff_heatmap.setChecked(bool(values.get("save_diff_heatmap", True)))

        self.edit_roi_text = QLineEdit(values.get("roi_text", ""))
        self.edit_roi_text.setPlaceholderText("例如 0.15,0.10,0.70,0.65，按 x,y,w,h 填 0-1")

        self.spin_green_ratio_threshold = QDoubleSpinBox()
        self.spin_green_ratio_threshold.setRange(0.01, 1.0)
        self.spin_green_ratio_threshold.setDecimals(2)
        self.spin_green_ratio_threshold.setSingleStep(0.01)
        self.spin_green_ratio_threshold.setValue(float(values.get("green_ratio_threshold", 0.35) or 0.35))

        self.spin_green_area_threshold = QDoubleSpinBox()
        self.spin_green_area_threshold.setRange(0.01, 1.0)
        self.spin_green_area_threshold.setDecimals(2)
        self.spin_green_area_threshold.setSingleStep(0.01)
        self.spin_green_area_threshold.setValue(float(values.get("green_area_threshold", 0.18) or 0.18))

        self.spin_green_margin = QSpinBox()
        self.spin_green_margin.setRange(0, 255)
        self.spin_green_margin.setValue(int(values.get("green_margin", 35) or 35))

        self.spin_green_saturation_threshold = QSpinBox()
        self.spin_green_saturation_threshold.setRange(0, 255)
        self.spin_green_saturation_threshold.setValue(int(values.get("green_saturation_threshold", 70) or 70))

        self.spin_green_value_threshold = QSpinBox()
        self.spin_green_value_threshold.setRange(0, 255)
        self.spin_green_value_threshold.setValue(int(values.get("green_value_threshold", 60) or 60))

        self.spin_green_check_frames = QSpinBox()
        self.spin_green_check_frames.setRange(1, 10)
        self.spin_green_check_frames.setValue(int(values.get("green_check_frames", 3) or 3))

        self.spin_green_check_interval = QSpinBox()
        self.spin_green_check_interval.setRange(50, 10000)
        self.spin_green_check_interval.setSingleStep(50)
        self.spin_green_check_interval.setValue(int(values.get("green_check_interval_ms", 250) or 250))
        self.spin_green_check_interval.setSuffix(" ms")

        self.spin_repeat = QSpinBox()
        self.spin_repeat.setRange(1, 999)
        self.spin_repeat.setValue(int(values.get("repeat", 1)))

        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 600000)
        self.spin_delay.setSingleStep(50)
        self.spin_delay.setValue(int(values.get("delay_ms", 250)))
        self.spin_delay.setSuffix(" ms")

        self.edit_note = QLineEdit(values.get("note", ""))
        self.edit_note.setPlaceholderText("步骤备注，会显示在详情说明里")

        self.lbl_help = QLabel()
        self.lbl_help.setWordWrap(True)
        self.lbl_green_help = QLabel(_green_help_text())
        self.lbl_green_help.setWordWrap(True)
        self.lbl_green_help.setStyleSheet("background:#f8fafc; border:1px solid rgba(148,163,184,0.25); border-radius:10px; padding:10px;")
        preview_row = QHBoxLayout()
        self.btn_pick_green_preview = QPushButton("导入参考图")
        self.btn_pick_green_preview.clicked.connect(self._pick_green_preview_image)
        self.btn_green_preset_rookie = QPushButton("新手宽松")
        self.btn_green_preset_rookie.clicked.connect(lambda: self._apply_green_preset("rookie"))
        self.btn_green_preset_balanced = QPushButton("默认推荐")
        self.btn_green_preset_balanced.clicked.connect(lambda: self._apply_green_preset("balanced"))
        self.btn_green_preset_strict = QPushButton("严格复检")
        self.btn_green_preset_strict.clicked.connect(lambda: self._apply_green_preset("strict"))
        self.lbl_green_preview_info = QLabel("未导入参考图时，显示 ROI 和阈值示意图。")
        self.lbl_green_preview_info.setWordWrap(True)
        preview_row.addWidget(self.btn_pick_green_preview)
        preview_row.addWidget(self.btn_green_preset_rookie)
        preview_row.addWidget(self.btn_green_preset_balanced)
        preview_row.addWidget(self.btn_green_preset_strict)
        preview_row.addWidget(self.lbl_green_preview_info, 1)
        self.lbl_green_preview = QLabel()
        self.lbl_green_preview.setMinimumHeight(380)
        self.lbl_green_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_green_preview.setStyleSheet("background:#ffffff; border:1px solid rgba(148,163,184,0.25); border-radius:12px; padding:8px;")
        self.lbl_green_analysis = QLabel(_build_green_analysis_text(None, int(self.spin_green_check_frames.value())))
        self.lbl_green_analysis.setWordWrap(True)
        self.lbl_green_analysis.setStyleSheet("background:#fff8ee; border:1px solid rgba(245,158,11,0.22); border-radius:10px; padding:10px;")

        form.addRow("步骤类型", self.combo_type)
        form.addRow("执行条件", self.edit_condition)
        form.addRow("快捷配置", self.combo_setting)
        form.addRow("快捷指令", self.combo_shortcut)
        form.addRow("串口指令", self._serial_cmd_widget)
        form.addRow("参考值", self.edit_check_reference)
        form.addRow("匹配方式", self.combo_check_mode)
        form.addRow("等待超时", self.spin_check_timeout)
        form.addRow("不匹配时", self.combo_check_fail_action)
        form.addRow("快选预设", self._check_preset_widget)
        form.addRow("变量名", self.edit_variable_name)
        form.addRow("变量值", self.edit_variable_value)
        form.addRow("等待时长", self.spin_wait)
        form.addRow("抓拍张数", self.spin_capture_count)
        form.addRow("抓拍间隔", self.spin_capture_interval)
        form.addRow("结果变量", self.edit_result_variable)
        form.addRow("恢复动作", self.combo_recovery_shortcut)
        form.addRow("参考分类", self.edit_reference_category)
        form.addRow("参考图库目录", self.edit_reference_dir)
        form.addRow("图库样本上限", self.spin_reference_pool_size)
        form.addRow("ROI 区域", self.edit_roi_text)
        form.addRow("产物开关", self.chk_save_diff_heatmap)
        form.addRow("绿像素占比阈值", self.spin_green_ratio_threshold)
        form.addRow("最大连通域阈值", self.spin_green_area_threshold)
        form.addRow("绿色通道领先值", self.spin_green_margin)
        form.addRow("饱和度下限", self.spin_green_saturation_threshold)
        form.addRow("亮度下限", self.spin_green_value_threshold)
        form.addRow("连续命中帧数", self.spin_green_check_frames)
        form.addRow("取样间隔", self.spin_green_check_interval)
        form.addRow("失败重试", self.spin_retry_count)
        form.addRow("重试间隔", self.spin_retry_interval)
        form.addRow("失败策略", self.chk_pause_on_fail)
        form.addRow("飞书通知", self.chk_notify_on_fail)

        # --- 复合步骤子动作列表 ---
        self._compound_sub_steps: List[Dict[str, Any]] = list(values.get("sub_steps", []))
        self._compound_quick_settings = quick_settings
        self._compound_shortcuts = shortcuts
        compound_container = QWidget()
        compound_layout = QVBoxLayout(compound_container)
        compound_layout.setContentsMargins(0, 0, 0, 0)
        compound_layout.setSpacing(4)
        self.list_sub_steps = QListWidget()
        self.list_sub_steps.setMinimumHeight(120)
        self.list_sub_steps.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        compound_layout.addWidget(self.list_sub_steps)
        btn_row_compound = QHBoxLayout()
        btn_add_sub = QPushButton("添加子动作")
        btn_add_sub.clicked.connect(self._add_sub_step)
        btn_edit_sub = QPushButton("编辑子动作")
        btn_edit_sub.clicked.connect(self._edit_sub_step)
        btn_del_sub = QPushButton("删除子动作")
        btn_del_sub.clicked.connect(self._delete_sub_step)
        btn_row_compound.addWidget(btn_add_sub)
        btn_row_compound.addWidget(btn_edit_sub)
        btn_row_compound.addWidget(btn_del_sub)
        btn_row_compound.addStretch()
        compound_layout.addLayout(btn_row_compound)
        self._compound_widget = compound_container
        form.addRow("子动作列表", self._compound_widget)

        form.addRow("执行次数", self.spin_repeat)
        form.addRow("每次后等待", self.spin_delay)
        form.addRow("备注", self.edit_note)
        left_layout.addLayout(form)
        left_layout.addWidget(self.lbl_help)
        left_layout.addStretch(1)
        left_scroll.setWidget(left_wrap)
        body_splitter.addWidget(left_scroll)

        right_wrap = QWidget()
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self.lbl_green_help)
        right_layout.addLayout(preview_row)
        right_layout.addWidget(self.lbl_green_analysis)
        right_layout.addWidget(self.lbl_green_preview, 1)
        body_splitter.addWidget(right_wrap)
        body_splitter.setSizes([520, 760])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        current_type = values.get("type", "shortcut")
        index = self.combo_type.findData(current_type)
        self.combo_type.setCurrentIndex(index if index >= 0 else 0)
        if values.get("target"):
            setting_index = self.combo_setting.findText(values.get("target", ""))
            if setting_index >= 0:
                self.combo_setting.setCurrentIndex(setting_index)
            shortcut_index = self.combo_shortcut.findText(values.get("target", ""))
            if shortcut_index >= 0:
                self.combo_shortcut.setCurrentIndex(shortcut_index)
        self.combo_type.currentIndexChanged.connect(self._sync_type_widgets)
        self._sync_type_widgets()
        self.edit_roi_text.textChanged.connect(self._refresh_green_preview)
        self.spin_green_ratio_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_area_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_check_frames.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_margin.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_saturation_threshold.valueChanged.connect(self._refresh_green_preview)
        self.spin_green_value_threshold.valueChanged.connect(self._refresh_green_preview)
        if self._green_preview_path:
            self._load_green_preview_image(self._green_preview_path)

    def _on_serial_quick_selected(self, index: int):
        """从快捷指令下拉框选中后填入串口指令输入框。"""
        if index <= 0:
            return
        cmd_index = index - 1  # 减去"选择快捷指令…"占位项
        if 0 <= cmd_index < len(self._serial_quick_cmds):
            _, cmd = self._serial_quick_cmds[cmd_index]
            self.edit_command.setText(cmd.replace('\n', '; '))
        self.combo_serial_quick.setCurrentIndex(0)

    def _sync_type_widgets(self):
        current_type = self.combo_type.currentData()
        show_setting = current_type == "setting"
        show_shortcut = current_type == "shortcut"
        show_command = current_type == "serial"
        show_check = current_type == "serial_check"
        show_wait = current_type == "wait"
        show_variable = current_type == "set_variable"
        show_capture = current_type == "capture_snapshot"
        show_append_reference = current_type == "append_reference"
        show_compare = current_type == "compare_reference"
        show_green = current_type == "green_screen_detect"
        show_compound = current_type == "compound"
        show_detect_result = show_compare or show_green

        _set_form_row_visible(self._form, self.combo_setting, show_setting)
        _set_form_row_visible(self._form, self.combo_shortcut, show_shortcut)
        _set_form_row_visible(self._form, self._serial_cmd_widget, show_command or show_check)
        _set_form_row_visible(self._form, self._compound_widget, show_compound)
        _set_form_row_visible(self._form, self.edit_check_reference, show_check)
        _set_form_row_visible(self._form, self.combo_check_mode, show_check)
        _set_form_row_visible(self._form, self.spin_check_timeout, show_check)
        _set_form_row_visible(self._form, self.combo_check_fail_action, show_check)
        _set_form_row_visible(self._form, self._check_preset_widget, show_check)
        _set_form_row_visible(self._form, self.spin_wait, show_wait)
        _set_form_row_visible(self._form, self.edit_variable_name, show_variable)
        _set_form_row_visible(self._form, self.edit_variable_value, show_variable)
        _set_form_row_visible(self._form, self.spin_capture_count, show_capture)
        _set_form_row_visible(self._form, self.spin_capture_interval, show_capture)
        _set_form_row_visible(self._form, self.edit_result_variable, show_detect_result or show_check)
        _set_form_row_visible(self._form, self.combo_recovery_shortcut, show_detect_result)
        _set_form_row_visible(self._form, self.edit_reference_category, show_compare or show_append_reference)
        _set_form_row_visible(self._form, self.edit_reference_dir, show_compare or show_append_reference)
        _set_form_row_visible(self._form, self.spin_reference_pool_size, show_compare or show_append_reference)
        _set_form_row_visible(self._form, self.edit_roi_text, show_compare or show_green)
        _set_form_row_visible(self._form, self.chk_save_diff_heatmap, show_detect_result)
        _set_form_row_visible(self._form, self.spin_green_ratio_threshold, show_green)
        _set_form_row_visible(self._form, self.spin_green_area_threshold, show_green)
        _set_form_row_visible(self._form, self.spin_green_margin, show_green)
        _set_form_row_visible(self._form, self.spin_green_saturation_threshold, show_green)
        _set_form_row_visible(self._form, self.spin_green_value_threshold, show_green)
        _set_form_row_visible(self._form, self.spin_green_check_frames, show_green)
        _set_form_row_visible(self._form, self.spin_green_check_interval, show_green)
        self.btn_pick_green_preview.setVisible(show_green)
        self.btn_green_preset_rookie.setVisible(show_green)
        self.btn_green_preset_balanced.setVisible(show_green)
        self.btn_green_preset_strict.setVisible(show_green)
        self.lbl_green_preview_info.setVisible(show_green)
        self.lbl_green_help.setVisible(show_green)
        self.lbl_green_analysis.setVisible(show_green)
        self.lbl_green_preview.setVisible(show_green)
        _set_form_row_visible(self._form, self.spin_retry_count, show_detect_result)
        _set_form_row_visible(self._form, self.spin_retry_interval, show_detect_result)
        _set_form_row_visible(self._form, self.chk_pause_on_fail, show_detect_result)
        _set_form_row_visible(self._form, self.chk_notify_on_fail, show_detect_result)
        if show_green:
            self.edit_result_variable.setPlaceholderText("例如 screen_ok；未检出绿屏会写入 true")
        elif show_compare:
            self.edit_result_variable.setPlaceholderText("例如 boot_ok，检图结果会写入 true/false")
        elif show_check:
            self.edit_result_variable.setPlaceholderText("例如 check_ok；匹配写 true，不匹配写 false（留空不写）")
        self.lbl_help.setText(self._TYPE_HELP.get(current_type, ""))
        self._refresh_green_preview()
        if show_compound:
            self._refresh_sub_steps_list()

    # --- 复合步骤子动作管理 ---
    def _refresh_sub_steps_list(self):
        self.list_sub_steps.clear()
        _type_labels = self._TYPE_LABELS
        for i, sub in enumerate(self._compound_sub_steps):
            st = sub.get("type", "serial")
            label = _type_labels.get(st, st)
            note = sub.get("note", "")
            cmd = sub.get("command", "")
            target = sub.get("target", "")
            display = f"{i+1}. [{label}]"
            if target:
                display += f" {target}"
            elif cmd:
                display += f" {cmd[:40]}"
            if note:
                display += f" ({note})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.list_sub_steps.addItem(item)

    def _add_sub_step(self):
        dlg = ScriptStepDialog(
            self._compound_quick_settings,
            self._compound_shortcuts,
            serial_check_presets=self._serial_check_presets,
            on_presets_changed=self._on_presets_changed,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            sub = dlg.get_data()
            self._compound_sub_steps.append(sub)
            self._refresh_sub_steps_list()

    def _edit_sub_step(self):
        idx = self.list_sub_steps.currentRow()
        if idx < 0 or idx >= len(self._compound_sub_steps):
            return
        dlg = ScriptStepDialog(
            self._compound_quick_settings,
            self._compound_shortcuts,
            data=self._compound_sub_steps[idx],
            serial_check_presets=self._serial_check_presets,
            on_presets_changed=self._on_presets_changed,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._compound_sub_steps[idx] = dlg.get_data()
            self._refresh_sub_steps_list()

    def _delete_sub_step(self):
        idx = self.list_sub_steps.currentRow()
        if idx < 0 or idx >= len(self._compound_sub_steps):
            return
        self._compound_sub_steps.pop(idx)
        self._refresh_sub_steps_list()

    def _on_sub_steps_reordered(self):
        """拖拽后根据列表项的 UserRole 索引重建 sub_steps 顺序"""
        new_order = []
        for i in range(self.list_sub_steps.count()):
            item = self.list_sub_steps.item(i)
            orig_idx = item.data(Qt.ItemDataRole.UserRole)
            if orig_idx is not None and 0 <= orig_idx < len(self._compound_sub_steps):
                new_order.append(self._compound_sub_steps[orig_idx])
        if len(new_order) == len(self._compound_sub_steps):
            self._compound_sub_steps = new_order
        self._refresh_sub_steps_list()

    def _fill_preset_combo(self):
        """用当前 _serial_check_presets 刷新预设下拉框。"""
        self.combo_check_preset.blockSignals(True)
        self.combo_check_preset.clear()
        self.combo_check_preset.addItem("选择预设…", None)
        for preset in self._serial_check_presets:
            self.combo_check_preset.addItem(preset.get("name", ""), preset)
        self.combo_check_preset.setCurrentIndex(0)
        self.combo_check_preset.blockSignals(False)

    def _on_check_preset_selected(self, index: int):
        if index <= 0:
            return
        preset = self.combo_check_preset.itemData(index)
        if not preset:
            return
        self.edit_command.setText(preset.get("command", ""))
        self.edit_check_reference.setText(preset.get("check_reference", ""))
        mode_idx = self.combo_check_mode.findData(preset.get("check_mode", "contains"))
        self.combo_check_mode.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
        self.spin_check_timeout.setValue(int(preset.get("check_timeout_ms", 3000)))
        fail_idx = self.combo_check_fail_action.findData(preset.get("check_fail_action", "stop"))
        self.combo_check_fail_action.setCurrentIndex(fail_idx if fail_idx >= 0 else 0)

    def _save_check_preset(self):
        name, ok = QInputDialog.getText(self, "保存条件检查预设", "预设名称:")
        if not ok or not name.strip():
            return
        preset = {
            "name": name.strip(),
            "command": self.edit_command.text().strip(),
            "check_reference": self.edit_check_reference.text().strip(),
            "check_mode": self.combo_check_mode.currentData() or "contains",
            "check_timeout_ms": int(self.spin_check_timeout.value()),
            "check_fail_action": self.combo_check_fail_action.currentData() or "stop",
        }
        # 同名覆盖
        self._serial_check_presets[:] = [p for p in self._serial_check_presets if p.get("name") != preset["name"]]
        self._serial_check_presets.append(preset)
        self._fill_preset_combo()
        if self._on_presets_changed:
            self._on_presets_changed()

    def _delete_check_preset(self):
        index = self.combo_check_preset.currentIndex()
        if index <= 0:
            return
        preset = self.combo_check_preset.itemData(index)
        if not preset:
            return
        self._serial_check_presets[:] = [p for p in self._serial_check_presets if p.get("name") != preset.get("name")]
        self._fill_preset_combo()
        if self._on_presets_changed:
            self._on_presets_changed()

    def _apply_green_preset(self, preset_key: str):
        values = _green_preset_values(preset_key)
        self.spin_green_ratio_threshold.setValue(float(values["green_ratio_threshold"]))
        self.spin_green_area_threshold.setValue(float(values["green_area_threshold"]))
        self.spin_green_margin.setValue(int(values["green_margin"]))
        self.spin_green_saturation_threshold.setValue(int(values["green_saturation_threshold"]))
        self.spin_green_value_threshold.setValue(int(values["green_value_threshold"]))
        self.spin_green_check_frames.setValue(int(values["green_check_frames"]))
        self.spin_green_check_interval.setValue(int(values["green_check_interval_ms"]))
        self._refresh_green_preview()

    def _refresh_green_preview(self):
        if self._green_preview_image is not None:
            detection = detect_green_screen(
                self._green_preview_image,
                _parse_preview_roi_text(self.edit_roi_text.text().strip()),
                green_ratio_threshold=float(self.spin_green_ratio_threshold.value()),
                area_ratio_threshold=float(self.spin_green_area_threshold.value()),
                green_margin=int(self.spin_green_margin.value()),
                saturation_threshold=int(self.spin_green_saturation_threshold.value()),
                value_threshold=int(self.spin_green_value_threshold.value()),
            )
            combined_preview = _compose_source_and_overlay(self._green_preview_image, detection.get("heatmap"))
            self.lbl_green_preview.setPixmap(_cv_image_to_pixmap(combined_preview, 820, 420))
            self.lbl_green_preview_info.setText(
                f"参考图: {os.path.basename(self._green_preview_path)} | 绿像素占比={float(detection.get('green_ratio', 0.0)):.4f} | "
                f"最大连通域={float(detection.get('largest_component_ratio', 0.0)):.4f} | 判定={'命中绿屏' if detection.get('detected', False) else '未命中'}"
            )
            self.lbl_green_analysis.setText(_build_green_analysis_text(detection, int(self.spin_green_check_frames.value())))
            return
        self.lbl_green_preview.setPixmap(
            _build_green_preview_pixmap(
                self.edit_roi_text.text().strip(),
                float(self.spin_green_ratio_threshold.value()),
                float(self.spin_green_area_threshold.value()),
                int(self.spin_green_check_frames.value()),
                int(self.spin_green_margin.value()),
                int(self.spin_green_saturation_threshold.value()),
                int(self.spin_green_value_threshold.value()),
            )
        )
        self.lbl_green_preview_info.setText("未导入参考图时，显示 ROI 和阈值示意图。")
        self.lbl_green_analysis.setText(_build_green_analysis_text(None, int(self.spin_green_check_frames.value())))

    def _load_green_preview_image(self, file_path: str):
        image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            self._green_preview_image = None
            self._green_preview_path = ""
            self.lbl_green_preview_info.setText("参考图读取失败，请重新选择。")
            self._refresh_green_preview()
            return
        self._green_preview_image = image
        self._green_preview_path = file_path
        self._refresh_green_preview()

    def _pick_green_preview_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择绿屏预览参考图", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not file_path:
            return
        self._load_green_preview_image(file_path)

    def _on_accept(self):
        current_type = self.combo_type.currentData()
        if current_type == "serial" and not self.edit_command.text().strip():
            QMessageBox.warning(self, "提示", "串口指令不能为空")
            return
        if current_type == "serial_check" and not self.edit_command.text().strip():
            QMessageBox.warning(self, "提示", "条件检查：发送指令不能为空")
            return
        if current_type == "serial_check" and not self.edit_check_reference.text().strip():
            QMessageBox.warning(self, "提示", "条件检查：参考值不能为空")
            return
        if current_type == "set_variable" and not self.edit_variable_name.text().strip():
            QMessageBox.warning(self, "提示", "变量名不能为空")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        current_type = self.combo_type.currentData()
        target = ""
        command = ""
        seconds = 0.0
        pause_on_fail = self.chk_pause_on_fail.isChecked()

        if current_type == "setting":
            target = self.combo_setting.currentText().strip()
        elif current_type == "shortcut":
            target = self.combo_shortcut.currentText().strip()
        elif current_type in {"serial", "serial_check"}:
            command = self.edit_command.text().strip()
        elif current_type == "wait":
            seconds = float(self.spin_wait.value())

        return {
            "type": current_type,
            "target": target,
            "command": command,
            "seconds": seconds,
            "repeat": int(self.spin_repeat.value()),
            "delay_ms": int(self.spin_delay.value()),
            "note": self.edit_note.text().strip(),
            "reference_image": "",
            "threshold": 0.72,
            "pause_on_fail": pause_on_fail,
            "capture_count": int(self.spin_capture_count.value()),
            "capture_interval_ms": int(self.spin_capture_interval.value()),
            "retry_count": int(self.spin_retry_count.value()),
            "retry_interval_ms": int(self.spin_retry_interval.value()),
            "condition": self.edit_condition.text().strip(),
            "variable_name": self.edit_variable_name.text().strip(),
            "variable_value": self.edit_variable_value.text().strip(),
            "result_variable": self.edit_result_variable.text().strip(),
            "recovery_target": self.combo_recovery_shortcut.currentData() or "",
            "reference_category": self.edit_reference_category.text().strip() or "default",
            "reference_dir": self.edit_reference_dir.text().strip(),
            "reference_pool_size": int(self.spin_reference_pool_size.value()),
            "save_diff_heatmap": self.chk_save_diff_heatmap.isChecked(),
            "roi_text": self.edit_roi_text.text().strip(),
            "green_preview_image": self._green_preview_path,
            "green_ratio_threshold": float(self.spin_green_ratio_threshold.value()),
            "green_area_threshold": float(self.spin_green_area_threshold.value()),
            "green_margin": int(self.spin_green_margin.value()),
            "green_saturation_threshold": int(self.spin_green_saturation_threshold.value()),
            "green_value_threshold": int(self.spin_green_value_threshold.value()),
            "green_check_frames": int(self.spin_green_check_frames.value()),
            "green_check_interval_ms": int(self.spin_green_check_interval.value()),
            "check_reference": self.edit_check_reference.text().strip(),
            "check_mode": self.combo_check_mode.currentData() or "contains",
            "check_timeout_ms": int(self.spin_check_timeout.value()),
            "check_fail_action": self.combo_check_fail_action.currentData() or "stop",
            "notify_on_fail": self.chk_notify_on_fail.isChecked(),
            "sub_steps": list(self._compound_sub_steps) if current_type == "compound" else [],
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


class _FlatDropTreeWidget(QTreeWidget):
    """仅支持同级拖拽排序的 QTreeWidget（禁止拖入子级）。"""
    items_reordered = pyqtSignal()

    def dropEvent(self, event):  # type: ignore[override]
        # 仅允许同级排序，禁止变成子项
        drop_indicator = self.dropIndicatorPosition()
        if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
            event.ignore()
            return
        super().dropEvent(event)
        self.items_reordered.emit()


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
        self._command_queue: List[Dict[str, Any]] = []
        self._queue_timer = QTimer(self)
        self._queue_timer.setSingleShot(True)
        self._queue_timer.timeout.connect(self._process_next_queue_item)

        self._camera_capture = None
        self._current_camera_frame = None
        self._camera_timer = QTimer(self)
        self._camera_timer.timeout.connect(self._update_camera_frame)
        self._camera_frame_counter = 0
        self._camera_fps_anchor = time.time()
        self._snapshot_timer = QTimer(self)
        self._snapshot_timer.timeout.connect(self._capture_next_snapshot)
        self._snapshot_remaining = 0
        self._snapshot_total = 0
        self._snapshot_batch_dir = ""
        self._snapshot_batch_token = ""
        self._last_snapshot_path = ""
        self._last_run_output_dir = ""
        self._run_log_file = None  # 当前运行的日志文件句柄
        self._active_run_context: Optional[Dict[str, Any]] = None
        self._queue_paused = False
        self._queue_busy = False
        self._failure_notified = False  # 是否已发送过失败/暂停通知（防止重复发完成通知）
        self._script_camera_capture = None
        self._running_step_id: Optional[str] = None
        self._last_preview_render_at = 0.0
        self._last_preview_size = None
        self._run_metrics: Dict[str, Any] = {}
        self._paused_elapsed: float = 0.0  # 暂停时已经过的秒数（暂停时冻结计时）
        self._run_stats_timer = QTimer(self)
        self._run_stats_timer.setInterval(1000)
        self._run_stats_timer.timeout.connect(self._update_run_stats)
        self._state_save_counter = 0  # 每 30 次 tick（~30s）自动保存状态
        self._reference_capture_timer = QTimer(self)
        self._reference_capture_timer.timeout.connect(self._attempt_auto_reference_capture)
        self._reference_reject_count = 0
        self._script_variables: Dict[str, Any] = {}
        self._selected_remote_id: Optional[str] = None
        self._remote_buttons: Dict[str, DraggableRemoteButton] = {}

        self._cmd_history: List[str] = []
        self._history_idx = -1
        self._tab_candidates: List[str] = []
        self._tab_idx = -1
        self._pre_tab_text = ""
        self._rx_path_cache: List[str] = []
        self._serial_rx_buffer = bytearray()
        self._serial_flush_timer = QTimer(self)
        self._serial_flush_timer.setInterval(220)
        self._serial_flush_timer.timeout.connect(self._flush_serial_rx_buffer)

        self._serial_check_timer = QTimer(self)
        self._serial_check_timer.setInterval(100)
        self._serial_check_timer.timeout.connect(self._on_serial_check_tick)
        self._serial_check_lines: List[str] = []
        self._serial_check_deadline: float = 0.0
        self._serial_check_action: Optional[Dict[str, Any]] = None

        self.setObjectName("device_lab_root")
        self.setStyleSheet(_PAGE_QSS)
        self._init_ui()
        self._load_profile_to_ui()
        self._refresh_serial_ports()
        self._refresh_queue_controls()
        self._refresh_workspace_overview()

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

        overview = QFrame()
        overview_layout = QHBoxLayout(overview)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.setSpacing(10)
        self.lbl_overview_scope = QLabel("项目/剧本: 未选择")
        self.lbl_overview_scope.setObjectName("status_chip")
        self.lbl_overview_scope.setWordWrap(True)
        self.lbl_overview_run = QLabel("运行: 空闲")
        self.lbl_overview_run.setObjectName("status_chip")
        self.lbl_overview_run.setWordWrap(True)
        self.lbl_overview_output = QLabel("输出: 待执行")
        self.lbl_overview_output.setObjectName("status_chip")
        self.lbl_overview_output.setWordWrap(True)
        overview_layout.addWidget(self.lbl_overview_scope, 1)
        overview_layout.addWidget(self.lbl_overview_run, 1)
        overview_layout.addWidget(self.lbl_overview_output, 2)
        root_layout.addWidget(overview)

        workspace_split = QSplitter(Qt.Orientation.Horizontal)
        workspace_split.setChildrenCollapsible(False)
        self.workspace_nav = QTreeWidget()
        self.workspace_nav.setHeaderHidden(True)
        self.workspace_nav.setMinimumWidth(220)
        self.workspace_nav.currentItemChanged.connect(self._on_workspace_nav_changed)
        workspace_split.addWidget(self.workspace_nav)

        self.workspace_stack = QStackedWidget()
        workspace_split.addWidget(self.workspace_stack)
        workspace_split.setSizes([240, 1180])
        root_layout.addWidget(workspace_split, 1)

        self._workspace_pages = {}
        self._add_workspace_tree_branch(
            "设备控制",
            self._create_workspace_overview_page("设备控制", "集中处理串口连接、快捷配置和联调剧本，适合按步骤推进联调。"),
            [
                ("串口工作台", self._build_serial_card()),
                ("快捷配置", self._build_quick_tabs_card()),
                ("联调剧本", self._build_script_card()),
            ],
        )
        self._add_workspace_tree_branch(
            "图像观察",
            self._create_workspace_overview_page("图像观察", "集中处理相机预览、遥控模拟和运行日志，适合看现场画面与执行反馈。"),
            [
                ("USB 相机", self._build_camera_card()),
                ("遥控器", self._build_remote_card()),
                ("运行日志", self._build_log_card()),
            ],
        )
        first_item = self.workspace_nav.topLevelItem(0)
        if first_item is not None:
            self.workspace_nav.setCurrentItem(first_item)

    def _create_workspace_overview_page(self, title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        card = QGroupBox(title)
        card.setObjectName("lab_card")
        card_layout = QVBoxLayout(card)
        summary = QLabel(description)
        summary.setWordWrap(True)
        card_layout.addWidget(summary)
        tips = QLabel("左侧树状导航可进入该工作区下的具体子面板。")
        tips.setWordWrap(True)
        card_layout.addWidget(tips)
        card_layout.addStretch(1)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _add_workspace_tree_branch(self, root_title: str, root_page: QWidget, children: List[Tuple[str, QWidget]]):
        root_item = QTreeWidgetItem([root_title])
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_title)
        self.workspace_nav.addTopLevelItem(root_item)
        self.workspace_stack.addWidget(root_page)
        self._workspace_pages[root_title] = root_page
        for child_title, child_page in children:
            child_item = QTreeWidgetItem([child_title])
            child_item.setData(0, Qt.ItemDataRole.UserRole, child_title)
            root_item.addChild(child_item)
            self.workspace_stack.addWidget(child_page)
            self._workspace_pages[child_title] = child_page
        root_item.setExpanded(True)

    def _on_workspace_nav_changed(self, current: Optional[QTreeWidgetItem], _previous: Optional[QTreeWidgetItem]):
        if current is None:
            return
        page_key = current.data(0, Qt.ItemDataRole.UserRole)
        page = self._workspace_pages.get(page_key)
        if page is not None:
            self.workspace_stack.setCurrentWidget(page)

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
        self.chk_tab_passthrough = QCheckBox("Tab直发设备")
        row2.addWidget(self.chk_newline)
        row2.addWidget(self.chk_auto_su)
        row2.addWidget(self.chk_tab_passthrough)
        row2.addStretch(1)
        layout.addLayout(row2)

        send_row = QHBoxLayout()
        self.edit_serial_cmd = QLineEdit()
        self.edit_serial_cmd.setPlaceholderText("输入串口指令，例如 input keyevent 23")
        self.edit_serial_cmd.installEventFilter(self)
        self.edit_serial_cmd.returnPressed.connect(self._on_send)
        self.combo_newline = QComboBox()
        self.combo_newline.addItems(["\\r\\n", "\\n", "\\r", "无"])
        self.combo_newline.setFixedWidth(64)
        self.combo_newline.setToolTip("发送时附加的换行符")
        btn_send_tab = QPushButton("发送Tab")
        btn_send_tab.setObjectName("lab_secondary")
        btn_send_tab.clicked.connect(self._send_tab_character)
        btn_send = QPushButton("发送")
        btn_send.setObjectName("lab_primary")
        btn_send.clicked.connect(self._on_send)
        send_row.addWidget(self.edit_serial_cmd, 1)
        send_row.addWidget(self.combo_newline)
        send_row.addWidget(btn_send_tab)
        send_row.addWidget(btn_send)
        layout.addLayout(send_row)

        self.serial_terminal = QPlainTextEdit()
        self.serial_terminal.setObjectName("device_log")
        self.serial_terminal.setReadOnly(True)
        self.serial_terminal.setMaximumBlockCount(800)
        self.serial_terminal.setMinimumHeight(240)
        self.serial_terminal.installEventFilter(self)
        self.serial_terminal.setPlaceholderText("串口输出会显示在这里。终端聚焦时可以直接输入，Enter 发送，Tab 按当前模式工作。")
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
        self.combo_project.currentIndexChanged.connect(self._on_project_selection_changed)
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

        content_split = QSplitter(Qt.Orientation.Horizontal)
        content_split.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(QLabel("剧本导航树"))

        self.list_scripts = QTreeWidget()
        self.list_scripts.setHeaderHidden(True)
        self.list_scripts.currentItemChanged.connect(self._on_script_selection_changed)
        self.list_scripts.setMinimumWidth(280)
        self.list_scripts.setMinimumHeight(120)
        self.list_scripts.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        left_layout.addWidget(self.list_scripts, 1)

        left_layout.addWidget(QLabel("剧本说明"))
        self.lbl_script_desc = QLabel("请选择剧本")
        self.lbl_script_desc.setWordWrap(True)
        script_desc_scroll = QScrollArea()
        script_desc_scroll.setWidgetResizable(True)
        script_desc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        script_desc_scroll.setMinimumHeight(60)
        script_desc_scroll.setWidget(self.lbl_script_desc)
        left_layout.addWidget(script_desc_scroll)
        content_split.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 0, 0, 0)
        right_layout.setSpacing(8)
        step_workspace_split = QSplitter(Qt.Orientation.Horizontal)
        step_workspace_split.setChildrenCollapsible(False)

        step_nav_panel = QWidget()
        step_nav_layout = QVBoxLayout(step_nav_panel)
        step_nav_layout.setContentsMargins(0, 0, 0, 0)
        step_nav_layout.setSpacing(8)
        step_nav_layout.addWidget(QLabel("步骤导航树"))

        self.list_script_steps = _FlatDropTreeWidget()
        self.list_script_steps.setHeaderHidden(True)
        self.list_script_steps.currentItemChanged.connect(self._on_step_selection_changed)
        self.list_script_steps.setMinimumWidth(300)
        self.list_script_steps.setMinimumHeight(160)
        self.list_script_steps.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.list_script_steps.setDragEnabled(True)
        self.list_script_steps.setAcceptDrops(True)
        self.list_script_steps.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_script_steps.setDropIndicatorShown(True)
        self.list_script_steps.items_reordered.connect(self._on_steps_reordered)
        step_nav_layout.addWidget(self.list_script_steps, 1)
        step_workspace_split.addWidget(step_nav_panel)

        detail_inner = QWidget()
        detail_layout = QVBoxLayout(detail_inner)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(8)
        detail_layout.addWidget(QLabel("步骤详情"))
        self.lbl_step_detail = QLabel("请选择步骤")
        self.lbl_step_detail.setWordWrap(True)
        step_detail_scroll = QScrollArea()
        step_detail_scroll.setWidgetResizable(True)
        step_detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        step_detail_scroll.setMinimumHeight(80)
        step_detail_scroll.setWidget(self.lbl_step_detail)
        detail_layout.addWidget(step_detail_scroll, 1)

        status_panel = QFrame()
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        status_layout.addWidget(QLabel("运行输出"))
        self.lbl_run_output = QLabel("输出目录: 待执行")
        self.lbl_run_output.setWordWrap(True)
        run_output_scroll = QScrollArea()
        run_output_scroll.setWidgetResizable(True)
        run_output_scroll.setFrameShape(QFrame.Shape.NoFrame)
        run_output_scroll.setMinimumHeight(60)
        run_output_scroll.setWidget(self.lbl_run_output)
        status_layout.addWidget(run_output_scroll)
        status_layout.addWidget(QLabel("运行状态"))
        self.lbl_run_stats = QLabel("运行状态: 空闲")
        self.lbl_run_stats.setWordWrap(True)
        run_stats_scroll = QScrollArea()
        run_stats_scroll.setWidgetResizable(True)
        run_stats_scroll.setFrameShape(QFrame.Shape.NoFrame)
        run_stats_scroll.setMinimumHeight(60)
        run_stats_scroll.setWidget(self.lbl_run_stats)
        status_layout.addWidget(run_stats_scroll)
        detail_layout.addWidget(status_panel)

        detail_panel_scroll = QScrollArea()
        detail_panel_scroll.setWidgetResizable(True)
        detail_panel_scroll.setFrameShape(QFrame.Shape.NoFrame)
        detail_panel_scroll.setWidget(detail_inner)
        step_workspace_split.addWidget(detail_panel_scroll)
        step_workspace_split.setSizes([340, 500])

        right_layout.addWidget(step_workspace_split, 1)
        content_split.addWidget(right_panel)
        content_split.setSizes([360, 760])

        layout.addWidget(content_split, 1)

        row_top = QHBoxLayout()
        row_bottom = QHBoxLayout()
        top_actions = [
            ("新增剧本", self._add_script, False),
            ("编辑剧本", self._edit_script, False),
            ("删除剧本", self._delete_script, False),
            ("新增步骤", self._add_script_step, False),
            ("编辑步骤", self._edit_script_step, False),
            ("删除步骤", self._delete_script_step, False),
        ]
        bottom_actions = [
            ("上移", self._move_script_step_up, False),
            ("下移", self._move_script_step_down, False),
            ("执行剧本", self._run_selected_script, True),
        ]
        for text, slot, primary in top_actions:
            button = QPushButton(text)
            button.setObjectName("lab_primary" if primary else "lab_secondary")
            button.clicked.connect(slot)
            row_top.addWidget(button)
        row_top.addStretch(1)
        for text, slot, primary in bottom_actions:
            button = QPushButton(text)
            button.setObjectName("lab_primary" if primary else "lab_secondary")
            button.clicked.connect(slot)
            row_bottom.addWidget(button)
        self.btn_script_pause = QPushButton("暂停执行")
        self.btn_script_pause.setObjectName("lab_secondary")
        self.btn_script_pause.setEnabled(False)
        self.btn_script_pause.clicked.connect(self._toggle_script_pause)
        row_bottom.addWidget(self.btn_script_pause)
        self.btn_open_output_dir = QPushButton("打开输出目录")
        self.btn_open_output_dir.setObjectName("lab_secondary")
        self.btn_open_output_dir.clicked.connect(self._open_run_output_dir)
        row_bottom.addWidget(self.btn_open_output_dir)
        self.btn_script_stop = QPushButton("停止执行")
        self.btn_script_stop.setObjectName("lab_secondary")
        self.btn_script_stop.setEnabled(False)
        self.btn_script_stop.clicked.connect(self._stop_script_run)
        row_bottom.addWidget(self.btn_script_stop)

        self.btn_script_resume = QPushButton("断点续执行")
        self.btn_script_resume.setObjectName("lab_secondary")
        self.btn_script_resume.setEnabled(False)
        self.btn_script_resume.setToolTip("从上次暂停/失败/崩溃的位置恢复执行")
        self.btn_script_resume.clicked.connect(self._resume_from_saved_state)
        row_bottom.addWidget(self.btn_script_resume)

        self.btn_feishu_notify = QPushButton("📨 飞书通知 ▾")
        self.btn_feishu_notify.setObjectName("lab_secondary")
        self.btn_feishu_notify.setToolTip("手动发送通知或配置步骤自动通知")
        feishu_menu = QMenu(self.btn_feishu_notify)
        feishu_menu.addAction("📨 手动发送通知", self._on_feishu_notify)
        feishu_menu.addAction("⚙️ 配置步骤自动通知", self._on_step_notify_config)
        self.btn_feishu_notify.setMenu(feishu_menu)
        row_bottom.addWidget(self.btn_feishu_notify)

        row_bottom.addStretch(1)
        layout.addLayout(row_top)
        layout.addLayout(row_bottom)
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
        btn_open_snapshot_dir = QPushButton("打开保存路径")
        btn_open_snapshot_dir.setObjectName("lab_secondary")
        btn_open_snapshot_dir.clicked.connect(self._open_snapshot_dir)
        row.addWidget(QLabel("相机"))
        row.addWidget(self.combo_camera, 1)
        row.addWidget(QLabel("扫描上限"))
        row.addWidget(self.edit_scan_max)
        row.addWidget(btn_scan)
        row.addWidget(self.btn_camera_toggle)
        row.addWidget(btn_snapshot)
        row.addWidget(btn_open_snapshot_dir)
        layout.addLayout(row)

        preview_tools = QHBoxLayout()
        self.slider_preview_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_preview_zoom.setRange(50, 250)
        self.slider_preview_zoom.setSingleStep(10)
        self.slider_preview_zoom.setPageStep(25)
        self.slider_preview_zoom.valueChanged.connect(self._on_preview_zoom_changed)
        self.lbl_preview_zoom = QLabel("100%")
        preview_tools.addWidget(QLabel("预览缩放"))
        preview_tools.addWidget(self.slider_preview_zoom, 1)
        preview_tools.addWidget(self.lbl_preview_zoom)
        preview_tools.addStretch(1)
        layout.addLayout(preview_tools)

        self.edit_reference_dir = QLineEdit()
        self.edit_reference_dir.setPlaceholderText("参考图库目录")
        self.edit_reference_dir.editingFinished.connect(self._persist_profile)
        self.spin_reference_pool_size = QSpinBox()
        self.spin_reference_pool_size.setRange(1, 20)
        self.spin_reference_pool_size.setValue(5)
        self.spin_reference_pool_size.valueChanged.connect(lambda _v: self._persist_profile())
        self.edit_reference_category = QLineEdit()
        self.edit_reference_category.setPlaceholderText("参考分类，例如 default / boot / menu")
        self.edit_reference_category.editingFinished.connect(self._persist_profile)
        self.edit_compare_roi = QLineEdit()
        self.edit_compare_roi.setPlaceholderText("ROI，例如 0.10,0.10,0.80,0.60")
        self.edit_compare_roi.editingFinished.connect(self._persist_profile)
        self.chk_save_diff_heatmap = QCheckBox("检图时生成差异热图")
        self.chk_save_diff_heatmap.toggled.connect(lambda _checked: self._persist_profile())
        self.chk_auto_reference = QCheckBox("自动更新稳定参考图")
        self.chk_auto_reference.toggled.connect(self._toggle_auto_reference_capture)
        self.spin_auto_reference_interval = QSpinBox()
        self.spin_auto_reference_interval.setRange(1000, 3600000)
        self.spin_auto_reference_interval.setSingleStep(1000)
        self.spin_auto_reference_interval.setValue(5000)
        self.spin_auto_reference_interval.setSuffix(" ms")
        self.spin_auto_reference_interval.valueChanged.connect(self._on_auto_reference_interval_changed)
        self.spin_auto_reference_retry = QSpinBox()
        self.spin_auto_reference_retry.setRange(1, 20)
        self.spin_auto_reference_retry.setValue(3)
        self.spin_auto_reference_retry.valueChanged.connect(lambda _v: self._persist_profile())
        self.lbl_reference_meta = QLabel("参考图库: 0 张")
        self.lbl_reference_meta.setWordWrap(True)
        self.lbl_reference_meta.setVisible(False)

        hint = QLabel("拍摄参数已迁移到快捷指令和剧本步骤。右侧仅保留手动预览与抓拍回显。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.lbl_camera_meta = QLabel("等待扫描 USB 相机")
        layout.addWidget(self.lbl_camera_meta)

        self.lbl_camera_preview = QLabel("暂无视频流")
        self.lbl_camera_preview.setObjectName("camera_preview")
        self.lbl_camera_preview.setMinimumSize(520, 320)
        self.lbl_camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview_scroll = QScrollArea()
        self.camera_preview_scroll.setObjectName("camera_preview_scroll")
        self.camera_preview_scroll.setWidgetResizable(False)
        self.camera_preview_scroll.setMinimumHeight(380)
        self.camera_preview_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview_scroll.setWidget(self.lbl_camera_preview)
        layout.addWidget(self.camera_preview_scroll)
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
        self.remote_canvas.setMinimumSize(400, 920)
        self.remote_canvas.resize(400, 920)
        remote_scroll = QScrollArea()
        remote_scroll.setWidgetResizable(False)
        remote_scroll.setFrameShape(QFrame.Shape.NoFrame)
        remote_scroll.setMinimumHeight(760)
        remote_scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        remote_scroll.setWidget(self.remote_canvas)
        self.remote_canvas_scroll = remote_scroll
        layout.addWidget(remote_scroll)
        return card

    def _build_log_card(self) -> QGroupBox:
        card = QGroupBox("联调事件")
        card.setObjectName("lab_card")
        layout = QVBoxLayout(card)
        self.text_log = QPlainTextEdit()
        self.text_log.setObjectName("device_log")
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumBlockCount(2000)
        self.text_log.setMinimumHeight(200)
        layout.addWidget(self.text_log)
        return card

    def _load_profile_to_ui(self):
        serial_data = self._profile.get("serial", {})
        self.combo_baud.setCurrentText(str(serial_data.get("baudrate", 115200)))
        self.chk_newline.setChecked(bool(serial_data.get("newline", True)))
        self.chk_auto_su.setChecked(bool(serial_data.get("auto_su", False)))
        self.chk_tab_passthrough.setChecked(bool(serial_data.get("tab_passthrough", False)))
        self.combo_newline.setCurrentText(serial_data.get("newline_mode", "\\r\\n"))

        camera_data = self._profile.get("camera", {})
        self.edit_scan_max.setText(str(camera_data.get("scan_max_index", 5)))
        self.slider_preview_zoom.setValue(int(camera_data.get("preview_zoom_percent", 100)))
        self.edit_reference_dir.setText(camera_data.get("reference_dir", "reports/device_lab_references"))
        self.edit_reference_category.setText(camera_data.get("reference_category", "default"))
        self.edit_compare_roi.setText(camera_data.get("compare_roi", ""))
        self.chk_save_diff_heatmap.setChecked(bool(camera_data.get("save_diff_heatmap", True)))
        self.spin_reference_pool_size.setValue(int(camera_data.get("reference_pool_size", 5)))
        self.chk_auto_reference.setChecked(False)
        self.spin_auto_reference_interval.setValue(int(camera_data.get("auto_reference_interval_ms", 5000)))
        self.spin_auto_reference_retry.setValue(int(camera_data.get("auto_reference_max_retry", 3)))
        self.chk_remote_edit_mode.setChecked(bool(self._profile.get("remote", {}).get("edit_mode", False)))
        self._refresh_command_lists()
        self._refresh_projects()
        self._render_remote_buttons()
        self._refresh_reference_meta()
        self._refresh_workspace_overview()

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
        if data.get("action_type") == "camera_snapshot":
            detail = f"相机动作: 抓拍保存 x{int(data.get('capture_count', 1) or 1)}，间隔 {int(data.get('capture_interval_ms', 1000) or 1000)} ms"
        elif data.get("action_type") == "append_reference":
            category = data.get("reference_category", "default") or "default"
            detail = f"相机动作: 当前帧写入参考图库[{category}]，样本上限={int(data.get('reference_pool_size', 5) or 5)}"
        elif data.get("action_type") == "compare_reference":
            category = data.get("reference_category", "default") or "default"
            roi_text = data.get("roi_text", "").strip() or "全图"
            detail = f"相机动作: 先抓拍留档，再按分类 {category} 自动检图，ROI={roi_text}，热图={'开' if data.get('save_diff_heatmap', True) else '关'}"
        elif data.get("action_type") == "green_screen_detect":
            roi_text = data.get("roi_text", "").strip() or "全图"
            detail = (
                f"相机动作: 连续检测绿屏，ROI={roi_text}，"
                f"占比阈值={float(data.get('green_ratio_threshold', 0.35) or 0.35):.2f}，"
                f"连通域阈值={float(data.get('green_area_threshold', 0.18) or 0.18):.2f}，热图={'开' if data.get('save_diff_heatmap', True) else '关'}"
            )
        else:
            commands_text = " | ".join(data.get("commands", [])[:3]) or "无指令"
            detail = f"指令: {commands_text}"
        label.setText(f"{data.get('description', '无说明')}\n{detail}")

    def _get_list_source_for_widget(self, widget: QListWidget) -> List[Dict[str, Any]]:
        if widget is self.list_quick_settings:
            return self._profile.get("quick_settings", [])
        return self._profile.get("shortcuts", [])

    def _refresh_projects(self):
        ui_state = self._profile.get("ui_state", {})
        current_project_id = ui_state.get("last_project_id") or self.combo_project.currentData()
        current_name = self.combo_project.currentText()
        self.combo_project.blockSignals(True)
        self.combo_project.clear()
        for project in self._profile.get("projects", []):
            self.combo_project.addItem(project["name"], project["id"])
        index = self.combo_project.findData(current_project_id)
        if index < 0 and current_name:
            index = self.combo_project.findText(current_name)
        self.combo_project.setCurrentIndex(index if index >= 0 else 0)
        self.combo_project.blockSignals(False)
        self._refresh_scripts()

    def _refresh_scripts(self):
        self.list_scripts.clear()
        project = self._current_project()
        ui_state = self._profile.setdefault("ui_state", {})
        if not project:
            self.lbl_script_desc.setText("请先创建项目")
            self.list_script_steps.clear()
            self.lbl_step_detail.setText("请选择步骤")
            ui_state["last_project_id"] = ""
            ui_state["last_script_id"] = ""
            ui_state["last_step_id"] = ""
            return
        ui_state["last_project_id"] = project.get("id", "")
        target_script_id = ui_state.get("last_script_id")
        root_item = QTreeWidgetItem([project.get("name", "当前项目")])
        root_item.setData(0, Qt.ItemDataRole.UserRole, "")
        root_item.setExpanded(True)
        self.list_scripts.addTopLevelItem(root_item)
        first_script_item = None
        for script in project.get("scripts", []):
            item = QTreeWidgetItem([script["name"]])
            item.setData(0, Qt.ItemDataRole.UserRole, script["id"])
            root_item.addChild(item)
            if first_script_item is None:
                first_script_item = item
        if first_script_item is not None:
            target_item = first_script_item
            if target_script_id:
                matched_item = self._find_script_tree_item(target_script_id)
                if matched_item is not None:
                    target_item = matched_item
            self.list_scripts.setCurrentItem(target_item)
        else:
            self.lbl_script_desc.setText("当前项目还没有联调剧本")
            self.list_script_steps.clear()
            self.lbl_step_detail.setText("请选择步骤")
            ui_state["last_script_id"] = ""
            ui_state["last_step_id"] = ""

    def _sync_script_details(self):
        script = self._current_script()
        if not script:
            self.lbl_script_desc.setText("请选择剧本")
            self.list_script_steps.clear()
            self.lbl_step_detail.setText("请选择步骤")
            return
        self.lbl_script_desc.setText(
            f"{script.get('description', '无说明')}\n"
            f"循环次数: {int(script.get('run_count', 1) or 1)} | "
            f"轮次间隔: {int(script.get('cycle_interval_ms', 0) or 0)} ms | "
            f"失败策略: {'失败暂停' if script.get('stop_on_fail', True) else '失败继续'}"
        )
        self._refresh_script_steps()

    def _refresh_script_steps(self):
        self.list_script_steps.clear()
        script = self._current_script()
        ui_state = self._profile.setdefault("ui_state", {})
        if not script:
            self.lbl_step_detail.setText("请选择步骤")
            ui_state["last_step_id"] = ""
            return
        target_step_id = ui_state.get("last_step_id")
        first_step_item = None
        for index, step in enumerate(script.get("steps", []), start=1):
            item = QTreeWidgetItem([f"{index:02d}. {self._step_summary(step)}"])
            item.setData(0, Qt.ItemDataRole.UserRole, step.get("id"))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            self.list_script_steps.addTopLevelItem(item)
            if first_step_item is None:
                first_step_item = item
        if first_step_item is not None:
            target_item = first_step_item
            if target_step_id:
                matched_item = self._find_step_tree_item(target_step_id)
                if matched_item is not None:
                    target_item = matched_item
            self.list_script_steps.setCurrentItem(target_item)
        else:
            self.lbl_step_detail.setText("当前剧本还没有步骤")
            ui_state["last_step_id"] = ""

    def _on_steps_reordered(self):
        """拖拽排序后，按树中当前顺序更新剧本步骤数据并重新渲染序号。"""
        script = self._current_script()
        if not script:
            return
        old_steps = {step.get("id"): step for step in script.get("steps", [])}
        new_order = []
        for index in range(self.list_script_steps.topLevelItemCount()):
            step_id = self.list_script_steps.topLevelItem(index).data(0, Qt.ItemDataRole.UserRole)
            step = old_steps.get(step_id)
            if step is not None:
                new_order.append(step)
        if not new_order:
            return
        script["steps"] = new_order
        self._persist_profile()
        # 记住当前选中步骤，完整刷新列表以更新序号
        current_item = self.list_script_steps.currentItem()
        if current_item:
            self._profile.setdefault("ui_state", {})["last_step_id"] = current_item.data(0, Qt.ItemDataRole.UserRole) or ""
        self._refresh_script_steps()

    def _on_project_selection_changed(self):
        project = self._current_project()
        self._profile.setdefault("ui_state", {})["last_project_id"] = project.get("id", "") if project else ""
        self._refresh_scripts()
        self._refresh_workspace_overview()

    def _on_script_selection_changed(self):
        script = self._current_script()
        self._profile.setdefault("ui_state", {})["last_script_id"] = script.get("id", "") if script else ""
        self._sync_script_details()
        self._refresh_workspace_overview()

    def _on_step_selection_changed(self):
        step = self._current_script_step()
        self._profile.setdefault("ui_state", {})["last_step_id"] = step.get("id", "") if step else ""
        self._sync_selected_step_detail()

    def _sync_selected_step_detail(self):
        step = self._current_script_step()
        if not step:
            self.lbl_step_detail.setText("请选择步骤")
            return
        self.lbl_step_detail.setText(self._step_detail_text(step))

    def _current_script_step(self) -> Optional[Dict[str, Any]]:
        current = self.list_script_steps.currentItem()
        script = self._current_script()
        if current is None or not script:
            return None
        step_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not step_id:
            return None
        return self._find_item_by_id(script.get("steps", []), step_id)

    def _step_group_title(self, step: Dict[str, Any]) -> str:
        step_type = step.get("type", "serial")
        if step_type in {"setting", "shortcut", "serial"}:
            return "指令步骤"
        if step_type in {"capture_snapshot", "append_reference", "compare_reference", "green_screen_detect"}:
            return "图像步骤"
        if step_type in {"set_variable"}:
            return "变量步骤"
        if step_type in {"wait"}:
            return "等待步骤"
        if step_type in {"serial_check"}:
            return "条件步骤"
        return "其他步骤"

    def _find_step_tree_item(self, step_id: str) -> Optional[QTreeWidgetItem]:
        for index in range(self.list_script_steps.topLevelItemCount()):
            item = self.list_script_steps.topLevelItem(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == step_id:
                return item
        return None

    def _step_summary(self, step: Dict[str, Any]) -> str:
        step_type = step.get("type", "serial")
        repeat = max(1, int(step.get("repeat", 1) or 1))
        if step_type == "setting":
            base = f"快捷配置 {step.get('target', '')}"
        elif step_type == "shortcut":
            base = f"快捷指令 {step.get('target', '')}"
        elif step_type == "wait":
            base = f"等待 {float(step.get('seconds', 0.0)):.2f}s"
        elif step_type == "set_variable":
            base = f"变量赋值 {step.get('variable_name', '')}={step.get('variable_value', '')}"
        elif step_type == "capture_snapshot":
            base = f"抓拍保存 {max(1, int(step.get('capture_count', 1) or 1))}张"
        elif step_type == "append_reference":
            category = step.get("reference_category", "default") or "default"
            base = f"加入参考图库[{category}]"
        elif step_type == "compare_reference":
            category = step.get("reference_category", "default") or "default"
            base = f"检查参考图库[{category}]"
        elif step_type == "green_screen_detect":
            base = (
                f"绿屏检测[{step.get('roi_text', '').strip() or '全图'}]"
            )
        elif step_type == "serial_check":
            mode_labels = {"contains": "含", "not_contains": "不含", "exact": "精确", "regex": "正则"}
            mode_label = mode_labels.get(step.get("check_mode", "contains"), "含")
            ref = step.get("check_reference", "")
            base = f"条件检查[{mode_label}] {ref[:30]}{'…' if len(ref) > 30 else ''}"
        elif step_type == "compound":
            sub_count = len(step.get("sub_steps", []))
            base = f"复合步骤 ({sub_count}个子动作)"
        else:
            base = step.get("command", "串口指令") or "串口指令"
        if repeat > 1:
            base += f" x{repeat}"
        return base

    def _step_detail_text(self, step: Dict[str, Any]) -> str:
        lines = [f"类型: {self._step_summary(step)}"]
        if step.get("condition"):
            lines.append(f"执行条件: {step.get('condition')}")
        lines.append(f"执行次数: {max(1, int(step.get('repeat', 1) or 1))}")
        lines.append(f"每次后等待: {int(step.get('delay_ms', 250) or 0)} ms")
        if step.get("type") == "set_variable":
            lines.append(f"变量名: {step.get('variable_name', '')}")
            lines.append(f"变量值: {step.get('variable_value', '')}")
        if step.get("type") == "capture_snapshot":
            lines.append(f"单次抓拍张数: {max(1, int(step.get('capture_count', 1) or 1))}")
            lines.append(f"单次抓拍间隔: {int(step.get('capture_interval_ms', 1000) or 1000)} ms")
        if step.get("type") == "append_reference":
            lines.append(f"参考图库: {step.get('reference_dir', '').strip() or self.edit_reference_dir.text().strip() or '未指定'}")
            lines.append(f"参考分类: {step.get('reference_category', 'default') or 'default'}")
            lines.append(f"图库样本上限: {int(step.get('reference_pool_size', self.spin_reference_pool_size.value()) or self.spin_reference_pool_size.value())}")
        if step.get("type") == "compare_reference":
            lines.append(f"参考图库: {step.get('reference_dir', '').strip() or self.edit_reference_dir.text().strip() or '未指定'}")
            lines.append(f"参考分类: {step.get('reference_category', 'default') or 'default'}")
            lines.append(f"图库样本上限: {int(step.get('reference_pool_size', self.spin_reference_pool_size.value()) or self.spin_reference_pool_size.value())}")
            lines.append(f"ROI 区域: {step.get('roi_text', '').strip() or '全图'}")
            lines.append("热图输出: 开" if step.get("save_diff_heatmap", True) else "热图输出: 关")
            if step.get("result_variable"):
                lines.append(f"结果变量: {step.get('result_variable')}")
            if step.get("recovery_target"):
                lines.append(f"恢复动作: {step.get('recovery_target')}")
            lines.append(f"失败重试: {int(step.get('retry_count', 0) or 0)} 次")
            lines.append(f"重试间隔: {int(step.get('retry_interval_ms', 1000) or 1000)} ms")
            lines.append("失败策略: 不通过暂停" if step.get("pause_on_fail", True) else "失败策略: 仅记录失败")
        if step.get("type") == "green_screen_detect":
            lines.append(f"ROI 区域: {step.get('roi_text', '').strip() or '全图'}")
            lines.append("掩码图输出: 开" if step.get("save_diff_heatmap", True) else "掩码图输出: 关")
            lines.append(f"绿像素占比阈值: {float(step.get('green_ratio_threshold', 0.35) or 0.35):.2f}")
            lines.append(f"最大连通域阈值: {float(step.get('green_area_threshold', 0.18) or 0.18):.2f}")
            lines.append(f"绿色通道领先值: {int(step.get('green_margin', 35) or 35)}")
            lines.append(f"饱和度下限: {int(step.get('green_saturation_threshold', 70) or 70)}")
            lines.append(f"亮度下限: {int(step.get('green_value_threshold', 60) or 60)}")
            lines.append(f"连续命中帧数: {int(step.get('green_check_frames', 3) or 3)}")
            lines.append(f"取样间隔: {int(step.get('green_check_interval_ms', 250) or 250)} ms")
            if step.get("result_variable"):
                lines.append(f"结果变量: {step.get('result_variable')}")
            if step.get("recovery_target"):
                lines.append(f"恢复动作: {step.get('recovery_target')}")
            lines.append(f"失败重试: {int(step.get('retry_count', 0) or 0)} 次")
            lines.append(f"重试间隔: {int(step.get('retry_interval_ms', 1000) or 1000)} ms")
            lines.append("失败策略: 检出即暂停" if step.get("pause_on_fail", True) else "失败策略: 仅记录命中")
        if step.get("type") == "serial_check":
            mode_labels = {"contains": "包含", "not_contains": "不包含", "exact": "精确匹配", "regex": "正则匹配"}
            lines.append(f"发送指令: {step.get('command', '')}")
            lines.append(f"参考值: {step.get('check_reference', '')}")
            lines.append(f"匹配方式: {mode_labels.get(step.get('check_mode', 'contains'), '包含')}")
            lines.append(f"等待超时: {int(step.get('check_timeout_ms', 3000) or 3000)} ms")
            fail_label = "停止剧本" if step.get("check_fail_action", "stop") == "stop" else "继续执行"
            lines.append(f"不匹配时: {fail_label}")
            if step.get("result_variable"):
                lines.append(f"结果变量: {step.get('result_variable')}")
        if step.get("note"):
            lines.append(f"说明: {step.get('note')}")
        return "\n".join(lines)

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
        self._profile["serial"]["tab_passthrough"] = self.chk_tab_passthrough.isChecked()
        self._profile["serial"]["newline_mode"] = self.combo_newline.currentText()
        self._persist_profile()

        self.btn_serial_connect.setText("断开串口")
        self.lbl_serial_chip.setText(f"串口在线: {port}")
        self._log(f"串口已连接: {port} @ {self.combo_baud.currentText()}")
        self._append_terminal(f"[SYS] 已连接 {port} @ {self.combo_baud.currentText()}")
        self._reader_thread = SerialReaderThread(self._serial)
        self._reader_thread.data_received.connect(self._on_serial_data_received)
        self._reader_thread.error_occurred.connect(self._on_serial_error)
        self._reader_thread.disconnected.connect(self._on_serial_disconnected)
        self._reader_thread.start()
        self._serial_flush_timer.start()
        if self.chk_auto_su.isChecked():
            self._queue_commands([{"type": "serial", "command": "su", "delay_seconds": 0.0, "source": "连接自动初始化"}])

    def _disconnect_serial(self):
        self._queue_timer.stop()
        self._command_queue.clear()
        self._serial_flush_timer.stop()
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
        self._append_terminal("[SYS] 串口已断开")
        self._log("串口已断开")

    def _on_serial_data_received(self, data: bytes):
        self._serial_rx_buffer.extend(data)
        self._process_serial_rx_buffer()

    def _on_serial_error(self, message: str):
        self._append_terminal(f"[ERR] {message}")
        self._log(f"串口读取异常: {message}", "ERROR")

    def _on_serial_disconnected(self):
        if self._serial and getattr(self._serial, "is_open", False):
            return
        self.btn_serial_connect.setText("连接串口")
        self.lbl_serial_chip.setText("串口未连接")
        self._append_terminal("[SYS] 连接已断开")

    def _send_manual_serial_command(self):
        command = self.edit_serial_cmd.text().strip()
        if not command:
            return
        self._send_serial_command(command, source="手工发送")
        self.edit_serial_cmd.clear()

    def _on_send(self):
        command = self.edit_serial_cmd.text()
        self._send_serial_command(command, source="串口终端")
        stripped = command.strip()
        if stripped and (not self._cmd_history or self._cmd_history[-1] != stripped):
            self._cmd_history.append(stripped)
        self._history_idx = -1
        self._tab_candidates = []
        self._tab_idx = -1
        self.edit_serial_cmd.clear()

    def _send_serial_command(self, command: str, source: str = "串口发送") -> bool:
        if not self._serial or not getattr(self._serial, "is_open", False):
            self._log("串口未连接，无法发送指令", "ERROR")
            return False
        newline_map = {"\\r\\n": "\r\n", "\\n": "\n", "\\r": "\r", "无": ""}
        newline = newline_map.get(self.combo_newline.currentText(), "\r\n")
        if not self.chk_newline.isChecked():
            newline = ""
        payload = command + newline
        try:
            self._serial.write(payload.encode("utf-8", errors="ignore"))
            self._append_terminal(f">>> {command}" if command else ">>> [ENTER]")
            self._log(f"{source}: {command}")
            return True
        except Exception as exc:
            self._log(f"串口发送失败: {exc}", "ERROR")
            return False

    def _append_terminal(self, text: str):
        self.serial_terminal.appendPlainText(text)
        self.serial_terminal.verticalScrollBar().setValue(self.serial_terminal.verticalScrollBar().maximum())

    def _process_serial_rx_buffer(self):
        normalized = self._serial_rx_buffer.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if b"\n" not in normalized:
            return
        parts = normalized.split(b"\n")
        for part in parts[:-1]:
            line = part.decode("utf-8", errors="replace")
            if line:
                self._append_terminal(line)
                self._collect_rx_paths(line)
                if self._serial_check_timer.isActive():
                    self._serial_check_lines.append(line)
        self._serial_rx_buffer = bytearray(parts[-1])

    def _flush_serial_rx_buffer(self):
        if not self._serial_rx_buffer:
            return
        line = self._serial_rx_buffer.decode("utf-8", errors="replace")
        self._serial_rx_buffer.clear()
        if line.strip():
            self._append_terminal(line)
            self._collect_rx_paths(line)
            if self._serial_check_timer.isActive():
                self._serial_check_lines.append(line)

    def _collect_rx_paths(self, text: str):
        for path in re.findall(r"(?:/[A-Za-z0-9._-]+)+/?", text):
            if path not in self._rx_path_cache:
                self._rx_path_cache.insert(0, path)
        self._rx_path_cache = self._rx_path_cache[:120]

    def _check_serial_lines_match(self, lines: List[str], reference: str, mode: str) -> bool:
        combined_nl = "\n".join(lines)        # 行内精确搜索
        combined_flat = "".join(lines)        # 跨行 token 桥接（串口换行切词时仍能匹配）
        if mode == "contains":
            return reference in combined_nl or reference in combined_flat
        if mode == "not_contains":
            return reference not in combined_nl and reference not in combined_flat
        if mode == "exact":
            return any(line.strip() == reference.strip() for line in lines)
        if mode == "regex":
            try:
                return bool(re.search(reference, combined_nl)) or bool(re.search(reference, combined_flat))
            except re.error:
                return False
        return reference in combined_nl or reference in combined_flat

    def _on_serial_check_tick(self):
        if self._serial_check_action is None:
            self._serial_check_timer.stop()
            return
        reference = self._serial_check_action.get("check_reference", "")
        mode = self._serial_check_action.get("check_mode", "contains")
        matched = self._check_serial_lines_match(self._serial_check_lines, reference, mode)
        if matched:
            self._serial_check_timer.stop()
            source = self._serial_check_action.get("source", "条件检查")
            result_var = self._serial_check_action.get("result_variable", "")
            if result_var:
                self._script_variables[result_var] = True
            self._log(f"条件检查通过: {source}")
            self._finish_serial_check(success=True)
            return
        if time.time() >= self._serial_check_deadline:
            self._serial_check_timer.stop()
            source = self._serial_check_action.get("source", "条件检查")
            result_var = self._serial_check_action.get("result_variable", "")
            if result_var:
                self._script_variables[result_var] = False
            fail_action = self._serial_check_action.get("check_fail_action", "stop")
            recv_count = len(self._serial_check_lines)
            preview = self._serial_check_lines[:5]
            preview_str = " | ".join(repr(l) for l in preview)
            if recv_count > 5:
                preview_str += f" …({recv_count} 行)"
            self._log(f"条件检查超时/不匹配: {source}（{recv_count} 行回发）回发预览: {preview_str}", "WARN")
            self._finish_serial_check(success=(fail_action == "continue"))

    def _finish_serial_check(self, success: bool):
        action = self._serial_check_action
        self._serial_check_action = None
        if action is None:
            return
        stop_on_fail = bool(action.get("stop_on_fail", True))
        source = action.get("source", "条件检查")
        delay_seconds = float(action.get("delay_seconds", 0.0) or 0.0)
        if not success and stop_on_fail:
            self._queue_timer.stop()
            self._queue_paused = True
            self._log(f"条件检查失败，已暂停: {source}", "ERROR")
            self._queue_busy = False
            # 冻结计时
            if self._run_metrics:
                self._paused_elapsed = time.time() - self._run_metrics.get('start_time', time.time())
            self._run_stats_timer.stop()
            self._update_run_stats(force_status="失败暂停")
            # >>> AI 集成：条件检查失败事件（仅步骤开启 notify_on_fail 时）
            if action.get("notify_on_fail", False):
                # 收集检查条件和实际结果
                _mode_labels = {"contains": "包含", "not_contains": "不包含", "exact": "精确匹配", "regex": "正则匹配"}
                check_mode = action.get("check_mode", "contains")
                check_ref = action.get("check_reference", "")
                actual_lines = getattr(self, '_serial_check_lines', []) or []
                actual_preview = " | ".join(repr(l) for l in actual_lines[:5])
                if len(actual_lines) > 5:
                    actual_preview += f" …(共{len(actual_lines)}行)"
                elif not actual_lines:
                    actual_preview = "（无回发数据）"

                reason_detail = (
                    f"条件检查失败: {source}\n"
                    f"**检查模式：** {_mode_labels.get(check_mode, check_mode)}\n"
                    f"**期望值：** `{check_ref}`\n"
                    f"**实际回发：** `{actual_preview}`"
                )

                try:
                    from core.event_bus import get_event_bus, Events
                    _cycle = self._run_metrics.get('current_cycle', 1) if self._run_metrics else 1
                    _total = self._run_metrics.get('total_cycles', 1) if self._run_metrics else 1
                    get_event_bus().emit_async(
                        Events.CONDITION_CHECK_FAILED,
                        script_name=self._run_metrics.get('script_name', '') if self._run_metrics else '',
                        step_name=source, reason=reason_detail,
                        notify_title=action.get("notify_title", ""),
                        notify_content=action.get("notify_content", ""),
                        include_logs=action.get("include_logs", True),
                        use_ai_summary=action.get("use_ai_summary", False),
                        current_cycle=_cycle,
                        total_cycles=_total,
                    )
                    self._failure_notified = True
                except Exception:
                    pass
            self._save_execution_state()
            self._refresh_queue_controls()
            return
        if not success:
            self._log(f"条件检查失败但按配置继续: {source}", "WARN")
        self._queue_busy = False
        self._queue_timer.start(max(0, int(delay_seconds * 1000)))
        self._refresh_queue_controls()

    def _history_prev(self):
        if not self._cmd_history:
            return
        if self._history_idx == -1:
            self._history_idx = len(self._cmd_history) - 1
        elif self._history_idx > 0:
            self._history_idx -= 1
        self.edit_serial_cmd.setText(self._cmd_history[self._history_idx])
        self.edit_serial_cmd.setCursorPosition(len(self.edit_serial_cmd.text()))

    def _history_next(self):
        if not self._cmd_history:
            return
        if self._history_idx == -1:
            return
        if self._history_idx < len(self._cmd_history) - 1:
            self._history_idx += 1
            self.edit_serial_cmd.setText(self._cmd_history[self._history_idx])
        else:
            self._history_idx = -1
            self.edit_serial_cmd.clear()
            return
        self.edit_serial_cmd.setCursorPosition(len(self.edit_serial_cmd.text()))

    def _is_tab_passthrough_enabled(self) -> bool:
        return self.chk_tab_passthrough.isChecked()

    def _send_tab_character(self):
        if not self._serial or not getattr(self._serial, "is_open", False):
            self._log("串口未连接，无法发送 Tab", "ERROR")
            return
        try:
            self._serial.write(b"\t")
            self._append_terminal(">>> [TAB]")
            self._log("已发送 Tab 到设备")
        except Exception as exc:
            self._log(f"Tab 发送失败: {exc}", "ERROR")

    def _on_tab_complete(self):
        current = self.edit_serial_cmd.text()
        if not self._tab_candidates:
            self._pre_tab_text = current
            parts = current.rsplit(" ", 1)
            if len(parts) == 2:
                base_text = parts[0] + " "
                prefix_word = parts[1].lower()
            else:
                base_text = ""
                prefix_word = current.lower()

            seen = set()
            candidates: List[str] = []

            def _add(text: str, keep_base: bool):
                full = (base_text + text) if keep_base else text
                if full not in seen:
                    seen.add(full)
                    candidates.append(full)

            if prefix_word.startswith("/"):
                for path in self._rx_path_cache:
                    if path.lower().startswith(prefix_word):
                        _add(path, True)

            for command in self._get_all_known_commands():
                lowered = command.lower()
                if not base_text and lowered.startswith(prefix_word):
                    _add(command, False)
                elif base_text:
                    last = command.split(" ")[-1] if " " in command else command
                    if last.lower().startswith(prefix_word):
                        _add(last, True)
                    if lowered.startswith(current.lower()):
                        _add(command, False)

            if not candidates:
                return
            self._tab_candidates = candidates
            self._tab_idx = -1

        self._tab_idx = (self._tab_idx + 1) % len(self._tab_candidates)
        candidate = self._tab_candidates[self._tab_idx]
        self.edit_serial_cmd.setText(candidate)
        self.edit_serial_cmd.setCursorPosition(len(candidate))

    def _get_all_known_commands(self) -> List[str]:
        commands: List[str] = list(reversed(self._cmd_history))
        for item in self._profile.get("quick_settings", []):
            commands.extend(item.get("commands", []))
        for item in self._profile.get("shortcuts", []):
            commands.extend(item.get("commands", []))
        for project in self._profile.get("projects", []):
            for script in project.get("scripts", []):
                for step in script.get("steps", []):
                    if isinstance(step, dict):
                        if step.get("type") == "serial" and step.get("command"):
                            commands.append(step.get("command", ""))
                        continue
                    if isinstance(step, str) and not step.startswith(("setting:", "shortcut:", "wait:")):
                        commands.append(step)
        deduped: List[str] = []
        seen = set()
        for command in commands:
            if command and command not in seen:
                seen.add(command)
                deduped.append(command)
        return deduped

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            if obj is self.edit_serial_cmd:
                if key == Qt.Key.Key_Tab:
                    if self._is_tab_passthrough_enabled():
                        self._send_tab_character()
                    else:
                        self._on_tab_complete()
                    return True
                if key == Qt.Key.Key_Up:
                    self._history_prev()
                    return True
                if key == Qt.Key.Key_Down:
                    self._history_next()
                    return True
                if modifiers == Qt.KeyboardModifier.ControlModifier:
                    control_map = {
                        Qt.Key.Key_C: (b"\x03", "Ctrl+C"),
                        Qt.Key.Key_D: (b"\x04", "Ctrl+D"),
                        Qt.Key.Key_L: (b"\x0c", "Ctrl+L"),
                        Qt.Key.Key_Z: (b"\x1a", "Ctrl+Z"),
                    }
                    if key in control_map and self._serial and getattr(self._serial, "is_open", False):
                        raw, label = control_map[key]
                        try:
                            self._serial.write(raw)
                            self._append_terminal(f">>> [{label}]")
                            self._log(f"已发送 {label}")
                        except Exception as exc:
                            self._log(f"发送 {label} 失败: {exc}", "ERROR")
                        return True
                self._tab_candidates = []
                self._tab_idx = -1

            if obj is self.serial_terminal:
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._on_send()
                    return True
                if key == Qt.Key.Key_Tab:
                    if self._is_tab_passthrough_enabled():
                        self._send_tab_character()
                    else:
                        self._on_tab_complete()
                    self.edit_serial_cmd.setFocus()
                    return True
                if key == Qt.Key.Key_Up:
                    self._history_prev()
                    self.edit_serial_cmd.setFocus()
                    return True
                if key == Qt.Key.Key_Down:
                    self._history_next()
                    self.edit_serial_cmd.setFocus()
                    return True
                if key == Qt.Key.Key_Backspace:
                    current = self.edit_serial_cmd.text()
                    if current:
                        self.edit_serial_cmd.setText(current[:-1])
                        self.edit_serial_cmd.setFocus()
                    return True
                if modifiers == Qt.KeyboardModifier.ControlModifier:
                    control_map = {
                        Qt.Key.Key_C: (b"\x03", "Ctrl+C"),
                        Qt.Key.Key_D: (b"\x04", "Ctrl+D"),
                        Qt.Key.Key_L: (b"\x0c", "Ctrl+L"),
                        Qt.Key.Key_Z: (b"\x1a", "Ctrl+Z"),
                    }
                    if key in control_map and self._serial and getattr(self._serial, "is_open", False):
                        raw, label = control_map[key]
                        try:
                            self._serial.write(raw)
                            self._append_terminal(f">>> [{label}]")
                            self._log(f"已发送 {label}")
                        except Exception as exc:
                            self._log(f"发送 {label} 失败: {exc}", "ERROR")
                        return True
                char = event.text()
                if char and char.isprintable() and modifiers in (
                    Qt.KeyboardModifier.NoModifier,
                    Qt.KeyboardModifier.ShiftModifier,
                ):
                    self.edit_serial_cmd.insert(char)
                    self.edit_serial_cmd.setFocus()
                    return True
        return super().eventFilter(obj, event)

    def _queue_commands(self, steps: List[Dict[str, Any]]):
        self._command_queue.extend(steps)
        self._queue_paused = False
        self._refresh_queue_controls()
        if not self._queue_timer.isActive():
            self._process_next_queue_item()

    def _process_next_queue_item(self):
        if self._queue_paused:
            self._refresh_queue_controls()
            return
        if not self._command_queue:
            self._queue_busy = False
            self._log("执行队列完成")
            self._finish_queue_run("执行队列完成")
            return
        self._queue_busy = True
        self._refresh_queue_controls()
        action = self._command_queue.pop(0)
        self._highlight_running_step(action.get("step_id"))
        action_type = action.get("type", "serial")
        delay_seconds = float(action.get("delay_seconds", 0.0) or 0.0)
        source = self._interpolate_text(action.get("source", "设备联调"))
        stop_on_fail = bool(action.get("stop_on_fail", True))
        retry_count = int(action.get("retry_count", 0) or 0)
        retry_interval_ms = int(action.get("retry_interval_ms", 1000) or 1000)

        if not self._evaluate_condition(action.get("condition", "")):
            self._log(f"条件不满足，跳过: {source}", "WARN")
            self._queue_busy = False
            self._queue_timer.start(max(0, int(delay_seconds * 1000)))
            self._refresh_queue_controls()
            return

        success = True
        if action_type == "serial":
            success = self._send_serial_command(self._interpolate_text(action.get("command", "")), source=source)
        elif action_type == "wait":
            self._log(f"等待 {delay_seconds:.2f}s: {source}")
        elif action_type == "set_variable":
            variable_name = action.get("variable_name", "").strip()
            if variable_name:
                variable_value = self._coerce_variable_value(action.get("variable_value", ""))
                self._script_variables[variable_name] = variable_value
                self._log(f"变量写入: {variable_name}={variable_value}")
        elif action_type == "cycle_marker":
            cycle_idx = int(action.get("cycle_index", 1))
            total = int(action.get("total_cycles", 1))
            if self._run_metrics:
                self._run_metrics['current_cycle'] = cycle_idx
                self._run_metrics['total_cycles'] = total
            self._log(f"--- 第 {cycle_idx}/{total} 轮开始 ---")
        elif action_type == "capture_snapshot":
            success = bool(self._capture_snapshot_frame(file_prefix=action.get("file_prefix", "snapshot")))
        elif action_type == "append_reference":
            success = self._append_current_frame_to_reference_pool(
                quiet=True,
                category=action.get("reference_category", "default"),
                reference_dir_override=action.get("reference_dir", ""),
            )
        elif action_type == "compare_reference":
            success = self._compare_against_reference(
                pause_on_fail=bool(action.get("pause_on_fail", True)),
                source=source,
                save_snapshot=bool(action.get("save_snapshot", True)),
                category=action.get("reference_category", "default"),
                reference_dir=action.get("reference_dir", ""),
                reference_pool_size=int(action.get("reference_pool_size", self.spin_reference_pool_size.value()) or self.spin_reference_pool_size.value()),
                save_diff_heatmap=bool(action.get("save_diff_heatmap", True)),
                roi_text=action.get("roi_text", ""),
                result_variable=action.get("result_variable", ""),
                notify_on_fail=bool(action.get("notify_on_fail", False)),
                notify_title=action.get("notify_title", ""),
                notify_content=action.get("notify_content", ""),
                include_logs=action.get("include_logs", True),
                use_ai_summary=action.get("use_ai_summary", False),
            )
        elif action_type == "green_screen_detect":
            success = self._detect_green_screen(
                pause_on_fail=bool(action.get("pause_on_fail", True)),
                source=source,
                save_snapshot=bool(action.get("save_snapshot", True)),
                roi_text=action.get("roi_text", ""),
                result_variable=action.get("result_variable", ""),
                save_diff_heatmap=bool(action.get("save_diff_heatmap", True)),
                green_ratio_threshold=float(action.get("green_ratio_threshold", 0.35) or 0.35),
                green_area_threshold=float(action.get("green_area_threshold", 0.18) or 0.18),
                green_margin=int(action.get("green_margin", 35) or 35),
                green_saturation_threshold=int(action.get("green_saturation_threshold", 70) or 70),
                green_value_threshold=int(action.get("green_value_threshold", 60) or 60),
                green_check_frames=int(action.get("green_check_frames", 3) or 3),
                green_check_interval_ms=int(action.get("green_check_interval_ms", 250) or 250),
            )
        elif action_type == "serial_check":
            cmd = self._interpolate_text(action.get("command", ""))
            send_ok = self._send_serial_command(cmd, source=source) if cmd else True
            if send_ok:
                timeout_ms = int(action.get("check_timeout_ms", 3000) or 3000)
                self._serial_check_action = action
                self._serial_check_lines = []
                self._serial_check_deadline = time.time() + timeout_ms / 1000.0
                self._serial_check_timer.start()
                self._queue_busy = True
                self._refresh_queue_controls()
                return  # 等待 _on_serial_check_tick 完成后续逻辑
            success = False  # 发送失败直接走失败分支
        elif action_type == "ai_notify":
            # >>> AI 集成：AI 通知步骤
            try:
                from core.event_bus import get_event_bus, Events
                get_event_bus().emit_async(
                    Events.AI_NOTIFY_TRIGGERED,
                    script_name=self._run_metrics.get('script_name', '') if self._run_metrics else '',
                    step_name=source,
                    prompt_template=action.get('prompt_template', ''),
                    include_logs=action.get('include_logs', True),
                )
                self._log(f"AI 通知已触发: {source}")
            except Exception as e:
                self._log(f"AI 通知失败: {e}", "WARN")

        if not success and retry_count > 0:
            action["retry_count"] = retry_count - 1
            self._command_queue.insert(0, action)
            self._log(f"执行失败，准备重试: {source}，剩余 {retry_count} 次", "WARN")
            self._queue_busy = False
            self._queue_timer.start(max(0, retry_interval_ms))
            self._refresh_queue_controls()
            return

        if not success and action.get("recovery_target"):
            recovery_item = self._find_item_by_name(self._profile.get("shortcuts", []), action.get("recovery_target", ""))
            recovery_actions = self._build_actions_from_shortcut(recovery_item, f"恢复动作 {action.get('recovery_target', '')}", stop_on_fail=False)
            if recovery_actions:
                self._command_queue = recovery_actions + self._command_queue
                self._log(f"已插入失败恢复动作: {action.get('recovery_target', '')}", "WARN")

        if not success and stop_on_fail:
            self._queue_timer.stop()
            self._queue_paused = True
            self._log(f"执行失败，已暂停: {source}", "ERROR")
            self._queue_busy = False
            # 冻结计时
            if self._run_metrics:
                self._paused_elapsed = time.time() - self._run_metrics.get('start_time', time.time())
            self._run_stats_timer.stop()
            self._update_run_stats(force_status="失败暂停")
            # >>> AI 集成：步骤失败暂停事件（仅步骤开启 notify_on_fail 时）
            if action.get("notify_on_fail", False):
                try:
                    from core.event_bus import get_event_bus, Events
                    _cycle = self._run_metrics.get('current_cycle', 1) if self._run_metrics else 1
                    _total = self._run_metrics.get('total_cycles', 1) if self._run_metrics else 1
                    get_event_bus().emit_async(
                        Events.STEP_FAILED,
                        script_name=self._run_metrics.get('script_name', '') if self._run_metrics else '',
                        step_name=source, reason=f"执行失败: {source}",
                        notify_title=action.get("notify_title", ""),
                        notify_content=action.get("notify_content", ""),
                        include_logs=action.get("include_logs", True),
                        use_ai_summary=action.get("use_ai_summary", False),
                        current_cycle=_cycle,
                        total_cycles=_total,
                    )
                    self._failure_notified = True
                except Exception:
                    pass
            self._save_execution_state()
            self._refresh_queue_controls()
            return
        if not success:
            self._log(f"执行失败但按配置继续: {source}", "WARN")

        self._queue_busy = False
        self._queue_timer.start(max(0, int(delay_seconds * 1000)))
        self._refresh_queue_controls()

    def _build_actions_from_shortcut(self, item: Optional[Dict[str, Any]], source_prefix: str, stop_on_fail: bool = True) -> List[Dict[str, Any]]:
        if not item:
            return []
        action_type = item.get("action_type", "serial_bundle")
        if action_type == "camera_snapshot":
            capture_count = max(1, int(item.get("capture_count", 1) or 1))
            capture_interval = max(100, int(item.get("capture_interval_ms", 1000) or 1000)) / 1000.0
            actions: List[Dict[str, Any]] = []
            for index in range(capture_count):
                actions.append({
                    "type": "capture_snapshot",
                    "delay_seconds": capture_interval if index < capture_count - 1 else 0.25,
                    "source": f"{source_prefix} {item['name']}",
                    "stop_on_fail": stop_on_fail,
                    "file_prefix": "shortcut_snapshot",
                })
            return actions
        if action_type == "append_reference":
            return [{
                "type": "append_reference",
                "delay_seconds": 0.25,
                "source": f"{source_prefix} {item['name']}",
                "stop_on_fail": stop_on_fail,
                "reference_category": item.get("reference_category", "default"),
                "reference_dir": item.get("reference_dir", ""),
                "reference_pool_size": int(item.get("reference_pool_size", 5) or 5),
            }]
        if action_type == "compare_reference":
            return [{
                "type": "compare_reference",
                "pause_on_fail": True,
                "delay_seconds": 0.25,
                "source": f"{source_prefix} {item['name']}",
                "stop_on_fail": stop_on_fail,
                "save_snapshot": True,
                "reference_category": item.get("reference_category", "default"),
                "reference_dir": item.get("reference_dir", ""),
                "reference_pool_size": int(item.get("reference_pool_size", 5) or 5),
                "save_diff_heatmap": bool(item.get("save_diff_heatmap", True)),
                "roi_text": item.get("roi_text", ""),
            }]
        if action_type == "green_screen_detect":
            return [{
                "type": "green_screen_detect",
                "pause_on_fail": True,
                "delay_seconds": 0.25,
                "source": f"{source_prefix} {item['name']}",
                "stop_on_fail": stop_on_fail,
                "save_snapshot": True,
                "roi_text": item.get("roi_text", ""),
                "save_diff_heatmap": bool(item.get("save_diff_heatmap", True)),
                "green_ratio_threshold": item.get("green_ratio_threshold", 0.35),
                "green_area_threshold": item.get("green_area_threshold", 0.18),
                "green_margin": item.get("green_margin", 35),
                "green_saturation_threshold": item.get("green_saturation_threshold", 70),
                "green_value_threshold": item.get("green_value_threshold", 60),
                "green_check_frames": item.get("green_check_frames", 3),
                "green_check_interval_ms": item.get("green_check_interval_ms", 250),
            }]
        return [
            {"type": "serial", "command": command, "delay_seconds": 0.25, "source": f"{source_prefix} {item['name']}", "stop_on_fail": stop_on_fail}
            for command in item.get("commands", []) if command
        ]

    def _build_actions_from_step(self, step: Dict[str, Any], stop_on_fail: bool = True) -> List[Dict[str, Any]]:
        step_type = step.get("type", "serial")
        repeat = max(1, int(step.get("repeat", 1) or 1))
        delay_seconds = max(0.0, int(step.get("delay_ms", 250) or 0) / 1000.0)
        source = step.get("note") or self._step_summary(step)
        actions: List[Dict[str, Any]] = []

        for _ in range(repeat):
            if step_type == "setting":
                item = self._find_item_by_name(self._profile.get("quick_settings", []), step.get("target", ""))
                if item:
                    for command in item.get("commands", []):
                        actions.append({"type": "serial", "command": command, "delay_seconds": delay_seconds, "source": source, "stop_on_fail": stop_on_fail, "condition": step.get("condition", ""), "step_id": step.get("id", "")})
            elif step_type == "shortcut":
                item = self._find_item_by_name(self._profile.get("shortcuts", []), step.get("target", ""))
                shortcut_actions = self._build_actions_from_shortcut(item, "剧本步骤", stop_on_fail=stop_on_fail)
                for shortcut_action in shortcut_actions:
                    shortcut_action["delay_seconds"] = delay_seconds
                    shortcut_action["condition"] = step.get("condition", "")
                    shortcut_action["step_id"] = step.get("id", "")
                actions.extend(shortcut_actions)
            elif step_type == "wait":
                actions.append({"type": "wait", "delay_seconds": float(step.get("seconds", 0.0) or 0.0), "source": source, "stop_on_fail": stop_on_fail, "condition": step.get("condition", ""), "step_id": step.get("id", "")})
            elif step_type == "set_variable":
                actions.append({
                    "type": "set_variable",
                    "delay_seconds": delay_seconds,
                    "source": source,
                    "stop_on_fail": False,
                    "condition": step.get("condition", ""),
                    "variable_name": step.get("variable_name", ""),
                    "variable_value": step.get("variable_value", ""),
                    "step_id": step.get("id", ""),
                })
            elif step_type == "capture_snapshot":
                capture_count = max(1, int(step.get("capture_count", 1) or 1))
                capture_interval = max(100, int(step.get("capture_interval_ms", 1000) or 1000)) / 1000.0
                for index in range(capture_count):
                    actions.append({
                        "type": "capture_snapshot",
                        "delay_seconds": capture_interval if index < capture_count - 1 else delay_seconds,
                        "source": source,
                        "stop_on_fail": stop_on_fail,
                        "file_prefix": "script_snapshot",
                        "condition": step.get("condition", ""),
                        "step_id": step.get("id", ""),
                    })
            elif step_type == "append_reference":
                actions.append({
                    "type": "append_reference",
                    "delay_seconds": delay_seconds,
                    "source": source,
                    "stop_on_fail": stop_on_fail,
                    "condition": step.get("condition", ""),
                    "reference_category": step.get("reference_category", "default"),
                    "reference_dir": step.get("reference_dir", ""),
                    "reference_pool_size": int(step.get("reference_pool_size", 5) or 5),
                    "step_id": step.get("id", ""),
                })
            elif step_type == "compare_reference":
                actions.append({
                    "type": "compare_reference",
                    "pause_on_fail": bool(step.get("pause_on_fail", True)),
                    "delay_seconds": delay_seconds,
                    "source": source,
                    "stop_on_fail": stop_on_fail,
                    "save_snapshot": True,
                    "retry_count": int(step.get("retry_count", 0) or 0),
                    "retry_interval_ms": int(step.get("retry_interval_ms", 1000) or 1000),
                    "condition": step.get("condition", ""),
                    "reference_category": step.get("reference_category", "default"),
                    "reference_dir": step.get("reference_dir", ""),
                    "reference_pool_size": int(step.get("reference_pool_size", 5) or 5),
                    "save_diff_heatmap": bool(step.get("save_diff_heatmap", True)),
                    "roi_text": step.get("roi_text", ""),
                    "result_variable": step.get("result_variable", ""),
                    "recovery_target": step.get("recovery_target", ""),
                    "step_id": step.get("id", ""),
                    "notify_on_fail": bool(step.get("notify_on_fail", False)),
                    "notify_title": step.get("notify_title", ""),
                    "notify_content": step.get("notify_content", ""),
                    "include_logs": bool(step.get("include_logs", True)),
                    "use_ai_summary": bool(step.get("use_ai_summary", False)),
                })
            elif step_type == "green_screen_detect":
                actions.append({
                    "type": "green_screen_detect",
                    "pause_on_fail": bool(step.get("pause_on_fail", True)),
                    "delay_seconds": delay_seconds,
                    "source": source,
                    "stop_on_fail": stop_on_fail,
                    "save_snapshot": True,
                    "retry_count": int(step.get("retry_count", 0) or 0),
                    "retry_interval_ms": int(step.get("retry_interval_ms", 1000) or 1000),
                    "condition": step.get("condition", ""),
                    "roi_text": step.get("roi_text", ""),
                    "save_diff_heatmap": bool(step.get("save_diff_heatmap", True)),
                    "result_variable": step.get("result_variable", ""),
                    "recovery_target": step.get("recovery_target", ""),
                    "step_id": step.get("id", ""),
                    "green_ratio_threshold": float(step.get("green_ratio_threshold", 0.35) or 0.35),
                    "green_area_threshold": float(step.get("green_area_threshold", 0.18) or 0.18),
                    "green_margin": int(step.get("green_margin", 35) or 35),
                    "green_saturation_threshold": int(step.get("green_saturation_threshold", 70) or 70),
                    "green_value_threshold": int(step.get("green_value_threshold", 60) or 60),
                    "green_check_frames": int(step.get("green_check_frames", 3) or 3),
                    "green_check_interval_ms": int(step.get("green_check_interval_ms", 250) or 250),
                    "notify_on_fail": bool(step.get("notify_on_fail", False)),
                    "notify_title": step.get("notify_title", ""),
                    "notify_content": step.get("notify_content", ""),
                    "include_logs": bool(step.get("include_logs", True)),
                    "use_ai_summary": bool(step.get("use_ai_summary", False)),
                })
            elif step_type == "serial_check":
                command = step.get("command", "").strip()
                reference = step.get("check_reference", "")
                _mode_lbls = {"contains": "含", "not_contains": "不含", "exact": "精确", "regex": "正则"}
                _mode_lbl = _mode_lbls.get(step.get("check_mode", "contains"), "含")
                check_source = step.get("note") or f"条件检查[{_mode_lbl}] {reference}"
                if command:
                    actions.append({
                        "type": "serial_check",
                        "command": command,
                        "check_reference": reference,
                        "check_mode": step.get("check_mode", "contains"),
                        "check_timeout_ms": int(step.get("check_timeout_ms", 3000) or 3000),
                        "check_fail_action": step.get("check_fail_action", "stop"),
                        "result_variable": step.get("result_variable", ""),
                        "delay_seconds": delay_seconds,
                        "source": check_source,
                        "stop_on_fail": stop_on_fail,
                        "condition": step.get("condition", ""),
                        "step_id": step.get("id", ""),
                        "notify_on_fail": bool(step.get("notify_on_fail", False)),
                        "notify_title": step.get("notify_title", ""),
                        "notify_content": step.get("notify_content", ""),
                        "include_logs": bool(step.get("include_logs", True)),
                        "use_ai_summary": bool(step.get("use_ai_summary", False)),
                    })
            elif step_type == "ai_notify":
                actions.append({
                    "type": "ai_notify",
                    "delay_seconds": delay_seconds,
                    "source": source,
                    "stop_on_fail": False,
                    "condition": step.get("condition", ""),
                    "prompt_template": step.get("prompt_template", ""),
                    "include_logs": bool(step.get("include_logs", True)),
                    "step_id": step.get("id", ""),
                })
            elif step_type == "compound":
                for sub_step in step.get("sub_steps", []):
                    sub_step_copy = dict(sub_step)
                    if not sub_step_copy.get("id"):
                        sub_step_copy["id"] = step.get("id", "")
                    actions.extend(self._build_actions_from_step(sub_step_copy, stop_on_fail=stop_on_fail))
            else:
                command = step.get("command", "").strip()
                if command:
                    actions.append({"type": "serial", "command": command, "delay_seconds": delay_seconds, "source": source, "stop_on_fail": stop_on_fail, "condition": step.get("condition", ""), "step_id": step.get("id", "")})
        return actions

    def _build_actions_from_script(self, script: Dict[str, Any], start_cycle: int = 1) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        run_count = max(1, int(script.get("run_count", 1) or 1))
        cycle_interval = max(0, int(script.get("cycle_interval_ms", 0) or 0))
        stop_on_fail = bool(script.get("stop_on_fail", True))
        for run_index in range(start_cycle - 1, run_count):
            # 轮次标记（用于运行时跟踪当前轮次）
            actions.append({
                "type": "cycle_marker",
                "cycle_index": run_index + 1,
                "total_cycles": run_count,
                "delay_seconds": 0,
                "source": f"轮次 {run_index + 1}/{run_count}",
                "stop_on_fail": False,
            })
            for step in script.get("steps", []):
                actions.extend(self._build_actions_from_step(step, stop_on_fail=stop_on_fail))
            if cycle_interval > 0 and run_index < run_count - 1:
                actions.append({
                    "type": "wait",
                    "delay_seconds": cycle_interval / 1000.0,
                    "source": f"剧本轮次间隔 {cycle_interval} ms",
                    "stop_on_fail": stop_on_fail,
                })
        return actions

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
        self._camera_timer.start(max(50, interval))
        self.btn_camera_toggle.setText("断开预览")
        self.lbl_camera_chip.setText(f"相机在线: {self.combo_camera.currentText()}")
        self._camera_frame_counter = 0
        self._camera_fps_anchor = time.time()
        self._last_preview_render_at = 0.0
        self._last_preview_size = None
        self._current_camera_frame = None
        if self.chk_auto_reference.isChecked():
            self._reference_capture_timer.start(self.spin_auto_reference_interval.value())
        self._log(f"相机预览已连接: {self.combo_camera.currentText()}")

    def _stop_camera_preview(self):
        self._camera_timer.stop()
        self._snapshot_timer.stop()
        self._reference_capture_timer.stop()
        self._snapshot_remaining = 0
        if self._camera_capture is not None:
            self._camera_capture.release()
            self._camera_capture = None
        self._current_camera_frame = None
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
        self._current_camera_frame = frame.copy()
        self._camera_frame_counter += 1
        now = time.time()
        elapsed = max(now - self._camera_fps_anchor, 0.001)
        fps = self._camera_frame_counter / elapsed
        if now - self._last_preview_render_at >= 0.08:
            self._render_camera_frame(frame)
            self._last_preview_render_at = now
        self.lbl_camera_meta.setText(f"分辨率 {frame.shape[1]}x{frame.shape[0]} | 预览 FPS {fps:.1f}")

    def _save_camera_snapshot(self):
        saved_path = self._capture_snapshot_frame()
        if saved_path:
            QMessageBox.information(self, "抓拍成功", saved_path)

    def _open_snapshot_dir(self):
        snapshot_dir = self._action_snapshot_dir()
        if not snapshot_dir or not os.path.isdir(snapshot_dir):
            QMessageBox.information(self, "提示", "当前还没有可打开的抓拍目录")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(snapshot_dir))

    def _browse_reference_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择参考图库目录", self.edit_reference_dir.text().strip() or "")
        if not dir_path:
            return
        self.edit_reference_dir.setText(dir_path)
        self._persist_profile()
        self._refresh_reference_meta()

    def _compare_current_frame_with_reference(self):
        self._compare_against_reference(source="手动检图")

    def _get_latest_camera_frame(self) -> Optional[Any]:
        if self._current_camera_frame is not None:
            return self._current_camera_frame.copy()
        capture = self._camera_capture
        if capture is None:
            capture = self._ensure_script_capture()
        if capture is not None:
            ret, frame = capture.read()
            if ret and frame is not None:
                self._current_camera_frame = frame.copy()
                return frame
        return None

    def _selected_camera_index(self) -> int:
        camera_index = self.combo_camera.currentData()
        if camera_index is None or int(camera_index) < 0:
            return int(self._profile.get("camera", {}).get("last_index", 0) or 0)
        return int(camera_index)

    def _ensure_script_capture(self):
        if self._script_camera_capture is not None and self._script_camera_capture.isOpened():
            return self._script_camera_capture
        if not self._active_run_context:
            return None
        capture = self._open_camera(self._selected_camera_index())
        if not capture.isOpened():
            return None
        # 预热：丢弃前 N 帧，等待相机自动曝光调整
        for _ in range(15):
            capture.read()
        self._script_camera_capture = capture
        self.lbl_camera_chip.setText("剧本拍摄中")
        return self._script_camera_capture

    def _close_script_capture(self):
        if self._script_camera_capture is not None:
            try:
                self._script_camera_capture.release()
            except Exception:
                pass
            self._script_camera_capture = None

    def _action_snapshot_dir(self) -> str:
        if self._active_run_context:
            return self._active_run_context.get("snapshot_dir", "")
        project_root = self._config_mgr.get_project_root() if self._config_mgr else os.getcwd()
        rel_dir = self._profile.get("camera", {}).get("snapshot_dir", "reports/device_lab_snapshots")
        return self._store.resolve_path(rel_dir, project_root)

    def _action_artifact_dir(self) -> str:
        if self._active_run_context:
            return self._active_run_context.get("artifact_dir", self._action_snapshot_dir())
        return self._action_snapshot_dir()

    def _reference_dir_path(self, category: Optional[str] = None, reference_dir_override: str = "") -> str:
        project_root = self._config_mgr.get_project_root() if self._config_mgr else os.getcwd()
        if reference_dir_override.strip():
            base_dir = self._store.resolve_path(reference_dir_override.strip(), project_root)
        elif self._active_run_context:
            base_dir = self._active_run_context.get("reference_dir", self._action_snapshot_dir())
        else:
            base_dir = self._store.resolve_path(self.edit_reference_dir.text().strip() or "reports/device_lab_references", project_root)
        normalized_category = self._normalized_category(category or self.edit_reference_category.text().strip() or "default")
        return os.path.join(base_dir, normalized_category)

    def _normalized_category(self, category: str) -> str:
        sanitized = re.sub(r"[^0-9A-Za-z_\-]+", "_", (category or "default").strip())
        return sanitized or "default"

    def _parse_roi_text(self, roi_text: str) -> Optional[Tuple[float, float, float, float]]:
        text = (roi_text or "").strip()
        if not text:
            return None
        parts = [part.strip() for part in text.split(",")]
        if len(parts) != 4:
            return None
        try:
            values = [float(part) for part in parts]
        except ValueError:
            return None
        if all(0.0 <= value <= 100.0 for value in values) and any(value > 1.0 for value in values):
            values = [value / 100.0 for value in values]
        x, y, w, h = values
        if w <= 0.0 or h <= 0.0:
            return None
        if x < 0.0 or y < 0.0 or x + w > 1.0 or y + h > 1.0:
            return None
        return x, y, w, h

    def _interpolate_text(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(
            r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
            lambda match: str(self._script_variables.get(match.group(1), "")),
            text,
        )

    def _coerce_variable_value(self, raw_value: str) -> Any:
        value_text = self._interpolate_text(raw_value).strip()
        lowered = value_text.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            if "." in value_text:
                return float(value_text)
            return int(value_text)
        except ValueError:
            return value_text

    def _evaluate_condition(self, expression: str) -> bool:
        expr = (expression or "").strip()
        if not expr:
            return True

        def _eval(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                return self._script_variables.get(node.id, False)
            if isinstance(node, ast.BoolOp):
                values = [_eval(value) for value in node.values]
                if isinstance(node.op, ast.And):
                    return all(values)
                if isinstance(node.op, ast.Or):
                    return any(values)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return not bool(_eval(node.operand))
            if isinstance(node, ast.Compare):
                left = _eval(node.left)
                for op, comparator in zip(node.ops, node.comparators):
                    right = _eval(comparator)
                    if isinstance(op, ast.Eq):
                        ok = left == right
                    elif isinstance(op, ast.NotEq):
                        ok = left != right
                    elif isinstance(op, ast.Gt):
                        ok = left > right
                    elif isinstance(op, ast.GtE):
                        ok = left >= right
                    elif isinstance(op, ast.Lt):
                        ok = left < right
                    elif isinstance(op, ast.LtE):
                        ok = left <= right
                    else:
                        raise ValueError("不支持的条件操作")
                    if not ok:
                        return False
                    left = right
                return True
            if isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
            raise ValueError("条件表达式不支持该语法")

        try:
            parsed = ast.parse(expr, mode="eval")
            return bool(_eval(parsed))
        except Exception as exc:
            self._log(f"条件表达式解析失败: {expr} ({exc})", "WARN")
            return False

    def _load_reference_pool(self, category: Optional[str] = None, reference_dir_override: str = "", pool_size: Optional[int] = None) -> List[str]:
        reference_dir = self._reference_dir_path(category, reference_dir_override=reference_dir_override)
        if not os.path.isdir(reference_dir):
            return []
        image_names = [
            name for name in os.listdir(reference_dir)
            if os.path.isfile(os.path.join(reference_dir, name)) and name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ]
        image_names.sort(key=lambda name: os.path.getmtime(os.path.join(reference_dir, name)), reverse=True)
        limit = max(1, int(pool_size if pool_size is not None else self.spin_reference_pool_size.value()))
        return [os.path.join(reference_dir, name) for name in image_names[:limit]]

    def _refresh_reference_meta(self):
        pool_paths = self._load_reference_pool()
        self.lbl_reference_meta.setText(
            f"参考图库[{self._normalized_category(self.edit_reference_category.text() or 'default')}]: {len(pool_paths)} 张 | "
            f"ROI: {self.edit_compare_roi.text().strip() or '全图'} | 最新参考: {os.path.basename(pool_paths[0]) if pool_paths else '未设置'}"
        )

    def _append_current_frame_to_reference_pool(self, quiet: bool = False, category: Optional[str] = None, reference_dir_override: str = "") -> bool:
        if self._current_camera_frame is None:
            if not quiet:
                QMessageBox.warning(self, "提示", "请先连接相机预览")
            return False
        reference_dir = self._reference_dir_path(category, reference_dir_override=reference_dir_override)
        os.makedirs(reference_dir, exist_ok=True)
        file_path = self._capture_snapshot_frame(file_prefix="reference_pool")
        if not file_path:
            return False
        pool_target = os.path.join(reference_dir, os.path.basename(file_path))
        if os.path.normcase(file_path) != os.path.normcase(pool_target):
            try:
                os.replace(file_path, pool_target)
            except OSError:
                pool_target = file_path
        self._persist_profile()
        self._refresh_reference_meta()
        self._log(f"参考图库新增: {pool_target}")
        return True

    def _toggle_auto_reference_capture(self, checked: bool):
        self._profile.setdefault("camera", {})["auto_reference_enabled"] = checked
        self._persist_profile()
        if checked and self._camera_capture is not None:
            self._reference_capture_timer.start(self.spin_auto_reference_interval.value())
            self._reference_reject_count = 0
        else:
            self._reference_capture_timer.stop()

    def _on_auto_reference_interval_changed(self, value: int):
        self._persist_profile()
        if self._reference_capture_timer.isActive():
            self._reference_capture_timer.start(value)

    def _attempt_auto_reference_capture(self):
        if self._current_camera_frame is None:
            return
        accepted = self._try_capture_stable_reference()
        if accepted:
            self._reference_reject_count = 0
            return
        self._reference_reject_count += 1
        self._log(f"自动稳定参考图被舍弃，第 {self._reference_reject_count} 次", "WARN")
        if self._reference_reject_count >= int(self.spin_auto_reference_retry.value()):
            self._reference_reject_count = 0

    def _try_capture_stable_reference(self) -> bool:
        pool_paths = self._load_reference_pool()
        if not pool_paths:
            return self._append_current_frame_to_reference_pool(quiet=True)
        reference_images = []
        for path in pool_paths:
            image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is not None:
                reference_images.append(image)
        if not reference_images:
            return self._append_current_frame_to_reference_pool(quiet=True)
        result = compare_with_reference_set(
            reference_images,
            self._current_camera_frame,
            float(self._profile.get("camera", {}).get("reference_accept_threshold", 0.82)),
            roi=self._parse_roi_text(self.edit_compare_roi.text().strip()),
        )
        if result.get("passed", False):
            return self._append_current_frame_to_reference_pool(quiet=True)
        return False

    def _capture_snapshot_frame(self, batch_index: Optional[int] = None, batch_total: Optional[int] = None, file_prefix: str = "snapshot") -> Optional[str]:
        if self._camera_capture is None and self._current_camera_frame is None and self._active_run_context is None:
            QMessageBox.warning(self, "提示", "请先连接相机预览")
            return None
        frame = self._get_latest_camera_frame()
        if frame is None:
            QMessageBox.warning(self, "提示", "当前帧获取失败")
            return None
        snapshot_dir = self._action_snapshot_dir()
        os.makedirs(snapshot_dir, exist_ok=True)
        if batch_index is not None and batch_total is not None:
            file_path = os.path.join(
                snapshot_dir,
                f"{file_prefix}_{self._snapshot_batch_token}_{batch_index:03d}-of-{batch_total:03d}.png",
            )
        else:
            file_path = os.path.join(snapshot_dir, f"{file_prefix}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        ext = os.path.splitext(file_path)[1]
        _, buf = cv2.imencode(ext, frame)
        buf.tofile(file_path)
        self._last_snapshot_path = file_path
        self._current_camera_frame = frame.copy()
        self._render_camera_frame(frame)
        if self._active_run_context and self._camera_capture is None:
            self.lbl_camera_meta.setText(f"剧本拍摄回显 | 最近照片: {os.path.basename(file_path)}")
        self._log(f"相机抓拍已保存: {file_path}")
        if self._run_metrics:
            self._run_metrics["saved_images"] = int(self._run_metrics.get("saved_images", 0)) + 1
            self._update_run_stats()
        return file_path

    def _compare_against_reference(
        self,
        pause_on_fail: bool = True,
        source: str = "图片检查",
        save_snapshot: bool = True,
        category: Optional[str] = None,
        reference_dir: str = "",
        reference_pool_size: Optional[int] = None,
        save_diff_heatmap: Optional[bool] = None,
        roi_text: str = "",
        result_variable: str = "",
        notify_on_fail: bool = False,
        notify_title: str = "",
        notify_content: str = "",
        include_logs: bool = True,
        use_ai_summary: bool = False,
    ) -> bool:
        current_frame = self._get_latest_camera_frame()
        if current_frame is None:
            self._log("当前没有可用于检图的相机画面", "ERROR")
            return False
        self._current_camera_frame = current_frame.copy()

        compare_category = self._normalized_category(category or self.edit_reference_category.text().strip() or "default")
        compare_roi_text = (roi_text or self.edit_compare_roi.text().strip()).strip()
        compare_roi = self._parse_roi_text(compare_roi_text)

        if save_snapshot:
            self._capture_snapshot_frame(file_prefix="compare_snapshot")

        reference_images = []
        reference_paths = self._load_reference_pool(compare_category, reference_dir_override=reference_dir, pool_size=reference_pool_size)

        if not reference_paths:
            self._log(f"参考图库[{compare_category}]为空，无法执行检图", "ERROR")
            return False

        for path in reference_paths:
            image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is not None:
                reference_images.append(image)

        if not reference_images:
            self._log("参考图库读取失败，无法执行检图", "ERROR")
            return False

        compare_result = compare_with_reference_set(
            reference_images,
            current_frame,
            float(self._profile.get("camera", {}).get("compare_threshold", 0.72)),
            roi=compare_roi,
        )
        metrics = compare_result.get("metrics", {})
        self._script_variables["last_compare_passed"] = bool(compare_result.get("passed", False))
        self._script_variables["last_compare_score"] = float(compare_result.get("final_score", 0.0))
        self._script_variables["last_compare_threshold"] = float(compare_result.get("threshold_used", 0.0))
        self._script_variables["last_compare_category"] = compare_category
        if result_variable:
            self._script_variables[result_variable] = bool(compare_result.get("passed", False))

        heatmap_path = ""
        heatmap = compare_result.get("heatmap")
        save_heatmap = self.chk_save_diff_heatmap.isChecked() if save_diff_heatmap is None else bool(save_diff_heatmap)
        if getattr(heatmap, "shape", None) is not None and save_heatmap:
            snapshot_dir = self._action_artifact_dir()
            os.makedirs(snapshot_dir, exist_ok=True)
            heatmap_path = os.path.join(snapshot_dir, f"compare_heatmap_{time.strftime('%Y%m%d_%H%M%S')}.png")
            _, buf = cv2.imencode('.png', heatmap)
            buf.tofile(heatmap_path)

        self._log(
            f"{source}: category={compare_category}, roi={compare_roi_text or 'full'}, refs={compare_result.get('reference_count', len(reference_images))}, best={compare_result.get('matched_index', -1)}, "
            f"score={compare_result['final_score']:.4f}, threshold={compare_result['threshold_used']:.4f}, "
            f"corr={metrics.get('correlation', 0):.4f}, hist={metrics.get('histogram', 0):.4f}, "
            f"edge={metrics.get('edge', 0):.4f}, orb={metrics.get('orb', 0):.4f}, grid={metrics.get('grid', 0):.4f}, roi={metrics.get('roi', 'na')}"
        )
        if heatmap_path:
            self._log(f"差异热图已保存: {heatmap_path}")
        if compare_result["passed"]:
            return True

        self._log(f"{source} 未通过，已判定为异常画面", "ERROR")
        # >>> AI 集成：图像对比失败事件（仅步骤开启 notify_on_fail 时）
        if notify_on_fail:
            try:
                from core.event_bus import get_event_bus, Events
                _cycle = self._run_metrics.get('current_cycle', 1) if self._run_metrics else 1
                _total = self._run_metrics.get('total_cycles', 1) if self._run_metrics else 1
                get_event_bus().emit_async(
                    Events.COMPARE_FAILED,
                    script_name=self._run_metrics.get('script_name', '') if self._run_metrics else '',
                    step_name=source,
                    reason=f"图像对比未通过 score={compare_result['final_score']:.4f} threshold={compare_result['threshold_used']:.4f}",
                    notify_title=notify_title,
                    notify_content=notify_content,
                    include_logs=include_logs,
                    use_ai_summary=use_ai_summary,
                    current_cycle=_cycle,
                    total_cycles=_total,
                )
                self._failure_notified = True
            except Exception:
                pass
        if pause_on_fail:
            QMessageBox.warning(
                self,
                "图片检查失败",
                f"{source} 未通过\nscore={compare_result['final_score']:.4f}\nthreshold={compare_result['threshold_used']:.4f}",
            )
        return False

    def _detect_green_screen(
        self,
        *,
        pause_on_fail: bool = True,
        source: str = "绿屏检测",
        save_snapshot: bool = True,
        roi_text: str = "",
        result_variable: str = "",
        save_diff_heatmap: Optional[bool] = None,
        green_ratio_threshold: float = 0.35,
        green_area_threshold: float = 0.18,
        green_margin: int = 35,
        green_saturation_threshold: int = 70,
        green_value_threshold: int = 60,
        green_check_frames: int = 3,
        green_check_interval_ms: int = 250,
    ) -> bool:
        compare_roi_text = (roi_text or self.edit_compare_roi.text().strip()).strip()
        compare_roi = self._parse_roi_text(compare_roi_text)
        sample_frames = max(1, int(green_check_frames or 1))
        sample_interval = max(0, int(green_check_interval_ms or 0))

        if save_snapshot:
            self._capture_snapshot_frame(file_prefix="green_detect_snapshot")

        sample_results: List[Dict[str, Any]] = []
        for sample_index in range(sample_frames):
            frame = self._get_latest_camera_frame()
            if frame is None:
                self._log("当前没有可用于绿屏检测的相机画面", "ERROR")
                return False
            detection = detect_green_screen(
                frame,
                compare_roi,
                green_ratio_threshold=green_ratio_threshold,
                area_ratio_threshold=green_area_threshold,
                green_margin=green_margin,
                saturation_threshold=green_saturation_threshold,
                value_threshold=green_value_threshold,
            )
            sample_results.append(detection)
            if sample_index < sample_frames - 1 and sample_interval > 0:
                time.sleep(sample_interval / 1000.0)

        hit_count = sum(1 for item in sample_results if item.get("detected", False))
        detected = hit_count >= sample_frames
        peak_green_ratio = max(float(item.get("green_ratio", 0.0)) for item in sample_results)
        peak_area_ratio = max(float(item.get("largest_component_ratio", 0.0)) for item in sample_results)
        peak_excess = max(float(item.get("mean_green_excess", 0.0)) for item in sample_results)
        self._script_variables["last_green_detected"] = detected
        self._script_variables["last_green_passed"] = not detected
        self._script_variables["last_green_ratio"] = peak_green_ratio
        self._script_variables["last_green_area_ratio"] = peak_area_ratio
        self._script_variables["last_green_excess"] = peak_excess
        self._script_variables["last_green_sample_frames"] = sample_frames
        self._script_variables["last_green_hit_count"] = hit_count
        if result_variable:
            self._script_variables[result_variable] = not detected

        last_result = sample_results[-1]
        heatmap_path = ""
        heatmap = last_result.get("heatmap")
        save_heatmap = self.chk_save_diff_heatmap.isChecked() if save_diff_heatmap is None else bool(save_diff_heatmap)
        if getattr(heatmap, "shape", None) is not None and save_heatmap:
            snapshot_dir = self._action_artifact_dir()
            os.makedirs(snapshot_dir, exist_ok=True)
            heatmap_path = os.path.join(snapshot_dir, f"green_detect_mask_{time.strftime('%Y%m%d_%H%M%S')}.png")
            _, buf = cv2.imencode('.png', heatmap)
            buf.tofile(heatmap_path)

        self._log(
            f"{source}: roi={compare_roi_text or 'full'}, sampled={sample_frames}, hits={hit_count}, "
            f"green_ratio={peak_green_ratio:.4f}/{float(green_ratio_threshold):.4f}, "
            f"area_ratio={peak_area_ratio:.4f}/{float(green_area_threshold):.4f}, "
            f"green_excess={peak_excess:.4f}, margin={int(green_margin)}, sat>={int(green_saturation_threshold)}, value>={int(green_value_threshold)}"
        )
        if heatmap_path:
            self._log(f"绿屏掩码图已保存: {heatmap_path}")
        if not detected:
            return True

        self._log(f"{source} 命中大面积绿屏，已判定为异常画面", "ERROR")
        if pause_on_fail:
            QMessageBox.warning(
                self,
                "绿屏检测失败",
                f"{source} 命中绿屏\n绿像素占比={peak_green_ratio:.4f}\n最大连通域={peak_area_ratio:.4f}",
            )
        return False

    def _start_batch_snapshot(self):
        if self._camera_capture is None and self._current_camera_frame is None:
            QMessageBox.warning(self, "提示", "请先连接相机预览")
            return
        camera_cfg = self._profile.setdefault("camera", {})
        self._snapshot_total = max(1, int(camera_cfg.get("capture_count", 1) or 1))
        self._snapshot_remaining = self._snapshot_total
        self._snapshot_batch_token = time.strftime("%Y%m%d_%H%M%S")
        self._log(
            f"开始自动抓拍，共 {self._snapshot_total} 张，间隔 {int(camera_cfg.get('capture_interval_ms', 1000) or 1000)} ms"
        )
        self._capture_next_snapshot()

    def _capture_next_snapshot(self):
        if self._snapshot_remaining <= 0:
            self._snapshot_timer.stop()
            self._snapshot_batch_token = ""
            self._log("自动抓拍完成")
            return
        current_index = self._snapshot_total - self._snapshot_remaining + 1
        self._capture_snapshot_frame(batch_index=current_index, batch_total=self._snapshot_total)
        self._snapshot_remaining -= 1
        if self._snapshot_remaining > 0:
            self._snapshot_timer.start(int(self._profile.get("camera", {}).get("capture_interval_ms", 1000) or 1000))
        else:
            self._snapshot_timer.stop()
            self._snapshot_batch_token = ""
            self._log("自动抓拍完成")

    def _on_preview_zoom_changed(self, value: int):
        self.lbl_preview_zoom.setText(f"{value}%")
        self._profile.setdefault("camera", {})["preview_zoom_percent"] = value
        self._persist_profile()
        if self._current_camera_frame is not None:
            self._render_camera_frame(self._current_camera_frame)

    def _render_camera_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format.Format_RGB888)
        zoom_ratio = max(0.5, self.slider_preview_zoom.value() / 100.0)
        target_width = max(160, int(frame.shape[1] * zoom_ratio))
        target_height = max(120, int(frame.shape[0] * zoom_ratio))
        pixmap = QPixmap.fromImage(image).scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.lbl_camera_preview.setPixmap(pixmap)
        preview_size = (pixmap.width(), pixmap.height())
        if self._last_preview_size != preview_size:
            self.lbl_camera_preview.resize(pixmap.size())
            self._last_preview_size = preview_size

    def _sanitize_output_name(self, text: str) -> str:
        value = re.sub(r'[<>:"/\\|?*]+', '_', (text or '').strip())
        value = value.strip(' ._')
        return value or 'unnamed'

    # ── 断点续执行：执行状态持久化 ──────────────────────────────────
    def _execution_state_path(self) -> str:
        if self._config_mgr and hasattr(self._config_mgr, '_config_dir'):
            config_dir = self._config_mgr._config_dir
        else:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        return os.path.join(config_dir, 'execution_state.json')

    def _save_execution_state(self):
        """保存当前执行状态到磁盘（用于断点续执行 / 崩溃恢复）"""
        if not self._run_metrics or not self._active_run_context:
            return
        state = {
            'version': 1,
            'timestamp': time.time(),
            'run_metrics': {
                'script_name': self._run_metrics.get('script_name', ''),
                'run_count': self._run_metrics.get('run_count', 1),
                'current_cycle': self._run_metrics.get('current_cycle', 1),
                'total_cycles': self._run_metrics.get('total_cycles', 1),
                'saved_images': self._run_metrics.get('saved_images', 0),
                'error_count': self._run_metrics.get('error_count', 0),
                'start_time': self._run_metrics.get('start_time', 0),
            },
            'run_context': self._active_run_context,
            'script_variables': self._script_variables,
            'remaining_queue': self._command_queue[:],
            'queue_paused': self._queue_paused,
            'project_name': (self._current_project() or {}).get('name', ''),
        }
        try:
            state_path = self._execution_state_path()
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self._log(f"执行状态已保存: {state_path}")
        except Exception as e:
            self._log(f"保存执行状态失败: {e}", "WARN")

    def _clear_execution_state(self):
        """清除保存的执行状态文件"""
        try:
            state_path = self._execution_state_path()
            if os.path.exists(state_path):
                os.remove(state_path)
        except Exception:
            pass

    def _load_execution_state(self) -> Optional[Dict[str, Any]]:
        """从磁盘加载保存的执行状态，如果不存在或已过期返回 None"""
        try:
            state_path = self._execution_state_path()
            if not os.path.exists(state_path):
                return None
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            if state.get('version') != 1:
                self._clear_execution_state()
                return None
            # 超过 24 小时的状态视为过期
            if time.time() - state.get('timestamp', 0) > 86400:
                self._clear_execution_state()
                return None
            return state
        except Exception:
            self._clear_execution_state()
            return None

    def _create_run_context(self, script: Dict[str, Any]) -> Dict[str, Any]:
        project_root = self._config_mgr.get_project_root() if self._config_mgr else os.getcwd()
        project = self._current_project() or {}
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        folder_name = f"{timestamp}__{self._sanitize_output_name(project.get('name', 'project'))}__{self._sanitize_output_name(script.get('name', 'script'))}"
        base_dir = os.path.join(project_root, 'reports', 'device_lab_runs', folder_name)
        snapshot_dir = os.path.join(base_dir, 'snapshots')
        reference_dir = os.path.join(base_dir, 'references')
        artifact_dir = os.path.join(base_dir, 'artifacts')
        os.makedirs(snapshot_dir, exist_ok=True)
        os.makedirs(reference_dir, exist_ok=True)
        os.makedirs(artifact_dir, exist_ok=True)
        self._last_run_output_dir = base_dir
        self.lbl_run_output.setText(f"输出目录: {base_dir}")
        # 开启日志文件
        if self._run_log_file is not None:
            try:
                self._run_log_file.close()
            except Exception:
                pass
        try:
            self._run_log_file = open(os.path.join(base_dir, 'run_log.txt'), 'w', encoding='utf-8')
        except Exception:
            self._run_log_file = None
        return {
            'base_dir': base_dir,
            'snapshot_dir': snapshot_dir,
            'reference_dir': reference_dir,
            'artifact_dir': artifact_dir,
        }

    def _refresh_queue_controls(self):
        has_running_queue = self._queue_busy or self._queue_timer.isActive() or bool(self._command_queue)
        if hasattr(self, 'btn_script_pause'):
            self.btn_script_pause.setEnabled(has_running_queue)
            self.btn_script_pause.setText('继续执行' if self._queue_paused else '暂停执行')
        if hasattr(self, 'btn_open_output_dir'):
            self.btn_open_output_dir.setEnabled(bool(self._last_run_output_dir or (self._active_run_context and self._active_run_context.get('base_dir'))))
        if hasattr(self, 'btn_script_stop'):
            self.btn_script_stop.setEnabled(has_running_queue)
        if hasattr(self, 'btn_script_resume'):
            # 仅在没有正在运行的队列时，且有可恢复状态时启用
            has_saved_state = os.path.exists(self._execution_state_path()) if not has_running_queue else False
            self.btn_script_resume.setEnabled(has_saved_state)

    def _finish_queue_run(self, message: str, manual_stop: bool = False):
        # 完成通知（仅自动完成，非手动停止）
        if not manual_stop and not self._failure_notified and self._run_metrics:
            self._send_finish_notification()

        self._failure_notified = False
        self._queue_paused = False
        self._queue_busy = False
        self._refresh_queue_controls()
        self._close_script_capture()
        self._run_stats_timer.stop()
        self._highlight_running_step(None)
        self._clear_execution_state()
        if self._active_run_context:
            self._log(f"{message}，输出目录: {self._active_run_context.get('base_dir', '')}")
            self._last_run_output_dir = self._active_run_context.get('base_dir', self._last_run_output_dir)
            self.lbl_run_output.setText(f"输出目录: {self._last_run_output_dir}")
        # 关闭日志文件
        if self._run_log_file is not None:
            try:
                self._run_log_file.close()
            except Exception:
                pass
            self._run_log_file = None
        self._active_run_context = None
        self._update_run_stats(force_status="空闲")
        if self._camera_capture is None:
            self.lbl_camera_chip.setText('相机未连接')
        self._refresh_workspace_overview()

    def _send_finish_notification(self):
        """运行完成后发送飞书通知（受全局开关控制）"""
        try:
            if not self._config_mgr:
                return
            ai_cfg = self._config_mgr.load_ai_config()
            rules = ai_cfg.get('notification_rules', {})
            if not rules.get('notify_on_finish', False):
                return
            metrics = self._run_metrics or {}
            elapsed = max(0, int(time.time() - metrics.get('start_time', time.time())))
            duration = f"{elapsed // 60}m {elapsed % 60}s" if elapsed >= 60 else f"{elapsed}s"
            from core.feishu_service import get_feishu_service, FeishuTemplates
            fs = get_feishu_service()
            if not fs.webhook_configured and not fs.openapi_configured:
                return
            payload = FeishuTemplates.test_completed_card(
                title=metrics.get('script_name', '未知脚本'),
                status="成功",
                duration=duration,
                summary=f"轮次: {metrics.get('current_cycle', 1)}/{metrics.get('total_cycles', 1)} | "
                        f"保存图片: {metrics.get('saved_images', 0)} | 报错: {metrics.get('error_count', 0)}",
            )
            fs.send(payload)
            self._log("运行完成通知已发送")
        except Exception as e:
            self._log(f"完成通知发送失败: {e}", "WARN")

    def _toggle_script_pause(self):
        has_running_queue = self._queue_busy or self._queue_timer.isActive() or bool(self._command_queue)
        if not has_running_queue:
            return
        if not self._queue_paused:
            self._queue_paused = True
            self._queue_timer.stop()
            # 冻结计时：记录已运行时长
            if self._run_metrics:
                self._paused_elapsed = time.time() - self._run_metrics.get('start_time', time.time())
            self._run_stats_timer.stop()
            self._log('剧本执行已暂停', 'WARN')
            self._update_run_stats(force_status="已暂停")
            self._save_execution_state()
            self._refresh_queue_controls()
            return
        self._queue_paused = False
        # 恢复计时：重新设定 start_time 使得已用时间连续
        if self._run_metrics:
            self._run_metrics['start_time'] = time.time() - self._paused_elapsed
        self._run_stats_timer.start()
        self._log('剧本执行已继续')
        self._update_run_stats(force_status="运行中")
        self._refresh_queue_controls()
        self._process_next_queue_item()

    def _stop_script_run(self):
        has_running_queue = self._queue_busy or self._queue_timer.isActive() or bool(self._command_queue)
        if not has_running_queue:
            return
        self._queue_timer.stop()
        self._command_queue.clear()
        self._queue_paused = False
        self._queue_busy = False
        self._log('剧本执行已手动停止', 'WARN')
        self._finish_queue_run('剧本执行已手动停止', manual_stop=True)

    def _resume_from_saved_state(self):
        """从保存的执行状态中恢复（断点续执行）"""
        state = self._load_execution_state()
        if not state:
            QMessageBox.information(self, "提示", "没有可恢复的执行状态")
            self._refresh_queue_controls()
            return
        metrics = state.get('run_metrics', {})
        remaining = state.get('remaining_queue', [])
        script_name = metrics.get('script_name', '未知')
        current_cycle = metrics.get('current_cycle', 1)
        total_cycles = metrics.get('total_cycles', 1)
        remaining_count = len(remaining)
        project_name = state.get('project_name', '')
        saved_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state.get('timestamp', 0)))
        msg = (
            f"检测到未完成的执行状态：\n\n"
            f"  项目：{project_name}\n"
            f"  剧本：{script_name}\n"
            f"  轮次：{current_cycle}/{total_cycles}\n"
            f"  剩余动作：{remaining_count} 个\n"
            f"  保存时间：{saved_time}\n\n"
            f"是否从断点处继续执行？\n（将跳过失败步骤，从下一步开始）"
        )
        reply = QMessageBox.question(self, "断点续执行", msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Discard)
        if reply == QMessageBox.StandardButton.Discard:
            self._clear_execution_state()
            self._log("已丢弃保存的执行状态")
            self._refresh_queue_controls()
            return
        if reply != QMessageBox.StandardButton.Yes:
            return
        # 恢复执行上下文
        run_context = state.get('run_context', {})
        base_dir = run_context.get('base_dir', '')
        if base_dir:
            for sub in ('snapshots', 'references', 'artifacts'):
                os.makedirs(os.path.join(base_dir, sub), exist_ok=True)
        self._active_run_context = run_context
        self._script_variables = state.get('script_variables', {})
        self._failure_notified = False
        self._paused_elapsed = 0.0
        self._run_metrics = {
            'script_name': metrics.get('script_name', ''),
            'run_count': metrics.get('run_count', 1),
            'current_cycle': current_cycle,
            'total_cycles': total_cycles,
            'saved_images': metrics.get('saved_images', 0),
            'error_count': metrics.get('error_count', 0),
            'start_time': time.time(),  # 重置计时
        }
        self._last_run_output_dir = base_dir
        self.lbl_run_output.setText(f"输出目录: {base_dir}")
        # 重新打开日志文件（追加模式）
        if self._run_log_file is not None:
            try:
                self._run_log_file.close()
            except Exception:
                pass
        try:
            self._run_log_file = open(os.path.join(base_dir, 'run_log.txt'), 'a', encoding='utf-8')
        except Exception:
            self._run_log_file = None
        self._log(f"断点续执行: {script_name} | 轮次 {current_cycle}/{total_cycles} | 剩余 {remaining_count} 个动作")
        self._run_stats_timer.start()
        self._update_run_stats(force_status='运行中')
        self._clear_execution_state()
        self._queue_commands(remaining)

    def _highlight_running_step(self, step_id: Optional[str]):
        self._running_step_id = step_id or None
        for index in range(self.list_script_steps.topLevelItemCount()):
            item = self.list_script_steps.topLevelItem(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == self._running_step_id:
                item.setBackground(0, QColor('#fef3c7'))
                item.setForeground(0, QColor('#92400e'))
                self.list_script_steps.setCurrentItem(item)
            else:
                item.setBackground(0, QBrush())
                item.setForeground(0, QBrush())

    def _open_run_output_dir(self):
        target_dir = self._last_run_output_dir
        if self._active_run_context:
            target_dir = self._active_run_context.get('base_dir', target_dir)
        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.information(self, '提示', '当前还没有可打开的输出目录')
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir))

    def _on_feishu_notify(self):
        """弹出飞书通知发送弹窗（设备联调台）。"""
        from ui.widgets.feishu_notify_dialog import FeishuNotifyDialog

        dlg = FeishuNotifyDialog(self)

        # 收集可发送的文件（输出目录下的截图/日志）
        files = []
        target_dir = self._last_run_output_dir
        if self._active_run_context:
            target_dir = self._active_run_context.get('base_dir', target_dir)
        if target_dir and os.path.isdir(target_dir):
            for fn in os.listdir(target_dir):
                fp = os.path.join(target_dir, fn)
                if os.path.isfile(fp):
                    files.append(fp)

        # 获取当前脚本信息
        script_name = ""
        if self._run_metrics:
            script_name = self._run_metrics.get("script_name", "")

        status = ""
        if self._queue_paused:
            status = "已暂停"
        elif self._queue_timer.isActive() or self._queue_busy:
            status = "运行中"
        else:
            status = "空闲"

        dlg.set_preset(
            title=f"设备联调台 - {script_name or '手动通知'}",
            description=f"脚本: {script_name}\n状态: {status}",
            files=files[:20],
            include_logs=True,
            context_info=f"脚本={script_name}, 状态={status}",
        )
        dlg.exec()

    def _on_step_notify_config(self):
        """打开步骤自动通知配置弹窗。"""
        script = self._current_script()
        if not script:
            QMessageBox.information(self, "提示", "请先选择一个剧本。")
            return

        from ui.widgets.step_notify_config import StepNotifyConfigDialog

        dlg = StepNotifyConfigDialog(script, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # 将修改后的步骤写回 store
            script["steps"] = dlg.get_modified_steps()
            self._store.save()
            self._refresh_script_steps()
            self._log("步骤自动通知配置已更新")

    def _update_run_stats(self, force_status: str = ""):
        if not self._run_metrics:
            self.lbl_run_stats.setText('运行状态: 空闲')
            self._refresh_workspace_overview()
            return
        start_time = float(self._run_metrics.get('start_time', time.time()))
        elapsed_seconds = max(0, int(time.time() - start_time))
        status = force_status or ('已暂停' if self._queue_paused else '运行中')
        self.lbl_run_stats.setText(
            f"运行状态: {status} | 剧本: {self._run_metrics.get('script_name', '-') } | 总时长: {elapsed_seconds}s | "
            f"轮次: {self._run_metrics.get('current_cycle', 1)}/{self._run_metrics.get('total_cycles', 1)} | 已保存图片: {self._run_metrics.get('saved_images', 0)} | "
            f"报错次数: {self._run_metrics.get('error_count', 0)} | 剩余动作: {len(self._command_queue)}"
        )
        self._refresh_workspace_overview()
        # 每 30 个 tick（~30s）自动保存执行状态，用于崩溃恢复
        self._state_save_counter += 1
        if self._state_save_counter >= 30:
            self._state_save_counter = 0
            self._save_execution_state()

    def _refresh_workspace_overview(self):
        if not hasattr(self, 'lbl_overview_scope'):
            return
        project = self._current_project()
        script = self._current_script()
        project_name = project.get('name', '未选择项目') if project else '未选择项目'
        script_name = script.get('name', '未选择剧本') if script else '未选择剧本'
        scope_text = f"项目/剧本: {project_name} / {script_name}"
        self.lbl_overview_scope.setText(scope_text)
        self.lbl_overview_scope.setToolTip(scope_text)
        run_text = self.lbl_run_stats.text().replace('运行状态: ', '') if hasattr(self, 'lbl_run_stats') else '空闲'
        run_full = f"运行: {run_text}"
        self.lbl_overview_run.setText(run_full)
        self.lbl_overview_run.setToolTip(run_full)
        output_text = self.lbl_run_output.text().replace('输出目录: ', '') if hasattr(self, 'lbl_run_output') else '待执行'
        output_full = f"输出: {output_text}"
        self.lbl_overview_output.setText(output_full)
        self.lbl_overview_output.setToolTip(output_full)

    def _open_camera(self, index: int):
        logger = getattr(cv2, "utils", None)
        logging_api = getattr(logger, "logging", None)
        if logging_api is None:
            capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if capture.isOpened():
                return capture
            capture.release()
            return cv2.VideoCapture(index)

        old_level = logging_api.getLogLevel()
        logging_api.setLogLevel(logging_api.LOG_LEVEL_SILENT)
        try:
            capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if capture.isOpened():
                return capture
            capture.release()
            return cv2.VideoCapture(index)
        finally:
            logging_api.setLogLevel(old_level)

    def _render_remote_buttons(self):
        for button in self._remote_buttons.values():
            button.deleteLater()
        self._remote_buttons.clear()
        self._selected_remote_id = None
        max_right = 400
        max_bottom = 920
        for data in self._profile.get("remote", {}).get("buttons", []):
            button = DraggableRemoteButton(data["id"], self.chk_remote_edit_mode.isChecked, self.remote_canvas)
            button.setText(data["name"])
            x = data.get("x", 80)
            y = data.get("y", 80)
            width = data.get("w", 76)
            height = data.get("h", 34)
            button.setGeometry(x, y, width, height)
            button.activated.connect(self._on_remote_button_activated)
            button.moved.connect(self._on_remote_button_moved)
            button.selected.connect(self._select_remote_button)
            button.show()
            self._remote_buttons[data["id"]] = button
            max_right = max(max_right, x + width + 24)
            max_bottom = max(max_bottom, y + height + 24)
        self.remote_canvas.resize(max_right, max_bottom)
        self.remote_canvas.setMinimumSize(max_right, max_bottom)

    def _toggle_remote_edit_mode(self, checked: bool):
        self._profile.setdefault("remote", {})["edit_mode"] = checked
        self._persist_profile()
        self.lbl_remote_hint.setText(
            "编辑模式下可拖动按键并选择后编辑。"
            if checked else
            "默认点击按键会直接发送，勾选布局编辑模式后可拖动和选择。"
        )
        if self._selected_remote_id:
            self._select_remote_button(self._selected_remote_id)

    def _on_remote_button_activated(self, button_id: str):
        button = self._find_item_by_id(self._profile.get("remote", {}).get("buttons", []), button_id)
        if not button:
            return
        steps = self._resolve_button_steps(button)
        if not steps:
            self._log(f"按键 {button.get('name')} 未绑定有效指令", "WARN")
            return
        self._queue_commands(steps)

    def _resolve_button_steps(self, button: Dict[str, Any]) -> List[Dict[str, Any]]:
        if button.get("binding_type") == "shortcut":
            shortcut = self._find_item_by_name(self._profile.get("shortcuts", []), button.get("binding_value", ""))
            if not shortcut:
                return []
            return self._build_actions_from_shortcut(shortcut, f"遥控快捷 {button['name']}")
        command = button.get("binding_value", "").strip()
        return [{"type": "serial", "command": command, "delay_seconds": 0.25, "source": f"遥控按键 {button['name']}"}] if command else []

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
            "y": 438,
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
        script_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not script_id:
            return None
        return self._find_item_by_id(project.get("scripts", []), script_id)

    def _find_script_tree_item(self, script_id: str) -> Optional[QTreeWidgetItem]:
        for index in range(self.list_scripts.topLevelItemCount()):
            root_item = self.list_scripts.topLevelItem(index)
            for child_index in range(root_item.childCount()):
                item = root_item.child(child_index)
                if item.data(0, Qt.ItemDataRole.UserRole) == script_id:
                    return item
        return None

    def _add_project(self):
        name, ok = QInputDialog.getText(self, "新增项目", "项目名")
        if not ok or not name.strip():
            return
        project = {
            "id": self._store.make_id("project"),
            "name": name.strip(),
            "description": "",
            "scripts": [],
        }
        self._profile.setdefault("projects", []).append(project)
        self._profile.setdefault("ui_state", {})["last_project_id"] = project["id"]
        self._profile["ui_state"]["last_script_id"] = ""
        self._profile["ui_state"]["last_step_id"] = ""
        self._persist_profile()
        self._refresh_projects()
        index = self.combo_project.findData(project["id"])
        if index >= 0:
            self.combo_project.setCurrentIndex(index)

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
        data["steps"] = []
        project.setdefault("scripts", []).append(data)
        self._profile.setdefault("ui_state", {})["last_project_id"] = project.get("id", "")
        self._profile["ui_state"]["last_script_id"] = data["id"]
        self._profile["ui_state"]["last_step_id"] = ""
        self._persist_profile()
        self._refresh_scripts()
        self._select_script(data["id"])

    def _edit_script(self):
        script = self._current_script()
        if not script:
            return
        dialog = ScriptDialog("编辑联调剧本", script, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dialog.get_data()
        script["name"] = updated["name"]
        script["description"] = updated["description"]
        script["run_count"] = updated["run_count"]
        script["cycle_interval_ms"] = updated["cycle_interval_ms"]
        script["stop_on_fail"] = updated["stop_on_fail"]
        self._profile.setdefault("ui_state", {})["last_script_id"] = script.get("id", "")
        self._persist_profile()
        self._refresh_scripts()
        self._select_script(script.get("id"))

    def _delete_script(self):
        project = self._current_project()
        script = self._current_script()
        if not project or not script:
            return
        reply = QMessageBox.question(self, "删除剧本", f"确定删除剧本 {script['name']} 吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        scripts = project.get("scripts", [])
        removed_script_id = script.get("id", "")
        scripts[:] = [item for item in scripts if item["id"] != script["id"]]
        ui_state = self._profile.setdefault("ui_state", {})
        if ui_state.get("last_script_id") == removed_script_id:
            ui_state["last_script_id"] = scripts[0].get("id", "") if scripts else ""
            ui_state["last_step_id"] = ""
        self._persist_profile()
        self._refresh_scripts()

    def _add_script_step(self):
        script = self._current_script()
        if not script:
            return
        dialog = ScriptStepDialog(
            self._profile.get("quick_settings", []),
            self._profile.get("shortcuts", []),
            serial_check_presets=self._profile.setdefault("serial_check_presets", []),
            on_presets_changed=self._persist_profile,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        step = dialog.get_data()
        step["id"] = self._store.make_id("step")
        script.setdefault("steps", []).append(step)
        self._profile.setdefault("ui_state", {})["last_step_id"] = step["id"]
        self._persist_profile()
        self._refresh_script_steps()
        self._select_script_step(step["id"])

    def _edit_script_step(self):
        script = self._current_script()
        step = self._current_script_step()
        if not script or not step:
            return
        dialog = ScriptStepDialog(
            self._profile.get("quick_settings", []),
            self._profile.get("shortcuts", []),
            step,
            serial_check_presets=self._profile.setdefault("serial_check_presets", []),
            on_presets_changed=self._persist_profile,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        step.update(dialog.get_data())
        self._profile.setdefault("ui_state", {})["last_step_id"] = step.get("id", "")
        self._persist_profile()
        self._refresh_script_steps()
        self._select_script_step(step.get("id"))

    def _delete_script_step(self):
        script = self._current_script()
        step = self._current_script_step()
        if not script or not step:
            return
        removed_step_id = step.get("id")
        script["steps"] = [item for item in script.get("steps", []) if item.get("id") != removed_step_id]
        ui_state = self._profile.setdefault("ui_state", {})
        if ui_state.get("last_step_id") == removed_step_id:
            ui_state["last_step_id"] = script["steps"][0].get("id", "") if script.get("steps") else ""
        self._persist_profile()
        self._refresh_script_steps()

    def _select_script(self, script_id: Optional[str]):
        if not script_id:
            return
        item = self._find_script_tree_item(script_id)
        if item is not None:
            parent = item.parent()
            if parent is not None:
                parent.setExpanded(True)
            self.list_scripts.setCurrentItem(item)

    def _move_script_step_up(self):
        self._move_script_step(-1)

    def _move_script_step_down(self):
        self._move_script_step(1)

    def _move_script_step(self, offset: int):
        script = self._current_script()
        step = self._current_script_step()
        if not script or not step:
            return
        steps = script.get("steps", [])
        current_index = next((idx for idx, item in enumerate(steps) if item.get("id") == step.get("id")), -1)
        if current_index < 0:
            return
        new_index = current_index + offset
        if new_index < 0 or new_index >= len(steps):
            return
        steps[current_index], steps[new_index] = steps[new_index], steps[current_index]
        self._persist_profile()
        self._refresh_script_steps()
        self._select_script_step(step.get("id"))

    def _select_script_step(self, step_id: Optional[str]):
        if not step_id:
            return
        item = self._find_step_tree_item(step_id)
        if item is not None:
            self.list_script_steps.setCurrentItem(item)

    def _run_selected_script(self):
        script = self._current_script()
        if not script:
            return
        if self._queue_busy or self._queue_timer.isActive() or self._command_queue:
            QMessageBox.warning(self, "提示", "当前已有执行中的队列，请先等待完成或暂停后处理")
            return
        if self._camera_capture is not None:
            self._log("执行剧本前已断开实时预览，后续拍摄将显示静态回显", "WARN")
            self._stop_camera_preview()
        self._active_run_context = self._create_run_context(script)
        self._script_variables = {}
        self._failure_notified = False
        self._paused_elapsed = 0.0
        self._run_metrics = {
            'script_name': script.get('name', ''),
            'run_count': int(script.get('run_count', 1) or 1),
            'current_cycle': 1,
            'total_cycles': int(script.get('run_count', 1) or 1),
            'saved_images': 0,
            'error_count': 0,
            'start_time': time.time(),
        }
        actions = self._build_actions_from_script(script)
        if not actions:
            QMessageBox.warning(self, "提示", "当前剧本没有可执行步骤")
            self._active_run_context = None
            self._run_metrics = {}
            return
        self._log(f"开始执行联调剧本: {script['name']} | 输出目录: {self._active_run_context.get('base_dir', '')}")
        self._run_stats_timer.start()
        self._update_run_stats(force_status='运行中')
        self._queue_commands(actions)

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
        self._queue_commands([
            {"type": "serial", "command": command, "delay_seconds": 0.25, "source": f"快捷配置 {item['name']}"}
            for command in item.get("commands", []) if command
        ])

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
        self._queue_commands(self._build_actions_from_shortcut(item, "快捷指令"))

    def _edit_or_add_command_item(self, section: str, item: Optional[Dict[str, Any]], title: str):
        dialog = CommandItemDialog(title, item, allow_camera_actions=(section == "shortcuts"), parent=self)
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
        self._profile.setdefault("serial", {})["tab_passthrough"] = self.chk_tab_passthrough.isChecked()
        self._profile["serial"]["newline_mode"] = self.combo_newline.currentText()
        self._profile["serial"]["newline"] = self.chk_newline.isChecked()
        self._profile.setdefault("camera", {})["preview_zoom_percent"] = self.slider_preview_zoom.value()
        self._profile["camera"]["reference_dir"] = self.edit_reference_dir.text().strip()
        self._profile["camera"]["reference_category"] = self.edit_reference_category.text().strip() or "default"
        self._profile["camera"]["compare_roi"] = self.edit_compare_roi.text().strip()
        self._profile["camera"]["save_diff_heatmap"] = self.chk_save_diff_heatmap.isChecked()
        self._profile["camera"]["reference_pool_size"] = self.spin_reference_pool_size.value()
        self._profile["camera"]["auto_reference_enabled"] = False
        self._profile["camera"]["auto_reference_interval_ms"] = self.spin_auto_reference_interval.value()
        self._profile["camera"]["auto_reference_max_retry"] = self.spin_auto_reference_retry.value()
        ui_state = self._profile.setdefault("ui_state", {})
        project = self._current_project()
        script = self._current_script()
        step = self._current_script_step()
        ui_state["last_project_id"] = project.get("id", "") if project else ""
        ui_state["last_script_id"] = script.get("id", "") if script else ""
        ui_state["last_step_id"] = step.get("id", "") if step else ""
        self._store.set_all(self._profile)
        self._store.save()

    def _log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {level:<5} {message}"
        self.text_log.appendPlainText(line)
        if self._run_log_file is not None:
            try:
                self._run_log_file.write(line + "\n")
                self._run_log_file.flush()
            except Exception:
                pass
        if level == 'ERROR' and self._run_metrics:
            self._run_metrics['error_count'] = int(self._run_metrics.get('error_count', 0)) + 1
            self._update_run_stats()
        if self._log_panel is not None:
            panel_level = {
                "INFO": "INFO",
                "WARN": "WARNING",
                "ERROR": "ERROR",
            }.get(level, "INFO")
            self._log_panel.append_log(message, panel_level)

    def cleanup(self):
        # 如果有未完成的执行，保存状态用于下次恢复
        if self._run_metrics and (self._command_queue or self._queue_paused):
            self._save_execution_state()
        self._persist_profile()
        self._reference_capture_timer.stop()
        self._close_script_capture()
        self._stop_camera_preview()
        self._disconnect_serial()
