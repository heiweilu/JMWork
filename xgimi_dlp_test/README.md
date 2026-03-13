# xgimi_dlp_test

极米 DLP 投影仪自动化测试与数据分析系统

---

## 快速开始（开发模式）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行
python main.py
```

---

## 打包为 EXE

### 前提条件

| 条件 | 说明 |
|---|---|
| Python 3.10+ | 必须与开发环境一致 |
| pip install pyinstaller | 一次性安装即可 |
| pip install -r requirements.txt | 确保所有依赖已安装 |

### 一键打包

双击运行 **`build_exe.bat`**，或在命令行执行：

```bat
pyinstaller xgimi_dlp_test.spec --clean
```

### 输出结构

```
dist/
└── xgimi_dlp_test/
    ├── xgimi_dlp_test.exe   ← 主程序入口（双击运行）
    ├── _internal/           ← PyQt6 运行时库（勿删）
    ├── config/              ← 配置文件（随包一起发布）
    ├── assets/              ← 固件等资源文件
    ├── modules/             ← 模块源码（task_registry 动态扫描需要）
    └── BUILD_INFO.txt       ← 构建时间戳
```

> ⚠️ **必须整个 `dist/xgimi_dlp_test/` 目录一起分发，不可单独拷贝 .exe 文件。**

### 打包常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| `No module named pyinstaller` | PATH 未包含 Python Scripts 目录 | 重开命令行，或用 `pip show pyinstaller` 确认安装路径 |
| `UnicodeDecodeError gbk` | requirements.txt 含中文注释 | 已修复，注释改为英文 |
| `No module named 'unittest'` | spec 的 excludes 误排除了标准库 | 已修复，spec 中只保留 `tkinter/wx/gi` 的排除 |
| 缺少某个模块 | 动态导入未被静态分析识别 | 在 spec 文件的 `hidden_imports` 中手动添加 |
| 启动闪退 | 未安装 libusb / CH340 驱动 | 参考"硬件驱动"章节 |

### 硬件驱动（EXE 运行环境需要）

- **USB 设备（DLPC843x）**：用 [Zadig](https://zadig.akeo.ie/) 将设备驱动切换为 WinUSB 或 libusb-win32
- **串口设备**：安装对应 CH340 / CP2102 驱动

---

## 打包后还能继续修改代码吗？

**可以，随时修改。** 打包与开发完全独立：

```
VSCode 里写代码  ──→  python main.py 即时验证  ──→  git commit
                                                        │
                                      积累到里程碑版本后  ↓
                                         pyinstaller 打包一次 EXE
```

- **日常开发**：直接运行 `python main.py`，无需每次打包
- **打包时机**：到达版本里程碑（如 v0.1、v0.2）才打包，对外发布
- **打包不影响源码**：`dist/` 目录完全独立，`.gitignore` 已排除它

---

## 版本管理策略

### 版本号规则

```
v<主版本>.<次版本>.<补丁>

v0.1.0   首个可演示版本（内部测试）
v0.2.0   新增主要功能
v0.2.1   Bug 修复
v1.0.0   功能齐全、稳定可交付
```

### 何时打包 EXE？

| 情况 | 建议 |
|---|---|
| 日常开发、调试 | **不打包**，直接 `python main.py` |
| 提交给测试人员验证 | 打包，内部分发目录即可 |
| 里程碑版本（vX.Y.0） | 打包 + Git Tag + GitHub Release |
| 只修复 Bug（vX.Y.Z） | 可选择性打包 |

---

## GitHub 版本控制与 Release 发布

### 初始化 Git 仓库（一次性操作）

```bash
cd xgimi_dlp_test
git init
git add .
git commit -m "feat: 初始化工程 v0.1.0"

# 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-name/xgimi_dlp_test.git
git push -u origin main
```

### .gitignore 必须排除的内容

工程根目录的 `.gitignore` 应包含：

```gitignore
# 打包产物（不入库，通过 Release 分发）
dist/
build/
*.spec.bak

# Python 缓存
__pycache__/
*.pyc
*.pyo

