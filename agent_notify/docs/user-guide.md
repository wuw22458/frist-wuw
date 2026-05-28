# Agent Notify 用户指南

## 安装

### 下载 exe（推荐）

1. 从 [GitHub Releases](https://github.com/wuw22458/agent_notify/releases) 下载 `AgentNotify.exe`
2. 双击运行，系统托盘区出现蓝色图标
3. 运行以下命令配置 Claude Code hook：

```bash
AgentNotify.exe --install-hooks
```

### 从源码运行

```bash
git clone https://github.com/wuw22458/agent_notify.git
cd agent_notify
pip install -r requirements.txt
python main.py
```

## 基本使用

### 托盘图标

| 操作 | 效果 |
|------|------|
| 左键点击 | 打开设置面板 |
| 右键点击 | 弹出菜单（设置/暂停/退出） |

### 图标状态

| 图标颜色 | 含义 |
|----------|------|
| 蓝色 | 正常监控中 |
| 蓝色闪烁 | 刚收到通知 |
| 橙色 | 已暂停 |

## 设置面板

### 状态区

- **监控中 / 已暂停** — 当前运行状态
- **暂停按钮** — 临时停止所有通知

### 监控来源

每个 Agent 有独立开关，可单独启用或禁用通知。

### 通知选项

- **播放提示音** — 收到通知时播放声音
- **显示系统通知** — 收到通知时弹出 Windows Toast
- **更换 / 恢复默认 / 试听** — 自定义提示音文件（支持 WAV、MP3）

### 免打扰

- 启用后在指定时段内静音所有通知
- 支持跨午夜时段（如 22:00 到 08:00）
- 时间格式：HH:MM（24 小时制）

### 最近通知

显示最近收到的通知记录，包含时间、类型标签和消息内容。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Shift+P | 全局暂停/恢复通知 |

## 各 Agent 配置

### Claude Code

运行 `AgentNotify.exe --install-hooks` 自动配置。之后 Claude Code 在需要确认或任务完成时会自动触发通知。

### Cursor / Windsurf

自动检测已安装的客户端，通过窗口标题轮询检测 "needs attention" 状态。首次启动时自动启用。

### Aider

启动 Aider 时添加参数：

```bash
aider --notify-cmd "python aider_notify_helper.py"
```

### 自定义 Agent（YAML）

编辑 `~/.agent-notify/custom_agents.yaml`：

```yaml
agents:
  - agent_id: my-agent
    display_name: My Agent
    description: 我的自定义 agent
    glob_pattern: "my-agent_*.json"
    event_map:
      needs_input: waiting
      done: completed
    poll_interval_ms: 2000
```

然后让你的 Agent 写入 JSON 信号文件到 `~/.agent-notify/`：

```json
{"event": "needs_input", "message": "请确认这个改动"}
```

## CLI 命令

```bash
AgentNotify.exe                 # 启动托盘应用
AgentNotify.exe --install-hooks # 配置 Claude Code hooks
AgentNotify.exe --auto-start    # 设置开机自启
AgentNotify.exe --no-auto-start # 取消开机自启
```

## 配置文件

配置文件位于 `~/.agent-notify/config.json`，支持以下字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sound_enabled` | bool | `true` | 是否播放提示音 |
| `toast_enabled` | bool | `true` | 是否显示 Toast 通知 |
| `auto_start` | bool | `true` | 是否开机自启 |
| `custom_sound` | string | `""` | 自定义提示音路径 |
| `dnd_enabled` | bool | `false` | 是否启用免打扰 |
| `dnd_start` | string | `"22:00"` | 免打扰开始时间 |
| `dnd_end` | string | `"08:00"` | 免打扰结束时间 |
| `max_history` | int | `200` | 最大通知历史数 |

## 日志与崩溃

- 运行日志：`~/.agent-notify/agent-notify.log`
- 崩溃日志：`~/.agent-notify/crash.log`（自动检测，下次启动提示）

## 常见问题

### 没有收到通知

1. 检查托盘图标是否为蓝色（非橙色暂停状态）
2. 检查对应 Agent 的开关是否启用
3. 检查是否在免打扰时段内
4. 查看日志文件排查问题

### Claude Code hook 不生效

1. 确认运行了 `--install-hooks`
2. 检查 `~/.claude/settings.json` 中是否包含 Agent Notify 的 hook 配置
3. 确认 Agent Notify 托盘应用正在运行

### 声音不播放

1. 检查"播放提示音"开关是否启用
2. 确认系统音量未静音
3. 尝试"试听"按钮测试
4. 如果使用自定义音频，确认文件格式为 WAV 或 MP3

### 开机自启不生效

1. 检查 `auto_start` 配置是否为 `true`
2. 手动运行 `AgentNotify.exe --auto-start`
3. 检查 Windows 任务管理器 → 启动 页签
