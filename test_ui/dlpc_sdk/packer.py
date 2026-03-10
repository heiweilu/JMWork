# -*- coding: utf-8 -*-
"""
位操作工具 (packer)

来源: TI DLP Control Program / Scripts / api / packer.py
用于 dlpc843x.py 中的 bitfield 打包/解包

注意: 使用全局状态 (_packervalue)，非线程安全。
在多线程环境下需要加锁或每次调用前 packerinit()。
"""

_packervalue = 0


def packerinit(value=0):
    global _packervalue
    _packervalue = value


def setbits(newvalue, numbits, startindex):
    global _packervalue
    mask = (1 << numbits) - 1
    _packervalue = (_packervalue & ~(mask << startindex)) | ((newvalue & mask) << startindex)
    return _packervalue


def getbits(numbits, startindex):
    global _packervalue
    mask = (1 << numbits) - 1
    return (_packervalue >> startindex) & mask


def convertfloattofixed(value, scale=256):
    return int(value * scale)


def convertfixedtofloat(value, scale=256):
    return float(value) / scale
