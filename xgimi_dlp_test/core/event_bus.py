# -*- coding: utf-8 -*-
"""
事件总线模块

轻量级发布-订阅系统，用于解耦剧本执行器与 AI / 飞书通知模块。
所有事件在发布线程中同步执行，订阅者应避免长时间阻塞。
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# 预定义事件类型常量
class Events:
    """事件类型枚举。"""
    SCRIPT_STARTED = "script_started"
    SCRIPT_FINISHED = "script_finished"
    SCRIPT_PAUSED = "script_paused"

    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"

    CONDITION_CHECK_FAILED = "condition_check_failed"
    COMPARE_FAILED = "compare_failed"
    GREEN_SCREEN_DETECTED = "green_screen_detected"

    AI_NOTIFY_TRIGGERED = "ai_notify_triggered"


class EventBus:
    """
    进程内事件总线。

    - subscribe(event_type, callback) → 注册监听
    - unsubscribe(event_type, callback) → 取消监听
    - emit(event_type, **data) → 发布事件
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """
        订阅事件。

        Args:
            event_type: 事件类型（建议使用 Events 常量）
            callback:   回调函数，签名 callback(event_type: str, data: dict)
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logger.debug("订阅事件 [%s] → %s", event_type, callback.__name__)

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅。"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass

    def subscribe_all(self, callback: Callable):
        """订阅所有事件类型（通配监听）。"""
        self.subscribe("*", callback)

    def emit(self, event_type: str, **data):
        """
        发布事件。同步调用所有订阅者。

        Args:
            event_type: 事件类型
            **data:     事件携带的数据
        """
        with self._lock:
            listeners = list(self._subscribers.get(event_type, []))
            wildcard = list(self._subscribers.get("*", []))
        all_listeners = listeners + wildcard

        if not all_listeners:
            return

        logger.debug("发布事件 [%s], 订阅者: %d", event_type, len(all_listeners))

        for cb in all_listeners:
            try:
                cb(event_type, data)
            except Exception:
                logger.exception(
                    "事件 [%s] 订阅者 %s 执行异常", event_type, cb.__name__
                )

    def emit_async(self, event_type: str, **data):
        """
        在后台线程中发布事件（不阻塞调用方）。
        适合耗时操作（如 AI 分析、飞书发送）。
        """
        t = threading.Thread(
            target=self.emit,
            args=(event_type,),
            kwargs=data,
            daemon=True,
        )
        t.start()

    def clear(self):
        """清空所有订阅。"""
        with self._lock:
            self._subscribers.clear()


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线单例。"""
    global _instance
    if _instance is None:
        _instance = EventBus()
    return _instance
