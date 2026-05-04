' 停止 AutoAi 后台守护进程
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
stopFile = scriptDir & "\.daemon_stop"
' 创建 stop 文件，守护进程检测到后会自行退出
Set file = fso.CreateTextFile(stopFile, True)
file.WriteLine "stop"
file.Close
