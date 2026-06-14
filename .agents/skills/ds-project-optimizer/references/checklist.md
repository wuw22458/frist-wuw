# 阶段检查清单

## 前置检查

- [ ] 项目路径存在且可读
- [ ] `main.py` 或 `notebook.ipynb` 存在
- [ ] `README.md` 存在
- [ ] `data/` 目录存在且非空
- [ ] `project_optimization_log.json` 已读取，确认未重复优化
- [ ] `backup_original/` 已创建，原始文件已备份

## 阶段 1：代码质量审查

### 数据泄漏检查
- [ ] 标准化/归一化在 train_test_split **之后**执行
- [ ] 缺失值填补使用训练集统计量（非全量数据）
- [ ] 特征选择未使用测试集信息
- [ ] 时间序列数据未使用未来信息
- [ ] 过采样（SMOTE 等）仅在训练集上执行

### 评估指标检查
- [ ] 分类任务：已检查类别分布
  - 少数类 < 20% → 已添加 F1/ROC-AUC/PR-AUC
  - 多分类 → 已使用 macro/micro 平均
- [ ] 回归任务：已检查离群值，必要时使用 MAE/RMSLE

### 代码风格
- [ ] black/autopep8 已运行，无报错
- [ ] 行宽 ≤ 100
- [ ] 无行尾空格
- [ ] 文件末尾有且仅有一个换行符

### 测试
- [ ] `pytest test_main.py` 全部通过
- [ ] ≥ 3 个测试用例（含 ≥ 1 个业务逻辑测试）
- [ ] 测试覆盖核心函数

## 阶段 2：性能优化

### 诊断
- [ ] 已定位耗时 top-3 函数
- [ ] 已定位内存 top-3 DataFrame
- [ ] 已记录优化前基准（时间 + 内存）

### 代码层面
- [ ] iterrows()/for 循环已改为向量化/.apply()
- [ ] object → category（低基数 ≤ 列数*0.5 的列）
- [ ] float64 → float32，int64 → int32
- [ ] 高缺失率（>50%）列已删除
- [ ] 零方差列已删除
- [ ] 1-2 个衍生特征已添加
- [ ] 已记录优化后指标

### 模型层面
- [ ] 交叉验证已引入（StratifiedKFold, n_splits=5）
- [ ] 超参数搜索已完成（RandomizedSearchCV, n_iter=20）
- [ ] 所有随机种子已固定（SEED=42）
- [ ] numpy, random, torch（如用）均已设定
- [ ] 优化前后模型指标已对比记录

## 阶段 3：文档

### docstring
- [ ] 每个函数有 Google 风格 docstring
- [ ] docstring 含功能、参数、返回值、示例
- [ ] 类型标注完整

### 注释
- [ ] 关键数据处理步骤有"为什么"注释
- [ ] 非直观参数选择有理由说明
- [ ] 边界情况处理有解释

### README
- [ ] STAR 原则简历描述
- [ ] 学习要点 section（3-5 点）
- [ ] 截图占位符描述
- [ ] 一键运行命令可执行
- [ ] 业务洞察 section

## 阶段 4：可视化

### 图表
- [ ] seaborn 主题已设定
- [ ] 统一调色板
- [ ] 至少 3 张图表已转为 plotly 交互式 HTML
- [ ] 每张图表有标题、轴标签、图例
- [ ] 图表存入 `output/`

### 展示报告
- [ ] 品牌配色/字体已统一
- [ ] `output/project_showcase.html` 已生成
- [ ] 包含所有必需 section（Hero、业务问题、关键发现、模型性能、业务建议、技术栈）
- [ ] 可独立在浏览器打开

## 阶段 5：收尾

- [ ] `requirements_locked.txt` 已生成
- [ ] 所有输出文件被正确引用
- [ ] `OPTIMIZATION_REPORT.md` 已创建并填写完整
- [ ] `backup_original/` 包含所有被修改的原始文件
- [ ] `project_optimization_log.json` 已更新
- [ ] 最终通知已发送
