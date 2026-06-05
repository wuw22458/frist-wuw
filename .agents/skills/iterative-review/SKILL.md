---
name: iterative-review
description: 自动迭代优化引擎——用 agent 审查循环替代人工反复修改。支持 5 种迭代方向（strict/balanced/wild/adaptive/custom），自动跑 do→review→improve 循环直到达标。适用于代码优化、架构审查、UI 迭代、文档润色等需要反复打磨的场景。
globs: []
alwaysApply: false
---

# Iterative Review — 自动迭代优化引擎

## 什么时候用这个技能

- 用户说"帮我优化"、"帮我审查"、"反复改改"、"迭代一下"
- 用户给了一个代码/文件/方案，希望自动打磨到满意
- 用户想设定一个方向（规矩/天马行空/自定义），让 agent 自动循环改进
- 用户不想每轮都手动说"再改改"

## 核心概念

### 迭代方向轴（Mode）

```
strict ←——→ balanced ←——→ wild
严格规范       均衡         大胆突破
逐项修复     兼顾两者      整体重构
```

五种模式：

| 模式 | 审查风格 | 一轮改几个 | 允许推翻重来 | 典型场景 |
|------|----------|-----------|-------------|---------|
| `strict` | 质检员：按清单逐项检查 | 1 个 | 否 | 生产代码、安全审计 |
| `balanced` | 技术负责人：关注整体+细节 | ≤3 个 | 否 | 日常开发、功能迭代 |
| `wild` | 创意总监：看大方向，鼓励突破 | 不限 | 是 | 原型探索、UI 设计、架构重构 |
| `adaptive` | 智能判断：小问题 strict，大问题 wild | 自动 | 自动 | 通用场景（推荐默认） |
| `custom` | 用户定义：参照物+关键词 | 按方向调整 | 按方向调整 | "像 Linear 那样改" |

### Custom 方向描述方式

用户用"参照物 + 关键词"描述，不需要长篇大论。示例：
- "往 Linear 的风格改" → 极简、克制、信息密度高
- "像 Stripe 那样优雅" → 动画流畅、间距舒适、层次分明
- "要酷，暗黑科技感" → 深色主题、霓虹点缀、未来感
- "功能优先，UI 能用就行" → 只审功能正确性，UI 不挑
- "跟 v0.dev 默认风格差不多" → 参照那个工具的视觉语言

系统将用户的描述转化为审查 agent 的 system prompt 中的"审美锚点"。

## 工作流程

```
用户给任务 + 设定方向
        │
        ▼
   ┌─────────────┐
   │ Worker Agent │ ← 执行初始版本
   └──────┬──────┘
          │
          ▼
   ┌──────────────┐
   │ Review Agent  │ ← 独立审查（新建会话，不继承上下文）
   └──────┬──────┘
          │
     ┌────┴────┐
     │ 通过？   │
     └────┬────┘
      yes │    no
          │     │
          ▼     ▼
       输出   ┌──────────────┐
       最终   │ 置信度判断    │
       成果   └──────┬──────┘
                 ┌───┴───┐
                 │ 高？   │
                 └───┬───┘
              yes   │   no（分歧）
                  ▼       ▼
              Worker    暂停，问用户
              自动改     让用户拍板
                  │
                  ▼
              Review Agent（下一轮）
                  │
              ...循环直到通过或达到 max_rounds
```

## 详细步骤

### Step 1: 初始化

1. 解析用户的任务描述和迭代方向
2. 如果是 `custom` 模式，提取参照物和关键词，转化为审查标准
3. 如果是 `adaptive` 模式，准备两套审查标准（strict + wild）
4. 创建工作目录 `.hermes/iterative/<task-slug>/`
5. 如果任务涉及文件，复制到工作目录作为 checkpoint 基线
6. 用 `todo` 创建任务列表，记录总轮次上限

### Step 2: 执行（Worker）

Worker agent 负责实际的代码/文件修改。

- 第一轮：从零创建初始版本（或基于用户提供的文件优化）
- 后续轮次：根据 Review Agent 的反馈修改
- 每轮开始前：用 git commit 或文件复制做 checkpoint（支持回滚）
- 每轮结束后：输出变更摘要（改了什么、为什么改）

