# -*- coding: utf-8 -*-
"""
梯形测试模块 (预留骨架)

原始脚本: 202602027_dlp_auto/src/Test/trapezoid_test_script.py
功能: 通过 DLP SDK 控制投影仪执行梯形校正测试
依赖: dlpc843x SDK + USB 硬件连接

当前状态: UI 占位，等待硬件 SDK 可用后集成
"""

MODULE_INFO = {
    "name": "梯形测试(硬件)",
    "category": "test",
    "description": "通过DLP SDK控制投影仪执行梯形校正测试。\n"
                   "⚠ 需要 dlpc843x SDK 和 USB 硬件连接。\n"
                   "当前为预留骨架，暂不可执行。",
    "input_type": "none",
    "input_description": "无需输入文件（由设备直接执行）",
    "output_type": "dir",
    "enabled": False,
    "params": [
        {"key": "yaw", "label": "Yaw角度", "type": "float", "default": 0},
        {"key": "pitch", "label": "Pitch角度", "type": "float", "default": 0},
        {"key": "repeat", "label": "重复次数", "type": "int", "default": 10},
        {"key": "interval", "label": "间隔(秒)", "type": "float", "default": 1.0},
    ],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    """
    预留接口 - 梯形测试

    后续集成要点:
    1. import dlpc843x
    2. USB 设备初始化
    3. dlpc843x.write_ak_scan_yaw_pitch(yaw, pitch)
    4. 读取 isKstValid / ErrorCode / ReadCoords
    5. 多次重复并记录每次数据
    """
    if log_callback:
        log_callback("梯形测试模块尚未集成硬件SDK", "WARNING")
        log_callback("需要: dlpc843x SDK + USB设备连接", "WARNING")
        log_callback("请在硬件环境中通过命令行运行原始脚本", "INFO")

    return {
        "status": "error",
        "message": "梯形测试需要 dlpc843x SDK 和 USB 硬件连接，当前不可用。\n"
                   "请在硬件环境中运行:\n"
                   "  python src/Test/trapezoid_test_script.py",
        "output_path": None,
        "figure": None,
    }
