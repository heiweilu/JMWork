# -*- coding: utf-8 -*-
"""
USB Bulk 通信层

替代 TI DLP Control Program 的 .NET CLR USB 实现，
使用 pyusb 直接与 DLPC8430 设备进行 USB Bulk 通信。

协议参数 (与 TI connection.py 保持一致):
  - InsertByteLength = True
  - InsertChecksum   = False
  - RequestACK       = True
  - Timeout          = 2000 ms
  - VID  = 0x0451 (Texas Instruments)
  - PID  = 0x8430 (DLPC8430)

帧格式:
  Write: [ByteLength(2)] + [Opcode + Data]
  Read:  发送 [ByteLength(2)] + [Opcode]  → 接收 [ByteLength(2)] + [Data]
"""

import struct
import threading
import logging

logger = logging.getLogger(__name__)

# TI DLPC8430 USB identifiers
USB_VID = 0x0451
USB_PID = 0x8430

# USB Bulk endpoints (标准 TI DLP 设备)
EP_OUT = 0x01  # Host → Device
EP_IN = 0x81   # Device → Host

# Protocol settings (匹配 TI connection.py)
INSERT_BYTE_LENGTH = True
INSERT_CHECKSUM = False
REQUEST_ACK = True
USB_TIMEOUT_MS = 2000


class USBConnectionError(Exception):
    """USB 连接异常"""
    pass


