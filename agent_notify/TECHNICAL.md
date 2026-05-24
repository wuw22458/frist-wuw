# Agent Notify — 技术设计文档

## 1. 项目背景

### 问题

AI 编码 Agent（Claude Code、Cursor、Windsurf、Aider 等）在执行任务时需要用户介入（权限确认、任务完成），但各 Agent 的通知机制独立且碎片化：

- Claude Code 通过 hook 脚本通知
- Cursor / Windsurf 通过窗口标题变化提示
- Aider 通过 `--notify-cmd` 参数支持自定义通知

用户同时使用多个 Agent 时，容易错过关键通知，导致 Agent 长时间等待。

### 目标

构建一个**统一通知中心**：
- 聚合多个 Agent 的状态事件
- 通过系统级通知（Toast + 声音）提醒用户
- 插件化架构，支持快速接入新 Agent
- 用户无需编程即可添加自定义 Agent

## 2. 架构设计

### 整体架构

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Claude Code  │  │   Cursor     │  │  Windsurf    │  │    Aider     │
│  (hook 脚本)  │  │ (窗口标题轮询) │  │ (--notify-cmd)│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│                 Adapter 层                       │
│  ClaudeCodeAdapter │ CursorAdapter │ WindsurfAdapter │ AiderAdapter│
│         SignalFileAdapter (中间层)                │
│              PollingAdapter (QTimer)              │
│              AgentAdapter (抽象基类)              │
└──────────────────────┬──────────────────────────┘
                       │ emit(AgentEvent)
                       ▼
              ┌─────────────────┐
              │    EventBus     │
              │  (Qt Signal)    │
              └────────┬────────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
     ┌───────────┐ ┌────────┐ ┌──────────┐
     │ TrayApp   │ │ Toast  │ │ 声音播放  │
     │ (托盘 UI) │ │ 通知   │ │ QMedia   │
     └───────────┘ └────────┘ └──────────┘
```

核心设计：**EventBus 解耦**。Adapter 只负责检测状态并发射事件，UI 和通知通过订阅 EventBus 接收事件，互不依赖。

### Adapter 继承层次

```python
AgentAdapter (抽象基类)
  │  agent_id, display_name, description
  │  emit(), is_enabled(), detect()
  │
  └── PollingAdapter (QTimer 轮询)
        │  poll_interval_ms, start(), stop()
        │
        ├── SignalFileAdapter (JSON 文件信号)
        │     │  glob_pattern, exclude_names, event_map
        │     │  check() → glob → parse → emit → delete
        │     │
        │     ├── ClaudeCodeAdapter  (23 行)
        │     ├── AiderAdapter       (~30 行)
        │     └── Custom_*           (YAML 动态生成)
        │
        ├── CursorAdapter (窗口标题检测)
        │     │  _get_cursor_window_titles() via ctypes
        │     │  状态机: idle ↔ waiting
        │
        └── WindsurfAdapter (窗口标题检测)
              │  _get_windsurf_window_titles() via ctypes
              │  状态机: idle ↔ waiting
```

**关键简化**：SignalFileAdapter 中间层吸收了 JSON 文件轮询的通用逻辑，子类只需声明 4 个类属性（agent_id、glob_pattern、exclude_names、event_map），无需实现 check() 方法。Claude Code adapter 从 103 行简化到 23 行。

### 事件模型

```python
class EventType(str, Enum):
    WAITING = "waiting"      # Agent 需要用户介入
    COMPLETED = "completed"  # 任务完成
    ERROR = "error"          # 出错
    INFO = "info"            # 一般信息

@dataclass
class AgentEvent:
    agent_id: str           # 来源标识，如 "claude-code"
    event_type: str         # EventType 值
    message: str            # 显示给用户的消息
    timestamp: float        # time.time()
    metadata: dict          # 扩展字段
