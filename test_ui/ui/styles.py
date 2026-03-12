# -*- coding: utf-8 -*-
"""QSS 样式表  科技浅色主题"""

_BG_BASE    = "#eef3fc"
_BG_CARD    = "#ffffff"
_BG_INPUT   = "#f4f8ff"
_BG_HEADER  = "#e8eeff"
_ACC_BLUE   = "#2563eb"
_ACC_CYAN   = "#0891b2"
_ACC_PURP   = "#7c3aed"
_ACC_GREEN  = "#059669"
_ACC_RED    = "#dc2626"
_TXT_PRI    = "#0f172a"
_TXT_SEC    = "#475569"
_TXT_DIM    = "#94a3b8"
_BORDER     = "rgba(37,99,235,0.14)"
_BORDER_ACT = "rgba(37,99,235,0.45)"

MAIN_STYLE = f"""
QWidget {{
    font-family: "Microsoft YaHei","PingFang SC","Segoe UI",sans-serif;
    font-size: 13px; color: {_TXT_PRI}; background-color: {_BG_CARD};
}}
QMainWindow, QDialog {{ background-color: {_BG_BASE}; }}
QSplitter > QWidget, QSplitter > QFrame {{ background-color: transparent; }}

QListWidget#nav_list {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {_BG_HEADER}, stop:1 rgba(232,238,255,0.96));
    color:{_TXT_SEC}; border:none; border-right:2px solid {_BORDER};
    outline:none; font-size:13px; padding:12px 6px;
}}
QListWidget#nav_list::item {{
    padding:12px 14px; border-radius:10px; margin:4px 6px;
    border:1px solid transparent; color:{_TXT_SEC}; background-color:transparent;
}}
QListWidget#nav_list::item:hover {{
    background:rgba(37,99,235,0.08); color:{_ACC_BLUE};
    border:1px solid rgba(37,99,235,0.20);
}}
QListWidget#nav_list::item:selected {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(37,99,235,0.15),stop:1 rgba(37,99,235,0.06));
    color:{_ACC_BLUE}; font-weight:bold; border:1px solid {_BORDER_ACT};
}}
QListWidget#nav_list::item:disabled {{ color:{_TXT_DIM}; }}

QPushButton {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffffff, stop:0.25 #f8fbff, stop:1 #e8f0fe);
    color:{_TXT_PRI}; border:1px solid {_BORDER};
    border-top:1.5px solid rgba(255,255,255,0.85);
    border-radius:11px;
    padding:6px 16px 7px 16px; min-height:28px;
}}
QPushButton:hover {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f0f6ff, stop:0.3 rgba(37,99,235,0.09), stop:1 rgba(37,99,235,0.18));
    border:1px solid {_BORDER_ACT};
    border-top:1.5px solid rgba(255,255,255,0.95);
    color:{_ACC_BLUE};
    padding:5px 16px 8px 16px;
}}
QPushButton:pressed {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(37,99,235,0.22), stop:1 rgba(37,99,235,0.10));
    border:1px solid {_ACC_BLUE};
    border-top:1px solid rgba(37,99,235,0.45);
    padding:8px 16px 5px 16px;
}}
QPushButton:disabled {{
    background:#f1f5f9; color:{_TXT_DIM}; border:1px solid rgba(37,99,235,0.06);
}}
QPushButton#btn_primary,QPushButton#btn_run_test,QPushButton#btn_connect {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #4f8af8, stop:0.4 {_ACC_BLUE}, stop:1 #1d4ed8);
    color:white; border:1px solid rgba(37,99,235,0.55);
    border-top:1.5px solid rgba(120,170,255,0.75);
    font-weight:bold; border-radius:11px;
}}
QPushButton#btn_primary:hover,QPushButton#btn_run_test:hover,QPushButton#btn_connect:hover {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #6ea3ff,stop:1 #1d4ed8);
    border:1px solid {_ACC_BLUE}; border-top:1.5px solid rgba(150,200,255,0.9);
    padding:5px 16px 8px 16px;
}}
QPushButton#btn_primary:pressed,QPushButton#btn_run_test:pressed,QPushButton#btn_connect:pressed {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1d4ed8,stop:1 #1e40af);
    border-top:1px solid rgba(37,99,235,0.6); padding:8px 16px 5px 16px;
}}
QPushButton#btn_danger,QPushButton#btn_stop_test,QPushButton#btn_disconnect {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f87171, stop:0.4 {_ACC_RED}, stop:1 #b91c1c);
    color:white; border:1px solid rgba(220,38,38,0.50);
    border-top:1.5px solid rgba(255,140,140,0.75);
    font-weight:bold; border-radius:11px;
}}
QPushButton#btn_danger:hover,QPushButton#btn_stop_test:hover,QPushButton#btn_disconnect:hover {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fca5a5,stop:1 #b91c1c);
    border:1px solid {_ACC_RED}; border-top:1.5px solid rgba(255,160,160,0.9);
    padding:5px 16px 8px 16px;
}}
QPushButton#btn_danger:pressed,QPushButton#btn_stop_test:pressed,QPushButton#btn_disconnect:pressed {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #b91c1c,stop:1 #991b1b);
    border-top:1px solid rgba(220,38,38,0.6); padding:8px 16px 5px 16px;
}}
QPushButton#btn_success {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #34d399, stop:0.4 {_ACC_GREEN}, stop:1 #047857);
    color:white; border:1px solid rgba(5,150,105,0.50);
    border-top:1.5px solid rgba(100,255,180,0.60);
    font-weight:bold; border-radius:11px;
}}
QPushButton#btn_success:hover {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #6ee7b7,stop:1 #047857);
    border:1px solid {_ACC_GREEN}; padding:5px 16px 8px 16px;
}}
QPushButton#btn_success:pressed {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #047857,stop:1 #065f46);
    padding:8px 16px 5px 16px;
}}
QPushButton#btn_log_toggle,QPushButton#btn_status_log_toggle {{
    min-height:22px; padding:3px 10px; border-radius:11px;
    background:rgba(37,99,235,0.07); color:{_ACC_BLUE};
    border:1px solid rgba(37,99,235,0.20); font-size:11px;
}}
QPushButton#btn_log_toggle:hover,QPushButton#btn_status_log_toggle:hover {{
    background:rgba(37,99,235,0.14); border:1px solid {_BORDER_ACT};
}}

QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {{
    background-color:{_BG_INPUT}; border:1px solid {_BORDER}; border-radius:8px;
    padding:5px 9px; min-height:28px; color:{_TXT_PRI};
    selection-background-color:rgba(37,99,235,0.18);
}}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus {{
    border:1px solid {_BORDER_ACT}; background-color:#edf3ff;
}}
QLineEdit:read-only {{ background-color:#f8faff; color:{_TXT_SEC}; }}
QLineEdit:disabled,QComboBox:disabled,QSpinBox:disabled,QDoubleSpinBox:disabled {{
    background-color:#f1f5f9; color:{_TXT_DIM}; border-color:rgba(37,99,235,0.08);
}}
QComboBox::drop-down {{ border:none; width:22px; border-left:1px solid {_BORDER}; }}
QComboBox QAbstractItemView {{
    background-color:{_BG_CARD}; border:1px solid {_BORDER_ACT};
    selection-background-color:rgba(37,99,235,0.12); color:{_TXT_PRI}; border-radius:6px;
}}

QGroupBox {{
    background-color:{_BG_CARD}; font-weight:bold; border:1px solid {_BORDER};
    border-radius:14px; margin-top:22px; padding-top:20px; color:{_TXT_PRI};
}}
QGroupBox::title {{
    subcontrol-origin:margin; left:14px; top:2px; padding:3px 10px;
    color:{_ACC_BLUE}; background-color:{_BG_CARD}; border-radius:7px;
    border:1px solid {_BORDER}; font-size:12px; letter-spacing:1px;
}}

QProgressBar {{
    border:1px solid {_BORDER}; border-radius:7px;
    background-color:rgba(37,99,235,0.07); text-align:center;
    height:14px; font-weight:bold; color:{_ACC_BLUE}; font-size:11px;
}}
QProgressBar::chunk {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {_ACC_BLUE},stop:0.5 #38bdf8,stop:1 {_ACC_PURP});
    border-radius:6px;
}}

QTableView {{
    background-color:{_BG_CARD}; gridline-color:rgba(37,99,235,0.08);
    border:1px solid {_BORDER}; border-radius:10px;
    alternate-background-color:rgba(37,99,235,0.03); color:{_TXT_PRI};
}}
QTableView::item:selected,QTreeView::item:selected {{
    background-color:rgba(37,99,235,0.12); color:{_ACC_BLUE};
}}
QHeaderView::section {{
    background-color:{_BG_HEADER}; color:{_TXT_SEC}; border:none;
    border-bottom:1px solid {_BORDER}; border-right:1px solid rgba(37,99,235,0.08);
    padding:7px 6px; font-weight:bold; font-size:12px;
}}
QTreeView {{
    background-color:{_BG_CARD}; border:1px solid {_BORDER};
    border-radius:10px; padding:4px; color:{_TXT_PRI};
}}
QTreeView::item:hover {{ background-color:rgba(37,99,235,0.06); }}

QSplitter::handle {{ background-color:rgba(37,99,235,0.12); }}
QSplitter::handle:horizontal {{ width:6px; }}
QSplitter::handle:vertical   {{ height:6px; }}
QSplitter::handle:hover {{ background-color:{_ACC_BLUE}; }}

QTabWidget::pane {{
    background-color:{_BG_CARD}; border:1px solid {_BORDER}; border-radius:10px; top:-1px;
}}
QTabBar::tab {{
    background-color:{_BG_HEADER}; color:{_TXT_SEC}; border:1px solid {_BORDER};
    border-bottom:none; padding:9px 18px; margin-right:2px;
    border-top-left-radius:9px; border-top-right-radius:9px;
    font-weight:bold; font-size:12px;
}}
QTabBar::tab:selected {{ background-color:{_BG_CARD}; color:{_ACC_BLUE}; border-bottom:2px solid {_ACC_BLUE}; }}
QTabBar::tab:hover:!selected {{ background-color:rgba(37,99,235,0.06); color:{_TXT_PRI}; }}

QScrollBar:vertical {{ background:rgba(37,99,235,0.05); width:8px; margin:2px; border-radius:4px; }}
QScrollBar:horizontal {{ background:rgba(37,99,235,0.05); height:8px; margin:2px; border-radius:4px; }}
QScrollBar::handle:vertical,QScrollBar::handle:horizontal {{
    background:rgba(37,99,235,0.22); border-radius:4px; min-height:20px; min-width:20px;
}}
QScrollBar::handle:vertical:hover,QScrollBar::handle:horizontal:hover {{ background:rgba(37,99,235,0.45); }}
QScrollBar::add-line,QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page,QScrollBar::sub-page {{ background:transparent; }}

QStatusBar {{ background-color:{_BG_HEADER}; border-top:1px solid {_BORDER}; color:{_TXT_SEC}; font-size:11px; }}

QToolTip {{
    background-color:{_BG_CARD}; color:{_TXT_PRI}; border:1px solid {_BORDER_ACT};
    border-left:3px solid {_ACC_BLUE}; padding:7px 11px; border-radius:7px; font-size:12px;
}}

QTextEdit,QPlainTextEdit {{
    background-color:{_BG_INPUT}; color:{_TXT_PRI};
    border:1px solid {_BORDER}; border-radius:8px; padding:6px;
    font-family:"Cascadia Code","Consolas","Courier New",monospace;
    font-size:12px; selection-background-color:rgba(37,99,235,0.18);
}}
QTextEdit:focus,QPlainTextEdit:focus {{ border:1px solid {_BORDER_ACT}; }}
QTextBrowser {{
    background-color:transparent; border:none; color:{_TXT_SEC};
    selection-background-color:rgba(37,99,235,0.12); font-size:12px;
}}

QLabel#log_dock_title {{ color:{_ACC_BLUE}; font-size:12px; font-weight:bold; letter-spacing:1.5px; background-color:transparent; }}
QFrame#log_dock_header {{ background-color:{_BG_HEADER}; border:1px solid {_BORDER}; border-radius:8px; }}

QFrame#card_top_glow,QFrame#log_top_glow {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0   rgba(37,99,235,0.00),
        stop:0.2 rgba(37,99,235,0.90),
        stop:0.5 rgba(56,189,248,0.80),
        stop:0.8 rgba(124,58,237,0.65),
        stop:1   rgba(124,58,237,0.00));
    border-radius:2px; min-height:3px;
}}

QCheckBox {{ color:{_TXT_PRI}; spacing:6px; background-color:transparent; }}
QCheckBox::indicator {{
    width:16px; height:16px; border:1px solid {_BORDER};
    border-radius:4px; background:{_BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {_ACC_BLUE},stop:1 #3b82f6);
    border:1px solid {_ACC_BLUE};
}}
QCheckBox::indicator:hover {{ border:1px solid {_BORDER_ACT}; }}

QToolButton {{
    background:rgba(37,99,235,0.07); color:{_TXT_PRI};
    border:1px solid {_BORDER}; border-radius:6px; padding:3px 6px;
}}
QToolButton:hover {{ background:rgba(37,99,235,0.16); border:1px solid {_BORDER_ACT}; color:{_ACC_BLUE}; }}
QToolButton:pressed {{ background:rgba(37,99,235,0.28); }}

QLabel {{ background-color:transparent; color:{_TXT_PRI}; }}
"""
