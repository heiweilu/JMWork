# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
#  PyInstaller 打包配置  —  xgimi_dlp_test
#  生成单目录可执行包，内含所有数据文件和 PyQt6 运行时
#
#  构建命令：
#    pyinstaller xgimi_dlp_test.spec --clean
#  输出目录：
#    dist/xgimi_dlp_test/xgimi_dlp_test.exe
# =============================================================================

import os, sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录（spec 文件所在位置）
ROOT = os.path.dirname(os.path.abspath(SPEC))

# ---------- 数据文件收集 ----------
datas = [
    # 配置文件
    (os.path.join(ROOT, 'config'),  'config'),
    # 资源文件（固件、参考图片）
    (os.path.join(ROOT, 'assets'),  'assets'),
    # 模块源码（自动发现时 importlib 需要文件存在）
    (os.path.join(ROOT, 'modules'), 'modules'),
    # 报告目录占位（保证目录结构完整）
    (os.path.join(ROOT, 'reports'), 'reports'),
    # 日志目录占位
    (os.path.join(ROOT, 'logs'),    'logs'),
]

# 收集 PyQt6 附带的平台插件 / 样式插件
datas += collect_data_files('PyQt6', subdir='Qt6/plugins')

# ---------- 隐藏导入（动态 import 不能被静态解析的模块）----------
hidden_imports = [
    # PyQt6 核心
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtPrintSupport',
    # matplotlib 后端
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'matplotlib.figure',
    # 数据处理
    'pandas',
    'numpy',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    # 串口 / USB
    'serial',
    'serial.tools.list_ports',
    'usb',
    'usb.core',
    'usb.backend.libusb1',
    'libusb_package',
    # 动态加载的模块子包（task_registry.discover_all 用 importlib 扫描）
    'modules.analysis',
    'modules.preprocessing',
    'modules.test',
    'modules.analysis.degree_01_visualization',
    'modules.analysis.degree_1_visualization',
    'modules.analysis.trapezoid_result_vis',
    'modules.analysis.angle_boundary_stats',
    'modules.analysis.excel_report',
    'modules.analysis.kst_valid_vis',
    'modules.analysis.manual_trapezoid_gen',
    'modules.analysis.quadrant_boundary',
    'modules.analysis.quadrant_limit_vis',
    'modules.analysis.trajectory_drawing',
    'modules.analysis.errorcode1_vis',
    'modules.analysis.trapezoid_coord_vis',
    'modules.preprocessing.csv_split_quadrant',
    'modules.preprocessing.csv_to_txt',
    'modules.preprocessing.extract_errorcode',
    'modules.preprocessing.trapezoid_gen',
    'modules.test.angle_test',
    'modules.test.trapezoid_test',
    # 内部包
    'core',
    'core.config_manager',
    'core.task_registry',
    'core.coord_parser',
    'core.data_loader',
    'core.file_utils',
    'core.logger',
    'core.plot_style',
    'workers',
    'workers.serial_worker',
    'workers.task_worker',
    'dlpc_sdk',
    'dlpc_sdk.dlp_manager',
    'dlpc_sdk.dlpc843x',
    'dlpc_sdk.packer',
    'dlpc_sdk.usb_connection',
    'ui',
    'ui.styles',
    'ui.animations',
    'ui.main_window',
    'ui.pages.analysis_page',
    'ui.pages.preprocessing_page',
    'ui.pages.config_page',
    'ui.pages.history_page',
    'ui.pages.test_page',
    'ui.pages.docs_page',
    'ui.pages.serial_page',
    'ui.widgets.log_panel',
    'ui.widgets.progress_bar',
    'ui.widgets.particle_bg',
    'ui.widgets.file_selector',
    'ui.widgets.param_editor',
    'ui.widgets.matplotlib_canvas',
]

# ---------- 主分析 ----------
a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'wx', 'gi',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='xgimi_dlp_test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX 压缩可能引起杀毒误报，保持关闭
    console=False,       # 无控制台窗口（GUI 应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',   # 取消注释并提供 .ico 文件以设置图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='xgimi_dlp_test',
)
