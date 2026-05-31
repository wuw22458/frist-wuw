# 故障排除指南

本文档帮助你解决 Agent Notify 使用过程中的常见问题。

## 目录

- [安装问题](#安装问题)
- [通知问题](#通知问题)
- [Agent 集成问题](#agent-集成问题)
- [性能问题](#性能问题)
- [其他问题](#其他问题)

---

## 安装问题

### Q: Windows Defender 提示 AgentNotify.exe 不安全

**原因**：未签名的 exe 文件可能被 Windows Defender 标记为潜在威胁。

**解决方案**：
1. 点击"更多信息" → "仍要运行"
2. 或者将 AgentNotify.exe 添加到 Windows Defender 排除列表：
   - 打开"Windows 安全中心" → "病毒和威胁防护" → "管理设置"
   - 在"排除项"中添加 AgentNotify.exe

### Q: 安装后无法启动

**可能原因**：
1. 缺少 Visual C++ 运行时
2. 权限不足

**解决方案**：
1. 安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. 右键以管理员身份运行
3. 检查 `~/.agent-notify/crash.log` 查看错误详情

### Q: 如何完全卸载 Agent Notify？

**步骤**：
1. 通过控制面板或设置卸载程序
2. 手动删除用户数据（可选）：
   ```
   删除文件夹: %USERPROFILE%\.agent-notify
   ```
3. 清理注册表自启动项（可选）：
   ```
   HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
   删除 AgentNotify 键值
   ```

---

## 通知问题

### Q: 收不到通知

**排查步骤**：
1. **检查通知权限**：
   - 打开设置 → 系统 → 通知
   - 确保"获取来自应用和其他发送者的通知"已开启
   - 找到 Agent Notify，确保通知权限已开启

2. **检查应用设置**：
   - 右键托盘图标 → 设置
   - 确保"显示系统通知"已开启
   - 确保相关 Agent 的监控已开启

3. **检查免打扰模式**：
   - 确保不在免打扰时段内
   - 或者临时关闭免打扰模式

4. **使用诊断功能**：
   - 打开设置 → 点击"诊断"按钮
   - 检查各项配置是否正常

### Q: 通知声音不播放

**排查步骤**：
1. **检查音量设置**：
   - 打开设置 → 调整音量滑块
   - 确保"播放提示音"已开启

2. **检查系统音量**：
   - 确保系统未静音
   - 确保应用音量未被单独静音

3. **测试提示音**：
   - 打开设置 → 点击"试听"按钮
   - 如果无法播放，尝试更换提示音文件

### Q: 通知显示但没有声音

**可能原因**：
1. 提示音文件损坏或格式不支持
2. QMediaPlayer 初始化失败

**解决方案**：
1. 打开设置 → 点击"恢复默认"按钮
2. 或者手动选择一个 WAV/MP3 文件作为提示音

---

## Agent 集成问题

### Q: Claude Code 不发送通知

**排查步骤**：
1. **检查 Hook 配置**：
   ```bash
   # 查看 Claude Code 设置
   cat ~/.claude/settings.json
   ```
   确保包含 `hooks` 配置项

2. **重新配置 Hook**：
   ```bash
   AgentNotify.exe --install-hooks
   ```

3. **检查信号目录**：
   - 打开 `%USERPROFILE%\.agent-notify`
   - 检查是否有 JSON 信号文件
   - 如果有文件但没有通知，检查日志

4. **查看日志**：
   - 打开设置 → 点击"查看日志"按钮
   - 查找 `claude_code` 相关的错误信息

### Q: Cursor/Windsurf 不发送通知

**排查步骤**：
1. **确认窗口标题**：
   - Cursor 窗口标题应包含 "Cursor"
   - Windsurf 窗口标题应包含 "Windsurf"
   - 如果标题被修改，通知可能无法检测

2. **检查轮询间隔**：
   - 默认轮询间隔为 3 秒
   - 如果需要更快响应，可考虑使用 Claude Code 的 Hook 机制

### Q: 如何添加自定义 Agent？

**YAML 方式（推荐）**：
1. 编辑 `%USERPROFILE%\.agent-notify\custom_agents.yaml`
2. 添加 Agent 配置：
   ```yaml
   agents:
     - agent_id: my-agent
       display_name: My Agent
       description: 我的自定义 Agent
       glob_pattern: "my-agent_*.json"
       event_map:
         needs_input: waiting
         done: completed
   ```
3. 重启应用

**信号文件格式**：
```json
{
  "event": "needs_input",
  "message": "请确认这个改动",
  "timestamp": 1234567890,
  "source": "my-agent"
}
```

---

## 性能问题

### Q: CPU 占用过高

**可能原因**：
1. 多个 Agent 同时轮询
2. 轮询间隔过短

**解决方案**：
1. 禁用不需要的 Agent 监控
2. 检查是否有异常的信号文件堆积
3. 重启应用

### Q: 内存占用过高

**可能原因**：
1. 通知历史过多
2. QMediaPlayer 资源泄漏

**解决方案**：
1. 清除通知历史（设置 → 清除历史）
2. 重启应用
3. 检查日志是否有 QMediaPlayer 错误

---

## 其他问题

### Q: 如何查看应用日志？

**方法 1**：
- 打开设置 → 点击"查看日志"按钮

**方法 2**：
- 直接打开文件：`%USERPROFILE%\.agent-notify\agent-notify.log`

### Q: 如何报告 Bug？

1. 收集以下信息：
   - 应用版本（托盘图标显示）
   - 操作系统版本
   - 错误日志（`agent-notify.log` 和 `crash.log`）
   - 复现步骤

2. 在 GitHub 提交 Issue：
   - 访问 https://github.com/wuw22458/agent_notify/issues
   - 点击 "New Issue"
   - 填写问题描述和相关信息

### Q: 如何贡献代码？

请参阅 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解贡献指南。

---

## 获取帮助

如果以上方法都无法解决问题：

1. **查看 GitHub Issues**：
   - https://github.com/wuw22458/agent_notify/issues
   - 搜索是否有类似问题

2. **提交新 Issue**：
   - 详细描述问题
   - 附上日志和截图
   - 说明复现步骤

3. **联系作者**：
   - GitHub: @wuw22458
