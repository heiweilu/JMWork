# -*- coding: utf-8 -*-
"""
角度测试模块

功能: 通过 DLP SDK (dlpc843x) 控制投影仪执行角度遍历测试
流程: 从TXT/CSV读取yaw/pitch角度及对应四角坐标 → 逐点下发 → 回读验证 → 生成结果TXT
支持: 断点续传、范围过滤、步长过滤、进度回调
"""

import io
import os
import time
import traceback
from typing import List, Optional, Tuple

MODULE_INFO = {
    "name": "角度测试(硬件)",
    "category": "test",
    "description": "通过DLP SDK控制投影仪执行角度遍历测试。\n"
                   "从CSV文件读取yaw/pitch角度和四角坐标,逐点下发到DLP硬件并回读验证。\n"
                   "支持断点续传、范围/步长过滤。",
    "input_type": "data",
    "input_description": "角度测试数据文件（CSV 或 TXT，自动检测分隔符）\n"
                         "必须含列: yaw, pitch, TL_X, TL_Y, TR_X, TR_Y, BL_X, BL_Y, BR_X, BR_Y",
    "input_file_formats": "数据文件 (*.csv *.txt);;CSV (*.csv);;TXT (*.txt);;All (*)",
    "output_type": "txt",
    "enabled": True,
    "params": [
        {"key": "yaw_min", "label": "Yaw最小角度", "type": "float", "default": -40,
         "tooltip": "Yaw(偏航)测试范围最小值，单位:度"},
        {"key": "yaw_max", "label": "Yaw最大角度", "type": "float", "default": 40,
         "tooltip": "Yaw(偏航)测试范围最大值，单位:度"},
        {"key": "pitch_min", "label": "Pitch最小角度", "type": "float", "default": -40,
         "tooltip": "Pitch(俯仰)测试范围最小值，单位:度"},
        {"key": "pitch_max", "label": "Pitch最大角度", "type": "float", "default": 40,
         "tooltip": "Pitch(俯仰)测试范围最大值，单位:度"},
        {"key": "step", "label": "步长", "type": "float", "default": 1.0,
         "tooltip": "角度步长，过滤CSV中的角度值。如0.1表示每0.1度测一次"},
        {"key": "resume", "label": "断点续传", "type": "combo",
         "options": ["启用", "禁用"], "default": "启用",
         "tooltip": "启用后会自动跳过之前已测试过的角度，从断点处继续"},
        {"key": "resume_result_file", "label": "续跑结果文件(可选)", "type": "string", "default": "",
         "tooltip": "可手动指定历史 angle_test_result_*.txt 文件。为空时会自动优先查找输入数据同工程下的 reports/Angle_test_results 最新结果文件。"},
        {"key": "execute_delay", "label": "执行延迟(秒)", "type": "float", "default": 0.3,
         "tooltip": "WriteExecuteDisplay后的等待时间，建议0.3秒"},
    ],
}