```

## 3. 关键设计决策

### 决策 1：轮询 vs inotify/watchdog

**问题**：如何检测信号文件的变化？

**方案**：QTimer 轮询（1 秒间隔）

**权衡**：
- inotify/watchdog 响应更快（毫秒级），但依赖跨平台库，Windows 上 inotify 不可用
- 1 秒轮询对通知场景完全足够（用户不会在意 1 秒延迟）
- 实现简单，无需额外依赖，QTimer 已由 PySide6 提供
- CPU 开销可忽略（glob 一个目录 + 读几个小文件）

### 决策 2：PID 文件锁 vs socket 锁

**问题**：如何防止重复启动？

**方案**：PID 文件锁（`~/.agent-notify/.lock`）

**权衡**：
- socket 锁更可靠（端口占用是 OS 级别的），但需要选择端口、处理冲突
- PID 文件锁实现简单，通过 `kernel32.OpenProcess` 查询进程是否存活
- 使用 `PROCESS_QUERY_LIMITED_INFORMATION`（0x1000）最低权限，不会向目标进程发送信号
- 异常情况（进程崩溃未清理锁文件）通过 PID 检测自动恢复

### 决策 3：PowerShell Toast vs plyer

**问题**：如何发送 Windows 系统通知？

**方案**：PowerShell + Windows Runtime API

**权衡**：
- plyer 跨平台但依赖额外包，且 Windows 上通知样式受限
- PowerShell 原生调用 Windows Notification API，无额外依赖
- 支持 Toast 通知的所有特性（标题、正文、图标、声音）
- 唯一缺点是仅支持 Windows，但目标用户群体明确是 Windows 开发者

### 决策 4：EventBus 解耦 vs 直接调用

**问题**：Adapter 检测到事件后如何通知 UI 和通知引擎？

**方案**：Qt Signal 事件总线（EventBus 单例）

**权衡**：
- 直接调用耦合度高：新增 Adapter 需要修改 TrayApp 和 NotificationEngine
- EventBus 模式：Adapter 只发射事件，订阅者自行处理
- 新增 Adapter 无需修改任何现有代码
- 新增通知方式（如 Slack webhook）只需订阅 EventBus
- 代价是多了一层间接性，调试时需要追踪信号连接

### 决策 5：YAML 自定义 Agent vs 纯 Python 扩展

**问题**：如何降低用户添加 Agent 的门槛？

**方案**：双轨制 — YAML 配置（零代码）+ Python 继承（开发者）

**权衡**：
- 纯 Python 扩展灵活但需要编程能力
- YAML 配置覆盖 90% 的信号文件类 Agent（写 JSON 文件 → 轮询 → 通知）
- YAML 动态创建类（`type()` 构造），通过 `@register_adapter` 注册
- PyYAML 不可用时自动 fallback 到 JSON 解析（YAML 的子集）
- 不支持复杂逻辑（如 Cursor 的窗口标题检测），这类场景仍需 Python

### 决策 6：路径解耦（~/.claude → ~/.agent-notify）

**问题**：原始设计将数据存储在 `~/.claude/agent-notify/`，与 Claude Code 耦合。

**方案**：迁移到 `~/.agent-notify/`，首次启动自动迁移

**权衡**：
- 独立路径体现"通用工具"定位，不依附于任何特定 Agent
- 迁移逻辑只复制 config.json 和 hooks/，不复制 .lock 和信号文件
- 新路径已存在时不覆盖，避免数据丢失
- 旧路径保留不删除，用户可手动清理

## 4. 扩展性设计

### 新增 Adapter（Python 方式）

1. 在 `adapters/` 下新建 `.py` 文件
2. 继承 `SignalFileAdapter`（信号文件类）或 `PollingAdapter`（自定义检测逻辑）
3. 用 `@register_adapter` 装饰
4. 定义 `agent_id`、`display_name`、`event_map` 等类属性
5. 重启应用，`adapters/__init__.py` 的 `pkgutil` 自动发现并导入

自动发现机制：
```python
# adapters/__init__.py
for _importer, _modname, _ispkg in pkgutil.iter_modules(__path__):
    if _modname not in _SKIP:
        importlib.import_module(f".{_modname}", __package__)
```

### YAML 自定义 Agent 协议

配置文件：`~/.agent-notify/custom_agents.yaml`

```yaml
agents:
  - agent_id: my-agent        # 必填，唯一标识
    display_name: My Agent     # 可选，默认等于 agent_id
    description: 功能描述      # 可选
    glob_pattern: "my_*.json"  # 可选，默认 "{agent_id}_*.json"
    exclude_names: []          # 可选，排除的文件名
    event_map:                 # 可选，原始 event → EventType
      needs_input: waiting     #   支持: waiting, completed, error, info
      done: completed
    poll_interval_ms: 1000     # 可选，轮询间隔
```

### 信号文件 JSON 协议

Agent 需要写入 JSON 文件到 `~/.agent-notify/`：

```json
{
  "event": "notification",
  "message": "Claude Code 需要你的确认",
  "timestamp": 1700000000000,
  "source": "claude-code"
}
```

- `event`：事件类型，由 adapter 的 `event_map` 映射
- `message`：显示给用户的消息
- `timestamp`：毫秒时间戳（可选）
- `source`：来源标识（可选）

文件名格式：`{timestamp}.json`（保证唯一且有序）

## 5. 测试策略

### 三层测试架构

按依赖复杂度分层，优先写纯 Python 测试（ROI 最高）：

| 层级 | 依赖 | 测试内容 | 示例 |
|------|------|---------|------|
| 第一层 | 无 Qt、无 mock | 数据类、配置、注册表 | AgentEvent 构造、配置读写、迁移逻辑 |
| 第二层 | mock（无 Qt） | 外部依赖调用 | 进程检测、Agent 检测、Cursor 状态机 |
| 第三层 | QApplication | Qt Signal/QTimer | EventBus 单例、信号文件轮询 |

### 测试覆盖

- 70 个测试用例，覆盖所有核心模块
- `conftest.py` 提供 `qapp`（session 级 QApplication）和 `signal_dir`（monkeypatch 隔离临时目录）
- 运行：`python -m pytest tests/ -v`

## 6. 打包与分发

### PyInstaller 配置

- 单文件模式（`onefile`），产物为 `AgentNotify.exe`（~56MB）
- `console=False`，无控制台窗口
- 打包资源：`resources/`（图标、提示音）、`hooks/`（Claude Code hook 脚本）、`adapters/`（自定义 Agent 包）
- UPX 压缩启用

### 依赖管理

```
PySide6 >= 6.11        # Qt 框架
pyinstaller >= 6.20    # 打包（仅开发依赖）
```

运行时无其他依赖，所有功能通过标准库 + PySide6 实现。
