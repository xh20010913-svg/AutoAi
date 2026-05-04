' 启动 AutoAi 后台守护进程 (无窗口)
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("WScript.Shell")
ws.Run "pythonw """ & scriptDir & "\daemon.py""", 0, False
