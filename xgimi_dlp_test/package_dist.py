# -*- coding: utf-8 -*-
"""
分发打包脚本：将 xgimi_dlp_test 清理并复制到分发目录。

移除：系统管理、串口调试、日志定位、管理员控制台
清理：敏感配置信息（API Key、密码、个人路径）
"""

import json
import os
import re
import shutil
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = r"D:\software\heiweilu\test\2026\5\0513\xgimi_dlp_test_public"

# ───────── 排除规则 ─────────
EXCLUDE_DIRS = {
    ".github", ".vscode", ".wolf",
    "data", "logs", "reports", "output",
    "build", "dist",
    "__pycache__",
    os.path.join("assets", "Angle_data"),
    os.path.join("assets", "firmware"),
    os.path.join("assets", "doc"),
}

EXCLUDE_FILES = {
    "test_log_locator_temp.py",
    "package_dist.py",                          # 本脚本自身
    os.path.join("ui", "pages", "serial_page.py"),
    os.path.join("ui", "pages", "log_locator_page.py"),
    os.path.join("ui", "pages", "config_page.py"),
    os.path.join("ui", "pages", "history_page.py"),
    os.path.join("ui", "pages", "docs_page.py"),
    os.path.join("ui", "dialogs", "admin_console_dialog.py"),
    os.path.join("core", "admin_console_store.py"),
    os.path.join("config", "admin_console.json"),
    os.path.join("config", "bug_tracking_data.json"),
    os.path.join("config", "device_lab_profile.json"),  # 含个人调试命令，替换为空模板
    os.path.join("config", "user_config.json"),          # 含本机路径，替换为空模板
}


def _should_exclude(rel_path: str) -> bool:
    rel_path = rel_path.replace("\\", "/")
    # Any path segment named __pycache__
    if "__pycache__" in rel_path.split("/"):
        return True
    for d in EXCLUDE_DIRS:
        d_norm = d.replace("\\", "/")
        if rel_path == d_norm or rel_path.startswith(d_norm + "/"):
            return True
    for f in EXCLUDE_FILES:
        if rel_path == f.replace("\\", "/"):
            return True
    return False


# ───────── 文件复制 ─────────
def copy_tree(src: str, dst: str):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(src):
        rel_dir = os.path.relpath(dirpath, src)
        if rel_dir == ".":
            rel_dir = ""

        if _should_exclude(rel_dir):
            dirnames.clear()
            continue

        # 过滤子目录
        dirnames[:] = [
            d for d in dirnames
            if not _should_exclude(os.path.join(rel_dir, d) if rel_dir else d)
        ]

        target_dir = os.path.join(dst, rel_dir) if rel_dir else dst
        os.makedirs(target_dir, exist_ok=True)

        for fname in filenames:
            rel_file = os.path.join(rel_dir, fname) if rel_dir else fname
            if _should_exclude(rel_file):
                print(f"  [SKIP] {rel_file}")
                continue
            shutil.copy2(os.path.join(dirpath, fname), os.path.join(target_dir, fname))

    print(f"[DONE] 文件复制完成 → {dst}")


# ───────── patch: main_window.py ─────────
NEW_MAIN_WINDOW_HEADER = '''\
# -*- coding: utf-8 -*-
"""
主窗口（分发版 — 已移除：系统管理 / 串口调试 / 日志定位 / 管理员控制台）
"""

import os

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QTreeWidget, QTreeWidgetItem, QStackedWidget,
                              QSplitter, QStatusBar, QFrame,
                              QLabel, QPushButton, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from ui.styles import MAIN_STYLE
from ui.widgets.log_panel import LogPanel
from ui.widgets.progress_bar import ProgressWidget
from ui.pages.analysis_page import AnalysisPage
from ui.pages.preprocessing_page import PreprocessingPage
from ui.pages.test_page import TestPage
from ui.pages.bug_tracking_page import MtkBugTrackingPage
from ui.pages.device_lab_page import DeviceLabPage
from ui.pages.ai_settings_page import AISettingsPage
from ui.widgets.ai_chat_panel import AIChatPanel
from core.app_meta import APP_NAME, APP_SIGNATURE, APP_VERSION, full_app_title
from core.config_manager import ConfigManager
from ui.animations import UIAnimator, TypewriterEffect, NeonPulse


# 导航项定义
NAV_ITEMS = [
    {"name": "数据预处理", "icon": "📁", "enabled": True},
    {"name": "分析执行",   "icon": "📊", "enabled": True},
    {"name": "SVM训练",     "icon": "🤖", "enabled": True},
    {"name": "设备联调台", "icon": "🎛", "enabled": True},
    {"name": "硬件测试",   "icon": "🔧", "enabled": True},
    {"name": "MTK问题跟踪", "icon": "🐛", "enabled": True},
    {"name": "AI 助手",    "icon": "🧠", "enabled": True},
]

NAV_GROUPS = [
    ("数据处理",  ["数据预处理", "分析执行", "SVM训练"]),
    ("设备工作台", ["设备联调台", "硬件测试"]),
    ("BUG追踪",   ["MTK问题跟踪"]),
    ("AI",        ["AI 助手"]),
]

'''

