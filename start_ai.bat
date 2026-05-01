@echo off
chcp 65001 >nul
title 拓岳AI服务
echo 正在启动拓岳AI服务...
start "" python "d:\试验场\ERP\backend\ai_server.py"
echo 已在新窗口启动
