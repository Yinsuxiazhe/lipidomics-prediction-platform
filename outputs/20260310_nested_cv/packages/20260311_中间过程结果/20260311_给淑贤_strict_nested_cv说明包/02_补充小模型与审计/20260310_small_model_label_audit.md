# 2026-03-10 strict nested CV 小模型与标签/队列审计

> 本报告是对现有 strict nested CV 主结果的补充审计。所有性能数字继续沿用训练折内筛选、训练折内调参、外层测试折评估的诚实口径；本报告不把任何 exploratory 小模型结果升级为主结果。

## 1. 本轮补充动作

本轮只做了两件事：

1. 用**现有 strict nested CV 管线**重导出了两个预先定义的小模型比较：
   - `ultra_sparse_lipid` = `lipid_elastic_net` + `lipid_top_k=5` + `clinical_top_k=5` + `correlation_threshold=0.80`
   - `compact_fusion` = `fusion_elastic_net` + `lipid_top_k=15` + `clinical_top_k=10` + `correlation_threshold=0.90`
2. 基于本地现有 281/287 CSV 与会议记录，完成了一轮**结构级标签/队列/稳定特征审计**。

## 2. 结构级标签与队列审计

### 2.1 原始表与重叠队列

| 表 | 行数 | ID 唯一值个数 | 重复 ID 数 |
|---|---:|---:|---:|
| 281_new_grouped.csv | 281 | 281 | 0 |
| 281_merge_lipids_enroll.csv | 281 | 281 | 0 |
| 287_enroll_data_clean.csv | 287 | 287 | 0 |
| 287_enroll_data_predict.csv | 287 | 287 | 0 |

- 四表重叠后的最终分析样本量为 **281**。
- 临床表中存在但未进入最终 281 分析队列的 6 个 ID 为：`C115, C316, E217, F249, F298, F303`。
- 这与会议纪要中“287 → 281”的口径一致，说明本地分析队列边界是**可追溯的**。

### 2.2 标签文件本身能审计到什么程度

- `281_new_grouped.csv` 本地仅包含两列：`ID`、`Group`。
- `Group` 分布为：**response 163 / noresponse 118**。
- 在 `287_enroll_data_predict.csv` 与 `287_enroll_data_clean.csv` 中，按列名可检索到的相关字段为：`无`。
- 这些字段中没有可直接作为结局原始定义核验的一手信息（例如明确的 response 判定阈值、随访窗口、visit/week/month 终点值）。
- 因此，**本地当前最多只能完成结构级标签审计，不能完成“response/noresponse 真值口径”的原始定义核验**。这一点应在论文 Limitations 或内部方法记录中明确说明。

### 2.3 ID 前缀分布（弱证据，用于排查潜在批次/招募波次不均衡）

| prefix | n | response_n | noresponse_n | response_rate |
| --- | --- | --- | --- | --- |
| A | 54 | 32 | 22 | 0.5926 |
| B | 18 | 11 | 7 | 0.6111 |
| C | 52 | 20 | 32 | 0.3846 |
| D | 37 | 27 | 10 | 0.7297 |
| E | 38 | 19 | 19 | 0.5000 |
| F | 40 | 34 | 6 | 0.8500 |
| G | 42 | 20 | 22 | 0.4762 |

解读：
- 各前缀 response rate 在约 0.3191–0.8148 间波动，提示**可能存在招募波次或人群结构差异**。
- 但由于本地没有中心/批次/时间窗字段，以上仅能视为**弱线索**，不能直接下结论为批次效应或标签漂移。

## 3. 三个预定义小模型的 strict nested CV 比较

| model_label | source | mean_auc | std_auc | mean_train_auc | mean_gap | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- |
| clinical_baseline_main | clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 0.0767 | 5.0000 |
| ultra_sparse_lipid | lipid_elastic_net | 0.5396 | 0.0871 | 0.6949 | 0.1554 | 4.6000 |
| compact_fusion | fusion_elastic_net | 0.5376 | 0.0506 | 0.7621 | 0.2245 | 19.2000 |

关键读法：
- 主基线 `clinical_slim_logistic` 仍是**最稳但最弱**的模型，mean gap 仅 **0.0767**。
- `ultra_sparse_lipid` 的 mean AUC 为 **0.5396**，略高于主结果里的 baseline lipid（**0.5338**）；同时 mean gap 从 **0.2556** 降至 **0.1554**，说明**压缩到约 5 个脂质后，过拟合明显缓解**。
- `compact_fusion` 的 mean AUC 为 **0.5376**，与主结果 fusion（**0.5364**）非常接近，但 mean gap 从 **0.2691** 降至 **0.2245**，说明**融合模型缩小后更稳，但提升仍然很有限**。

结论：这组结果支持“**先压缩模型复杂度，再谈增量提升**”的方向；但它**不支持**把小模型的轻微数值改善包装成已经建立了高泛化预测模型。

## 4. 稳定特征审计（exploratory，仅用于解释，不作为主证据）

### 4.1 主基线 5 个临床变量

