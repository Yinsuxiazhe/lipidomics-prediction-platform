# analysis data

本目录用于说明本次正式报告包直接对应的数据来源与受限范围。

## 已随包提供的关键衍生表格

本包根目录已提供以下关键衍生表格：

- `overlap_feature_mapping.csv`：论文 36 biomarker 与本地字段的映射表。
- `reduced_external_proxy_model_feature_set.csv`：`transport_core_8` 与 `transport_extended_12` 特征草案。
- `strict_nested_cv_performance_summary.csv`：当前项目正式主结果汇总表。

## 原始或更大体量输入数据说明

本次报告包未重复拷贝完整 cohort-level 输入表，而采用清单说明方式保留来源边界。当前直接相关的上游输入包括：

- `281_merge_lipids_enroll.csv`：baseline species-level lipidomics。
- `281_new_grouped.csv`：当前 responder / non-responder 分组文件。
- `287_enroll_data_clean.csv`：baseline 临床化学与协变量表。
- `287_outroll_data_clean.csv`：out-phase 临床化学与协变量表。

## 说明

- 本目录用于说明当前报告页、表格与判断所依赖的数据来源。
- 若后续需要正式共享完整原始输入，应另行确认数据权限、共享范围与接收对象。
