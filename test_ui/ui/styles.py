# -*- coding: utf-8 -*-
"""QSS 样式表 - 浅色科技感主题。"""

MAIN_STYLE = """
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
    color: #24344D;
}

QMainWindow {
    background-color: #F4F9FF;
}

QListWidget#nav_list {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FDFEFF, stop:1 #EDF5FF);
    color: #5A7397;
    border: none;
    outline: none;
    font-size: 14px;
    padding: 14px 8px;
    border-right: 1px solid rgba(80, 132, 255, 0.14);
}

QListWidget#nav_list::item {
    padding: 14px 16px;
    border-radius: 12px;
    margin: 5px 8px;
    border: 1px solid transparent;
}

QListWidget#nav_list::item:hover {
    background-color: rgba(120, 190, 255, 0.10);
    color: #1D4ED8;
    border: 1px solid rgba(103, 173, 255, 0.18);
}

QListWidget#nav_list::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #6DAEFF, stop:1 #8AE7FF);
    color: white;
    font-weight: bold;
    border: 1px solid rgba(79, 140, 255, 0.18);
}

QListWidget#nav_list::item:disabled {
    color: #9EB0C7;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255,255,255,0.98), stop:1 rgba(242,247,255,0.92));
    color: #234067;
    border: 1px solid rgba(127, 174, 235, 0.18);
    border-radius: 10px;
    padding: 7px 16px;
    min-height: 28px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255,255,255,1.0), stop:1 rgba(232,244,255,0.96));
    border-color: rgba(103, 173, 255, 0.28);
    color: #184FC6;
}

QPushButton:pressed {
    background-color: #E4EEFF;
}

QPushButton:disabled {
    background-color: #F3F6FB;
    color: #A7B6CA;
    border-color: rgba(120, 146, 180, 0.14);
}

QPushButton#btn_primary,
QPushButton#btn_run_test,
QPushButton#btn_connect {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #5B9BFF, stop:1 #3B7CFF);
    color: white;
    border: 1px solid rgba(59, 124, 255, 0.25);
    font-weight: bold;
}

QPushButton#btn_primary:hover,
QPushButton#btn_run_test:hover,
QPushButton#btn_connect:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #73ADFF, stop:1 #4C8CFF);
    color: white;
}

QPushButton#btn_danger,
QPushButton#btn_stop_test,
QPushButton#btn_disconnect {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FF8E98, stop:1 #F46C7A);
    color: white;
    border: 1px solid rgba(244, 108, 122, 0.24);
    font-weight: bold;
}

QPushButton#btn_danger:hover,
QPushButton#btn_stop_test:hover,
QPushButton#btn_disconnect:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FFA1A9, stop:1 #F77E8B);
    color: white;
}

QPushButton#btn_success {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #49D7C3, stop:1 #20BFA7);
    color: white;
    border: 1px solid rgba(32, 191, 167, 0.24);
}

QPushButton#btn_success:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #62E3D0, stop:1 #30CCB3);
    color: white;
}

QPushButton#btn_log_toggle,
QPushButton#btn_status_log_toggle {
    min-height: 24px;
    padding: 4px 12px;
    border-radius: 12px;
    background-color: #F1F6FF;
    color: #3561A8;
}

QPushButton#btn_log_toggle:hover,
QPushButton#btn_status_log_toggle:hover {
    background-color: #E3EEFF;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid rgba(97, 128, 171, 0.24);
    border-radius: 10px;
    padding: 6px 10px;
    min-height: 28px;
    selection-background-color: #77B5FF;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid rgba(79, 140, 255, 0.7);
    background-color: #FCFEFF;
}

QLineEdit:read-only {
    background-color: #F6F9FE;
    color: #8193AB;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F4F7FB;
    color: #A7B6CA;
    border-color: rgba(120, 146, 180, 0.14);
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    border-left: 1px solid rgba(97, 128, 171, 0.14);
}

QGroupBox,
QFrame#page_stack_container,
QFrame#log_panel_container,
QTabWidget::pane,
QTableView,
QTreeView,
QTextEdit,
QTextBrowser,
QPlainTextEdit {
    background-color: rgba(255, 255, 255, 0.88);
}

QGroupBox {
    font-weight: bold;
    border: 1px solid rgba(123, 168, 228, 0.14);
    border-radius: 16px;
    margin-top: 16px;
    padding-top: 20px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    top: -8px;
    padding: 4px 10px;
    color: #2A64D6;
    background-color: rgba(247, 251, 255, 0.96);
    border-radius: 8px;
    border: 1px solid rgba(103, 173, 255, 0.12);
}

QProgressBar {
    border: 1px solid rgba(97, 128, 171, 0.2);
    border-radius: 8px;
    background-color: #F5F8FD;
    text-align: center;
    height: 16px;
    font-weight: bold;
    color: #35517A;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #67D3FF, stop:1 #4F8CFF);
    border-radius: 7px;
}

QTableView {
    gridline-color: rgba(130, 160, 210, 0.12);
    border: 1px solid rgba(123, 168, 228, 0.14);
    border-radius: 12px;
    alternate-background-color: rgba(248, 251, 255, 0.9);
}

QTableView::item:selected,
QTreeView::item:selected {
    background-color: rgba(79, 140, 255, 0.16);
    color: #173A7A;
}

QHeaderView::section {
    background-color: #F7FAFF;
    color: #5A74A0;
    border: none;
    border-bottom: 1px solid rgba(97, 128, 171, 0.16);
    border-right: 1px solid rgba(97, 128, 171, 0.08);
    padding: 8px 6px;
    font-weight: bold;
}

QTreeView {
    border: 1px solid rgba(123, 168, 228, 0.14);
    border-radius: 12px;
    padding: 4px;
}

QTreeView::item:hover {
    background-color: rgba(103, 211, 255, 0.12);
}

QSplitter::handle {
    background-color: rgba(192, 216, 245, 0.56);
}

QSplitter::handle:horizontal { width: 8px; }
QSplitter::handle:vertical { height: 8px; }

QSplitter::handle:hover {
    background-color: rgba(123, 214, 255, 0.62);
}

QTabWidget::pane {
    border: 1px solid rgba(123, 168, 228, 0.14);
    border-radius: 12px;
    top: -1px;
}

QTabBar::tab {
    background-color: rgba(245, 249, 255, 0.96);
    color: #6880A8;
    border: 1px solid rgba(123, 168, 228, 0.12);
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2463DA;
    border-bottom: 2px solid #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #EEF5FF;
    color: #3D6FCF;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background: rgba(144, 177, 221, 0.85);
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {
    background: rgba(103, 211, 255, 0.92);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

QStatusBar {
    background-color: rgba(255, 255, 255, 0.86);
    border-top: 1px solid rgba(123, 168, 228, 0.10);
    color: #6880A8;
    font-size: 12px;
}

QToolTip {
    background-color: #FFFFFF;
    color: #294469;
    border: 1px solid rgba(79, 140, 255, 0.18);
    border-left: 3px solid #67D3FF;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
}

QTextBrowser {
    background-color: transparent;
    border: none;
    color: #294469;
    selection-background-color: rgba(79, 140, 255, 0.18);
    font-size: 12px;
}

QLabel#log_dock_title {
    color: #2D4F85;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 1px;
}

QFrame#log_dock_header {
    background-color: rgba(247, 250, 255, 0.96);
    border: 1px solid rgba(103, 173, 255, 0.12);
    border-radius: 10px;
}

QFrame#card_top_glow,
QFrame#log_top_glow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(115, 211, 255, 0.18),
                                stop:0.45 rgba(120, 164, 255, 0.85),
                                stop:1 rgba(255, 255, 255, 0.0));
    border-radius: 2px;
}
"""
