# -*- coding: utf-8 -*-
"""
AI Agent 引擎

实现 ReAct 模式（Observe → Think → Act → Observe）的 Agent 循环。
支持：
- 自动事件响应（订阅事件总线，触发时自动分析 + 通知）
- 手动对话模式（用户通过 AI 面板发起交互）
- 流式输出回调
"""

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Agent 状态
STATE_IDLE = "idle"
STATE_THINKING = "thinking"
STATE_ACTING = "acting"
STATE_WAITING_USER = "waiting_user"


class AIAgent:
    """
    AI Agent 引擎。

    负责协调 AI 服务、工具注册表，实现自主决策循环。
    """

    def __init__(self):
        self._state = STATE_IDLE
        self._lock = threading.Lock()
        self._on_state_change: Optional[Callable[[str], None]] = None
        self._on_message: Optional[Callable[[str, str], None]] = None  # (role, content)
        self._on_tool_call: Optional[Callable[[str, dict, str], None]] = None  # (name, args, result)
        self._conversation: List[Dict[str, str]] = []

        # 系统提示词
        self._system_prompt = (
            "你是 DLP 自动化测试系统的 AI 助手。你的职责是：\n"
            "1. 分析测试执行中的失败原因\n"
            "2. 通过飞书群发送测试状态通知\n"
            "3. 查询和分析日志、串口输出\n"
            "4. 帮助用户控制测试脚本（恢复/停止）\n\n"
            "你可以调用以下工具来完成任务。请用中文回复。\n"
            "当测试暂停时，请先分析可能的原因，然后生成简洁的通知摘要发送到飞书。"
        )

    # ------------------------------------------------------------------
    # 状态管理
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    def _set_state(self, new_state: str):
        self._state = new_state
        if self._on_state_change:
            try:
                self._on_state_change(new_state)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 回调注册
    # ------------------------------------------------------------------

    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[str], None]] = None,
        on_message: Optional[Callable[[str, str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict, str], None]] = None,
    ):
        """
        设置 UI 回调。

        Args:
            on_state_change: 状态变更回调 (new_state)
            on_message:      消息回调 (role, content) — role: "user"/"assistant"/"system"
            on_tool_call:    工具调用回调 (tool_name, arguments, result)
        """
        self._on_state_change = on_state_change
        self._on_message = on_message
        self._on_tool_call = on_tool_call

    def _emit_message(self, role: str, content: str):
        if self._on_message:
            try:
                self._on_message(role, content)
            except Exception:
                pass

    def _emit_tool_call(self, name: str, args: dict, result: str):
        if self._on_tool_call:
            try:
                self._on_tool_call(name, args, result)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 对话管理
    # ------------------------------------------------------------------

    def clear_conversation(self):
        """清空对话历史。"""
        self._conversation.clear()

    def get_conversation(self) -> List[Dict[str, str]]:
        """获取当前对话历史。"""
        return list(self._conversation)

    # ------------------------------------------------------------------
    # 核心：对话执行
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        max_rounds: int = 5,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        用户发起对话，Agent 自动完成工具调用循环。

        Args:
            user_message: 用户输入
            max_rounds:   最大 Agent 循环轮数
            on_chunk:     流式输出回调

        Returns:
            最终 AI 回复文本
        """
        from core.ai_service import get_ai_service, AIServiceError
        from core.ai_tools import get_tool_registry

        ai = get_ai_service()
        tools = get_tool_registry()

        if not ai.is_configured:
            msg = "AI 未配置，请先在设置中填入 API Key。"
            self._emit_message("system", msg)
            return msg

        # 追加用户消息
        self._conversation.append({"role": "user", "content": user_message})
        self._emit_message("user", user_message)

        # 构建完整消息（含系统提示）
        messages = [{"role": "system", "content": self._system_prompt}]
        messages.extend(self._conversation)

        tool_schemas = tools.get_schemas()
        self._set_state(STATE_THINKING)

        try:
            final_text = ai.chat_with_tools(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
                tool_handler=self._handle_tool_call,
                max_rounds=max_rounds,
                on_chunk=on_chunk,
            )
        except AIServiceError as e:
            final_text = f"AI 调用失败: {e}"
            self._emit_message("system", final_text)
            self._set_state(STATE_IDLE)
            return final_text

        # 保存 assistant 回复到对话历史
        self._conversation.append({"role": "assistant", "content": final_text})
        self._emit_message("assistant", final_text)
        self._set_state(STATE_IDLE)
        return final_text

    def _handle_tool_call(self, name: str, arguments: dict) -> str:
        """处理 AI 的工具调用请求。"""
        from core.ai_tools import get_tool_registry

        self._set_state(STATE_ACTING)
        logger.info("Agent 执行工具: %s(%s)", name, arguments)

        tools = get_tool_registry()
        result = tools.call(name, arguments)

        self._emit_tool_call(name, arguments, result)
        self._set_state(STATE_THINKING)
        return result

    # ------------------------------------------------------------------
    # 自动事件响应
    # ------------------------------------------------------------------

    def handle_event(self, event_type: str, data: dict):
        """
        处理来自事件总线的事件。
        仅处理步骤级事件（由步骤 notify_on_fail 触发），不做全局规则过滤。

        Args:
            event_type: 事件类型
            data:       事件数据
        """
        from core.config_manager import ConfigManager
        import os

        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config'
        )
        cm = ConfigManager(config_dir=config_dir)
        rules = cm.load_ai_config().get("notification_rules", {})

        # 构建上下文摘要
        include_logs = data.get("include_logs", rules.get("include_logs", True))
        context_text = self._build_event_context(event_type, data, rules, include_logs=include_logs)

        # 检查步骤级自定义补充内容
        custom_content = data.get("notify_content", "")

        # 变量替换自定义内容
        if custom_content:
            var_map = {
                "{step_name}": data.get("step_name", ""),
                "{reason}": data.get("reason", data.get("error", "")),
                "{script_name}": data.get("script_name", ""),
                "{status}": data.get("status", ""),
                "{duration}": data.get("duration", ""),
            }
            for k, v in var_map.items():
                custom_content = custom_content.replace(k, str(v))

        # 始终使用 AI 摘要；自定义内容作为补充附在尾部
        if rules.get("use_ai_summary", True):
            self._ai_analyze_and_notify(event_type, data, context_text, extra_note=custom_content)
        else:
            self._direct_notify(event_type, data, context_text, extra_note=custom_content)

    def _build_event_context(self, event_type: str, data: dict, rules: dict, include_logs: bool = True) -> str:
        """从事件数据构建上下文描述。"""
        parts = []
        parts.append(f"事件类型: {event_type}")

        if "script_name" in data:
            parts.append(f"脚本名称: {data['script_name']}")
        if "step_name" in data:
            parts.append(f"当前步骤: {data['step_name']}")
        if "step_index" in data:
            parts.append(f"步骤序号: {data['step_index']}")
        if "reason" in data:
            parts.append(f"原因: {data['reason']}")
        if "error" in data:
            parts.append(f"错误: {data['error']}")
        if "status" in data:
            parts.append(f"状态: {data['status']}")
        if "duration" in data:
            parts.append(f"耗时: {data['duration']}")

        # 附带日志
        if include_logs:
            from core.ai_tools import get_tool_registry
            tools = get_tool_registry()
            log_buffer = tools.get_context("log_buffer")
            max_lines = rules.get("max_log_lines", 30)
            if log_buffer and isinstance(log_buffer, list):
                recent = log_buffer[-max_lines:]
                parts.append("--- 最近日志 ---")
                parts.extend(str(l) for l in recent)

        return "\n".join(parts)

    def _ai_analyze_and_notify(self, event_type: str, data: dict, context: str, extra_note: str = ""):
        """使用 AI 分析事件并生成通知。extra_note 作为补充附在 AI 摘要尾部。"""
        from core.ai_service import get_ai_service, AIServiceError

        ai = get_ai_service()
        if not ai.is_configured:
            logger.warning("AI 未配置，回退到直接通知")
            self._direct_notify(event_type, data, context)
            return

        prompt = (
            f"以下是一个 DLP 自动化测试事件，请分析并生成简洁的飞书群通知摘要：\n\n"
            f"{context}\n\n"
            f"要求：\n"
            f"1. 用 2-3 句话概括发生了什么\n"
            f"2. 如果是失败/暂停，推测可能原因\n"
            f"3. 给出建议的下一步操作\n"
            f"4. 语言简洁专业"
        )

        try:
            result = ai.chat(
                [{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            summary = result.get("content", "")
        except AIServiceError as e:
            logger.error("AI 分析失败: %s", e)
            summary = ""

        if not summary:
            self._direct_notify(event_type, data, context, extra_note=extra_note)
            return

        # 将用户自定义补充内容附在 AI 摘要尾部
        if extra_note:
            summary = f"{summary}\n\n📌 {extra_note}"

        # 使用 AI 生成的摘要发送飞书
        from core.feishu_service import get_feishu_service, FeishuTemplates
        fs = get_feishu_service()
        if not fs.webhook_configured and not fs.openapi_configured:
            logger.warning("飞书未配置，跳过通知")
            return

        try:
            if event_type in ("script_paused", "step_failed", "condition_check_failed"):
                payload = FeishuTemplates.test_paused_card(
                    title=data.get("script_name", "未知脚本"),
                    step_name=data.get("step_name", ""),
                    reason=data.get("reason", data.get("error", "")),
                    logs=context.split("--- 最近日志 ---")[-1] if "--- 最近日志 ---" in context else "",
                    issue_link=data.get("issue_link", ""),
                    extra=f"🤖 AI 分析：\n{summary}",
                )
            elif event_type == "script_finished":
                payload = FeishuTemplates.test_completed_card(
                    title=data.get("script_name", "未知脚本"),
                    status=data.get("status", "完成"),
                    duration=data.get("duration", ""),
                    summary=summary,
                )
            else:
                payload = FeishuTemplates.simple_text(
                    f"[{event_type}] {data.get('script_name', '')}\n{summary}"
                )
            fs.send(payload)
            logger.info("AI 分析通知已发送: [%s]", event_type)
        except Exception as e:
            logger.error("飞书通知发送失败: %s", e)

    def _direct_notify(self, event_type: str, data: dict, context: str, extra_note: str = ""):
        """不使用 AI，直接发送事件通知到飞书。extra_note 附在卡片尾部。"""
        from core.feishu_service import get_feishu_service, FeishuTemplates
        fs = get_feishu_service()
        if not fs.webhook_configured and not fs.openapi_configured:
            return

        try:
            if event_type in ("script_paused", "step_failed", "condition_check_failed"):
                payload = FeishuTemplates.test_paused_card(
                    title=data.get("script_name", "未知脚本"),
                    step_name=data.get("step_name", ""),
                    reason=data.get("reason", data.get("error", "")),
                    extra=f"📌 {extra_note}" if extra_note else "",
                )
            elif event_type == "script_finished":
                payload = FeishuTemplates.test_completed_card(
                    title=data.get("script_name", "未知脚本"),
                    status=data.get("status", "完成"),
                    duration=data.get("duration", ""),
                    summary=extra_note,
                )
            else:
                payload = FeishuTemplates.simple_text(
                    f"[{event_type}] {data.get('script_name', '')}: "
                    f"{data.get('reason', data.get('error', ''))}"
                )
            fs.send(payload)
        except Exception as e:
            logger.error("直接飞书通知失败: %s", e)

    # ------------------------------------------------------------------
    # 事件总线集成
    # ------------------------------------------------------------------

    def bind_event_bus(self):
        """
        将 Agent 绑定到全局事件总线，自动响应测试事件。
        """
        from core.event_bus import get_event_bus, Events

        bus = get_event_bus()
        events_to_watch = [
            Events.STEP_FAILED,
            Events.CONDITION_CHECK_FAILED,
            Events.COMPARE_FAILED,
            Events.GREEN_SCREEN_DETECTED,
            Events.AI_NOTIFY_TRIGGERED,
        ]
        for evt in events_to_watch:
            bus.subscribe(evt, self._on_event)

        logger.info("AI Agent 已绑定事件总线（监听 %d 种事件）", len(events_to_watch))

    def _on_event(self, event_type: str, data: dict):
        """事件回调入口（在事件发布线程中执行）。"""
        # 用后台线程处理，避免阻塞执行器
        t = threading.Thread(
            target=self.handle_event,
            args=(event_type, data),
            daemon=True,
        )
        t.start()


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_instance: Optional[AIAgent] = None


def get_ai_agent() -> AIAgent:
    """获取全局 AI Agent 单例。"""
    global _instance
    if _instance is None:
        _instance = AIAgent()
    return _instance
