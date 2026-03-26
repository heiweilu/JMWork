# -*- coding: utf-8 -*-
"""BUG 追踪 → MTK 问题跟踪记录页面"""

import json
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QAbstractItemView, QComboBox, QPushButton,
    QApplication, QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QDesktopServices
from PyQt6.QtCore import QUrl

# 持久化文件路径（xgimi_dlp_test/config/bug_tracking_data.json）
_DATA_FILE = Path(__file__).parent.parent.parent / 'config' / 'bug_tracking_data.json'


def _load_data() -> list:
    """从 JSON 文件加载数据，失败则回退使用 _RAW。"""
    try:
        if _DATA_FILE.exists():
            with _DATA_FILE.open('r', encoding='utf-8') as f:
                rows = json.load(f)
            # JSON 里是 list-of-list，转为 list-of-tuple
            return [tuple(r) for r in rows]
    except Exception:
        pass
    return list(_RAW)


def _save_data(data: list) -> None:
    """将当前数据保存到 JSON 文件。"""
    try:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _DATA_FILE.open('w', encoding='utf-8') as f:
            json.dump([list(r) for r in data], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ─────────────────── 原始数据 ─────────────────────────────────────────────────
# 字段顺序: (平台, 问题描述, MTK链接, 飞书链接, 机型, 负责人, 备注)

def _u(raw: str) -> str:
    """从可能含额外说明文字的字符串中提取第一个 URL（http 开头），如无则返回原字符串。"""
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

def _row_color(notes: str) -> QColor | None:
    n = notes.lower()
    if 'resolved' in n:
        return QColor('#d4edda')   # 绿色 - 已解决
    if '暂停跟踪' in n:
        return QColor('#e2e3e5')   # 灰色 - 暂停
    if '未复现' in n:
        return QColor('#d1ecf1')   # 浅蓝 - 未复现
    if '继续跟踪' in n:
        return QColor('#fff3cd')   # 黄 - 跟踪中
    if '等待' in n or '复测' in n:
        return QColor('#cce5ff')   # 蓝 - 等待
    return None


# ─────────────────── 表格单元格（可点击链接）────────────────────────────────

class _LinkItem(QTableWidgetItem):
    """存储 URL 的单元格，双击在浏览器中打开；需通过编辑按钮才能编辑。"""
    def __init__(self, url: str):
        super().__init__(url or '')
        self.setData(Qt.ItemDataRole.ToolTipRole, url or '（空）')
        # 默认不可编辑，防止双击进入编辑模式
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)

    @property
    def url(self) -> str:
        return self.text()


# ─────────────────── 页面 ────────────────────────────────────────────────────

