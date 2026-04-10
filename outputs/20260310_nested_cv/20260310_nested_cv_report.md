# 脂质组学预测项目阶段性结果汇总

> 基于 281 例样本、5 折外层 nested CV、3 折内层调参，对临床、脂质组及融合模型进行了首轮严格泛化评估。

## 一、执行摘要

- 当前严格 nested CV 下，**最佳模型为 `fusion_elastic_net`，mean AUC = 0.5364**。
- 目前所有模型的验证 AUC 都集中在 **0.50–0.54** 区间，**尚未接近 0.80 目标**。
- 扩展临床和扩展融合模型的训练集 AUC 明显更高，但验证集未同步提升，提示**过拟合明显**。
- 后续工作的重点不应再是盲目堆复杂模型，而应转向 **标签审计、队列 QC、变量质量检查与任务重构**。

## 二、数据与队列概况

| 队列 | 样本数 | 特征维度 | 分组分布 |
|---|---:|---:|---|
| group_lipid | 281 | 1611 | 163 response / 118 noresponse |
| group_clinical_slim | 281 | 7 | 163 response / 118 noresponse |
| group_clinical_full | 281 | 416 | 163 response / 118 noresponse |
| group_fusion | 281 | 1615 | 163 response / 118 noresponse |
| group_fusion_full | 281 | 2024 | 163 response / 118 noresponse |

## 三、主模型结果（严格 nested CV）

| 实验 | mean AUC | std AUC | mean train AUC | 训练-验证差值 |
|---|---:|---:|---:|---:|
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 | 0.2691 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7894 | 0.2556 |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 0.0767 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 | 0.3238 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 | 0.2426 |

### 结果解读

- `fusion_elastic_net` 暂时排名第一，但优势非常有限，说明“临床精简变量 + 脂质组”有一点点增益，但远不够支撑高泛化预测。
- `fusion_full_elastic_net` 的训练 AUC 达到 **0.8496**，但验证 AUC 只有 **0.5258**，属于最典型的高维过拟合。
- `clinical_slim_logistic` 虽然分数不高，但训练-验证差值最小，说明它是目前**最稳但最弱**的基线。

## 四、各模型 fold 级稳定性

- **clinical_slim_logistic**：fold AUC = [0.4356, 0.5296, 0.5296, 0.5169, 0.6367]；平均训练-验证差值 = 0.0767
- **lipid_elastic_net**：fold AUC = [0.5732, 0.4704, 0.4914, 0.6536, 0.4805]；平均训练-验证差值 = 0.2556
- **clinical_full_elastic_net**：fold AUC = [0.4129, 0.6034, 0.5231, 0.5469, 0.4193]；平均训练-验证差值 = 0.2426
- **fusion_elastic_net**：fold AUC = [0.5783, 0.4704, 0.4954, 0.6159, 0.5221]；平均训练-验证差值 = 0.2691
- **fusion_full_elastic_net**：fold AUC = [0.5215, 0.5072, 0.5402, 0.599, 0.4609]；平均训练-验证差值 = 0.3238

## 五、稳定出现的特征（按出现频次排序）

### 精简融合模型：`fusion_elastic_net`

| 特征 | 出现频次（5 folds） |
|---|---:|
| BMI | 5 |
| Gender | 5 |
| PA(28:0) | 5 |
| PC(38:7e) | 5 |
| SFT | 5 |
| age_enroll | 5 |
| bmi_z_enroll | 5 |
| Cer(d19:1_24:1) | 4 |
| Hex1Cer(d18:0_20:4) | 4 |
| Hex2Cer(d18:2_16:0) | 4 |

### 脂质组模型：`lipid_elastic_net`

| 特征 | 出现频次（5 folds） |
|---|---:|
| PA(28:0) | 5 |
| PC(38:7e) | 5 |
| Cer(d19:1_24:1) | 4 |
| Hex1Cer(d18:0_20:4) | 4 |
| Hex2Cer(d18:2_16:0) | 4 |
| PC(26:3e) | 4 |
| PC(32:1_22:4) | 4 |
| FA(20:4) | 3 |
| FA(22:5) | 3 |
| Hex2Cer(d34:2) | 3 |

### 扩展融合模型：`fusion_full_elastic_net`

