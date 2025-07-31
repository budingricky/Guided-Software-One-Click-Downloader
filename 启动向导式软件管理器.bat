@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    🧙‍♂️ 软件资源整合管理器 v4.0 向导
echo ========================================
echo.

echo 正在检查运行环境...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到Python环境
    echo 请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

REM 检查必要的依赖包
echo 正在检查依赖包...

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  CustomTkinter未安装，正在安装...
    pip install customtkinter
    if errorlevel 1 (
        echo ❌ CustomTkinter安装失败
        pause
        exit /b 1
    )
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Pillow未安装，正在安装...
    pip install Pillow
    if errorlevel 1 (
        echo ❌ Pillow安装失败
        pause
        exit /b 1
    )
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  requests未安装，正在安装...
    pip install requests
    if errorlevel 1 (
        echo ❌ requests安装失败
        pause
        exit /b 1
    )
)

echo ✅ 依赖包检查完成

REM 检查软件数据文件
if not exist "software_data.json" (
    echo ❌ 错误：软件数据文件 software_data.json 不存在
    echo 请确保软件数据文件在程序目录中
    pause
    exit /b 1
)

echo ✅ 软件数据文件检查通过
echo.
echo 🚀 正在启动向导式软件管理器...
echo.

REM 启动程序
python wizard_ui_main.py

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    pause
)

echo.
echo 程序已退出
pause