### Step 3: 审查（Review）

Review Agent 是一个**独立的子 agent**（delegate_task），不继承 Worker 的上下文。

审查 agent 的 prompt 模板：

```
你是一个[模式对应的审查角色]。

审查标准：
[根据模式生成的具体标准]

{如果是 custom 模式，追加：}
审美锚点：{用户的参照物描述}
按这个方向评估每一项改动。

审查对象：{具体文件/代码/方案}

请按以下格式输出：
1. PASS / FAIL / PARTIAL
2. 问题清单（每个问题标注严重性：critical / major / minor）
3. 具体修改建议（可直接执行的指令）
4. 置信度：HIGH / MEDIUM / LOW
   - HIGH = 这些问题确定是问题，建议确定可行
   - MEDIUM = 大概率是问题但可能有我不了解的上下文
   - LOW = 不确定，可能是设计意图，需要用户判断
```

各模式的审查标准：

**strict:**
- 代码规范（命名、格式、注释）
- 边界条件（空值、异常、并发）
- 性能（时间/空间复杂度、内存泄漏）
- 安全（注入、越权、敏感信息泄露）
- 测试覆盖
- 每次只标记 1 个最高优先级问题

**balanced:**
- 功能正确性
- 代码可读性和可维护性
- 基本的性能和安全
- 架构合理性
- 每次标记不超过 3 个问题

**wild:**
- 整体方向是否足够大胆
- 是否有更好的架构/方案被忽略了
- 用户体验是否有质的提升空间
- 是否可以跳出当前框架思考
- 鼓励推翻重来，只要新方案明显更好

**adaptive:**
- 先评估当前状态：小问题多还是大问题多
- 小问题为主 → strict 模式
- 大问题为主 → wild 模式
- 混合 → 优先处理大问题（wild），下一轮处理小问题（strict）

**custom:**
- 以用户的参照物为锚点评估
- 检查是否朝参照物的方向前进了
- 偏离方向时给出修正建议

### Step 4: 决策分支

根据 Review Agent 的结果和置信度：

**置信度 HIGH + PASS:** → 直接输出最终成果，结束迭代

**置信度 HIGH + FAIL:**
- 连续 2 轮改动都很小（minor 问题，改动 < 10 行）→ 告诉用户"基本打磨完了，剩余的都是边角问题，要继续吗？"
- 否则 → Worker 自动修改，进入下一轮

**置信度 MEDIUM:**
- Worker 先按建议改，但标记为"待确认"
- 下一轮 Review Agent 重点检查这些改动是否合理

**置信度 LOW:**
- 暂停迭代
- 向用户展示分歧点："Review 发现了这些问题，但不确定是不是真的问题，你怎么看？"
- 用户拍板后继续

**达到 max_rounds:**
- 强制结束，输出当前最佳版本
- 告诉用户：已经迭代了 N 轮，剩余问题是什么，建议手动处理还是继续

### Step 5: 输出成果

迭代完成后输出：

1. **最终版本** — 改好的文件/代码
2. **变更报告** — 每一轮改了什么（结构化列表）
3. **迭代摘要** — 总轮次、每轮的审查结果和改动类型
4. **剩余问题** — 如果有未解决的 minor 问题，列出来

## 成本与安全

### Token 预算
- 每轮消耗 ≈ 2x 单次任务执行（Worker + Review）
- 默认 max_rounds = 5（wild 模式 = 10）
- 第一轮开始前告诉用户预计总消耗
- 如果连续 2 轮审查结果几乎一样 → 提前结束，不浪费 token

### Checkpoint 回滚
- 每轮开始前自动做 checkpoint（git commit 或文件复制）
- 用户说"回到第 N 轮"时，用 `git checkout` 或文件还原
- 工作目录：`.hermes/iterative/<task-slug>/round-N/`

### 用户中断
- 用户随时可以说"停"来结束迭代
- 输出当前最佳版本（不一定是最新的，而是审查评分最高的那轮）

## 使用示例

### 示例 1: 代码优化（adaptive 模式）
```
用户: 帮我优化这个函数，用 adaptive 模式
文件: d:/1/project/utils.py

→ Worker 分析代码，第 1 轮重命名变量+添加类型注解
→ Review: PASS (minor: 缺少 docstring)
→ Worker 第 2 轮加 docstring
→ Review: PASS (无问题)
→ 输出最终版本 + 变更报告
```