# 日志与运行时报告（数据量大，不入库）
logs/*.log
reports/

# 本地配置覆盖
config/user_config.json

# IDE
.vscode/settings.json
.idea/
```

### 日常开发工作流

```bash
# 开发新功能
git checkout -b feature/add-thermal-analysis
# ... 写代码 ...
git add .
git commit -m "feat: 新增温度漂移分析模块"
git push origin feature/add-thermal-analysis

# 合并到主分支
git checkout main
git merge feature/add-thermal-analysis
git push
```

### 发布一个版本（Release 流程）

#### 第一步：打 Git Tag

```bash
# 确保在 main 分支且代码已 commit
git checkout main
git pull

# 打版本标签（轻量标签）
git tag v0.1.0
git push origin v0.1.0
```

或带描述的注释标签（更规范）：

```bash
git tag -a v0.1.0 -m "v0.1.0: 基础功能完成，支持角度/梯形测试和可视化分析"
git push origin v0.1.0
```

#### 第二步：打包 EXE

```bat
REM 确保版本号写入 BUILD_INFO.txt
build_exe.bat
```

#### 第三步：创建 GitHub Release

1. 打开 GitHub 仓库页面 → **Releases** → **Draft a new release**
2. **Choose a tag** 选择刚刚推送的 `v0.1.0`
3. **Title** 填 `v0.1.0 - 初始发布`
4. **Description** 填 Release Notes（本次新增/修复内容）
5. **Attach binaries**：将整个 `dist/xgimi_dlp_test/` 打成 zip 上传

```bat
REM 打包成 zip（PowerShell）
Compress-Archive -Path dist\xgimi_dlp_test -DestinationPath xgimi_dlp_test_v0.1.0.zip
```

6. 点击 **Publish release**

#### Release Notes 模板

```markdown
## v0.1.0 - 首个可用版本

### 新增
- 角度精度测试（0.1°/1° 分辨率）
- 梯形坐标测试
- 串口调试终端（快捷指令面板）
- 四象限数据可视化（猫头鹰散点图）

### 修复
- 无

### 下载
- `xgimi_dlp_test_v0.1.0.zip`：Windows 可执行包（解压后运行 xgimi_dlp_test.exe）

### 运行要求
- Windows 10/11 x64
- 无需安装 Python
- USB 设备需预先安装 Zadig WinUSB 驱动
```

### 版本历史一览示例

| 版本 | 时间 | 说明 |
|---|---|---|
| v0.1.0 | 2026-03 | 首个可用版本，内部测试 |
| v0.2.0 | 计划 | 新增历史对比分析 |
| v1.0.0 | 计划 | 正式交付版本 |

---

## 工程结构概览

```
xgimi_dlp_test/
├── main.py                  # 程序入口
├── requirements.txt         # 依赖清单
├── xgimi_dlp_test.spec      # PyInstaller 打包配置
├── build_exe.bat            # 一键打包脚本
├── config/                  # 配置文件
├── assets/                  # 固件资源
├── core/                    # 基础设施（配置/注册表/工具）
├── dlpc_sdk/                # 硬件 SDK（DLPC843x USB 控制）
├── modules/                 # 业务模块（插件式自动注册）
│   ├── analysis/            # 数据分析
│   ├── preprocessing/       # 数据预处理
│   └── test/                # 硬件测试（需设备）
├── workers/                 # Qt 工作线程
├── ui/                      # 完整 GUI 层
│   ├── styles.py            # 全局 QSS 浅色科技主题
│   ├── animations.py        # 动画系统
│   ├── main_window.py       # 主窗口
│   ├── pages/               # 7 个功能页面
│   └── widgets/             # 可复用控件
├── reports/                 # 测试报告输出
└── logs/                    # 运行日志
```

---

## 新增功能模块（最简步骤）

1. 在 `modules/analysis/`（或 `preprocessing/` / `test/`）新建 `.py` 文件
2. 声明 `MODULE_INFO` 字典和 `run()` 函数（参考 `DEVELOPMENT_PROMPT.txt` 第四章）
3. 重启应用，下拉框中自动出现新模块，无需手动注册
