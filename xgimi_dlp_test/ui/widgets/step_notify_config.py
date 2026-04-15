# -*- coding: utf-8 -*-
"""
步骤通知配置弹窗

从当前剧本中列出所有步骤（去重），用户勾选要触发自动通知的步骤。
勾选后，对应步骤的 notify_on_fail 字段会被更新。
"""

import os
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class StepNotifyConfigDialog(QDialog):
    """
    步骤自动通知配置弹窗。

    显示当前剧本中所有可触发通知的步骤（去重），
    用户勾选后保存到步骤的 notify_on_fail 字段。
    """

    # 支持通知的步骤类型（会检测失败/暂停的类型）
    _NOTIFY_TYPES = {
        "serial_check": "条件检查",
        "compare_reference": "检查参考图",
        "green_screen_detect": "绿屏检测",
        "serial": "串口指令",
    }

    def __init__(self, script: Dict[str, Any], parent=None):
        """
        Args:
            script: 剧本数据字典，包含 steps 列表
        """
        super().__init__(parent)
        self.setWindowTitle("📨 配置步骤自动通知")
        self.setMinimumSize(520, 400)
        self._script = script
        self._steps = script.get("steps", [])
        self._step_groups: List[Dict[str, Any]] = []  # 去重后的步骤组
        self._checkboxes: List[QCheckBox] = []
        self._selected_group_idx: int = -1  # 当前在右侧编辑的组索引
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 说明
        desc = QLabel(
            "勾选步骤后，当该步骤执行失败/条件不满足时，系统会自动发送飞书通知。\n"
            "点击步骤可在右侧编辑通知内容。相同类型+指令的步骤已合并显示。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; padding: 4px 0;")
        layout.addWidget(desc)

        # 左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # --- 左侧：步骤列表 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.step_list = QListWidget()
        self.step_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.step_list.currentRowChanged.connect(self._on_step_selected)
        left_layout.addWidget(self.step_list, 1)

        self._build_step_list()

        # 统计
        total = len(self._step_groups)
        checked = sum(1 for g in self._step_groups if g["notify_on_fail"])
        self.lbl_stats = QLabel(f"共 {total} 个可配置步骤，已启用 {checked} 个通知")
        self.lbl_stats.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0;")
        left_layout.addWidget(self.lbl_stats)

        # 快捷操作
        quick_row = QHBoxLayout()
        btn_select_all = QPushButton("全选")
        btn_select_all.clicked.connect(self._select_all)
        btn_deselect_all = QPushButton("全不选")
        btn_deselect_all.clicked.connect(self._deselect_all)
        btn_select_checks = QPushButton("仅选条件检查")
        btn_select_checks.clicked.connect(self._select_checks_only)
        quick_row.addWidget(btn_select_all)
        quick_row.addWidget(btn_deselect_all)
        quick_row.addWidget(btn_select_checks)
        quick_row.addStretch()
        left_layout.addLayout(quick_row)

        splitter.addWidget(left_widget)

        # --- 右侧：通知内容编辑 ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.notify_group = QGroupBox("通知内容配置")
        notify_form = QFormLayout(self.notify_group)

        self.edit_notify_title = QLineEdit()
        self.edit_notify_title.setPlaceholderText("通知标题（留空则自动生成）")
        notify_form.addRow("标题:", self.edit_notify_title)

        self.edit_notify_content = QPlainTextEdit()
        self.edit_notify_content.setPlaceholderText(
            "补充说明（会附在 AI 摘要尾部）...\n\n"
            "例如：\n"
            "  注意事项：该步骤连续失败3次请检查硬件\n"
            "  提示：优先确认串口连接是否正常\n\n"
            "支持变量：\n"
            "  {step_name} — 步骤名称\n"
            "  {reason} — 失败原因\n"
            "  {script_name} — 剧本名称"
        )
        self.edit_notify_content.setMaximumHeight(150)
        notify_form.addRow("补充说明:", self.edit_notify_content)

        self.chk_notify_include_logs = QCheckBox("附带最近日志")
        self.chk_notify_include_logs.setChecked(True)
        notify_form.addRow("", self.chk_notify_include_logs)

        self.lbl_notify_hint = QLabel("← 请在左侧选择一个步骤进行编辑")
        self.lbl_notify_hint.setStyleSheet("color: #999; padding: 20px;")
        self.lbl_notify_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.lbl_notify_hint)
        right_layout.addWidget(self.notify_group)
        self.notify_group.setVisible(False)

        right_layout.addStretch()
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 300])

        # 底部按钮
        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_save = QPushButton("💾 保存配置")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_save)
        bottom.addWidget(btn_cancel)
        layout.addLayout(bottom)

    def _build_step_list(self):
        """构建去重后的步骤列表。"""
        seen = set()

        for step in self._steps:
            step_type = step.get("type", "serial")
            if step_type not in self._NOTIFY_TYPES:
                continue

            # 去重键：类型 + 指令/目标
            key_cmd = step.get("command", "").strip()
            key_target = step.get("target", "").strip()
            key_ref = step.get("check_reference", "").strip()
            dedup_key = f"{step_type}|{key_cmd}|{key_target}|{key_ref}"

            if dedup_key in seen:
                # 找到已存在的分组，添加 step_id
                for g in self._step_groups:
                    if g["dedup_key"] == dedup_key:
                        g["step_ids"].append(step.get("id", ""))
                        break
                continue
            seen.add(dedup_key)

            # 构建显示摘要
            type_label = self._NOTIFY_TYPES.get(step_type, step_type)
            summary = self._step_summary(step, type_label)

            group = {
                "dedup_key": dedup_key,
                "step_ids": [step.get("id", "")],
                "step_type": step_type,
                "summary": summary,
                "notify_on_fail": bool(step.get("notify_on_fail", False)),
                "notify_title": step.get("notify_title", ""),
                "notify_content": step.get("notify_content", ""),
                "include_logs": bool(step.get("include_logs", True)),
                "use_ai_summary": bool(step.get("use_ai_summary", False)),
            }
            self._step_groups.append(group)

            # 创建 UI 项
            item = QListWidgetItem()
            chk = QCheckBox(summary)
            chk.setChecked(group["notify_on_fail"])
            chk.stateChanged.connect(self._update_stats)
            self._checkboxes.append(chk)
            self.step_list.addItem(item)
            self.step_list.setItemWidget(item, chk)

        if not self._step_groups:
            item = QListWidgetItem("当前剧本中没有可配置通知的步骤")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.step_list.addItem(item)

    def _step_summary(self, step: Dict[str, Any], type_label: str) -> str:
        """生成步骤的显示摘要。"""
        parts = [f"[{type_label}]"]
        note = step.get("note", "").strip()
        if note:
            parts.append(note)
        else:
            cmd = step.get("command", "").strip()
            target = step.get("target", "").strip()
            ref = step.get("check_reference", "").strip()
            if cmd:
                parts.append(cmd[:40])
            if target:
                parts.append(target)
            if ref:
                parts.append(f"参考值: {ref[:30]}")
        return " ".join(parts)

    def _update_stats(self):
        """更新统计标签。"""
        total = len(self._checkboxes)
        checked = sum(1 for chk in self._checkboxes if chk.isChecked())
        self.lbl_stats.setText(f"共 {total} 个可配置步骤，已启用 {checked} 个通知")

    def _select_all(self):
        for chk in self._checkboxes:
            chk.setChecked(True)

    def _deselect_all(self):
        for chk in self._checkboxes:
            chk.setChecked(False)

    def _select_checks_only(self):
        """仅勾选条件检查类步骤。"""
        for i, chk in enumerate(self._checkboxes):
            is_check = self._step_groups[i]["step_type"] == "serial_check"
            chk.setChecked(is_check)

    # ------------------------------------------------------------------
    # 右侧通知内容编辑
    # ------------------------------------------------------------------

    def _on_step_selected(self, row: int):
        """左侧步骤列表选中变化时，加载对应的通知内容到右侧编辑区。"""
        # 先保存上一个选中项的编辑内容
        self._save_current_notify_config()

        if row < 0 or row >= len(self._step_groups):
            self.notify_group.setVisible(False)
            self.lbl_notify_hint.setVisible(True)
            self._selected_group_idx = -1
            return

        self._selected_group_idx = row
        group = self._step_groups[row]

        self.edit_notify_title.setText(group.get("notify_title", ""))
        self.edit_notify_content.setPlainText(group.get("notify_content", ""))
        self.chk_notify_include_logs.setChecked(group.get("include_logs", True))

        self.notify_group.setVisible(True)
        self.lbl_notify_hint.setVisible(False)

    def _save_current_notify_config(self):
        """将右侧编辑区的内容保存回当前选中的步骤组。"""
        idx = self._selected_group_idx
        if idx < 0 or idx >= len(self._step_groups):
            return
        group = self._step_groups[idx]
        group["notify_title"] = self.edit_notify_title.text().strip()
        group["notify_content"] = self.edit_notify_content.toPlainText().strip()
        group["include_logs"] = self.chk_notify_include_logs.isChecked()

    def _on_save(self):
        """保存配置到步骤数据。"""
        # 先保存当前编辑中的内容
        self._save_current_notify_config()

        for i, group in enumerate(self._step_groups):
            new_notify = self._checkboxes[i].isChecked()
            for step in self._steps:
                if step.get("id", "") in group["step_ids"]:
                    step["notify_on_fail"] = new_notify
                    step["notify_title"] = group.get("notify_title", "")
                    step["notify_content"] = group.get("notify_content", "")
                    step["include_logs"] = group.get("include_logs", True)
                    step["use_ai_summary"] = group.get("use_ai_summary", False)

        self.accept()

    def get_modified_steps(self) -> List[Dict[str, Any]]:
        """获取修改后的完整步骤列表。"""
        return self._steps
