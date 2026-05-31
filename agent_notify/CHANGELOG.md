# Changelog

All notable changes to Agent Notify will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-05-31

### Added

- 测试通知功能改进：发送结果反馈（✓ 已发送 / ✗ 失败），2 秒后自动恢复按钮状态
- 向导自动配置 Claude Code Hook：配置过程中显示进度状态，成功/失败时显示明确提示
- 诊断功能：检查信号目录、Claude Code Hook、Toast 通知权限、配置文件，显示诊断结果对话框
- 反馈提示优化：标题映射提取到配置文件（title_map），支持用户自定义通知标题
- FAQ 和故障排除指南：创建 docs/troubleshooting.md，README 添加 FAQ 部分
- 自适应轮询机制：根据事件频率动态调整轮询间隔，夜间自动降低频率，添加性能监控统计
- 版本锁定文件：创建 requirements-lock.txt 确保构建一致性
- 产品需求文档（PRD）：定义产品定位、功能优先级、用户故事、发布计划
- 设置界面添加「帮助」按钮，链接到故障排除指南
- 重试机制：创建 retry.py 通用重试装饰器，信号文件解析、更新检查/下载支持重试

### Fixed

- 单实例锁竞态条件：使用 Windows Mutex 替代 PID 文件，消除 TOCTOU 竞态条件

### Changed

- 样式重构：提取 settings.py 样式方法到 ui/settings_styles.py，settings.py 从 1263 行减少到 1160 行
- 日志优化："节流抑制"改为"通知已发送，稍后再次提醒"，更用户友好
- 更新检查和下载失败后自动重试 3 次（指数退避）

## [1.2.0] - 2026-05-24

### Added

- 免打扰时段：可配置开始/结束时间，时段内自动静音所有通知
- 全局快捷键 Ctrl+Shift+P：暂停/恢复监控
- 版本号管理：`constants.__version__`，设置面板和托盘图标显示版本
- 通知节流：同一 agent + 事件类型 3 秒内不重复通知，防止通知风暴
- QMediaPlayer 错误状态自动重建

## [1.1.1] - 2026-05-24

### Added

- 统一日志系统（`log.py`），所有模块使用 Python logging，输出到 `~/.agent-notify/agent-notify.log`（轮转 5×1MB）
- hook 脚本集成测试（23 个新测试，含 subprocess 端到端验证）
- 配置校验：`settings.py` 对未知键记录警告日志

### Fixed

- 权限确认通知兜底：添加 PreToolUse 无 matcher hook，解决 Notification hook 不触发的问题
- PreToolUse hook 添加工具白名单过滤（Bash/Write/Edit/NotebookEdit），只读工具不再误触发通知
- claude_code adapter event_map 添加 tool_use/permission 映射为 WAITING 类型
- `notification.py` 添加 try/except 错误处理（PowerShell 不可用、QMediaPlayer 失败不再静默崩溃）
- `ensure_app_running()` 改为非阻塞，不再延迟 Claude Code 响应
- `_processed` 集合改用 OrderedDict LRU 淘汰，避免无限增长
- 移除 README 和 CHANGELOG 中虚假的 CI/CD 声明

## [1.1.0] - 2026-05-23

### Added

- Windsurf IDE 适配器（窗口标题轮询检测，与 Cursor 同架构）

### Fixed

- PreToolUse hook 支持：AskUserQuestion / ExitToolMode 触发通知
- PyInstaller 打包配置添加 adapters.windsurf

## [1.0.0] - 2025-05-22

### Added

- 多 Agent 支持：Claude Code / Cursor / Aider 开箱即用
- YAML 自定义 Agent（零代码扩展）
- Python 适配器扩展（开发者模式）
- Windows Toast 通知 + 声音提醒（QMediaPlayer，支持 WAV/MP3/FLAC/OGG/M4A/AAC）
- 暗色科技风系统托盘 UI（GitHub trust-dark 配色）
- 自动检测已安装的 Agent（首次启动扫描）
- 开机自启动（Windows 注册表 Run 键）
- 单实例锁防止重复启动（PID 文件 + kernel32.OpenProcess）
- Claude Code hook 自动配置（`--install-hooks`）
- Aider notify-cmd 辅助脚本
- Cursor 窗口标题轮询检测
- EventBus 解耦架构（Adapter → EventBus → UI/通知）
- Adapter 继承层次（AgentAdapter → PollingAdapter → SignalFileAdapter）
- 93 个单元测试（3 层测试架构：纯 Python / mock / QApplication）
- 完整文档（README.md + TECHNICAL.md）
- MIT License
