' AutoAi Dispatcher — 完全静默启动器
' 用 WScript 运行，不显示任何窗口
Set ws = CreateObject("WScript.Shell")
ws.Run "pythonw """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\dispatch.py"" --loop 30", 0, False
