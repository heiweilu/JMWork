# -*- coding: utf-8 -*-
"""
日志定位模块

功能：
  1. 解析飞书/MTK 问题单，提取关键信息（时间、设备SN、描述）
  2. 扫描内部日志系统导出的文件夹（syslog/ 下的 logcat_X 子目录）
  3. 根据问题时间点 ± N 分钟，精准提取日志片段
  4. 支持关键词二次过滤（取关键词命中行前后 N 分钟）
  5. 输出带上下文（问题说明）的 txt，可直接投喂 AI 分析
"""

import os
import re
import io
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

# ─────────────────── Logcat 时间戳正则 ───────────────────────────────────────
# 标准 Android logcat 格式：MM-DD HH:MM:SS.mmm  PID  TID  LEVEL  TAG: message
_LOG_TS_PATTERN = re.compile(
    r'^(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\.\d+'
)

# ─────────────────── 问题单时间解析正则 ──────────────────────────────────────
# "Fri Feb 27 14:43:00 EST 2026" 类格式
_LARK_TIME_PATTERN_EN = re.compile(
    r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+'
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+'
    r'(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+\w+\s+(\d{4})',
    re.IGNORECASE,
)
# "2026-02-27 14:43:00" 类格式
_LARK_TIME_PATTERN_ISO = re.compile(
    r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s+(\d{2}:\d{2}:\d{2})'
)
# 纯时间 "14:43" 或 "14:43:00"
_LARK_TIME_PATTERN_HHMM = re.compile(r'(\d{2}:\d{2}(?::\d{2})?)')

_MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


# ════════════════════════════════════════════════════════════════════════
# 1. 问题单解析
# ════════════════════════════════════════════════════════════════════════

def parse_bug_report(text: str) -> dict:
    """
    从飞书/MTK 问题单文本中提取关键字段。

    返回 dict，键值说明：
        title       : 缺陷名称
        firmware    : 关联固件版本
        sn          : 机身SN
        occur_time  : 解析出的 datetime 对象（可能为 None）
        occur_time_raw : 原始时间字符串
        description : 问题描述（操作步骤 + 实际结果 + 预期结果 拼接）
        platform    : 平台信息（从标题或机型推断）
        raw         : 原始文本
    """
    result = {
        'title': '',
        'firmware': '',
        'sn': '',
        'occur_time': None,
        'occur_time_raw': '',
        'description': '',
        'platform': '',
        'raw': text,
    }

    # ── 标题：优先取"缺陷名称"之后的第一个非空行
    m = re.search(r'缺陷名称\s*\n+\s*(.+)', text)
    if m:
        result['title'] = m.group(1).strip()[:200]
    else:
        # 找第一个非空、非"缺陷名称"的行
        for line in text.splitlines():
            line = line.strip()
            if line and line not in ('缺陷名称',):
                result['title'] = line[:200]
                break

    # ── 固件版本
    m = re.search(r'(?:关联固件版本|固件版本|版本号)\s*[：:]\s*([^\n]+)', text)
    if not m:
        m = re.search(r'(v\d+\.\d+[\.\d]*)', text, re.IGNORECASE)
    if m:
        result['firmware'] = m.group(1).strip()

    # ── 机身SN
    m = re.search(r'(?:机身SN[/／]?标签|SN)\s*[：:]\s*([A-Z0-9]{8,20})', text, re.IGNORECASE)
    if m:
        result['sn'] = m.group(1).strip()

    # ── 平台/机型（从标题推断）
    platform_keywords = ['戴安娜', 'Diana', '海外', '国内', 'MTK', 'RK', 'AM', 'DLP']
    for kw in platform_keywords:
        if kw.lower() in text.lower():
            result['platform'] += kw + ' '
    result['platform'] = result['platform'].strip()

    # ── 发生时间
    raw_time, parsed_time, time_only = _extract_occur_time(text)
    result['occur_time_raw'] = raw_time
    result['occur_time'] = parsed_time
    result['occur_time_only'] = time_only  # (hour, minute, second) 仅有时分秒时非 None

    # ── 问题描述（拼接关键段落）
    desc_parts = []
    for section in ['操作步骤', '实际结果', '预期结果']:
        m = re.search(rf'\[{section}\]([\s\S]*?)(?=\[|\Z)', text)
        if m:
            content = m.group(1).strip()
            if content:
                desc_parts.append(f"[{section}]\n{content}")
    result['description'] = '\n\n'.join(desc_parts)

    return result


