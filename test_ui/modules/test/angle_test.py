# -*- coding: utf-8 -*-
"""
角度测试模块 (预留骨架)

原始脚本: 202602027_dlp_auto/src/Test/angle_test_script_csv.py
功能: 通过 DLP SDK (dlpc843x) 控制投影仪执行角度测试
依赖: dlpc843x SDK + USB 硬件连接

当前状态: UI 占位，等待硬件 SDK 可用后集成
"""

MODULE_INFO = {
    "name": "角度测试(硬件)",
    "category": "test",
    "description": "通过DLP SDK控制投影仪执行角度遍历测试。\n"
                   "⚠ 需要 dlpc843x SDK 和 USB 硬件连接。\n"
                   "当前为预留骨架，暂不可执行。",
    "input_type": "csv",
    "input_description": "角度原始数据CSV（含yaw, pitch列和坐标列）",
    "output_type": "csv",
    "enabled": False,
    "params": [
        {"key": "yaw_start", "label": "Yaw起始角度", "type": "float", "default": -40},
        {"key": "yaw_end", "label": "Yaw终止角度", "type": "float", "default": 40},
        {"key": "pitch_start", "label": "Pitch起始角度", "type": "float", "default": -40},
        {"key": "pitch_end", "label": "Pitch终止角度", "type": "float", "default": 40},
        {"key": "step", "label": "步长", "type": "float", "default": 1.0},
        {"key": "timeout", "label": "超时(秒)", "type": "int", "default": 5},
    ],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    """
    预留接口 - 角度测试

    后续集成要点:
    1. import dlpc843x
    2. USB 设备初始化: find_dpp3435_device() / find_cdc_device()
    3. 遍历 yaw×pitch → dlpc843x.write_ak_scan_yaw_pitch()
    4. 读取 WriteCoords / ErrorCode
    5. 逐行写入 CSV
    """
    if log_callback:
        log_callback("角度测试模块尚未集成硬件SDK", "WARNING")
        log_callback("需要: dlpc843x SDK + USB设备连接", "WARNING")
        log_callback("请在硬件环境中通过命令行运行原始脚本", "INFO")

    return {
        "status": "error",
        "message": "角度测试需要 dlpc843x SDK 和 USB 硬件连接，当前不可用。\n"
                   "请在硬件环境中运行:\n"
                   "  python src/Test/angle_test_script_csv.py",
        "output_path": None,
        "figure": None,
    }
