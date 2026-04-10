# responder follow-up 第一阶段汇总（已接入真实 school split）

## 1. 正式主结果（只读引用既有 strict nested CV）

以下内容继续以既有 strict nested CV 为主口径，不在本轮覆盖旧目录。

| experiment | mean_auc | std_auc | mean_train_auc | n_outer_folds |
| --- | --- | --- | --- | --- |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 5 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 | 5 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 | 5 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 | 5 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 | 5 |

## 2. 补充稳健性证据（不是外部验证）

- repeated random hold-out：作为内部自我验证。
- leave-one-school-out：本轮已接入**真实 school grouped split**，但仍属于内部 grouped validation，不得表述为 external validation。
- 旧的 leave-one-prefix-out 仅保留为早期 grouped weak proxy；由于 prefix 与 school 并非一一对应，**不能把旧的 leave-one-prefix-out 改名成学校 split**。

| experiment | model_label | validation_scheme | n_total_splits | n_completed | n_skipped | mean_auc | std_auc | mean_train_auc | mean_gap | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | leave_one_school_out | 7 | 7 | 0 | 0.5155 | 0.0784 | 0.6060 | 0.0904 | 5.0000 |
| clinical_slim_logistic | clinical_baseline_main | repeated_random_holdout | 30 | 30 | 0 | 0.5545 | 0.0851 | 0.6073 | 0.0528 | 5.0000 |
| fusion_elastic_net | compact_fusion | leave_one_school_out | 7 | 7 | 0 | 0.5246 | 0.1039 | 0.7599 | 0.2353 | 19.8571 |
| fusion_elastic_net | compact_fusion | repeated_random_holdout | 30 | 30 | 0 | 0.5718 | 0.0624 | 0.7655 | 0.1938 | 19.7333 |
| lipid_elastic_net | ultra_sparse_lipid | leave_one_school_out | 7 | 7 | 0 | 0.5310 | 0.0945 | 0.6935 | 0.1625 | 4.8571 |
| lipid_elastic_net | ultra_sparse_lipid | repeated_random_holdout | 30 | 30 | 0 | 0.5409 | 0.0617 | 0.6833 | 0.1424 | 4.9000 |

## 3. 内部时相验证（out-phase，不是外部验证）

| experiment | model_label | validation_scheme | train_phase | test_phase | n_total_splits | n_completed | n_skipped | mean_auc | std_auc | mean_train_auc | mean_gap | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4221 | 0.0988 | 0.6060 | 0.1839 | 5.0000 |
| clinical_slim_logistic | clinical_baseline_main | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.3601 | 0.0872 | 0.6073 | 0.2472 | 5.0000 |
| fusion_elastic_net | compact_fusion | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4774 | 0.1118 | 0.7599 | 0.2825 | 19.8571 |
| fusion_elastic_net | compact_fusion | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.4986 | 0.0983 | 0.7655 | 0.2670 | 19.7333 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4941 | 0.0503 | 0.6934 | 0.1993 | 4.8571 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.5034 | 0.0919 | 0.6833 | 0.1799 | 4.9000 |

## 4. 小模型 follow-up 比较

| model_label | strict_mean_auc | leave_one_school_out_mean_auc | repeated_random_holdout_mean_auc | outphase_leave_one_school_out_mean_auc | outphase_repeated_random_holdout_mean_auc | leave_one_school_out_mean_gap | outphase_leave_one_school_out_mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | 0.5297 | 0.5155 | 0.5545 | 0.4221 | 0.3601 | 0.0904 | 0.1839 |
| ultra_sparse_lipid | 0.5338 | 0.5310 | 0.5409 | 0.4941 | 0.5034 | 0.1625 | 0.1993 |
| compact_fusion | 0.5364 | 0.5246 | 0.5718 | 0.4774 | 0.4986 | 0.2353 | 0.2825 |

## 5. 学校 grouped split 补充产物

- 学校/强度映射：`id_school_intensity_mapping.csv`
- 学校留一汇总：`school_group_holdout_summary.csv`
- 文献与 protocol 说明：`03_literature_followup_note.md`
- 新建议定位页：`followup_plan_alignment.md`

## 6. 当前分组证据链

- 分组审计：`group_definition_audit.md`
- 基线平衡表：`baseline_balance_summary.csv`
- 当前分组来源仅能回溯到会议纪要级证据，不是原始真值表。

## 7. 本轮新增 follow-up 图组

- 小模型 follow-up 主图：`assets/02_followup_f1_model_performance.png`
- generalization gap 图：`assets/03_followup_f2_generalization_gap.png`
- self-validation 分布图：`assets/04_followup_f3_self_validation_distribution.png`
- 当前分组审计图：`assets/05_followup_f4_group_audit.png`
- out-phase 主图：`assets/06_followup_f5_outphase_model_performance.png`
- out-phase 分布图：`assets/07_followup_f6_outphase_distribution.png`

## 8. 待数据到位后再执行

- 缺少 endpoint_source：本地没有用于重定义 responder 的原始连续终点文件
- 缺少心血管表型整理表：本轮不执行机制桥接分析