def _load_csv_data(csv_path: str, config: dict, log_cb=None) -> list:
    """从CSV/TXT文件加载角度测试数据（自动检测分隔符：Tab / 逗号 / 空白）"""
    if log_cb:
        log_cb(f"加载数据文件: {csv_path}", "INFO")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"数据文件不存在: {csv_path}")

    yaw_min = config.get('yaw_min', -40)
    yaw_max = config.get('yaw_max', 40)
    pitch_min = config.get('pitch_min', -40)
    pitch_max = config.get('pitch_max', 40)
    step = config.get('step', 1.0)

    test_data = []
    total_rows = 0
    loaded = 0
    filtered = 0

    with open(csv_path, 'rb') as f:
        content = f.read()
    content = content.replace(b'\x00', b'')
    lines = content.decode('utf-8-sig', errors='ignore').split('\n')

    # 跳过注释行，找到表头
    header = None
    delim = None  # None = 按任意空白分割
    data_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if header is None:
            # 自动检测分隔符：有 Tab 用 Tab，有逗号用逗号，否则按空白
            if '\t' in stripped:
                delim = '\t'
            elif ',' in stripped:
                delim = ','
            else:
                delim = None
            if delim:
                header = [h.strip() for h in stripped.split(delim)]
            else:
                header = stripped.split()
            data_start = i + 1
            if log_cb:
                log_cb(f"分隔符: {repr(delim) if delim else 'whitespace'}  列: {header}", "INFO")
            break

    if header is None:
        raise ValueError("数据文件中无有效表头行")

    required = ['yaw', 'pitch', 'TL_X', 'TL_Y', 'TR_X', 'TR_Y',
                'BL_X', 'BL_Y', 'BR_X', 'BR_Y']
    missing = [col for col in required if col not in header]
    if missing:
        raise ValueError(f"数据文件缺少必要列: {missing}")

    for line_num in range(data_start, len(lines)):
        line = lines[line_num].strip()
        if not line:
            continue
        total_rows += 1
        try:
            if delim:
                values = [v.strip() for v in line.split(delim)]
            else:
                values = line.split()
            if len(values) < len(header):
                continue
            row = {header[i]: values[i] for i in range(len(header))}
            yaw = float(row['yaw'])
            pitch = float(row['pitch'])

            if not (yaw_min <= yaw <= yaw_max and pitch_min <= pitch <= pitch_max):
                filtered += 1
                continue

            if step >= 1.0:
                yaw_ok = abs(yaw % step) < 0.5 or abs(yaw % step - step) < 0.5
                pitch_ok = abs(pitch % step) < 0.5 or abs(pitch % step - step) < 0.5
            else:
                tolerance = step / 2.0
                yaw_ok = abs(yaw % step) < tolerance or abs(yaw % step - step) < tolerance
                pitch_ok = abs(pitch % step) < tolerance or abs(pitch % step - step) < tolerance

            if not (yaw_ok and pitch_ok):
                filtered += 1
                continue

            points = [
                [int(float(row['TL_X'])), int(float(row['TL_Y']))],
                [int(float(row['TR_X'])), int(float(row['TR_Y']))],
                [int(float(row['BL_X'])), int(float(row['BL_Y']))],
                [int(float(row['BR_X'])), int(float(row['BR_Y']))],
            ]
            test_data.append({'yaw': yaw, 'pitch': pitch, 'points': points})
            loaded += 1
        except (ValueError, KeyError, IndexError):
            continue

    test_data.sort(key=lambda t: (t['yaw'], t['pitch']))
    if log_cb:
        log_cb(f"数据加载完成: {loaded}/{total_rows} 条 (过滤 {filtered} 条)", "INFO")
    if loaded == 0:
        raise ValueError("没有匹配的测试数据！请检查数据文件和参数范围。")
    return test_data


def _load_tested_angles_from_file(result_file: str, log_cb=None) -> set:
    """从单个历史结果文件加载已测试角度。"""
    tested = set()
    if not result_file or not os.path.exists(result_file):
        return tested

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            next(f, None)  # 跳过表头
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        tested.add((float(parts[0]), float(parts[1])))
                    except ValueError:
                        continue
    except Exception:
        return set()

    if tested and log_cb:
        log_cb(f"断点续传: 从历史结果中读取到 {len(tested)} 个已测试角度", "INFO")
    return tested


def _find_resume_search_dirs(input_path: str, output_dir: str) -> List[str]:
    """收集断点续跑候选目录，优先包含输入数据所属工程的历史结果目录。"""
    dirs = []

    def _add_dir(path: str):
        if path and os.path.isdir(path) and path not in dirs:
            dirs.append(path)

    _add_dir(output_dir)

    cur = os.path.abspath(os.path.dirname(input_path))
    for _ in range(6):
        candidate = os.path.join(cur, 'reports', 'Angle_test_results')
        _add_dir(candidate)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    return dirs


def _find_latest_resume_file(input_path: str, output_dir: str,
                             manual_resume_file: str = '', log_cb=None) -> Optional[str]:
    """定位用于断点续跑的历史结果文件。"""
    manual_resume_file = (manual_resume_file or '').strip().strip('"')
    if manual_resume_file:
        if os.path.isfile(manual_resume_file):
            if log_cb:
                log_cb(f"断点续传: 使用手动指定结果文件: {manual_resume_file}", "INFO")
            return manual_resume_file
        if log_cb:
            log_cb(f"断点续传: 手动指定结果文件不存在: {manual_resume_file}", "WARNING")

    candidate_dirs = _find_resume_search_dirs(input_path, output_dir)
    if log_cb and candidate_dirs:
        log_cb("断点续传: 搜索目录 -> " + ' | '.join(candidate_dirs), "INFO")

    candidates: List[Tuple[float, str]] = []
    for base_dir in candidate_dirs:
        for root, _dirs, files in os.walk(base_dir):
            for fname in files:
                if fname.startswith('angle_test_result_') and fname.endswith('.txt'):
                    fpath = os.path.join(root, fname)
                    try:
                        candidates.append((os.path.getmtime(fpath), fpath))
                    except OSError:
                        continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    latest = candidates[0][1]
    if log_cb:
        log_cb(f"断点续传: 自动匹配最新结果文件: {latest}", "INFO")
    return latest


