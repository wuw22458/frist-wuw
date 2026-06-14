---
name: ds-project-optimizer
description: >-
  对全栈数据科学项目进行深度审查、性能优化与可视化美化，输出可直接放入作品集的精品项目。
  适用于用户提到"优化数据科学项目"、"美化项目报告"、"提升代码质量"、"准备作品集项目"、
  "审查 notebook 代码"、"提升模型性能"、"项目重构"、"DS项目优化"等场景。
  也适用于用户想把"初学者完成品"提升为"专业可展示作品"的任何数据科学项目。
---

# 数据科学项目优化器

将数据科学项目从"初学者完成品"提升为"专业可展示作品"。

## 前置条件

执行前必须确认：

1. **项目路径存在**：项目目录必须包含 `main.py`（或 `notebook.ipynb`）、`README.md`、`data/` 目录。缺任一文件则停止并报错：
   ```
   项目路径无效：{path}
   缺失文件：{list}
   请确认生成任务已正确完成。
   ```

2. **读取优化日志**：检查项目同级目录下的 `project_optimization_log.json`。若当前项目已标记为 `completed` 且用户无明确要求重新优化，则跳过并告知用户。

3. **创建备份**：在任何修改操作前，将原始文件复制到 `backup_original/` 子目录。

## 优化流程（5 阶段，必须按顺序执行）

### 阶段 1：代码质量审查

**目标**：零规范错误，零数据泄漏，零逻辑缺陷。

**步骤**：

1. **诊断扫描** — 调用 `diagnose` skill（如不可用则手动审查），逐项排查：
   - 数据泄漏：在 split 之前做了标准化/特征选择/缺失值填补 → 移到 split 之后
   - 缺失值处理：直接 dropna() 而非先分析缺失模式 → 补充缺失值分析步骤
   - 标签对齐：train/test 的 y 是否与 X 正确对应
   - **评估指标合理性**：分类任务检查类别分布，若少数类占比 < 20% 则 accuracy 不可靠，改用 F1/ROC-AUC/PR-AUC；回归任务检查是否存在严重离群值，若有则补充 MAE 或 RMSLE

2. **代码风格审查** — 调用 `grill-me` skill 审查代码结构与最佳实践，记录所有建议。

3. **格式化修复** — 对 Python 文件运行 `black` 或 `autopep8`（若不可用则手动对齐缩进、行宽 ≤ 100、移除行尾空格）。

4. **测试验证**：
   - 若存在 `test_main.py`，运行 `pytest` 确保全部通过；失败则修复源码
   - 若测试不足（< 3 个测试用例），调用 `tdd` skill 补充至少 1 个业务逻辑测试（如预测值分布合理、管道输出形状正确）
   - 若无测试文件，创建 `test_main.py` 并加入核心测试

**验收标准**：black/pylint 无报错；pytest 全部通过；无数据泄漏；评估指标与任务类型匹配。

### 阶段 2：性能与最佳实践优化

**目标**：运行效率显著提升，模型性能可衡量，结果完全可复现。

**步骤**：

1. **性能定位** — 再次调用 `diagnose`，定位瓶颈（耗时 top-3 函数、内存占用 top-3 DataFrame）。

2. **架构优化** — 调用 `improve-codebase-architecture`，获取并执行优化方案：
   - 函数拆分（单函数 > 50 行 → 拆分）
   - 减少耦合（全局变量 → 参数传递）
   - 配置集中（硬编码参数 → 配置字典）

3. **手动实施**（记录每项的前后耗时对比）：
   - **向量化**：将 `iterrows()` / `for` 循环替换为向量化运算或 `.apply()`
   - **类型优化**：object → category（低基数列），float64 → float32，int64 → int32
   - **特征工程**：删除高缺失率（> 50%）和零方差特征；增加 1-2 个衍生特征（如移动平均、比率、交互项）
   - **内存测量**：优化前后分别用 `df.info(memory_usage='deep')` 记录内存

