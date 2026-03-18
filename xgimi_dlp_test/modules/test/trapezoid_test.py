# -*- coding: utf-8 -*-
"""
梯形坐标测试模块

功能: 通过 DLP SDK 控制投影仪执行梯形校正坐标扫描测试
流程: 固定三个角点 → 对第四个角点在坐标范围内逐步扫描 → 逐点写入/回读/比对
支持: 四个角点选择、步长配置、失败细扫、进度回调
输出: 结果TXT（制表符分隔），格式与 Trapezoid-test.py 一致
"""

import io
import os
import copy
import time
import traceback

MODULE_INFO = {
    "name": "梯形坐标测试(硬件)",
    "category": "test",
    "description": "通过DLP SDK控制投影仪执行梯形坐标扫描测试。\n"
                   "固定三个角点,第四个角点在坐标范围内逐步扫描,\n"
                   "写入坐标→执行→回读→比对,寻找坐标边界。",
    "input_type": "optional",
    "input_description": "scan(扫描模式): 无需输入文件（由参数配置扫描范围）\n"
                         "file(文件模式): 读取坐标文件逐行测试（TXT/CSV, Tab或逗号分隔）",
    "output_type": "txt",
    "enabled": True,
    "params": [
        {"key": "test_mode", "label": "测试模式", "type": "combo",
         "options": ["scan(扫描模式)", "file(文件模式)"], "default": "scan(扫描模式)",
         "tooltip": "scan: 自动扫描坐标范围; file: 从输入文件读取坐标逐行测试"},
        {"key": "scan_corner", "label": "扫描角点", "type": "combo",
         "options": ["右上(TopRight)", "左上(TopLeft)", "左下(BottomLeft)", "右下(BottomRight)"],
         "default": "右上(TopRight)",
         "tooltip": "选择要扫描的角点，其余三个角点保持默认位置",
         "visible_when": {"key": "test_mode", "values": ["scan(扫描模式)"]}},
        {"key": "x_step", "label": "X步长", "type": "int", "default": 6,
         "tooltip": "X坐标扫描步长(像素)。值越小精度越高但耗时越长",
         "visible_when": {"key": "test_mode", "values": ["scan(扫描模式)"]}},
        {"key": "y_step", "label": "Y步长", "type": "int", "default": 3,
         "tooltip": "Y坐标扫描步长(像素)。值越小精度越高但耗时越长",
         "visible_when": {"key": "test_mode", "values": ["scan(扫描模式)"]}},
        {"key": "fine_scan", "label": "失败细扫", "type": "combo",
         "options": ["启用", "禁用"], "default": "启用",
         "tooltip": "遇到FAIL时，以step=1对周围区域细扫确定精确边界",
         "visible_when": {"key": "test_mode", "values": ["scan(扫描模式)"]}},
        {"key": "single_row_test", "label": "单行测试", "type": "combo",
         "options": ["否", "是"], "default": "否",
         "tooltip": "仅测试第一行(Y的第一个值)，用于快速验证和时间估算",
         "visible_when": {"key": "test_mode", "values": ["scan(扫描模式)"]}},
        {"key": "execute_delay", "label": "执行延迟(秒)", "type": "float", "default": 0.3,
         "tooltip": "WriteExecuteDisplay后的等待时间，建议0.3秒"},
    ],
}

# 默认的四角坐标范围 (屏幕分辨率 3840x2160)
WIDTH = 3839
HEIGHT = 2159

DEFAULT_POINTS = {
    # [起点坐标, 终点坐标]  — 每个角点的扫描范围
    0: {"name": "TopLeft",     "start": [0, 0],        "end": [1536, 864]},
    1: {"name": "TopRight",    "start": [3839, 0],     "end": [2304, 864]},
    2: {"name": "BottomLeft",  "start": [0, 2159],     "end": [1536, 1296]},
    3: {"name": "BottomRight", "start": [3839, 2159],  "end": [2304, 1296]},
}

CORNER_MAP = {
    "右上(TopRight)": 1,
    "左上(TopLeft)": 0,
    "左下(BottomLeft)": 2,
    "右下(BottomRight)": 3,
}


