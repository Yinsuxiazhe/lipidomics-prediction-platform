# 固定校区组合 split 结果（方案 A / sensitivity）

> 本目录对应 5 校区 train + 2 校区 test 的 sensitivity analysis，独立于主 follow-up 输出，不覆盖 strict nested CV 主锚点。

## 实施方案

- train schools：中关村、冷泉、唐家岭校区、本部、百旺
- test schools：六里屯、华清校区
- train_n=195，test_n=86
- train_response_rate=0.5744，test_response_rate=0.5930
- abs_response_rate_gap=0.0187
- train/test intensity 覆盖：3 / 2

## 候选方案对比

| scheme | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | sensitivity |
| B_4train_3test_all_intensity | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | selected |

## self-validation 固定校区组合结果

| experiment | model_label | validation_scheme | n_total_splits | n_completed | mean_auc | mean_train_auc | mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | 1 | 1 | 0.5787 | 0.6292 | 0.0505 |
| fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | 1 | 1 | 0.5501 | 0.8269 | 0.2768 |
| lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | 1 | 1 | 0.4857 | 0.7473 | 0.2616 |

## out-phase 固定校区组合结果

| experiment | model_label | validation_scheme | n_total_splits | n_completed | mean_auc | mean_train_auc | mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | 1 | 1 | 0.4543 | 0.6292 | 0.1749 |
| fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | 1 | 1 | 0.4594 | 0.8269 | 0.3675 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 1 | 1 | 0.3843 | 0.7473 | 0.3630 |

## split 级别明细

### self-validation fold

| experiment | model_label | validation_scheme | split_id | holdout_group | status | auc | train_auc | n_train | n_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.5787 | 0.6292 | 195 | 86 |
| lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.4857 | 0.7473 | 195 | 86 |
| fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.5501 | 0.8269 | 195 | 86 |

### out-phase fold

| experiment | model_label | validation_scheme | split_id | holdout_group | status | auc | train_auc | n_train | n_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.4543 | 0.6292 | 195 | 86 |
| lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.3843 | 0.7473 | 195 | 86 |
| fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | outphase_fixed_school_combo_holdout_balanced_5train2test_balanced_rate | 六里屯 + 华清校区 | completed | 0.4594 | 0.8269 | 195 | 86 |

## sensitivity interpretation

- 方案 A 的价值在于 response rate 更平衡，适合作为 sensitivity analysis。
- 若方案 A 与方案 B 都没有把 AUC 提升到新的量级，则可以更稳妥地说明：当前跨校区泛化结论整体仍偏弱。
- 本 fixed school combo split、leave-one-school-out、repeated hold-out、out-phase fixed school combo 都不是 external validation。

## 口径边界

- 正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 中的 mean_train_auc。
- 本固定校区组合 split 仍属于 internal grouped validation / internal temporal validation。
