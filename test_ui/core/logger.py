# -*- coding: utf-8 -*-
"""
日志模块

合并了 Angle_test_csv.py 和 Trapezoid-test.py 中重复的 _Tee 类，
扩展为:
  - TeeLogger: stdout 分流 + 文件日志（保留原始功能）
  - QtSignalHandler: 通过 Qt 信号推送日志到 UI 面板
  - setup_logger(): 标准 logging 配置
"""

import io
import os
import sys
import time
import logging
from typing import Optional, Callable


class TeeLogger:
    """
    stdout 分流器：同时输出到控制台和日志文件。

    保留原有 _Tee 的行为：行缓冲 + [HH:MM:SS] 时间戳前缀。
    新增: ui_callback 支持，可将日志推送到 UI 面板。
    """

    def __init__(self, log_path: str, ui_callback: Optional[Callable] = None):
        """
        Args:
            log_path: 日志文件路径
            ui_callback: 可选的 UI 回调函数 callback(message, level)
        """
        self._console = sys.stdout
        self._ui_callback = ui_callback
        self._buf = ''

        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        self._logfile = io.open(log_path, 'w', encoding='utf-8')

    def write(self, msg):
        self._console.write(msg)
        self._buf += msg
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            timestamp = time.strftime('%H:%M:%S')
            log_line = f'[{timestamp}] {line}\n'
            self._logfile.write(log_line)
            if self._ui_callback:
                level = 'ERROR' if 'error' in line.lower() or 'fail' in line.lower() else 'INFO'
                self._ui_callback(line, level)

    def flush(self):
        self._console.flush()
        self._logfile.flush()

    def close(self):
        if self._buf:
            timestamp = time.strftime('%H:%M:%S')
            self._logfile.write(f'[{timestamp}] {self._buf}\n')
            self._buf = ''
        self._logfile.close()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *args):
        sys.stdout = self._console
        self.close()


class QtSignalHandler(logging.Handler):
    """
    logging.Handler 子类，通过信号/回调将日志推送到 Qt UI。

    用法：
        handler = QtSignalHandler(callback=log_panel.append_log)
        logging.getLogger().addHandler(handler)
    """

    def __init__(self, callback: Callable):
        """
        Args:
            callback: 回调函数 callback(message: str, level: str)
        """
        super().__init__()
        self._callback = callback

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            self._callback(msg, level)
        except Exception:
            self.handleError(record)


def setup_logger(name: str = 'dlp_test',
                 log_file: Optional[str] = None,
                 level: int = logging.INFO,
                 ui_callback: Optional[Callable] = None) -> logging.Logger:
    """
    配置标准 logging 日志器。

    Args:
        name: 日志器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
        ui_callback: UI 回调（可选，用于 QtSignalHandler）

    Returns:
        配置好的 Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        logger.handlers.clear()

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    fmt = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S')
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    # UI 信号输出
    if ui_callback:
        qt_handler = QtSignalHandler(ui_callback)
        qt_handler.setLevel(level)
        qt_handler.setFormatter(fmt)
        logger.addHandler(qt_handler)

    return logger
