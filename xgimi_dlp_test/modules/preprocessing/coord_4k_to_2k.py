# -*- coding: utf-8 -*-
"""
4K坐标转2K坐标模块

功能: 将 4K 分辨率设备采集的角度扫描 TXT/CSV 数据，把所有坐标列（TL_X/TL_Y/.../BR_Y）
     除以 2，转换为 2K 分辨率下的等效坐标，其余列（yaw/pitch/Fixed_Axis）保持不变。

支持格式:
  - TXT（制表符分隔），可含 # 注释行（原样保留）
  - CSV（逗号分隔）
"""

import os
import csv

MODULE_INFO = {
    "name": "4K坐标转2K",
    "category": "preprocessing",
    "description": (
        "将 4K 分辨率采集的角度扫描数据转换为 2K 分辨率坐标。\n"
        "规则：yaw / pitch / Fixed_Axis 列保持不变，\n"
        "TL_X / TL_Y / TR_X / TR_Y / BL_X / BL_Y / BR_X / BR_Y 列各除以 2。\n"
        "支持 TXT（制表符分隔，可含 # 注释行）和 CSV（逗号分隔）。\n"
        "输出文件名自动追加 _2k 后缀，保存到与输入文件相同目录。"
    ),
    "input_type": "txt_or_csv",
    "input_description": "AK接口输出的角度扫描 TXT 或 CSV 文件（含 yaw/pitch/Fixed_Axis + 8个坐标列）",
    "output_type": "txt",
    "params": [
        {
            "key": "decimal_places",
            "label": "坐标小数位数",
            "type": "int",
            "default": 2,
            "min": 0,
            "max": 6,
        },
    ],
}

# 坐标列名（这些列需要除以2，其余列不变）
_COORD_COLS = {"TL_X", "TL_Y", "TR_X", "TR_Y", "BL_X", "BL_Y", "BR_X", "BR_Y"}


def _convert_file(input_path: str, output_path: str, decimal_places: int,
                  log_cb, progress_cb) -> int:
    """
    转换单个文件，返回处理的数据行数（不含注释行和表头行）。
    """
    # 先扫描一遍统计数据行数（用于进度）
    total_data_lines = 0
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            if not line.startswith('#') and line.strip():
                total_data_lines += 1
    if total_data_lines > 0:
        total_data_lines -= 1  # 减去表头行

    # 检测分隔符
    delimiter = '\t'
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            if '\t' in line:
                delimiter = '\t'
            elif ',' in line:
                delimiter = ','
            break

    coord_indices = []   # 坐标列的列索引，读表头时确定
    processed = 0

    with open(input_path, 'r', encoding='utf-8-sig', newline='') as fin, \
         open(output_path, 'w', encoding='utf-8-sig', newline='') as fout:

        for raw_line in fin:
            # 保留 # 注释行原样输出
            if raw_line.startswith('#'):
                fout.write(raw_line)
                continue

            stripped = raw_line.rstrip('\r\n')
            if not stripped:
                fout.write(raw_line)
                continue

            fields = stripped.split(delimiter)

            # 表头行：确定坐标列索引，原样写出
            if not coord_indices and any(h in fields for h in _COORD_COLS):
                for i, h in enumerate(fields):
                    if h.strip() in _COORD_COLS:
                        coord_indices.append(i)
                fout.write(raw_line)
                continue

            # 数据行：对坐标列除以 2
            new_fields = []
            for i, val in enumerate(fields):
                if i in coord_indices:
                    try:
                        new_val = float(val) / 2.0
                        # 保持符号感知的格式：-0.00 保留原始符号前缀样式
                        formatted = f"{new_val:.{decimal_places}f}"
                        new_fields.append(formatted)
                    except ValueError:
                        new_fields.append(val)
                else:
                    new_fields.append(val)

            fout.write(delimiter.join(new_fields) + '\n')
            processed += 1
            if progress_cb and total_data_lines > 0:
                progress_cb(processed, total_data_lines)

    return processed


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        decimal_places = int(params.get('decimal_places', 2))

        if not os.path.exists(input_path):
            return {"status": "error", "message": f"路径不存在: {input_path}"}

        # 收集待转换文件
        files = []
        if os.path.isfile(input_path):
            files.append(input_path)
        elif os.path.isdir(input_path):
            for fn in sorted(os.listdir(input_path)):
                if fn.lower().endswith(('.txt', '.csv')):
                    files.append(os.path.join(input_path, fn))

        if not files:
            return {"status": "error", "message": "未找到可处理的 TXT/CSV 文件"}

        _log(f"共 {len(files)} 个文件待转换")
        output_paths = []

        for idx, fpath in enumerate(files):
            base, ext = os.path.splitext(os.path.basename(fpath))
            out_name = f"{base}_2k{ext}"
            out_dir = os.path.dirname(fpath)
            out_path = os.path.join(out_dir, out_name)

            _log(f"[{idx+1}/{len(files)}] {os.path.basename(fpath)} → {out_name}")
            rows = _convert_file(fpath, out_path, decimal_places, _log, _progress)
            _log(f"  已处理 {rows} 行数据，输出: {out_path}")
            output_paths.append(out_path)

        _log(f"全部完成，共转换 {len(output_paths)} 个文件", "SUCCESS")
        _progress(1, 1)

        final_path = output_paths[0] if len(output_paths) == 1 else os.path.dirname(output_paths[0])
        return {
            "status": "success",
            "output_path": final_path,
            "figure": None,
            "message": f"已转换 {len(output_paths)} 个文件，坐标列均已除以 2",
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
