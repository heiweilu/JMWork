# -*- coding: utf-8 -*-
"""
开发文档页面

说明如何新增/删除/修改功能模块，以及项目整体结构。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QTextBrowser, QListWidget,
                              QListWidgetItem, QSplitter, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# ──────────────────────────────────────────────
#  文档内容定义（标题 → HTML 正文）
# ──────────────────────────────────────────────
DOCS = [
    {
        "title": "📁 项目结构总览",
        "content": """
<h2>项目结构总览</h2>
<pre style="background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px;line-height:1.8">
test_ui/
├── main.py                 # 程序入口
├── config/
│   └── default_config.json # 默认配置文件
├── assets/
│   └── reference_images/   # 各模块参考结果图
├── core/
│   ├── config_manager.py   # 配置管理
│   ├── task_registry.py    # 模块注册表（自动发现）
│   └── file_utils.py       # 文件工具
├── modules/                # ★ 功能模块目录（核心业务代码）
│   ├── analysis/           #   分析执行类模块
│   ├── preprocessing/      #   数据预处理类模块
│   └── test/               #   硬件测试类模块
├── ui/
│   ├── main_window.py      # 主窗口（导航 + 页面切换）
│   ├── styles.py           # 全局样式
│   ├── animations.py       # UI动效
│   ├── pages/              # 各功能页面
│   └── widgets/            # 可复用组件
└── workers/
    └── task_worker.py      # 后台任务线程
</pre>
<p style="color:#555">所有业务逻辑写在 <b>modules/</b> 下，UI 层通过 <b>task_registry</b> 自动发现并展示，
两层完全解耦——修改模块不需要改任何 UI 代码。</p>
"""
    },
    {
        "title": "➕ 新增分析模块",
        "content": """
<h2>新增分析模块（分析执行页）</h2>

<h3>第一步：在 <code>modules/analysis/</code> 下新建 <code>xxx.py</code></h3>
<pre style="background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px;line-height:1.8">
# modules/analysis/my_analysis.py

MODULE_INFO = {
    "name": "我的分析",            # 显示在下拉框的名称
    "category": "analysis",        # 固定写 "analysis"
    "description": "功能说明...",
    "input_type": "csv",           # csv / txt / directory
    "input_description": "输入文件格式说明",
    "output_type": "image",        # image / excel / csv
    "script_file": "my_analysis.py",    # 便于调试定位
    # 如有参考结果图，把图放到 assets/reference_images/ 并填写文件名：
    "reference_image": "my_analysis.png",
    "params": [
        {"key": "threshold", "label": "阈值", "type": "float",
         "default": 0.5, "min": 0.0, "max": 1.0},
    ],
}