class USBBulkConnection:
    """
    DLPC8430 USB Bulk 通信层

    实现 TI DLP Control Program 的 USBBulkCommandInterface 功能，
    为 dlpc843x.py 提供 read_command / write_command 回调。
    """

    def __init__(self, vid=USB_VID, pid=USB_PID, timeout=USB_TIMEOUT_MS):
        self.vid = vid
        self.pid = pid
        self.timeout = timeout
        self._device = None
        self._ep_out = None
        self._ep_in = None
        self._lock = threading.Lock()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected and self._device is not None

    def open(self) -> bool:
        """
        打开 USB 连接

        Returns:
            True if connected successfully

        Raises:
            USBConnectionError: 连接失败
        """
        try:
            import usb.core
            import usb.util
        except ImportError:
            raise USBConnectionError(
                "pyusb 未安装。请运行: pip install pyusb libusb-package"
            )

        # 获取 libusb1 后端（优先使用 libusb-package 自带的 DLL）
        backend = None
        try:
            import libusb_package
            backend = libusb_package.get_libusb1_backend()
        except Exception:
            pass  # 回退到 pyusb 默认后端搜索

        with self._lock:
            if self._connected:
                return True

            # 查找设备
            self._device = usb.core.find(idVendor=self.vid, idProduct=self.pid,
                                          backend=backend)
            if self._device is None:
                raise USBConnectionError(
                    f"未找到 DLPC8430 设备 (VID=0x{self.vid:04X}, PID=0x{self.pid:04X})\n"
                    "请检查:\n"
                    "  1. USB 线缆已连接\n"
                    "  2. 设备已上电\n"
                    "  3. 设备管理器中可见 'DLPC8430' 设备\n"
                    "  4. 已安装正确的 USB 驱动 (libusb/WinUSB)"
                )

            # 设置设备配置
            try:
                self._device.set_configuration()
            except Exception:
                # 可能已经配置
                pass

            # 获取活动配置和接口
            cfg = self._device.get_active_configuration()
            intf = cfg[(0, 0)]

            # 查找 Bulk 端点
            self._ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )
            self._ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )

            if self._ep_out is None or self._ep_in is None:
                raise USBConnectionError(
                    "未找到 USB Bulk 端点。\n"
                    "确认设备驱动已正确安装 (Zadig → libusb-win32 / WinUSB)"
                )

            self._connected = True
            logger.info("DLPC8430 USB 连接成功 (OUT=0x%02X, IN=0x%02X)",
                        self._ep_out.bEndpointAddress, self._ep_in.bEndpointAddress)
            return True

    def close(self):
        """关闭 USB 连接"""
        with self._lock:
            if self._device is not None:
                try:
                    import usb.util
                    usb.util.dispose_resources(self._device)
                except Exception:
                    pass
                self._device = None
                self._ep_out = None
                self._ep_in = None
            self._connected = False
            logger.info("DLPC8430 USB 连接已关闭")

    def write_command(self, writebytes, protocol_data):
        """
        写命令到设备 (对应 TI 的 _writecommand 回调)

        Args:
            writebytes: 字节列表 [opcode, data...]
            protocol_data: ProtocolData 对象 (CommandDestination, OpcodeLength 等)
        """
        if not self._connected:
            raise USBConnectionError("USB 未连接")

        with self._lock:
            packet = self._build_write_packet(writebytes, protocol_data)
            try:
                self._ep_out.write(packet, timeout=self.timeout)
                logger.debug("TX [%d bytes]: %s", len(packet), packet.hex() if isinstance(packet, (bytes, bytearray)) else bytes(packet).hex())
            except Exception as e:
                if self._is_device_gone(e):
                    self._connected = False
                raise USBConnectionError(f"USB 写入失败: {e}")

            # RequestACK — 等待 ACK 响应
            if REQUEST_ACK:
                try:
                    ack = self._ep_in.read(64, timeout=self.timeout)
                    logger.debug("ACK [%d bytes]: %s", len(ack), bytes(ack).hex())
                except Exception as e:
                    logger.warning("ACK 读取超时: %s", e)

    def read_command(self, read_length, writebytes, protocol_data):
        """
        读命令 (对应 TI 的 _readcommand 回调)

        先发送读请求 (opcode)，然后接收响应数据。

        Args:
            read_length: 期望读取的数据字节数
            writebytes: 字节列表 [opcode] (读请求)
            protocol_data: ProtocolData 对象

        Returns:
            list: 读取到的数据字节列表
        """
        if not self._connected:
            raise USBConnectionError("USB 未连接")

        with self._lock:
            packet = self._build_read_packet(writebytes, protocol_data)
            try:
                self._ep_out.write(packet, timeout=self.timeout)
                logger.debug("TX-Read [%d bytes]: %s", len(packet), bytes(packet).hex())
            except Exception as e:
                if self._is_device_gone(e):
                    self._connected = False
                raise USBConnectionError(f"USB 读请求失败: {e}")

            # 接收响应
            try:
                # 读取足够长度的数据
                response_len = read_length + 4  # 额外的 header 空间
                raw = self._ep_in.read(max(64, response_len), timeout=self.timeout)
                raw = list(raw)
                logger.debug("RX [%d bytes]: %s", len(raw), bytes(raw).hex())
            except Exception as e:
                if self._is_device_gone(e):
                    self._connected = False
                raise USBConnectionError(f"USB 读取失败: {e}")

            # 解析响应 — 提取有效数据
            data = self._parse_read_response(raw, read_length)
            return data

    @staticmethod
    def _is_device_gone(exc) -> bool:
        """
        判断异常是否表示 USB 设备物理断开。
        通信超时/协议错误不视为断开；仅设备拔出才标记为断开。
        """
        try:
            import usb.core
            if isinstance(exc, usb.core.USBError):
                msg = str(exc).lower()
                # ENODEV/No such device / Entity not found
                if getattr(exc, 'errno', None) in (19, -19):
                    return True
                if any(k in msg for k in ('no such device', 'entity not found',
                                          'device not found')):
                    return True
        except Exception:
            pass
        return False

    def _build_write_packet(self, writebytes, protocol_data):
        """
        构建写命令数据包

        TI 协议格式: [ByteLength(2)] + [CommandByte] + [Data]
        CommandByte 高2位: destination (00=broadcast, 01=controller)
        CommandByte bit5: 0=write
        """
        cmd_byte = self._make_command_byte(
            destination=protocol_data.CommandDestination,
            is_read=False)
        opcode = writebytes[0]
        data = writebytes[1:] if len(writebytes) > 1 else []

        payload = [cmd_byte, opcode] + data

        if INSERT_BYTE_LENGTH:
            length = len(payload)
            packet = list(struct.pack('<H', length)) + payload
        else:
            packet = payload

        return bytes(packet)

    def _build_read_packet(self, writebytes, protocol_data):
        """
        构建读命令数据包

        TI 协议格式: [ByteLength(2)] + [CommandByte] + [Opcode]
        CommandByte bit5: 1=read
        """
        cmd_byte = self._make_command_byte(
            destination=protocol_data.CommandDestination,
            is_read=True)
        opcode = writebytes[0]

        payload = [cmd_byte, opcode]

        if INSERT_BYTE_LENGTH:
            length = len(payload)
            packet = list(struct.pack('<H', length)) + payload
        else:
            packet = payload

        return bytes(packet)

    def _make_command_byte(self, destination, is_read):
        """
        构建命令字节

        Bit 7-6: Destination (0=broadcast, 1=controller, 4=composer)
        Bit 5:   R/W (0=write, 1=read)
        Bit 4-0: Flags (reserved)
        """
        cmd = (destination & 0x07) << 6
        if is_read:
            cmd |= 0x20  # bit 5 = read
        return cmd

    def _parse_read_response(self, raw, expected_length):
        """
        解析读响应数据

        响应格式: [ByteLength(2)] + [Header(1)] + [Data(N)]
        """
        if INSERT_BYTE_LENGTH:
            if len(raw) < 3:
                logger.warning("响应数据过短: %d bytes", len(raw))
                return raw
            # 跳过 2 字节长度 + 1 字节 header
            data = raw[3:]
        else:
            if len(raw) < 1:
                return raw
            data = raw[1:]

        return data[:expected_length]

    @staticmethod
    def find_device():
        """
        检查 DLPC8430 设备是否存在

        Returns:
            dict: 设备信息 {'found': bool, 'vid': int, 'pid': int, 'desc': str}
        """
        try:
            import usb.core
            # 获取 libusb1 后端
            _backend = None
            try:
                import libusb_package
                _backend = libusb_package.get_libusb1_backend()
            except Exception:
                pass
            dev = usb.core.find(idVendor=USB_VID, idProduct=USB_PID, backend=_backend)
            if dev:
                return {
                    'found': True,
                    'vid': USB_VID,
                    'pid': USB_PID,
                    'desc': f"DLPC8430 (VID=0x{USB_VID:04X}, PID=0x{USB_PID:04X})",
                    'manufacturer': getattr(dev, 'manufacturer', 'Texas Instruments'),
                    'product': getattr(dev, 'product', 'DLPC8430'),
                }
            return {'found': False, 'vid': USB_VID, 'pid': USB_PID, 'desc': '未找到设备'}
        except ImportError:
            return {'found': False, 'vid': USB_VID, 'pid': USB_PID,
                    'desc': 'pyusb 未安装'}
        except Exception as e:
            return {'found': False, 'vid': USB_VID, 'pid': USB_PID,
                    'desc': f'检测失败: {e}'}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()
