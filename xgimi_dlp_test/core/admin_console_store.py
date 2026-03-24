# -*- coding: utf-8 -*-
"""管理员控制台配置存储。"""

import json
import os
import re
from copy import deepcopy
from html import unescape
from typing import List, Dict

from core.app_meta import APP_AUTHOR_EMAIL, APP_VERSION, DEFAULT_ADMIN_PASSWORD


DEFAULT_ADMIN_DATA = {
    'password': DEFAULT_ADMIN_PASSWORD,
    'app_version': APP_VERSION,
    'author_email': APP_AUTHOR_EMAIL,
    'docs': [],
}


def _looks_like_html(text: str) -> bool:
    value = str(text or '').strip().lower()
    if not value:
        return False
    return bool(re.search(r'<\s*(h\d|p|pre|code|table|tr|td|th|ul|ol|li|br)\b', value))


def _has_unbalanced_code_fence(text: str) -> bool:
    return str(text or '').count('```') % 2 != 0


def _has_broken_markdown_table(text: str) -> bool:
    lines = [line.strip() for line in str(text or '').splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line.startswith('|') and line.endswith('|'):
            next_line = lines[index + 1]
            if '---' not in next_line and next_line.startswith('|') and next_line.endswith('|'):
                return True
    return False


def _strip_tags(text: str) -> str:
    value = re.sub(r'<[^>]+>', '', str(text or ''), flags=re.IGNORECASE | re.DOTALL)
    return unescape(value).strip()


def _convert_pre_block(match) -> str:
    content = unescape(match.group(1)).strip('\n')
    return f"\n```\n{content}\n```\n"


def _convert_list_block(match) -> str:
    inner = match.group(1)
    items = re.findall(r'<li[^>]*>(.*?)</li>', inner, flags=re.IGNORECASE | re.DOTALL)
    lines = [f"- {_strip_tags(item)}" for item in items if _strip_tags(item)]
    return '\n' + '\n'.join(lines) + '\n'


def _convert_table_block(match) -> str:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', match.group(1), flags=re.IGNORECASE | re.DOTALL)
    table_rows = []
    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, flags=re.IGNORECASE | re.DOTALL)
        clean_cells = [_strip_tags(cell) for cell in cells]
        if clean_cells:
            table_rows.append(clean_cells)
    if not table_rows:
        return ''
    header = table_rows[0]
    body = table_rows[1:] if len(table_rows) > 1 else []
    separator = ['---'] * len(header)
    lines = [
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(separator) + ' |',
    ]
    for row in body:
        if len(row) < len(header):
            row = row + [''] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[:len(header)]
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n' + '\n'.join(lines) + '\n'


def _normalize_markdown_spacing(text: str) -> str:
    value = str(text or '')
    value = re.sub(r'\n{3,}', '\n\n', value)
    lines = [line.rstrip() for line in value.splitlines()]
    return '\n'.join(lines).strip()


def html_to_markdown(text: str) -> str:
    value = str(text or '')
    value = re.sub(r'<pre[^>]*>(.*?)</pre>', _convert_pre_block, value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<table[^>]*>(.*?)</table>', _convert_table_block, value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<(ol|ul)[^>]*>(.*?)</\1>', _convert_list_block, value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<h1[^>]*>(.*?)</h1>', lambda m: f"# {_strip_tags(m.group(1))}\n\n", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<h2[^>]*>(.*?)</h2>', lambda m: f"## {_strip_tags(m.group(1))}\n\n", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<h3[^>]*>(.*?)</h3>', lambda m: f"### {_strip_tags(m.group(1))}\n\n", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<h4[^>]*>(.*?)</h4>', lambda m: f"#### {_strip_tags(m.group(1))}\n\n", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<p[^>]*>(.*?)</p>', lambda m: f"{_strip_tags(m.group(1))}\n\n", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<br\s*/?>', '\n', value, flags=re.IGNORECASE)
    value = re.sub(r'<code[^>]*>(.*?)</code>', lambda m: f"`{_strip_tags(m.group(1))}`", value, flags=re.IGNORECASE | re.DOTALL)
    value = _strip_tags(value)
    value = _normalize_markdown_spacing(value)
    return value


def normalize_doc_item(item: Dict[str, str]) -> Dict[str, str]:
    content = str(item.get('content', ''))
    fmt = str(item.get('format', '')).strip().lower() or 'markdown'
    if fmt != 'markdown' or _looks_like_html(content):
        content = html_to_markdown(content)
        fmt = 'markdown'
    return {
        'title': str(item.get('title', '')).strip() or '未命名文档',
        'category': str(item.get('category', '未分类')).strip() or '未分类',
        'format': fmt,
        'content': content,
    }


def normalize_docs_with_defaults(docs: List[Dict[str, str]], default_docs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    default_map = {
        (str(item.get('title', '')).strip() or '未命名文档'): normalize_doc_item(item)
        for item in default_docs
        if isinstance(item, dict)
    }
    result = []
    for item in docs:
        normalized = normalize_doc_item(item)
        default_doc = default_map.get(normalized['title'])
        if default_doc and (
            _has_unbalanced_code_fence(normalized['content'])
            or _has_broken_markdown_table(normalized['content'])
        ):
            normalized = dict(default_doc)
        result.append(normalized)
    return result


class AdminConsoleStore:
    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._path = os.path.join(config_dir, 'admin_console.json')
        self._data = deepcopy(DEFAULT_ADMIN_DATA)
        self.load()

    def load(self):
        self._data = deepcopy(DEFAULT_ADMIN_DATA)
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, 'r', encoding='utf-8') as handle:
                raw = json.load(handle)
            if isinstance(raw, dict):
                self._data.update(raw)
        except Exception:
            self._data = deepcopy(DEFAULT_ADMIN_DATA)

    def save(self):
        os.makedirs(self._config_dir, exist_ok=True)
        with open(self._path, 'w', encoding='utf-8') as handle:
            json.dump(self._data, handle, ensure_ascii=False, indent=2)

    def verify_password(self, password: str) -> bool:
        return str(password or '') == str(self._data.get('password', DEFAULT_ADMIN_PASSWORD))

    def has_docs(self) -> bool:
        return bool(self._data.get('docs'))

    def get_app_version(self) -> str:
        return str(self._data.get('app_version', APP_VERSION) or APP_VERSION)

    def set_app_version(self, value: str):
        self._data['app_version'] = str(value or APP_VERSION).strip() or APP_VERSION

    def get_author_email(self) -> str:
        return str(self._data.get('author_email', APP_AUTHOR_EMAIL) or APP_AUTHOR_EMAIL)

    def set_author_email(self, value: str):
        self._data['author_email'] = str(value or APP_AUTHOR_EMAIL).strip() or APP_AUTHOR_EMAIL

    def get_docs(self, default_docs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        docs = self._data.get('docs', [])
        should_save = False
        if not docs:
            docs = default_docs
        source_docs = [item for item in docs if isinstance(item, dict)]
        result = normalize_docs_with_defaults(source_docs, default_docs)
        for item, normalized in zip(source_docs, result):
            if item != normalized:
                should_save = True
        if should_save and self._data.get('docs'):
            self._data['docs'] = [dict(item) for item in result]
            self.save()
        return result

    def set_docs(self, docs: List[Dict[str, str]]):
        self._data['docs'] = [normalize_doc_item(item) for item in docs]