def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    \"""
    返回值规范:
      成功: {"status": "success", "output_path": "...", "figure": fig_or_None}
      失败: {"status": "error",   "message": "错误描述"}
      取消: {"status": "cancelled"}
    \"""
    try:
        # 你的业务逻辑 ...
        if log_callback:
            log_callback("处理中...", "INFO")
        if progress_callback:
            progress_callback(1, 1)
        return {"status": "success", "output_path": output_dir, "figure": None}
    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\\n{traceback.format_exc()}"}
</pre>

<h3>第二步：重启程序</h3>
<p>task_registry 会自动扫描 <code>modules/analysis/</code>，无需修改任何 UI 代码，
新模块会自动出现在「分析执行」页的下拉框中。</p>

<h3>params 支持的类型</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px">
<tr style="background:#eef"><th>type</th><th>控件</th><th>额外字段</th></tr>
<tr><td>string</td><td>文本框</td><td>default</td></tr>
<tr><td>int</td><td>整数输入</td><td>default, min, max</td></tr>
<tr><td>float</td><td>浮点输入</td><td>default, min, max, decimals</td></tr>
<tr><td>bool</td><td>复选框</td><td>default (True/False)</td></tr>
<tr><td>choice</td><td>下拉框</td><td>options(标签列表), values(实际值列表), default</td></tr>
<tr><td>tuple</td><td>范围输入(两框)</td><td>default=(min,max)</td></tr>
</table>
"""
    },
    {
        "title": "➕ 新增预处理模块",
        "content": """
<h2>新增预处理模块（数据预处理页）</h2>

<h3>在 <code>modules/preprocessing/</code> 下新建 <code>xxx.py</code></h3>
<pre style="background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px;line-height:1.8">
# modules/preprocessing/my_preprocess.py

MODULE_INFO = {
    "name": "我的预处理",
    "category": "preprocessing",   # 固定写 "preprocessing"
    "description": "功能说明...",
    "input_type": "csv",            # csv / txt / directory / csv_or_dir
    "input_description": "输入格式说明",
    "output_type": "csv",
    "script_file": "my_preprocess.py",
    "params": [
        {"key": "encoding", "label": "编码", "type": "choice",
         "options": ["utf-8-sig", "gbk"],
         "values":  ["utf-8-sig", "gbk"],
         "default": "utf-8-sig"},
    ],
}

def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    # 同分析模块，返回规范一样
    ...
</pre>
<p>重启后自动出现在「数据预处理」页的 Tab 中，每个预处理模块对应一个 Tab。</p>
"""
    },
    {
        "title": "🗑️ 删除/禁用模块",
        "content": """
<h2>删除或禁用模块</h2>

<h3>方法一：直接删除文件（彻底删除）</h3>
<p>删除 <code>modules/analysis/</code> 或 <code>modules/preprocessing/</code>
或 <code>modules/test/</code> 下对应的 <code>.py</code> 文件，重启程序即生效。</p>

<h3>方法二：重命名为下划线开头（临时禁用）</h3>
<p>将文件改名为 <code>_xxx.py</code>（加下划线前缀），
task_registry 会跳过所有以 <code>_</code> 开头的文件，等于软禁用，
恢复时改回原名即可。</p>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px">
# 禁用：
my_analysis.py  →  _my_analysis.py

# 恢复：
_my_analysis.py  →  my_analysis.py
</pre>

<h3>相关代码位置</h3>
<p>跳过逻辑在 <code>core/task_registry.py</code>：</p>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px">
if name.startswith('_'):
    continue
</pre>
"""
    },
    {
        "title": "✏️ 修改已有模块",
        "content": """
<h2>修改已有模块</h2>

<h3>只改业务逻辑（不改 MODULE_INFO）</h3>
<p>直接编辑 <code>modules/xxx/yyy.py</code> 中的 <code>run()</code> 函数，
重启程序生效。UI 自动适配，无需改任何界面代码。</p>

<h3>修改参数列表</h3>
<p>编辑 <code>MODULE_INFO["params"]</code>，重启后 UI 会重新生成表单控件。</p>

<h3>修改下拉框显示名称</h3>
<p>编辑 <code>MODULE_INFO["name"]</code>，显示名称和脚本文件名分离，互不干扰。</p>

<h3>修改参考结果图</h3>
<ol>
<li>替换 <code>assets/reference_images/xxx.png</code></li>
<li>或修改 <code>MODULE_INFO["reference_image"]</code> 指向新文件名</li>
</ol>

<h3>修改输出路径逻辑</h3>
<p>输出路径由 <code>run(output_dir, ...)</code> 的第二个参数传入，
可在模块内部自行决定最终写入路径，不受 UI 限制。</p>
"""
    },
    {
        "title": "⚙️ 配置说明",
        "content": """
<h2>配置文件说明</h2>

<h3>配置文件位置</h3>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px">
test_ui/config/default_config.json
</pre>

<h3>常用配置项</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px">
<tr style="background:#eef"><th>配置键</th><th>说明</th><th>示例值</th></tr>
<tr><td>general.project_root</td><td>DLP 自动化测试工程根目录</td><td>D:/...../202602027_dlp_auto</td></tr>
<tr><td>paths.angle_results_dir</td><td>角度测试结果目录（相对工程根）</td><td>reports/Angle_test_results</td></tr>
<tr><td>paths.csv_quadrant_dir</td><td>象限CSV目录（相对工程根）</td><td>data/CSV_quadrant_data</td></tr>
<tr><td>paths.reports_dir</td><td>报告输出目录（相对工程根）</td><td>reports</td></tr>
<tr><td>screen.height</td><td>投影屏幕高度（像素）</td><td>2159</td></tr>
<tr><td>angle.yaw_max / yaw_min</td><td>Yaw 角度范围</td><td>40 / -40</td></tr>
<tr><td>angle.pitch_max / pitch_min</td><td>Pitch 角度范围</td><td>40 / -40</td></tr>
</table>

<h3>修改配置</h3>
<p>在「配置管理」页直接编辑并点击「保存配置」即可，
所有模块的 <code>run()</code> 通过 <code>params['project_root']</code> 获取工程根目录。</p>
"""
    },
    {
        "title": "🖥️ 新增导航菜单页",
        "content": """
<h2>新增导航菜单页（UI 级别扩展）</h2>

<h3>第一步：新建页面文件</h3>
<p>在 <code>ui/pages/</code> 下新建 <code>my_page.py</code>，继承 <code>QWidget</code>：</p>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px;line-height:1.8">
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyPage(QWidget):
    def __init__(self, log_panel=None, config_mgr=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("我的新页面"))
</pre>

<h3>第二步：在 <code>ui/main_window.py</code> 注册</h3>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px;line-height:1.8">
# 1. 顶部导入
from ui.pages.my_page import MyPage

# 2. NAV_ITEMS 中添加一项
NAV_ITEMS = [
    ...
    {"name": "我的页面", "icon": "🆕", "enabled": True},  # ← 新增
]

# 3. _init_ui() 中创建并加入 page_stack
self.my_page = MyPage(log_panel=self.log_panel, config_mgr=self._config_mgr)
self.page_stack.addWidget(self.my_page)

# 注意：page_stack 中页面顺序须与 NAV_ITEMS 顺序一致
</pre>
"""
    },
    {
        "title": "🔍 调试技巧",
        "content": """
<h2>调试技巧</h2>

<h3>快速定位某功能对应的脚本</h3>
<p>在「分析执行」页的下拉框中，每个选项显示格式为：<br>
<code>模块名  —  script_file.py</code><br>
直接打开 <code>modules/analysis/script_file.py</code> 即可。</p>

<h3>查看运行日志</h3>
<p>底部日志面板会记录所有 INFO / SUCCESS / WARNING / ERROR 信息，
点击「导出日志」可保存为文件。</p>

<h3>模块加载失败排查</h3>
<p>若某模块未出现在下拉框：检查启动时控制台输出，
task_registry 会打印加载失败原因：</p>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px">
[TaskRegistry] 模块 modules.analysis.xxx 加载失败: &lt;错误信息&gt;
</pre>
<p>常见原因：<code>MODULE_INFO</code> 缺字段、<code>run()</code> 函数签名不对、
依赖库未安装。</p>

<h3>让模块打印中间日志</h3>
<pre style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:13px">
def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None):
    if log_callback:
        log_callback("步骤1完成", "INFO")     # 显示在日志面板
    if progress_callback:
        progress_callback(1, 3)               # 更新进度条 (当前, 总数)
</pre>
"""
    },
]


class DocsPage(QWidget):
    """开发文档页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
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

        self.toc_list = QListWidget()
        self.toc_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 6px;
                border-radius: 6px;
                color: #37474F;
            }
            QListWidget::item:selected {
                background: #C5CAE9;
                color: #1A237E;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background: #E8EAF6;
            }
        """)
        for doc in DOCS:
            self.toc_list.addItem(QListWidgetItem(doc["title"]))

        self.toc_list.currentRowChanged.connect(self._on_toc_changed)
        left_layout.addWidget(self.toc_list)

        # ── 右侧内容 ──
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

        splitter.addWidget(left)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)

        root_layout.addWidget(splitter)

        # 默认选中第一项
        self.toc_list.setCurrentRow(0)

    def _on_toc_changed(self, index: int):
        if 0 <= index < len(DOCS):
            self.browser.setHtml(_wrap_html(DOCS[index]["content"]))
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
    </style></head><body>{body}</body></html>
    """
