# 固定校区组合版 split：正式说明 + sensitivity analysis

> 本页用于外部正式交接，单独回答“若固定若干校区训练、另外若干校区测试，结论会怎样变化”，并把已选主方案 B 与补跑的 sensitivity 方案 A 放在同一页中，便于接收方快速理解 train/test 组合设计与边界判断。

## 怎么读这页

1. **先看方案设计**：不要一上来只盯某一格 AUC，而要先看 train/test 样本量、response rate gap、intensity 覆盖是否合理。
2. **再看 B 为什么是主方案**：它不是因为“所有数字都最高”，而是因为更像真正的多校区固定 hold-out。
3. **最后再看 A 的 sensitivity 价值**：A 的作用不是取代 B，而是检验“换一种更平衡的切法，结论会不会根本改变”。

> 这页真正要回答的不是“哪一套切法赢了”，而是“固定校区 train/test 组合之后，我们的结论边界有没有改变”。

## 1. 为什么要单独做固定校区组合版 split

- `leave_one_school_out` 是逐校区留一，更像系统的 grouped validation。
- 固定校区组合版 split 则更贴近现在讨论的实际表述：**若干校区训练，另外若干校区测试**。
- 但它的定位仍是 internal grouped validation / internal temporal validation，**不是 external validation**。

## 2. 两个固定校区方案

| scheme | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | sensitivity |
| B_4train_3test_all_intensity | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | selected |

### 当前主方案：B（4 train + 3 test）

- 选择理由：train/test 两侧都覆盖 3 种 intensity；test 样本量更大；更像多校区固定 hold-out。

## 3. 方案 B 结果（已选主方案）

### self-validation

| model_label | validation_scheme | mean_auc | mean_train_auc | mean_gap | train_schools | test_schools | train_n | test_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | fixed_school_combo_holdout | 0.5940 | 0.5687 | -0.0253 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |
| compact_fusion | fixed_school_combo_holdout | 0.5171 | 0.8178 | 0.3008 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |
| ultra_sparse_lipid | fixed_school_combo_holdout | 0.5334 | 0.7064 | 0.1730 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |

### out-phase

| model_label | validation_scheme | mean_auc | mean_train_auc | mean_gap | train_schools | test_schools | train_n | test_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | outphase_fixed_school_combo_holdout | 0.5325 | 0.5687 | 0.0362 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |
| compact_fusion | outphase_fixed_school_combo_holdout | 0.3191 | 0.8180 | 0.4988 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |
| ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 0.3133 | 0.7064 | 0.3931 | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 |

解读：

- `clinical_baseline_main` 在方案 B 的 self-validation AUC 约 **0.5940**，但 out-phase 约 **0.5325**。
- `compact_fusion` 与 `ultra_sparse_lipid` 的 train AUC 仍高于 test AUC 很多，说明 fixed split 下 generalization gap 依旧存在。

## 4. 方案 A 结果（补跑 sensitivity analysis）

### self-validation

| model_label | validation_scheme | mean_auc | mean_train_auc | mean_gap | train_schools | test_schools | train_n | test_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | fixed_school_combo_holdout | 0.5787 | 0.6292 | 0.0505 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |
| compact_fusion | fixed_school_combo_holdout | 0.5501 | 0.8269 | 0.2768 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |
| ultra_sparse_lipid | fixed_school_combo_holdout | 0.4857 | 0.7473 | 0.2616 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |

### out-phase

| model_label | validation_scheme | mean_auc | mean_train_auc | mean_gap | train_schools | test_schools | train_n | test_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | outphase_fixed_school_combo_holdout | 0.4543 | 0.6292 | 0.1749 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |
| compact_fusion | outphase_fixed_school_combo_holdout | 0.4594 | 0.8269 | 0.3675 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |
| ultra_sparse_lipid | outphase_fixed_school_combo_holdout | 0.3843 | 0.7473 | 0.3630 | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 |

解读：

- 方案 A 的优点是 response rate gap 更小，更适合作为 sensitivity analysis。
- 如果方案 A 与方案 B 的结论方向一致，就可以更稳妥地说明：**固定校区组合怎么切，当前信号都没有上升到强跨校区泛化的层级**。

## A / B 并排后的真正结论

- **方案 B** 在 `clinical_baseline_main` 上更好，尤其 out-phase 仍能保持在 **0.5325** 左右，因此它更适合作为当前正式交接的主固定 split。
- **方案 A** 在 response rate 上更平衡，也让 `compact_fusion` 的数值看起来稍好一些，但这并没有消除它的大 gap 问题。
- 两套切法下，模型排序会有一些细节变化，但**没有任何一个模型在 A/B 两套方案下都表现出一致、强而稳定的跨校区泛化**。
- 因此 A/B 并排之后最重要的收获不是“挑出更高分的一套”，而是可以更稳妥地说：**固定校区 train/test 的具体切法会影响局部数值，但不会把当前结论从 modest signal 改写成 strong generalization**。

## 5. 当前最稳妥的正式表述

1. strict nested CV outer-test AUC 约 **0.50–0.54** 仍是正式主结果。
2. AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`。
3. 固定校区组合版 split、leave-one-school-out、repeated hold-out、out-phase 都只能写成内部验证，不是 external validation。
4. 方案 B 适合作为当前主固定 split 展示；方案 A 可作为 sensitivity analysis 证明结论不依赖单一切法。

## 如对方问询：为什么不直接采用方案 A？

- 因为 **B 的结构更合理**：test 侧样本量更大，而且 train/test 两边都覆盖 3 种 intensity，更接近“多校区固定 hold-out”的主问题。
- 因为 **A 的定位本来就是 sensitivity**：它更像在问“如果用更平衡的 response rate 组合切一次，结论会不会变”。
- 现在 A 已经补跑，所以我们可以更从容地说：**不是没试过别的切法，而是试过以后，边界并没有根本变化。**

> 可直接用于正式交接的一句话：固定校区组合版 split 我们现在已经有主方案 B，也补跑了方案 A 做 sensitivity；两套切法结论方向一致——当前信号可以说存在，但还不足以写成强跨校区泛化或 external validation。

## 6. 包内可直接打开的文件

- 统一汇报页： [02_combined_formal_report.html](02_combined_formal_report.html)
- 文献 / protocol 说明： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)
- 固定校区组合结果对比 CSV： [fixed_school_combo_result_comparison.csv](fixed_school_combo_result_comparison.csv)
- 固定校区组合方案设计 CSV： [fixed_school_combo_scheme_design.csv](fixed_school_combo_scheme_design.csv)