| 特征 | 出现频次（5 folds） |
|---|---:|
| PA(28:0) | 5 |
| PC(38:7e) | 5 |
| whole_blood_LYMPH_count | 5 |
| AV_sub | 4 |
| Cer(d19:1_24:1) | 4 |
| HAD | 4 |
| HARI | 4 |
| HRI | 4 |
| Hex1Cer(d18:0_20:4) | 4 |
| Hex2Cer(d18:2_16:0) | 4 |

### 扩展临床模型：`clinical_full_elastic_net`

| 特征 | 出现频次（5 folds） |
|---|---:|
| whole_blood_LYMPH_count | 5 |
| AV_sub | 4 |
| HAD | 4 |
| HARI | 4 |
| HRI | 4 |
| Inbody_122_BFM._of_Left_Leg | 4 |
| Inbody_207_Growth_Score | 4 |
| SFT | 4 |
| SWE | 4 |
| FENO_CV. | 3 |

## 六、特征数压缩后的诊断结论

| 配置 | 实验 | mean AUC | mean train AUC | mean gap | 平均入模特征数 |
|---|---|---:|---:|---:|---:|
| baseline_30_30_corr095 | clinical_full_elastic_net | 0.5011 | 0.7437 | 0.2426 | 22.8 |
| compact_15_10_corr090 | fusion_elastic_net | 0.5376 | 0.7621 | 0.2245 | 19.2 |
| baseline_30_30_corr095 | fusion_elastic_net | 0.5364 | 0.8055 | 0.2691 | 34.4 |
| baseline_30_30_corr095 | fusion_full_elastic_net | 0.5258 | 0.8496 | 0.3239 | 52.2 |
| ultra_sparse_5_5_corr080 | lipid_elastic_net | 0.5396 | 0.6949 | 0.1553 | 4.6 |
| baseline_30_30_corr095 | lipid_elastic_net | 0.5338 | 0.7895 | 0.2556 | 29.4 |

### 诊断解释

- 当脂质组模型从约 29 个特征压缩到约 5 个特征后，验证 AUC 从 **0.5338** 小幅升到 **0.5396**，同时过拟合差值明显变小。
- 当融合模型从约 34 个特征压缩到约 19 个特征后，验证 AUC 基本不变（**0.5364 → 0.5376**），说明问题不只是“特征太多”。
- 当前更像是：**信号强度不足** 或 **标签/队列定义仍需进一步审计**。

## 七、当前阶段的研究判断

1. **不能把某一折偶然跑高视为成功。** 目前真正重要的是平均 AUC 与 fold 间稳定性。
2. **扩展临床变量没有自然带来提升。** 这通常意味着额外变量质量一般，或者高缺失/高噪声压过了有效信号。
3. **脂质组变量里确实有少量稳定特征。** 例如 `PC(38:7e)`、`PC(32:1_22:4)`、`Hex1Cer(d18:0_20:4)` 等，在多个配置中反复出现。
4. **下一步更应做审计而非堆模型。** 否则很可能只会继续抬高训练 AUC。

## 八、建议的下一步

### 建议 1：标签与结局口径审计
- 核对 `response / noresponse` 的定义是否完全一致
- 检查是否有随访窗口不一致、人工整理误差或标签漂移

### 建议 2：队列与变量 QC
- 逐列检查缺失率、异常值、单位混杂、批次差异
- 对 top lipids 和关键临床变量做单变量可视化

### 建议 3：任务重构
- 评估是否需要改终点、分层建模或引入更稳定的临床亚组
- 若继续建模，建议以 **5–15 个特征的小模型** 为主

可直接发送：

> 目前我们已经用严格 nested CV 跑完了第一轮临床、脂质组和融合模型。结果显示最佳 mean AUC 约 0.54，距离 0.80 仍有明显差距；扩展变量虽然提高了训练集拟合，但没有改善验证集表现，提示过拟合较明显。下一步更建议先做标签定义、队列质量和变量质量审计，而不是继续盲目增加模型复杂度。

## 九、已生成的支撑文件

- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/feature_frequency.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/roc_curve_points.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/run_stage_experiments_result.json`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/diagnostic_topk_sweep.csv`
- `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/20260310_nested_cv_summary.md`
