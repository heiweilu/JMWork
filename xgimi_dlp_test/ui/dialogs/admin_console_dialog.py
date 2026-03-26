# -*- coding: utf-8 -*-
"""管理员控制台。"""

from typing import List, Dict

from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QSplitter,
)

from core.admin_console_store import normalize_doc_item
from core.markdown_renderer import render_markdown_html


class _MarkdownImageEditor(QTextEdit):
    """支持从剪贴板直接粘贴图片（转为 base64 data URL）的 Markdown 编辑器。"""

    def insertFromMimeData(self, source):
        if source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage):
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                img.save(buf, 'PNG')
                buf.close()
                b64 = ba.toBase64().data().decode('ascii')
                self.insertPlainText(f'![image](data:image/png;base64,{b64})')
                return
        super().insertFromMimeData(source)


class AdminConsoleDialog(QDialog):
    def __init__(self, app_version: str, author_email: str, docs: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle('管理员控制台')
        self.resize(1280, 820)
        self._docs = [normalize_doc_item(item) for item in docs]
        self._current_doc_index = -1
        self._init_ui(app_version, author_email)
        self._refresh_doc_list()

    def _init_ui(self, app_version: str, author_email: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel('可修改顶部显示版本号、作者邮箱，以及开发文档目录内容。保存后立即作用于 UI。')
        hint.setWordWrap(True)
        layout.addWidget(hint)

        meta_form = QFormLayout()
        self.edit_version = QLineEdit(app_version)
        self.edit_email = QLineEdit(author_email)
        meta_form.addRow('顶部版本号', self.edit_version)
        meta_form.addRow('作者邮箱', self.edit_email)
        layout.addLayout(meta_form)

        doc_split = QHBoxLayout()

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(QLabel('开发文档目录'))
        self.list_docs = QTreeWidget()
        self.list_docs.setHeaderHidden(True)
        self.list_docs.currentItemChanged.connect(self._on_doc_selected)
        left_layout.addWidget(self.list_docs, 1)
        row = QHBoxLayout()
        btn_add = QPushButton('新增文档')
        btn_add.clicked.connect(self._add_doc)
        btn_delete = QPushButton('删除文档')
        btn_delete.clicked.connect(self._delete_doc)
        btn_up = QPushButton('上移')
        btn_up.clicked.connect(lambda: self._move_doc(-1))
        btn_down = QPushButton('下移')
        btn_down.clicked.connect(lambda: self._move_doc(1))
        btn_import = QPushButton('导入 Markdown')
        btn_import.clicked.connect(self._import_doc)
        btn_export = QPushButton('导出 Markdown')
        btn_export.clicked.connect(self._export_doc)
        row.addWidget(btn_add)
        row.addWidget(btn_delete)
        row.addWidget(btn_up)
        row.addWidget(btn_down)
        row.addWidget(btn_import)
        row.addWidget(btn_export)
        row.addStretch(1)
        left_layout.addLayout(row)
        doc_split.addWidget(left, 1)

        right = QSplitter()
        right.setOrientation(Qt.Orientation.Vertical)

        editor_wrap = QWidget()
        right_layout = QVBoxLayout(editor_wrap)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        form = QFormLayout()
        self.edit_doc_category = QLineEdit()
        self.edit_doc_title = QLineEdit()
        self.edit_doc_content = _MarkdownImageEditor()
        self.edit_doc_content.setAcceptRichText(False)
        self.edit_doc_content.setPlaceholderText(
            "在此输入 Markdown 内容…\n提示：可直接 Ctrl+V 粘贴截图（自动转为 base64 图片插入）")
        self.edit_doc_content.textChanged.connect(self._update_preview)
        form.addRow('文档分类', self.edit_doc_category)
        form.addRow('文档标题', self.edit_doc_title)
        form.addRow('文档内容', self.edit_doc_content)
        right_layout.addLayout(form)

        preview_wrap = QWidget()
        preview_layout = QVBoxLayout(preview_wrap)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)
        preview_layout.addWidget(QLabel('Markdown 预览'))
        self.preview = QTextBrowser()
        preview_layout.addWidget(self.preview, 1)
        right.addWidget(editor_wrap)
        right.addWidget(preview_wrap)
        right.setSizes([420, 320])
        doc_split.addWidget(right, 2)

        layout.addLayout(doc_split, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save_current_doc(self):
        if self._current_doc_index < 0 or self._current_doc_index >= len(self._docs):
            return
        self._docs[self._current_doc_index]['category'] = self.edit_doc_category.text().strip() or '未分类'
        self._docs[self._current_doc_index]['title'] = self.edit_doc_title.text().strip() or '未命名文档'
        self._docs[self._current_doc_index]['format'] = 'markdown'
        self._docs[self._current_doc_index]['content'] = self.edit_doc_content.toPlainText()
        current_item = self._find_item_by_index(self._current_doc_index)
        if current_item is not None:
            current_item.setText(0, self._docs[self._current_doc_index]['title'])

    def _refresh_doc_list(self):
        self.list_docs.blockSignals(True)
        self.list_docs.clear()
        categories = {}
        for index, item in enumerate(self._docs):
            category = item.get('category', '未分类') or '未分类'
            if category not in categories:
                category_item = QTreeWidgetItem([category])
                category_item.setData(0, 256, -1)
                self.list_docs.addTopLevelItem(category_item)
                category_item.setExpanded(True)
                categories[category] = category_item
            doc_item = QTreeWidgetItem([item.get('title', '未命名文档')])
            doc_item.setData(0, 256, index)
            categories[category].addChild(doc_item)
        self.list_docs.blockSignals(False)
        if self._docs:
            self.list_docs.setCurrentItem(self._find_item_by_index(0))
        else:
            self.edit_doc_category.clear()
            self.edit_doc_title.clear()
            self.edit_doc_content.clear()
            self.preview.clear()

    def _find_item_by_index(self, index: int):
        for i in range(self.list_docs.topLevelItemCount()):
            category_item = self.list_docs.topLevelItem(i)
            for j in range(category_item.childCount()):
                item = category_item.child(j)
                if item.data(0, 256) == index:
                    return item
        return None

    def _on_doc_selected(self, current, _previous):
        self._save_current_doc()
        index = current.data(0, 256) if current is not None else -1
        self._current_doc_index = index
        if index < 0 or index >= len(self._docs):
            self.edit_doc_category.clear()
            self.edit_doc_title.clear()
            self.edit_doc_content.clear()
            self.preview.clear()
            return
        self.edit_doc_category.setText(self._docs[index].get('category', '未分类'))
        self.edit_doc_title.setText(self._docs[index].get('title', ''))
        self.edit_doc_content.setPlainText(self._docs[index].get('content', ''))
        self._update_preview()

    def _add_doc(self):
        self._save_current_doc()
        self._docs.append(normalize_doc_item({'category': '未分类', 'title': '新文档', 'format': 'markdown', 'content': ''}))
        self._refresh_doc_list()
        self.list_docs.setCurrentItem(self._find_item_by_index(len(self._docs) - 1))

    def _delete_doc(self):
        item = self.list_docs.currentItem()
        row = item.data(0, 256) if item is not None else -1
        if row < 0 or row >= len(self._docs):
            return
        reply = QMessageBox.question(self, '删除文档', f"确定删除《{self._docs[row].get('title', '未命名文档')}》吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._docs.pop(row)
        self._current_doc_index = -1
        self._refresh_doc_list()

    def _move_doc(self, offset: int):
        item = self.list_docs.currentItem()
        row = item.data(0, 256) if item is not None else -1
        if row < 0 or row >= len(self._docs):
            return
        new_row = row + offset
        if new_row < 0 or new_row >= len(self._docs):
            return
        self._save_current_doc()
        self._docs[row], self._docs[new_row] = self._docs[new_row], self._docs[row]
        self._refresh_doc_list()
        self.list_docs.setCurrentItem(self._find_item_by_index(new_row))

    def _update_preview(self):
        self.preview.setHtml(render_markdown_html(self.edit_doc_content.toPlainText()))

    def _import_doc(self):
        path, _ = QFileDialog.getOpenFileName(self, '导入 Markdown 文档', '', 'Markdown (*.md);;所有文件 (*)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                content = handle.read()
        except Exception as exc:
            QMessageBox.critical(self, '导入失败', str(exc))
            return
        self._save_current_doc()
        title = path.replace('\\', '/').split('/')[-1].rsplit('.', 1)[0]
        self._docs.append(normalize_doc_item({'category': '导入文档', 'title': title, 'format': 'markdown', 'content': content}))
        self._refresh_doc_list()
        self.list_docs.setCurrentItem(self._find_item_by_index(len(self._docs) - 1))

    def _export_doc(self):
        item = self.list_docs.currentItem()
        row = item.data(0, 256) if item is not None else -1
        if row < 0 or row >= len(self._docs):
            QMessageBox.information(self, '提示', '请先选择要导出的文档')
            return
        self._save_current_doc()
        path, _ = QFileDialog.getSaveFileName(
            self,
            '导出 Markdown 文档',
            f"{self._docs[row].get('title', '文档')}.md",
            'Markdown (*.md);;所有文件 (*)',
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(self._docs[row].get('content', ''))
        except Exception as exc:
            QMessageBox.critical(self, '导出失败', str(exc))

    def _on_accept(self):
        self._save_current_doc()
        if not self.edit_version.text().strip():
            QMessageBox.warning(self, '提示', '顶部版本号不能为空')
            return
        if not self.edit_email.text().strip():
            QMessageBox.warning(self, '提示', '作者邮箱不能为空')
            return
        self.accept()

    def get_data(self):
        self._save_current_doc()
        return {
            'app_version': self.edit_version.text().strip(),
            'author_email': self.edit_email.text().strip(),
            'docs': [dict(item) for item in self._docs],
        }