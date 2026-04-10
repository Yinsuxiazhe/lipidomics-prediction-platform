# 固定校区组合 split 对比（A sensitivity vs B selected）

## 方案设计总览

| scheme | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | sensitivity |
| B_4train_3test_all_intensity | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | selected |

## 结果对比

| scheme | scheme_role | stage | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | experiment | model_label | validation_scheme | mean_auc | mean_train_auc | mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | sensitivity | outphase | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | 0.4543 | 0.6292 | 0.1749 |
| A_5train_2test_balanced_rate | sensitivity | outphase | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | 0.4594 | 0.8269 | 0.3675 |
| A_5train_2test_balanced_rate | sensitivity | outphase | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 0.3843 | 0.7473 | 0.3630 |
| A_5train_2test_balanced_rate | sensitivity | self_validation | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | 0.5787 | 0.6292 | 0.0505 |
| A_5train_2test_balanced_rate | sensitivity | self_validation | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | 0.5501 | 0.8269 | 0.2768 |
| A_5train_2test_balanced_rate | sensitivity | self_validation | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | 0.4857 | 0.7473 | 0.2616 |
| B_4train_3test_all_intensity | selected | outphase | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | clinical_slim_logistic | clinical_baseline_main | outphase_fixed_school_combo_holdout | 0.5325 | 0.5687 | 0.0362 |
| B_4train_3test_all_intensity | selected | outphase | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | fusion_elastic_net | compact_fusion | outphase_fixed_school_combo_holdout | 0.3191 | 0.8180 | 0.4988 |
| B_4train_3test_all_intensity | selected | outphase | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | lipid_elastic_net | ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 0.3133 | 0.7064 | 0.3931 |
| B_4train_3test_all_intensity | selected | self_validation | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | clinical_slim_logistic | clinical_baseline_main | fixed_school_combo_holdout | 0.5940 | 0.5687 | -0.0253 |
| B_4train_3test_all_intensity | selected | self_validation | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | fusion_elastic_net | compact_fusion | fixed_school_combo_holdout | 0.5171 | 0.8178 | 0.3008 |
| B_4train_3test_all_intensity | selected | self_validation | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | lipid_elastic_net | ultra_sparse_lipid | fixed_school_combo_holdout | 0.5334 | 0.7064 | 0.1730 |

## 一句话结论

- 方案 B 仍更适合作为主固定校区组合版 split，因为 train/test 两侧都覆盖 3 种 intensity，且 test 样本量更大。
- 方案 A 作为 sensitivity analysis 的补跑结果，可用于说明：即便选更平衡的 response-rate 组合，结论边界也没有根本改变。
- 两个方案都仍属于 internal grouped validation / internal temporal validation，不是 external validation。
