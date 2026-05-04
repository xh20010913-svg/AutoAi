# AutoAi 自动化说明

## 架构总览

```
┌─────────────────────────────────────────────────┐
│  你 (用户)                                       │
│  └── 启动 dispatch 脚本 (手动或定时)             │
│                                                  │
│  dispatch.py                                     │
│  ├── 1. 从本地缓存读取 issue 状态 (不调 git)     │
│  ├── 2. 关闭 in_review 的任务 (调 1 次 multica)  │
│  ├── 3. 给空闲 agent 派发任务 (调 multica)        │
│  └── 4. 保存缓存，退出                           │
│                                                  │
│  Agent (自动)                                    │
│  ├── 收到任务通知                                │
│  ├── multica repo checkout (这里会弹 git 窗口)    │
│  ├── 写代码                                      │
│  └── git push (这里也会弹 git 窗口)              │
│                                                  │
│  项目经理 (我，自动)                              │
│  ├── 合并 agent 的分支到 master                  │
│  └── 标记任务 done                               │
└─────────────────────────────────────────────────┘
```

## 弹窗来源

弹窗来自 **multica CLI 内部调 git**，不是来自 dispatch 脚本。
dispatch 脚本已经用了 `STARTUPINFO(SW_HIDE)` 隐藏自己的窗口。

弹窗发生时机：
- Agent checkout 仓库时 (每个 agent 一次)
- Agent push 代码时
- 我合并分支时

## 怎么运行

### 方式 1: 手动运行 (推荐先试这个)
```bash
cd D:\code\AutoAi
python scripts/dispatch.py --sync
```
跑完就退出，不会一直弹窗。

### 方式 2: 静默运行 (双击)
双击 `scripts\run-dispatch-once.vbs`
完全无窗口，跑完自动退出。

### 方式 3: 定时自动运行 (推荐)
用 Windows 任务计划程序：
1. Win+R → taskschd.msc
2. 创建基本任务
3. 触发器: 每 5 分钟
4. 操作: 启动程序 `wscript.exe`
5. 参数: `D:\code\AutoAi\scripts\run-dispatch-once.vbs`

这样每 5 分钟自动检查一次，不需要手动操作。

### 方式 4: 持续循环 (不推荐，会一直占用终端)
```bash
python scripts/dispatch.py --sync --loop 120
```

## 命令参数

| 参数 | 说明 |
|------|------|
| `--sync` | 先从 multica 同步状态 (否则用本地缓存) |
| `--loop N` | 每 N 秒循环一次 (不加则跑一次就退出) |
| `--dry-run` | 只看不干，测试用 |
| `--reset` | 清除本地缓存 |
