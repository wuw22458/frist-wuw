# Changelog

All notable changes to Agent Notify will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
- 67 个单元测试（3 层测试架构：纯 Python / mock / QApplication）
- 完整文档（README.md + TECHNICAL.md）
- GitHub Actions CI/CD（自动测试 + 打包）
- MIT License
