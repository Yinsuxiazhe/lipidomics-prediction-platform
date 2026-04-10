# 学校 / 社区 split 与运动 protocol 正式说明（外部交接版）

> 本页基于两篇参考文献与当前项目已完成分析整理，目的不是重写正式主结果，而是把“学校 / 社区 split 放在哪里、能怎么写、不能怎么写、运动 protocol 如何稳妥落地”整理成对外可引用的正式说明。

## 怎么读这页

- 这页不是用来展示“又做出了一个更高的 AUC”，而是用来回答两个更实际的问题：**学校 / 社区 split 现在到底放在哪里了？运动 protocol 正文该怎么写才稳妥？**
- 因此它的阅读顺序应该是：**先看文献启发 → 再看本地已落地分析 → 最后看现在能怎么写、不能怎么写**。
- 如果把 02 页看成“总交接页”，那这页就是用于补充方法学解释与写作边界的正式说明页。

## 1. 这轮新增分析现在放在哪里

- 学校/强度映射：`id_school_intensity_mapping.csv`
- 学校级 grouped holdout 汇总：`school_group_holdout_summary.csv`
- 模型级 self-validation 汇总：`self_validation_summary.csv`
- 模型级 out-phase 汇总：`outphase_validation_summary.csv`
- 综合比较表：`small_model_followup_comparison.csv`
- 总交接页：`02_combined_formal_report.html`
- 正式说明页：`03_school_split_protocol_note.html`


如果只想快速回答“学校/社区 split 现在放哪了”，最直接看这 4 个文件：

1. `school_group_holdout_summary.csv`：按学校汇总的留一结果，含 `baseline_n / response_rate / intensity / self_auc / outphase_auc`。
2. `self_validation_summary.csv`：模型级 `leave_one_school_out` 均值。
3. `outphase_validation_summary.csv`：模型级 `outphase_leave_one_school_out` 均值。
4. `02_combined_formal_report.html`：汇总当前结论边界、页面入口与正式交接顺序。

## 2. 两篇参考文献给我们的实际启发

| 参考文献 | 设计要点 | 对本项目真正可借鉴之处 | 当前不能直接照搬之处 |
| --- | --- | --- | --- |
| Liu et al., Cell Metabolism 2020（徐爱民团队） | discovery cohort 与独立 validation cohort 来自不同 community | 提醒我们：如果存在可审计的真实来源分组，可以优先做 grouped split / cohort-style validation | 我们当前补跑的是同一项目内的学校 grouped split，仍属于 internal grouped validation，不是独立 external validation |
| Nature Medicine 儿童脂质组文章 | cohort 内 repeated cross-validation 即可形成预测证据 | 支持我们把 repeated hold-out / school grouped split 作为 honest internal evidence 写清楚 | 这不意味着可以把 `mean_train_auc≈0.8` 写成正式 test AUC，更不能替代 strict nested CV outer-test 结果 |

## 3. 本项目现在已经补上的真实 school grouped split

### 3.1 映射来源

- 真实映射来自项目原始学校-强度对应表。
- 已导出为：`id_school_intensity_mapping.csv`。
- 当前学校与运动强度的对应关系如下：

| school | intensity |
| --- | --- |
| 华清校区 | Intermittent vigorous |
| 百旺 | Intermittent vigorous |
| 唐家岭校区 | Low-intensity |
| 本部 | Low-intensity |
| 中关村 | Moderate-intensity |
| 六里屯 | Moderate-intensity |
| 冷泉 | Moderate-intensity |

### 3.2 为什么旧 prefix split 不能回溯改名成 school split

- 这轮已经确认：`prefix != school`，两者并非一一对应。
- 典型例子：`C` 前缀同时对应 `本部` 和 `六里屯`。
- 因此旧的 `leave-one-prefix-out` 只能保留为早期 grouped weak proxy，**不能在更新后回写成学校 / 社区 split**。

## 4. 当前结果说明什么

| model_label | strict_mean_auc | leave_one_school_out_mean_auc | repeated_random_holdout_mean_auc | outphase_leave_one_school_out_mean_auc | outphase_repeated_random_holdout_mean_auc | leave_one_school_out_mean_gap | outphase_leave_one_school_out_mean_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | 0.5297 | 0.5155 | 0.5545 | 0.4221 | 0.3601 | 0.0904 | 0.1839 |
| ultra_sparse_lipid | 0.5338 | 0.5310 | 0.5409 | 0.4941 | 0.5034 | 0.1625 | 0.1993 |
| compact_fusion | 0.5364 | 0.5246 | 0.5718 | 0.4774 | 0.4986 | 0.2353 | 0.2825 |

