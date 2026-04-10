# 三个 biobanks external-proxy 可行性正式报告包

> 本页是正式报告包总入口，用于概览当前结论、阅读顺序、材料清单与结论边界。  
> 生成日期：2026-03-17

## 项目角色

- 需求方：`Shuxian Zhang`
- 分析提供方：`Chenyu Fan`

## 本包一句话结论

当前材料支持的结论是：**UK Biobank、Estonian Biobank、THL Biobank 可以作为第二阶段的 external-proxy / transportability 候选资源；但现阶段仍不能直接写成当前儿童运动干预 responder 模型的严格 external validation。**

## 建议阅读顺序

1. 先打开 `01_biobank_external_proxy_formal_report.html`：这是本次结果的主报告页。
2. 再看 `02_supplementary_note.html`：这是补充说明页，包含结果比对、数据申请现实性判断与下一步建议。
3. 如需查看配套表格，继续查看根目录下 CSV 文件。
4. 如需复核材料来源与可复现性，查看 `analysis_code/` 与 `analysis_data/`。

## 包内主要内容

| 文件 | 作用 |
| --- | --- |
| `index.html` | 本包总入口 |
| `01_biobank_external_proxy_formal_report.html` | 主报告页 |
| `02_supplementary_note.html` | 补充说明页 |
| `overlap_feature_mapping.csv` | overlap-feature 对照表 |
| `reduced_external_proxy_model_feature_set.csv` | reduced external-proxy model 草案 |
| `strict_nested_cv_performance_summary.csv` | 当前正式主结果汇总 |
| `analysis_code/` | 直接相关的主要分析代码 |
| `analysis_data/` | 数据说明与输入来源清单 |

## 当前必须坚持的结论边界

- 正式主结果仍是：**strict nested CV outer-test AUC 约 0.50–0.54**。
- 用户印象中的 **AUC≈0.8** 对应的是训练侧 `mean_train_auc`，不能写成 outer-test AUC。
- repeated hold-out、leave-one-school-out、baseline -> out-phase 队列内时相验证都属于补充分析，**不能升级表述为 strict external validation**。
- 本包支持的是：**external-proxy / transportability feasibility** 的可行性说明。
- 本包不支持的是：**当前 responder 分类器已完成严格外部验证**。

## 下一步建议

1. 先在本地运行 `transport_core_8` / `transport_extended_12` 的 strict nested CV 与 follow-up 比较。
2. 如果需要推进外部资源，优先评估 UK Biobank 的 feasibility。
3. 对外措辞继续使用 `external-proxy validation`、`transportability assessment` 或 `targeted replication feasibility`。