def _check_keystone(mgr, write_points: list, txt_writer) -> tuple:
    """
    单次梯形校正测试

    Args:
        mgr: DLPManager 实例
        write_points: [[TL_x,TL_y], [TR_x,TR_y], [BL_x,BL_y], [BR_x,BR_y]]
        txt_writer: 已打开的TXT文件对象

    Returns:
        tuple: (match_success: bool, error_code: int)
    """
    from dlpc_sdk.usb_connection import USBConnectionError

    def _do_write():
        return mgr.write_corners_and_execute(
            write_points[0][0], write_points[0][1],
            write_points[1][0], write_points[1][1],
            write_points[2][0], write_points[2][1],
            write_points[3][0], write_points[3][1],
        )

    result = None
    try:
        result = _do_write()
    except USBConnectionError:
        # 设备断连，尝试重连一次
        try:
            mgr.disconnect()
        except Exception:
            pass
        res = mgr.connect()
        if not res['success']:
            raise USBConnectionError(f"重连失败: {res.get('message', '')}") from None
        # 重连成功后再次执行
        try:
            result = _do_write()
        except Exception as e:
            raise USBConnectionError(f"重连后再次执行失败: {str(e)}") from e

    if result is None:
        # 防御性编程：确保 result 有值
        raise RuntimeError("_check_keystone 内部错误：result 未被设置")

    w_str = ','.join(map(str, result.get('write_coords', [])))
    r_str = ','.join(map(str, result.get('read_coords', [])))
    ec = result.get('error_code', -1)
    match = result.get('match', False)
    ok = 'PASS' if (match and ec == 1) else 'FAIL'

    txt_writer.write('{}\t{}\t{}\t{}\n'.format(w_str, r_str, ok, ec))
    txt_writer.flush()

    return match, ec  # 返回 (match_success, error_code)



