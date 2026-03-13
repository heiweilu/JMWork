# -*- coding: utf-8 -*-
"""
文件工具模块

提供路径构建、时间戳文件名生成、文件搜索等公共功能。
统一了所有脚本中 DATA_ROOT 计算 + 输出目录创建 + 时间戳文件名模式。
"""

import os
import glob
from datetime import datetime
from typing import Optional, Tuple


def get_project_root() -> str:
    """
    获取 DLP 自动化测试工程根目录。

    基于本文件位置自动计算，假设 test_ui 与 202602027_dlp_auto 在同级目录下。
    """
    # test_ui/core/file_utils.py → 上两级到 code/
    code_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    )
    dlp_root = os.path.join(code_dir, '202602027_dlp_auto')
    if os.path.isdir(dlp_root):
        return dlp_root
    return code_dir


def make_output_path(project_root: str,
                     category: str,
                     subcategory: str = '',
                     prefix: str = '',
                     ext: str = '.png',
                     timestamp_fmt: str = '%Y%m%d_%H%M%S') -> Tuple[str, str]:
    """
    构建标准输出路径并创建目录。

    模式: {project_root}/reports/{category}/{subcategory}/{date}/{prefix}_{timestamp}.{ext}

    Args:
        project_root: 工程根目录
        category: 输出类别（如 'Data_Analysis_Result', 'Angle_test_results'）
        subcategory: 子类别（如 'Angle/1'）
        prefix: 文件名前缀
        ext: 扩展名
        timestamp_fmt: 时间戳格式

    Returns:
        (output_dir, output_filepath)
    """
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    timestamp = now.strftime(timestamp_fmt)

    parts = [project_root, 'reports', category]
    if subcategory:
        parts.append(subcategory)
    parts.append(date_str)

    output_dir = os.path.join(*parts)
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{prefix}_{timestamp}{ext}" if prefix else f"{timestamp}{ext}"
    output_filepath = os.path.join(output_dir, filename)

    return output_dir, output_filepath


def find_latest_file(search_dir: str,
                     pattern: str = '*.csv',
                     recursive: bool = True) -> Optional[str]:
    """
    在指定目录中查找最新修改的文件。

    Args:
        search_dir: 搜索根目录
        pattern: glob 模式
        recursive: 是否递归子目录

    Returns:
        最新文件的完整路径，或 None
    """
    if not os.path.isdir(search_dir):
        return None

    if recursive:
        files = glob.glob(os.path.join(search_dir, '**', pattern), recursive=True)
    else:
        files = glob.glob(os.path.join(search_dir, pattern))

    if not files:
        return None

    return max(files, key=os.path.getmtime)


def list_files(directory: str,
               extensions: Optional[list] = None,
               recursive: bool = False) -> list:
    """
    列出目录中指定扩展名的文件。

    Args:
        directory: 目录路径
        extensions: 扩展名列表，如 ['.csv', '.txt']，None 表示所有文件
        recursive: 是否递归

    Returns:
        文件路径列表
    """
    if not os.path.isdir(directory):
        return []

    result = []
    if recursive:
        for root, dirs, files in os.walk(directory):
            for f in files:
                if extensions is None or any(f.lower().endswith(e) for e in extensions):
                    result.append(os.path.join(root, f))
    else:
        for f in os.listdir(directory):
            fp = os.path.join(directory, f)
            if os.path.isfile(fp):
                if extensions is None or any(f.lower().endswith(e) for e in extensions):
                    result.append(fp)
    return sorted(result)


def safe_copy_for_encryption(src: str, dst: str) -> str:
    """
    安全复制文件（用于应对公司加密系统锁定源文件的场景）。

    来自 CSV_Preprocessing_Split_quadarant.py 的防加密策略。
    """
    import shutil
    shutil.copy2(src, dst)
    return dst
