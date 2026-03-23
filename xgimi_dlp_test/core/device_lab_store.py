# -*- coding: utf-8 -*-
"""设备联调台的数据持久化。"""

import copy
import json
import os
import uuid
from typing import Any, Dict, List, Optional


def _make_step(
    step_type: str,
    *,
    target: str = "",
    command: str = "",
    seconds: float = 0.0,
    repeat: int = 1,
    delay_ms: int = 250,
    note: str = "",
    reference_image: str = "",
    threshold: float = 0.72,
    pause_on_fail: bool = True,
    capture_count: int = 1,
    capture_interval_ms: int = 1000,
    retry_count: int = 0,
    retry_interval_ms: int = 1000,
    condition: str = "",
    variable_name: str = "",
    variable_value: str = "",
    result_variable: str = "",
    recovery_target: str = "",
    reference_category: str = "default",
    roi_text: str = "",
    green_ratio_threshold: float = 0.35,
    green_area_threshold: float = 0.18,
    green_margin: int = 35,
    green_saturation_threshold: int = 70,
    green_value_threshold: int = 60,
    green_check_frames: int = 3,
    green_check_interval_ms: int = 250,
    reference_dir: str = "",
    reference_pool_size: int = 5,
    save_diff_heatmap: bool = True,
) -> Dict[str, Any]:
    return {
        "id": f"step-{uuid.uuid4().hex[:8]}",
        "type": step_type,
        "target": target,
        "command": command,
        "seconds": seconds,
        "repeat": repeat,
        "delay_ms": delay_ms,
        "note": note,
        "reference_image": reference_image,
        "threshold": threshold,
        "pause_on_fail": pause_on_fail,
        "capture_count": capture_count,
        "capture_interval_ms": capture_interval_ms,
        "retry_count": retry_count,
        "retry_interval_ms": retry_interval_ms,
        "condition": condition,
        "variable_name": variable_name,
        "variable_value": variable_value,
        "result_variable": result_variable,
        "recovery_target": recovery_target,
        "reference_category": reference_category,
        "roi_text": roi_text,
        "green_ratio_threshold": green_ratio_threshold,
        "green_area_threshold": green_area_threshold,
        "green_margin": green_margin,
        "green_saturation_threshold": green_saturation_threshold,
        "green_value_threshold": green_value_threshold,
        "green_check_frames": green_check_frames,
        "green_check_interval_ms": green_check_interval_ms,
        "reference_dir": reference_dir,
        "reference_pool_size": reference_pool_size,
        "save_diff_heatmap": save_diff_heatmap,
    }


def _make_script(
    script_id: str,
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    *,
    run_count: int = 1,
    cycle_interval_ms: int = 0,
    stop_on_fail: bool = True,
) -> Dict[str, Any]:
    return {
        "id": script_id,
        "name": name,
        "description": description,
        "steps": steps,
        "run_count": run_count,
        "cycle_interval_ms": cycle_interval_ms,
        "stop_on_fail": stop_on_fail,
    }


DEFAULT_QUICK_SETTINGS = [
    {
        "id": "setting-close-ak-shift",
        "name": "关闭位移AK",
        "description": "关闭位移触发 AK，适合做稳定性联调前的基线配置。",
        "commands": ["setprop persist.sys.acc.trigger.ak 0"],
    },
    {
        "id": "setting-open-ak-shift",
        "name": "打开位移AK",
        "description": "恢复位移触发 AK。",
        "commands": ["setprop persist.sys.acc.trigger.ak 1"],
    },
    {
        "id": "setting-close-ak-boot",
        "name": "关闭开机AK",
        "description": "关闭开机 AK。",
        "commands": ["setprop persist.sys.poweron.ak 0"],
    },
    {
        "id": "setting-open-ak-boot",
        "name": "打开开机AK",
        "description": "恢复开机 AK。",
        "commands": ["setprop persist.sys.poweron.ak 1"],
    },
    {
        "id": "setting-open-remote-pair",
        "name": "开放遥控器配对",
        "description": "沿用 Cattle 的煲机配置项。",
        "commands": ["setprop persist.sys.btrrsi -65"],
    },
    {
        "id": "setting-close-remote-pair",
        "name": "屏蔽遥控器配对",
        "description": "限制配对入口，方便封闭场景测试。",
        "commands": ["setprop persist.sys.btrrsi -21"],
    },
    {
        "id": "setting-open-log-cn",
        "name": "国内通用日志指令",
        "description": "批量打开核心日志开关。",
        "commands": [
            "su",
            "setprop persist.xgimilog.data true",
            "setprop persist.sys.xgimi.log true",
            "setprop persist.vendor.xgimi.logserver 1",
            "setprop persist.xgimilog.buffersize 102400",
            "setprop persist.xgimilog.buffernumber 30",
            "setprop persist.sys.xgimi.kernellog true",
            "setprop persist.sys.bt.debug 1",
            "setprop persist.sys.bt.ble.testmode.enabled true",
            "setprop persist.bluetooth.xgimi.log 5",
            "setprop persist.xgimilog.maxbootcount 50",
        ],
    },
]

