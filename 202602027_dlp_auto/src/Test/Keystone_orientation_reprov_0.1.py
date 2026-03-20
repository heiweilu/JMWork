#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用于对比 Lua 现象的最小脚本：
1. 设置 keystone 参数并生效
2. 可选：等待一段时间
3. 设置投影方式并提交显示
"""

import sys
import time
print("Importing libraries...")
try:
    from dlpc843x.commands import *
    print("Library import successful")
except Exception as e:
    print("Error: Cannot import dlpc843x.commands: {}".format(e))
    sys.exit(1)


# ---------- 手动配置区 ----------
ENABLE_KEYSTONE = True

TL_X, TL_Y = 0, 0
TR_X, TR_Y = 3839, 0
BL_X, BL_Y = 0, 2159
BR_X, BR_Y = 3838, 2159

# Lua: disp:setProjectorPutMode(1)
TARGET_LONG_AXIS_FLIP = 1
TARGET_SHORT_AXIS_FLIP = 0

# Composer 里加载脚本后是否自动执行
AUTO_RUN_ON_LOAD = True

def main():
    WriteKeystoneEnableQueued(ENABLE_KEYSTONE)
    
    corners = KeystoneCornersQueued()
    corners.TopLeftX, corners.TopLeftY = TL_X, TL_Y
    corners.TopRightX, corners.TopRightY = TR_X, TR_Y
    corners.BottomLeftX, corners.BottomLeftY = BL_X, BL_Y
    corners.BottomRightX, corners.BottomRightY = BR_X, BR_Y
    
    summary = WriteKeystoneCornersQueued(corners)
    summary = WriteExecuteDisplay()

    #time.sleep(DELAY_BEFORE_SET_MODE_SEC)

    summary = WriteDisplayImageOrientationQueued(TARGET_LONG_AXIS_FLIP, TARGET_SHORT_AXIS_FLIP)    
    summary = WriteExecuteDisplay()


if __name__ == '__main__':
    main()
elif AUTO_RUN_ON_LOAD:
    main()