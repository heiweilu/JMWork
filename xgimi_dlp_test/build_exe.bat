@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   xgimi_dlp_test  —  PyInstaller 打包脚本
echo ============================================================
echo.

for /f "tokens=1,2 delims=|" %%a in ('python -c "from core.app_meta import APP_VERSION, APP_SIGNATURE; print(str(APP_VERSION) + '|' + str(APP_SIGNATURE))"') do (
    set APP_VERSION=%%a
    set APP_SIGNATURE=%%b
)
echo [信息] 当前打包版本: %APP_VERSION%  %APP_SIGNATURE%
echo.

:: ---------- 切换到脚本所在目录 ----------
cd /d "%~dp0"

:: ---------- 检查 Python ----------
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 已安装并加入 PATH
    pause & exit /b 1
)

:: ---------- 检查 / 安装 PyInstaller ----------
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 PyInstaller，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause & exit /b 1
    )
)

:: ---------- 检查依赖 ----------
echo [1/5] 检查项目依赖...
pip install -r requirements.txt --quiet --no-warn-script-location
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，继续打包（可能影响功能）
)

:: ---------- 清理旧构建 ----------
echo [2/5] 清理旧构建产物...
if exist build\xgimi_dlp_test  rmdir /s /q build\xgimi_dlp_test
if exist dist\xgimi_dlp_test   rmdir /s /q dist\xgimi_dlp_test
if exist __pycache__ rmdir /s /q __pycache__

:: ---------- 生成 Windows 版本资源 ----------
python -c "from pathlib import Path; from core.app_meta import APP_NAME, APP_VERSION, APP_SIGNATURE; version = str(APP_VERSION).lstrip('vV'); parts = (version.split('.') + ['0', '0', '0'])[:4]; major, minor, patch, build = [int(p or 0) for p in parts]; text = f'''VSVersionInfo(\n  ffi=FixedFileInfo(\n    filevers=({major}, {minor}, {patch}, {build}),\n    prodvers=({major}, {minor}, {patch}, {build}),\n    mask=0x3f,\n    flags=0x0,\n    OS=0x40004,\n    fileType=0x1,\n    subtype=0x0,\n    date=(0, 0)\n  ),\n  kids=[\n    StringFileInfo([\n      StringTable(\'080404B0\', [\n        StringStruct(\'CompanyName\', \'{APP_SIGNATURE}\'),\n        StringStruct(\'FileDescription\', \'{APP_NAME}\'),\n        StringStruct(\'FileVersion\', \'{APP_VERSION}\'),\n        StringStruct(\'InternalName\', \'xgimi_dlp_test\'),\n        StringStruct(\'OriginalFilename\', \'xgimi_dlp_test.exe\'),\n        StringStruct(\'ProductName\', \'{APP_NAME}\'),\n        StringStruct(\'ProductVersion\', \'{APP_VERSION}\')\n      ])\n    ]),\n    VarFileInfo([VarStruct(\'Translation\', [2052, 1200])])\n  ]\n)'''; Path('build').mkdir(exist_ok=True); Path('build/version_info.txt').write_text(text, encoding='utf-8')"

:: ---------- 打包 ----------
echo [3/5] 开始打包（首次可能需要 3-8 分钟）...
python -m PyInstaller xgimi_dlp_test.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上方错误信息
    pause & exit /b 1
)

:: ---------- 复制 Playwright Chromium Headless Shell ----------
echo [4/6] 复制 Playwright Chromium Headless Shell（约260MB，请稍候）...
for /f "tokens=*" %%i in ('python -c "import subprocess,re; r=subprocess.check_output([\"python\",\"-m\",\"playwright\",\"install\",\"--dry-run\"],stderr=subprocess.STDOUT,text=True); m=re.search(r\"chromium-headless-shell v(\d+)\",r); print(\"chromium_headless_shell-\"+m.group(1) if m else \"\")"') do set HEADLESS_VER=%%i
if "%HEADLESS_VER%"=="" (
    echo [警告] 无法确定 Headless Shell 版本，MTK 扫描功能需手动安装：playwright install chromium
) else (
    set HEADLESS_SRC=%LOCALAPPDATA%\ms-playwright\%HEADLESS_VER%
    if exist "!HEADLESS_SRC!" (
        xcopy /E /I /Q /Y "!HEADLESS_SRC!" "dist\xgimi_dlp_test\ms-playwright\!HEADLESS_VER!\"
        echo [Playwright] !HEADLESS_VER! 复制完成
    ) else (
        echo [警告] !HEADLESS_SRC! 不存在，请先运行：playwright install chromium
    )
)

:: ---------- 创建运行时输出目录占位 ----------
echo [5/6] 创建运行时输出目录...
if not exist dist\xgimi_dlp_test\_internal\reports mkdir dist\xgimi_dlp_test\_internal\reports
if not exist dist\xgimi_dlp_test\_internal\logs    mkdir dist\xgimi_dlp_test\_internal\logs

:: ---------- 写入版本信息文件 ----------
echo [6/6] 写入版本信息...
for /f "tokens=*" %%i in ('python -c "import datetime; print(datetime.datetime.now().strftime(\"%%Y%%m%%d_%%H%%M%%S\"))"') do set BUILD_TIME=%%i
echo BUILD_TIME=%BUILD_TIME% > dist\xgimi_dlp_test\BUILD_INFO.txt
echo SOURCE=xgimi_dlp_test >> dist\xgimi_dlp_test\BUILD_INFO.txt
echo APP_VERSION=%APP_VERSION% >> dist\xgimi_dlp_test\BUILD_INFO.txt
echo APP_SIGNATURE=%APP_SIGNATURE% >> dist\xgimi_dlp_test\BUILD_INFO.txt

:: ---------- 完成 ----------
echo.
echo ============================================================
echo   打包完成！
echo   可执行文件: dist\xgimi_dlp_test\xgimi_dlp_test.exe
echo   版本      : %APP_VERSION%  %APP_SIGNATURE%
echo   运行方式  : 双击 dist\xgimi_dlp_test\xgimi_dlp_test.exe
echo   注意      : 必须保持 dist\xgimi_dlp_test\ 整个目录结构，
echo               不可单独拷贝 .exe 文件！
echo ============================================================
echo.
pause
