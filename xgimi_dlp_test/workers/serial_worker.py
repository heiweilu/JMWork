# -*- coding: utf-8 -*-
"""
串口读取后台线程

负责在独立线程中持续读取串口数据并通过信号发送到 UI。
"""

from PyQt6.QtCore import QThread, pyqtSignal
import time


class SerialReaderThread(QThread):
    """持续读取串口数据的后台线程"""

    data_received = pyqtSignal(bytes)   # 收到原始字节数据
    error_occurred = pyqtSignal(str)    # 串口出错
    disconnected = pyqtSignal()         # 连接断开

    def __init__(self, serial_port, parent=None):
        super().__init__(parent)
        self._serial = serial_port
        self._running = True

    def run(self):
        while self._running:
            try:
                if not self._serial or not self._serial.is_open:
                    break
                waiting = self._serial.in_waiting
                if waiting > 0:
                    data = self._serial.read(waiting)
                    if data:
                        self.data_received.emit(data)
                else:
                    time.sleep(0.02)
            except Exception as e:
                err = str(e)
                if self._running:
                    self.error_occurred.emit(err)
                break

        self.disconnected.emit()

    def stop(self):
        self._running = False
        self.wait(2000)
