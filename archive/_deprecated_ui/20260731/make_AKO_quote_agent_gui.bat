@echo off
REM ============================================
REM  AKO_quote_agent GUI 打包脚本 (Windows)
REM  使用 PyInstaller 打包为单个 .exe 文件
REM ============================================
echo.
echo ============================================
echo   AKO_quote_agent GUI 打包工具
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install PySide6 PySide6-Fluent-Widgets --quiet
if %errorlevel% neq 0 (
    echo [警告] pip install 失败，请手动安装依赖
)

REM 清理旧构建
echo [2/3] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AKO_quote_agent_gui.spec del /q AKO_quote_agent_gui.spec

REM 执行 PyInstaller 打包
echo [3/3] PyInstaller 打包中...
pyinstaller --onefile --windowed ^
    --name="AKO_quote_agent" ^
    --icon=exe_icon.png ^
    --add-data="ako_quote_agent\pricing_config.json;ako_quote_agent" ^
    --add-data="ako_quote_agent\templates;ako_quote_agent\templates" ^
    --add-data="ako_quote_agent\assets;ako_quote_agent\assets" ^
    --add-data="ako_quote_agent\data;ako_quote_agent\data" ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=PIL ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=qfluentwidgets ^
    --hidden-import=ako_quote_agent.gui.ako_style ^
    --hidden-import=ako_quote_agent.gui.login_dialog ^
    --hidden-import=ako_quote_agent.gui.main_window ^
    --hidden-import=ako_quote_agent.gui.quote_page ^
    --hidden-import=ako_quote_agent.gui.history_page ^
    --hidden-import=ako_quote_agent.gui.settings_page ^
    --hidden-import=ako_quote_agent.gui.launcher ^
    --hidden-import=ako_quote_agent.gui.auth_manager ^
    --hidden-import=ako_quote_agent.gui.change_password_dialog ^
    --hidden-import=ako_quote_agent.gui.user_management_dialog ^
    --hidden-import=ako_quote_agent.quote_engine ^
    --hidden-import=ako_quote_agent.logger ^
    AKO_quote_agent_gui.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   打包成功！
    echo   输出文件: dist\AKO_quote_agent.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   打包失败，请检查错误信息。
    echo ============================================
)

pause