class MtkBugTrackingPage(QWidget):
    """MTK 问题跟踪记录表格页面"""

    COLUMNS = ['平台', '问题描述', 'MTK链接', '飞书链接', '机型', '负责人', '备注/状态']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_data = _load_data()
        self._setup_ui()
        self._populate()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(10)

        # ── 标题 ──
        title = QLabel("🐛  MTK 问题跟踪记录")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A237E;")
        root.addWidget(title)

        # ── 工具栏 ──
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
        self._combo_status.addItems(["全部状态", "继续跟踪", "Resolved", "暂停跟踪", "未复现", "等待/复测"])
        self._combo_status.currentTextChanged.connect(self._apply_filter)
        self._combo_status.setFixedWidth(110)

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

        # ── 表格 ──
        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # 所有列均可拖拽调整宽度
        hh.setStretchLastSection(True)  # 最后一列自动拉伸填满
        # 设置初始合理列宽
        hh.resizeSection(0, 70)    # 平台
        hh.resizeSection(1, 280)   # 描述
        hh.resizeSection(2, 160)   # MTK链接
        hh.resizeSection(3, 160)   # 飞书链接
        hh.resizeSection(4, 90)    # 机型
        hh.resizeSection(5, 70)    # 负责人
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(False)  # 我们自己控制颜色
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
            QTableWidget::item { padding: 4px 6px; }
            QTableWidget::item:selected { background: #BBDEFB; color: #0D47A1; }
        """)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.itemChanged.connect(self._on_item_changed)
        root.addWidget(self._table)

        # ── 图例 ──
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for color, text in [
            ('#d4edda', '已解决 (Resolved)'),
            ('#d1ecf1', '未复现'),
            ('#fff3cd', '继续跟踪'),
            ('#cce5ff', '等待/复测'),
            ('#e2e3e5', '暂停跟踪'),
        ]:
            dot = QLabel(f"<span style='background:{color};padding:3px 10px;"
                         f"border:1px solid #bbb;border-radius:3px;'>&nbsp;</span> {text}")
            dot.setStyleSheet("font-size:11px;color:#555;")
            legend.addWidget(dot)
        legend.addStretch()
        root.addLayout(legend)

    def _make_item(self, text: str, align_center: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if align_center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        # 普通单元格允许编辑（链接单元格在 _LinkItem 中单独设置为不可编辑）
        return item

    def _populate(self, data=None):
        rows = data if data is not None else self._all_data
        self._displayed_data = list(rows)   # 记录当前视图行对应的原始数据
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

            color = _row_color(notes)
            if color:
                for c in range(len(self.COLUMNS)):
                    item = self._table.item(r, c)
                    if item:
                        item.setBackground(color)

        self._table.resizeRowsToContents()
        self._table.blockSignals(False)
        self._count_lbl.setText(f"共 {len(rows)} 条")

    def _apply_filter(self):
        query = self._search.text().strip().lower()
        plat = self._combo_plat.currentText()
        status = self._combo_status.currentText()

        def _match_status(notes: str) -> bool:
            n = notes.lower()
            if status == "全部状态":
                return True
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
            and _match_status(row[6])
            and (not query or any(query in str(f).lower() for f in row))
        ]
        self._populate(filtered)

    def _on_toggle_edit(self, checked: bool):
        """切换编辑模式：开启时链接单元格可编辑，关闭时恢复为不可编辑。"""
        for r in range(self._table.rowCount()):
            for c in (2, 3):  # MTK链接、飞书链接列
                item = self._table.item(r, c)
                if isinstance(item, _LinkItem):
                    flags = item.flags()
                    if checked:
                        item.setFlags(flags | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item.setFlags(flags & ~Qt.ItemFlag.ItemIsEditable)

    def _on_cell_double_clicked(self, row: int, col: int):
        """双击链接列时在浏览器中打开 URL（非编辑模式下）。"""
        if col not in (2, 3):
            return
        item = self._table.item(row, col)
        if not item:
            return
        url = item.text().strip()
        if url.startswith('http'):
            QDesktopServices.openUrl(QUrl(url))

    def _on_context_menu(self, pos):
        """右键菜单：在浏览器中打开 MTK / 飞书 链接。"""
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        mtk_item = self._table.item(row, 2)
        feishu_item = self._table.item(row, 3)
        mtk_url = mtk_item.text().strip() if mtk_item else ''
        feishu_url = feishu_item.text().strip() if feishu_item else ''

        menu = QMenu(self)
        if mtk_url.startswith('http'):
            act_mtk = menu.addAction('🔗 打开 MTK 链接')
            act_mtk.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(mtk_url)))
        if feishu_url.startswith('http'):
            act_fs = menu.addAction('🔗 打开飞书链接')
            act_fs.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(feishu_url)))
        if not menu.isEmpty():
            menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_item_changed(self, item: QTableWidgetItem):
        """将表格单元格的编辑内容同步回 _all_data，确保过滤时使用最新值。"""
        row = self._table.row(item)
        # 重建该行为 tuple
        def _get(c):
            it = self._table.item(row, c)
            return it.text() if it else ''
        new_row = tuple(_get(c) for c in range(len(self.COLUMNS)))
        if hasattr(self, '_displayed_data') and 0 <= row < len(self._displayed_data):
            orig = self._displayed_data[row]
            try:
                idx = self._all_data.index(orig)
                self._all_data[idx] = new_row
                self._displayed_data[row] = new_row
            except ValueError:
                pass
            _save_data(self._all_data)
        # 如果编辑的是"备注/状态"列，实时更新行颜色
        if self._table.column(item) == 6:
            notes = item.text()
            color = _row_color(notes)
            self._table.blockSignals(True)
            for c in range(len(self.COLUMNS)):
                it = self._table.item(row, c)
                if it:
                    if color:
                        it.setBackground(color)
                    else:
                        it.setBackground(QColor(Qt.GlobalColor.white))
            self._table.blockSignals(False)

    def _on_add_row(self):
        """在 _all_data 末尾追加一条空行并刷新显示。"""
        empty = ('', '', '', '', '', '', '')
        self._all_data.append(empty)
        # 不重置过滤，直接在当前视图尾部插入
        self._populate_append_empty()

    def _populate_append_empty(self):
        """仅在表格末尾插入一条空行，不全量刷新（保持过滤/滚动位置）。"""
        r = self._table.rowCount()
        self._table.blockSignals(True)
        self._table.insertRow(r)
        empty = ('', '', '', '', '', '', '')
        for c, val in enumerate(empty):
            self._table.setItem(r, c, QTableWidgetItem(val))
        self._displayed_data.append(empty)
        self._table.blockSignals(False)
        _save_data(self._all_data)
        self._table.scrollToBottom()
        self._table.setCurrentCell(r, 0)
        self._table.editItem(self._table.item(r, 0))
        self._count_lbl.setText(f'共 {self._table.rowCount()} 条')

    def _on_delete_rows(self):
        """删除当前选中的行（支持多选）。"""
        rows = sorted(
            {idx.row() for idx in self._table.selectedIndexes()},
            reverse=True   # 从底部开始删，避免行号移位
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
        _save_data(self._all_data)
        self._count_lbl.setText(f'共 {self._table.rowCount()} 条')
