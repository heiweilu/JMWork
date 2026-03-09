#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Angle_test_csv.py
脚本作用:
    从预处理好的象限 TXT 文件（制表符分隔）中读取角度和坐标数据，
    逐一向 DLP8445 硬件写入梯形校正参数并回读验证，
    统计每个角度点的 PASS/FAIL 结果（含 ErrorCode 和坐标偏差 Delta），
    支持断点续传（跳过已测试角度），
    输出测试结果 TXT 至：reports/Angle_test_results/{日期}/

前置步骤:
    1. 将原始接口数据放入 data/Angle_Raw_interface_output_data/
    2. 运行 CSV_Preprocessing_Split_quadarant.py 拆分象限（仅需一次）
    3. 运行 CSV_to_TXT_converter.py 将象限 CSV 转为 TXT（仅需一次）
    4. 修改下方【手动配置区】，然后运行本脚本
============================================================
"""
import io
import os
import sys
import time
import traceback


#  工程根目录  #
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# ============================================================================
# 【手动配置区】每次测试前修改此处
#
# DATA_MODE 可选值：
#   'quadrant'  - 使用预处理后的分象限 TXT 文件
#   'raw_1deg'  - 原始1度完整数据（需先转换为 TXT）
#   'raw_05deg' - 原始0.5度完整数据（需先转换为 TXT）
#   'raw_01deg' - 原始0.1度完整数据（需先转换为 TXT）
DATA_MODE = 'quadrant'

# DATA_MODE = 'quadrant' 时选择象限文件：
#   quadrant_1_left_top.txt / quadrant_2_right_top.txt
#   quadrant_3_left_bottom.txt / quadrant_4_right_bottom.txt
#   quadrant_3_left_bottom_test.txt
TXT_QUADRANT_FILE = 'quadrant_3_left_bottom.txt'

# 测试范围（分段测试时使用，不需要时设为 None）
TEST_RANGE = {
    'yaw_min':   -40,
    'yaw_max':   40,
    'pitch_min': -40,
    'pitch_max': 40,
    'sub_yaw_min':   None,
    'sub_yaw_max':   None,
    'sub_pitch_min': None,
    'sub_pitch_max': None,
}

# 断点续传：True=跳过已测试角度；False=从头开始
RESUME_FROM_PREVIOUS = True

# 每隔 LOG_INTERVAL 个有效测试输出一次进度
LOG_INTERVAL = 10
# 每条写入后立即 flush（硬件每次测试 ~0.5s，IO 开销可忽略，防止断电/中断导致数据丢失）
# FLUSH_INTERVAL 已废弃，保留兼容旧配置，不再使用
# ============================================================================

# 步长根据 DATA_MODE 自动确定
_STEP_MAP = {'raw_1deg': 1.0, 'raw_05deg': 0.5}
STEP = _STEP_MAP.get(DATA_MODE, 0.1)

# 数据文件路径
_DATA_QUADRANT_DIR = os.path.join(DATA_ROOT, 'data', 'CSV_quadrant_data')
_DATA_RAW_DIR      = os.path.join(DATA_ROOT, 'data', 'Angle_Raw_interface_output_data')

_TXT_FILE_MAP = {
    'quadrant':  os.path.join(_DATA_QUADRANT_DIR, TXT_QUADRANT_FILE),
    'raw_1deg':  os.path.join(_DATA_RAW_DIR, 'ak_scan_yaw_pitch_step1_20260204_100304.txt'),
    'raw_05deg': os.path.join(_DATA_RAW_DIR, 'ak_scan_yaw_pitch_step0.50_20260204_125453.txt'),
    'raw_01deg': os.path.join(_DATA_RAW_DIR, 'ak_scan_yaw_pitch_step0.10_20260204_143212.txt'),
}

if DATA_MODE not in _TXT_FILE_MAP:
    raise ValueError("Invalid DATA_MODE. Choices: {}".format(list(_TXT_FILE_MAP.keys())))

TXT_FILE_PATH = _TXT_FILE_MAP[DATA_MODE]
OUTPUT_PATH   = os.path.join(DATA_ROOT, 'reports')


#  日志辅助：stdout 同时写入控制台和日志文件  #
class _Tee(object):
    def __init__(self, log_path):
        self._console = sys.stdout
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self._logfile = io.open(log_path, 'w', encoding='utf-8')
        self._buf = ''

    def write(self, msg):
        self._console.write(msg)
        self._buf += msg
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            self._logfile.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), line))

    def flush(self):
        self._console.flush()
        self._logfile.flush()

    def close(self):
        if self._buf:
            self._logfile.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), self._buf))
            self._buf = ''
        self._logfile.close()


#  导入硬件库  #
print("Importing libraries...")
try:
    from dlpc843x.commands import *
    print("Library import successful")
except Exception as e:
    print("Error: Cannot import dlpc843x.commands: {}".format(e))
    sys.exit(1)

try:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from 梯形验证器 import KeystoneValidator
    print("Keystone validator imported")
except Exception as e:
    print("Warning: Cannot import validator: {}".format(e))
    KeystoneValidator = None

print("Enabling keystone correction...")
try:
    WriteKeystoneEnableQueued(True)
    print("Keystone correction enabled")
except Exception as e:
    print("Warning: Failed to enable keystone correction: {}".format(e))

validator = KeystoneValidator() if KeystoneValidator else None
if not validator:
    print("Warning: Running without validation!")


# ──────────────────────────────────────────────────────────────────────────────
#  流式数据处理（替代原 KeystoneTestData 整体加载方案）
#  参考 Trapezoid-test.py file 模式：读一行、测一行，零等待
# ──────────────────────────────────────────────────────────────────────────────

def _in_range(yaw, pitch, test_range, step):
    """判断 (yaw, pitch) 是否在测试范围内且符合步长对齐。"""
    r = test_range
    if not (r['yaw_min'] <= yaw <= r['yaw_max']):
        return False
    if not (r['pitch_min'] <= pitch <= r['pitch_max']):
        return False
    if r.get('sub_yaw_min')   is not None and yaw   < r['sub_yaw_min']:   return False
    if r.get('sub_yaw_max')   is not None and yaw   > r['sub_yaw_max']:   return False
    if r.get('sub_pitch_min') is not None and pitch < r['sub_pitch_min']: return False
    if r.get('sub_pitch_max') is not None and pitch > r['sub_pitch_max']: return False
    s   = step
    tol = s / 2.0 if s < 1.0 else 0.5
    yaw_ok   = abs(yaw   % s) < tol or abs(yaw   % s - s) < tol
    pitch_ok = abs(pitch % s) < tol or abs(pitch % s - s) < tol
    return yaw_ok and pitch_ok


def _count_data_lines(txt_path):
    """快速统计数据行数（仅计行，不解析），用于 ETA 估算。"""
    if not os.path.exists(txt_path):
        return 0
    with open(txt_path, 'rb') as f:
        content = f.read()
    lines   = content.decode('utf-8', errors='ignore').split('\n')
    skipped = 0  # 表头 + 空行 + 注释
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        skipped += 1  # 第一条非注释行是表头
        break
    total = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
    return max(0, total - 1)  # 减去表头


def stream_test_data(txt_path, step, test_range):
    """
    流式读取 TXT 文件，逐行解析并 yield (yaw, pitch, points)。
    不把全部数据加载到内存，实现「读一行、测一行」。
    """
    if not os.path.exists(txt_path):
        raise IOError("TXT file not found: {}".format(txt_path))

    # IronPython io.open 文本模式迭代不可靠，一次性读取字节再 split
    with open(txt_path, 'rb') as f:
        content = f.read()
    # 使用 utf-8-sig 自动剥除文件开头的 BOM (\ufeff)，避免首列键名被污染
    lines  = content.decode('utf-8-sig', errors='ignore').split('\n')
    header = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if header is None:
            header = [h.strip().lstrip('\ufeff') for h in line.split('\t')]
            print("  Data header: {}".format(header))
            continue
        try:
            vals = line.split('\t')
            if len(vals) < len(header):
                continue
            row   = {header[i]: vals[i] for i in range(len(header))}
            yaw   = float(row['yaw'])
            pitch = float(row['pitch'])
            if not _in_range(yaw, pitch, test_range, step):
                continue
            points = [
                [int(float(row['TL_X'])), int(float(row['TL_Y']))],
                [int(float(row['TR_X'])), int(float(row['TR_Y']))],
                [int(float(row['BL_X'])), int(float(row['BL_Y']))],
                [int(float(row['BR_X'])), int(float(row['BR_Y']))],
            ]
            yield (yaw, pitch, points)
        except (ValueError, KeyError, IndexError):
            continue


#  核心测试函数  #
def check_keystone(write_points, txt_writer, v_angle, h_angle, angle_desc):
    """Write keystone coords to device, read back and verify, append result to TXT."""
    flat = [
        write_points[0][0], write_points[0][1],
        write_points[1][0], write_points[1][1],
        write_points[2][0], write_points[2][1],
        write_points[3][0], write_points[3][1],
    ]

    def _write_row(read_str, result, ec, delta):
        txt_writer.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            v_angle, h_angle, angle_desc,
            ','.join(map(str, flat)), read_str,
            result, ec, delta))

    try:
        if any(c < 0 or c > 65535 for c in flat):
            _write_row('', 'FAIL', '-1', '0')
            return False

        obj = KeystoneCornersQueued()
        obj.TopLeftX,     obj.TopLeftY     = write_points[0]
        obj.TopRightX,    obj.TopRightY    = write_points[1]
        obj.BottomLeftX,  obj.BottomLeftY  = write_points[2]
        obj.BottomRightX, obj.BottomRightY = write_points[3]

        WriteKeystoneCornersQueued(obj)
        WriteExecuteDisplay()
        time.sleep(0.3)

        _, _, ErrorCode = ReadExecuteDisplayStatus()
        _, read_obj     = ReadKeystoneCornersQueued()

        read = [
            int(read_obj.TopLeftX),     int(read_obj.TopLeftY),
            int(read_obj.TopRightX),    int(read_obj.TopRightY),
            int(read_obj.BottomLeftX),  int(read_obj.BottomLeftY),
            int(read_obj.BottomRightX), int(read_obj.BottomRightY),
        ]

        is_match = all(w == r for w, r in zip(flat, read))
        result   = 'PASS' if is_match else 'FAIL'
        max_diff = max(abs(w - r) for w, r in zip(flat, read))

        _write_row(','.join(map(str, read)), result, str(int(ErrorCode)), str(max_diff))
        return is_match and int(ErrorCode) == 1

    except Exception:
        try:
            _write_row('', 'FAIL', '-1', '0')
        except Exception:
            pass
        return False


def format_angle_name(v, h):
    v_s = "Yaw{}{}".format('+' if v > 0 else '', v) if v != 0 else "Yaw0"
    h_s = "Pitch{}{}".format('+' if h > 0 else '', h) if h != 0 else "Pitch0"
    return "{}, {}".format(v_s, h_s)


def load_tested_angles(txt_path):
    """Read (yaw, pitch) set from an existing result TXT for resume support."""
    tested = set()
    if not os.path.exists(txt_path):
        return tested
    try:
        with io.open(txt_path, 'r', encoding='utf-8') as f:
            next(f)  # skip header
            for line in f:
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        tested.add((float(parts[0]), float(parts[1])))
                    except ValueError:
                        pass
        print("Resume: loaded {} previously tested angles.".format(len(tested)))
    except Exception as e:
        print("Warning: Cannot read existing result file: {}".format(e))
    return tested


#  主流程  #
def main():
    t_start = time.time()

    log_path = os.path.join(DATA_ROOT, 'logs',
                            'angle_test_{}.log'.format(time.strftime("%Y%m%d_%H%M%S")))
    tee = _Tee(log_path)
    sys.stdout = tee

    print("Log file: {}".format(log_path))

    print("=" * 80)
    print("Keystone Angle Test  |  Streaming Mode (read-test-immediately)")
    print("=" * 80)
    print("Data file  : {}".format(TXT_FILE_PATH))
    print("Test range : Yaw [{}, {}]  Pitch [{}, {}]  Step {}deg".format(
        TEST_RANGE['yaw_min'], TEST_RANGE['yaw_max'],
        TEST_RANGE['pitch_min'], TEST_RANGE['pitch_max'], STEP))
    print("Resume     : {}".format('enabled' if RESUME_FROM_PREVIOUS else 'disabled'))
    print("=" * 80)

    # ── 快速预统计总行数（仅计行，不解析），用于 ETA 及进度显示 ────────── #
    print("Pre-scanning file for row count (fast)...")
    t_scan = time.time()
    grand_total = _count_data_lines(TXT_FILE_PATH)
    print("  Estimated data rows: {}  ({:.2f}s)".format(grand_total, time.time() - t_scan))

    # ── 断点续传：查找最新结果文件，加载已测角度集合 ─────────────────── #
    tested_angles = set()
    resume_file   = None   # 续跑时复用的文件路径
    if RESUME_FROM_PREVIOUS:
        results_root = os.path.join(OUTPUT_PATH, 'Angle_test_results')
        latest_txt, latest_mtime = None, 0
        if os.path.exists(results_root):
            for d in os.listdir(results_root):
                dp = os.path.join(results_root, d)
                if not os.path.isdir(dp):
                    continue
                for fname in os.listdir(dp):
                    if fname.startswith('angle_test_result_') and fname.endswith('.txt'):
                        fp = os.path.join(dp, fname)
                        mt = os.path.getmtime(fp)
                        if mt > latest_mtime:
                            latest_mtime, latest_txt = mt, fp
        if latest_txt:
            print("Resume: found result file: {}".format(latest_txt))
            tested_angles = load_tested_angles(latest_txt)
            resume_file   = latest_txt   # 续跑：追加到同一文件
        else:
            print("Resume: no previous result file found, starting from scratch\n")

    # 决定最终输出文件路径及打开模式
    if resume_file:
        txt_out   = resume_file
        file_mode = 'a'          # 追加，不重写表头
        print("Resume: appending results to: {}\n".format(txt_out))
    else:
        # 新建文件（含时间戳）
        txt_out   = os.path.join(OUTPUT_PATH, 'Angle_test_results', time.strftime("%Y%m%d"),
                                 'angle_test_result_{}.txt'.format(time.strftime("%Y_%m_%d_%H_%M_%S")))
        file_mode = 'w'
        _out_dir  = os.path.dirname(txt_out)
        if not os.path.exists(_out_dir):
            os.makedirs(_out_dir)
        print("New output file: {}\n".format(txt_out))

    # ── 核心：流式读取 + 立即测试（参考 Trapezoid-test.py file 模式）──── #
    _HEADER = ('VerticalAngle(Yaw)\tHorizontalAngle(Pitch)\tAngleDesc\t'
               'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\t'
               'Result\tErrorCode\tDelta\n')

    passed = failed = skipped = 0
    row_idx = 0          # 流中已遇到的行序号（含被跳过的）
    t_test = time.time()
    t_last_log = t_test

    print("Output file: {}".format(txt_out))
    print("\nStarting tests (streaming)...\n")

    try:
        with io.open(txt_out, file_mode, encoding='utf-8') as txtfile:
            if file_mode == 'w':
                # 全新文件：写表头
                txtfile.write(_HEADER)
            else:
                # 续跑追加：写一条分隔注释，方便区分不同批次的测试段
                txtfile.write('# --- Resume {} ---\n'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
            txtfile.flush()

            for v, h, pts in stream_test_data(TXT_FILE_PATH, STEP, TEST_RANGE):
                row_idx += 1

                # 断点续传：跳过已测角度
                if (v, h) in tested_angles:
                    skipped += 1
                    continue

                executed = passed + failed
                now = time.time()
                if executed == 0 or executed % LOG_INTERVAL == 0 \
                        or (now - t_last_log) >= 300:
                    elapsed  = now - t_test
                    avg      = elapsed / executed if executed > 0 else 0.0
                    remaining = max(grand_total - row_idx - skipped, 0)
                    eta      = remaining * avg / 60
                    rate_pct = passed * 100 // executed if executed > 0 else 0
                    print("[{}] [{}/~{}] PASS:{} FAIL:{} ({}%) | "
                          "Elapsed:{:.1f}min | Rate:{:.3f}s/test | ETA:{:.1f}min".format(
                          time.strftime('%H:%M:%S'),
                          executed + skipped, grand_total,
                          passed, failed, rate_pct,
                          elapsed / 60, avg, eta))
                    t_last_log = now

                ok = check_keystone(pts, txtfile, v, h, format_angle_name(v, h))
                if ok:
                    passed += 1
                else:
                    failed += 1

                # 每条写入后立即 flush，防止中断/异常时数据丢失
                txtfile.flush()

                time.sleep(0.1)

            txtfile.flush()  # 循环正常结束后的最终 flush

    except Exception as e:
        print("\nError during streaming test: {}".format(e))
        traceback.print_exc(file=sys.stdout)

    total_exec = passed + failed
    elapsed = time.time() - t_start
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
    print("Executed: {}  Skipped: {}  (file rows seen: {})".format(
        total_exec, skipped, row_idx))
    print("PASS: {} ({:.1f}%)  FAIL: {} ({:.1f}%)".format(
        passed, passed * 100.0 / total_exec if total_exec else 0,
        failed, failed * 100.0 / total_exec if total_exec else 0))
    print("Elapsed: {:.2f}s ({:.2f}min)".format(elapsed, elapsed / 60))
    print("Output: {}".format(txt_out))
    print("=" * 80)

    sys.stdout = tee._console
    tee.close()


if __name__ == "__main__" or str(__name__) == "<module>":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print("\nException: {}".format(e))
        traceback.print_exc()
    finally:
        if hasattr(sys.stdout, '_console'):
            orig = sys.stdout._console
            try:
                sys.stdout.close()
            except Exception:
                pass
            sys.stdout = orig
        print("\nProgram ended")