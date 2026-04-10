# 出组 / 干预后 out-phase 验证

## 方法定位

- 本模块是**内部时相验证**：训练数据来自基线时点，测试数据来自同一批受试者的 out / 干预后时点。
- 这里**不是外部验证**，也不应写成 external validation。
- 为避免同一受试者在训练与测试同时出现，所有 split 都采用“基线训练 ID 集 / out-phase 测试 ID 集”配对评估。

## grouped split 说明

- 本轮已接入真实 school grouped split（leave-one-school-out / outphase leave-one-school-out）；这仍属于内部 grouped validation / internal temporal validation，不是 external validation。

## 数据接入概况

- overlap_id_count: 281
- out_lipid 内置 Group 与主标签一致率: 0.9146
- out_lipid Group mismatch count: 24
- clinical anchor mapping: {'age_enroll': 'age_out', 'bmi_z_enroll': 'bmi_z_out', 'SFT': 'SFT', 'Gender': 'Gender', 'BMI': 'BMI'}

## 结果汇总

| experiment | model_label | validation_scheme | train_phase | test_phase | n_total_splits | n_completed | n_skipped | mean_auc | std_auc | mean_train_auc | mean_gap | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4221 | 0.0988 | 0.6060 | 0.1839 | 5.0000 |
| clinical_slim_logistic | clinical_baseline_main | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.3601 | 0.0872 | 0.6073 | 0.2472 | 5.0000 |
| fusion_elastic_net | compact_fusion | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4774 | 0.1118 | 0.7599 | 0.2825 | 19.8571 |
| fusion_elastic_net | compact_fusion | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.4986 | 0.0983 | 0.7655 | 0.2670 | 19.7333 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_leave_one_school_out | baseline | outphase | 7 | 7 | 0 | 0.4941 | 0.0503 | 0.6934 | 0.1993 | 4.8571 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_repeated_random_holdout | baseline | outphase | 30 | 30 | 0 | 0.5034 | 0.0919 | 0.6833 | 0.1799 | 4.9000 |

> 解读边界：如果 out-phase 下仍保留一定区分趋势，只能支持“差异可能具有一定时相稳定性/个体异质性延续”，不能等同于外部人群复现。
