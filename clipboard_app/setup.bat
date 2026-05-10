@echo off
chcp 65001 >nul
title 剪贴板历史 - 打包安装

echo.
echo ========================================
echo     剪贴板历史 v1.0 - 打包安装程序
echo ========================================
echo.

:: ==========================================
:: Step 0: 检查 Python
:: ==========================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo.
    echo 请访问 https://www.python.org/downloads/ 下载安装
    echo 安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [检测] Python %PYVER%

:: ==========================================
:: Step 1: 创建虚拟环境（如不存在）
:: ==========================================
echo.
echo [1/4] 准备虚拟环境...
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo   虚拟环境已创建
) else (
    echo   虚拟环境已存在，跳过
)

call venv\Scripts\activate.bat

:: ==========================================
:: Step 2: 安装依赖 + PyInstaller
:: ==========================================
echo.
echo [2/4] 安装依赖包（首次需要联网，约 1-2 分钟）...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 安装运行时依赖失败，请检查网络连接
    pause
    exit /b 1
)
echo   运行时依赖已安装

echo   安装 PyInstaller...
pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo [错误] 安装 PyInstaller 失败
    pause
    exit /b 1
)
echo   PyInstaller 已安装

:: ==========================================
:: Step 3: PyInstaller 打包
:: ==========================================
echo.
echo [3/4] 打包为独立 exe 文件（约 1-3 分钟）...

cd /d "%~dp0"

pyinstaller --onefile --windowed --name "ClipboardHistory" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import pyautogui ^
    --hidden-import mouseinfo ^
    --clean ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

:: ==========================================
:: Step 4: 创建桌面快捷方式
:: ==========================================
echo.
echo [4/4] 生成快捷方式...

set "EXE_PATH=%~dp0dist\ClipboardHistory.exe"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\剪贴板历史.url"

if not exist "%EXE_PATH%" (
    echo [错误] 未找到生成的 exe 文件: %EXE_PATH%
    pause
    exit /b 1
)

echo [InternetShortcut] > "%SHORTCUT%"
echo URL=file:///%EXE_PATH:\=/% >> "%SHORTCUT%"
echo IconFile=%EXE_PATH:\=/% >> "%SHORTCUT%"
echo IconIndex=0 >> "%SHORTCUT%"

echo.
echo ========================================
echo     打包完成！
echo ========================================
echo.
echo   exe 文件: %EXE_PATH%
echo   桌面快捷方式: %SHORTCUT%
echo.
echo 双击桌面上的「剪贴板历史」即可启动软件。
echo 启动后软件会在系统托盘（右下角）运行，
echo 点击托盘图标或按 Win+Shift+V 即可查看历史。
echo.
echo 如需开机自启动，请在软件设置中开启。
echo ========================================
echo.
pause