DEFAULT_SHORTCUTS = [
    {
        "id": "shortcut-up",
        "name": "上键",
        "description": "遥控方向上。",
        "commands": ["input keyevent 19"],
    },
    {
        "id": "shortcut-down",
        "name": "下键",
        "description": "遥控方向下。",
        "commands": ["input keyevent 20"],
    },
    {
        "id": "shortcut-left",
        "name": "左键",
        "description": "遥控方向左。",
        "commands": ["input keyevent 21"],
    },
    {
        "id": "shortcut-right",
        "name": "右键",
        "description": "遥控方向右。",
        "commands": ["input keyevent 22"],
    },
    {
        "id": "shortcut-ok",
        "name": "OK键",
        "description": "遥控确认。",
        "commands": ["input keyevent 23"],
    },
    {
        "id": "shortcut-power",
        "name": "电源键",
        "description": "投影仪电源键。",
        "commands": ["input keyevent KEYCODE_KPPOWER"],
    },
    {
        "id": "shortcut-home",
        "name": "主页键",
        "description": "回到桌面。",
        "commands": ["input keyevent 3"],
    },
    {
        "id": "shortcut-menu",
        "name": "菜单键",
        "description": "打开菜单。",
        "commands": ["input keyevent 82"],
    },
    {
        "id": "shortcut-back",
        "name": "返回键",
        "description": "返回上一级。",
        "commands": ["input keyevent 4"],
    },
    {
        "id": "shortcut-setting",
        "name": "设置键",
        "description": "打开设置。",
        "commands": ["input keyevent 122"],
    },
    {
        "id": "shortcut-sleep",
        "name": "休眠键",
        "description": "发送休眠键值，用于待机相关验证。",
        "commands": ["input keyevent 223"],
    },
    {
        "id": "shortcut-volume-up",
        "name": "音量+",
        "description": "调高音量。",
        "commands": ["input keyevent 24"],
    },
    {
        "id": "shortcut-volume-down",
        "name": "音量-",
        "description": "调低音量。",
        "commands": ["input keyevent 25"],
    },
    {
        "id": "shortcut-pair-open",
        "name": "开放遥控器配对",
        "description": "配对调试快捷入口。",
        "commands": ["setprop persist.sys.btrrsi -65"],
    },
    {
        "id": "shortcut-take-photo",
        "name": "抓拍保存",
        "description": "直接抓拍当前相机画面并保存到设备联调目录。",
        "commands": [],
        "action_type": "camera_snapshot",
        "capture_count": 1,
        "capture_interval_ms": 1000,
    },
    {
        "id": "shortcut-append-reference",
        "name": "当前帧加入图库",
        "description": "把当前拍摄画面归档到指定参考分类目录。",
        "commands": [],
        "action_type": "append_reference",
        "reference_category": "default",
        "reference_dir": "",
        "reference_pool_size": 5,
    },
    {
        "id": "shortcut-check-reference",
        "name": "检查指定正常照片",
        "description": "先保存当前画面，再按参考图库自动检图；不通过时会中止后续队列。",
        "commands": [],
        "action_type": "compare_reference",
        "capture_count": 1,
        "capture_interval_ms": 1000,
        "reference_category": "default",
        "reference_dir": "",
        "reference_pool_size": 5,
        "save_diff_heatmap": True,
        "roi_text": "",
    },
    {
        "id": "shortcut-detect-green-screen",
        "name": "绿屏检测",
        "description": "连续取样当前画面，命中大面积绿屏后立即判定异常。",
        "commands": [],
        "action_type": "green_screen_detect",
        "roi_text": "",
        "green_ratio_threshold": 0.35,
        "green_area_threshold": 0.18,
        "green_margin": 35,
        "green_saturation_threshold": 70,
        "green_value_threshold": 60,
        "green_check_frames": 3,
        "green_check_interval_ms": 250,
        "save_diff_heatmap": True,
    },
]