def _run_file_mode(input_path: str, output_dir: str, params: dict,
                   log, prog, stop_event=None) -> dict:
    """
    文件模式：从 TXT/CSV 坐标文件逐行读取 8 个坐标，逐行调用 _check_keystone 测试。

    文件格式（参考 Trapezoid-test.py）：
      - 首列为 TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y（逗号分隔）
      - 每行可用 Tab 分隔多列，取第一列作为坐标字符串
      - 以 "WriteCoords" 开头的行视为表头跳过    输出: Tab 分隔的 TXT 文件，格式与 Trapezoid-test.py 一致    """
    from dlpc_sdk import DLPManager

    log("=" * 60, "INFO")
    log("梯形坐标测试 (文件模式)", "INFO")
    log("=" * 60, "INFO")

    if not input_path or not os.path.exists(input_path):
        msg = f"输入文件不存在: {input_path}"
        log(msg, "ERROR")
        return {'status': 'error', 'message': msg, 'output_path': None, 'figure': None}

    execute_delay = float(params.get('execute_delay', 0.3))

    # 读取坐标行
    # 支持两种格式：
    #   1. 传统格式：每行首列为 "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y"
    #   2. 扩圆坐标格式（TSV 多列）：含 WriteCoords 命名列，取该列值解析
    coord_rows = []
    with open(input_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        lines = f.readlines()

    # 检测是否为带命名列的 TSV（第一行含 Tab 且包含 "WriteCoords" 字段）
    wc_col_idx = None
    if lines:
        first = lines[0].strip()
        if '\t' in first and 'WriteCoords' in first.split('\t'):
            wc_col_idx = first.split('\t').index('WriteCoords')
            log(f"检测到 TSV 格式，WriteCoords 位于第 {wc_col_idx+1} 列", "INFO")
            lines = lines[1:]  # 跳过表头

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        # 跳过传统格式的表头行（以 WriteCoords 开头）
        if stripped.startswith('WriteCoords') and '\t' not in stripped:
            continue
        # 取坐标字符串
        if wc_col_idx is not None:
            # TSV 多列格式：取 WriteCoords 列
            cols = stripped.split('\t')
            if len(cols) <= wc_col_idx:
                continue
            coord_str = cols[wc_col_idx].strip().strip('"\'')
        elif '\t' in stripped:
            # 传统 Tab 格式：首列为坐标
            coord_str = stripped.split('\t')[0].strip().strip('"\'')
        else:
            coord_str = stripped.strip('"\'')
        try:
            parts = [int(float(x.strip())) for x in coord_str.split(',') if x.strip()]
            if len(parts) < 8:
                continue
            # TL, TR, BL, BR
            wp = [
                [parts[0], parts[1]],
                [parts[2], parts[3]],
                [parts[4], parts[5]],
                [parts[6], parts[7]],
            ]
            coord_rows.append(wp)
        except (ValueError, IndexError):
            continue

    if not coord_rows:
        msg = "文件中未找到有效坐标行（需要8个逗号分隔整数）"
        log(msg, "ERROR")
        return {'status': 'error', 'message': msg, 'output_path': None, 'figure': None}

    log(f"从文件加载了 {len(coord_rows)} 行坐标", "INFO")

    # 连接设备    log("连接 DLPC8430...", "INFO")
    mgr = DLPManager()
    if not mgr.connected:
        res = mgr.connect()
        if not res['success']:
            log(f"连接失败: {res['message']}", "ERROR")
            return {'status': 'error', 'message': res['message'],
                    'output_path': None, 'figure': None}
    log("设备已连接", "SUCCESS")

    kst_res = mgr.enable_keystone(True)
    log(kst_res['message'], "SUCCESS" if kst_res['success'] else "ERROR")

    os.makedirs(output_dir, exist_ok=True)
    date_dir = os.path.join(output_dir, time.strftime('%Y%m%d'))
    os.makedirs(date_dir, exist_ok=True)
    txt_path = os.path.join(
        date_dir,
        'result_file_{}.txt'.format(time.strftime('%Y_%m_%d_%H_%M_%S')))

    _HEADER = ('WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'Result\tErrorCode\n')

    log(f"Creating TXT file: {txt_path}", "INFO")

    total_tests = len(coord_rows)
    pass_count = 0
    fail_count = 0
    start_time = time.time()

    def _stopped():
        return stop_event is not None and stop_event.is_set()

    try:
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(_HEADER)
            for idx, wp in enumerate(coord_rows):
                if _stopped():
                    log("\u68c0测到停止信号，提前结束文件模式测试", "WARNING")
                    break
                ok, ec_val = _check_keystone(mgr, wp, txtfile)
                if ok:
                    pass_count += 1
                else:
                    fail_count += 1
                done = pass_count + fail_count
                _es = time.time() - start_time
                _rt = _es / done if done > 0 else 0
                _pct = pass_count * 100.0 / done if done > 0 else 0
                _eta = (total_tests - done) * _rt / 60 if done > 0 else 0
                log(
                    f"[{done}/{total_tests}] "
                    f"TL={wp[0]} TR={wp[1]} BL={wp[2]} BR={wp[3]} "
                    f"\u2192 {'PASS' if ok else 'FAIL'} EC={ec_val} | "
                    f"PASS:{pass_count} FAIL:{fail_count} ({_pct:.0f}%) | "
                    f"Elapsed:{_es / 60:.1f}min | Rate:{_rt:.3f}s/test | ETA:{_eta:.1f}min",
                    "INFO" if ok else "WARNING"
                )
                prog(done, total_tests)
                time.sleep(execute_delay)

    except Exception as e:
        log(f"测试异常: {traceback.format_exc()}", "ERROR")
        return {'status': 'error', 'message': str(e),
                'output_path': txt_path, 'figure': None}

    elapsed = time.time() - start_time
    done_tests = pass_count + fail_count

    log("=" * 60, "INFO")
    if _stopped() and done_tests < total_tests:
        log("文件模式测试已停止（用户中断）", "WARNING")
    else:
        log("文件模式测试完成", "SUCCESS")
    log(f"总计: {total_tests} 行, 已测: {done_tests}, PASS: {pass_count}, FAIL: {fail_count}", "INFO")
    log(f"耗时: {elapsed:.1f}秒", "INFO")
    log(f"结果: {txt_path}", "INFO")
    log("=" * 60, "INFO")

    status = 'cancelled' if (_stopped() and done_tests < total_tests) else \
             ('success' if fail_count == 0 else 'warning')
    return {
        'status': status,
        'message': f"文件模式测试{'已停止' if status == 'cancelled' else '完成'}: "
                   f"{done_tests} 点, PASS={pass_count}, FAIL={fail_count}\n结果: {txt_path}",
        'output_path': txt_path,
        'figure': None,
        'summary': {
            'total_tests': done_tests,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'elapsed_sec': round(elapsed, 1),
        }
    }


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:
    """
    梯形坐标扫描测试主流程

    1. 连接DLP设备
    2. 启用梯形校正
    3. 固定三个角点，对选定角点进行X/Y范围扫描
    4. 遇到失败时可选细扫
    5. 输出结果TXT（Tab分隔，格式与 Trapezoid-test.py 一致）
    同时将日志写入 logs/trapezoid_test_{timestamp}.log（格式：[HH:MM:SS] msg）
    """
    _log_cb = log_callback or (lambda msg, lvl="INFO": None)
    prog = progress_callback or (lambda cur, total: None)

    from dlpc_sdk import DLPManager

    # ---- 日志文件（参考 Trapezoid-test.py 中的 _Tee 类）----
    os.makedirs(output_dir, exist_ok=True)
    _log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(output_dir))), 'logs')
    try:
        os.makedirs(_log_dir, exist_ok=True)
    except OSError:
        _log_dir = os.path.join(output_dir, 'logs')
        os.makedirs(_log_dir, exist_ok=True)
    _log_path = os.path.join(
        _log_dir, 'trapezoid_test_{}.log'.format(time.strftime('%Y%m%d_%H%M%S')))
    _log_file = io.open(_log_path, 'w', encoding='utf-8')

    def log(msg: str, lvl: str = "INFO"):
        _log_cb(msg, lvl)
        _log_file.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), msg))
        _log_file.flush()

    log(f"Log file: {_log_path}", "INFO")

    # 参数解析
    test_mode = params.get('test_mode', 'scan(扫描模式)')
    is_file_mode = test_mode.startswith('file')

    # ---- 文件模式 ----
    if is_file_mode:
        result = _run_file_mode(input_path, output_dir, params, log, prog, stop_event)
        _log_file.close()
        return result

    corner_name = params.get('scan_corner', '右上(TopRight)')
    corner_idx = CORNER_MAP.get(corner_name, 1)
    x_step = int(params.get('x_step', 6))
    y_step = int(params.get('y_step', 3))
    fine_scan = params.get('fine_scan', '启用') == '启用'
    single_row = params.get('single_row_test', '否') == '是'
    execute_delay = float(params.get('execute_delay', 0.3))

    start_time = time.time()

    log("=" * 60, "INFO")
    log("梯形坐标扫描测试", "INFO")
    log("=" * 60, "INFO")

    corner_info = DEFAULT_POINTS[corner_idx]
    x_start, y_start = corner_info["start"]
    x_end, y_end = corner_info["end"]
    x_step_signed = x_step if x_end >= x_start else -x_step
    y_step_signed = y_step if y_end >= y_start else -y_step

    total_x = abs(x_end - x_start) // x_step + 1
    total_y = abs(y_end - y_start) // y_step + 1

    log(f"扫描角点: {corner_info['name']} (index={corner_idx})", "INFO")
    log(f"X范围: {x_start} → {x_end} (step={x_step_signed}, {total_x}步)", "INFO")
    log(f"Y范围: {y_start} → {y_end} (step={y_step_signed}, {total_y}行)", "INFO")
    log(f"模式: {'单行测试' if single_row else '完整测试'}", "INFO")

    # 固定的三个角点
    fixed_points = []
    for i in range(4):
        if i != corner_idx:
            fixed_points.append(DEFAULT_POINTS[i]["start"][:])

    # 连接设备
    log("连接 DLPC8430...", "INFO")
    mgr = DLPManager()
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

    # 输出 TXT（参考 Trapezoid-test.py 路径结构）
    date_dir = os.path.join(output_dir, time.strftime('%Y%m%d'))
    os.makedirs(date_dir, exist_ok=True)
    txt_path = os.path.join(
        date_dir,
        'result_scan_{}_{}.txt'.format(
            corner_info["name"], time.strftime('%Y_%m_%d_%H_%M_%S')))

    _HEADER = ('WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'Result\tErrorCode\n')

    log(f"Creating TXT file: {txt_path}", "INFO")

    row_count = 0
    total_tests = 0
    pass_count = 0
    fail_count = 0
    _stopped = (lambda: stop_event is not None and stop_event.is_set())

    try:
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(_HEADER)

            for current_y in range(y_start, y_end + y_step_signed, y_step_signed):
                if _stopped():
                    log("检测到停止信号，终止扫描", "WARNING")
                    break

                row_start = time.time()
                row_tests = 0

                log(f"[Y={current_y}] 开始扫描...", "INFO")

                for current_x in range(x_start, x_end + x_step_signed, x_step_signed):
                    if _stopped():
                        log(f"检测到停止信号，终止 Y={current_y} 行扫描", "WARNING")
                        break

                    # 构建完整四角坐标
                    points = copy.deepcopy(fixed_points)
                    points.insert(corner_idx, [current_x, current_y])

                    ok, _ec = _check_keystone(mgr, points, txtfile)
                    total_tests += 1
                    row_tests += 1

                    prog(total_tests, total_x * total_y)

                    if ok:
                        pass_count += 1
                    else:
                        fail_count += 1
                        # 失败细扫
                        if fine_scan and not _stopped():
                            log(f"  [FAIL @ ({current_x},{current_y})] 细扫...", "WARNING")
                            new_y_start = max(current_y - y_step, 0) if y_step_signed > 0 else current_y + y_step
                            new_x_start = max(current_x - x_step, 0) if x_step_signed > 0 else current_x + x_step
                            fine_y_step = 1 if y_step_signed > 0 else -1
                            fine_x_step = 1 if x_step_signed > 0 else -1

                            if new_y_start != current_y:
                                for ny in range(new_y_start, current_y, fine_y_step):
                                    if _stopped():
                                        break
                                    if new_x_start != current_x:
                                        for nx in range(new_x_start, current_x, fine_x_step):
                                            if _stopped():
                                                break
                                            fp = copy.deepcopy(fixed_points)
                                            fp.insert(corner_idx, [nx, ny])
                                            _check_keystone(mgr, fp, txtfile)
                                            total_tests += 1
                                    else:
                                        fp = copy.deepcopy(fixed_points)
                                        fp.insert(corner_idx, [new_x_start, ny])
                                        _check_keystone(mgr, fp, txtfile)
                                        total_tests += 1
                            else:
                                for nx in range(new_x_start, current_x, fine_x_step):
                                    if _stopped():
                                        break
                                    fp = copy.deepcopy(fixed_points)
                                    fp.insert(corner_idx, [nx, new_y_start])
                                    _check_keystone(mgr, fp, txtfile)
                                    total_tests += 1

                        log(f"  X扫描在 ({current_x},{current_y}) 断开", "WARNING")
                        break

                row_elapsed = time.time() - row_start
                row_count += 1
                _done_s = pass_count + fail_count
                _es_s = time.time() - start_time
                _rt_s = _es_s / _done_s if _done_s > 0 else 0
                _pct_s = pass_count * 100.0 / _done_s if _done_s > 0 else 0
                _rem_s = total_x * total_y - _done_s
                _eta_s = _rem_s * _rt_s / 60 if _done_s > 0 else 0
                log(
                    f"[Y={current_y}] {row_tests}点完成 | "
                    f"PASS:{pass_count} FAIL:{fail_count} ({_pct_s:.0f}%) | "
                    f"Elapsed:{_es_s / 60:.1f}min | Rate:{_rt_s:.3f}s/test | ETA:{_eta_s:.1f}min",
                    "INFO"
                )

                # 首行时间估算
                if row_count == 1:
                    est = row_elapsed * total_y
                    log(f"预估总时间: {est:.0f}秒 ({est / 60:.1f}分 / {est / 3600:.1f}时)", "INFO")

                if single_row:
                    log("单行测试模式完成", "INFO")
                    break

    except Exception as e:
        log(f"测试异常: {traceback.format_exc()}", "ERROR")
        _log_file.close()
        return {'status': 'error', 'message': str(e),
                'output_path': txt_path, 'figure': None}

    elapsed = time.time() - start_time

    # 判断是否被手动停止
    if _stopped():
        log("=" * 60, "INFO")
        log("扫描已停止（用户中断）", "WARNING")
        log(f"已完成: {total_tests} 测试点, 失败: {fail_count}", "INFO")
        log(f"耗时: {elapsed:.1f}秒", "INFO")
        log(f"结果: {txt_path}", "INFO")
        log("=" * 60, "INFO")
        _log_file.close()
        return {
            'status': 'cancelled',
            'message': f"扫描已停止: {total_tests} 测试点, {fail_count} 失败\n结果文件: {txt_path}",
            'output_path': txt_path,
            'figure': None,
            'summary': {
                'total_tests': total_tests,
                'fail_count': fail_count,
                'rows_scanned': row_count,
                'elapsed_sec': round(elapsed, 1),
            }
        }

    log("=" * 60, "INFO")
    log("扫描完成", "SUCCESS")
    log(f"总测试点: {total_tests}, 失败: {fail_count}", "INFO")
    log(f"耗时: {elapsed:.1f}秒 ({elapsed / 60:.1f}分)", "INFO")
    log(f"结果: {txt_path}", "INFO")
    log(f"Final save to {txt_path}", "INFO")
    log("=" * 60, "INFO")

    _log_file.close()
    return {
        'status': 'success' if fail_count == 0 else 'warning',
        'message': f"梯形扫描完成: {total_tests} 测试点, {fail_count} 失败\n"
                   f"结果文件: {txt_path}",
        'output_path': txt_path,
        'figure': None,
        'summary': {
            'total_tests': total_tests,
            'fail_count': fail_count,
            'rows_scanned': row_count,
            'elapsed_sec': round(elapsed, 1),
        }
    }
