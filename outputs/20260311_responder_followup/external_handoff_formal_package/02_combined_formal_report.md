# Responder 外部正式交接包（基线主结果 + school split follow-up）

> 本页是外部正式交接的总入口，按“正式主结果 → grouped split follow-up → out-phase temporal validation → protocol 与写作边界”的顺序组织，适合发送给外部协作方、顾问或公司端接收方。

**交接摘要：**

> 本包的核心价值不是把 headline AUC 做高，而是把当前最关键的科学边界讲清楚：strict nested CV outer-test AUC 仍约 0.50–0.54；真实 school split 与 out-phase 已完成补跑，但均属于内部验证证据链，不构成 external validation；AUC≈0.8 仅对应 `mean_train_auc`。

## 建议阅读顺序

1. **Figure 1：基线主图** —— 锚定正式主结果仍是谁。
2. **Figure 2：follow-up 小模型主图（F1）** —— 看真实 school split 接入后模型层面发生了什么。
3. **Figure 3：generalization gap（F2）** —— 看为什么不能只报最高 AUC。
4. **Figure 4：self-validation 分布（F3）** —— 看 repeated hold-out 与 school hold-out 的稳定性。
5. **Figure 5：out-phase 主图（F5）** —— 看 baseline → out-phase 的内部时相验证。
6. **Figure 6：out-phase 分布（F6）** —— 看时相迁移是否只由少数 split 支撑。
7. **Figure 7：group audit（F4）** —— 看当前 responder 标签与基线平衡边界。

## 三层正式表述边界

### 第一层：正式主结果

- 既有 strict nested CV 仍是正式主结果；旧目录保持只读引用，不被 follow-up 覆盖。

### 第二层：补充稳健性证据

- 本轮已补齐 repeated hold-out 与真实 `leave_one_school_out`。
- 旧 `leave-one-prefix-out` 仅保留为早期 weak proxy，不在本页作为主证据链。
- 这一层只说明“结论经受住了更严的内部切分检验”，**不构成 external validation**。

### 第三层：时相验证 + 写作边界

- 已接入 baseline → out-phase 的 `outphase_leave_one_school_out`。
- 运动 protocol 的主文建议仍保留在方案编号、周期、频次、总体框架这一级。
- 当前仍缺 `endpoint_source` 与心血管表型整理表，因此后续仍有明确待补项。

## 如何使用这一包进行交接

- **第一步**：先讲 strict nested CV outer-test AUC≈0.50–0.54 仍是正式主结果，AUC≈0.8 只对应 mean_train_auc。
- **第二步**：用 Figure 2–4 说明，真实 school split 补跑以后，模型之间更重要的差别是“稳不稳”，不是“谁偶尔更高一点”。
- **第三步**：用 Figure 5–6 说明 out-phase internal temporal validation 已经接进来，但时相迁移仍更难。
- **第四步**：用 Figure 7 + protocol 写法说明，把当前能写什么、还缺什么、不能过度说什么一次讲清楚。

> 如果接收方只需要一句话：这套包的核心价值，不是把分数做高，而是把“正式主结果 + grouped split + out-phase + protocol 边界”串成一条能防守的解释链。

## Figure 1. 基线主图：既有 strict nested CV 正式主结果锚点

![Figure 1：基线主图](assets/01_baseline_main.png)

图文件： [PNG](assets/01_baseline_main.png) · [PDF](assets/01_baseline_main.pdf)

- 这张图仍是正式主结果的锚点。
- follow-up 的任务不是替换它，而是补强它的边界、防守性与解释链。

## Figure 2. Follow-up 小模型主图（F1）

![Figure 2：follow-up 小模型主图](assets/02_followup_f1_model_performance.png)

图文件： [PNG](assets/02_followup_f1_model_performance.png) · [PDF](assets/02_followup_f1_model_performance.pdf)

- 这张图对应真实 school split 接入后的核心 follow-up 比较。
- `compact_fusion` 的上限仍在，但 `clinical_baseline_main` 仍是更稳的路线。

## Figure 3. Generalization gap（F2）

![Figure 3：generalization gap](assets/03_followup_f2_generalization_gap.png)

图文件： [PNG](assets/03_followup_f2_generalization_gap.png) · [PDF](assets/03_followup_f2_generalization_gap.pdf)

- 这张图专门解释为什么不能把 AUC 最高的模型直接写成主叙事。
- school hold-out 与 out-phase 下，gap 依旧提示融合路线更难防守。

## Figure 4. Self-validation 分布（F3）

![Figure 4：self-validation 分布](assets/04_followup_f3_self_validation_distribution.png)

图文件： [PNG](assets/04_followup_f3_self_validation_distribution.png) · [PDF](assets/04_followup_f3_self_validation_distribution.pdf)

- 这里看的是 repeated hold-out 与 leave-one-school-out 的 split-level 分布。
- 它能支持“结果不是单次随机切分偶然所得”，但不能支持“已经有强外部验证”。

## Figure 5. out-phase 主图（F5）

