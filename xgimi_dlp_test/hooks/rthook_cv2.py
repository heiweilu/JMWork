# -*- coding: utf-8 -*-
"""
PyInstaller runtime hook: 处理 TSD 存储驱动导致的 .py 文件损坏。

在某些 Windows 透明存储去重 (TSD) 驱动下，.py 数据文件在
PyInstaller frozen 环境中被读取时，内容被替换为 TSD 元数据。

策略:
1. hook-cv2.py 排除 cv2 的 .py 数据文件（避免磁盘上的 TSD 损坏版本）
2. 本 hook 在 _MEIPASS/cv2/ 创建干净的 config 文件（exec_file_wrapper 需要从磁盘读取）
3. monkey-patch open() 和 compile() 作为安全网
"""
import builtins
import os
import sys
import io

# ===== 1. 创建干净的 cv2 config 文件 =====
if getattr(sys, 'frozen', False):
    _cv2_dir = os.path.join(sys._MEIPASS, 'cv2')
    if os.path.isdir(_cv2_dir):
        _configs = {
            'config.py': "import os\nBINARIES_PATHS = [\n    os.path.join(LOADER_DIR, '..')\n] + BINARIES_PATHS\n",
            'config-3.py': "PYTHON_EXTENSIONS_PATHS = [\n    LOADER_DIR\n] + PYTHON_EXTENSIONS_PATHS\n",
            f'config-{sys.version_info[0]}.{sys.version_info[1]}.py':
                "PYTHON_EXTENSIONS_PATHS = [\n    LOADER_DIR\n] + PYTHON_EXTENSIONS_PATHS\n",
        }
        for name, content in _configs.items():
            _p = os.path.join(_cv2_dir, name)
            with open(_p, 'w', encoding='utf-8') as _f:
                _f.write(content)

# ===== 2. monkey-patch open() 拦截 cv2 config 读取 =====
_CV2_CONFIG_CONTENT = {
    'config.py': "import os\nBINARIES_PATHS = [\n    os.path.join(LOADER_DIR, '..')\n] + BINARIES_PATHS\n",
    'config-3.py': "PYTHON_EXTENSIONS_PATHS = [\n    LOADER_DIR\n] + PYTHON_EXTENSIONS_PATHS\n",
}
_CV2_CONFIG_CONTENT[f'config-{sys.version_info[0]}.{sys.version_info[1]}.py'] = (
    "PYTHON_EXTENSIONS_PATHS = [\n    LOADER_DIR\n] + PYTHON_EXTENSIONS_PATHS\n"
)

_original_open = builtins.open
_norm_cv2_dir = os.path.normpath(os.path.join(sys._MEIPASS, 'cv2')) if getattr(sys, 'frozen', False) else None

def _patched_open(file, mode='r', *args, **kwargs):
    if _norm_cv2_dir and isinstance(file, str) and 'r' in mode and 'b' not in mode:
        try:
            norm = os.path.normpath(file)
            if os.path.dirname(norm) == _norm_cv2_dir:
                basename = os.path.basename(norm)
                if basename in _CV2_CONFIG_CONTENT:
                    return io.StringIO(_CV2_CONFIG_CONTENT[basename])
        except Exception:
            pass
    return _original_open(file, mode, *args, **kwargs)

builtins.open = _patched_open
