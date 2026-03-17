# -*- coding: utf-8 -*-
"""
DLP 单点读写诊断模块

目的：
将一次梯形坐标写入拆成 4 个阶段分别诊断：
1. WriteKeystoneCornersQueued
2. WriteExecuteDisplay
3. ReadExecuteDisplayStatus
4. ReadKeystoneCornersQueued

与 angle_test / trapezoid_test 不同，本模块不依赖 DLPManager 的兜底逻辑，
而是直接调用底层 SDK，完整记录每一步的：
- 是否成功（Summary.Successful）
- 耗时
- 异常信息
- 原始 ErrorCode / State
- 回读坐标

用于定位：为什么某次设备能正常回读，另一次却只写不读。
"""

import os
import time
import datetime
import traceback

MODULE_INFO = {
    "name": "DLP单点读写诊断",
    "category": "test",
    "script_file": "dlp_single_point_diag.py",
    "description": (
        "对一组固定梯形坐标执行底层 SDK 分步诊断。\n\n"
        "流程：写入坐标 → 执行显示 → 读执行状态 → 读回坐标\n"
        "输出每一步的成功位、耗时、异常、ErrorCode 和回读值，\n"
        "用于确认当前设备为什么会出现 USB 读超时。"
    ),
    "input_type": "optional",
    "input_description": "无需输入文件；通过参数直接指定 8 个角点坐标。",
    "output_type": "txt",
    "enabled": True,
    "params": [
        {"key": "tl_x", "label": "TL_x", "type": "int", "default": 0},
        {"key": "tl_y", "label": "TL_y", "type": "int", "default": 54},
        {"key": "tr_x", "label": "TR_x", "type": "int", "default": 2299},
        {"key": "tr_y", "label": "TR_y", "type": "int", "default": 0},
        {"key": "bl_x", "label": "BL_x", "type": "int", "default": 301},
        {"key": "bl_y", "label": "BL_y", "type": "int", "default": 1517},
        {"key": "br_x", "label": "BR_x", "type": "int", "default": 2008},
        {"key": "br_y", "label": "BR_y", "type": "int", "default": 2158},
        {
            "key": "repeat_count",
            "label": "重复次数",
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 20,
            "tooltip": "同一组坐标重复执行次数，用于观察第一次和后续次数是否有差异",
        },
        {
            "key": "execute_delay",
            "label": "执行后等待(秒)",
            "type": "float",
            "default": 0.3,
            "tooltip": "WriteExecuteDisplay 后等待多久再读状态/坐标",
        },
        {
            "key": "enable_keystone",
            "label": "测试前启用梯形校正",
            "type": "choice",
            "options": ["启用", "禁用"],
            "values": [True, False],
            "default": True,
        },
    ],
}


def _safe_name(obj):
    if hasattr(obj, "name"):
        return obj.name
    return str(obj)


def _safe_int(obj):
    if hasattr(obj, "value"):
        return int(obj.value)
    return int(obj)


def _fmt_ms(t0):
    return f"{(time.perf_counter() - t0) * 1000.0:.1f} ms"


