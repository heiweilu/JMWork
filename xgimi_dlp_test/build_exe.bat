@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   xgimi_dlp_test  —  PyInstaller 打包脚本
echo ============================================================
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
echo [1/4] 检查项目依赖...
pip install -r requirements.txt --quiet --no-warn-script-location
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，继续打包（可能影响功能）
)

:: ---------- 清理旧构建 ----------
echo [2/4] 清理旧构建产物...
if exist build\xgimi_dlp_test  rmdir /s /q build\xgimi_dlp_test
if exist dist\xgimi_dlp_test   rmdir /s /q dist\xgimi_dlp_test
if exist __pycache__ rmdir /s /q __pycache__

:: ---------- 打包 ----------
echo [3/4] 开始打包（首次可能需要 3-8 分钟）...
python -m PyInstaller xgimi_dlp_test.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上方错误信息
    pause & exit /b 1
)

:: ---------- 写入版本信息文件 ----------
echo [4/4] 写入版本信息...
for /f "tokens=*" %%i in ('python -c "import datetime; print(datetime.datetime.now().strftime(\"%%Y%%m%%d_%%H%%M%%S\"))"') do set BUILD_TIME=%%i
echo BUILD_TIME=%BUILD_TIME% > dist\xgimi_dlp_test\BUILD_INFO.txt
echo SOURCE=xgimi_dlp_test >> dist\xgimi_dlp_test\BUILD_INFO.txt

:: ---------- 完成 ----------
echo.
echo ============================================================
echo   打包完成！
echo   可执行文件: dist\xgimi_dlp_test\xgimi_dlp_test.exe
echo   运行方式  : 双击 dist\xgimi_dlp_test\xgimi_dlp_test.exe
echo   注意      : 必须保持 dist\xgimi_dlp_test\ 整个目录结构，
echo               不可单独拷贝 .exe 文件！
echo ============================================================
echo.
pause
