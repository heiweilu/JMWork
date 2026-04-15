# -*- coding: utf-8 -*-
"""BUG 追踪 → MTK 问题跟踪记录页面（v2）

新增功能：
  1. 表列表头双击可修改名称，改名持久化到 JSON 配置
  2. 打开页面时自动后台扫描所有 MTK 问题单：
       - 分析最后活动日期 / Action Buttons 状态
       - 筛选"需要催促"的问题单（超过 N 天未回复且非 Reopen 状态）
       - 用状态过滤器快速查看
       - 可在工具栏设置催促阈值天数
"""

import json
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QFont, QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QMenu, QProgressBar, QPushButton,
    QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QWidget,
)

# ─────────────────── 持久化配置文件路径 ───────────────────────────────────────
_DATA_FILE = Path(__file__).parent.parent.parent / 'config' / 'bug_tracking_data.json'

_DEFAULT_HEADERS = ['平台', '问题描述', 'MTK链接', '飞书链接', '机型', '负责人', '备注/状态']
_DEFAULT_THRESHOLD = 7
_DEFAULT_CREDENTIALS = {"username": "app@xgimi.com", "password": "xgimi202508"}


# ─────────────────── 配置加载 / 保存 ─────────────────────────────────────────

def _load_config() -> dict:
    """加载完整配置；自动迁移旧格式（list-of-lists → dict 格式）。"""
    defaults: dict = {
        "headers":      list(_DEFAULT_HEADERS),
        "rows":         list(_RAW),
        "threshold_days": _DEFAULT_THRESHOLD,
        "credentials":  dict(_DEFAULT_CREDENTIALS),
        "scan_results": {},        # key = mtk_url
    }
    try:
        if _DATA_FILE.exists():
            with _DATA_FILE.open('r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                # 旧格式：直接是 list-of-list
                defaults["rows"] = [tuple(r) for r in data]
            elif isinstance(data, dict):
                defaults["headers"]        = data.get("headers", list(_DEFAULT_HEADERS))
                defaults["rows"]           = [tuple(r) for r in data.get("rows", list(_RAW))]
                defaults["threshold_days"] = data.get("threshold_days", _DEFAULT_THRESHOLD)
                defaults["credentials"]    = data.get("credentials", dict(_DEFAULT_CREDENTIALS))
                defaults["scan_results"]   = data.get("scan_results", {})
    except Exception:
        pass
    return defaults


def _save_config(headers: list, rows: list, threshold_days: int,
                 credentials: dict, scan_results: dict) -> None:
    """将完整配置保存到 JSON。"""
    try:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _DATA_FILE.open('w', encoding='utf-8') as f:
            json.dump(
                {
                    "version": 2,
                    "headers":       headers,
                    "rows":          [list(r) for r in rows],
                    "threshold_days": threshold_days,
                    "credentials":   credentials,
                    "scan_results":  scan_results,
                },
                f, ensure_ascii=False, indent=2,
            )
    except Exception:
        pass


# ─────────────────── 原始数据 ─────────────────────────────────────────────────
# 字段顺序: (平台, 问题描述, MTK链接, 飞书链接, 机型, 负责人, 备注)

def _u(raw: str) -> str:
    m = re.search(r'https?://\S+', raw)
    return m.group(0).rstrip('】').rstrip(']') if m else raw.strip()


_RAW: list = [
    # ── 9679R+ ──────────────────────────────────────────────────────────────
    ("9679R+", "蓝光3D播放切换3D模式画面闪屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143202022",
     "https://project.feishu.cn/6bxxuo/issue/detail/6665000706",
     "海外雅典娜", "王建", "极米端已经关闭该问题单，没有在复现该问题"),
    ("9679R+", "切换3D损失清晰度",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143167363",
     "https://project.feishu.cn/6bxxuo/issue/detail/6492320139",
     "海外雅典娜", "王建", "按照要求新建了CR"),
    ("9679R+", "切换左右3D转2D，画面会拉伸一下",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143157574",
     "https://project.feishu.cn/6bxxuo/issue/detail/6469928925",
     "海外雅典娜", "王建", "MTK回复：留意后续由 Wenyuan release 给我们的Google build 版本是否有OK"),
    ("9679R+", "PS4播放3D碟片，切换3D模式时右侧闪绿或彩色-205",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143096588",
     "https://project.feishu.cn/6bxxuo/issue/detail/6409667215",
     "海外雅典娜", "王建", "继续跟踪"),
    ("9679R+", "240HZ下，开关超码框压测；压测中关超码框时投影息屏后一直未亮-245",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143057789",
     "https://project.feishu.cn/6bxxuo/issue/detail/6409829261",
     "海外雅典娜", "王建", "MTK回复：待另外一道3D问题修复后再来解决此问题"),
    ("9679R+", "本地视频播放中，进行3D模式切换；出现投影卡死，无光无图情况-248",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143053244",
     "https://project.feishu.cn/6bxxuo/issue/detail/6409588789",
     "海外雅典娜", "王建", "未复现了，暂停跟踪"),
    ("9679R+", "偶现花屏问题",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143168418",
     "",
     "海外雅典娜", "王建", "待复现，暂停跟踪"),
    ("9679R+", "盒子帧率为50hz，播放24/30/50fps的3D片源并切换3D模式，画面抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143172043",
     "https://project.feishu.cn/6bxxuo/issue/detail/6509649179",
     "海外雅典娜", "方振", "此CR先挂起，后续DTV04802305处理完毕后，重新复测此CR，如果仍有问题则继续处理。"),
    ("9679R+", "PS4上蓝光3D画面有明显抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143162118",
     "https://project.feishu.cn/6bxxuo/issue/detail/6478297665",
     "海外雅典娜", "方振", "MTK回复：对该现象都没有改善效果"),

    # ── 9660R+ ──────────────────────────────────────────────────────────────
    ("9660R+", "屏保界面触发实时AK后底部闪烁",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143232278",
     "https://project.feishu.cn/6bxxuo/issue/detail/6776594490",
     "海外大鹏", "李梦江", "等待我们复测"),
    ("9660R+", "HDMI同屏画面，投影仪端画面字体有抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143231897",
     "https://project.feishu.cn/6bxxuo/issue/detail/6698731919",
     "海外猛禽", "李梦江", "继续跟踪"),
    ("9660R+", "游戏极速模式下，未作AK，遥控器移动系统设置菜单会出现setting花屏，home键回到桌面，桌面会出现撕裂花屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143222994",
     "https://project.feishu.cn/6bxxuo/issue/detail/6747099101",
     "海外猛禽", "李梦江", "最新提供的措施有效，未复现出问题，release的话，会在t-xgimi-apollo-mp-2103-refu-fy24h2v4-1783提供。"),
    ("9660R+", "开启梯形之后1080P和4K的机器延时不一样",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143219220",
     "",
     "海外猛禽", "陈旭东", "02-27 需要我们录制视频🎈🎈🎈"),
    ("9660R+", "梯形坐标设置为0之后，梯形还在运行",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143218326",
     "",
     "海外猛禽", "陈旭东", "3-02 这周等待release合入tag后，复测"),
    ("9660R+", "4K机型实时AK过程中，hwcomposer.merak出现崩溃",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143232113",
     "https://project.feishu.cn/6bxxuo/issue/detail/6773402960",
     "海外大鹏", "陈旭东", "3-05 验证了几十次，未复现，已反馈"),
    ("9660R+", "梯形坐标设置为0之后，梯形还在运行（国内）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143218326",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9660R+", "有梯形形变情况下，延时不达标",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143241494",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9660R+", "连接PC切换到HDR桌面字体抖动变严重（R+）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143243431",
     "",
     "海外大鹏", "陈旭东", "继续跟踪"),

    # ── 9681 ────────────────────────────────────────────────────────────────
    ("9681", "本地播放视频开启至臻120，画面噪点明显",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143199693",
     "https://project.feishu.cn/6bxxuo/issue/detail/6458866600",
     "国内雅典娜", "方振", "我们最新回复于2-11"),
    ("9681", "软梯下抠图防射眼/切换焦点时弹幕抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143221941",
     "https://project.feishu.cn/6bxxuo/issue/detail/6755751766",
     "国内雅典娜", "陈旭东", "继续跟踪"),
    ("9681", "开关防射眼之后弹幕抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143214120",
     "https://project.feishu.cn/6bxxuo/issue/detail/6702015503",
     "国内雅典娜", "陈旭东", "继续跟踪"),
    ("9681", "需要播放3D的时候，需要soc的3D sync信号给到后端",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143225483",
     "",
     "", "陈旭东", "年后跟踪"),
    ("9681", "当前需求支持动态切换到4k120的timing，如果配置panel路径呢",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143229977",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "从PS5切换到高帧率信号源，画面卡在PS5界面，一会闪退至桌面",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143170628",
     "https://project.feishu.cn/6bxxuo/issue/detail/6496753848",
     "", "陈旭东", "继续跟踪"),
    ("9681", "软梯开启VRR进入游戏会闪全屏花",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143169726",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "实时ak只有半屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143141868",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "软梯下1.5速度出现残影",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143126293",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "默认画面,播放同一个图片，9681比9679锯齿感严重",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143100011",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "软梯下切换至臻120，播放视频会闪屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143097596",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "游戏基础模式下有AK效果，切换VRR过程中移动机器触发位移AK，画面卡死，UI显示会错位",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143091605",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "偶现游戏基础模式下有AK，切换VRR过程中移动机器，会出现有光无图",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143091568",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "全民K歌过程中做避障AK，AK过程中抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143078465",
     "",
     "", "陈旭东", "继续跟踪"),
    ("9681", "连接PC切换到HDR桌面字体抖动变严重（9681）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143243444",
     "",
     "国内雅典娜", "陈旭东", "继续跟踪"),

    # ── 9660 ────────────────────────────────────────────────────────────────
    ("9660", "右下角往上调节后，会有garbage",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143227798",
     "",
     "国内猛禽", "陈旭东", "继续跟踪"),
    ("9660", "当前软梯框架实时ak怀疑会漏边",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143203291",
     "",
     "国内猛禽", "陈旭东", "继续跟踪"),
    ("9660", "软梯120的支持",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143211186",
     "",
     "国内猛禽", "陈旭东", "Resolved"),
    ("9660", "tag106合入后STR 花屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143226825",
     "",
     "", "陈旭东", "Resolved"),
    ("9660", "视频播放和HDMI播放都有文字闪烁问题",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143231897",
     "",
     "国内猛禽", "陈旭东", "继续跟踪"),
    ("9660", "巨幕模式有手动梯形点位下，退出重新播放时视频为黑屏",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143252967",
     "https://project.feishu.cn/6bxxuo/issue/detail/6849807846",
     "国内猛禽", "李梦江", "继续跟踪"),
    ("9660", "偶现STR之后，GOP2花屏（猛禽）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143253188",
     "https://project.feishu.cn/6bxxuo/issue/detail/6859105905",
     "国内猛禽", "陈旭东", "继续跟踪"),
    ("9660", "连接PC切换到HDR桌面字体抖动变严重（大鹏）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143258869",
     "",
     "国内大鹏", "李清龙", ""),
    ("9660", "偶现STR之后，GOP2花屏（大鹏）",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143262134",
     "",
     "国内大鹏", "陈旭东", ""),
    ("9660", "有AK数据下播放MEMC片源，画面抖动",
     "",
     "https://project.feishu.cn/6bxxuo/issue/detail/6921455665",
     "国内猛禽", "", ""),
    ("9660", "播放HDR视频，setting展示不完全",
     "",
     "https://project.feishu.cn/6bxxuo/issue/detail/6921553004",
     "国内猛禽", "", ""),
    ("9660", "打开MEMC，执行过AK后播放MEMC片源，画面抖动",
     "https://eservice.mediatek.com/eservice-portal/issue_manager/update/143271116",
     "https://project.feishu.cn/6bxxuo/issue/detail/6921455665",
     "国内猛禽", "李梦江", ""),
]


# ─────────────────── 颜色规则 ────────────────────────────────────────────────

_SCAN_FOLLOWUP_COLOR = QColor('#FFE0B2')  # 橙色 - 需要催促


def _row_color(notes: str) -> QColor | None:
    n = notes.lower()
    if 'resolved' in n:
        return QColor('#d4edda')   # 绿 - 已解决
    if '暂停跟踪' in n:
        return QColor('#e2e3e5')   # 灰 - 暂停
    if '未复现' in n:
        return QColor('#d1ecf1')   # 浅蓝 - 未复现
    if '继续跟踪' in n:
        return QColor('#fff3cd')   # 黄 - 跟踪中
    if '等待' in n or '复测' in n:
        return QColor('#cce5ff')   # 蓝 - 等待
    return None


# ─────────────────── 链接单元格 ──────────────────────────────────────────────

class _LinkItem(QTableWidgetItem):
    """存储 URL 的单元格，双击在浏览器中打开；编辑模式下才可编辑。"""
    def __init__(self, url: str):
        super().__init__(url or '')
        self.setData(Qt.ItemDataRole.ToolTipRole, url or '（空）')
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)

    @property
    def url(self) -> str:
        return self.text()


