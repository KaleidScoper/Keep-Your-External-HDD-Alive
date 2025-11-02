@echo off
chcp 65001 >nul
title 硬盘保活工具 - 打包脚本

echo ========================================
echo   硬盘保活工具 - 打包脚本
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境！
    echo.
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到PyInstaller！
    echo [信息] 正在安装PyInstaller...
    echo.
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo [错误] PyInstaller安装失败！
        echo 请手动运行: pip install pyinstaller
        echo.
        pause
        exit /b 1
    )
    echo [信息] PyInstaller安装成功！
    echo.
)

echo [1/3] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "硬盘保活工具.spec" del "硬盘保活工具.spec"
echo       完成！
echo.

echo [2/3] 开始打包...
echo       这可能需要几分钟时间，请耐心等待...
echo.

python -m PyInstaller --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --name="硬盘保活工具" ^
    --add-data="styles.qss;." ^
    --add-data="icon.ico;." ^
    --add-data="icon.png;." ^
    main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 打包失败！
    echo ========================================
    echo.
    echo 请检查:
    echo 1. 所有必需文件是否存在 (main.py, styles.qss, icon.ico)
    echo 2. PyQt5是否已正确安装
    echo 3. 错误日志中的具体问题
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo ========================================
echo          打包成功！
echo ========================================
echo.
echo 生成的exe文件位置: dist\硬盘保活工具.exe
echo.
echo 您可以:
echo 1. 进入 dist 目录测试运行
echo 2. 将 exe 文件复制到任何位置使用
echo 3. 分发给其他用户（无需Python环境）
echo.
echo 提示: build 和 .spec 文件可以删除，只保留 dist\硬盘保活工具.exe
echo.
pause

