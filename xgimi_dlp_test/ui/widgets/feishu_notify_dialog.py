# -*- coding: utf-8 -*-
"""
飞书通知发送弹窗

可复用的通知配置对话框，支持：
- 自定义标题、正文
- 勾选附件（txt/png/csv 等文件列表）
- 勾选是否附带日志
- 预设上下文（脚本名、步骤名、输出内容描述）
- 支持 Webhook（纯文本/卡片）+ Open API（文本+文件）两种模式
"""

import os
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
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
    QVBoxLayout,
)


class FeishuNotifyDialog(QDialog):
    """
    飞书通知发送弹窗。

    使用方式：
        dlg = FeishuNotifyDialog(parent)
        dlg.set_preset(title="角度分析完成", description="...", files=[...])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # 通知已发送
            pass
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📨 飞书通知发送")
        self.setMinimumSize(520, 560)
        self._file_paths: List[str] = []
        self._init_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- 消息内容 ---
        msg_group = QGroupBox("消息内容")
        msg_form = QFormLayout(msg_group)

        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("通知标题（如：角度边界分析完成）")
        msg_form.addRow("标题:", self.edit_title)

        self.edit_content = QPlainTextEdit()
        self.edit_content.setPlaceholderText(
            "通知正文内容...\n"
            "支持飞书 Markdown 语法（仅卡片模式）"
        )
        self.edit_content.setMaximumHeight(120)
        msg_form.addRow("正文:", self.edit_content)

        self.chk_use_card = QCheckBox("使用卡片格式（更美观，支持 Markdown）")
        self.chk_use_card.setChecked(True)
        msg_form.addRow("", self.chk_use_card)

        self.chk_include_logs = QCheckBox("附带最近日志（最多 30 行）")
        msg_form.addRow("", self.chk_include_logs)

        layout.addWidget(msg_group)

        # --- 附件文件 ---
        file_group = QGroupBox("附件文件（仅 Open API 模式支持文件发送）")
        file_layout = QVBoxLayout(file_group)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        file_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ 添加文件")
        btn_add.clicked.connect(self._add_files)
        btn_remove = QPushButton("🗑️ 移除选中")
        btn_remove.clicked.connect(self._remove_checked_files)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        file_layout.addLayout(btn_row)

        layout.addWidget(file_group)

        # --- 预览信息 ---
        self.lbl_preview = QLabel("")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        layout.addWidget(self.lbl_preview)

        # --- 底部按钮 ---
        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_send = QPushButton("📨 发送")
        btn_send.setDefault(True)
        btn_send.clicked.connect(self._on_send)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_send)
        bottom.addWidget(btn_cancel)
        layout.addLayout(bottom)

    # ------------------------------------------------------------------
    # 预设
    # ------------------------------------------------------------------

    def set_preset(
        self,
        title: str = "",
        description: str = "",
        files: Optional[List[str]] = None,
        include_logs: bool = False,
        context_info: str = "",
    ):
        """
        设置预填内容。

        Args:
            title:        通知标题
            description:  正文内容
            files:        预填文件列表（绝对路径）
            include_logs: 是否默认勾选附带日志
            context_info: 底部预览区的上下文信息
        """
        if title:
            self.edit_title.setText(title)
        if description:
            self.edit_content.setPlainText(description)
        if files:
            for fp in files:
                if os.path.isfile(fp):
                    self._add_file_item(fp, checked=True)
        self.chk_include_logs.setChecked(include_logs)
        if context_info:
            self.lbl_preview.setText(f"📋 上下文: {context_info}")

    # ------------------------------------------------------------------
    # 文件管理
    # ------------------------------------------------------------------

    def _add_files(self):
        """弹出文件选择器添加文件。"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择附件文件", "",
            "所有文件 (*);;图片 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;文本 (*.txt *.csv *.log)"
        )
        for fp in paths:
            if fp not in self._file_paths:
                self._add_file_item(fp, checked=True)

    def _add_file_item(self, file_path: str, checked: bool = True):
        """向列表添加一个文件项。"""
        self._file_paths.append(file_path)
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, file_path)

        chk = QCheckBox(os.path.basename(file_path))
        chk.setChecked(checked)
        chk.setToolTip(file_path)

        # 文件大小
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            chk.setText(f"{os.path.basename(file_path)}  ({size_str})")
        except OSError:
            pass

        self.file_list.addItem(item)
        self.file_list.setItemWidget(item, chk)

    def _remove_checked_files(self):
        """移除所有已勾选的文件。"""
        to_remove = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                to_remove.append(i)

        for i in reversed(to_remove):
            item = self.file_list.takeItem(i)
            fp = item.data(Qt.ItemDataRole.UserRole)
            if fp in self._file_paths:
                self._file_paths.remove(fp)

    def _get_checked_files(self) -> List[str]:
        """获取所有已勾选的文件路径。"""
        result = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                fp = item.data(Qt.ItemDataRole.UserRole)
                if fp:
                    result.append(fp)
        return result

    # ------------------------------------------------------------------
    # 发送
    # ------------------------------------------------------------------

    def _on_send(self):
        """执行发送逻辑。"""
        title = self.edit_title.text().strip()
        content = self.edit_content.toPlainText().strip()

        if not title and not content:
            QMessageBox.warning(self, "内容为空", "请至少填写标题或正文。")
            return

        # 获取附件
        checked_files = self._get_checked_files()

        # 构建正文
        full_content = content

        # 将勾选的文件名嵌入正文（仅名称，不含路径）
        if checked_files:
            file_names = [os.path.basename(f) for f in checked_files]
            file_section = "\n".join(f"  • {fn}" for fn in file_names)
            full_content += f"\n\n📎 相关文件 ({len(file_names)} 个):\n{file_section}"

        # 附带日志
        if self.chk_include_logs.isChecked():
            logs = self._collect_recent_logs()
            if logs:
                full_content += f"\n\n--- 最近日志 ---\n{logs}"

        try:
            from core.feishu_service import get_feishu_service, FeishuTemplates
            fs = get_feishu_service()

            # 发送文本/卡片消息
            if self.chk_use_card.isChecked():
                payload = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": title or "通知"},
                            "template": "blue",
                        },
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": full_content or title,
                                },
                            },
                            {
                                "tag": "note",
                                "elements": [{
                                    "tag": "plain_text",
                                    "content": "DLP 自动化测试系统",
                                }],
                            },
                        ],
                    },
                }
            else:
                text = f"【{title}】\n{full_content}" if title else full_content
                payload = FeishuTemplates.simple_text(text)

            fs.send(payload)

            # Open API 模式额外发送实际文件
            if checked_files and fs.openapi_configured:
                file_results = fs.send_files_batch(checked_files)
                failed = [r for r in file_results if r["status"] == "failed"]
                if failed:
                    names = ", ".join(os.path.basename(r["file"]) for r in failed)
                    QMessageBox.warning(
                        self, "部分文件发送失败",
                        f"以下文件发送失败:\n{names}"
                    )

            QMessageBox.information(self, "发送成功", "飞书通知已发送！")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "发送失败", f"飞书通知发送失败:\n\n{e}")

    def _collect_recent_logs(self, max_lines: int = 30) -> str:
        """尝试从工具注册表获取最近日志。"""
        try:
            from core.ai_tools import get_tool_registry
            registry = get_tool_registry()
            log_buffer = registry.get_context("log_buffer")
            if log_buffer and isinstance(log_buffer, list):
                lines = log_buffer[-max_lines:]
                return "\n".join(str(l) for l in lines)
        except Exception:
            pass
        return ""
