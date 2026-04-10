# 固定校区组合 split 结果（方案 B）

> 本目录只做局部 fixed school combo split 分析，不覆盖主 follow-up 目录，不改 strict nested CV 主锚点。

## 实施方案

- train schools：六里屯、冷泉、本部、百旺
- test schools：中关村、华清校区、唐家岭校区
- train_n=161，test_n=120
- train_response_rate=0.5590，test_response_rate=0.6083
- train/test 两侧均覆盖 3 种 intensity。

## 候选方案对比

| scheme | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | backup |
| B_4train_3test_all_intensity | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | selected |

## self-validation 固定校区组合结果

| experiment | model_label | validation_scheme | n_total_splits | n_completed | mean_auc | mean_train_auc | mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | 1 | 1 | 0.5940 | 0.5687 | -0.0253 |
| fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | 1 | 1 | 0.5171 | 0.8178 | 0.3008 |
| lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | 1 | 1 | 0.5334 | 0.7064 | 0.1730 |

## out-phase 固定校区组合结果

| experiment | model_label | validation_scheme | n_total_splits | n_completed | mean_auc | mean_train_auc | mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | 1 | 1 | 0.5325 | 0.5687 | 0.0362 |
| fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | 1 | 1 | 0.3191 | 0.8180 | 0.4988 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 1 | 1 | 0.3133 | 0.7064 | 0.3931 |

## split 级别明细

### self-validation fold

| experiment | model_label | validation_scheme | split_id | holdout_group | status | auc | train_auc | n_train | n_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.5940 | 0.5687 | 161 | 120 |
| lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.5334 | 0.7064 | 161 | 120 |
| fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.5171 | 0.8178 | 161 | 120 |

### out-phase fold

| experiment | model_label | validation_scheme | split_id | holdout_group | status | auc | train_auc | n_train | n_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.5325 | 0.5687 | 161 | 120 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.3133 | 0.7064 | 161 | 120 |
| fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_4train3test_all_intensity | 中关村 + 华清校区 + 唐家岭校区 | completed | 0.3191 | 0.8180 | 161 | 120 |

## 口径边界

- 正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 中的 mean_train_auc。
- 本固定校区组合 split、leave-one-school-out、repeated hold-out、outphase fixed school combo 都不是 external validation。
