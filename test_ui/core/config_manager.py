# -*- coding: utf-8 -*-
"""
配置管理模块

替代所有脚本中的"手动修改硬编码常量"模式。
提供 JSON 配置读写、参数校验、分组管理功能。
"""

import json
import os
import copy
from typing import Any, Optional


# 默认配置
DEFAULT_CONFIG = {
    "general": {
        "project_root": "",
        "language": "zh-CN",
    },
    "screen": {
        "width": 3839,
        "height": 2159,
    },
    "angle": {
        "step": 0.1,
        "yaw_min": -40,
        "yaw_max": 40,
        "pitch_min": -40,
        "pitch_max": 40,
        "axis_yaw_range": [-42, 42],
        "axis_pitch_range": [-42, 42],
    },
    "test": {
        "resume_from_previous": True,
        "log_interval": 10,
        "data_mode": "quadrant",
    },
    "visualization": {
        "dpi": 150,
        "figsize_width": 16,
        "figsize_height": 10,
        "corner_ratio": 0.40,
    },
    "paths": {
        "data_dir": "data",
        "reports_dir": "reports",
        "logs_dir": "logs",
        "csv_quadrant_dir": "data/CSV_quadrant_data",
        "angle_results_dir": "reports/Angle_test_results",
        "trapezoid_results_dir": "reports/Trapezoidal_coordinate_test_results",
    },
}

# 配置项描述（用于 UI 配置管理面板显示）
CONFIG_DESCRIPTIONS = {
    "general.project_root": "DLP 自动化测试工程根目录",
    "general.language": "界面语言",
    "screen.width": "投影屏幕宽度（像素）",
    "screen.height": "投影屏幕高度（像素）",
    "angle.step": "角度步长",
    "angle.yaw_min": "Yaw 最小角度",
    "angle.yaw_max": "Yaw 最大角度",
    "angle.pitch_min": "Pitch 最小角度",
    "angle.pitch_max": "Pitch 最大角度",
    "angle.axis_yaw_range": "可视化 Yaw 轴显示范围",
    "angle.axis_pitch_range": "可视化 Pitch 轴显示范围",
    "test.resume_from_previous": "断点续传开关",
    "test.log_interval": "进度日志间隔（条数）",
    "test.data_mode": "数据模式 (quadrant/raw_1deg/raw_05deg/raw_01deg)",
    "visualization.dpi": "输出图片 DPI",
    "visualization.figsize_width": "默认图片宽度（英寸）",
    "visualization.figsize_height": "默认图片高度（英寸）",
    "visualization.corner_ratio": "四角矩形范围比例",
    "paths.data_dir": "数据目录（相对工程根目录）",
    "paths.reports_dir": "报告输出目录",
    "paths.logs_dir": "日志目录",
    "paths.csv_quadrant_dir": "象限CSV数据目录",
    "paths.angle_results_dir": "角度测试结果目录",
    "paths.trapezoid_results_dir": "梯形测试结果目录",
}

# 配置项类型（用于 UI 表单组件选择）
CONFIG_TYPES = {
    "general.project_root": "path",
    "general.language": "string",
    "screen.width": "int",
    "screen.height": "int",
    "angle.step": "float",
    "angle.yaw_min": "float",
    "angle.yaw_max": "float",
    "angle.pitch_min": "float",
    "angle.pitch_max": "float",
    "angle.axis_yaw_range": "tuple",
    "angle.axis_pitch_range": "tuple",
    "test.resume_from_previous": "bool",
    "test.log_interval": "int",
    "test.data_mode": "string",
    "visualization.dpi": "int",
    "visualization.figsize_width": "float",
    "visualization.figsize_height": "float",
    "visualization.corner_ratio": "float",
    "paths.data_dir": "path",
    "paths.reports_dir": "path",
    "paths.logs_dir": "path",
    "paths.csv_quadrant_dir": "path",
    "paths.angle_results_dir": "path",
    "paths.trapezoid_results_dir": "path",
}


