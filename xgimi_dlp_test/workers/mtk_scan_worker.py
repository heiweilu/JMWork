# -*- coding: utf-8 -*-
"""
MTK eService 问题单状态爬取 Worker

使用 Playwright 登录 MTK portal，逐个爬取问题单页面，
解析最后回复时间和 Action Buttons 状态，筛选需要催促的问题单。

需要催促的条件：
  1. 距离最后回复时间超过 threshold_days 天
  2. Action Buttons 中 **没有** "Reopen Issue"（有 Reopen 说明 MTK 已处理/关闭，轮到我们行动）
"""

import re
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QThread, pyqtSignal


class MtkScanWorker(QThread):
    """
    后台线程：爬取所有 MTK 问题单状态。

    Signals:
        progress(int, int, str)    -- (已完成数, 总数, 当前问题描述前40字)
        login_screenshot(bytes)    -- 登录完成后的页面截图（PNG bytes），用于 UI 预览确认
        scan_finished(dict)        -- key=row_idx(int), value=结果字典
        scan_error(str)            -- 错误信息（登录失败/import失败/全局异常）
    """

    progress = pyqtSignal(int, int, str)
    login_screenshot = pyqtSignal(bytes)   # ← 新增：截图数据
    scan_finished = pyqtSignal(dict)
    scan_error = pyqtSignal(str)

    MTK_BASE = "https://eservice.mediatek.com/eservice-portal/"

    def __init__(
        self,
        issues: List[Tuple],   # [(row_idx, desc, mtk_url), ...]
        threshold_days: int,
        username: str,
        password: str,
        parent=None,
    ):
        super().__init__(parent)
        self._issues = issues
        self._threshold = threshold_days
        self._username = username
        self._password = password
        self._stop_requested = False

    # ── 公共接口 ──────────────────────────────────────────────────────────────

    def request_stop(self):
        """请求提前停止扫描。"""
        self._stop_requested = True

    # ── 线程主体 ──────────────────────────────────────────────────────────────

    def run(self):
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as _PwTimeout
        except ImportError:
            self.scan_error.emit(
                "未安装 playwright，请在终端依次执行：\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )
            return

        results: Dict[int, dict] = {}
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                page = ctx.new_page()

                # ── 登录 ──────────────────────────────────────────────────
                if not self._login(page, _PwTimeout):
                    self.scan_error.emit(
                        "MTK portal 登录失败，请检查账号密码或网络连接。\n"
                        f"账号：{self._username}"
                    )
                    browser.close()
                    return

                # ── 登录后截图，回传主线程供用户确认 ─────────────────────
                try:
                    screenshot_bytes = page.screenshot(type="png", full_page=False)
                    self.login_screenshot.emit(screenshot_bytes)
                except Exception:
                    pass  # 截图失败不影响扫描继续

                total = len(self._issues)
                for idx, (row_idx, desc, mtk_url) in enumerate(self._issues):
                    if self._stop_requested:
                        break

                    self.progress.emit(idx + 1, total, (desc or "")[:40])

                    if not mtk_url or not mtk_url.startswith("http"):
                        results[row_idx] = _no_url_result(mtk_url)
                        continue

                    try:
                        info = self._parse_issue(page, mtk_url, _PwTimeout)
                        days = info.get("days_since_reply", -1)
                        action = info.get("action_status", "unknown")
                        # 需要催促：超阈值 AND 不是 reopen 状态
                        info["needs_followup"] = (
                            days != -1
                            and days >= self._threshold
                            and action != "reopen"
                        )
                        results[row_idx] = info
                    except Exception as exc:
                        results[row_idx] = _error_result(mtk_url, str(exc))

                browser.close()

        except Exception as exc:
            self.scan_error.emit(f"扫描过程出现异常：{exc}\n{traceback.format_exc()}")
            return

        self.scan_finished.emit(results)

    # ── 登录逻辑 ──────────────────────────────────────────────────────────────

    def _login(self, page, _PwTimeout) -> bool:
        """尝试登录 MTK eService portal，返回是否成功。"""
        try:
            page.goto(self.MTK_BASE, timeout=30_000, wait_until="domcontentloaded")

            # 如果不在登录页，说明已经有 session 或直接到达主页
            if not _is_login_page(page):
                return True

            # 填用户名
            for sel in [
                'input[name="username"]', 'input[name="user"]',
                'input[type="email"]',    'input[id*="user" i]',
                'input[placeholder*="user" i]', 'input[placeholder*="email" i]',
            ]:
                if page.locator(sel).count():
                    page.fill(sel, self._username)
                    break

            # 填密码
            for sel in [
                'input[name="password"]', 'input[type="password"]',
                'input[id*="pass" i]',
            ]:
                if page.locator(sel).count():
                    page.fill(sel, self._password)
                    break

            # 点登录按钮
            for sel in [
                'button[type="submit"]', 'input[type="submit"]',
                'button:has-text("Log")', 'button:has-text("Sign")',
                'button:has-text("Login")', 'button:has-text("登录")',
                'a:has-text("Login")',
            ]:
                if page.locator(sel).count():
                    page.click(sel)
                    break

            page.wait_for_load_state("networkidle", timeout=20_000)
            return not _is_login_page(page)

        except Exception:
            return False

    # ── 解析单个问题单页面 ────────────────────────────────────────────────────

    def _parse_issue(self, page, url: str, _PwTimeout) -> dict:
        """访问问题单 URL，解析最后活动日期和 Action Buttons 状态。"""
        page.goto(url, timeout=30_000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:
            pass  # 允许部分超时，继续解析已加载内容

        html = page.content()

        # ── Action Buttons：检测 "Reopen Issue" ──────────────────────────
        has_reopen = bool(re.search(r"reopen\s*issue", html, re.I))
        if not has_reopen:
            for sel in ["button", "a", '[class*="btn"]', '[class*="action"]']:
                for el in page.locator(sel).all():
                    try:
                        if "reopen" in el.inner_text().strip().lower():
                            has_reopen = True
                            break
                    except Exception:
                        continue
                if has_reopen:
                    break

        # ── 提取页面中所有日期时间字符串，取最新一条作为"最后活动时间" ──────
        parsed_dates = _extract_dates(html)
        last_date: Optional[datetime] = max(parsed_dates) if parsed_dates else None

        return {
            "url": url,
            "last_reply_date": last_date.strftime("%Y-%m-%d") if last_date else "未知",
            "days_since_reply": (datetime.now() - last_date).days if last_date else -1,
            "action_status": "reopen" if has_reopen else "pending",
            "needs_followup": False,   # 由 run() 计算覆盖
            "error": "",
        }


# ── 模块级工具函数 ────────────────────────────────────────────────────────────

def _is_login_page(page) -> bool:
    url = page.url.lower()
    return "login" in url or "signin" in url or "sign_in" in url


def _extract_dates(html: str) -> List[datetime]:
    """从 HTML 文本中提取所有日期时间，返回解析后的 datetime 列表。"""
    patterns_fmts = [
        (r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]),
        (r"\d{4}/\d{2}/\d{2}[T ]\d{2}:\d{2}:\d{2}", ["%Y/%m/%d %H:%M:%S", "%Y/%m/%dT%H:%M:%S"]),
        (r"\d{4}-\d{2}-\d{2}", ["%Y-%m-%d"]),
        (r"\d{4}/\d{2}/\d{2}", ["%Y/%m/%d"]),
    ]
    result = []
    for pattern, fmts in patterns_fmts:
        for match in re.findall(pattern, html):
            for fmt in fmts:
                try:
                    result.append(datetime.strptime(match.strip(), fmt))
                    break
                except ValueError:
                    continue
    return result


def _no_url_result(url: str) -> dict:
    return {
        "url": url or "",
        "last_reply_date": "N/A",
        "days_since_reply": -1,
        "action_status": "unknown",
        "needs_followup": False,
        "error": "无MTK链接，跳过",
    }


def _error_result(url: str, reason: str) -> dict:
    return {
        "url": url or "",
        "last_reply_date": "错误",
        "days_since_reply": -1,
        "action_status": "unknown",
        "needs_followup": False,
        "error": reason,
    }