NEW_INIT_UI_PAGES = '''\
        # 创建各页面
        self.analysis_page = AnalysisPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)
        self.svm_page = AnalysisPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr,
            category='svm')
        self.preprocessing_page = PreprocessingPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)
        self.test_page = TestPage(
            log_panel=self.log_panel,
            config_mgr=self._config_mgr)

        self.page_stack.addWidget(self.preprocessing_page)
        self.page_stack.addWidget(self.analysis_page)
        self.page_stack.addWidget(self.svm_page)
        self.device_lab_page = DeviceLabPage(
            config_mgr=self._config_mgr,
            log_panel=self.log_panel,
        )
        self.page_stack.addWidget(self.device_lab_page)
        self.page_stack.addWidget(self.test_page)
        self.bug_tracking_page = MtkBugTrackingPage()
        self.page_stack.addWidget(self.bug_tracking_page)
        self.ai_settings_page = AISettingsPage(
            config_mgr=self._config_mgr,
            log_panel=self.log_panel,
        )
        self.page_stack.addWidget(self.ai_settings_page)
        # 预处理页信号
        self.preprocessing_page.import_to_test.connect(self._on_import_to_test)
        self.analysis_page.send_to_preprocessing.connect(self._on_send_to_preprocess_expand)
        self.analysis_page.send_to_svm.connect(self._on_send_to_svm)
        self.analysis_page.send_to_angle_test.connect(self._on_send_to_angle_test)
'''


def patch_main_window(dest_path: str):
    """重写 ui/main_window.py 的 imports / NAV / 页面部分。"""
    path = os.path.join(dest_path, "ui", "main_window.py")
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    # ── 1. 替换 header（到 class MainWindow 之前）
    class_marker = "\nclass MainWindow(QMainWindow):"
    cls_idx = src.index(class_marker)
    src = NEW_MAIN_WINDOW_HEADER + src[cls_idx:]

    # ── 2. 移除 _admin_store 初始化
    src = re.sub(
        r"        self\._admin_store = AdminConsoleStore\([^)]+\)\n",
        "",
        src,
    )

    # ── 3. 移除管理员控制台按钮及其信号连接
    src = re.sub(
        r"        self\._btn_admin_console = QPushButton\('管理员控制台'\)\n"
        r"        self\._btn_admin_console\.clicked\.connect\(self\._open_admin_console\)\n",
        "",
        src,
    )
    src = re.sub(
        r"        header_layout\.addWidget\(self\._btn_admin_console\)\n",
        "",
        src,
    )

    # ── 4. 替换"创建各页面"到 splitter.addWidget 之前的代码段
    create_pages_marker = "        # 创建各页面"
    splitter_add_marker = "        self.splitter.addWidget(self.page_stack_container)"
    cp_idx = src.index(create_pages_marker)
    sa_idx = src.index(splitter_add_marker)
    src = src[:cp_idx] + NEW_INIT_UI_PAGES + src[sa_idx:]

    # ── 5. 移除 _refresh_app_meta_ui 中对 email 的引用
    src = src.replace(
        "        if hasattr(self, '_header_meta'):\n"
        "            self._header_meta.setText(f'{version} | {APP_SIGNATURE} | {email}')\n"
        "        if hasattr(self, '_status_app_meta'):\n"
        "            self._status_app_meta.setText(f'{APP_NAME} {version} | {APP_SIGNATURE} | {email}')\n",
        "        if hasattr(self, '_header_meta'):\n"
        "            self._header_meta.setText(f'{version} | {APP_SIGNATURE}')\n"
        "        if hasattr(self, '_status_app_meta'):\n"
        "            self._status_app_meta.setText(f'{APP_NAME} {version} | {APP_SIGNATURE}')\n",
    )
    # Remove email retrieval
    src = src.replace(
        "    def _current_author_email(self) -> str:\n"
        "        return self._admin_store.get_author_email() or APP_AUTHOR_EMAIL\n",
        "",
    )
    src = src.replace(
        "    def _current_app_version(self) -> str:\n"
        "        return self._admin_store.get_app_version() or APP_VERSION\n",
        "    def _current_app_version(self) -> str:\n"
        "        return APP_VERSION\n",
    )
    src = src.replace(
        "        version = self._current_app_version()\n"
        "        email = self._current_author_email()\n"
        "        self.setWindowTitle(f'{APP_NAME} {version} {APP_SIGNATURE}')\n",
        "        version = self._current_app_version()\n"
        "        self.setWindowTitle(f'{APP_NAME} {version} {APP_SIGNATURE}')\n",
    )

    # ── 6. 移除 _open_admin_console 方法
    src = re.sub(
        r"    def _open_admin_console\(self\):.*?(?=\n    def |\Z)",
        "",
        src,
        flags=re.DOTALL,
    )

    # ── 7. 移除 docs_page 相关引用（admin console 里用到了 self.docs_page）
    src = re.sub(r"        self\.docs_page\.refresh_docs\(\)\n", "", src)

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("[PATCH] ui/main_window.py")


