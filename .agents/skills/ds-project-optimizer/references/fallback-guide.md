# 子技能不可用时的替代方案

当某个子 skill 在当前环境中不可用时，按以下方案手动完成。

## diagnose → 手动诊断

按以下检查表手动审查代码：

### 数据泄漏（最常见）
```python
# ❌ 错误：在 split 前标准化
from sklearn.preprocessing import StandardScaler
X_scaled = StandardScaler().fit_transform(X)  # 全量数据！
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)

# ✅ 正确：先 split 再 fit_transform
X_train, X_test, y_train, y_test = train_test_split(X, y)
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # 仅 transform，不 fit
```

### 缺失值
```python
# ❌ 简单粗暴
df.dropna(inplace=True)

# ✅ 分析后处理
missing_pct = df.isnull().sum() / len(df)
high_missing = missing_pct[missing_pct > 0.5].index  # >50% 删除
df.drop(columns=high_missing, inplace=True)
# 其余用中位数/众数填补
```

### 评估指标
```python
from sklearn.metrics import classification_report, roc_auc_score, f1_score

# 检查类别分布
print(y.value_counts(normalize=True))

# 不平衡 → 不用 accuracy
if y.value_counts(normalize=True).min() < 0.2:
    print(f"F1: {f1_score(y_test, y_pred, average='macro')}")
    print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba, multi_class='ovr')}")
```

### 性能瓶颈
```python
import cProfile, pstats

# 定位耗时函数
cProfile.run('main()', 'profile_stats')
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative').print_stats(10)  # top-10 耗时函数

# 定位内存大户
for col in df.columns:
    print(f"{col}: {df[col].memory_usage(deep=True) / 1024**2:.2f} MB")
```

## grill-me → 手动代码审查

按以下 checklist 审查：
1. 变量命名是否清晰（避免 x, tmp, df2）
2. 函数是否单一职责（一个函数只做一件事）
3. 魔法数字是否提取为常量
4. 重复代码是否可提取为函数
5. 错误处理是否合理（不要裸 except）
6. 文件路径是否硬编码（应使用 pathlib 或相对路径）

## grill-with-docs → 手动文档审查

按以下标准检查每个函数：
1. 有 docstring 吗？
2. docstring 写了"为什么"而不仅是"做了什么"吗？
3. 参数类型标注了吗？
4. 返回值类型标注了吗？
5. 有使用示例吗（复杂函数）？

## improve-codebase-architecture → 手动架构优化

标准优化模式：
1. **配置集中**：硬编码参数 → config dict
2. **管道抽象**：手写步骤 → sklearn Pipeline
3. **函数拆分**：> 50 行函数 → 多个小函数
4. **IO 分离**：数据加载与处理逻辑分离

```python
# ✅ 配置集中
CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "cv_folds": 5,
    "model_params": {"n_estimators": 200, "max_depth": 10}
}
```

## tdd → 手动创建测试

```python
import pytest
import numpy as np

def test_model_output_shape():
    """模型输出形状应与输入样本数一致"""
    from main import predict
    X_sample = np.random.randn(100, 10)
    y_pred = predict(X_sample)
    assert len(y_pred) == 100

def test_prediction_range():
    """分类任务：预测概率应在 [0, 1] 之间"""
    from main import predict_proba
    X_sample = np.random.randn(100, 10)
    y_proba = predict_proba(X_sample)
    assert np.all(y_proba >= 0) and np.all(y_proba <= 1)

def test_pipeline_reproducibility():
    """固定种子后两次运行应产出相同结果"""
    # run twice and compare
    pass
```

## chart-visualization → 手动图表美化

```python
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# 统一风格
sns.set_theme(style="whitegrid", palette="muted", font="sans-serif")
PALETTE = sns.color_palette("husl", 8).as_hex()
PRIMARY = PALETTE[0]
SECONDARY = PALETTE[2]
ACCENT = PALETTE[4]

# matplotlib → plotly 转换模板
def make_interactive_bar(df, x, y, title, filename):
    fig = px.bar(
        df, x=x, y=y, title=title,
        color_discrete_sequence=[PRIMARY],
        template="plotly_white"
    )
    fig.update_layout(
        font=dict(family="Segoe UI, Arial, sans-serif"),
        title_font_size=20,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    fig.write_html(f"output/{filename}.html")
```

## brand-guidelines → 默认品牌规范

```
主色：#2563EB (蓝色)
辅色：#10B981 (绿色), #6366F1 (紫色)
强调色：#F59E0B (琥珀色)
背景：#FFFFFF
文字：#1F2937
字体：system-ui, -apple-system, "Segoe UI", sans-serif
代码字体："JetBrains Mono", "Fira Code", monospace
```

## consulting-analysis → 手动业务分析

引导问题：
1. 最重要的 3 个特征在业务上代表什么？它们的影响方向符合直觉吗？
2. 如果把模型预测用在一线业务，ROI 体现在哪里？（减少人工？提升转化？降低风险？）
3. 数据中有哪些反直觉的发现？这些发现对业务策略有什么影响？
4. 这个模型的局限性是什么？什么场景下不应使用？

## frontend-design → 默认展示报告模板

使用以下 HTML 骨架，替换 `{}` 占位符：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} - 数据科学项目</title>
<style>
  :root {
    --primary: #2563EB;
    --secondary: #10B981;
    --accent: #F59E0B;
    --bg: #FFFFFF;
    --text: #1F2937;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, "Segoe UI", sans-serif; color: var(--text); background: var(--bg); line-height: 1.6; }
  .hero { background: linear-gradient(135deg, var(--primary), #7C3AED); color: white; padding: 80px 40px; text-align: center; }
  .hero h1 { font-size: 2.5rem; margin-bottom: 16px; }
  .tags { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin: 16px 0; }
  .tag { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }
  .container { max-width: 960px; margin: 0 auto; padding: 40px 20px; }
  section { margin-bottom: 48px; }
  h2 { font-size: 1.5rem; margin-bottom: 16px; border-bottom: 2px solid var(--primary); padding-bottom: 8px; display: inline-block; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th, td { border: 1px solid #E5E7EB; padding: 12px; text-align: left; }
  th { background: #F3F4F6; font-weight: 600; }
  .chart-container { margin: 24px 0; }
  .insight { background: #F0FDF4; border-left: 4px solid var(--secondary); padding: 16px; margin: 16px 0; border-radius: 4px; }
  .footer { text-align: center; padding: 40px 20px; color: #9CA3AF; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="hero">
  <h1>{project_name}</h1>
  <div class="tags">{tags_html}</div>
  <p>{one_liner}</p>
</div>
<div class="container">
  <section>
    <h2>业务问题</h2>
    <p>{business_problem}</p>
    <p>数据规模：{data_scale}</p>
  </section>
  <section>
    <h2>关键发现</h2>
    {findings_html}
  </section>
  <section>
    <h2>模型性能</h2>
    {performance_table_html}
  </section>
  <section>
    <h2>业务建议</h2>
    {recommendations_html}
  </section>
  <section>
    <h2>技术栈</h2>
    {tech_stack_html}
  </section>
</div>
<div class="footer"><p>{project_name} · 优化于 {date}</p></div>
</body>
</html>
```
