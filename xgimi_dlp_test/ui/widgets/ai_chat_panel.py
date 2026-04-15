# -*- coding: utf-8 -*-
"""AI 对话面板 Widget — 可嵌入主窗口或独立使用。"""

import time
import threading
from typing import Optional

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AIChatPanel(QWidget):
    """
    AI 对话面板。

    提供自然语言输入 → AI Agent 处理 → 结果展示。
    支持：流式输出、工具调用显示、快捷指令。
    """

    # 跨线程信号
    _sig_append_text = pyqtSignal(str, str)  # (role, content)
    _sig_tool_call = pyqtSignal(str, str, str)  # (name, args_str, result)
    _sig_state_change = pyqtSignal(str)  # new_state
    _sig_stream_chunk = pyqtSignal(str)  # delta_text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        self._is_streaming = False

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 标题栏
        header = QHBoxLayout()
        lbl_title = QLabel("🤖 AI 助手")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.lbl_status = QLabel("就绪")
        self.lbl_status.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_status)
        layout.addLayout(header)

        # 对话区
        self.txt_chat = QPlainTextEdit()
        self.txt_chat.setReadOnly(True)
        self.txt_chat.setPlaceholderText("与 AI 助手对话，输入问题或指令...")
        self.txt_chat.setStyleSheet(
            "QPlainTextEdit { background: #1a1a2e; color: #e0e0e0; "
            "border: 1px solid #333; border-radius: 4px; font-family: 'Consolas', 'Microsoft YaHei'; "
            "font-size: 12px; padding: 6px; }"
        )
        layout.addWidget(self.txt_chat, 1)

        # 快捷指令行
        shortcuts = QHBoxLayout()
        for label, cmd in [
            ("📊 分析失败", "请分析最近一次失败的原因并给出建议"),
            ("📨 发飞书", "请把当前测试状态发送到飞书群"),
            ("📋 查日志", "请获取最近20条执行日志"),
            ("📡 脚本状态", "请获取当前脚本的执行状态"),
        ]:
            btn = QPushButton(label)
            btn.setMaximumHeight(28)
            btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            btn.clicked.connect(lambda checked, c=cmd: self._send_shortcut(c))
            shortcuts.addWidget(btn)
        shortcuts.addStretch()
        layout.addLayout(shortcuts)

        # 输入区
        input_row = QHBoxLayout()
        self.edit_input = QLineEdit()
        self.edit_input.setPlaceholderText("输入指令或问题...")
        self.edit_input.returnPressed.connect(self._on_send)
        self.btn_send = QPushButton("发送")
        self.btn_send.clicked.connect(self._on_send)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._on_clear)
        input_row.addWidget(self.edit_input, 1)
        input_row.addWidget(self.btn_send)
        input_row.addWidget(self.btn_clear)
        layout.addLayout(input_row)

    def _connect_signals(self):
        self._sig_append_text.connect(self._do_append_text)
        self._sig_tool_call.connect(self._do_tool_call)
        self._sig_state_change.connect(self._do_state_change)
        self._sig_stream_chunk.connect(self._do_stream_chunk)

    # ------------------------------------------------------------------
    # 发送
    # ------------------------------------------------------------------

    def _send_shortcut(self, cmd: str):
        self.edit_input.setText(cmd)
        self._on_send()

    def _on_send(self):
        text = self.edit_input.text().strip()
        if not text:
            return
        self.edit_input.clear()
        self._append_message("user", text)
        self._run_agent(text)

    def _on_clear(self):
        self.txt_chat.clear()
        try:
            from core.ai_agent import get_ai_agent
            get_ai_agent().clear_conversation()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Agent 调用（后台线程）
    # ------------------------------------------------------------------

    def _run_agent(self, user_message: str):
        self.btn_send.setEnabled(False)
        self.lbl_status.setText("思考中...")

        def worker():
            try:
                from core.ai_agent import get_ai_agent
                agent = get_ai_agent()

                # 设置回调
                agent.set_callbacks(
                    on_state_change=lambda s: self._sig_state_change.emit(s),
                    on_message=None,  # 我们通过最终结果显示
                    on_tool_call=lambda n, a, r: self._sig_tool_call.emit(
                        n, str(a), r[:500]
                    ),
                )

                reply = agent.chat(
                    user_message,
                    on_chunk=lambda c: self._sig_stream_chunk.emit(c),
                )
                self._sig_append_text.emit("assistant", reply)
            except Exception as e:
                self._sig_append_text.emit("system", f"错误: {e}")
            finally:
                self._sig_state_change.emit("idle")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # UI 线程槽
    # ------------------------------------------------------------------

    def _append_message(self, role: str, content: str):
        """直接在 UI 线程追加消息。"""
        prefix_map = {
            "user": "👤 你",
            "assistant": "🤖 AI",
            "system": "⚠️ 系统",
            "tool": "🔧 工具",
        }
        prefix = prefix_map.get(role, role)
        self.txt_chat.appendPlainText(f"\n{prefix}:\n{content}")
        # 滚动到底部
        sb = self.txt_chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _do_append_text(self, role: str, content: str):
        if role == "assistant" and self._is_streaming:
            self._is_streaming = False
            self.txt_chat.appendPlainText("")  # 换行
        elif role == "assistant":
            self._append_message(role, content)
        else:
            self._append_message(role, content)

    def _do_tool_call(self, name: str, args_str: str, result: str):
        self.txt_chat.appendPlainText(f"\n🔧 调用工具: {name}")
        if args_str and args_str != "{}":
            self.txt_chat.appendPlainText(f"   参数: {args_str}")
        self.txt_chat.appendPlainText(f"   结果: {result}")
        sb = self.txt_chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _do_state_change(self, state: str):
        state_labels = {
            "idle": "就绪",
            "thinking": "🤔 思考中...",
            "acting": "⚡ 执行工具...",
            "waiting_user": "等待输入",
        }
        self.lbl_status.setText(state_labels.get(state, state))
        self.btn_send.setEnabled(state == "idle")

    def _do_stream_chunk(self, chunk: str):
        if not self._is_streaming:
            self._is_streaming = True
            self.txt_chat.appendPlainText("\n🤖 AI:")

        # 追加文本（不换行，模拟打字效果）
        cursor = self.txt_chat.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.txt_chat.setTextCursor(cursor)
        sb = self.txt_chat.verticalScrollBar()
        sb.setValue(sb.maximum())