# ─────────────────── 页面主体 ────────────────────────────────────────────────

class MtkBugTrackingPage(QWidget):
    """MTK 问题跟踪记录表格页面（含 MTK 状态自动扫描）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        cfg = _load_config()
        self._columns: list         = cfg["headers"]
        self._all_data: list        = cfg["rows"]
        self._threshold_days: int   = cfg["threshold_days"]
        self._credentials: dict     = cfg["credentials"]
        self._scan_results: dict    = cfg["scan_results"]   # {mtk_url: result_dict}
        self._scan_worker           = None
        self._first_show: bool      = True
        self._displayed_data: list  = []
        self._setup_ui()
        self._populate()

    # ── 生命周期 ─────────────────────────────────────────────────────────────

    def showEvent(self, event):
        """页面第一次显示时自动触发 MTK 扫描。"""
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self._on_start_scan()

    # ── UI 搭建 ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(10)

        # ── 标题 ──
        title = QLabel("🐛  MTK 问题跟踪记录")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A237E;")
        root.addWidget(title)

        # ── 工具栏 第一行（搜索 / 过滤 / 编辑）──────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        lbl_search = QLabel("🔍 搜索:")
        lbl_search.setFixedWidth(52)
        self._search = QLineEdit()
        self._search.setPlaceholderText("问题描述 / 负责人 / 备注…")
        self._search.setStyleSheet(
            "QLineEdit{border:1px solid #C5CAE9;border-radius:5px;"
            "padding:4px 8px;font-size:13px;background:#FAFAFA;}")
        self._search.textChanged.connect(self._apply_filter)

        lbl_plat = QLabel("平台:")
        lbl_plat.setFixedWidth(36)
        self._combo_plat = QComboBox()
        self._combo_plat.addItem("全部平台")
        for p in ['9679R+', '9660R+', '9681', '9660']:
            self._combo_plat.addItem(p)
        self._combo_plat.currentTextChanged.connect(self._apply_filter)
        self._combo_plat.setFixedWidth(100)

        lbl_status = QLabel("状态:")
        lbl_status.setFixedWidth(36)
        self._combo_status = QComboBox()
        self._combo_status.addItems(
            ["全部状态", "🔴 需要催促", "继续跟踪", "Resolved", "暂停跟踪", "未复现", "等待/复测"]
        )
        self._combo_status.currentTextChanged.connect(self._apply_filter)
        self._combo_status.setFixedWidth(120)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color:#888;font-size:12px;")
        self._count_lbl.setFixedWidth(80)

        btn_add = QPushButton("➕ 新增行")
        btn_add.setFixedWidth(80)
        btn_add.setStyleSheet(
            "QPushButton{border:1px solid #81C784;border-radius:4px;"
            "padding:3px 6px;color:#2E7D32;background:#F1F8E9;}"
            "QPushButton:hover{background:#C8E6C9;}")
        btn_add.clicked.connect(self._on_add_row)

        btn_del = QPushButton("🗑 删除选中")
        btn_del.setFixedWidth(90)
        btn_del.setStyleSheet(
            "QPushButton{border:1px solid #E57373;border-radius:4px;"
            "padding:3px 6px;color:#C62828;background:#FFEBEE;}"
            "QPushButton:hover{background:#FFCDD2;}")
        btn_del.clicked.connect(self._on_delete_rows)

        self._btn_edit = QPushButton("✏️ 编辑")
        self._btn_edit.setFixedWidth(70)
        self._btn_edit.setCheckable(True)
        self._btn_edit.setStyleSheet(
            "QPushButton{border:1px solid #64B5F6;border-radius:4px;"
            "padding:3px 6px;color:#1565C0;background:#E3F2FD;}"
            "QPushButton:hover{background:#BBDEFB;}"
            "QPushButton:checked{background:#1565C0;color:white;}")
        self._btn_edit.toggled.connect(self._on_toggle_edit)

        bar.addWidget(lbl_search)
        bar.addWidget(self._search, stretch=1)
        bar.addWidget(lbl_plat)
        bar.addWidget(self._combo_plat)
        bar.addWidget(lbl_status)
        bar.addWidget(self._combo_status)
        bar.addWidget(self._count_lbl)
        bar.addWidget(btn_add)
        bar.addWidget(btn_del)
        bar.addWidget(self._btn_edit)
        root.addLayout(bar)

        # ── 工具栏 第二行（MTK 扫描控制）─────────────────────────────────────
        scan_bar = QHBoxLayout()
        scan_bar.setSpacing(8)

        scan_lbl = QLabel("⚡ MTK 自动扫描：")
        scan_lbl.setStyleSheet("font-weight:bold;color:#5C4033;font-size:12px;")
        scan_lbl.setFixedWidth(110)

        lbl_threshold = QLabel("催促阈值(天):")
        lbl_threshold.setStyleSheet("font-size:12px;color:#555;")
        lbl_threshold.setFixedWidth(85)

        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(1, 365)
        self._threshold_spin.setValue(self._threshold_days)
        self._threshold_spin.setSuffix(" 天")
        self._threshold_spin.setFixedWidth(72)
        self._threshold_spin.setToolTip("超过此天数且 Action Buttons 不含 Reopen Issue，则标记为需要催促")
        self._threshold_spin.valueChanged.connect(self._on_threshold_changed)

        self._btn_scan = QPushButton("🔍 立即扫描")
        self._btn_scan.setFixedWidth(90)
        self._btn_scan.setStyleSheet(
            "QPushButton{border:1px solid #FF8F00;border-radius:4px;"
            "padding:3px 8px;color:#E65100;background:#FFF8E1;font-weight:bold;}"
            "QPushButton:hover{background:#FFE0B2;}"
            "QPushButton:disabled{color:#aaa;background:#f5f5f5;border-color:#ddd;}")
        self._btn_scan.clicked.connect(self._on_start_scan)

        self._btn_stop_scan = QPushButton("⏹ 停止")
        self._btn_stop_scan.setFixedWidth(62)
        self._btn_stop_scan.setEnabled(False)
        self._btn_stop_scan.setStyleSheet(
            "QPushButton{border:1px solid #EF9A9A;border-radius:4px;"
            "padding:3px 6px;color:#B71C1C;background:#FFEBEE;}"
            "QPushButton:hover{background:#FFCDD2;}"
            "QPushButton:disabled{color:#aaa;background:#f5f5f5;border-color:#ddd;}")
        self._btn_stop_scan.clicked.connect(self._on_stop_scan)

        self._scan_progress = QProgressBar()
        self._scan_progress.setRange(0, 100)
        self._scan_progress.setValue(0)
        self._scan_progress.setFixedHeight(16)
        self._scan_progress.setFixedWidth(120)
        self._scan_progress.setVisible(False)
        self._scan_progress.setStyleSheet(
            "QProgressBar{border:1px solid #FFB300;border-radius:3px;background:#FFF8E1;}"
            "QProgressBar::chunk{background:#FF8F00;border-radius:3px;}")

        self._scan_status = QLabel("尚未扫描")
        self._scan_status.setStyleSheet("color:#888;font-size:11px;")

        scan_bar.addWidget(scan_lbl)
        scan_bar.addWidget(lbl_threshold)
        scan_bar.addWidget(self._threshold_spin)
        scan_bar.addWidget(self._btn_scan)
        scan_bar.addWidget(self._btn_stop_scan)
        scan_bar.addWidget(self._scan_progress)
        scan_bar.addWidget(self._scan_status, stretch=1)
        root.addLayout(scan_bar)

        # ── 表格 ─────────────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(self._columns))
        self._table.setHorizontalHeaderLabels(self._columns)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setStretchLastSection(True)
        hh.resizeSection(0, 70)
        hh.resizeSection(1, 280)
        hh.resizeSection(2, 160)
        hh.resizeSection(3, 160)
        hh.resizeSection(4, 90)
        hh.resizeSection(5, 70)
        # ★ 双击表头可修改列名
        hh.sectionDoubleClicked.connect(self._on_header_dbl_click)
        hh.setToolTip("双击表头可修改列名")

        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(False)
        self._table.setWordWrap(True)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #C5CAE9;
                border-radius: 4px;
                font-size: 12px;
                gridline-color: #E8EAF6;
            }
            QHeaderView::section {
                background: #E8EAF6;
                color: #283593;
                font-weight: bold;
                padding: 5px 8px;
                border: none;
                border-right: 1px solid #C5CAE9;
            }
            QHeaderView::section:hover {
                background: #C5CAE9;
                cursor: pointer;
            }
            QTableWidget::item { padding: 4px 6px; }
            QTableWidget::item:selected { background: #BBDEFB; color: #0D47A1; }
        """)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.itemChanged.connect(self._on_item_changed)
        root.addWidget(self._table)

        # ── 图例 ─────────────────────────────────────────────────────────────
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for color, text in [
            ('#FFE0B2', '需要催促 (MTK扫描)'),
            ('#d4edda', '已解决 (Resolved)'),
            ('#d1ecf1', '未复现'),
            ('#fff3cd', '继续跟踪'),
            ('#cce5ff', '等待/复测'),
            ('#e2e3e5', '暂停跟踪'),
        ]:
            dot = QLabel(
                f"<span style='background:{color};padding:3px 10px;"
                f"border:1px solid #bbb;border-radius:3px;'>&nbsp;</span> {text}"
            )
            dot.setStyleSheet("font-size:11px;color:#555;")
            legend.addWidget(dot)
        legend.addStretch()
        root.addLayout(legend)

    # ── 数据填充 ─────────────────────────────────────────────────────────────

    def _make_item(self, text: str, align_center: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if align_center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _populate(self, data=None):
        rows = data if data is not None else self._all_data
        self._displayed_data = list(rows)
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        self._table.setRowCount(len(rows))
        for r, (platform, desc, mtk, feishu, device, person, notes) in enumerate(rows):
            self._table.setItem(r, 0, self._make_item(platform, True))
            self._table.setItem(r, 1, self._make_item(desc))
            self._table.setItem(r, 2, _LinkItem(mtk))
            self._table.setItem(r, 3, _LinkItem(feishu))
            self._table.setItem(r, 4, self._make_item(device, True))
            self._table.setItem(r, 5, self._make_item(person, True))
            self._table.setItem(r, 6, self._make_item(notes))

            # 优先显示扫描结果颜色（橙色=需催促），其次按备注状态着色
            scan_res = self._scan_results.get(mtk, {}) if mtk else {}
            if scan_res.get("needs_followup"):
                color = _SCAN_FOLLOWUP_COLOR
                # 在备注列附加扫描摘要
                note_item = self._table.item(r, 6)
                if note_item:
                    days = scan_res.get("days_since_reply", -1)
                    last = scan_res.get("last_reply_date", "未知")
                    tip = f"⚠️ 需催促 | 最后活动：{last}（{days}天前）"
                    note_item.setToolTip(tip)
            else:
                color = _row_color(notes)

            if color:
                for c in range(len(self._columns)):
                    item = self._table.item(r, c)
                    if item:
                        item.setBackground(color)

        self._table.resizeRowsToContents()
        self._table.blockSignals(False)
        self._count_lbl.setText(f"共 {len(rows)} 条")

    # ── 过滤 ─────────────────────────────────────────────────────────────────

    def _apply_filter(self):
        query = self._search.text().strip().lower()
        plat = self._combo_plat.currentText()
        status = self._combo_status.currentText()

        def _match_status(row) -> bool:
            notes = row[6]
            n = notes.lower()
            mtk_url = row[2]
            if status == "全部状态":
                return True
            if status == "🔴 需要催促":
                return self._scan_results.get(mtk_url, {}).get("needs_followup", False)
            if status == "继续跟踪":
                return "继续跟踪" in n
            if status == "Resolved":
                return "resolved" in n
            if status == "暂停跟踪":
                return "暂停跟踪" in n
            if status == "未复现":
                return "未复现" in n
            if status == "等待/复测":
                return "等待" in n or "复测" in n
            return True

        filtered = [
            row for row in self._all_data
            if (plat == "全部平台" or row[0] == plat)
            and _match_status(row)
            and (not query or any(query in str(f).lower() for f in row))
        ]
        self._populate(filtered)

    # ── 表头双击修改列名 ──────────────────────────────────────────────────────

    def _on_header_dbl_click(self, section: int):
        """双击表头弹出输入框修改列名，修改后写入配置持久化。"""
        if section < 0 or section >= len(self._columns):
            return
        current_name = self._columns[section]
        new_name, ok = QInputDialog.getText(
            self,
            "修改列名",
            f"请输入第 {section + 1} 列的新名称：",
            text=current_name,
        )
        if ok and new_name.strip() and new_name.strip() != current_name:
            self._columns[section] = new_name.strip()
            self._table.setHorizontalHeaderLabels(self._columns)
            self._save()

    # ── 编辑模式切换 ─────────────────────────────────────────────────────────

    def _on_toggle_edit(self, checked: bool):
        for r in range(self._table.rowCount()):
            for c in (2, 3):
                item = self._table.item(r, c)
                if isinstance(item, _LinkItem):
                    flags = item.flags()
                    if checked:
                        item.setFlags(flags | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item.setFlags(flags & ~Qt.ItemFlag.ItemIsEditable)

    # ── 双击单元格打开链接 ────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, col: int):
        if col not in (2, 3):
            return
        item = self._table.item(row, col)
        if not item:
            return
        url = item.text().strip()
        if url.startswith('http'):
            QDesktopServices.openUrl(QUrl(url))

    # ── 右键菜单 ─────────────────────────────────────────────────────────────

    def _on_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        mtk_item   = self._table.item(row, 2)
        feishu_item = self._table.item(row, 3)
        mtk_url    = mtk_item.text().strip()   if mtk_item    else ''
        feishu_url = feishu_item.text().strip() if feishu_item else ''

        menu = QMenu(self)
        if mtk_url.startswith('http'):
            act = menu.addAction('🔗 打开 MTK 链接')
            act.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(mtk_url)))
        if feishu_url.startswith('http'):
            act = menu.addAction('🔗 打开飞书链接')
            act.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(feishu_url)))
        if not menu.isEmpty():
            menu.exec(self._table.viewport().mapToGlobal(pos))

    # ── 单元格编辑同步 ────────────────────────────────────────────────────────

    def _on_item_changed(self, item: QTableWidgetItem):
        row = self._table.row(item)

        def _get(c):
            it = self._table.item(row, c)
            return it.text() if it else ''

        new_row = tuple(_get(c) for c in range(len(self._columns)))
        if hasattr(self, '_displayed_data') and 0 <= row < len(self._displayed_data):
            orig = self._displayed_data[row]
            try:
                idx = self._all_data.index(orig)
                self._all_data[idx] = new_row
                self._displayed_data[row] = new_row
            except ValueError:
                pass
            self._save()

        if self._table.column(item) == 6:
            notes = item.text()
            mtk_url = (_get(2)) if True else ''
            scan_res = self._scan_results.get(mtk_url, {})
            color = (_SCAN_FOLLOWUP_COLOR if scan_res.get("needs_followup")
                     else _row_color(notes))
            self._table.blockSignals(True)
            for c in range(len(self._columns)):
                it = self._table.item(row, c)
                if it:
                    if color:
                        it.setBackground(color)
                    else:
                        it.setBackground(QColor(Qt.GlobalColor.white))
            self._table.blockSignals(False)

    # ── 新增行 ────────────────────────────────────────────────────────────────

    def _on_add_row(self):
        empty = ('', '', '', '', '', '', '')
        self._all_data.append(empty)
        self._populate_append_empty()

    def _populate_append_empty(self):
        r = self._table.rowCount()
        self._table.blockSignals(True)
        self._table.insertRow(r)
        empty = ('', '', '', '', '', '', '')
        for c, val in enumerate(empty):
            self._table.setItem(r, c, QTableWidgetItem(val))
        self._displayed_data.append(empty)
        self._table.blockSignals(False)
        self._save()
        self._table.scrollToBottom()
        self._table.setCurrentCell(r, 0)
        self._table.editItem(self._table.item(r, 0))
        self._count_lbl.setText(f'共 {self._table.rowCount()} 条')

    # ── 删除行 ────────────────────────────────────────────────────────────────

    def _on_delete_rows(self):
        rows = sorted(
            {idx.row() for idx in self._table.selectedIndexes()},
            reverse=True,
        )
        if not rows:
            return
        self._table.blockSignals(True)
        for r in rows:
            if hasattr(self, '_displayed_data') and 0 <= r < len(self._displayed_data):
                orig = self._displayed_data[r]
                try:
                    self._all_data.remove(orig)
                except ValueError:
                    pass
                self._displayed_data.pop(r)
            self._table.removeRow(r)
        self._table.blockSignals(False)
        self._save()
        self._count_lbl.setText(f'共 {self._table.rowCount()} 条')

    # ── 阈值变更 ──────────────────────────────────────────────────────────────

    def _on_threshold_changed(self, value: int):
        self._threshold_days = value
        self._save()

    # ── MTK 扫描 ──────────────────────────────────────────────────────────────

    def _on_start_scan(self):
        """启动 MTK 问题单后台扫描。"""
        from workers.mtk_scan_worker import MtkScanWorker

        if self._scan_worker and self._scan_worker.isRunning():
            return  # 正在扫描中，忽略重复点击

        # 收集所有有 MTK URL 的问题单
        issues = [
            (i, row[1], row[2])
            for i, row in enumerate(self._all_data)
            if row[2] and row[2].startswith('http')
        ]
        if not issues:
            self._scan_status.setText("没有可扫描的 MTK 链接")
            return

        self._scan_worker = MtkScanWorker(
            issues=issues,
            threshold_days=self._threshold_days,
            username=self._credentials.get("username", ""),
            password=self._credentials.get("password", ""),
            parent=self,
        )
        self._scan_worker.progress.connect(self._on_scan_progress_update)
        self._scan_worker.login_screenshot.connect(self._on_login_screenshot)
        self._scan_worker.scan_finished.connect(self._on_scan_finished)
        self._scan_worker.scan_error.connect(self._on_scan_error)

        self._btn_scan.setEnabled(False)
        self._btn_stop_scan.setEnabled(True)
        self._scan_progress.setVisible(True)
        self._scan_progress.setValue(0)
        self._scan_status.setText(f"正在启动（共 {len(issues)} 条，阈值 {self._threshold_days} 天）…")

        self._scan_worker.start()

    def _on_stop_scan(self):
        if self._scan_worker:
            self._scan_worker.request_stop()
            self._scan_status.setText("正在停止…")

    def _on_login_screenshot(self, png_bytes: bytes):
        """收到登录截图后弹出预览对话框，让用户确认登录状态。"""
        dlg = QDialog(self)
        dlg.setWindowTitle("MTK Portal 登录状态确认")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        dlg.resize(900, 620)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        tip = QLabel(
            "⬇ 以下是登录后的页面截图，请确认是否已成功登录 MTK eService Portal。\n"
            "若页面仍显示登录表单，说明账号密码有误；关闭此窗口后扫描将自动继续。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#5C4033;font-size:12px;")
        layout.addWidget(tip)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes, "PNG")
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(860, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(scaled)
        else:
            img_label.setText("（截图加载失败）")
        scroll.setWidget(img_label)
        layout.addWidget(scroll, stretch=1)

        btn_close = QPushButton("✅ 确认，继续扫描")
        btn_close.setStyleSheet(
            "QPushButton{border:1px solid #81C784;border-radius:4px;"
            "padding:4px 16px;color:#2E7D32;background:#F1F8E9;font-weight:bold;}"
            "QPushButton:hover{background:#C8E6C9;}"
        )
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        # 非阻塞展示，不影响后台扫描线程继续运行
        dlg.show()

    def _on_scan_progress_update(self, current: int, total: int, desc: str):
        pct = int(current / total * 100) if total else 0
        self._scan_progress.setValue(pct)
        self._scan_status.setText(f"扫描中 {current}/{total}：{desc}")

    def _on_scan_finished(self, results: dict):
        """扫描完成：按 row_idx 将结果写入 _scan_results（以 MTK URL 为键）。"""
        self._btn_scan.setEnabled(True)
        self._btn_stop_scan.setEnabled(False)
        self._scan_progress.setVisible(False)

        # 合并结果到 _scan_results {mtk_url: result}
        for row_idx, res in results.items():
            url = res.get("url", "")
            if url:
                self._scan_results[url] = res

        followup_count = sum(
            1 for r in self._scan_results.values() if r.get("needs_followup")
        )
        now_str = datetime.now().strftime("%H:%M:%S")
        if followup_count:
            self._scan_status.setText(
                f"✅ 扫描完成（{now_str}）— ⚠️ {followup_count} 条需要催促，"
                f"可在状态栏选择「🔴 需要催促」筛选"
            )
            self._scan_status.setStyleSheet("color:#E65100;font-size:11px;font-weight:bold;")
        else:
            self._scan_status.setText(f"✅ 扫描完成（{now_str}）— 暂无需催促问题单")
            self._scan_status.setStyleSheet("color:#2E7D32;font-size:11px;")

        self._save()
        self._apply_filter()  # 刷新高亮

    def _on_scan_error(self, msg: str):
        self._btn_scan.setEnabled(True)
        self._btn_stop_scan.setEnabled(False)
        self._scan_progress.setVisible(False)
        self._scan_status.setText(f"❌ 扫描失败：{msg[:80]}")
        self._scan_status.setStyleSheet("color:#C62828;font-size:11px;")

    # ── 统一保存 ─────────────────────────────────────────────────────────────

    def _save(self):
        """将当前所有配置持久化到 JSON。"""
        _save_config(
            headers=self._columns,
            rows=self._all_data,
            threshold_days=self._threshold_days,
            credentials=self._credentials,
            scan_results=self._scan_results,
        )
