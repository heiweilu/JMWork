# -*- coding: utf-8 -*-
"""
DLP 设备管理器

提供 DLPC8430 设备的高级管理接口:
- 连接/断开管理
- 初始化 dlpc843x 命令库
- 封装常用的梯形校正/角度校正命令流
- 线程安全的状态管理
"""

import time
import logging
import threading
from typing import Optional, Tuple, List

from .usb_connection import USBBulkConnection, USBConnectionError

logger = logging.getLogger(__name__)


class DLPManager:
    """
    DLPC8430 设备管理器 (单例)

    使用方式:
        mgr = DLPManager()
        mgr.connect()
        mgr.enable_keystone(True)
        mgr.write_corners_and_execute(corners_obj)
        result = mgr.read_corners()
        mgr.disconnect()
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._usb = USBBulkConnection()
        self._sdk_initialized = False
        self._connected = False
        self._dlpc843x = None
        self._log_callback = None
        # ReadKeystoneCornersQueued 失败后设 True，跳过所有坐标读命令
        self._write_only_mode = False
        # ReadExecuteDisplayStatus 不可用时设 True，无需影响坐标读取
        self._read_status_unavailable = False

    def set_log_callback(self, callback):
        """将底层 USB / SDK 日志透传给上层。"""
        self._log_callback = callback
        self._usb.set_log_callback(callback)

    # ──────────── 连接管理 ────────────

    @property
    def connected(self) -> bool:
        return self._connected and self._usb.connected

    def connect(self) -> dict:
        """
        连接 DLPC8430 设备并初始化 SDK

        Returns:
            dict: {'success': bool, 'message': str, 'mode': str}
        """
        try:
            self._usb.open()
            self._init_sdk()
            self._connected = True
            self._write_only_mode = False        # 每次重连时重置，重新探测读取能力
            self._read_status_unavailable = False

            # 读取设备模式验证连接
            mode_info = self._read_mode_safe()
            msg = f"DLPC8430 连接成功 — {mode_info}"
            logger.info(msg)
            return {'success': True, 'message': msg, 'mode': mode_info}

        except USBConnectionError as e:
            self._connected = False
            msg = str(e)
            logger.error("连接失败: %s", msg)
            return {'success': False, 'message': msg, 'mode': ''}

        except Exception as e:
            self._connected = False
            msg = f"初始化异常: {e}"
            logger.error(msg)
            return {'success': False, 'message': msg, 'mode': ''}

    def disconnect(self):
        """断开连接"""
        try:
            self._usb.close()
        finally:
            self._connected = False
            self._sdk_initialized = False
            logger.info("DLPC8430 已断开")

    def _init_sdk(self):
        """初始化 dlpc843x 命令库，注册 USB 回调"""
        if self._sdk_initialized:
            return

        from . import dlpc843x
        self._dlpc843x = dlpc843x

        # 注册 read/write 回调 — dlpc843x 的所有命令通过这两个回调通信
        dlpc843x.DLPC843Xinit(
            readcommandcb=self._usb.read_command,
            writecommandcb=self._usb.write_command
        )
        self._sdk_initialized = True
        logger.info("DLPC843X SDK 初始化完成")

    def _read_mode_safe(self) -> str:
        """安全读取设备模式"""
        try:
            sdk = self._dlpc843x
            summary, mode, config = sdk.ReadMode()
            if summary.Successful:
                return f"Mode={mode.name}, Config={config.name}"
            return "模式读取失败"
        except Exception as e:
            return f"模式读取异常: {e}"

    # ──────────── 梯形校正命令 ────────────

    def enable_keystone(self, enable: bool = True) -> dict:
        """
        启用/禁用梯形校正

        Returns:
            dict: {'success': bool, 'message': str}
        """
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary = sdk.WriteKeystoneEnableQueued(enable)
            ok = summary.Successful
            msg = f"梯形校正已{'启用' if enable else '禁用'}" if ok else "设置失败"
            return {'success': ok, 'message': msg}
        except Exception as e:
            return {'success': False, 'message': f"启用梯形校正异常: {e}"}

    def write_optical_params(self, throw_ratio: float = 1.2,
                             vertical_offset: float = 0.0) -> dict:
        """写入光学参数"""
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary = sdk.WriteOpticalParametersQueued(throw_ratio, vertical_offset)
            ok = summary.Successful
            return {'success': ok,
                    'message': f"光学参数: ThrowRatio={throw_ratio}, VertOffset={vertical_offset}"}
        except Exception as e:
            return {'success': False, 'message': f"写入光学参数异常: {e}"}

    def write_keystone_angles(self, pitch: float, yaw: float,
                              roll: float = 0.0) -> dict:
        """写入梯形校正角度 (Pitch/Yaw/Roll)"""
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary = sdk.WriteKeystoneAnglesQueued(pitch, yaw, roll)
            ok = summary.Successful
            return {'success': ok,
                    'message': f"角度设置: Pitch={pitch}, Yaw={yaw}, Roll={roll}"}
        except Exception as e:
            return {'success': False, 'message': f"写入角度异常: {e}"}

    def read_keystone_angles(self) -> dict:
        """读取当前梯形校正角度"""
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary, pitch, yaw, roll = sdk.ReadKeystoneAnglesQueued()
            if summary.Successful:
                return {'success': True, 'pitch': pitch, 'yaw': yaw, 'roll': roll}
            return {'success': False, 'message': '读取失败'}
        except Exception as e:
            return {'success': False, 'message': f"读取角度异常: {e}"}

    def write_corners(self, tl_x, tl_y, tr_x, tr_y,
                      bl_x, bl_y, br_x, br_y) -> dict:
        """
        写入梯形四角坐标

        Args:
            tl_x, tl_y: 左上角
            tr_x, tr_y: 右上角
            bl_x, bl_y: 左下角
            br_x, br_y: 右下角

        Returns:
            dict: {'success': bool, 'message': str}
        """
        self._check_connected()
        try:
            sdk = self._dlpc843x
            corners = sdk.KeystoneCornersQueued()
            corners.TopLeftX = int(tl_x)
            corners.TopLeftY = int(tl_y)
            corners.TopRightX = int(tr_x)
            corners.TopRightY = int(tr_y)
            corners.BottomLeftX = int(bl_x)
            corners.BottomLeftY = int(bl_y)
            corners.BottomRightX = int(br_x)
            corners.BottomRightY = int(br_y)

            summary = sdk.WriteKeystoneCornersQueued(corners)
            ok = summary.Successful
            return {'success': ok,
                    'message': f"写入坐标: TL({tl_x},{tl_y}) TR({tr_x},{tr_y}) "
                               f"BL({bl_x},{bl_y}) BR({br_x},{br_y})"}
        except Exception as e:
            return {'success': False, 'message': f"写入坐标异常: {e}"}

    def read_corners(self) -> dict:
        """
        读取当前梯形四角坐标

        Returns:
            dict: {'success': bool, 'corners': [TL_X,TL_Y,TR_X,TR_Y,BL_X,BL_Y,BR_X,BR_Y]}
        """
        self._check_connected()
        # 已知 USB 读取不可用，直接返回失败（调用层会用写入坐标兜底）
        if self._write_only_mode:
            return {'success': False, 'message': '只写模式：跳过 USB 读坐标'}
        try:
            sdk = self._dlpc843x
            summary, corners = sdk.ReadKeystoneCornersQueued()
            # TI SDK finally 块在 USB 读取失败时仍会 return (Summary, KeystoneCornersQueued 类对象)
            # 但类属性（TopLeftX等）从未被赋值 → AttributeError；用 hasattr 检查
            if summary.Successful and hasattr(corners, 'TopLeftX'):
                data = [
                    int(corners.TopLeftX), int(corners.TopLeftY),
                    int(corners.TopRightX), int(corners.TopRightY),
                    int(corners.BottomLeftX), int(corners.BottomLeftY),
                    int(corners.BottomRightX), int(corners.BottomRightY),
                ]
                return {'success': True, 'corners': data}
            # 读取失败，标记只写模式（首次触发时提示一次）
            self._write_only_mode = True
            if self._log_callback:
                self._log_callback("ReadKeystoneCornersQueued 无响应，切换只写模式（坐标读取将跳过）", "WARNING")
            return {'success': False, 'message': '读取坐标失败(SDK未能读回数据)，切换只写模式'}
        except Exception as e:
            if not self._write_only_mode:
                self._write_only_mode = True
                if self._log_callback:
                    self._log_callback(f"ReadKeystoneCornersQueued 异常 → 只写模式: {e}", "WARNING")
            return {'success': False, 'message': f"读取坐标异常: {e}"}

    def execute_display(self) -> dict:
        """
        执行显示 (WriteExecuteDisplay)
        触发所有排队命令生效

        Returns:
            dict: {'success': bool, 'state': str, 'error_code': int}
        """
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary = sdk.WriteExecuteDisplay()
            if not summary.Successful:
                return {'success': False, 'message': '执行显示命令发送失败', 'error_code': -1}

            # 等待执行完成
            time.sleep(0.3)

            # ReadExecuteDisplayStatus 可能超时或 TI SDK finally 块 NameError
            # ReadExecuteDisplayStatus 失败不代表写入一定失败，但错误码不可用。
            # 这里返回软件层哨兵值 -2，避免把 GeneralFailure(0) 或成功(1) 混淆。
            if self._read_status_unavailable:
                # ReadExecuteDisplayStatus 已确认不可用，直接跳过，免除每次 2s 超时
                ec = -2
                state_name = 'SkippedStatusUnavailable'
                ok = True
            else:
                try:
                    summary, state, error_code = sdk.ReadExecuteDisplayStatus()
                    if not summary.Successful:
                        # dlpc843x.py 的 finally 吞掉了超时异常并以 Successful=False 返回
                        # 主动抛出使外层 except 捕获并设置 _read_status_unavailable
                        raise RuntimeError(
                            f"ReadExecuteDisplayStatus Successful=False（USB 超时被内部捕获）"
                        )
                    # error_code 可能是 ErrCodeT 枚举成员或原始 int（0=NoError 不在枚举中）
                    ec = error_code.value if hasattr(error_code, 'value') else int(error_code)
                    state_name = state.name if hasattr(state, 'name') else str(state)
                    ok = summary.Successful
                except Exception as read_e:
                    logger.debug("ReadExecuteDisplayStatus 不可用 (%s)，标记跳过后续调用", read_e)
                    self._read_status_unavailable = True
                    ec = -2
                    state_name = 'ReadUnavailable'
                    ok = True

            return {
                'success': ok,
                'state': state_name,
                'error_code': ec,
                'message': f"ExecuteDisplay: state={state_name}, errorCode={ec}"
            }
        except Exception as e:
            return {'success': False, 'message': f"执行显示异常: {e}", 'error_code': -1}

    def write_corners_and_execute(self, tl_x, tl_y, tr_x, tr_y,
                                  bl_x, bl_y, br_x, br_y) -> dict:
        """
        完整的一次梯形测试: 写入坐标 → 执行显示 → 读回验证

        Returns:
            dict: {
                'success': bool,
                'write_coords': [8 ints],
                'read_coords': [8 ints],
                'match': bool,
                'error_code': int,
                'delta': int
            }
        """
        # 始终预先构建 write_coords，确保任何失败路径都能携带它
        write_coords = [int(tl_x), int(tl_y), int(tr_x), int(tr_y),
                        int(bl_x), int(bl_y), int(br_x), int(br_y)]

        # 1. 写入坐标
        w_res = self.write_corners(tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y)
        if not w_res['success']:
            return {'success': False, 'message': w_res['message'],
                    'write_coords': write_coords, 'read_coords': [],
                    'error_code': -1, 'match': False, 'delta': 0}

        # 2. 执行显示
        e_res = self.execute_display()
        error_code = e_res.get('error_code', -1)

        # 如果 execute_display 完全失败（USB 异常 → error_code=-1），
        # 跳过 read_corners（它也必然失败），避免额外浪费 2s USB 超时时间
        if error_code == -1 and not e_res.get('success', False):
            return {'success': False,
                    'message': e_res.get('message', '执行显示异常'),
                    'write_coords': write_coords, 'read_coords': [],
                    'error_code': -1, 'match': False, 'delta': 0}

        # 3. 读回坐标
        r_res = self.read_corners()
        if not r_res['success']:
            # 不再用写入坐标伪装成读回坐标，否则会把整批数据误记为 PASS。
            # 若执行状态已知且为真实硬件错误码，则保留该错误码；
            # 若执行状态成功(1)但坐标读失败，则使用 -3 明确表示读回不可用。
            logger.debug("read_corners 不可用 (%s)，返回明确失败而非 PASS 兜底",
                         r_res.get('message', ''))
            final_ec = error_code if error_code != 1 else -3
            return {
                'success': False,
                'write_coords': write_coords,
                'read_coords': [],
                'match': False,
                'error_code': final_ec,
                'delta': 0,
                'message': (
                    f"FAIL (read unavailable) ErrorCode={final_ec} "
                    f"ExecErrorCode={error_code} Delta=0px"
                )
            }

        # 4. 比对
        read_coords = r_res['corners']
        match = all(w == r for w, r in zip(write_coords, read_coords))
        diffs = [abs(w - r) for w, r in zip(write_coords, read_coords)]
        delta = max(diffs) if diffs else 0

        return {
            'success': match and error_code == 1,
            'write_coords': write_coords,
            'read_coords': read_coords,
            'match': match,
            'error_code': error_code,
            'delta': delta,
            'message': f"{'PASS' if match and error_code == 1 else 'FAIL'} "
                       f"ErrorCode={error_code} Delta={delta}px"
        }

    def read_version(self) -> dict:
        """读取固件版本"""
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary, major, minor, patch = sdk.ReadVersion()
            if summary.Successful:
                return {'success': True, 'version': f"{major}.{minor}.{patch}"}
            return {'success': False, 'message': '版本读取失败'}
        except Exception as e:
            return {'success': False, 'message': f"版本读取异常: {e}"}

    def read_system_status(self) -> dict:
        """读取系统状态"""
        self._check_connected()
        try:
            sdk = self._dlpc843x
            summary, status = sdk.ReadSystemStatus()
            if summary.Successful:
                return {
                    'success': True,
                    'initialized': status.SystemInitializationDone,
                    'error': status.SystemError,
                    'red_led': status.RedLedEnabled,
                    'green_led': status.GreenLedEnabled,
                    'blue_led': status.BlueLedEnabled,
                }
            return {'success': False, 'message': '状态读取失败'}
        except Exception as e:
            return {'success': False, 'message': f"状态读取异常: {e}"}

    # ──────────── 设备检测 (静态) ────────────

    @staticmethod
    def check_device() -> dict:
        """检查设备是否存在 (无需连接)"""
        return USBBulkConnection.find_device()

    @staticmethod
    def check_pyusb_available() -> bool:
        """检查 pyusb 是否可用"""
        try:
            import usb.core
            return True
        except ImportError:
            return False

    # ──────────── 内部方法 ────────────

    def _check_connected(self):
        if not self.connected:
            raise USBConnectionError("DLPC8430 未连接，请先调用 connect()")
