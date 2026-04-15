# -*- coding: utf-8 -*-
"""AI 助手设置页面 — 配置 AI 模型、飞书通知、触发规则。"""

import json
import os
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager


class AISettingsPage(QWidget):
    """AI 助手设置页面。"""

    def __init__(self, config_mgr: ConfigManager, log_panel=None, parent=None):
        super().__init__(parent)
        self._config_mgr = config_mgr
        self._log_panel = log_panel
        self._init_ui()
        self._load_config()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🤖 AI 助手设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 0;")
        layout.addWidget(title)

        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # --- AI 模型配置 ---
        ai_group = QGroupBox("通义千问 AI 模型配置")
        ai_form = QFormLayout(ai_group)

        self.edit_api_key = QLineEdit()
        self.edit_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_api_key.setPlaceholderText("sk-xxxxxxxxxxxx")
        ai_form.addRow("API Key:", self.edit_api_key)

        self.edit_base_url = QLineEdit()
        self.edit_base_url.setPlaceholderText("https://dashscope.aliyuncs.com/compatible-mode/v1")
        ai_form.addRow("Base URL:", self.edit_base_url)

        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "qwen3.5-flash", "qwen-plus", "qwen-turbo", "qwen-max",
            "qwen-long", "qwen-vl-plus", "qwen-vl-max",
        ])
        self.combo_model.setEditable(True)
        ai_form.addRow("模型:", self.combo_model)

        self.spin_max_tokens = QSpinBox()
        self.spin_max_tokens.setRange(128, 8192)
        self.spin_max_tokens.setValue(2048)
        ai_form.addRow("最大 Tokens:", self.spin_max_tokens)

        self.spin_temperature = QDoubleSpinBox()
        self.spin_temperature.setRange(0.0, 2.0)
        self.spin_temperature.setSingleStep(0.1)
        self.spin_temperature.setValue(0.7)
        ai_form.addRow("Temperature:", self.spin_temperature)

        btn_test_ai = QPushButton("🔗 测试 AI 连接")
        btn_test_ai.clicked.connect(self._test_ai_connection)
        ai_form.addRow("", btn_test_ai)

        scroll_layout.addWidget(ai_group)

        # --- 飞书配置 ---
        feishu_group = QGroupBox("飞书通知配置")
        feishu_form = QFormLayout(feishu_group)

        self.edit_webhook_url = QLineEdit()
        self.edit_webhook_url.setPlaceholderText("https://open.feishu.cn/open-apis/bot/v2/hook/...")
        feishu_form.addRow("Webhook URL:", self.edit_webhook_url)

        self.edit_webhook_secret = QLineEdit()
        self.edit_webhook_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_webhook_secret.setPlaceholderText("可选：签名密钥")
        feishu_form.addRow("Webhook 签名:", self.edit_webhook_secret)

        self.edit_app_id = QLineEdit()
        self.edit_app_id.setPlaceholderText("可选：Open API App ID")
        feishu_form.addRow("App ID:", self.edit_app_id)

        self.edit_app_secret = QLineEdit()
        self.edit_app_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_app_secret.setPlaceholderText("可选：Open API App Secret")
        feishu_form.addRow("App Secret:", self.edit_app_secret)

        self.edit_chat_id = QLineEdit()
        self.edit_chat_id.setPlaceholderText("可选：Open API 默认群组 chat_id")
        feishu_form.addRow("Chat ID:", self.edit_chat_id)

        self.combo_prefer_mode = QComboBox()
        self.combo_prefer_mode.addItems(["webhook", "openapi"])
        self.combo_prefer_mode.currentTextChanged.connect(self._on_prefer_mode_changed)
        feishu_form.addRow("优先模式:", self.combo_prefer_mode)

        self.lbl_openapi_hint = QLabel(
            "⚠️ OpenAPI 模式必须填写 App ID、App Secret 和 Chat ID，"
            "否则无法发送消息。请前往飞书开放平台创建应用并获取这些信息。"
        )
        self.lbl_openapi_hint.setWordWrap(True)
        self.lbl_openapi_hint.setStyleSheet("color: #e6a700; font-size: 12px; padding: 4px 0;")
        self.lbl_openapi_hint.setVisible(False)
        feishu_form.addRow("", self.lbl_openapi_hint)

        btn_test_feishu = QPushButton("📨 发送飞书测试消息")
        btn_test_feishu.clicked.connect(self._test_feishu_connection)
        feishu_form.addRow("", btn_test_feishu)

        scroll_layout.addWidget(feishu_group)

        # --- AI 通知行为 ---
        ai_notify_group = QGroupBox("AI 通知行为")
        ai_notify_layout = QVBoxLayout(ai_notify_group)

        self.chk_use_ai = QCheckBox("使用 AI 生成通知摘要（关闭则直接发送原始信息）")
        self.chk_include_logs = QCheckBox("在通知中附带最近日志")
        self.chk_notify_on_finish = QCheckBox("剧本自动执行完成后发送完成通知（手动停止不发）")
        self.chk_notify_on_finish.setChecked(False)

        self.spin_max_log_lines = QSpinBox()
        self.spin_max_log_lines.setRange(5, 100)
        self.spin_max_log_lines.setValue(30)

        ai_notify_layout.addWidget(self.chk_use_ai)
        ai_notify_layout.addWidget(self.chk_include_logs)
        ai_notify_layout.addWidget(self.chk_notify_on_finish)

        log_row = QHBoxLayout()
        log_row.addWidget(QLabel("最大日志行数:"))
        log_row.addWidget(self.spin_max_log_lines)
        log_row.addStretch()
        ai_notify_layout.addLayout(log_row)

        hint_label = QLabel("💡 通知触发由剧本步骤中的「失败时通知」开关控制，此处仅配置通知内容行为。")
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #888; font-size: 12px;")
        ai_notify_layout.addWidget(hint_label)

        scroll_layout.addWidget(ai_notify_group)
        scroll_layout.addStretch()

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 保存配置")
        btn_save.clicked.connect(self._save_config)
        btn_reset = QPushButton("🔄 恢复默认")
        btn_reset.clicked.connect(self._reset_config)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_reset)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # 配置 IO
    # ------------------------------------------------------------------

    def _load_config(self):
        cfg = self._config_mgr.load_ai_config()
        ai = cfg.get("ai", {})
        fs = cfg.get("feishu", {})
        rules = cfg.get("notification_rules", {})

        self.edit_api_key.setText(ai.get("api_key", ""))
        self.edit_base_url.setText(ai.get("base_url", ""))
        self.combo_model.setCurrentText(ai.get("model", "qwen-plus"))
        self.spin_max_tokens.setValue(ai.get("max_tokens", 2048))
        self.spin_temperature.setValue(ai.get("temperature", 0.7))

        self.edit_webhook_url.setText(fs.get("webhook_url", ""))
        self.edit_webhook_secret.setText(fs.get("webhook_secret", ""))
        self.edit_app_id.setText(fs.get("app_id", ""))
        self.edit_app_secret.setText(fs.get("app_secret", ""))
        self.edit_chat_id.setText(fs.get("default_chat_id", ""))
        self.combo_prefer_mode.setCurrentText(fs.get("prefer_mode", "webhook"))

        self.chk_use_ai.setChecked(rules.get("use_ai_summary", True))
        self.chk_include_logs.setChecked(rules.get("include_logs", True))
        self.chk_notify_on_finish.setChecked(rules.get("notify_on_finish", False))
        self.spin_max_log_lines.setValue(rules.get("max_log_lines", 30))

        # 初始化 OpenAPI 提示可见性
        self._on_prefer_mode_changed(self.combo_prefer_mode.currentText())

    def _build_config(self) -> dict:
        return {
            "ai": {
                "api_key": self.edit_api_key.text().strip(),
                "base_url": self.edit_base_url.text().strip(),
                "model": self.combo_model.currentText().strip(),
                "max_tokens": self.spin_max_tokens.value(),
                "temperature": self.spin_temperature.value(),
            },
            "feishu": {
                "webhook_url": self.edit_webhook_url.text().strip(),
                "webhook_secret": self.edit_webhook_secret.text().strip(),
                "app_id": self.edit_app_id.text().strip(),
                "app_secret": self.edit_app_secret.text().strip(),
                "default_chat_id": self.edit_chat_id.text().strip(),
                "prefer_mode": self.combo_prefer_mode.currentText(),
            },
            "notification_rules": {
                "use_ai_summary": self.chk_use_ai.isChecked(),
                "include_logs": self.chk_include_logs.isChecked(),
                "notify_on_finish": self.chk_notify_on_finish.isChecked(),
                "max_log_lines": self.spin_max_log_lines.value(),
            },
        }

    def _save_config(self):
        cfg = self._build_config()
        self._config_mgr.save_ai_config(cfg)
        self._config_mgr.apply_ai_config_to_services()
        QMessageBox.information(self, "保存成功", "AI 配置已保存并生效。")

    def _reset_config(self):
        defaults = self._config_mgr._AI_CONFIG_DEFAULTS
        self._config_mgr.save_ai_config(defaults)
        self._load_config()
        QMessageBox.information(self, "已重置", "AI 配置已恢复为默认值。")

    # ------------------------------------------------------------------
    # 测试
    # ------------------------------------------------------------------

    def _on_prefer_mode_changed(self, mode: str):
        """切换优先模式时显示/隐藏 OpenAPI 提示。"""
        is_openapi = (mode == "openapi")
        self.lbl_openapi_hint.setVisible(is_openapi)

    def _test_ai_connection(self):
        # 临时应用当前表单值
        cfg = self._build_config()
        self._config_mgr.save_ai_config(cfg)
        self._config_mgr.apply_ai_config_to_services()

        try:
            from core.ai_service import get_ai_service
            result = get_ai_service().test_connection()
            QMessageBox.information(self, "AI 连接测试", f"✅ 连接成功！\n\nAI 回复: {result}")
        except Exception as e:
            QMessageBox.warning(self, "AI 连接测试", f"❌ 连接失败:\n\n{e}")

    def _test_feishu_connection(self):
        cfg = self._build_config()
        fs = cfg["feishu"]

        # OpenAPI 模式校验必填项
        if fs["prefer_mode"] == "openapi":
            missing = []
            if not fs["app_id"]:
                missing.append("App ID")
            if not fs["app_secret"]:
                missing.append("App Secret")
            if not fs["default_chat_id"]:
                missing.append("Chat ID")
            if missing:
                QMessageBox.warning(
                    self, "OpenAPI 配置不完整",
                    f"OpenAPI 模式需要以下必填项：\n\n• {'、'.join(missing)}\n\n"
                    "请前往飞书开放平台（https://open.feishu.cn）创建应用后获取。"
                )
                return

        self._config_mgr.save_ai_config(cfg)
        self._config_mgr.apply_ai_config_to_services()

        try:
            from core.feishu_service import get_feishu_service
            get_feishu_service().test_connection()
            QMessageBox.information(self, "飞书连接测试", "✅ 消息发送成功！请检查飞书群。")
        except Exception as e:
            QMessageBox.warning(self, "飞书连接测试", f"❌ 发送失败:\n\n{e}")
