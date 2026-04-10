# 2026-03-10 Nested CV 结果摘要

## 1. 严格 nested CV 基线结果

| 实验 | mean AUC | std AUC | mean train AUC | 说明 |
|---|---:|---:|---:|---|
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 精简临床基线 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7894 | 脂质组弹性网 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 | 扩展临床弹性网 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 | 精简临床 + 脂质融合 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 | 扩展临床 + 脂质融合 |

## 2. 核心判断

- 当前最优严格 nested CV 表现为 `fusion_elastic_net`，但 mean AUC 仅约 **0.5364**
- `fusion_full_elastic_net` 的训练集 AUC 最高，但泛化 AUC 未提升，提示**明显过拟合**
- 在当前标签定义、样本量（n=281）和现有变量条件下，模型信号距离 **0.8** 仍有明显差距

## 3. 特征数压缩诊断

额外做了 top-k / 相关性阈值诊断扫参：

| 配置 | 实验 | mean AUC | mean train AUC | mean gap | 平均特征数 |
|---|---|---:|---:|---:|---:|
| baseline_30_30_corr095 | fusion_elastic_net | 0.5364 | 0.8055 | 0.2691 | 34.4 |
| compact_15_10_corr090 | fusion_elastic_net | 0.5376 | 0.7621 | 0.2245 | 19.2 |
| baseline_30_30_corr095 | lipid_elastic_net | 0.5338 | 0.7895 | 0.2556 | 29.4 |
| ultra_sparse_5_5_corr080 | lipid_elastic_net | 0.5396 | 0.6949 | 0.1554 | 4.6 |

## 4. 诊断结论

- **缩小特征数可以降低过拟合**，但 AUC 提升幅度很有限
- 当前更像是“数据与标签信号不足”，而不是“模型还不够复杂”
- 继续盲目堆模型（RF / XGBoost / 更深搜索）大概率只会进一步抬高训练集 AUC，而不是稳定提高验证 AUC

## 5. 建议的下一步

1. **标签审计**
   - 核对 `response / noresponse` 的定义是否稳定
   - 检查是否存在时间窗、终点口径或人工整理误差

2. **队列审计**
   - 检查极端值、重复样本、批次效应、缺失模式
   - 先做变量级 QC，再决定是否继续建模

3. **问题重构**
   - 尝试把任务从二分类改为更稳定的临床终点
   - 或考虑分层建模（例如按性别 / BMI / 临床亚型）

4. **更小更稳的候选模型**
   - 以 5–15 个特征的小模型为主
   - 优先保留跨 fold 稳定出现的变量，而不是追求一次性高分

## 6. 当前已导出的文件

- `performance_summary.csv`
- `feature_frequency.csv`
- `roc_curve_points.csv`
- `run_stage_experiments_result.json`
- `diagnostic_topk_sweep.csv`