def _extract_occur_time(text: str) -> Tuple[str, Optional[datetime], Optional[Tuple[int, int, int]]]:
    """
    从文本中提取发生时间。

    返回 (原始字符串, datetime 对象, (h,m,s) 仅时分秒元组)。
    - 如果能解析出完整日期时间，datetime 非 None，time_only 为 None。
    - 如果只能提取到时分秒（无日期），datetime 为 None，time_only 为 (h,m,s)。
    - 都无法解析时，两者均为 None。
    """
    # 优先在"发生时间"附近找
    occur_section = text
    m = re.search(r'发生时间[：:（(].*?[：:）)]?\s*([^\n]+)', text)
    if m:
        occur_section = m.group(1)

    # 尝试解析英文格式 "Fri Feb 27 14:43:00 EST 2026"
    m = _LARK_TIME_PATTERN_EN.search(occur_section)
    if m:
        month_str, day, time_str, year = m.group(1), m.group(2), m.group(3), m.group(4)
        month = _MONTH_MAP.get(month_str.lower(), 1)
        try:
            h, mi, s = [int(x) for x in time_str.split(':')]
            dt = datetime(int(year), month, int(day), h, mi, s)
            return m.group(0), dt, None
        except Exception:
            pass

    # 尝试 ISO 格式 "2026-02-27 14:43:00"
    m = _LARK_TIME_PATTERN_ISO.search(occur_section)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                          *[int(x) for x in m.group(4).split(':')])
            return m.group(0), dt, None
        except Exception:
            pass

    # 全文搜索英文格式
    m = _LARK_TIME_PATTERN_EN.search(text)
    if m:
        month_str, day, time_str, year = m.group(1), m.group(2), m.group(3), m.group(4)
        month = _MONTH_MAP.get(month_str.lower(), 1)
        try:
            h, mi, s = [int(x) for x in time_str.split(':')]
            dt = datetime(int(year), month, int(day), h, mi, s)
            return m.group(0), dt, None
        except Exception:
            pass

    # 全文搜索 ISO 格式
    m = _LARK_TIME_PATTERN_ISO.search(text)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                          *[int(x) for x in m.group(4).split(':')])
            return m.group(0), dt, None
        except Exception:
            pass

    # 最后：仅提取时分秒 "11:48左右" / "11:48:00"
    m = _LARK_TIME_PATTERN_HHMM.search(occur_section)
    if not m:
        m = _LARK_TIME_PATTERN_HHMM.search(text)
    if m:
        parts = m.group(1).split(':')
        try:
            h = int(parts[0])
            mi = int(parts[1])
            s = int(parts[2]) if len(parts) > 2 else 0
            if 0 <= h < 24 and 0 <= mi < 60 and 0 <= s < 60:
                return m.group(0), None, (h, mi, s)
        except Exception:
            pass

    return occur_section.strip()[:100], None, None


# ════════════════════════════════════════════════════════════════════════
# 2. 日志文件夹扫描
# ════════════════════════════════════════════════════════════════════════

