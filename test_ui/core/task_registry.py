# -*- coding: utf-8 -*-
"""
任务注册表

自动发现并注册 modules/ 下的所有可执行模块。
每个模块通过 MODULE_INFO 字典声明元信息，由 UI 自动展示。
"""

import os
import importlib
import pkgutil
from typing import Dict, List, Optional, Any


# 模块注册表 {module_id: {"info": MODULE_INFO, "module": module_obj}}
_registry: Dict[str, dict] = {}


def register(module_id: str, module_info: dict, module_obj: Any):
    """手动注册一个模块"""
    _registry[module_id] = {
        "info": module_info,
        "module": module_obj,
    }


def auto_discover(package_path: str, package_name: str):
    """
    自动发现并注册指定包路径下的所有模块。

    扫描 package_path 下的所有 .py 文件，
    导入后检查是否具有 MODULE_INFO 和 run 函数。

    Args:
        package_path: 包的文件系统路径
        package_name: 包的 Python 导入名称（如 'modules.analysis'）
    """
    if not os.path.isdir(package_path):
        return

    for finder, name, ispkg in pkgutil.iter_modules([package_path]):
        if name.startswith('_'):
            continue
        full_name = f"{package_name}.{name}"
        try:
            mod = importlib.import_module(full_name)
            if hasattr(mod, 'MODULE_INFO') and hasattr(mod, 'run'):
                module_id = f"{mod.MODULE_INFO.get('category', 'unknown')}.{name}"
                register(module_id, mod.MODULE_INFO, mod)
        except Exception as e:
            print(f"[TaskRegistry] 模块 {full_name} 加载失败: {e}")


def discover_all():
    """发现所有模块（analysis, preprocessing, test）"""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'modules')
    for sub_pkg in ['analysis', 'preprocessing', 'test']:
        sub_path = os.path.join(base, sub_pkg)
        if os.path.isdir(sub_path):
            auto_discover(sub_path, f"modules.{sub_pkg}")


def get_modules(category: Optional[str] = None) -> Dict[str, dict]:
    """
    获取注册的模块。

    Args:
        category: 过滤类别（'analysis', 'preprocessing', 'test'）。
                  None 返回全部。

    Returns:
        {module_id: {"info": MODULE_INFO, "module": module_obj}}
    """
    if category is None:
        return dict(_registry)
    return {k: v for k, v in _registry.items()
            if v['info'].get('category') == category}


def get_module(module_id: str) -> Optional[dict]:
    """获取单个模块"""
    return _registry.get(module_id)


def get_module_names(category: Optional[str] = None) -> List[str]:
    """获取模块显示名称列表"""
    modules = get_modules(category)
    return [(mid, m['info']['name']) for mid, m in modules.items()]


def run_module(module_id: str,
               input_path: str,
               output_dir: str,
               params: dict,
               progress_callback=None,
               log_callback=None) -> dict:
    """
    执行指定模块的 run() 函数。

    Args:
        module_id: 模块 ID
        input_path: 输入文件/目录路径
        output_dir: 输出目录
        params: 参数字典
        progress_callback: 进度回调 (current, total)
        log_callback: 日志回调 (message, level)

    Returns:
        {"status": "success"/"error", "output_path": "...", "figure": fig, "message": "..."}
    """
    entry = _registry.get(module_id)
    if entry is None:
        return {"status": "error", "message": f"未找到模块: {module_id}"}

    mod = entry['module']
    try:
        result = mod.run(
            input_path=input_path,
            output_dir=output_dir,
            params=params,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
        return result
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"模块执行异常: {e}\n{traceback.format_exc()}",
        }
