# -*- coding: utf-8 -*-
"""
通用任务工作线程

基于 QThread 的通用任务执行器，支持：
- 进度回调
- 日志回调
- 取消支持
- matplotlib Figure 安全传回主线程
"""

import threading
import traceback
from PyQt6.QtCore import QThread, pyqtSignal


class TaskWorker(QThread):
    """
    通用任务工作线程。

    在子线程中执行 module.run()，通过信号将进度/日志/结果传回主线程。

    Signals:
        progress(int, int): 进度更新 (current, total)
        log_message(str, str): 日志消息 (message, level)
        finished(dict): 任务完成，结果字典
        error(str): 任务异常
    """

    progress = pyqtSignal(int, int)
    log_message = pyqtSignal(str, str)
    finished_signal = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, run_func, input_path: str, output_dir: str,
                 params: dict, parent=None):
        """
        Args:
            run_func: 模块的 run() 函数
            input_path: 输入文件路径
            output_dir: 输出目录
            params: 参数字典
        """
        super().__init__(parent)
        self._run_func = run_func
        self._input_path = input_path
        self._output_dir = output_dir
        self._params = params
        self._cancel_event = threading.Event()

    def run(self):
        """线程执行体"""
        try:
            # 先尝试传入 stop_event（支持中途取消的模块），
            # 若模块签名不接受该参数则回退到标准调用
            try:
                result = self._run_func(
                    input_path=self._input_path,
                    output_dir=self._output_dir,
                    params=self._params,
                    progress_callback=self._on_progress,
                    log_callback=self._on_log,
                    stop_event=self._cancel_event,
                )
            except TypeError:
                result = self._run_func(
                    input_path=self._input_path,
                    output_dir=self._output_dir,
                    params=self._params,
                    progress_callback=self._on_progress,
                    log_callback=self._on_log,
                )
            if self._cancel_event.is_set():
                result = {"status": "cancelled", "message": "任务已取消"}
            self.finished_signal.emit(result)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")

    def _on_progress(self, current: int, total: int):
        """进度回调（从子线程发射信号到主线程）"""
        if not self._cancel_event.is_set():
            self.progress.emit(current, total)

    def _on_log(self, message: str, level: str = 'INFO'):
        """日志回调"""
        self.log_message.emit(message, level)

    def cancel(self):
        """请求取消任务"""
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()
