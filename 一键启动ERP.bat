@echo off
chcp 65001 >nul
title ERP一键启动（前后端）

echo.
echo ================================================
echo    辽宁跨境宝盒 - 一键启动脚本
echo ================================================
echo.

REM ===== 选择启动模式 =====
echo 请选择启动模式：
echo   [1] 只启动前端（后端已运行）
echo   [2] 只启动后端
echo   [3] 同时启动前后端（推荐）
echo   [4] 退出
echo.
set /p choice=请输入选项 [1-4]:

if "%choice%"=="1" goto :frontend
if "%choice%"=="2" goto :backend
if "%choice%"=="3" goto :both
if "%choice%"=="4" exit
goto :end

:frontend
echo [启动] 仅启动前端...
cd /d %~dp0\erp-admin
start "ERP前端" cmd /c "npm run dev && pause"
goto :done

:backend
echo [启动] 仅启动后端...
cd /d %~dp0\backend
start "ERP后端" cmd /c "启动后端.bat"
goto :done

:both
echo [启动] 启动后端服务...
cd /d %~dp0\backend
start "ERP后端" cmd /c "启动后端.bat"

echo [等待] 等待后端启动...
timeout /t 3 /nobreak >nul

echo [启动] 启动前端服务...
cd /d %~dp0\erp-admin
start "ERP前端" cmd /c "npm run dev && pause"
goto :done

:done
echo.
echo ================================================
echo    启动完成！
echo ================================================
echo.
echo    前端地址: http://localhost:5173
echo    后端地址: http://localhost:8000
echo    Swagger:  http://localhost:8000/swagger/
echo.
echo    请勿关闭此窗口
echo ================================================
echo.
pause

:end
