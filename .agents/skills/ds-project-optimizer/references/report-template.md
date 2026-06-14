# OPTIMIZATION_REPORT.md 模板

使用此模板生成最终优化报告。

---

# 项目优化报告

## 基本信息

| 项目 | 值 |
|------|-----|
| 项目名称 | {project_name} |
| 原始路径 | {original_path} |
| 优化日期 | {date} |
| 优化耗时 | {duration} |

## 阶段 1：代码质量审查

### 发现的问题

| # | 问题类型 | 描述 | 严重程度 | 状态 |
|---|---------|------|---------|------|
| 1 | 数据泄漏 | {描述} | 高/中/低 | ✅ 已修复 |
| 2 | 代码风格 | {描述} | 中 | ✅ 已修复 |

### 使用的工具
- diagnose skill：{调用结果摘要}
- grill-me skill：{调用结果摘要}

### 测试结果
- 测试用例数：{N}
- 通过率：{X}%
- 新增测试：{描述}

## 阶段 2：性能与最佳实践优化

### 性能对比

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 数据加载时间 | {X}s | {Y}s | -{Z}% |
| 特征工程时间 | {X}s | {Y}s | -{Z}% |
| 模型训练时间 | {X}s | {Y}s | -{Z}% |
| 总运行时间 | {X}s | {Y}s | -{Z}% |
| 内存占用（峰值） | {X}MB | {Y}MB | -{Z}% |

### 模型性能对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| {metric_1} | {X} | {Y} | +{Z}% |
| {metric_2} | {X} | {Y} | +{Z}% |
| CV Mean ± Std | {X}±{S} | {Y}±{S} | — |

### 实施的优化
- [ ] 向量化替代循环：{具体位置}
- [ ] 数据类型优化：{具体变更}
- [ ] 衍生特征新增：{特征名称与描述}
- [ ] 高缺失率/零方差特征删除：{列表}
- [ ] 交叉验证引入：{CV 策略}
- [ ] 超参数搜索：{搜索空间与最佳参数}
- [ ] 随机种子固定：{SEED=42}

### 使用的工具
- improve-codebase-architecture skill：{调用结果摘要}

## 阶段 3：文档与注释增强

### docstring 补全清单

| 文件 | 函数 | 状态 |
|------|------|------|
| main.py | func_a | ✅ |
| main.py | func_b | ✅ |

### README 变更
- [x] STAR 原则简历描述
- [x] 学习要点 section
- [x] 截图占位符
- [x] 一键运行验证

### 使用的工具
- grill-with-docs skill：{调用结果摘要}
- consulting-analysis skill：{调用结果摘要}

## 阶段 4：可视化美化与报告生成

### 图表清单

| 文件名 | 类型 | 原始格式 | 输出格式 |
|--------|------|---------|---------|
| chart_1 | 分布图 | PNG | HTML (plotly) |
| chart_2 | 混淆矩阵 | PNG | HTML (plotly) |

### 品牌规范
- 主色：{hex}
- 辅色：{hex}, {hex}
- 字体：{font_stack}

### 使用的工具
- chart-visualization skill：{调用结果摘要}
- frontend-design skill：{调用结果摘要}
- brand-guidelines skill：{调用结果摘要}

## 阶段 5：收尾与打包

### 新增/修改文件清单

```
{project_path}/
├── backup_original/          # 原始文件备份
├── test_main.py              # [新增] 单元测试
├── output/
│   ├── chart_*.html          # [新增] 交互式图表
│   └── project_showcase.html # [新增] 展示报告
├── OPTIMIZATION_REPORT.md    # [新增] 本报告
└── requirements_locked.txt   # [新增] 锁定依赖版本
```

### 依赖版本
```
# requirements_locked.txt 已生成
# 包含 {N} 个精确版本依赖
```

## Skill 调用摘要

| Skill | 阶段 | 状态 | 效果摘要 |
|-------|------|------|---------|
| diagnose | 1, 2 | ✅ | {摘要} |
| grill-me | 1 | ✅ | {摘要} |
| grill-with-docs | 3 | ✅ | {摘要} |
| improve-codebase-architecture | 2 | ✅ | {摘要} |
| tdd | 1 | ✅ | {摘要} |
| chart-visualization | 4 | ⚠️ 不可用 | 已手动完成 |
| frontend-design | 4 | ⚠️ 不可用 | 使用默认模板 |
| brand-guidelines | 4 | ⚠️ 不可用 | 使用默认配色 |
| consulting-analysis | 3 | ⚠️ 不可用 | 已手动分析 |

## 未修复项

（如无则写"无"）