DEFAULT_REMOTE_BUTTONS = [
    {"id": "remote-power", "name": "电源", "binding_type": "shortcut", "binding_value": "电源键", "x": 112, "y": 24, "w": 76, "h": 34},
    {"id": "remote-home", "name": "主页", "binding_type": "shortcut", "binding_value": "主页键", "x": 42, "y": 82, "w": 76, "h": 34},
    {"id": "remote-menu", "name": "菜单", "binding_type": "shortcut", "binding_value": "菜单键", "x": 182, "y": 82, "w": 76, "h": 34},
    {"id": "remote-up", "name": "上", "binding_type": "shortcut", "binding_value": "上键", "x": 112, "y": 144, "w": 76, "h": 40},
    {"id": "remote-left", "name": "左", "binding_type": "shortcut", "binding_value": "左键", "x": 42, "y": 196, "w": 76, "h": 40},
    {"id": "remote-ok", "name": "确定", "binding_type": "shortcut", "binding_value": "OK键", "x": 112, "y": 196, "w": 76, "h": 40},
    {"id": "remote-right", "name": "右", "binding_type": "shortcut", "binding_value": "右键", "x": 182, "y": 196, "w": 76, "h": 40},
    {"id": "remote-down", "name": "下", "binding_type": "shortcut", "binding_value": "下键", "x": 112, "y": 248, "w": 76, "h": 40},
    {"id": "remote-back", "name": "返回", "binding_type": "shortcut", "binding_value": "返回键", "x": 42, "y": 318, "w": 76, "h": 34},
    {"id": "remote-setting", "name": "设置", "binding_type": "shortcut", "binding_value": "设置键", "x": 182, "y": 318, "w": 76, "h": 34},
    {"id": "remote-vol-up", "name": "音量+", "binding_type": "shortcut", "binding_value": "音量+", "x": 42, "y": 386, "w": 76, "h": 34},
    {"id": "remote-vol-down", "name": "音量-", "binding_type": "shortcut", "binding_value": "音量-", "x": 182, "y": 386, "w": 76, "h": 34},
    {"id": "remote-sleep", "name": "休眠", "binding_type": "shortcut", "binding_value": "休眠键", "x": 42, "y": 438, "w": 76, "h": 34},
    {"id": "remote-photo", "name": "抓拍", "binding_type": "shortcut", "binding_value": "抓拍保存", "x": 112, "y": 438, "w": 76, "h": 34},
    {"id": "remote-check-reference", "name": "检图", "binding_type": "shortcut", "binding_value": "检查指定正常照片", "x": 182, "y": 438, "w": 76, "h": 34},
]

DEFAULT_PROJECTS = [
    {
        "id": "project-athena-9681",
        "name": "9681雅典娜",
        "description": "默认联调项目示例。",
        "scripts": [
            _make_script(
                "script-athena-boot",
                "开机联调基线",
                "先打开日志，再开放配对，最后回到桌面。",
                [
                    _make_step("setting", target="国内通用日志指令", note="批量打开日志，方便后续排障。"),
                    _make_step("wait", seconds=1.0, note="等待系统把日志属性落地。"),
                    _make_step("setting", target="开放遥控器配对", note="联调默认开放蓝牙配对。"),
                    _make_step("shortcut", target="主页键", repeat=1, delay_ms=400, note="回到桌面确认设备可响应。"),
                    _make_step("capture_snapshot", note="抓一张当前桌面图，留作联调记录。"),
                ],
                run_count=1,
                cycle_interval_ms=0,
                stop_on_fail=True,
            )
        ],
    }
]

