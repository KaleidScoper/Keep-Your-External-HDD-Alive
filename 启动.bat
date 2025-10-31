@echo off
chcp 65001 >nul
title 硬盘保活工具 - 启动中...

echo ========================================
echo    硬盘保活工具 - 启动脚本
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境！
    echo.
    echo 请先安装Python 3.6或更高版本：
    echo 下载地址：https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH" 选项
    echo.
    pause
    exit /b 1
)

echo [信息] Python环境检测通过
echo [信息] 正在启动硬盘保活工具...
echo.

REM 启动程序
python main.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 程序运行出错！
    echo ========================================
    echo.
    pause
    exit /b 1
)

