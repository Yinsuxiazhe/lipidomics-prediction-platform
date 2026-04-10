# Responder follow-up 图文汇报页（已接入真实 school split + out-phase）

> 本页给老师/合作者直接看：**不改正式 strict nested CV 主结果，但已把真实 school grouped split 与 out-phase internal temporal validation 接进来，形成当前第一阶段最完整的 follow-up 页面。**

**可直接发送：**

> 老师您好，我把 responder 第一阶段 follow-up 又往前补了一步：这次不是把旧的 prefix proxy 改名，而是已经根据学校映射表补跑了真实 `leave-one-school-out` 和 `outphase_leave_one_school_out`。当前结果整体仍在 AUC 0.50 左右，说明它补强的是稳健性与边界说明，不是更强的 external validation；正式主结果还是 strict nested CV outer-test AUC≈0.50–0.54，AUC≈0.8 只对应 mean_train_auc。

## 一页结论

- **正式主结果不变**：strict nested CV 仍是论文与正式汇报的主锚点。
- **真实学校 grouped split 已补跑**：`leave-one-school-out` 的 mean AUC 约 **0.5155–0.5310**。
- **out-phase 学校 grouped split 也已补跑**：`outphase_leave_one_school_out` 的 mean AUC 约 **0.4221–0.4941**。
- **结论边界不变**：repeated hold-out、school split、out-phase internal temporal validation 都不能写成 `external validation`。
- **运动 protocol 主文继续保守写**：先写方案编号、周期、频次、总体框架；强度细节放补充材料或答审。

## 怎么读这页

1. **先看主锚点**：strict nested CV outer-test AUC≈0.50–0.54 仍没变，这决定了正式主结论的上限。
2. **再看 grouped split / out-phase 数字**：核心不是看有没有某一格分数更高，而是看信号在更严切法下还能不能站住。
3. **再看 F1–F6**：这些图的作用是解释“为什么不能只报最高 AUC”，以及“为什么要同时看 gap、split-level 分布、时相迁移”。
4. **最后看 protocol 与 blocked**：知道当前主文能写到哪一步，哪些细节应该放补充材料或等后续数据到位再写。

## 结构性解读

- `repeated_random_holdout` 普遍高于 `leave_one_school_out`，说明**随机切分更乐观**，而真实学校 grouped split 更接近来源异质性的检验。
- `clinical_baseline_main` 的上限不是最高，但 **generalization gap 最小**，因此它更适合作为当前最稳妥、最防守的主叙事。
- `compact_fusion` 往往能给出更高的 train AUC，但 school split / out-phase 下 gap 更大，说明它更像“容量更高但稳定性更弱”的路线。
- `outphase_leave_one_school_out` 进一步下降，提示**时相迁移比同相 grouped split 更难**；这支持“信号 modest but not robust enough”，不支持“强泛化已建立”。

## 不能过度宣称的点

- 这里所有补充分析都属于**内部验证**，不是 external validation。
- 用户记得的 **AUC≈0.8** 仍然只对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- 这页的价值是把“边界、稳定性、风险”讲清楚，而不是把 headline 从 0.53 改写成更高的 test AUC。

## 新分析放在哪里

- 学校/强度映射：`id_school_intensity_mapping.csv`
- 学校级 grouped holdout 汇总：`school_group_holdout_summary.csv`
- 模型级 self-validation 汇总：`self_validation_summary.csv`
- 模型级 out-phase 汇总：`outphase_validation_summary.csv`
- 综合比较表：`small_model_followup_comparison.csv`
- 对接思路定位页：`followup_plan_alignment.md`
- 文献与 protocol 说明：`03_literature_followup_note.md`


## 正式主结果仍是主锚点

| experiment | mean_auc | std_auc | mean_train_auc | n_outer_folds |
| --- | --- | --- | --- | --- |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 5 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 | 5 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 | 5 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 | 5 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 | 5 |

- 正式可防守的主结论仍然来自 strict nested CV outer-test AUC≈0.50–0.54。
- 用户记得的 AUC≈0.8 只对应 `mean_train_auc`，不是 outer-test AUC。

## 学校 split + out-phase 关键数字