def _corners_to_str(vals):
    return ",".join(str(int(v)) for v in vals)


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on", "启用")
    return bool(value)


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    from dlpc_sdk import DLPManager

    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def prog(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    mgr = None
    try:
        coords = [
            int(params.get("tl_x", 0)), int(params.get("tl_y", 54)),
            int(params.get("tr_x", 2299)), int(params.get("tr_y", 0)),
            int(params.get("bl_x", 301)), int(params.get("bl_y", 1517)),
            int(params.get("br_x", 2008)), int(params.get("br_y", 2158)),
        ]
        repeat_count = max(1, int(params.get("repeat_count", 3)))
        execute_delay = max(0.0, float(params.get("execute_delay", 0.3)))
        enable_keystone = _as_bool(params.get("enable_keystone", True))

        date_dir = os.path.join(output_dir, time.strftime("%Y%m%d"))
        os.makedirs(date_dir, exist_ok=True)
        out_path = os.path.join(
            date_dir,
            f"dlp_single_point_diag_{time.strftime('%Y_%m_%d_%H_%M_%S')}.txt"
        )

        lines = []
        lines.append("DLP 单点读写诊断报告")
        lines.append("=" * 72)
        lines.append(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"WriteCoords: {_corners_to_str(coords)}")
        lines.append(f"重复次数: {repeat_count}")
        lines.append(f"执行后等待: {execute_delay}s")
        lines.append(f"测试前启用梯形: {enable_keystone}")
        lines.append("")

        log("连接 DLPC8430...", "INFO")
        mgr = DLPManager()
        mgr.set_log_callback(log_callback)
        res = mgr.connect()
        if not res.get("success"):
            return {"status": "error", "message": res.get("message", "连接失败")}
        log("设备已连接", "INFO")
        lines.append(f"Connect: {res.get('message', '')}")

        ver = mgr.read_version()
        if ver.get("success"):
            lines.append(f"Version: {ver.get('version', '')}")
            log(f"固件版本: {ver.get('version', '')}", "INFO")
        else:
            lines.append(f"Version: {ver.get('message', '')}")

        status = mgr.read_system_status()
        if status.get("success"):
            lines.append(
                "SystemStatus: "
                f"initialized={status.get('initialized')} "
                f"error={status.get('error')} "
                f"R={status.get('red_led')} G={status.get('green_led')} B={status.get('blue_led')}"
            )
        else:
            lines.append(f"SystemStatus: {status.get('message', '')}")

        if enable_keystone:
            kres = mgr.enable_keystone(True)
            lines.append(f"EnableKeystone: {kres.get('message', '')}")
            log(kres.get("message", "梯形设置完成"), "INFO" if kres.get("success") else "WARNING")

        lines.append("")

        sdk = mgr._dlpc843x

        for idx in range(repeat_count):
            prog(idx, repeat_count)
            lines.append("-" * 72)
            lines.append(f"Round {idx + 1}/{repeat_count}")
            log(f"[Round {idx + 1}/{repeat_count}] 开始诊断", "INFO")

            corners = sdk.KeystoneCornersQueued()
            corners.TopLeftX = coords[0]
            corners.TopLeftY = coords[1]
            corners.TopRightX = coords[2]
            corners.TopRightY = coords[3]
            corners.BottomLeftX = coords[4]
            corners.BottomLeftY = coords[5]
            corners.BottomRightX = coords[6]
            corners.BottomRightY = coords[7]

            # 1) WriteKeystoneCornersQueued
            t0 = time.perf_counter()
            try:
                summary = sdk.WriteKeystoneCornersQueued(corners)
                msg = f"WriteKeystoneCornersQueued: Successful={summary.Successful} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "INFO" if summary.Successful else "WARNING")
            except Exception as e:
                msg = f"WriteKeystoneCornersQueued: EXCEPTION={e} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "ERROR")
                lines.append(traceback.format_exc())
                continue

            # 2) WriteExecuteDisplay
            t0 = time.perf_counter()
            try:
                summary = sdk.WriteExecuteDisplay()
                msg = f"WriteExecuteDisplay: Successful={summary.Successful} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "INFO" if summary.Successful else "WARNING")
            except Exception as e:
                msg = f"WriteExecuteDisplay: EXCEPTION={e} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "ERROR")
                lines.append(traceback.format_exc())
                continue

            time.sleep(execute_delay)

            # 3) ReadExecuteDisplayStatus
            t0 = time.perf_counter()
            try:
                summary, state, error_code = sdk.ReadExecuteDisplayStatus()
                ec_val = _safe_int(error_code)
                ec_name = _safe_name(error_code)
                state_name = _safe_name(state)
                msg = (
                    "ReadExecuteDisplayStatus: "
                    f"Successful={summary.Successful} "
                    f"State={state_name} "
                    f"ErrorCode={ec_val} ({ec_name}) | {_fmt_ms(t0)}"
                )
                lines.append(msg)
                log(msg, "INFO" if summary.Successful else "WARNING")
            except Exception as e:
                msg = f"ReadExecuteDisplayStatus: EXCEPTION={e} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "ERROR")
                lines.append(traceback.format_exc())

            # 4) ReadKeystoneCornersQueued
            t0 = time.perf_counter()
            try:
                summary, read_corners = sdk.ReadKeystoneCornersQueued()
                if summary.Successful and hasattr(read_corners, "TopLeftX"):
                    read_vals = [
                        int(read_corners.TopLeftX), int(read_corners.TopLeftY),
                        int(read_corners.TopRightX), int(read_corners.TopRightY),
                        int(read_corners.BottomLeftX), int(read_corners.BottomLeftY),
                        int(read_corners.BottomRightX), int(read_corners.BottomRightY),
                    ]
                    delta = max(abs(a - b) for a, b in zip(coords, read_vals))
                    msg = (
                        "ReadKeystoneCornersQueued: "
                        f"Successful=True ReadCoords={_corners_to_str(read_vals)} Delta={delta} | {_fmt_ms(t0)}"
                    )
                    lines.append(msg)
                    log(msg, "INFO")
                else:
                    msg = (
                        "ReadKeystoneCornersQueued: "
                        f"Successful={summary.Successful} HasCorners={hasattr(read_corners, 'TopLeftX')} | {_fmt_ms(t0)}"
                    )
                    lines.append(msg)
                    log(msg, "WARNING")
            except Exception as e:
                msg = f"ReadKeystoneCornersQueued: EXCEPTION={e} | {_fmt_ms(t0)}"
                lines.append(msg)
                log(msg, "ERROR")
                lines.append(traceback.format_exc())

            lines.append("")
            prog(idx + 1, repeat_count)

        report_text = "\n".join(lines)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        return {
            "status": "success",
            "output_path": out_path,
            "figure": None,
            "report_text": report_text,
            "message": f"诊断完成: {out_path}",
        }

    except Exception as e:
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
    finally:
        try:
            if mgr is not None:
                mgr.disconnect()
        except Exception:
            pass