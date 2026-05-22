# Contributing to Agent Notify

感谢你对 Agent Notify 的关注！以下是参与贡献的指南。

## 报告 Bug

在 [Issues](../../issues) 中创建新 issue，包含：

- 问题描述（期望行为 vs 实际行为）
- 复现步骤
- 环境信息（Windows 版本、Python 版本）
- 错误日志（如有）

## 提交功能建议

在 [Issues](../../issues) 中创建新 issue，标签为 `feature request`，描述：

- 你想要的功能
- 使用场景
- 建议的实现方式（可选）

## 提交代码

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/frist-wuw.git
cd frist-wuw/agent_notify
```

### 2. 搭建开发环境

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 4. 开发 & 测试

```bash
# 运行测试
python -m pytest tests/ -v

# 启动应用测试
python main.py
```

### 5. 提交 & PR

```bash
git add .
git commit -m "feat: 描述你的改动"
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 代码规范

- Python 3.10+ 兼容
- 使用类型注解（type hints）
- 函数/类必须有 docstring
- 变量名、函数名用英文
- 注释用中文（解释"为什么"，不解释"是什么"）

## 新增 Adapter

在 `adapters/` 下新建 `.py` 文件：

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

详见 [TECHNICAL.md](TECHNICAL.md) 的扩展性设计章节。

## 测试要求

- 新增代码必须有对应测试
- 所有测试必须通过：`python -m pytest tests/ -v`
- 测试分层：纯 Python → mock → QApplication
