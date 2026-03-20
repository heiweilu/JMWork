# -*- coding: utf-8 -*-
"""加载 TI Script API 文档，供开发文档页展示。"""

from __future__ import annotations

import ast
import glob
import html
import os
import re
from dataclasses import dataclass


@dataclass
class ScriptApiItem:
    name: str
    opcode: str
    signature: str
    summary: str
    detail_html: str
    source: str
    search_text: str


def load_script_api_reference() -> tuple[list[ScriptApiItem], dict]:
    sdk_items = _load_from_local_sdk()
    sdk_map = {item.name: item for item in sdk_items}

    html_path = _find_external_html_doc()
    if html_path:
        html_items = _load_from_html_doc(html_path, sdk_map)
        if html_items:
            return html_items, {
                "source": "html",
                "source_label": "TI ScriptAPIDoc.html",
                "path": html_path,
                "count": len(html_items),
            }

    return sdk_items, {
        "source": "sdk",
        "source_label": "项目内 dlpc843x.py",
        "path": _local_sdk_path(),
        "count": len(sdk_items),
    }


def _find_external_html_doc() -> str:
    env_path = os.environ.get("TI_DLP_SCRIPT_API_DOC", "").strip()
    if env_path and os.path.exists(env_path):
        return env_path

    base_dir = os.environ.get("LOCALAPPDATA", "")
    if not base_dir:
        return ""

    pattern = os.path.join(
        base_dir,
        "Texas Instruments",
        "DLP Control Program*",
        "Settings",
        "Scripts",
        "dlpc843x",
        "ScriptAPIDoc.html",
    )
    matches = sorted(glob.glob(pattern), reverse=True)
    return matches[0] if matches else ""


def _load_from_html_doc(html_path: str, sdk_map: dict[str, ScriptApiItem]) -> list[ScriptApiItem]:
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
    except OSError:
        return []

    toc_start_marker = '<a href="#Funcs" class="section" name="FuncLink">Functions</a><div class="subsection">'
    toc_start = content.find(toc_start_marker)
    if toc_start == -1:
        return []
    toc_start += len(toc_start_marker)

    toc_end = content.find('</div><a href="#Enums"', toc_start)
    if toc_end == -1:
        return []

    toc_html = content[toc_start:toc_end]

    toc_entries = {}
    for anchor, label in re.findall(r'<a href="#([^"]+)">([^<]+)</a>', toc_html):
        if not re.match(r'^(Read|Write)[A-Z]', anchor):
            continue
        opcode = ""
        if " - " in label:
            opcode = label.split(" - ", 1)[0].strip()
        toc_entries[anchor] = opcode

    sections = {}
    heading_matches = list(re.finditer(
        r'<h2><a id="(?P<id>[^"]+)" name="[^"]+">(?P<name>[^<]+)</a></h2>',
        content,
        re.IGNORECASE,
    ))
    for index, match in enumerate(heading_matches):
        func_id = match.group("id")
        body_start = match.end()
        if index + 1 < len(heading_matches):
            next_heading_pos = content.rfind('<table class="heading">', body_start, heading_matches[index + 1].start())
            body_end = next_heading_pos if next_heading_pos != -1 else heading_matches[index + 1].start()
        else:
            enum_pos = content.find('<a href="#Enums"', body_start)
            body_end = enum_pos if enum_pos != -1 else len(content)
        body = _clean_html_fragment(content[body_start:body_end])
        sections[func_id] = body

    items = []
    for name, opcode in toc_entries.items():
        sdk_item = sdk_map.get(name)
        body_html = sections.get(name, "")
        summary = _extract_summary(body_html)
        if not summary and sdk_item:
            summary = sdk_item.summary
        signature = sdk_item.signature if sdk_item else f"{name}()"
        detail_html = _compose_detail_html(name, opcode, signature, body_html, sdk_item)
        search_text = " ".join(filter(None, [name, opcode, signature, summary]))
        items.append(
            ScriptApiItem(
                name=name,
                opcode=opcode,
                signature=signature,
                summary=summary,
                detail_html=detail_html,
                source="html",
                search_text=search_text.lower(),
            )
        )
    return items


