# first-wuw

wuw 的个人项目仓库，包含以下独立子项目。

## 📁 项目结构

```
├── agent_notify/     # 🖥️ Agent Notify — 系统托盘通知应用
├── clipboard_app/    # 📋 Clipboard History — 剪贴板历史管理
└── doc_pipeline/     # 📄 Doc Pipeline — 文档处理工具
```

## 🖥️ Agent Notify

统一监控多个 AI Agent（Claude Code、Cursor、Windsurf、Aider）通知状态的 Windows 系统托盘应用。

- **技术栈**：Python + PySide6，EventBus + Adapter 插件化架构
- **功能**：免打扰模式、全局快捷键、通知节流、自动更新
- **文档**：[agent_notify/README.md](agent_notify/README.md)

## 📋 Clipboard History

剪贴板历史记录管理工具，支持文本和图片。

- **技术栈**：Python + PySide6
- **功能**：剪贴板监控、历史卡片展示、图片预览

## 📄 Doc Pipeline

文档处理管线，支持多种格式转换和分析。

- **技术栈**：Python
- **功能**：文档扫描、提取、分析、转换、报告生成

## 开发

每个子项目有独立的依赖和测试：

```bash
# Agent Notify
cd agent_notify
pip install -r requirements.txt
python -m pytest tests/

# Clipboard History
cd clipboard_app
pip install -r requirements.txt

# Doc Pipeline
cd doc_pipeline
pip install -r requirements.txt
```

## 许可证

[MIT License](agent_notify/LICENSE)
