# -*- coding: utf-8 -*-
"""
QSS 样式表 - 简约亮色主题

统一的界面风格：
- 导航栏：深灰背景，白色文字
- 内容区：白色背景
- 按钮：圆角，悬停高亮
- 字体：Microsoft YaHei（中文友好）
"""

MAIN_STYLE = """
/* === 全局 === */
QWidget {
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 13px;
    color: #333333;
}

QMainWindow {
    background-color: #F5F5F5;
}

/* === 导航栏 === */
QListWidget#nav_list {
    background-color: #2C2C2C;
    color: #CCCCCC;
    border: none;
    outline: none;
    font-size: 14px;
    padding: 8px 0;
}

QListWidget#nav_list::item {
    padding: 12px 20px;
    border: none;
    border-left: 3px solid transparent;
}

QListWidget#nav_list::item:hover {
    background-color: #3C3C3C;
    color: #FFFFFF;
}

QListWidget#nav_list::item:selected {
    background-color: #0D47A1;
    color: #FFFFFF;
    border-left: 3px solid #2196F3;
}

QListWidget#nav_list::item:disabled {
    color: #666666;
}

/* === 按钮 === */
QPushButton {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #E3F2FD;
    border-color: #2196F3;
}

QPushButton:pressed {
    background-color: #BBDEFB;
}

QPushButton:disabled {
    background-color: #F0F0F0;
    color: #AAAAAA;
    border-color: #E0E0E0;
}

QPushButton#btn_primary {
    background-color: #1976D2;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}

QPushButton#btn_primary:hover {
    background-color: #1565C0;
}

QPushButton#btn_primary:pressed {
    background-color: #0D47A1;
}

QPushButton#btn_danger {
    background-color: #D32F2F;
    color: #FFFFFF;
    border: none;
}

QPushButton#btn_danger:hover {
    background-color: #C62828;
}

QPushButton#btn_success {
    background-color: #388E3C;
    color: #FFFFFF;
    border: none;
}

QPushButton#btn_success:hover {
    background-color: #2E7D32;
}

/* === 输入框 === */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 28px;
}

QLineEdit:focus {
    border-color: #2196F3;
}

QLineEdit:read-only {
    background-color: #F5F5F5;
}

/* === 下拉框 === */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #2196F3;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* === 分组框 === */
QGroupBox {
    font-weight: bold;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1976D2;
}

/* === 进度条 === */
QProgressBar {
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    background-color: #F0F0F0;
    text-align: center;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 3px;
}

/* === 表格 === */
QTableView {
    background-color: #FFFFFF;
    gridline-color: #E0E0E0;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
}

QTableView::item:selected {
    background-color: #E3F2FD;
    color: #333333;
}

QHeaderView::section {
    background-color: #F5F5F5;
    border: none;
    border-bottom: 1px solid #D0D0D0;
    padding: 6px;
    font-weight: bold;
}

/* === 树形视图 === */
QTreeView {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
}

QTreeView::item:hover {
    background-color: #E3F2FD;
}

QTreeView::item:selected {
    background-color: #BBDEFB;
    color: #333333;
}

/* === 分割器 === */
QSplitter::handle {
    background-color: #E0E0E0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* === 标签页 === */
QTabWidget::pane {
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #F0F0F0;
    border: 1px solid #D0D0D0;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    border-bottom: none;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #E3F2FD;
}

/* === 滚动条 === */
QScrollBar:vertical {
    background: #F5F5F5;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #C0C0C0;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #A0A0A0;
}

QScrollBar:horizontal {
    background: #F5F5F5;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #C0C0C0;
    border-radius: 4px;
    min-width: 20px;
}

/* === 状态栏 === */
QStatusBar {
    background-color: #F5F5F5;
    border-top: 1px solid #E0E0E0;
    color: #666666;
    font-size: 12px;
}

/* === 工具提示 === */
QToolTip {
    background-color: #333333;
    color: #FFFFFF;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}
"""
