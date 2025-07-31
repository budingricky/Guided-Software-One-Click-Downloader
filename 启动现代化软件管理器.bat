@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    🚀 软件资源整合管理器 v3.0 Modern
echo ========================================
echo.
echo 正在启动现代化界面版本...
echo.

cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 📦 检查依赖包...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo 📥 正在安装CustomTkinter依赖包...
    pip install customtkinter>=5.2.0 Pillow>=9.0.0
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

REM 检查数据文件
if not exist "software_data.json" (
    echo ❌ 错误：未找到软件数据文件 software_data.json
    echo 请确保该文件存在于当前目录
    pause
    exit /b 1
)

echo ✅ 依赖检查完成
echo 🎨 启动现代化界面...
echo.

REM 启动程序
python modern_ui_main.py

REM 程序结束后的处理
if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    echo 请检查错误信息并重试
    pause
) else (
    echo.
    echo ✅ 程序已正常退出
)