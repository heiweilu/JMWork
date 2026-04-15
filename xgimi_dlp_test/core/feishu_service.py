# -*- coding: utf-8 -*-
"""
飞书通知服务模块

支持两种接入方式：
1. Webhook 自定义机器人（零审核，快速接入）
2. Open API + lark-oapi SDK（完整功能，需创建应用）

消息格式支持：文本、富文本(post)、交互卡片(interactive)。
"""

import hashlib
import hmac
import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeishuServiceError(Exception):
    """飞书服务异常"""
    pass


# ======================================================================
# 消息模板
# ======================================================================

class FeishuTemplates:
    """预定义的飞书消息模板。"""

    @staticmethod
    def test_paused_card(
        title: str,
        step_name: str,
        reason: str,
        logs: str = "",
        issue_link: str = "",
        extra: str = "",
    ) -> dict:
        """测试暂停卡片模板。"""
        # 如果 reason 包含多行，拆分为首行概述 + 详情区块
        reason_lines = reason.split("\n") if reason else [""]
        brief_reason = reason_lines[0]
        detail_lines = reason_lines[1:]

        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**脚本名称：** {title}\n"
                        f"**暂停步骤：** {step_name}\n"
                        f"**暂停原因：** {brief_reason}"
                    ),
                },
            },
        ]

        # 结构化详情区块（如条件检查的模式/期望值/实际结果）
        if detail_lines:
            detail_content = "\n".join(detail_lines)
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📋 **检查详情**\n{detail_content}",
                },
            })

        if logs:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**最近日志：**\n```\n{logs[-1000:]}\n```",
                },
            })

        if issue_link:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📎 [查看飞书问题单]({issue_link})",
                },
            })

        if extra:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": extra},
            })

        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"DLP 自动化测试系统 · {time.strftime('%Y-%m-%d %H:%M:%S')}",
                }
            ],
        })

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "⚠️ 测试暂停通知"},
                    "template": "orange",
                },
                "elements": elements,
            },
        }

    @staticmethod
    def test_completed_card(
        title: str,
        status: str,
        duration: str = "",
        summary: str = "",
    ) -> dict:
        """测试完成卡片模板。"""
        template = "green" if status == "成功" else "red"
        emoji = "✅" if status == "成功" else "❌"
        content = f"**脚本名称：** {title}\n**执行结果：** {emoji} {status}"
        if duration:
            content += f"\n**执行耗时：** {duration}"
        if summary:
            content += f"\n**摘要：** {summary}"

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"{emoji} 测试完成通知"},
                    "template": template,
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": content}},
                    {
                        "tag": "note",
                        "elements": [{
                            "tag": "plain_text",
                            "content": f"DLP 自动化测试系统 · {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        }],
                    },
                ],
            },
        }

    @staticmethod
    def simple_text(text: str) -> dict:
        """纯文本消息。"""
        return {"msg_type": "text", "content": {"text": text}}

    @staticmethod
    def rich_text(title: str, content_lines: List[List[dict]]) -> dict:
        """
        富文本消息。

        content_lines 示例:
        [
            [{"tag": "text", "text": "项目已更新: "},
             {"tag": "a", "text": "查看", "href": "https://..."}],
        ]
        """
        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content_lines,
                    }
                }
            },
        }


# ======================================================================
# 飞书服务
# ======================================================================

