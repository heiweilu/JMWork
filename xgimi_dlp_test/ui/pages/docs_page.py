# -*- coding: utf-8 -*-
"""
开发文档页面

说明如何新增/删除/修改功能模块，以及项目整体结构。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QTextBrowser, QListWidget,
                              QListWidgetItem, QSplitter, QFrame,
                              QLineEdit, QTableWidget, QTableWidgetItem,
                              QHeaderView, QStackedWidget, QAbstractItemView,
                              QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from core.admin_console_store import normalize_doc_item
from core.default_docs import load_default_docs
from core.markdown_renderer import render_markdown_html
from core.script_api_doc_loader import load_script_api_reference


# ──────────────────────────────────────────────
#  文档内容定义（Markdown 默认文档源）
# ──────────────────────────────────────────────
DOCS = load_default_docs()


# ─────────────────────────────────────────────────────────────────────────────
# 错误码参考页面
# ─────────────────────────────────────────────────────────────────────────────

class _ErrorCodeWidget(QWidget):
    """错误码参考页：搜索 + 表格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_rows: list = []   # [(code_int, name, desc), ...]
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(8)

        # 标题
        title = QLabel("🔢  错误码参考 (ErrorCode Reference)")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A237E; padding-bottom:4px;")
        layout.addWidget(title)

        # 搜索栏
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_lbl = QLabel("🔍 搜索:")
        search_lbl.setFixedWidth(52)
        search_lbl.setStyleSheet("color:#555; font-size:13px;")
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(
            "输入错误码（数字）或名称关键词，实时过滤...")
        self._search_edit.setStyleSheet(
            "QLineEdit { border: 1px solid #C5CAE9; border-radius: 5px;"
            " padding: 4px 8px; font-size: 13px; background:#FAFAFA; }")
        self._search_edit.textChanged.connect(self._on_search)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self._search_edit)
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color:#888; font-size:12px;")
        self._count_lbl.setFixedWidth(100)
        search_row.addWidget(self._count_lbl)
        layout.addLayout(search_row)

        # 表格
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["ErrorCode", "名称 (Name)", "说明 (Description)"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
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
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { background: #C5CAE9; color: #1A237E; }
        """)
        layout.addWidget(self._table)

    def _load_data(self):
        """从 assets/doc/ErrorCode.txt 解析错误码"""
        import os, re
        here = os.path.dirname(os.path.abspath(__file__))
        ec_path = ""
        for _ in range(6):
            candidate = os.path.join(here, "assets", "doc", "ErrorCode.txt")
            if os.path.isfile(candidate):
                ec_path = candidate
                break
            here = os.path.dirname(here)

        rows = []
        if ec_path:
            try:
                with open(ec_path, "r", encoding="utf-8-sig", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line in ("ErrCodeT", "Top", "Members"):
                            continue
                        parts = re.split(r"\t", line)
                        if len(parts) < 3 or parts[1].strip() != "=":
                            continue
                        try:
                            code = int(parts[2].strip())
                        except ValueError:
                            continue
                        name = parts[0].strip()
                        desc = parts[3].lstrip("# ").strip() if len(parts) > 3 else ""
                        rows.append((code, name, desc))
            except Exception as e:
                rows = [(0, "加载失败", str(e))]
        else:
            rows = [(0, "未找到", "assets/doc/ErrorCode.txt 不存在")]

        # 按 code 排序，去重（同 code 保留第一条）
        seen_codes: set = set()
        unique_rows = []
        for r in sorted(rows, key=lambda x: x[0]):
            if r[0] not in seen_codes:
                seen_codes.add(r[0])
                unique_rows.append(r)
            else:
                # 同 code 多条：若已有的 desc 为空则替换
                idx = next(i for i, x in enumerate(unique_rows) if x[0] == r[0])
                if not unique_rows[idx][2] and r[2]:
                    unique_rows[idx] = r
        self._all_rows = unique_rows
        self._populate_table(self._all_rows)

    def _populate_table(self, rows: list):
        self._table.setRowCount(0)
        for code, name, desc in rows:
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)
            # ErrorCode：右对齐数字
            code_item = QTableWidgetItem(str(code))
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            code_item.setForeground(QColor("#1565C0"))
            self._table.setItem(row_idx, 0, code_item)
            self._table.setItem(row_idx, 1, QTableWidgetItem(name))
            desc_item = QTableWidgetItem(desc)
            desc_item.setForeground(QColor("#555555" if desc else "#AAAAAA"))
            self._table.setItem(row_idx, 2, desc_item)
        self._count_lbl.setText(f"{len(rows)} 条")
        self._table.resizeRowsToContents()

    def _on_search(self, text: str):
        kw = text.strip().lower()
        if not kw:
            self._populate_table(self._all_rows)
            return
        filtered = [
            r for r in self._all_rows
            if kw in str(r[0]) or kw in r[1].lower() or kw in r[2].lower()
        ]
        self._populate_table(filtered)


class _ScriptApiWidget(QWidget):
    """TI Script API 文档浏览器。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items = []
        self._visible_items = []
        self._meta = {}
        self._init_ui()
        self._load_items()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("TI Script API")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("color:#1565C0;")
        layout.addWidget(title)

        self._meta_lbl = QLabel("正在加载函数列表...")
        self._meta_lbl.setStyleSheet("color:#546E7A; font-size:12px;")
        self._meta_lbl.setWordWrap(True)
        layout.addWidget(self._meta_lbl)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("搜索 function 名称、命令号或关键字，例如 Keystone / E6 / Execute")
        self._search_edit.textChanged.connect(self._on_search)
        self._search_edit.setStyleSheet(
            "QLineEdit {padding:8px 10px; border:1px solid #CFD8DC; border-radius:6px;}"
        )
        search_row.addWidget(self._search_edit, 1)

        self._count_lbl = QLabel("0 个函数")
        self._count_lbl.setStyleSheet("color:#607D8B; font-size:12px;")
        search_row.addWidget(self._count_lbl)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self._func_list = QListWidget()
        self._func_list.setMinimumWidth(320)
        self._func_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: #FAFCFE;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #ECEFF1;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #0D47A1;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background: #F1F8FF;
            }
        """)
        self._func_list.currentRowChanged.connect(self._on_current_changed)
        left_layout.addWidget(self._func_list)

        self._detail_browser = QTextBrowser()
        self._detail_browser.setOpenExternalLinks(True)
        self._detail_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: #FFFFFF;
                padding: 14px 18px;
            }
        """)

        splitter.addWidget(left)
        splitter.addWidget(self._detail_browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 900])
        layout.addWidget(splitter, 1)

    def _load_items(self):
        self._all_items, self._meta = load_script_api_reference()
        self._visible_items = list(self._all_items)

        source_path = self._meta.get("path", "")
        source_label = self._meta.get("source_label", "未知来源")
        count = self._meta.get("count", 0)
        msg = f"当前来源：{source_label}，共 {count} 个 Read/Write API。"
        if source_path:
            msg += f"<br>路径：{source_path}"
        self._meta_lbl.setText(msg)
        self._refresh_list()

    def _refresh_list(self):
        self._func_list.blockSignals(True)
        self._func_list.clear()
        for item in self._visible_items:
            title = f"{item.opcode}  {item.name}".strip() if item.opcode else item.name
            list_item = QListWidgetItem(title)
            list_item.setToolTip(item.summary or item.signature)
            self._func_list.addItem(list_item)
        self._func_list.blockSignals(False)

        self._count_lbl.setText(f"{len(self._visible_items)} 个函数")
        if self._visible_items:
            self._func_list.setCurrentRow(0)
        else:
            self._detail_browser.setHtml(_wrap_html(
                "<h2>未找到匹配函数</h2><p>请尝试不同关键字，例如 <code>Keystone</code>、<code>Orientation</code>、<code>E1</code>。</p>"
            ))

    def _on_search(self, text: str):
        keyword = text.strip().lower()
        if not keyword:
            self._visible_items = list(self._all_items)
        else:
            self._visible_items = [
                item for item in self._all_items
                if keyword in item.search_text
            ]
        self._refresh_list()

    def _on_current_changed(self, row: int):
        if row < 0 or row >= len(self._visible_items):
            return
        item = self._visible_items[row]
        self._detail_browser.setHtml(_wrap_html(item.detail_html))
        self._detail_browser.verticalScrollBar().setValue(0)


