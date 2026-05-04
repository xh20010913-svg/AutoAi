@echo off
REM AutoAi Dispatcher — 静默运行脚本
REM 使用 pythonw.exe 运行，不显示命令行窗口
REM 每 30 秒扫描一次

pythonw "%~dp0dispatch.py" --loop 30