def _load_from_local_sdk() -> list[ScriptApiItem]:
    sdk_path = _local_sdk_path()
    try:
        with open(sdk_path, "r", encoding="utf-8-sig", errors="ignore") as fp:
            tree = ast.parse(fp.read(), filename=sdk_path)
    except (OSError, SyntaxError):
        return []

    items = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not re.match(r'^(Read|Write)[A-Z]', node.name):
            continue
        signature = _build_signature(node)
        doc = ast.get_docstring(node) or ""
        summary = _extract_summary(doc)
        detail_html = _compose_detail_html(
            node.name,
            "",
            signature,
            _docstring_to_html(doc),
            None,
        )
        search_text = " ".join(filter(None, [node.name, signature, summary]))
        items.append(
            ScriptApiItem(
                name=node.name,
                opcode="",
                signature=signature,
                summary=summary,
                detail_html=detail_html,
                source="sdk",
                search_text=search_text.lower(),
            )
        )
    return items


def _local_sdk_path() -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "dlpc_sdk", "dlpc843x.py")


def _build_signature(node: ast.FunctionDef) -> str:
    arg_names = [arg.arg for arg in node.args.args]
    defaults = [None] * (len(arg_names) - len(node.args.defaults)) + list(node.args.defaults)
    rendered = []
    for arg_name, default in zip(arg_names, defaults):
        if default is None:
            rendered.append(arg_name)
            continue
        default_repr = _literal_repr(default)
        rendered.append(f"{arg_name}={default_repr}")
    return f"{node.name}({', '.join(rendered)})"


def _literal_repr(node: ast.AST) -> str:
    try:
        value = ast.literal_eval(node)
    except Exception:
        return "..."
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _compose_detail_html(
    name: str,
    opcode: str,
    signature: str,
    body_html: str,
    sdk_item: ScriptApiItem | None,
) -> str:
    parts = [f"<h2>{html.escape(name)}</h2>"]
    meta_parts = []
    if opcode:
        meta_parts.append(f"<span class='api-badge'>命令号 {html.escape(opcode)}</span>")
    meta_parts.append(
        f"<span class='api-badge api-signature'>{html.escape(signature)}</span>"
    )
    parts.append(f"<p>{''.join(meta_parts)}</p>")

    if body_html:
        parts.append(body_html)
    elif sdk_item and sdk_item.detail_html:
        parts.append(sdk_item.detail_html)
    else:
        parts.append("<p style='color:#666;'>未提取到详细说明。</p>")
    return "".join(parts)


def _clean_html_fragment(fragment: str) -> str:
    fragment = re.sub(r'<script.*?</script>', '', fragment, flags=re.IGNORECASE | re.DOTALL)
    fragment = re.sub(r'<style.*?</style>', '', fragment, flags=re.IGNORECASE | re.DOTALL)
    fragment = re.sub(r'<a href="#[^"]+">([^<]+)</a>', r'\1', fragment)
    fragment = re.sub(r'\s+class="[^"]*"', '', fragment)
    fragment = re.sub(r'\s+style="[^"]*"', '', fragment)
    return fragment.strip()


def _extract_summary(text_or_html: str) -> str:
    plain = re.sub(r'<[^>]+>', ' ', text_or_html)
    plain = html.unescape(plain)
    plain = re.sub(r'\s+', ' ', plain).strip()
    if not plain:
        return ""
    return plain[:160] + ("..." if len(plain) > 160 else "")


def _docstring_to_html(doc: str) -> str:
    if not doc:
        return ""
    escaped = html.escape(doc).replace("\n\n", "</p><p>")
    escaped = escaped.replace("\n", "<br>")
    return f"<p>{escaped}</p>"