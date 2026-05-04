' AutoAi Dispatcher — 单次静默运行器
' 双击运行一次后退出，不弹任何窗口
' 配合 Windows 任务计划程序使用
Set ws = CreateObject("WScript.Shell")
ws.Run "pythonw """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\dispatch.py"" --sync", 0, True
