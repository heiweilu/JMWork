# -*- coding: utf-8 -*-
"""Markdown 渲染工具。"""

from html import escape

try:
    import markdown as _markdown
except Exception:
    _markdown = None

try:
    from pygments.formatters import HtmlFormatter
except Exception:
    HtmlFormatter = None


def _codehilite_css() -> str:
    if HtmlFormatter is None:
        return """
        .codehilite, pre {
            background: #f8fafc;
            color: #1f2937;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px 18px;
            overflow-x: auto;
        }
        .codehilite code, pre code {
            background: transparent;
            color: inherit;
            padding: 0;
        }
        """
    return HtmlFormatter(style='friendly').get_style_defs('.codehilite')


def render_markdown_html(text: str) -> str:
    source = str(text or '')
    if _markdown is None:
        body = f'<pre>{escape(source)}</pre>'
    else:
        body = _markdown.markdown(
            source,
            extensions=['fenced_code', 'tables', 'sane_lists', 'nl2br', 'codehilite'],
            output_format='html5',
        )

    return f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            font-size: 13px;
            color: #1f2937;
            line-height: 1.85;
            padding: 8px 4px 24px 4px;
            background: #ffffff;
        }}
        h1, h2, h3, h4 {{
            color: #163b7a;
            margin-top: 20px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        h1 {{ font-size: 24px; border-bottom: 2px solid #dbeafe; padding-bottom: 8px; }}
        h2 {{ font-size: 20px; border-bottom: 2px solid #dbeafe; padding-bottom: 6px; }}
        h3 {{ font-size: 17px; }}
        h4 {{ font-size: 15px; }}
        p {{ margin: 10px 0; }}
        ul, ol {{ margin: 8px 0 12px 0; padding-left: 24px; }}
        li {{ margin: 6px 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            background: #ffffff;
            border: 1px solid #cbd5e1;
        }}
        th, td {{
            border: 1px solid #cbd5e1;
            padding: 8px 10px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #e8eefc;
            color: #1e3a8a;
            font-weight: 700;
        }}
        tr:nth-child(even) td {{
            background: #f8fbff;
        }}
        code {{
            background: #eef2ff;
            color: #1d4ed8;
            padding: 2px 6px;
            border-radius: 6px;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12px;
        }}
        pre {{
            margin: 12px 0 16px 0;
        }}
        .codehilite {{
            margin: 12px 0 16px 0;
            border-radius: 12px;
            overflow: auto;
            box-shadow: inset 0 0 0 1px #cbd5e1;
            background: #f8fafc;
        }}
        .codehilite pre {{
            margin: 0;
            padding: 16px 18px;
            background: #f8fafc;
            color: #1f2937;
        }}
        blockquote {{
            margin: 12px 0;
            padding: 10px 14px;
            border-left: 4px solid #93c5fd;
            background: #eff6ff;
            color: #334155;
        }}
        hr {{
            border: none;
            border-top: 1px solid #dbeafe;
            margin: 20px 0;
        }}
        {_codehilite_css()}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """