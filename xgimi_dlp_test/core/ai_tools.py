# -*- coding: utf-8 -*-
"""
AI Agent 工具注册表

定义 Agent 可调用的工具（OpenAI function calling 格式）。
每个工具包含：schema（JSON Schema 定义）和 handler（执行函数）。

工具在运行时会绑定到 device_lab_page 实例以访问剧本状态。
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Agent 工具注册表。

    管理可被 AI Agent 调用的工具集合。
    """

    def __init__(self):
        self._tools: Dict[str, dict] = {}  # name → {schema, handler}
        self._context: Dict[str, Any] = {}  # 运行时上下文

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
    ):
        """
        注册一个工具。

        Args:
            name:        工具名称（英文标识符）
            description: 工具用途描述（给 AI 看的）
            parameters:  JSON Schema 格式的参数定义
            handler:     执行函数 handler(**kwargs) -> str
        """
        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "handler": handler,
        }

    def get_schemas(self) -> List[dict]:
        """获取所有工具的 OpenAI tools schema 列表。"""
        return [t["schema"] for t in self._tools.values()]

    def call(self, name: str, arguments: dict) -> str:
        """
        调用指定工具。

        Args:
            name:      工具名称
            arguments: 参数字典

        Returns:
            工具执行结果字符串
        """
        if name not in self._tools:
            return f"错误: 未知工具 '{name}'"
        try:
            result = self._tools[name]["handler"](**arguments)
            return str(result)
        except Exception as e:
            logger.error("工具 %s 执行异常: %s", name, e)
            return f"工具执行错误: {e}"

    def set_context(self, key: str, value: Any):
        """设置运行时上下文（如当前页面实例引用）。"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取运行时上下文。"""
        return self._context.get(key, default)

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())


# ======================================================================
# 内置工具定义
# ======================================================================