解读要点：

- **正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54。**
- 真实 `leave-one-school-out` 的均值大约在 **0.5155–0.5310**，没有出现更强的泛化结论。
- `outphase_leave_one_school_out` 更低，约 **0.4221–0.4941**，说明 baseline → out-phase 的时相迁移信号依然偏弱。
- 用户记得的 **AUC≈0.8 只对应 `mean_train_auc`**，不对应 outer-test AUC，也不对应任何 external validation AUC。

## 结构性解读：文献启发怎样映射到本项目

- 徐爱民团队那篇文章真正给我们的启发，不是“借一句 external validation 说法”，而是：**如果来源分组是真实且可审计的，就优先做 grouped split / cohort-style checking**。
- Nature Medicine 那篇文章给的启发则是：**cohort 内 repeated cross-validation 和内部验证本身也可以成为 honest evidence**，前提是口径不能越界。
- 放到我们项目里，当前最合理的落点就是：**真实学校 grouped split + out-phase internal temporal validation** 已经补上，但它们仍然都在同一项目框架内，因此不能升级表述为 external validation。
- 这也是为什么运动 protocol 的正文写法要保守：当前 prediction 的核心任务还是守住主结果边界，而不是在主文里过早铺开所有场地/强度细节。

## 5. 现在可以怎么写，不能怎么写

### 可以写的

1. 已经补跑了**真实学校 grouped split**：`leave_one_school_out` 与 `outphase_leave_one_school_out`。
2. 它们的定位是**内部 grouped validation / internal temporal validation**，用于补充稳健性证据。
3. 当前结果整体支持的仍是：现有 responder 信号较弱，正式主结论继续锚定 strict nested CV outer-test AUC≈0.50–0.54。

### 不能写的

1. 不能把 repeated hold-out、leave-one-school-out、leave-one-prefix-out、out-phase internal temporal validation 写成 **external validation**。
2. 不能把 `mean_train_auc≈0.8` 写成正式 test AUC。
3. 不能因为学校 split 已补跑，就把当前结果升级成“强泛化已被证明”。

## 6. 运动 protocol 写法建议

当前最稳妥的写法是：

- **主文先写**：干预方案编号、周期、频次、总体框架。
- **补充材料 / 答审再写**：学校/场地对应的强度分层、执行细节、依从性记录。
- 如对方进一步问询，再引用 `id_school_intensity_mapping.csv` 中的学校-强度对应关系，说明这套信息已整理为可审计映射文件。

## 7. 仍值得继续补的数据

1. `endpoint_source`：只有拿到 responder 原始连续终点，才值得做真正的 alternative grouping sensitivity。
2. 心血管表型整理表：只有数据到位后，才适合做机制桥接分析。

## 常见问答（对外版）

- **问：school / community split 是否已经完成？**  
  答：已经完成，真实学校映射来自项目原始学校-强度对应表，结果落在 `school_group_holdout_summary.csv`、`self_validation_summary.csv` 和 `outphase_validation_summary.csv`。
- **问：为什么这些结果仍不能写成 external validation？**  
  答：因为这些 split 仍然来自同一项目内部，只是按真实 school/source grouping 与时相去切，不是独立新 cohort。
- **问：为什么运动 protocol 不建议在主文中一次铺开所有强度细节？**  
  答：因为主文当前更需要先把主结果与验证边界讲清楚；学校-强度细节已整理为可审计映射文件，更适合放补充材料或答审时展开。

## 8. 一句话结论

> 学校 / 社区 split 对应的新分析已整合到 `school_group_holdout_summary.csv`、`self_validation_summary.csv`、`outphase_validation_summary.csv` 与 `02_combined_formal_report.html` 中；当前结果支持“真实学校 grouped split 已补跑，但整体 AUC 仍在 0.50 左右”，不支持将其升级表述为 external validation。运动 protocol 的主文写法则建议继续从方案编号、周期、频次入手，把强度细节放到补充材料或答审中。