DEFAULT_PROFILE = {
    "camera": {
        "last_index": 0,
        "scan_max_index": 5,
        "preview_interval_ms": 33,
        "preview_zoom_percent": 100,
        "reference_dir": "reports/device_lab_references",
        "reference_pool_size": 5,
        "compare_threshold": 0.72,
        "reference_accept_threshold": 0.82,
        "reference_category": "default",
        "compare_roi": "",
        "save_diff_heatmap": True,
        "green_ratio_threshold": 0.35,
        "green_area_threshold": 0.18,
        "green_margin": 35,
        "green_saturation_threshold": 70,
        "green_value_threshold": 60,
        "green_check_frames": 3,
        "green_check_interval_ms": 250,
        "auto_reference_enabled": False,
        "auto_reference_interval_ms": 5000,
        "auto_reference_max_retry": 3,
        "snapshot_dir": "reports/device_lab_snapshots",
    },
    "serial": {
        "last_port": "",
        "baudrate": 115200,
        "newline": True,
        "newline_mode": "\\r\\n",
        "auto_su": False,
        "tab_passthrough": False,
    },
    "quick_settings": DEFAULT_QUICK_SETTINGS,
    "shortcuts": DEFAULT_SHORTCUTS,
    "remote": {
        "edit_mode": False,
        "buttons": DEFAULT_REMOTE_BUTTONS,
    },
    "ui_state": {
        "last_project_id": "",
        "last_script_id": "",
        "last_step_id": "",
    },
    "projects": DEFAULT_PROJECTS,
}


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def _ensure_default_items(target: List[Dict[str, Any]], defaults: List[Dict[str, Any]]):
    existing_ids = {item.get("id") for item in target}
    for default in defaults:
        if default.get("id") not in existing_ids:
            target.append(copy.deepcopy(default))