def _read_first_log_line(filepath: str) -> Optional[str]:
    """读取日志文件的第一行（跳过非时间戳行）。"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if _LOG_TS_PATTERN.match(line):
                    return line.rstrip()
    except Exception:
        pass
    return None


def _read_last_log_line(filepath: str, tail_bytes: int = 65536) -> Optional[str]:
    """从文件末尾读取最后一条有效日志行（高效，不读整个文件）。"""
    try:
        size = os.path.getsize(filepath)
        read_size = min(tail_bytes, size)
        with open(filepath, 'rb') as f:
            f.seek(max(0, size - read_size))
            tail = f.read().decode('utf-8', errors='replace')
        # 从末尾逐行倒序找时间戳
        for line in reversed(tail.splitlines()):
            if _LOG_TS_PATTERN.match(line):
                return line.rstrip()
    except Exception:
        pass
    return None


def _parse_logcat_ts(line: str, year: int) -> Optional[datetime]:
    """解析 logcat 行时间戳，返回 datetime。year 需要外部传入（日志本身不含年份）。"""
    m = _LOG_TS_PATTERN.match(line)
    if not m:
        return None
    date_str = m.group(1)  # "02-27"
    time_str = m.group(2)  # "14:43:00"
    try:
        month, day = [int(x) for x in date_str.split('-')]
        h, mi, s = [int(x) for x in time_str.split(':')]
        return datetime(year, month, day, h, mi, s)
    except Exception:
        return None


def infer_year_from_folder(folder_path: str) -> int:
    """
    从日志文件夹名称推断年份。
    例: BVN1S1734YBK_2026_0227_145626 → 2026
    若无法推断，返回当前年份。
    """
    name = Path(folder_path).name
    m = re.search(r'_(\d{4})_', name)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d{4})', name)
    if m:
        y = int(m.group(1))
        if 2000 <= y <= 2100:
            return y
    return datetime.now().year


def scan_syslog_folder(
    syslog_path: str,
    year: Optional[int] = None,
    progress_callback=None,
) -> List[Dict]:
    """
    扫描 syslog 目录下所有 logcat_X 子目录，返回每个 logcat 文件的元信息列表。

    返回列表元素格式::
        {
            'dir':        str,       # logcat_X 目录名
            'file':       str,       # logcat.log 完整路径
            'size':       int,       # 文件大小（字节）
            'start_time': datetime,  # 第一行时间
            'end_time':   datetime,  # 最后一行时间
            'start_raw':  str,       # 第一行原始内容
            'end_raw':    str,       # 最后一行原始内容
        }
    """
    syslog_path = Path(syslog_path)
    if not syslog_path.exists():
        raise FileNotFoundError(f"路径不存在: {syslog_path}")

    if year is None:
        # 从父目录推断年份
        year = infer_year_from_folder(str(syslog_path.parent))

    # 查找所有 logcat_X 目录（含 logcat_XX_lastest 格式）
    logcat_dirs = sorted(
        [d for d in syslog_path.iterdir()
         if d.is_dir() and d.name.startswith('logcat')],
        key=lambda d: _logcat_dir_sort_key(d.name),
    )

    results = []
    total = len(logcat_dirs)
    for idx, ldir in enumerate(logcat_dirs):
        log_file = ldir / 'logcat.log'
        if not log_file.exists():
            continue

        size = log_file.stat().st_size
        first_line = _read_first_log_line(str(log_file))
        last_line = _read_last_log_line(str(log_file))

        start_time = _parse_logcat_ts(first_line, year) if first_line else None
        end_time = _parse_logcat_ts(last_line, year) if last_line else None

        results.append({
            'dir': ldir.name,
            'file': str(log_file),
            'size': size,
            'start_time': start_time,
            'end_time': end_time,
            'start_raw': first_line or '',
            'end_raw': last_line or '',
        })

        if progress_callback:
            progress_callback(idx + 1, total, ldir.name)

    return results


def _logcat_dir_sort_key(name: str) -> Tuple[int, str]:
    """对 logcat_1 / logcat_21_lastest 排序的 key。"""
    m = re.search(r'logcat_(\d+)', name)
    return (int(m.group(1)) if m else 9999, name)


# ════════════════════════════════════════════════════════════════════════
# 3. 日志提取
# ════════════════════════════════════════════════════════════════════════

def find_relevant_files(
    scan_results: List[Dict],
    target_time: datetime,
    before_min: int,
    after_min: int,
) -> List[Dict]:
    """
    从扫描结果中，筛选出时间范围与目标窗口有交集的 logcat 文件。

    特殊处理：
    - end_time 为 None（文件末行无法读取）：始终纳入，由提取阶段逐行判断
    - start_time 为设备开机时钟未同步的异常值（如 12-31，远早于或远晚于窗口）：
      仍纳入，因为文件内稍后可能包含时钟同步后的正常时间戳
    """
    window_start = target_time - timedelta(minutes=before_min)
    window_end = target_time + timedelta(minutes=after_min)

    relevant = []
    for item in scan_results:
        st = item.get('start_time')
        et = item.get('end_time')

        # end_time 未知：无法排除，纳入候选（提取时逐行过滤）
        if et is None:
            relevant.append(item)
            continue

        # start_time 未知：只要 end_time >= window_start 就纳入
        if st is None:
            if et >= window_start:
                relevant.append(item)
            continue

        # 正常交集判断
        if st <= window_end and et >= window_start:
            relevant.append(item)

    return relevant


def extract_log_window(
    file_path: str,
    year: int,
    window_start: datetime,
    window_end: datetime,
    keyword: Optional[str] = None,
    level_filter: Optional[set] = None,
    tag_filter: Optional[str] = None,
    max_lines: int = 50000,
) -> List[str]:
    """
    从单个 logcat 文件中，提取 [window_start, window_end] 时间窗口内的日志行。

    Args:
        keyword:      关键词过滤（大小写不敏感）
        level_filter: 日志级别集合，如 {'E', 'W', 'F'}；None 表示不过滤
        tag_filter:   TAG 正则关键词，如 'HDMI|display|video'；None 表示不过滤

    返回行列表。
    """
    import re as _re
    lines_out = []
    line_count = 0
    current_ts: Optional[datetime] = None

    # 预编译 TAG 过滤正则
    tag_re = _re.compile(tag_filter, _re.IGNORECASE) if tag_filter else None

    # logcat 行级别字段位置正则：MM-DD HH:MM:SS.mmm PID TID LEVEL TAG:
    _LEVEL_RE = _re.compile(
        r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+([VDIWEF])\s+(\S+)'
    )

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for raw_line in f:
                raw_line_stripped = raw_line.rstrip('\n')

                ts = _parse_logcat_ts(raw_line_stripped, year)
                if ts is not None:
                    current_ts = ts
                    if ts > window_end:
                        days_diff = abs((ts - window_end).days)
                        if days_diff < 180:
                            break

                if current_ts is not None and window_start <= current_ts <= window_end:
                    # 级别过滤
                    if level_filter:
                        m = _LEVEL_RE.match(raw_line_stripped)
                        if m and m.group(1) not in level_filter:
                            continue

                    # TAG 过滤
                    if tag_re and not tag_re.search(raw_line_stripped):
                        continue

                    # 关键词过滤
                    if keyword and keyword.lower() not in raw_line_stripped.lower():
                        continue

                    lines_out.append(raw_line_stripped)
                    line_count += 1
                    if line_count >= max_lines:
                        lines_out.append(f'[警告] 提取行数已达上限 {max_lines}，后续内容截断。')
                        break
    except Exception as e:
        lines_out.append(f'[错误] 读取文件失败: {e}')

    return lines_out


def extract_logs_by_time(
    syslog_path: str,
    target_time: datetime,
    before_min: int = 2,
    after_min: int = 2,
    keyword: Optional[str] = None,
    level_filter: Optional[set] = None,
    tag_filter: Optional[str] = None,
    year: Optional[int] = None,
    progress_callback=None,
) -> Tuple[List[str], List[Dict]]:
    """
    完整流程：扫描 + 定位 + 提取。

    返回 (extracted_lines, used_files)。
    """
    if year is None:
        year = infer_year_from_folder(str(Path(syslog_path).parent))

    scan_results = scan_syslog_folder(syslog_path, year=year,
                                      progress_callback=progress_callback)
    window_start = target_time - timedelta(minutes=before_min)
    window_end = target_time + timedelta(minutes=after_min)

    relevant = find_relevant_files(scan_results, target_time, before_min, after_min)

    all_lines: List[str] = []
    for item in relevant:
        header = f'\n{"="*60}\n[来源] {item["dir"]} | {_fmt_size(item["size"])}\n{"="*60}\n'
        all_lines.append(header)
        lines = extract_log_window(
            file_path=item['file'],
            year=year,
            window_start=window_start,
            window_end=window_end,
            keyword=keyword,
            level_filter=level_filter,
            tag_filter=tag_filter,
        )
        all_lines.extend(lines)
        if not lines:
            all_lines.append('（此文件在时间窗口内无匹配行）')

    return all_lines, relevant


def extract_logs_by_keyword(
    syslog_path: str,
    keyword: str,
    context_before_min: float = 2.0,
    context_after_min: float = 2.0,
    year: Optional[int] = None,
    progress_callback=None,
) -> Tuple[List[str], List[Dict]]:
    """
    在所有 logcat 文件中搜索关键词，对每次命中，提取命中时间点 ± N 分钟的日志。

    返回 (extracted_lines, matched_files)。
    """
    if year is None:
        year = infer_year_from_folder(str(Path(syslog_path).parent))

    scan_results = scan_syslog_folder(syslog_path, year=year,
                                      progress_callback=progress_callback)

    hit_windows: List[Tuple[datetime, datetime]] = []  # 收集命中时间窗口
    matched_files: List[Dict] = []

    for item in scan_results:
        current_ts = None
        file_hits: List[datetime] = []
        try:
            with open(item['file'], 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    ts = _parse_logcat_ts(line.rstrip(), year)
                    if ts is not None:
                        current_ts = ts
                    if keyword.lower() in line.lower() and current_ts is not None:
                        file_hits.append(current_ts)
        except Exception:
            pass

        if file_hits:
            matched_files.append(item)
            for hit_ts in file_hits:
                hit_windows.append((
                    hit_ts - timedelta(minutes=context_before_min),
                    hit_ts + timedelta(minutes=context_after_min),
                ))

    if not hit_windows:
        return [f'[结果] 未在任何 logcat 文件中找到关键词："{keyword}"'], []

    # 合并重叠窗口
    hit_windows.sort(key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    for ws, we in hit_windows:
        if merged and ws <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], we))
        else:
            merged.append((ws, we))

    # 按合并后的窗口提取日志
    all_lines: List[str] = []
    for ws, we in merged:
        all_lines.append(
            f'\n{"="*60}\n'
            f'[关键词命中窗口] {ws.strftime("%m-%d %H:%M:%S")} ~ {we.strftime("%m-%d %H:%M:%S")}\n'
            f'{"="*60}\n'
        )
        for item in scan_results:
            st = item.get('start_time')
            et = item.get('end_time')
            if st is None and et is None:
                continue
            file_start = st if st is not None else ws
            file_end = et if et is not None else we
            if file_start <= we and file_end >= ws:
                lines = extract_log_window(item['file'], year, ws, we)
                if lines:
                    all_lines.append(f'[来源: {item["dir"]}]')
                    all_lines.extend(lines)

    return all_lines, matched_files


# ════════════════════════════════════════════════════════════════════════
# 4. 输出格式化
# ════════════════════════════════════════════════════════════════════════

def format_output(
    bug_info: dict,
    extracted_lines: List[str],
    syslog_path: str,
    window_start: datetime,
    window_end: datetime,
    extraction_mode: str = 'time',  # 'time' | 'keyword'
    keyword: Optional[str] = None,
) -> str:
    """
    将 bug 上下文 + 提取的日志合并为一个完整的分析报告文本。
    """
    sep = '=' * 70
    lines = [
        sep,
        '  日志分析报告（由 DLP 自动化系统生成）',
        sep,
        '',
        '【问题背景】',
        f'  标题    : {bug_info.get("title", "")}',
        f'  固件版本: {bug_info.get("firmware", "")}',
        f'  设备SN  : {bug_info.get("sn", "")}',
        f'  平台/机型: {bug_info.get("platform", "")}',
        f'  问题时间: {bug_info.get("occur_time_raw", "")}',
        '',
        '【问题描述】',
    ]
    desc = bug_info.get('description', '')
    if desc:
        for dl in desc.splitlines():
            lines.append(f'  {dl}')
    else:
        lines.append('  （未解析到问题描述）')

    lines += [
        '',
        '【原始问题单】',
    ]
    raw = bug_info.get('raw', '')
    for rl in raw.splitlines():
        lines.append(f'  {rl}')

    lines += [
        '',
        sep,
        '【日志提取信息】',
        f'  日志路径  : {syslog_path}',
        f'  提取模式  : {extraction_mode}',
    ]
    if extraction_mode == 'time':
        lines += [
            f'  时间窗口  : {window_start.strftime("%Y-%m-%d %H:%M:%S")} ~ {window_end.strftime("%Y-%m-%d %H:%M:%S")}',
        ]
    else:
        lines += [
            f'  关键词    : {keyword}',
            f'  上下文窗口: ± {(window_end - window_start).seconds // 120} 分钟',
        ]
    lines += [
        sep,
        '【提取的日志内容】',
        '',
    ]

    lines.extend(extracted_lines)

    lines += [
        '',
        sep,
        '【AI 分析建议提示词】',
        '请根据以上日志内容，分析以下几点：',
        '1. 问题的根本原因（Root Cause）',
        '2. 涉及的关键模块或进程',
        '3. 关键错误 / 异常 / Warning 信息',
        '4. 建议在代码仓库中排查的关键位置',
        '5. 复现条件和时间线',
        sep,
    ]

    return '\n'.join(lines)


# ════════════════════════════════════════════════════════════════════════
# 5. 辅助工具
# ════════════════════════════════════════════════════════════════════════

def _fmt_size(size: int) -> str:
    """格式化文件大小。"""
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    else:
        return f'{size / 1024 / 1024:.1f} MB'


def list_log_root_folders(base_dir: str) -> List[str]:
    """
    在指定目录下递归搜索包含 syslog/ 子目录的文件夹，返回路径列表。
    搜索深度最多 4 层，避免遍历过深。
    """
    results = []
    base = Path(base_dir)
    if not base.exists():
        return results

    def _walk(path: Path, depth: int):
        if depth > 4:
            return
        try:
            for child in path.iterdir():
                if child.is_dir():
                    if child.name == 'syslog':
                        results.append(str(child.parent))
                    else:
                        _walk(child, depth + 1)
        except PermissionError:
            pass

    _walk(base, 0)
    return sorted(results)