| model_label | strict_mean_auc | leave_one_school_out_mean_auc | repeated_random_holdout_mean_auc | outphase_leave_one_school_out_mean_auc | outphase_repeated_random_holdout_mean_auc | leave_one_school_out_mean_gap | outphase_leave_one_school_out_mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | 0.5297 | 0.5155 | 0.5545 | 0.4221 | 0.3601 | 0.0904 | 0.1839 |
| ultra_sparse_lipid | 0.5338 | 0.5310 | 0.5409 | 0.4941 | 0.5034 | 0.1625 | 0.1993 |
| compact_fusion | 0.5364 | 0.5246 | 0.5718 | 0.4774 | 0.4986 | 0.2353 | 0.2825 |

## Figure F1. 小模型 follow-up 主图

![Figure F1：小模型 follow-up 主图](assets/02_followup_f1_model_performance.png)

图文件： [PNG](assets/02_followup_f1_model_performance.png) · [PDF](assets/02_followup_f1_model_performance.pdf)

- `compact_fusion` 的 repeated hold-out AUC 仍最高，但 `clinical_baseline_main` 的 generalization gap 更小。
- 真实 school hold-out 接入后，三条路线的 mean AUC 依旧在 0.52 左右，没有把主结论抬高到新的量级。

## Figure F2. Generalization gap

![Figure F2：generalization gap](assets/03_followup_f2_generalization_gap.png)

图文件： [PNG](assets/03_followup_f2_generalization_gap.png) · [PDF](assets/03_followup_f2_generalization_gap.pdf)

- `clinical_baseline_main` 的 `leave_one_school_out_mean_gap` 最小，更适合作为稳妥主叙事。
- `compact_fusion` 虽有性能上限，但 school hold-out 与 out-phase 下 gap 仍明显更大。

## Figure F3. Self-validation 分布图

![Figure F3：self-validation 分布图](assets/04_followup_f3_self_validation_distribution.png)

图文件： [PNG](assets/04_followup_f3_self_validation_distribution.png) · [PDF](assets/04_followup_f3_self_validation_distribution.pdf)

- 这张图把 repeated hold-out 与 leave-one-school-out 的 split-level 分布摆出来。
- 作用是告诉老师：这不是单次切分偶然得到的结果，但它也没有显示出强泛化。

## Figure F5. out-phase 内部时相验证主图

![Figure F5：out-phase 主图](assets/06_followup_f5_outphase_model_performance.png)

图文件： [PNG](assets/06_followup_f5_outphase_model_performance.png) · [PDF](assets/06_followup_f5_outphase_model_performance.pdf)

- baseline → out-phase 的内部时相验证已经接入。
- 但当前 best `outphase_leave_one_school_out` 也只在 0.49 左右，仍属于边界说明型证据。

## Figure F6. out-phase 分布图

![Figure F6：out-phase 分布图](assets/07_followup_f6_outphase_distribution.png)

图文件： [PNG](assets/07_followup_f6_outphase_distribution.png) · [PDF](assets/07_followup_f6_outphase_distribution.pdf)

- 这张图把 out-phase repeated hold-out 与 out-phase school hold-out 的分布展开。
- 它支持的不是“强复制”，而是“我们已经把更严一点的 internal temporal validation 做出来了”。

## Figure F4. 当前 responder 分组审计图

![Figure F4：当前 responder 分组审计图](assets/05_followup_f4_group_audit.png)

图文件： [PNG](assets/05_followup_f4_group_audit.png) · [PDF](assets/05_followup_f4_group_audit.pdf)

- 当前标签来源仍是既有二分类标签 + 会议纪要级证据链，不是原始连续终点真值表。
- 因此这张图的作用仍是交代边界，而不是证明 alternative grouping sensitivity 已完成。

## 运动 protocol 写法建议

- **主文**：写干预方案编号、周期、频次、总体框架。
- **补充材料 / 答审**：再写学校 / 场地对应的强度分层、执行细节、依从性。
- 如果需要对应学校强度，可直接查看 `id_school_intensity_mapping.csv`。

## 当前仍 blocked 的内容

- `endpoint_source`：缺原始连续终点文件，暂不做真正的 alternative grouping sensitivity。
- 心血管表型整理表：暂不做机制桥接分析。

## 相关文件入口

- 统一汇报页： [02_combined_report.html](02_combined_report.html)
- 主汇总： [followup_summary.md](followup_summary.md)
- 学校 split / protocol 说明： [03_literature_followup_note.html](03_literature_followup_note.html)
- 学校 grouped holdout： [school_group_holdout_summary.csv](school_group_holdout_summary.csv)
- 学校/强度映射： [id_school_intensity_mapping.csv](id_school_intensity_mapping.csv)
- out-phase 说明： [outphase_validation.md](outphase_validation.md)