class DeviceLabStore:
    """设备联调台配置存储。"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
            )
        self._config_dir = config_dir
        self._profile_path = os.path.join(config_dir, "device_lab_profile.json")
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        self._data = copy.deepcopy(DEFAULT_PROFILE)
        if os.path.exists(self._profile_path):
            try:
                with open(self._profile_path, "r", encoding="utf-8") as file:
                    user_data = json.load(file)
                _merge_dict(self._data, user_data)
            except (OSError, json.JSONDecodeError):
                pass
        self._ensure_schema()
        return self.get_all()

    def save(self):
        os.makedirs(self._config_dir, exist_ok=True)
        with open(self._profile_path, "w", encoding="utf-8") as file:
            json.dump(self._data, file, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        current = self._data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return copy.deepcopy(current)

    def set(self, key: str, value: Any):
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = copy.deepcopy(value)

    def get_all(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def set_all(self, data: Dict[str, Any]):
        self._data = copy.deepcopy(data)
        self._ensure_schema()

    def resolve_path(self, relative_or_absolute: str, project_root: str) -> str:
        if os.path.isabs(relative_or_absolute):
            return relative_or_absolute
        return os.path.join(project_root, relative_or_absolute)

    def make_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def _ensure_schema(self):
        camera = self._data.setdefault("camera", {})
        camera.setdefault("reference_dir", "reports/device_lab_references")
        camera.setdefault("reference_pool_size", 5)
        camera.setdefault("compare_threshold", 0.72)
        camera.setdefault("reference_accept_threshold", 0.82)
        camera.setdefault("reference_category", "default")
        camera.setdefault("compare_roi", "")
        camera.setdefault("save_diff_heatmap", True)
        camera.setdefault("green_ratio_threshold", 0.35)
        camera.setdefault("green_area_threshold", 0.18)
        camera.setdefault("green_margin", 35)
        camera.setdefault("green_saturation_threshold", 70)
        camera.setdefault("green_value_threshold", 60)
        camera.setdefault("green_check_frames", 3)
        camera.setdefault("green_check_interval_ms", 250)
        camera.setdefault("auto_reference_enabled", False)
        camera.setdefault("auto_reference_interval_ms", 5000)
        camera.setdefault("auto_reference_max_retry", 3)

        quick_settings = self._data.setdefault("quick_settings", [])
        _ensure_default_items(quick_settings, DEFAULT_QUICK_SETTINGS)
        for item in quick_settings:
            item.setdefault("id", self.make_id("setting"))
            item.setdefault("description", "")
            item.setdefault("commands", [])

        shortcuts = self._data.setdefault("shortcuts", [])
        _ensure_default_items(shortcuts, DEFAULT_SHORTCUTS)
        for item in shortcuts:
            item.setdefault("id", self.make_id("shortcut"))
            item.setdefault("description", "")
            item.setdefault("commands", [])
            item.setdefault("action_type", "serial_bundle")
            item.setdefault("capture_count", 1)
            item.setdefault("capture_interval_ms", 1000)
            item.setdefault("reference_category", "default")
            item.setdefault("roi_text", "")
            item.setdefault("green_ratio_threshold", 0.35)
            item.setdefault("green_area_threshold", 0.18)
            item.setdefault("green_margin", 35)
            item.setdefault("green_saturation_threshold", 70)
            item.setdefault("green_value_threshold", 60)
            item.setdefault("green_check_frames", 3)
            item.setdefault("green_check_interval_ms", 250)
            item.setdefault("reference_dir", "")
            item.setdefault("reference_pool_size", 5)
            item.setdefault("save_diff_heatmap", True)
        remote = self._data.setdefault("remote", {})
        remote.setdefault("edit_mode", False)
        buttons = remote.setdefault("buttons", [])
        _ensure_default_items(buttons, DEFAULT_REMOTE_BUTTONS)
        for button in buttons:
            button.setdefault("id", self.make_id("remote"))
            button.setdefault("binding_type", "serial")
            button.setdefault("binding_value", "")
            button.setdefault("x", 80)
            button.setdefault("y", 80)
            button.setdefault("w", 76)
            button.setdefault("h", 34)
        ui_state = self._data.setdefault("ui_state", {})
        ui_state.setdefault("last_project_id", "")
        ui_state.setdefault("last_script_id", "")
        ui_state.setdefault("last_step_id", "")
        projects: List[Dict[str, Any]] = self._data.setdefault("projects", [])
        for project in projects:
            project.setdefault("id", self.make_id("project"))
            project.setdefault("description", "")
            scripts = project.setdefault("scripts", [])
            for script in scripts:
                script.setdefault("id", self.make_id("script"))
                script.setdefault("description", "")
                script.setdefault("steps", [])
                script.setdefault("run_count", 1)
                script.setdefault("cycle_interval_ms", 0)
                script.setdefault("stop_on_fail", True)
                normalized_steps: List[Dict[str, Any]] = []
                for raw_step in script.get("steps", []):
                    if isinstance(raw_step, dict):
                        step = copy.deepcopy(raw_step)
                    else:
                        text = str(raw_step).strip()
                        if text.startswith("wait:"):
                            try:
                                seconds = float(text.split(":", 1)[1].strip())
                            except ValueError:
                                seconds = 0.5
                            step = _make_step("wait", seconds=seconds)
                        elif text.startswith("setting:"):
                            step = _make_step("setting", target=text.split(":", 1)[1].strip())
                        elif text.startswith("shortcut:"):
                            step = _make_step("shortcut", target=text.split(":", 1)[1].strip())
                        else:
                            step = _make_step("serial", command=text)
                    step.setdefault("id", self.make_id("step"))
                    step.setdefault("type", "serial")
                    step.setdefault("target", "")
                    step.setdefault("command", "")
                    step.setdefault("seconds", 0.0)
                    step.setdefault("repeat", 1)
                    step.setdefault("delay_ms", 250)
                    step.setdefault("note", "")
                    step.setdefault("reference_image", "")
                    step.setdefault("threshold", 0.72)
                    step.setdefault("pause_on_fail", True)
                    step.setdefault("capture_count", 1)
                    step.setdefault("capture_interval_ms", 1000)
                    step.setdefault("retry_count", 0)
                    step.setdefault("retry_interval_ms", 1000)
                    step.setdefault("condition", "")
                    step.setdefault("variable_name", "")
                    step.setdefault("variable_value", "")
                    step.setdefault("result_variable", "")
                    step.setdefault("recovery_target", "")
                    step.setdefault("reference_category", "default")
                    step.setdefault("roi_text", "")
                    step.setdefault("green_ratio_threshold", 0.35)
                    step.setdefault("green_area_threshold", 0.18)
                    step.setdefault("green_margin", 35)
                    step.setdefault("green_saturation_threshold", 70)
                    step.setdefault("green_value_threshold", 60)
                    step.setdefault("green_check_frames", 3)
                    step.setdefault("green_check_interval_ms", 250)
                    step.setdefault("reference_dir", "")
                    step.setdefault("reference_pool_size", 5)
                    step.setdefault("save_diff_heatmap", True)
                    normalized_steps.append(step)
                script["steps"] = normalized_steps