class ConfigManager:
    """
    JSON 配置管理器。

    支持分层 key 访问（如 'screen.width'），用户配置覆盖默认配置。
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Args:
            config_dir: 配置文件目录。默认为 test_ui/config/
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config'
            )
        self._config_dir = config_dir
        self._default_path = os.path.join(config_dir, 'default_config.json')
        self._user_path = os.path.join(config_dir, 'user_config.json')
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        """加载配置：默认 → 用户覆盖"""
        self._config = copy.deepcopy(DEFAULT_CONFIG)

        # 保存默认配置（如果不存在）
        if not os.path.exists(self._default_path):
            os.makedirs(self._config_dir, exist_ok=True)
            with open(self._default_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)

        # 加载用户配置覆盖
        if os.path.exists(self._user_path):
            try:
                with open(self._user_path, 'r', encoding='utf-8') as f:
                    user_cfg = json.load(f)
                self._deep_merge(self._config, user_cfg)
            except (json.JSONDecodeError, IOError):
                pass  # 损坏的用户配置，使用默认值

    def _deep_merge(self, base: dict, override: dict):
        """深度合并 override 到 base"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值。支持点分层 key，如 'screen.width'。

        Args:
            key: 配置键名（点分隔）
            default: 默认值

        Returns:
            配置值
        """
        parts = key.split('.')
        obj = self._config
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return default
        return obj

    def set(self, key: str, value: Any):
        """
        设置配置值。支持点分层 key。

        Args:
            key: 配置键名（点分隔）
            value: 值
        """
        parts = key.split('.')
        obj = self._config
        for part in parts[:-1]:
            if part not in obj or not isinstance(obj[part], dict):
                obj[part] = {}
            obj = obj[part]
        obj[parts[-1]] = value

    def save(self):
        """保存当前配置到用户配置文件"""
        os.makedirs(self._config_dir, exist_ok=True)
        # 只保存与默认值不同的部分
        diff = self._diff(DEFAULT_CONFIG, self._config)
        with open(self._user_path, 'w', encoding='utf-8') as f:
            json.dump(diff, f, ensure_ascii=False, indent=2)

    def _diff(self, default: dict, current: dict) -> dict:
        """计算当前配置与默认配置的差异"""
        result = {}
        for key, value in current.items():
            if key not in default:
                result[key] = value
            elif isinstance(value, dict) and isinstance(default.get(key), dict):
                sub_diff = self._diff(default[key], value)
                if sub_diff:
                    result[key] = sub_diff
            elif value != default.get(key):
                result[key] = value
        return result

    def reset(self):
        """恢复默认配置"""
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        if os.path.exists(self._user_path):
            os.remove(self._user_path)

    def get_all(self) -> dict:
        """获取完整配置字典"""
        return copy.deepcopy(self._config)

    def get_flat(self) -> dict:
        """获取扁平化配置（点分隔键 → 值），用于 UI 表格显示"""
        result = {}
        self._flatten(self._config, '', result)
        return result

    def _flatten(self, obj: dict, prefix: str, result: dict):
        for key, value in obj.items():
            full_key = f'{prefix}.{key}' if prefix else key
            if isinstance(value, dict):
                self._flatten(value, full_key, result)
            else:
                result[full_key] = value

    def get_project_root(self) -> str:
        """获取工程根目录（带自动检测）"""
        root = self.get('general.project_root', '')
        if root and os.path.isdir(root):
            return root
        # 自动检测
        from core.file_utils import get_project_root
        detected = get_project_root()
        self.set('general.project_root', detected)
        return detected

    def get_abs_path(self, key: str) -> str:
        """获取相对路径配置项的绝对路径"""
        rel_path = self.get(key, '')
        if os.path.isabs(rel_path):
            return rel_path
        return os.path.join(self.get_project_root(), rel_path)