class FeishuService:
    """
    飞书消息发送服务。

    同时支持 Webhook 和 Open API 两种模式。
    """

    def __init__(
        self,
        webhook_url: str = "",
        webhook_secret: str = "",
        app_id: str = "",
        app_secret: str = "",
        default_chat_id: str = "",
    ):
        self._webhook_url = webhook_url
        self._webhook_secret = webhook_secret
        self._app_id = app_id
        self._app_secret = app_secret
        self._default_chat_id = default_chat_id
        self._lark_client = None  # lazy init

    # ------------------------------------------------------------------
    # 配置
    # ------------------------------------------------------------------

    def configure(self, **kwargs):
        """动态更新配置。"""
        for key in ("webhook_url", "webhook_secret", "app_id", "app_secret", "default_chat_id"):
            if key in kwargs:
                setattr(self, f"_{key}", kwargs[key])
        self._lark_client = None

    @property
    def webhook_configured(self) -> bool:
        return bool(self._webhook_url)

    @property
    def openapi_configured(self) -> bool:
        return bool(self._app_id and self._app_secret)

    # ------------------------------------------------------------------
    # Webhook 模式
    # ------------------------------------------------------------------

    def _gen_webhook_sign(self, timestamp: str) -> str:
        """生成 Webhook 签名（HmacSHA256）。"""
        string_to_sign = f"{timestamp}\n{self._webhook_secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    def send_webhook(self, payload: dict) -> dict:
        """
        通过 Webhook 发送消息。

        Args:
            payload: 消息体（msg_type + content/card）

        Returns:
            飞书返回的 JSON 响应
        """
        if not self._webhook_url:
            raise FeishuServiceError("Webhook URL 未配置。")

        import requests

        data = dict(payload)

        # 签名
        if self._webhook_secret:
            timestamp = str(int(time.time()))
            data["timestamp"] = timestamp
            data["sign"] = self._gen_webhook_sign(timestamp)

        try:
            resp = requests.post(
                self._webhook_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("code", 0) != 0:
                err_msg = result.get("msg", "未知错误")
                logger.warning("飞书 Webhook 返回错误: %s", err_msg)
                raise FeishuServiceError(f"飞书返回错误: {err_msg}")
            logger.info("飞书 Webhook 消息发送成功")
            return result
        except requests.RequestException as e:
            logger.error("飞书 Webhook 请求失败: %s", e)
            raise FeishuServiceError(f"飞书请求失败: {e}") from e

    # ------------------------------------------------------------------
    # Open API 模式
    # ------------------------------------------------------------------

    def _get_lark_client(self):
        """懒加载 lark-oapi 客户端。"""
        if self._lark_client is None:
            if not self._app_id or not self._app_secret:
                raise FeishuServiceError("飞书 App ID / Secret 未配置。")
            try:
                import lark_oapi as lark
                self._lark_client = lark.Client.builder() \
                    .app_id(self._app_id) \
                    .app_secret(self._app_secret) \
                    .build()
            except ImportError:
                raise FeishuServiceError(
                    "缺少 lark-oapi 库，请执行: pip install lark-oapi"
                )
        return self._lark_client

    def send_openapi(
        self,
        msg_type: str,
        content: dict,
        chat_id: str = "",
        receive_id_type: str = "chat_id",
    ) -> dict:
        """
        通过 Open API 发送消息。

        Args:
            msg_type:        消息类型（text/post/interactive 等）
            content:         消息内容
            chat_id:         目标群组 ID（留空使用默认）
            receive_id_type: 接收者类型（chat_id/open_id/user_id/union_id/email）

        Returns:
            API 响应
        """
        target_id = chat_id or self._default_chat_id
        if not target_id:
            raise FeishuServiceError("目标群组 chat_id 未配置。")

        try:
            import lark_oapi as lark
            from lark_oapi.api.im.v1 import (
                CreateMessageRequest,
                CreateMessageRequestBody,
            )

            client = self._get_lark_client()

            body = CreateMessageRequestBody.builder() \
                .receive_id(target_id) \
                .msg_type(msg_type) \
                .content(json.dumps(content, ensure_ascii=False)) \
                .build()

            request = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(body) \
                .build()

            response = client.im.v1.message.create(request)

            if not response.success():
                err = f"code={response.code}, msg={response.msg}"
                logger.warning("飞书 Open API 错误: %s", err)
                raise FeishuServiceError(f"飞书 API 错误: {err}")

            logger.info("飞书 Open API 消息发送成功")
            return {"code": 0, "msg": "success"}

        except ImportError:
            raise FeishuServiceError("缺少 lark-oapi 库，请执行: pip install lark-oapi")
        except FeishuServiceError:
            raise
        except Exception as e:
            logger.error("飞书 Open API 调用失败: %s", e)
            raise FeishuServiceError(f"飞书 API 调用失败: {e}") from e

    # ------------------------------------------------------------------
    # 统一发送接口
    # ------------------------------------------------------------------

    def send(self, payload: dict, prefer: str = "webhook") -> dict:
        """
        统一发送接口。优先使用指定模式，不可用时尝试另一种。

        Args:
            payload: FeishuTemplates 生成的消息体
            prefer:  优先模式 "webhook" 或 "openapi"

        Returns:
            发送结果
        """
        if prefer == "webhook" and self.webhook_configured:
            return self.send_webhook(payload)
        elif prefer == "openapi" and self.openapi_configured:
            return self._send_via_openapi(payload)
        elif self.webhook_configured:
            return self.send_webhook(payload)
        elif self.openapi_configured:
            return self._send_via_openapi(payload)
        else:
            raise FeishuServiceError("飞书未配置。请先配置 Webhook URL 或 Open API 凭证。")

    def _send_via_openapi(self, payload: dict) -> dict:
        """将模板 payload 转换为 Open API 调用。"""
        msg_type = payload.get("msg_type", "text")
        if msg_type == "interactive":
            content = payload.get("card", {})
        elif msg_type == "post":
            content = payload.get("content", {}).get("post", {})
        else:
            content = payload.get("content", {})
        return self.send_openapi(msg_type, content)

    # ------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------

    def send_text(self, text: str, **kwargs) -> dict:
        """发送纯文本消息。"""
        return self.send(FeishuTemplates.simple_text(text), **kwargs)

    def send_test_paused(self, **template_kwargs) -> dict:
        """发送测试暂停通知。"""
        payload = FeishuTemplates.test_paused_card(**template_kwargs)
        return self.send(payload)

    def send_test_completed(self, **template_kwargs) -> dict:
        """发送测试完成通知。"""
        payload = FeishuTemplates.test_completed_card(**template_kwargs)
        return self.send(payload)

    # ------------------------------------------------------------------
    # 文件上传 (仅 Open API)
    # ------------------------------------------------------------------

    def upload_file(self, file_path: str, file_type: str = "stream") -> str:
        """
        通过 Open API 上传文件到飞书。

        Args:
            file_path:  本地文件路径
            file_type:  飞书文件类型 ("opus"/"mp4"/"pdf"/"doc"/"xls"/"ppt"/"stream"/"image")
                        - image: 图片（png/jpg/gif/bmp/webp）
                        - stream: 通用文件（txt/csv/zip 等）

        Returns:
            file_key: 文件标识符，用于后续发送消息
        """
        import os
        if not os.path.isfile(file_path):
            raise FeishuServiceError(f"文件不存在: {file_path}")

        if not self.openapi_configured:
            raise FeishuServiceError(
                "文件上传仅支持 Open API 模式，请先配置 App ID / App Secret。"
            )

        try:
            import lark_oapi as lark
            from lark_oapi.api.im.v1 import (
                CreateFileRequest,
                CreateFileRequestBody,
            )

            client = self._get_lark_client()

            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                body = CreateFileRequestBody.builder() \
                    .file_type(file_type) \
                    .file_name(file_name) \
                    .file(f) \
                    .build()

                request = CreateFileRequest.builder() \
                    .request_body(body) \
                    .build()

                response = client.im.v1.file.create(request)

            if not response.success():
                raise FeishuServiceError(
                    f"文件上传失败: code={response.code}, msg={response.msg}"
                )

            file_key = response.data.file_key
            logger.info("文件上传成功: %s → file_key=%s", file_name, file_key)
            return file_key

        except ImportError:
            raise FeishuServiceError("缺少 lark-oapi 库，请执行: pip install lark-oapi")
        except FeishuServiceError:
            raise
        except Exception as e:
            logger.error("文件上传失败: %s", e)
            raise FeishuServiceError(f"文件上传失败: {e}") from e

    def upload_image(self, image_path: str) -> str:
        """
        上传图片到飞书（返回 image_key）。

        Args:
            image_path: 本地图片路径（png/jpg/gif/bmp/webp）

        Returns:
            image_key: 图片标识符
        """
        import os
        if not os.path.isfile(image_path):
            raise FeishuServiceError(f"图片不存在: {image_path}")

        if not self.openapi_configured:
            raise FeishuServiceError(
                "图片上传仅支持 Open API 模式，请先配置 App ID / App Secret。"
            )

        try:
            import lark_oapi as lark
            from lark_oapi.api.im.v1 import (
                CreateImageRequest,
                CreateImageRequestBody,
            )

            client = self._get_lark_client()

            with open(image_path, "rb") as f:
                body = CreateImageRequestBody.builder() \
                    .image_type("message") \
                    .image(f) \
                    .build()

                request = CreateImageRequest.builder() \
                    .request_body(body) \
                    .build()

                response = client.im.v1.image.create(request)

            if not response.success():
                raise FeishuServiceError(
                    f"图片上传失败: code={response.code}, msg={response.msg}"
                )

            image_key = response.data.image_key
            logger.info("图片上传成功: %s → image_key=%s",
                        os.path.basename(image_path), image_key)
            return image_key

        except ImportError:
            raise FeishuServiceError("缺少 lark-oapi 库，请执行: pip install lark-oapi")
        except FeishuServiceError:
            raise
        except Exception as e:
            logger.error("图片上传失败: %s", e)
            raise FeishuServiceError(f"图片上传失败: {e}") from e

    def send_file_message(self, file_path: str, chat_id: str = "") -> dict:
        """
        上传文件并发送文件消息到群。

        Args:
            file_path: 本地文件路径
            chat_id:   目标群 ID（留空使用默认）

        Returns:
            发送结果
        """
        import os
        ext = os.path.splitext(file_path)[1].lower()
        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

        if ext in image_exts:
            image_key = self.upload_image(file_path)
            content = {"image_key": image_key}
            return self.send_openapi("image", content, chat_id=chat_id)
        else:
            file_key = self.upload_file(file_path)
            content = {"file_key": file_key}
            return self.send_openapi("file", content, chat_id=chat_id)

    def send_files_batch(
        self,
        file_paths: List[str],
        description: str = "",
        chat_id: str = "",
    ) -> List[dict]:
        """
        批量上传并发送多个文件。

        如果有描述文本，先发送文本消息，再逐个发送文件。

        Args:
            file_paths:  文件路径列表
            description: 可选的说明文本
            chat_id:     目标群 ID

        Returns:
            每个文件发送的结果列表
        """
        results = []

        if description:
            try:
                self.send_openapi("text", {"text": description}, chat_id=chat_id)
            except Exception as e:
                logger.warning("发送描述文本失败: %s", e)

        for fp in file_paths:
            try:
                result = self.send_file_message(fp, chat_id=chat_id)
                results.append({"file": fp, "status": "success", "result": result})
            except Exception as e:
                logger.error("发送文件 %s 失败: %s", fp, e)
                results.append({"file": fp, "status": "failed", "error": str(e)})

        return results

    def test_connection(self) -> str:
        """
        测试飞书连接。

        Returns:
            "success" 或抛出 FeishuServiceError
        """
        self.send_text("🔔 DLP 自动化测试系统连接测试 — 此消息表明配置正确。")
        return "success"


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_instance: Optional[FeishuService] = None


def get_feishu_service() -> FeishuService:
    """获取全局飞书服务单例。"""
    global _instance
    if _instance is None:
        _instance = FeishuService()
    return _instance
