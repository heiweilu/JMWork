# -*- coding: utf-8 -*-
"""
QSS 样式表 - 现代圆润立体主题 (Modern Rounded & Slightly 3D)

统一的界面风格：
- 导航栏：深色拟物态，圆角悬浮标签
- 内容区：明亮柔和背景，组件卡片化
- 按钮：柔和的圆角与轻微立体感（伪3D拟物）
- 字体：Microsoft YaHei，更友好的阅读体验
"""

MAIN_STYLE = """
/* === 全局 === */
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
    color: #2C3E50;
}

QMainWindow {
    background-color: #F4F7F9;
}

/* === 导航栏 === */
QListWidget#nav_list {
    background-color: #1E222D;
    color: #8A98A5;
    border: none;
    outline: none;
    font-size: 14px;
    padding: 12px 6px;
}

QListWidget#nav_list::item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 4px 8px;
    border: 1px solid transparent;
}

QListWidget#nav_list::item:hover {
    background-color: #2A303C;
    color: #FFFFFF;
}

QListWidget#nav_list::item:selected {
    background-color: #2A52BE;
    color: #FFFFFF;
    font-weight: bold;
    /* 轻微内发光或3D感 */
    border-bottom: 2px solid #1A367E;
}

QListWidget#nav_list::item:disabled {
    color: #4A5568;
}

/* === 按钮通用与立体效果 === */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F5F7FA);
    color: #2C3E50;
    border: 1px solid #CFD8DC;
    border-bottom: 2px solid #B0BEC5;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5F7FA, stop:1 #E4E8EB);
    border-color: #90A4AE;
    border-bottom: 2px solid #90A4AE;
}

QPushButton:pressed {
    background-color: #E4E8EB;
    border-top: 2px solid #CFD8DC;
    border-bottom: 1px solid #CFD8DC;
    padding-top: 7px;
    padding-bottom: 5px;
}

QPushButton:disabled {
    background-color: #E6EAF0;
    color: #9EABB3;
    border: 1px solid #D0D5D9;
    border-bottom: 1px solid #D0D5D9;
}

/* 强调按钮 */
QPushButton#btn_primary {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498DB, stop:1 #2980B9);
    color: #FFFFFF;
    border: 1px solid #2471A3;
    border-bottom: 2px solid #1A5276;
    font-weight: bold;
    letter-spacing: 0.5px;
}

QPushButton#btn_primary:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #74B9FF, stop:1 #0984E3);
    border: 1px solid #0652DD;
    border-bottom: 3px solid #023ED4;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton#btn_primary:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A5276, stop:1 #154360);
    border-top: 2px solid #0D3349;
    border-bottom: 1px solid #0D3349;
    padding-top: 7px;
    padding-bottom: 5px;
}

/* 危险按钮 */
QPushButton#btn_danger {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E74C3C, stop:1 #C0392B);
    color: #FFFFFF;
    border: 1px solid #A93226;
    border-bottom: 2px solid #7B241C;
    font-weight: bold;
}

QPushButton#btn_danger:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF7675, stop:1 #D63031);
    border: 1px solid #C0392B;
    border-bottom: 3px solid #A10000;
}

QPushButton#btn_danger:pressed {
    background-color: #922B21;
    border-top: 2px solid #641E16;
    border-bottom: 1px solid #641E16;
    padding-top: 7px;
    padding-bottom: 5px;
}

/* 成功按钮 */
QPushButton#btn_success {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2ECC71, stop:1 #27AE60);
    color: #FFFFFF;
    border: 1px solid #1E8449;
    border-bottom: 2px solid #145A32;
}

QPushButton#btn_success:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #58D68D, stop:1 #28B463);
}

QPushButton#btn_success:pressed {
    background-color: #1D8348;
    border-top: 2px solid #145A32;
    border-bottom: 1px solid #145A32;
    padding-top: 7px;
    padding-bottom: 5px;
}

/* === 输入框与下拉框（柔和圆角） === */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CFD8DC;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
    selection-background-color: #3498DB;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3498DB;
    background-color: #FAFCFE;
}

QLineEdit:read-only {
    background-color: #F0F3F4;
    color: #7F8C8D;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    border-left: 1px solid #ECEFF1;
}

QComboBox::down-arrow {
    image: none; /* 原生箭头可能不好看，保持简洁 */
}

/* === 卡片化分组框 GroupBox === */
QGroupBox {
    background-color: #FFFFFF;
    font-weight: bold;
    border: 1px solid #E0E6ED;
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 20px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    top: -8px;
    padding: 4px 10px;
    color: #2980B9;
    background-color: #EAF2F8;
    border-radius: 6px;
    border: 1px solid #D4E6F1;
}

/* === 进度条 === */
QProgressBar {
    border: 1px solid #CFD8DC;
    border-radius: 8px;
    background-color: #ECEFF1;
    text-align: center;
    height: 16px;
    font-weight: bold;
    color: #2C3E50;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5DADE2, stop:1 #2980B9);
    border-radius: 7px;
}

/* === 表格 === */
QTableView {
    background-color: #FFFFFF;
    gridline-color: #ECF0F1;
    border: 1px solid #CFD8DC;
    border-radius: 8px;
    alternate-background-color: #F9FBFC;
}

QTableView::item {
    padding: 4px;
}

QTableView::item:selected {
    background-color: #D4E6F1;
    color: #154360;
}

QHeaderView::section {
    background-color: #F4F7F9;
    color: #34495E;
    border: none;
    border-bottom: 2px solid #BDC3C7;
    border-right: 1px solid #ECF0F1;
    padding: 8px 6px;
    font-weight: bold;
}

/* === 树形视图 === */
QTreeView {
    background-color: #FFFFFF;
    border: 1px solid #CFD8DC;
    border-radius: 8px;
    padding: 4px;
}

QTreeView::item {
    border-radius: 4px;
    padding: 4px;
    margin: 1px 0px;
}

QTreeView::item:hover {
    background-color: #EAF2F8;
}

QTreeView::item:selected {
    background-color: #D4E6F1;
    color: #1A5276;
    font-weight: bold;
}

/* === 分割器 === */
QSplitter::handle {
    background-color: #E0E6ED;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

/* === 标签页圆滑化 === */
QTabWidget::pane {
    border: 1px solid #CFD8DC;
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: #ECEFF1;
    color: #7F8C8D;
    border: 1px solid #CFD8DC;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2980B9;
    border-bottom: 2px solid #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #E4E8EB;
    color: #2C3E50;
}

/* === 滚动条更优美 === */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #BDC3C7;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #95A5A6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #BDC3C7;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: #95A5A6;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* === 状态栏 === */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #CFD8DC;
    color: #7F8C8D;
    font-size: 12px;
}

/* === 工具提示 === */
QToolTip {
    background-color: #1E2A38;
    color: #E8F0FE;
    border: 1px solid #3D5A80;
    border-left: 3px solid #4FC3F7;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.5;
}

/* === 文内展示(描述区域) === */
QTextBrowser {
    background-color: transparent;
    border: none;
    color: #2C3E50;
    selection-background-color: #D4E6F1;
    font-size: 12px;
}
"""