4. **模型优化**：
   - 引入交叉验证：分类用 `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
   - 超参数搜索：`RandomizedSearchCV(n_iter=20, cv=skf, random_state=42, n_jobs=-1)`
   - **完全可复现**：文件顶部固定所有随机种子：
     ```python
     import random, numpy as np, torch
     SEED = 42
     random.seed(SEED)
     np.random.seed(SEED)
     torch.manual_seed(SEED)  # 如使用 torch
     ```
   - 对比优化前后指标，写入报告

**验收标准**：训练时间下降 > 20%；内存下降 > 15%；模型至少有一个指标提升；结果可完全复现。

### 阶段 3：文档与注释增强

**目标**：每个函数有清晰文档，README 可直接用于面试。

**步骤**：

1. **文档审查** — 调用 `grill-with-docs`，获取文档和注释的缺失点清单。

2. **补全 docstring** — 为每个函数添加 Google 风格 docstring：
   ```python
   def func_name(param1: type, param2: type) -> return_type:
       """一句话描述功能。

       Args:
           param1: 参数说明。
           param2: 参数说明。

       Returns:
           返回值说明。

       Example:
           >>> func_name(1, 2)
           3
       """
   ```

3. **关键注释** — 在以下位置添加"为什么这样做"注释：
   - 非直观的数据处理步骤（如 log1p 变换的原因）
   - 特定的参数选择理由（如 n_estimators=200 的依据）
   - 处理边界情况的逻辑（如异常值截断阈值的选择）

4. **业务洞察** — 调用 `consulting-analysis`（如不可用则手动分析）：
   - 最重要的 3 个特征是什么？业务上如何解读？
   - 模型预测结果对业务决策有何指导意义？
   - 数据中有哪些反直觉的发现？

5. **更新 README.md**：
   - 用 STAR 原则重写简历描述（Situation → Task → Action → Result，数字真实可验证）
   - 补充"学习要点"section，列出 3-5 个关键技术点
   - 补充运行截图占位符描述（`screenshots/` 目录）
   - 确保所有命令可一键运行（`pip install -r requirements.txt && python main.py`）

**验收标准**：每个函数有 docstring；README 含 STAR 描述 + 学习要点 + 截图描述。

### 阶段 4：可视化美化与报告生成

**目标**：图表专业美观，交互式，最终报告可直接展示。

**步骤**：

1. **图表美化** — 调用 `chart-visualization` skill；若不可用，手动执行：
   - 设置 seaborn 主题：`sns.set_theme(style="whitegrid", palette="muted", font="sans-serif")`
   - 统一配色：使用 seaborn `color_palette("husl", n_colors)` 或项目专属调色板
   - 所有 matplotlib 图表升级为 plotly 交互式版本，存入 `output/`：
     ```python
     import plotly.express as px
     fig = px.bar(df, x='...', y='...', title='...', color_discrete_sequence=palette)
     fig.write_html('output/chart_name.html')
     ```
   - 图标元素完整：标题、轴标签、图例、数据来源标注

2. **品牌规范** — 调用 `brand-guidelines` skill；若不可用，遵循：
   - 字体：标题用 sans-serif bold，正文用 sans-serif，代码用 monospace
   - 配色：选择 1 个主色 + 2 个辅色 + 1 个强调色
   - 所有图表遵循统一配色

3. **展示报告** — 调用 `frontend-design` skill 设计布局；若不可用，使用下方模板。

4. **生成 `output/project_showcase.html`**：单文件 HTML，包含以下 section：
   - **Hero**：项目名称、四维标签（如 [分类] [结构化数据] [sklearn] [医疗]）、一句话介绍
   - **业务问题**：业务背景、数据规模（行数×列数）、目标变量定义
   - **关键发现**：嵌入交互式 plotly 图表 + 每条发现的文字解读
   - **模型性能**：优化前 vs 优化后对比表（指标名、优化前、优化后、提升幅度）
   - **业务建议**：3 条 actionable 的业务建议
   - **技术栈**：使用的工具和库标签

**验收标准**：所有图表为交互式 HTML；配色统一；`project_showcase.html` 可独立在浏览器打开。

### 阶段 5：收尾与打包

**目标**：可复现、可审查、可交付。

**步骤**：

1. **锁定依赖**：
   ```bash
   pip freeze > requirements_locked.txt
   ```
   同时保留原 `requirements.txt` 作为最简依赖清单。

2. **引用检查**：确认 README 和 `project_showcase.html` 中所有引用的输出文件（.png/.html）都存在。

3. **生成优化报告** — 创建 `OPTIMIZATION_REPORT.md`，参考 `references/report-template.md`，记载：
   - 各阶段发现的问题及修复状态
   - 性能对比数据（时间、内存的前后对比表）
   - 新增/修改的文件清单
   - 每个 skill 调用的摘要与效果
   - 未修复项（如有）

4. **备份原始文件**：确认 `backup_original/` 包含所有被修改的原始文件。

5. **更新优化日志**：在 `project_optimization_log.json` 中追加当前项目记录：
   ```json
   {
     "project_path": "d:/trae-workspace/data-science-projects/Day20240522/",
     "optimized_at": "2024-05-22T10:00:00",
     "status": "completed",
     "summary": "发现 8 个问题已全部修复，训练时间减少 42%，内存降低 28%"
   }
   ```

## 最终通知

全部 5 阶段完成后，按此格式输出总结（填入实际数据）：

```
✅ 项目优化完成：{项目名称}
🔍 代码审计：diagnose + grill-me 发现 {N} 个问题，已全部修复
⚡ 性能提升：训练时间减少 {X}%，内存占用降低 {Y}%
🎨 可视化：图表升级为 plotly 交互式，展示报告 → output/project_showcase.html
📚 文档增强：补全 {N} 个函数 docstring，README 增加业务洞察 + STAR 描述
📁 优化报告：OPTIMIZATION_REPORT.md
💡 下一步：可推送到 GitHub 并部署展示页面
```

## 错误处理规则

- **子技能不可用**：不中断流程，记录到报告中，使用标准工具手动完成该子任务
- **子技能调用失败**：同上，记录原因后手动继续
- **覆盖性操作**：所有修改前已备份到 `backup_original/`，可随时回滚
- **项目路径无效**：立即停止，不执行任何操作

## 参考文件

- `references/report-template.md` — OPTIMIZATION_REPORT.md 完整模板
- `references/checklist.md` — 每阶段详细检查清单
- `references/fallback-guide.md` — 子技能不可用时的替代方案