def _register_builtin_tools(registry: ToolRegistry):
    """注册所有内置工具。"""

    # ------------------------------------------------------------------
    # 1. send_feishu_message — 发送飞书消息
    # ------------------------------------------------------------------
    def _send_feishu_message(text: str, use_card: bool = False, **kwargs) -> str:
        from core.feishu_service import get_feishu_service, FeishuTemplates
        fs = get_feishu_service()
        if not fs.webhook_configured and not fs.openapi_configured:
            return "飞书未配置，无法发送消息。"
        try:
            if use_card:
                payload = FeishuTemplates.test_paused_card(
                    title=kwargs.get("title", "AI 通知"),
                    step_name=kwargs.get("step_name", ""),
                    reason=text,
                    logs=kwargs.get("logs", ""),
                )
            else:
                payload = FeishuTemplates.simple_text(text)
            fs.send(payload)
            return "飞书消息发送成功。"
        except Exception as e:
            return f"飞书发送失败: {e}"

    registry.register(
        name="send_feishu_message",
        description="发送消息到飞书群。可以发送纯文本或卡片格式。",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要发送的消息内容",
                },
                "use_card": {
                    "type": "boolean",
                    "description": "是否使用卡片格式（默认纯文本）",
                    "default": False,
                },
            },
            "required": ["text"],
        },
        handler=_send_feishu_message,
    )

    # ------------------------------------------------------------------
    # 2. get_recent_logs — 获取最近日志
    # ------------------------------------------------------------------
    def _get_recent_logs(count: int = 20) -> str:
        log_buffer = registry.get_context("log_buffer")
        if log_buffer is None:
            return "日志缓冲区不可用。"
        lines = log_buffer[-count:] if isinstance(log_buffer, list) else []
        if not lines:
            return "暂无日志记录。"
        return "\n".join(str(l) for l in lines)

    registry.register(
        name="get_recent_logs",
        description="获取最近的测试执行日志。返回最近 N 条日志行。",
        parameters={
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "要获取的日志条数（默认20）",
                    "default": 20,
                },
            },
        },
        handler=_get_recent_logs,
    )

    # ------------------------------------------------------------------
    # 3. get_script_status — 获取当前脚本状态
    # ------------------------------------------------------------------
    def _get_script_status() -> str:
        status = registry.get_context("script_status")
        if status is None:
            return "当前没有正在执行的脚本。"
        return json.dumps(status, ensure_ascii=False, indent=2)

    registry.register(
        name="get_script_status",
        description="获取当前正在执行的脚本状态，包括脚本名称、当前步骤、进度、是否暂停等信息。",
        parameters={"type": "object", "properties": {}},
        handler=_get_script_status,
    )

    # ------------------------------------------------------------------
    # 4. get_step_result — 获取步骤结果
    # ------------------------------------------------------------------
    def _get_step_result(step_index: int = -1) -> str:
        results = registry.get_context("step_results")
        if not results:
            return "无步骤执行结果。"
        if step_index < 0:
            step_index = len(results) + step_index
        if 0 <= step_index < len(results):
            return json.dumps(results[step_index], ensure_ascii=False, indent=2)
        return f"步骤索引 {step_index} 超出范围（共 {len(results)} 步）。"

    registry.register(
        name="get_step_result",
        description="获取指定步骤的详细执行结果。-1 表示最后一步。",
        parameters={
            "type": "object",
            "properties": {
                "step_index": {
                    "type": "integer",
                    "description": "步骤索引（从0开始，-1表示最后一步）",
                    "default": -1,
                },
            },
        },
        handler=_get_step_result,
    )

    # ------------------------------------------------------------------
    # 5. analyze_serial_output — 分析串口输出
    # ------------------------------------------------------------------
    def _analyze_serial_output(keyword: str = "") -> str:
        serial_buf = registry.get_context("serial_buffer")
        if not serial_buf:
            return "串口缓冲区为空。"
        lines = serial_buf if isinstance(serial_buf, list) else [serial_buf]
        if keyword:
            lines = [l for l in lines if keyword.lower() in str(l).lower()]
        if not lines:
            return f"未找到包含 '{keyword}' 的串口输出。" if keyword else "串口无输出。"
        return "\n".join(str(l) for l in lines[-50:])

    registry.register(
        name="analyze_serial_output",
        description="获取并过滤串口输出内容。可按关键字筛选。",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "可选：筛选包含此关键字的行",
                    "default": "",
                },
            },
        },
        handler=_analyze_serial_output,
    )

    # ------------------------------------------------------------------
    # 6. resume_script — 恢复暂停的脚本
    # ------------------------------------------------------------------
    def _resume_script() -> str:
        resume_fn = registry.get_context("resume_callback")
        if resume_fn is None:
            return "无法恢复：未找到恢复回调（脚本可能未在暂停状态）。"
        try:
            resume_fn()
            return "已发送恢复信号，脚本将继续执行。"
        except Exception as e:
            return f"恢复失败: {e}"

    registry.register(
        name="resume_script",
        description="恢复当前暂停的脚本执行。仅在脚本处于暂停状态时有效。",
        parameters={"type": "object", "properties": {}},
        handler=_resume_script,
    )

    # ------------------------------------------------------------------
    # 7. stop_script — 停止脚本执行
    # ------------------------------------------------------------------
    def _stop_script() -> str:
        stop_fn = registry.get_context("stop_callback")
        if stop_fn is None:
            return "无法停止：未找到停止回调。"
        try:
            stop_fn()
            return "已发送停止信号。"
        except Exception as e:
            return f"停止失败: {e}"

    registry.register(
        name="stop_script",
        description="停止当前正在执行的脚本。此操作不可逆。",
        parameters={"type": "object", "properties": {}},
        handler=_stop_script,
    )

    # ------------------------------------------------------------------
    # 8. send_serial_command — 发送串口命令
    # ------------------------------------------------------------------
    def _send_serial_command(command: str) -> str:
        send_fn = registry.get_context("serial_send_callback")
        if send_fn is None:
            return "串口未连接或发送回调不可用。"
        try:
            send_fn(command)
            return f"已发送串口命令: {command}"
        except Exception as e:
            return f"串口发送失败: {e}"

    registry.register(
        name="send_serial_command",
        description="通过串口向设备发送命令。注意：这会直接影响设备状态。",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要发送的串口命令字符串",
                },
            },
            "required": ["command"],
        },
        handler=_send_serial_command,
    )


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表单例（含内置工具）。"""
    global _instance
    if _instance is None:
        _instance = ToolRegistry()
        _register_builtin_tools(_instance)
    return _instance
