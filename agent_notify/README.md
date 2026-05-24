# Agent Notify

> 通用 AI Agent 通知中心 — 当 Claude Code、Cursor、Windsurf、Aider 需要你时，第一时间提醒。

Agent Notify 是一个 Windows 系统托盘应用，统一监控多个 AI 编码 Agent 的状态。当 Agent 需要权限确认或任务完成时，通过 Toast 通知 + 声音提醒你，再也不会错过。

## 功能特性

- **多 Agent 支持** — Claude Code / Cursor / Windsurf / Aider 开箱即用，YAML 自定义更多 Agent
- **Windows Toast 通知 + 声音提醒** — 系统原生通知，支持自定义提示音
- **暗色科技风 UI** — GitHub trust-dark 配色，系统托盘图标 + 设置界面
- **自动检测** — 首次启动自动扫描已安装的 Agent，零配置开箱即用
- **开机自启** — Windows 注册表 Run 键，单实例锁防止重复启动
- **插件化架构** — Adapter 模式 + EventBus 解耦，新增 Agent 无需修改核心代码

## 快速开始

### 方式一：下载 exe（推荐）

1. 从 [Releases](../../releases) 下载 `AgentNotify.exe`
2. 双击运行，托盘区出现图标
3. 配置 Claude Code hook：

```bash
# 找到 AgentNotify.exe 的路径，运行：
AgentNotify.exe --install-hooks
```

### 方式二：从源码运行

```bash
git clone https://github.com/wuw22458/frist-wuw.git
cd frist-wuw/agent_notify
pip install -r requirements.txt
python main.py
```

### 配置 Claude Code hook

```bash
python main.py --install-hooks
```

这会自动将 hook 脚本写入 `~/.claude/settings.json`，Claude Code 触发 Notification 和 Stop 事件时会调用 Agent Notify。

## 使用指南

### 托盘图标

- **左键点击** — 打开设置界面
- **右键菜单** — 暂停/恢复通知、退出

### 设置界面

- 启用/禁用各 Agent 的通知
- 开关声音和 Toast 通知
- 自定义提示音文件（支持 WAV/MP3/FLAC/OGG/M4A/AAC）
- 开机自启开关

### 各 Agent 配置

| Agent | 配置方式 | 说明 |
|-------|---------|------|
| Claude Code | `--install-hooks` 自动配置 | Hook 脚本写入 `~/.claude/settings.json` |
| Cursor | 自动检测 | 窗口标题轮询，检测 "needs attention" |
| Windsurf | 自动检测 | 窗口标题轮询，检测 "needs attention" |
| Aider | 手动配置 `--notify-cmd` | `aider --notify-cmd "python aider_notify_helper.py"` |

### CLI 命令

```bash
python main.py                 # 启动托盘应用
python main.py --install-hooks # 配置 Claude Code hooks
python main.py --auto-start    # 设置开机自启
python main.py --no-auto-start # 取消开机自启
```

## 添加自定义 Agent

### YAML 方式（零代码）

编辑 `~/.agent-notify/custom_agents.yaml`：

```yaml
agents:
  - agent_id: my-agent
    display_name: My Agent
    description: 监控我的自定义 AI agent
    glob_pattern: "my-agent_*.json"
    event_map:
      needs_input: waiting
      done: completed
    poll_interval_ms: 2000
```

你的 Agent 只需要写入 JSON 信号文件到 `~/.agent-notify/`：

```json
{"event": "needs_input", "message": "请确认这个改动"}
```

### Python 方式（开发者）

在 `adapters/` 下新建 `.py` 文件，继承 `SignalFileAdapter` 或 `PollingAdapter`：

```python
from adapters.signal_file import SignalFileAdapter
from adapters.registry import register_adapter
from events import EventType

@register_adapter
class MyAgentAdapter(SignalFileAdapter):
    agent_id = "my-agent"
    display_name = "My Agent"
    glob_pattern = "my-agent_*.json"
    event_map = {"needs_input": EventType.WAITING, "done": EventType.COMPLETED}
```

重启应用即可生效。

## 项目结构

```
agent_notify/
├── main.py              # 入口 + CLI
├── tray_app.py          # 系统托盘 UI
├── notification.py      # Toast 通知 + 声音
├── event_bus.py         # 中央事件总线
├── events.py            # 统一事件模型
├── settings.py          # JSON 配置管理
├── constants.py         # 共享常量
├── lock_utils.py        # 进程锁
├── adapters/            # Agent 适配器
│   ├── base.py          # 抽象基类
│   ├── registry.py      # 注册表
│   ├── signal_file.py   # 信号文件轮询
│   ├── claude_code.py   # Claude Code
│   ├── cursor.py        # Cursor
│   ├── aider.py         # Aider
│   └── custom.py        # YAML 自定义加载
├── hooks/
│   └── claude_hook.py   # Claude Code hook 脚本
├── tests/               # 单元测试（93 个）
├── resources/           # 图标 + 提示音
├── requirements.txt     # 运行时依赖
├── requirements-dev.txt # 开发/构建依赖
└── agent_notify.spec    # PyInstaller 配置
```

## 开发指南

### 环境

- Python 3.10+
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发/测试依赖
```

### 运行测试

```bash
python -m pytest tests/ -v
```

### 打包

```bash
pyinstaller agent_notify.spec --noconfirm
# 产物：dist/AgentNotify.exe
```

## 技术栈

- Python 3.10+ + PySide6
- Windows Toast 通知（PowerShell + Windows Runtime API）
- PyInstaller 打包
- Windows 注册表（开机自启）

## 相关文档

- [CHANGELOG.md](CHANGELOG.md) — 版本变更记录
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献指南
- [TECHNICAL.md](TECHNICAL.md) — 技术设计文档

## License

MIT
