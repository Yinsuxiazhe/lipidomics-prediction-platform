# Strict Nested CV Small-Model Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不回退到旧泄漏流程、也不扩散修改范围的前提下，基于现有 strict nested CV 管线完成一轮“小模型 + 稳定特征 + 标签/队列审计”的窄范围跟进，并产出可直接用于论文/汇报的审计材料。

**Architecture:** 继续沿用现有 Python strict nested CV 管线与已生成的 Figure 6-4 诚实口径主结果，不修改主实验定义。只调用现有 `run_experiments()`、`write_experiment_tables()`、`write_roc_outputs()` 对预先定义的小模型配置做补充运行，并在 `outputs/20260310_nested_cv` 下增量写入新的审计与比较产物。标签/队列审计只基于本地现有 CSV 与会议记录做证据化整理；若本地没有随访窗口或结局原始定义字段，则明确标记为“现阶段无法完成的外部依赖”。

**Tech Stack:** Python 3.13, pandas, scikit-learn, PyYAML, 现有项目模块（`src.models.run_nested_cv`, `src.reports.make_tables`, `src.reports.make_figures`）

### Task 1: 锁定窄范围比较对象与数据边界

**Files:**
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/docs/plans/2026-03-10-figure6-4-honest-nested-cv-handoff.md`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_stability_summary.csv`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/diagnostic_topk_sweep.csv`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/281_new_grouped.csv`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/287_enroll_data_predict.csv`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/287_enroll_data_clean.csv`

**Step 1: 复核 strict nested CV 主结果与已有扫参结果**

确认以下三类对象作为唯一比较集：
1. `clinical_slim_logistic` 主基线（沿用当前主结果，不重写定义）
2. `lipid_elastic_net` 的 `ultra_sparse_5_5_corr080` 小模型
3. `fusion_elastic_net` 的 `compact_15_10_corr090` 小模型

**Step 2: 明确不做的事情**

- 不回退到全样本先筛特征再验证
- 不新增 RF / XGBoost / 深层搜索
- 不改 Figure 6-4 主图口径
- 不碰 handoff 未列出的无关目录

**Step 3: 记录边界结论**

若本地没有 response/noresponse 的原始结局定义、随访时间窗或人工判定字段，则在最终审计报告中明确标注“标签审计目前只能做到结构级/来源级检查，不能完成结局口径真值核验”。

### Task 2: 用现有 strict nested CV 管线重导出两个预定义小模型结果

**Files:**
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/run_pipeline.py`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/models/run_nested_cv.py`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/reports/make_tables.py`
- Read: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/src/reports/make_figures.py`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/*`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/*`

**Step 1: 用现有 API 跑 ultra-sparse lipid 小模型**

调用 `run_experiments()`，参数：
- `requested_experiments=['lipid_elastic_net']`
- `lipid_top_k=5`
- `clinical_top_k=5`
- `correlation_threshold=0.80`
- 其余 nested CV 参数保持主配置一致

将结果写出到 `predefined_small_models/ultra_sparse_lipid/`，至少包含：
- `performance_summary.csv`
- `feature_frequency.csv`
- `fold_metrics.csv`
- `feature_stability_summary.csv`
- `roc_curve_points.csv`
- `run_result.json`

**Step 2: 用现有 API 跑 compact fusion 小模型**

调用 `run_experiments()`，参数：
- `requested_experiments=['fusion_elastic_net']`
- `lipid_top_k=15`
- `clinical_top_k=10`
- `correlation_threshold=0.90`
- 其余 nested CV 参数保持主配置一致

将结果写出到 `predefined_small_models/compact_fusion/`，导出同样的 6 类文件。

**Step 3: 生成一个三模型对照汇总表**

在 `outputs/20260310_nested_cv/` 下生成 `20260310_predefined_small_model_comparison.csv`，至少包含列：
- `model_label`
- `source`
- `mean_auc`
- `std_auc`
- `mean_train_auc`
- `mean_gap`
- `mean_selected_feature_count`

其中三行分别对应：
- 现有主结果 `clinical_slim_logistic`
- `ultra_sparse_lipid`
- `compact_fusion`

### Task 3: 形成“发表口径友好”的标签/队列/稳定特征审计报告

**Files:**
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.md`
- Create: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.csv`

**Step 1: 审计结构级标签与队列边界**

至少写清：
- 287 → 281 的队列收敛路径
- overlap ID 数量
- response/noresponse 分布
- 是否存在重复 ID
- 是否存在本地可直接核验的结局原始字段；若没有，明确列为“待外部补证”

**Step 2: 审计稳定特征与缺失/可解释性**

围绕以下对象做整理：
- 主基线 5 个临床变量
- ultra-sparse lipid 稳定脂质
- compact fusion 的稳定变量

至少汇总：
- 频次 / selection_rate
- 在 281 队列中的缺失率
- exploratory 单变量方向性（如 response 组 vs noresponse 组均值或中位数）
- 任何明显的批次/前缀不均衡线索（若只能做到弱证据，也要明确写出）

**Step 3: 用论文/汇报能直接复用的语气收束**

报告结论只允许落在以下范围：
- 小模型在 strict nested CV 下更稳，但提升幅度有限
- 现阶段更支持“继续压缩 + 继续审计”，不支持“继续堆复杂模型”
- 旧版高分结果若提及，只能作为 exploratory / development-stage internal validation

### Task 4: 验证与交付

**Files:**
- Verify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/ultra_sparse_lipid/`
- Verify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/predefined_small_models/compact_fusion/`
- Verify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_predefined_small_model_comparison.csv`
- Verify: `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_small_model_label_audit.md`

**Step 1: 文件级验证**

使用 `ls -l` 确认所有新增文件已生成。

**Step 2: 结果级验证**

至少核对：
- ultra-sparse lipid 的 mean AUC 是否约 0.54，mean gap 是否明显低于 baseline lipid 主模型
- compact fusion 的 mean AUC 是否约 0.538 左右，且 mean gap 低于 baseline fusion 主模型
- 三模型比较表中的 clinical baseline 行与主结果文件一致

**Step 3: 回复时明确说明修改范围**

最终汇报必须列出：
- 新增了哪些输出文件
- 是否修改了任何源码（若没有，要明确写“本轮未改源码，只新增审计与补充结果产物”）
- 对用户下一步最值得做的 1–2 件事