![Figure 5：out-phase 主图](assets/06_followup_f5_outphase_model_performance.png)

图文件： [PNG](assets/06_followup_f5_outphase_model_performance.png) · [PDF](assets/06_followup_f5_outphase_model_performance.pdf)

- 这是 baseline → out-phase 的内部时相验证主图。
- 当前 best out-phase mean AUC 仍接近 0.50，只能作为 modest signal / 边界说明。

## Figure 6. out-phase 分布（F6）

![Figure 6：out-phase 分布](assets/07_followup_f6_outphase_distribution.png)

图文件： [PNG](assets/07_followup_f6_outphase_distribution.png) · [PDF](assets/07_followup_f6_outphase_distribution.pdf)

- 这张图用来说明 out-phase 的结果不是靠少数 split 偶然撑起来。
- 但它同时也提醒：时相迁移仍比同相切分更难。

## Figure 7. 当前 responder 分组审计（F4）

![Figure 7：当前 responder 分组审计](assets/05_followup_f4_group_audit.png)

图文件： [PNG](assets/05_followup_f4_group_audit.png) · [PDF](assets/05_followup_f4_group_audit.pdf)

- 这张图仍负责交代当前标签来源与基线平衡边界。
- 因为缺原始连续终点文件，所以它说明的是“为什么当前标签还能先保留”，不是“标签已被彻底重定义”。

## 关键数字速览

| model_label | strict_mean_auc | leave_one_school_out_mean_auc | repeated_random_holdout_mean_auc | outphase_leave_one_school_out_mean_auc | outphase_repeated_random_holdout_mean_auc | leave_one_school_out_mean_gap | outphase_leave_one_school_out_mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | 0.5297 | 0.5155 | 0.5545 | 0.4221 | 0.3601 | 0.0904 | 0.1839 |
| ultra_sparse_lipid | 0.5338 | 0.5310 | 0.5409 | 0.4941 | 0.5034 | 0.1625 | 0.1993 |
| compact_fusion | 0.5364 | 0.5246 | 0.5718 | 0.4774 | 0.4986 | 0.2353 | 0.2825 |

## 把 7 张图串起来看

- **Figure 1** 负责定锚：正式主结果仍是 strict nested CV，而不是 follow-up 里任何单次切法。
- **Figure 2–3** 负责比较模型路线：它们告诉我们为什么不能只拿最高 AUC 当主结论，而要同时看 gap 和稳健性。
- **Figure 4** 负责看 split-level 稳定性：证明不是一次随机切分碰巧得到的数字。
- **Figure 5–6** 负责看时相迁移：提醒我们 baseline → out-phase 的问题比同相 grouped split 更难。
- **Figure 7** 负责交代标签边界：当前 responder 标签还能先用，但并不代表 alternative grouping sensitivity 已完成。

## 不能过度宣称的点

- school split、fixed school combo split、repeated hold-out、out-phase internal temporal validation 都**不能写成 external validation**。
- 这套包支持的是“当前信号 modest、边界更清楚、表达更稳妥”，不支持“跨校区强泛化已被证明”。
- 新增的 fixed school combo 页面（`04_fixed_school_combo_note.html`）也只是把 train/test 组合切法讲得更具体，**不会改变正式主结果锚点**。

## school split 与 protocol 说明页

- school / community split 说明页： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)
- school split 与 protocol 说明： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)
- 固定校区组合版 split： [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)
- 学校 grouped holdout 明细： [school_group_holdout_summary.csv](school_group_holdout_summary.csv)
- 学校 / 强度映射： [id_school_intensity_mapping.csv](id_school_intensity_mapping.csv)

## 固定校区组合版 split（新增补充页）

- 如果接收方现在更关心‘固定若干校区训练、另外若干校区测试’的写法，直接打开 [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)。
- 该页同时放了当前主方案 **B（4 train + 3 test）**，以及补跑的 **方案 A（5 train + 2 test）sensitivity analysis**。
- 两个方案都仍属于 internal grouped validation / internal temporal validation，不能写成 external validation。

## 当前仍待补充的数据条件

- `endpoint_source`：没有原始连续终点文件，就不做真正的 alternative grouping sensitivity。
- 心血管表型整理表：没有这张表，就不做机制桥接分析。

## 包内文件

- 总交接页： [02_combined_formal_report.html](02_combined_formal_report.html)
- follow-up 正式交接页： [01_followup_formal_report.html](01_followup_formal_report.html)
- school split / protocol 说明： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)
- fixed school combo sensitivity： [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)
- strict nested CV 指标说明： [strict_nested_cv_key_metrics.csv](strict_nested_cv_key_metrics.csv)
- 学校 grouped holdout 汇总： [school_group_holdout_summary.csv](school_group_holdout_summary.csv)
- self-validation 汇总： [self_validation_summary.csv](self_validation_summary.csv)
- out-phase 汇总： [outphase_validation_summary.csv](outphase_validation_summary.csv)
- fixed school combo 对比： [fixed_school_combo_result_comparison.csv](fixed_school_combo_result_comparison.csv)