def _format_angle_name(yaw: float, pitch: float) -> str:
    yaw_text = _format_scalar(yaw)
    pitch_text = _format_scalar(pitch)
    y_s = f"Yaw{'+' if yaw > 0 else ''}{yaw_text}" if yaw != 0 else "Yaw0"
    p_s = f"Pitch{'+' if pitch > 0 else ''}{pitch_text}" if pitch != 0 else "Pitch0"
    return f"{y_s}, {p_s}"


def _format_scalar(value) -> str:
    """统一结果文件中的数值格式，避免浮点尾差。"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(num) < 1e-9:
        num = 0.0

    text = f"{num:.6f}".rstrip('0').rstrip('.')
    if '.' not in text:
        text += '.0'
    return text


def run(input_path: str, output_dir: str, params: dict,
    progress_callback=None, log_callback=None, stop_event=None) -> dict:
    """
    角度测试主流程

    1. 加载TXT数据
    2. 连接DLP设备
    3. 启用梯形校正
    4. 遍历角度 → 写入坐标 → 执行 → 回读验证
    5. 输出结果TXT
    同时将日志写入 logs/angle_test_{timestamp}.log（格式：[HH:MM:SS] msg）
    """
    _log_cb = log_callback or (lambda msg, lvl="INFO": None)
    prog = progress_callback or (lambda cur, total: None)

    from dlpc_sdk import DLPManager

    # ---- 日志文件（参考 Angle_test_csv.py 中的 _Tee 类）----
    os.makedirs(output_dir, exist_ok=True)
    _log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(output_dir))), 'logs')
    try:
        os.makedirs(_log_dir, exist_ok=True)
    except OSError:
        _log_dir = os.path.join(output_dir, 'logs')
        os.makedirs(_log_dir, exist_ok=True)
    _log_path = os.path.join(
        _log_dir, 'angle_test_{}.log'.format(time.strftime('%Y%m%d_%H%M%S')))
    _log_file = io.open(_log_path, 'w', encoding='utf-8')

    def log(msg: str, lvl: str = "INFO"):
        _log_cb(msg, lvl)
        _log_file.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), msg))
        _log_file.flush()

    def _stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    def _log_progress(executed: int, total_count: int, pass_count: int, fail_count: int,
                      start_ts: float, force: bool = False, start_offset: int = 0):
        if executed == 0 and not force:
            return
        elapsed_sec = max(0.0, time.time() - start_ts)
        elapsed_min = elapsed_sec / 60.0
        rate = (elapsed_sec / executed) if executed > 0 else 0.0
        global_pos = start_offset + executed
        remaining = max(0, total_count - global_pos)
        eta_min = (remaining * rate) / 60.0 if executed > 0 else 0.0
        pass_rate = (pass_count * 100.0 / executed) if executed > 0 else 0.0
        inner_ts = time.strftime('%H:%M:%S')
        log(
            f"[{inner_ts}] [{global_pos}/{total_count}] PASS:{pass_count} FAIL:{fail_count} ({pass_rate:.0f}%) | "
            f"Elapsed:{elapsed_min:.1f}min | Rate:{rate:.3f}s/test | ETA:{eta_min:.1f}min",
            "INFO"
        )

    log(f"Log file: {_log_path}", "INFO")

    config = {
        'yaw_min': float(params.get('yaw_min', -40)),
        'yaw_max': float(params.get('yaw_max', 40)),
        'pitch_min': float(params.get('pitch_min', -40)),
        'pitch_max': float(params.get('pitch_max', 40)),
        'step': float(params.get('step', 1.0)),
    }
    resume = params.get('resume', '启用') == '启用'
    resume_result_file = str(params.get('resume_result_file', '') or '').strip()
    execute_delay = float(params.get('execute_delay', 0.3))
    start_time = time.time()

    log("=" * 60, "INFO")
    log("角度测试 - TXT数据版", "INFO")
    log("=" * 60, "INFO")
    log(f"数据文件: {input_path}", "INFO")
    log(f"Yaw: [{config['yaw_min']}, {config['yaw_max']}], "
        f"Pitch: [{config['pitch_min']}, {config['pitch_max']}], "
        f"Step: {config['step']}°", "INFO")

    try:
        test_data = _load_csv_data(input_path, config, log)
    except Exception as e:
        log(f"数据加载失败: {e}", "ERROR")
        _log_file.close()
        return {'status': 'error', 'message': str(e), 'output_path': None, 'figure': None}

    total = len(test_data)
    log(f"共 {total} 个测试点", "INFO")
    _log_progress(0, total, 0, 0, start_time, force=True)

    log("连接 DLPC8430...", "INFO")
    mgr = DLPManager()
    mgr.set_log_callback(log)
    if not mgr.connected:
        res = mgr.connect()
        if not res['success']:
            log(f"连接失败: {res['message']}", "ERROR")
            _log_file.close()
            return {'status': 'error', 'message': res['message'],
                    'output_path': None, 'figure': None}
    log("设备已连接", "SUCCESS")

    kst_res = mgr.enable_keystone(True)
    log(kst_res['message'], "SUCCESS" if kst_res['success'] else "ERROR")

    tested_angles = set()
    resume_file = None
    if resume:
        resume_file = _find_latest_resume_file(input_path, output_dir, resume_result_file, log)
        if resume_file:
            tested_angles = _load_tested_angles_from_file(resume_file, log)
            log(f"断点续传: 本次将跳过 {len(tested_angles)} 个已测点", "INFO")
        else:
            log("断点续传: 未找到可续跑结果文件，将从头开始并新建结果文件", "WARNING")

    resume_offset = len(tested_angles)  # 已跳过数量，用于进度显示绝对位置

    date_dir = os.path.join(output_dir, time.strftime("%Y%m%d"))
    os.makedirs(date_dir, exist_ok=True)
    txt_path = resume_file or os.path.join(
        date_dir, f'angle_test_result_{time.strftime("%Y_%m_%d_%H_%M_%S")}.txt')

    passed = 0
    failed = 0
    skipped = 0

    _HEADER = ('VerticalAngle(Yaw)\tHorizontalAngle(Pitch)\tAngleDesc\t'
               'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'Result\tErrorCode\tDelta\n')

    try:
        file_exists = os.path.exists(txt_path)
        write_mode = 'a' if resume_file and file_exists else 'w'
        if resume_file:
            log(f"断点续传: 结果将继续写入历史文件: {txt_path}", "INFO")
        else:
            log(f"结果文件: {txt_path}", "INFO")

        with open(txt_path, write_mode, encoding='utf-8') as txtfile:
            if write_mode == 'w' or os.path.getsize(txt_path) == 0:
                txtfile.write(_HEADER)
            elif write_mode == 'a':
                try:
                    with open(txt_path, 'rb') as check_file:
                        check_file.seek(-1, os.SEEK_END)
                        last_char = check_file.read(1)
                    if last_char not in (b'\n', b'\r'):
                        txtfile.write('\n')
                except OSError:
                    pass
                # 续跑分隔符，便于区分新旧数据边界（不影响解析）
                txtfile.write(
                    f'# --- Resume {time.strftime("%Y-%m-%d %H:%M:%S")} '
                    f'| skipped={len(tested_angles)} ---\n'
                )
                txtfile.flush()

            for i, test in enumerate(test_data, 1):
                if _stopped():
                    log("检测到停止信号，测试将在当前点后结束", "WARNING")
                    break

                yaw = test['yaw']
                pitch = test['pitch']
                points = test['points']

                if (yaw, pitch) in tested_angles:
                    skipped += 1
                    continue

                angle_desc = _format_angle_name(yaw, pitch)
                prog(i, total)

                if i <= 5 or i % 100 == 0 or i == total:
                    log(f"[{i}/{total}] 测试 {angle_desc}", "INFO")

                # 始终从输入数据计算 write_coords，不依赖 result dict（防止 USB 失败时丢失坐标）
                flat_write = [
                    int(points[0][0]), int(points[0][1]),
                    int(points[1][0]), int(points[1][1]),
                    int(points[2][0]), int(points[2][1]),
                    int(points[3][0]), int(points[3][1]),
                ]

                # 坐标越界立即 FAIL，不发送 USB 命令（与原始脚本行为一致）
                if any(c < 0 or c > 65535 for c in flat_write):
                    w_str = ','.join(map(str, flat_write))
                    txtfile.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                        _format_scalar(yaw), _format_scalar(pitch), angle_desc,
                        w_str, '',
                        'FAIL', '-1', '0'
                    ))
                    txtfile.flush()
                    failed += 1
                    if failed <= 20:
                        log(f"  [FAIL] {angle_desc} 坐标越界: {flat_write}", "WARNING")
                    executed = passed + failed
                    if executed % 10 == 0 or _stopped():
                        _log_progress(executed, total, passed, failed, start_time, force=True, start_offset=resume_offset)
                    if _stopped():
                        break
                    continue

                result = mgr.write_corners_and_execute(
                    points[0][0], points[0][1],
                    points[1][0], points[1][1],
                    points[2][0], points[2][1],
                    points[3][0], points[3][1],
                )

                if _stopped():
                    log("检测到停止信号，停止后续测试点", "WARNING")

                w_str = ','.join(map(str, flat_write))  # 始终来自输入数据
                r_str = ','.join(map(str, result.get('read_coords', [])))
                ec = result.get('error_code', -1)
                delta = result.get('delta', 0)
                match = result.get('match', False)
                ok = match and ec == 1

                txtfile.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                    _format_scalar(yaw), _format_scalar(pitch), angle_desc,
                    w_str, r_str,
                    'PASS' if ok else 'FAIL',
                    ec, delta
                ))
                txtfile.flush()

                if ok:
                    passed += 1
                else:
                    failed += 1
                    if i <= 20 or failed <= 10:
                        err_detail = result.get('message', '')
                        log(f"  [FAIL] {angle_desc} ErrorCode={ec} Delta={delta}px" +
                            (f" ({err_detail})" if err_detail else ""), "WARNING")

                executed = passed + failed
                if executed % 10 == 0 or executed == total or _stopped():
                    _log_progress(executed, total, passed, failed, start_time, force=True, start_offset=resume_offset)

                if _stopped():
                    break

                time.sleep(max(0, execute_delay - 0.3))

    except Exception as e:
        log(f"测试异常: {traceback.format_exc()}", "ERROR")
        _log_file.close()
        return {'status': 'error', 'message': str(e),
                'output_path': txt_path, 'figure': None}

    elapsed = time.time() - start_time
    executed = passed + failed

    if executed and executed % 10 != 0:
        _log_progress(executed, total, passed, failed, start_time, force=True, start_offset=resume_offset)

    log("=" * 60, "INFO")
    if _stopped():
        log("测试已手动停止", "WARNING")
    else:
        log("测试完成", "SUCCESS")
    log(f"总计: {total}, 执行: {executed}, 跳过: {skipped}", "INFO")
    if executed > 0:
        log(f"通过: {passed} ({passed * 100 // executed}%), "
            f"失败: {failed} ({failed * 100 // executed}%)", "INFO")
    log(f"耗时: {elapsed:.1f}秒 ({elapsed / 60:.1f}分)", "INFO")
    log(f"结果: {txt_path}", "INFO")
    log(f"Final save to {txt_path}", "INFO")
    log("=" * 60, "INFO")

    _log_file.close()
    return {
        'status': 'cancelled' if _stopped() else ('success' if failed == 0 else 'warning'),
        'message': (
                   f"角度测试已停止: {passed} PASS / {failed} FAIL (共 {executed} 条)\n"
                   if _stopped() else
                   f"角度测试完成: {passed} PASS / {failed} FAIL (共 {executed} 条)\n"
                   ) +
                   f"结果文件: {txt_path}",
        'output_path': txt_path,
        'figure': None,
        'summary': {
            'total': total, 'executed': executed,
            'passed': passed, 'failed': failed,
            'skipped': skipped, 'elapsed_sec': round(elapsed, 1),
        }
    }