# ───────── patch: core/app_meta.py ─────────
def patch_app_meta(dest_path: str):
    path = os.path.join(dest_path, "core", "app_meta.py")
    content = (
        "# -*- coding: utf-8 -*-\n"
        '"""应用元信息。"""\n\n'
        "APP_NAME = 'DLP 自动化测试系统'\n"
        "APP_VERSION = 'v0.1.7'\n"
        "APP_SIGNATURE = ''\n"
        "APP_AUTHOR_EMAIL = ''\n"
        "DEFAULT_ADMIN_PASSWORD = ''\n"
        "\n\n"
        "def full_app_title() -> str:\n"
        "    return f'{APP_NAME} {APP_VERSION}'.strip()\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[PATCH] core/app_meta.py")


# ───────── patch: config files ─────────
def patch_configs(dest_path: str):
    cfg = os.path.join(dest_path, "config")

    # ai_config.json — 清空凭证，保留结构
    ai_cfg = {
        "ai": {
            "api_key": "",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen3.5-flash",
            "max_tokens": 2048,
            "temperature": 0.7
        },
        "feishu": {
            "webhook_url": "",
            "webhook_secret": "",
            "app_id": "",
            "app_secret": "",
            "default_chat_id": "",
            "prefer_mode": "openapi"
        },
        "notification_rules": {
            "use_ai_summary": True,
            "include_logs": True,
            "notify_on_finish": False,
            "max_log_lines": 29
        }
    }
    with open(os.path.join(cfg, "ai_config.json"), "w", encoding="utf-8") as f:
        json.dump(ai_cfg, f, ensure_ascii=False, indent=2)
    print("[PATCH] config/ai_config.json")

    # default_config.json — 清空 project_root
    dc_path = os.path.join(cfg, "default_config.json")
    with open(dc_path, "r", encoding="utf-8") as f:
        dc = json.load(f)
    dc["general"]["project_root"] = ""
    with open(dc_path, "w", encoding="utf-8") as f:
        json.dump(dc, f, ensure_ascii=False, indent=2)
    print("[PATCH] config/default_config.json")

    # user_config.json — 空对象
    with open(os.path.join(cfg, "user_config.json"), "w", encoding="utf-8") as f:
        f.write("{}\n")
    print("[PATCH] config/user_config.json (reset to empty)")

    # device_lab_profile.json — 最小空模板
    dlab = {"last_port": "", "camera_index": 0, "scripts": [], "quick_cmds": []}
    with open(os.path.join(cfg, "device_lab_profile.json"), "w", encoding="utf-8") as f:
        json.dump(dlab, f, ensure_ascii=False, indent=2)
    print("[PATCH] config/device_lab_profile.json (reset to empty template)")

    # requirements.txt — replace Chinese comments (pip on Windows GBK can't parse them)
    req_path = os.path.join(dest_path, "requirements.txt")
    with open(req_path, "r", encoding="utf-8") as f:
        req = f.read()
    req = req.replace("# AI + 飞书集成", "# AI + Feishu integration")
    req = req.replace("# Playwright 自动化浏览器（MTK 问题单状态扫描）", "# Playwright browser automation (MTK bug tracking)")
    req = req.replace("# 安装后还需执行：playwright install chromium", "# After install run: playwright install chromium")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(req)
    print("[PATCH] requirements.txt (Chinese comments -> English)")


# ───────── 创建空占位目录 ─────────
def create_placeholder_dirs(dest_path: str):
    for d in ["data", "logs", "reports", "output"]:
        dp = os.path.join(dest_path, d)
        os.makedirs(dp, exist_ok=True)
        gitkeep = os.path.join(dp, ".gitkeep")
        if not os.path.exists(gitkeep):
            open(gitkeep, "w").close()
    print("[DONE] 占位目录创建完成")


# ───────── 主流程 ─────────
def main():
    print(f"源目录: {SRC_DIR}")
    print(f"目标目录: {DEST_DIR}")
    print()

    print("Step 1: 复制文件...")
    copy_tree(SRC_DIR, DEST_DIR)

    print("\nStep 2: 修补源码...")
    patch_main_window(DEST_DIR)
    patch_app_meta(DEST_DIR)

    print("\nStep 3: 清理配置文件...")
    patch_configs(DEST_DIR)

    print("\nStep 4: 创建占位目录...")
    create_placeholder_dirs(DEST_DIR)

    print("\n" + "=" * 60)
    print("打包完成！")
    print(f"   分发目录: {DEST_DIR}")
    print()
    print("后续步骤（在分发目录下执行）:")
    print("  1. pip install -r requirements.txt")
    print("  2. 运行 build_exe.bat 生成 EXE")
    print("=" * 60)


if __name__ == "__main__":
    main()