# ─────────────────────────────────────────────────────────────────────────────

class DocsPage(QWidget):
    """开发文档页面"""

    def __init__(self, admin_store=None, parent=None):
        super().__init__(parent)
        self._admin_store = admin_store
        self._docs = []
        self._init_ui()

    def _load_docs(self):
        if self._admin_store is None:
            self._docs = [normalize_doc_item(item) for item in DOCS]
        else:
            self._docs = self._admin_store.get_docs(DOCS)
            if not self._admin_store.has_docs():
                self._admin_store.set_docs(self._docs)
                self._admin_store.save()

    def refresh_docs(self):
        self._load_docs()
        current_item = self.toc_list.currentItem()
        current_key = current_item.data(0, Qt.ItemDataRole.UserRole) if current_item is not None else ''
        self.toc_list.blockSignals(True)
        self.toc_list.clear()
        self._build_toc_tree()
        self.toc_list.blockSignals(False)
        if current_key:
            self._select_toc_key(str(current_key))
        elif self.toc_list.topLevelItemCount() > 0:
            self._select_toc_key(str(self.toc_list.topLevelItem(0).data(0, Qt.ItemDataRole.UserRole) or ''))

    def _build_toc_tree(self):
        categories = {}
        for index, doc in enumerate(self._docs):
            category = doc.get('category', '未分类') or '未分类'
            if category not in categories:
                category_item = QTreeWidgetItem([category])
                category_item.setData(0, Qt.ItemDataRole.UserRole, f'category:{category}')
                self.toc_list.addTopLevelItem(category_item)
                category_item.setExpanded(True)
                categories[category] = category_item
            doc_item = QTreeWidgetItem([doc['title']])
            doc_item.setData(0, Qt.ItemDataRole.UserRole, f'doc:{index}')
            categories[category].addChild(doc_item)

        ref_item = QTreeWidgetItem(['系统参考'])
        ref_item.setData(0, Qt.ItemDataRole.UserRole, 'category:系统参考')
        ref_item.setExpanded(True)
        api_item = QTreeWidgetItem(['🧭 TI Script API'])
        api_item.setData(0, Qt.ItemDataRole.UserRole, 'special:api')
        error_item = QTreeWidgetItem(['🔢 错误码参考'])
        error_item.setData(0, Qt.ItemDataRole.UserRole, 'special:error')
        ref_item.addChild(api_item)
        ref_item.addChild(error_item)
        self.toc_list.addTopLevelItem(ref_item)

    def _select_toc_key(self, key: str):
        def _walk(item):
            if str(item.data(0, Qt.ItemDataRole.UserRole) or '') == key:
                self.toc_list.setCurrentItem(item)
                return True
            for index in range(item.childCount()):
                if _walk(item.child(index)):
                    item.setExpanded(True)
                    return True
            return False

        for index in range(self.toc_list.topLevelItemCount()):
            if _walk(self.toc_list.topLevelItem(index)):
                break

    def _init_ui(self):
        self._load_docs()
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── 左侧目录 ──
        left = QWidget()
        left.setMaximumWidth(220)
        left.setMinimumWidth(180)
        left.setStyleSheet("background:#F0F4F8;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 16, 12, 12)
        left_layout.setSpacing(6)

        title_label = QLabel("📖  开发文档")
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color:#1A237E; padding-bottom:8px;")
        left_layout.addWidget(title_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#C5CAE9;")
        left_layout.addWidget(sep)
        left_layout.addSpacing(4)

        self.toc_list = QTreeWidget()
        self.toc_list.setHeaderHidden(True)
        self.toc_list.setStyleSheet("""
            QTreeWidget {
                background: transparent;
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px 6px;
                border-radius: 6px;
                color: #37474F;
            }
            QTreeWidget::item:selected {
                background: #C5CAE9;
                color: #1A237E;
                font-weight: bold;
            }
            QTreeWidget::item:hover:!selected {
                background: #E8EAF6;
            }
        """)
        self._build_toc_tree()

        self.toc_list.currentItemChanged.connect(self._on_toc_changed)
        left_layout.addWidget(self.toc_list)

        # ── 右侧内容（QStackedWidget：0=浏览器，1=错误码页）──
        self._right_stack = QStackedWidget()

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background: #FFFFFF;
                border: none;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
                padding: 20px 28px;
            }
        """)
        self._right_stack.addWidget(self.browser)          # index 0

        self._api_widget = _ScriptApiWidget()
        self._right_stack.addWidget(self._api_widget)      # index 1

        self._ec_widget = _ErrorCodeWidget()
        self._right_stack.addWidget(self._ec_widget)       # index 2

        splitter.addWidget(left)
        splitter.addWidget(self._right_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)

        root_layout.addWidget(splitter)

        # 默认选中第一项
        if self.toc_list.topLevelItemCount() > 0:
            first_root = self.toc_list.topLevelItem(0)
            first_root.setExpanded(True)
            if first_root.childCount() > 0:
                self.toc_list.setCurrentItem(first_root.child(0))

    def _on_toc_changed(self, current, _previous):
        if current is None:
            return
        key = str(current.data(0, Qt.ItemDataRole.UserRole) or '')
        if key.startswith('category:'):
            if current.childCount() > 0:
                self.toc_list.setCurrentItem(current.child(0))
            return
        if key == 'special:api':
            self._right_stack.setCurrentIndex(1)
        elif key == 'special:error':
            self._right_stack.setCurrentIndex(2)
        elif key.startswith('doc:'):
            index = int(key.split(':', 1)[1])
            self._right_stack.setCurrentIndex(0)
            doc = normalize_doc_item(self._docs[index])
            self.browser.setHtml(render_markdown_html(doc.get('content', '')))
            self.browser.verticalScrollBar().setValue(0)


def _wrap_html(body: str) -> str:
    return f"""
    <html><head><style>
        body {{ font-family: "Microsoft YaHei","Segoe UI",sans-serif;
                font-size: 13px; color: #212121;
                line-height: 1.8; padding: 4px; }}
        h2   {{ color: #1565C0; border-bottom: 2px solid #E3F2FD;
                padding-bottom: 6px; margin-top: 0; }}
        h3   {{ color: #1976D2; margin-top: 20px; margin-bottom: 6px; }}
        code {{ background: #EEF; padding: 2px 5px; border-radius: 3px;
                font-family: Consolas, monospace; font-size: 12px; }}
        pre  {{ font-family: Consolas, "Courier New", monospace;
                font-size: 12.5px; overflow-x: auto; }}
        table{{ width: 100%; margin-top: 8px; }}
        th   {{ background: #E8EAF6; color: #283593; }}
        td,th{{ border: 1px solid #C5CAE9; padding: 6px 10px; }}
        ol,ul{{ padding-left: 20px; }}
        li   {{ margin-bottom: 4px; }}
        p    {{ margin: 8px 0; }}
        .api-badge {{ display: inline-block; margin-right: 8px; margin-bottom: 6px;
                      padding: 4px 8px; border-radius: 999px;
                      background: #E3F2FD; color: #0D47A1; font-size: 12px; }}
        .api-signature {{ background: #ECEFF1; color: #37474F; }}
    </style></head><body>{body}</body></html>
    """