### 示例 2: UI 迭代（custom 模式）
```
用户: 帮我改这个页面，往 Linear 的风格改
文件: d:/1/project/index.html

→ Worker 第 1 轮简化布局、去掉多余装饰
→ Review: FAIL (按钮层级不够清晰)
→ Worker 第 2 轮调整按钮样式
→ Review: PASS
→ 输出最终版本
```

### 示例 3: 架构重构（wild 模式）
```
用户: 这个模块架构太乱了，wild 模式帮我重新设计
文件: d:/1/project/payment/

→ Worker 第 1 轮提出 3 种架构方案
→ Review: 推翻，建议第 4 种方案
→ Worker 第 2 轮按第 4 种方案实现
→ Review: PARTIAL (接口设计可以更优雅)
→ Worker 第 3 轮优化接口
→ Review: PASS
→ 输出最终版本 + 架构决策记录
```

## 实际执行指南

当用户触发这个技能时，按以下步骤操作：

### 触发词
用户说"帮我优化"、"帮我审查"、"迭代一下"、"反复改到满意"、"用 iterative-review 模式"时触发。

### Step 0: 确认任务和模式
1. 读取用户的任务描述
2. 如果用户没指定模式，默认用 `adaptive`
3. 如果用户说"规矩点" → strict，"大胆改" → wild，"像 XX 那样" → custom
4. 确认 max_rounds（默认 5，wild 默认 10）

### Step 1: 初始化
```bash
# 创建工作目录并复制源文件
mkdir -p .hermes/iterative/<task-slug>/
cp <source-files> .hermes/iterative/<task-slug>/

# 初始化 checkpoint
python3 ~/.hermes/skills/development/iterative-review/scripts/checkpoint.py init .hermes/iterative/<task-slug>/
python3 ~/.hermes/skills/development/iterative-review/scripts/checkpoint.py save .hermes/iterative/<task-slug>/ 0
```

### Step 2: 派发 Review Agent
用 `delegate_task` 派一个审查 agent，prompt 模板：

```
你是一个 {mode} 模式的代码审查 agent。

审查对象：{文件路径和内容}

审查标准：
{根据 mode 选择对应的标准，见 SKILL.md 中的"各模式审查标准"}

输出格式（严格遵守）：
1. 结果：PASS / FAIL / PARTIAL
2. 问题清单（每个标注严重性：critical / major / minor）
3. 具体修改建议（可直接执行的代码）
4. 置信度：HIGH / MEDIUM / LOW
5. 改动规模：small / medium / large
```

### Step 3: 判断决策分支
- PASS + HIGH → 输出最终成果，结束
- FAIL + HIGH → 继续 Step 4
- MEDIUM → 继续 Step 4，但标记"待确认"
- LOW → 暂停，问用户
- 连续 2 轮 minor 改动 → 问用户"差不多了，继续吗？"

### Step 4: 派发 Worker Agent
用 `delegate_task` 派一个 worker agent，把审查反馈中的修改建议传给它。

### Step 5: 保存快照
```bash
python3 ~/.hermes/skills/development/iterative-review/scripts/checkpoint.py save .hermes/iterative/<task-slug>/ <round>
```

### Step 6: 循环
回到 Step 2，直到满足结束条件。

### Step 7: 输出成果
最终输出：
1. 修改后的文件
2. 变更报告（每轮改了什么）
3. 迭代摘要（总轮次、审查结果）
4. 剩余问题（如有）

### 回滚操作
用户说"回到第 N 轮"时：
```bash
python3 ~/.hermes/skills/development/iterative-review/scripts/checkpoint.py restore .hermes/iterative/<task-slug>/ <N>
```

## 实现状态

- [ ] 主入口：解析任务 + 模式选择
- [ ] Worker agent prompt 模板
- [ ] Review agent prompt 模板（5 种模式）
- [ ] 置信度判断 + 决策分支
- [ ] Checkpoint 系统
- [ ] 成本控制 + 提前结束逻辑
- [ ] 成果输出模板