| feature | selection_rate | missing_rate_total | direction | exploratory_univariate_auc | standardized_mean_difference |
| --- | --- | --- | --- | --- | --- |
| age_enroll | 1.0000 | 0.0000 | higher_in_response | 0.5121 | 0.0689 |
| bmi_z_enroll | 1.0000 | 0.0000 | higher_in_response | 0.5414 | 0.1507 |
| SFT | 1.0000 | 0.0071 | higher_in_noresponse | 0.4275 | -0.2413 |
| Gender | 1.0000 | 0.0000 | higher_in_noresponse | 0.4834 | -0.0695 |
| BMI | 1.0000 | 0.0000 | higher_in_response | 0.5451 | 0.1464 |

解读：
- 5 个基线变量在主基线模型中均是预定义且 100% 入模。
- 从 full-cohort exploratory 单变量角度看，它们的效应量总体不大，更像是**弱到中等强度的基线差异**，这与基线模型 AUC 仅约 0.53 的结果一致。

### 4.2 ultra-sparse lipid 的前 5 个候选脂质

| feature | selection_rate | missing_rate_total | direction | exploratory_univariate_auc | standardized_mean_difference |
| --- | --- | --- | --- | --- | --- |
| LPC(16:0) | 0.6000 | 0.0000 | higher_in_noresponse | 0.3871 | -0.2027 |
| PC(32:1_22:4) | 0.6000 | 0.0000 | higher_in_noresponse | 0.3843 | -0.0882 |
| Hex2Cer(d18:2_16:0) | 0.4000 | 0.0000 | higher_in_response | 0.6132 | 0.3849 |
| PC(38:7e) | 0.4000 | 0.0000 | higher_in_noresponse | 0.3857 | -0.2047 |
| Cer(d19:1_24:1) | 0.2000 | 0.0000 | higher_in_noresponse | 0.3914 | -0.3356 |

解读：
- 在 ultra-sparse 设置下，真正达到较高稳定性的脂质并不多；最高 selection_rate 也仅 **0.6**。
- 这说明“把模型压缩到 5 个脂质”虽然有助于泛化，但**稳定脂质集合本身仍不够牢固**，暂时更适合作为候选变量而非定稿生物标志物。

### 4.3 compact fusion 中 selection_rate ≥ 0.6 的变量

| feature | selection_rate | missing_rate_total | direction | exploratory_univariate_auc | standardized_mean_difference |
| --- | --- | --- | --- | --- | --- |
| BMI | 1.0000 | 0.0000 | higher_in_response | 0.5451 | 0.1464 |
| Gender | 1.0000 | 0.0000 | higher_in_noresponse | 0.4834 | -0.0695 |
| SFT | 1.0000 | 0.0071 | higher_in_noresponse | 0.4275 | -0.2413 |
| age_enroll | 1.0000 | 0.0000 | higher_in_response | 0.5121 | 0.0689 |
| bmi_z_enroll | 1.0000 | 0.0000 | higher_in_response | 0.5414 | 0.1507 |
| Hex1Cer(d18:0_20:4) | 0.8000 | 0.0000 | higher_in_response | 0.6131 | 0.3964 |
| PC(32:1_22:4) | 0.8000 | 0.0000 | higher_in_noresponse | 0.3843 | -0.0882 |
| PC(38:7e) | 0.8000 | 0.0000 | higher_in_noresponse | 0.3857 | -0.2047 |
| Cer(d19:1_24:1) | 0.6000 | 0.0000 | higher_in_noresponse | 0.3914 | -0.3356 |
| FA(22:5) | 0.6000 | 0.0000 | higher_in_response | 0.3938 | 0.0406 |
| Hex2Cer(d18:2_16:0) | 0.6000 | 0.0000 | higher_in_response | 0.6132 | 0.3849 |
| LPC(16:0) | 0.6000 | 0.0000 | higher_in_noresponse | 0.3871 | -0.2027 |

解读：
- 5 个临床基线变量在 compact fusion 中仍全部保留，说明这些变量更像是**结构性锚点**。
- 相对稳定的脂质主要包括 `Hex1Cer(d18:0_20:4)`、`PC(32:1_22:4)`、`PC(38:7e)`、`Cer(d19:1_24:1)`、`FA(22:5)`、`Hex2Cer(d18:2_16:0)`、`LPC(16:0)`、`PC(26:3e)`。
- 但这些变量的 full-cohort exploratory 单变量 AUC 仍大多只在中等范围，提示**它们更可能贡献有限增量信号，而不是单独支撑高区分度**。

## 5. 可直接用于论文 / 汇报的收束表述

可以用下面这段作为当前更稳妥的工作结论：

> 在严格 nested CV 框架下，预先定义的小模型比较显示，进一步压缩特征数量可以降低训练-测试差值，并在脂质组模型中带来幅度很小的 AUC 改善；但整体泛化水平仍然有限，说明当前工作的主要瓶颈更可能来自标签定义、队列异质性与信号强度不足，而不是模型复杂度不够。基于此，后续更值得优先推进的是稳定特征与标签/队列审计，而不是继续无边界扩展变量与算法。

## 6. 本轮边界与定位

- 本报告中的小模型结果均属于 **strict nested CV 下的补充比较**，可用于 Discussion / Limitations / supplementary evidence。
- 论文主结果与主图仍应继续沿用当前 Figure 6-4 的 strict nested CV 主结果。
- 旧版高分结果若提及，仍只能定位为 **exploratory / development-stage internal validation**，不应升级为主结果。
