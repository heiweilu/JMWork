# -*- coding: utf-8 -*-
"""设备联调台的数据持久化。"""

import copy
import json
import os
import uuid
from typing import Any, Dict, List, Optional


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
]

DEFAULT_REMOTE_BUTTONS = [
    {"id": "remote-power", "name": "电源", "binding_type": "shortcut", "binding_value": "电源键", "x": 112, "y": 24, "w": 76, "h": 34},
    {"id": "remote-home", "name": "主页", "binding_type": "shortcut", "binding_value": "主页键", "x": 42, "y": 82, "w": 76, "h": 34},
    {"id": "remote-menu", "name": "菜单", "binding_type": "shortcut", "binding_value": "菜单键", "x": 182, "y": 82, "w": 76, "h": 34},
    {"id": "remote-up", "name": "上", "binding_type": "serial", "binding_value": "input keyevent 19", "x": 112, "y": 144, "w": 76, "h": 40},
    {"id": "remote-left", "name": "左", "binding_type": "serial", "binding_value": "input keyevent 21", "x": 42, "y": 196, "w": 76, "h": 40},
    {"id": "remote-ok", "name": "确定", "binding_type": "serial", "binding_value": "input keyevent 23", "x": 112, "y": 196, "w": 76, "h": 40},
    {"id": "remote-right", "name": "右", "binding_type": "serial", "binding_value": "input keyevent 22", "x": 182, "y": 196, "w": 76, "h": 40},
    {"id": "remote-down", "name": "下", "binding_type": "serial", "binding_value": "input keyevent 20", "x": 112, "y": 248, "w": 76, "h": 40},
    {"id": "remote-back", "name": "返回", "binding_type": "shortcut", "binding_value": "返回键", "x": 42, "y": 318, "w": 76, "h": 34},
    {"id": "remote-setting", "name": "设置", "binding_type": "shortcut", "binding_value": "设置键", "x": 182, "y": 318, "w": 76, "h": 34},
    {"id": "remote-vol-up", "name": "音量+", "binding_type": "shortcut", "binding_value": "音量+", "x": 42, "y": 386, "w": 76, "h": 34},
    {"id": "remote-vol-down", "name": "音量-", "binding_type": "shortcut", "binding_value": "音量-", "x": 182, "y": 386, "w": 76, "h": 34},
]

DEFAULT_PROJECTS = [
    {
        "id": "project-athena-9681",
        "name": "9681雅典娜",
        "description": "默认联调项目示例。",
        "scripts": [
            {
                "id": "script-athena-boot",
                "name": "开机联调基线",
                "description": "先打开日志，再开放配对，最后回到桌面。",
                "steps": [
                    "setting:国内通用日志指令",
                    "wait:1.0",
                    "setting:开放遥控器配对",
                    "wait:0.5",
                    "shortcut:主页键",
                ],
            }
        ],
    }
]

DEFAULT_PROFILE = {
    "camera": {
        "last_index": 0,
        "scan_max_index": 5,
        "preview_interval_ms": 33,
        "snapshot_dir": "reports/device_lab_snapshots",
    },
    "serial": {
        "last_port": "",
        "baudrate": 115200,
        "newline": True,
        "auto_su": False,
    },
    "quick_settings": DEFAULT_QUICK_SETTINGS,
    "shortcuts": DEFAULT_SHORTCUTS,
    "remote": {
        "edit_mode": False,
        "buttons": DEFAULT_REMOTE_BUTTONS,
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
        for item in self._data.get("quick_settings", []):
            item.setdefault("id", self.make_id("setting"))
            item.setdefault("description", "")
            item.setdefault("commands", [])
        for item in self._data.get("shortcuts", []):
            item.setdefault("id", self.make_id("shortcut"))
            item.setdefault("description", "")
            item.setdefault("commands", [])
        remote = self._data.setdefault("remote", {})
        remote.setdefault("edit_mode", False)
        buttons = remote.setdefault("buttons", [])
        for button in buttons:
            button.setdefault("id", self.make_id("remote"))
            button.setdefault("binding_type", "serial")
            button.setdefault("binding_value", "")
            button.setdefault("x", 80)
            button.setdefault("y", 80)
            button.setdefault("w", 76)
            button.setdefault("h", 34)
        projects: List[Dict[str, Any]] = self._data.setdefault("projects", [])
        for project in projects:
            project.setdefault("id", self.make_id("project"))
            project.setdefault("description", "")
            scripts = project.setdefault("scripts", [])
            for script in scripts:
                script.setdefault("id", self.make_id("script"))
                script.setdefault("description", "")
                script.setdefault("steps", [])