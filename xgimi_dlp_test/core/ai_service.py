# -*- coding: utf-8 -*-
"""
AI 服务模块

封装通义千问（Qwen）API 调用，采用 OpenAI 兼容接口。
支持：普通对话、流式输出、Function Calling（tool_use）。
"""

import json
import logging
from typing import Any, Callable, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

# 默认配置
_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen-plus"
_DEFAULT_MAX_TOKENS = 2048
_DEFAULT_TEMPERATURE = 0.7


class AIServiceError(Exception):
    """AI 服务异常"""
    pass


class AIService:
    """
    通义千问 AI 服务封装。

    采用 OpenAI Python SDK 通过兼容接口调用阿里云百炼平台模型。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = None  # lazy init

    # ------------------------------------------------------------------
    # 配置
    # ------------------------------------------------------------------

    def configure(self, **kwargs):
        """动态更新配置，会重置客户端连接。"""
        for key in ("api_key", "base_url", "model", "max_tokens", "temperature"):
            if key in kwargs:
                setattr(self, f"_{key}", kwargs[key])
        self._client = None  # 下次调用时重建

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _get_client(self):
        """懒加载 OpenAI 客户端。"""
        if self._client is None:
            if not self._api_key:
                raise AIServiceError("AI API Key 未配置，请在设置中填写。")
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url=self._base_url,
                )
            except ImportError:
                raise AIServiceError(
                    "缺少 openai 库，请执行: pip install openai"
                )
        return self._client

    def _build_params(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[dict]] = None,
        **overrides,
    ) -> dict:
        """构建 API 请求参数。"""
        params: dict = {
            "model": overrides.pop("model", self._model),
            "messages": messages,
            "max_tokens": overrides.pop("max_tokens", self._max_tokens),
            "temperature": overrides.pop("temperature", self._temperature),
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = overrides.pop("tool_choice", "auto")
        params.update(overrides)
        return params

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[dict]] = None,
        **kwargs,
    ) -> dict:
        """
        同步对话（非流式）。

        Args:
            messages: OpenAI 格式消息列表 [{"role": "user", "content": "..."}]
            tools:    可选的工具定义列表（Function Calling）
            **kwargs: 覆盖 model / max_tokens / temperature 等

        Returns:
            完整的 response.choices[0].message 字典，包含：
            - role, content（文本回复）
            - tool_calls（如果 AI 决定调用工具）
        """
        client = self._get_client()
        params = self._build_params(messages, tools, **kwargs)

        try:
            response = client.chat.completions.create(**params)
            choice = response.choices[0]
            msg = choice.message
            result = {"role": msg.role, "content": msg.content or ""}
            if msg.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            return result
        except Exception as e:
            logger.error("AI chat 调用失败: %s", e)
            raise AIServiceError(f"AI 调用失败: {e}") from e

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[dict]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """
        流式对话。逐 chunk 回调，最终返回完整文本。

        Args:
            messages: 消息列表
            tools:    工具定义（流式下工具调用会合并后返回）
            on_chunk: 每个文本片段的回调 on_chunk(delta_text)
            **kwargs: 覆盖参数

        Returns:
            完整的回复文本
        """
        client = self._get_client()
        params = self._build_params(messages, tools, stream=True, **kwargs)

        try:
            stream = client.chat.completions.create(**params)
            full_text = ""
            tool_calls_parts: Dict[int, dict] = {}

            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # 文本流
                if delta.content:
                    full_text += delta.content
                    if on_chunk:
                        on_chunk(delta.content)

                # 工具调用流（合并分片）
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_parts:
                            tool_calls_parts[idx] = {
                                "id": tc.id or "",
                                "type": tc.type or "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        part = tool_calls_parts[idx]
                        if tc.id:
                            part["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                part["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                part["function"]["arguments"] += tc.function.arguments

            return full_text
        except Exception as e:
            logger.error("AI stream 调用失败: %s", e)
            raise AIServiceError(f"AI 流式调用失败: {e}") from e

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[dict],
        tool_handler: Callable[[str, dict], str],
        max_rounds: int = 5,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """
        带工具调用的完整 Agent 对话循环。

        自动处理 AI → 工具调用 → 工具结果 → AI 的多轮循环。

        Args:
            messages:     初始消息列表（会被修改追加）
            tools:        工具定义列表
            tool_handler: 工具执行函数 handler(name, arguments) -> result_str
            max_rounds:   最大循环轮数
            on_chunk:     流式文本回调

        Returns:
            最终的 AI 文本回复
        """
        for _ in range(max_rounds):
            response = self.chat(messages, tools=tools, **kwargs)

            # 有工具调用
            if "tool_calls" in response:
                # 追加 assistant 消息（含 tool_calls）
                messages.append(response)

                for tc in response["tool_calls"]:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        fn_args = {}

                    logger.info("Agent 调用工具: %s(%s)", fn_name, fn_args)
                    try:
                        result = tool_handler(fn_name, fn_args)
                    except Exception as e:
                        result = f"工具执行错误: {e}"
                        logger.error("工具 %s 执行失败: %s", fn_name, e)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result),
                    })
                continue  # 下一轮，让 AI 处理工具结果

            # 无工具调用 → 最终回复
            final_text = response.get("content", "")
            if on_chunk and final_text:
                on_chunk(final_text)
            return final_text

        return "[Agent 达到最大循环次数，已停止]"

    def test_connection(self) -> str:
        """
        测试 AI 服务连接。

        Returns:
            AI 的回复文本，或抛出 AIServiceError
        """
        result = self.chat([
            {"role": "user", "content": "请回复'连接成功'四个字。"}
        ], max_tokens=32)
        return result.get("content", "")


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取全局 AI 服务单例。"""
    global _instance
    if _instance is None:
        _instance = AIService()
    return _instance
