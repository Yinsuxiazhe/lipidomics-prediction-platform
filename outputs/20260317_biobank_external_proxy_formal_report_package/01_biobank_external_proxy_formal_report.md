# 三个 biobanks external-proxy 可行性正式报告

> 本页用于正式结果说明。先给出当前可支持的结论，再补充 overlap-feature 草案、主结果边界与外部数据申请现实性。

## 项目角色

- 需求方：`Shuxian Zhang`
- 分析提供方：`Chenyu Fan`

## 本页摘要

- 当前定位：`external-proxy / transportability feasibility`
- 当前材料支持：`第二阶段 reduced external-proxy 路线`
- 当前材料不支持：`将三 biobanks 直接写成当前 responder 模型的严格 external validation`

## 1. 当前正式结论

基于 Nature Communications 三 biobanks 论文与本地 responder 项目数据结构的对照，当前更稳妥的判断是：

1. **UK Biobank、Estonian Biobank、THL Biobank 可以作为第二阶段 external-proxy / transportability 候选资源。**
2. **当前不宜直接表述为 responder 模型的严格 external validation。**
3. **更可执行的近期路线**，是先基于 overlap clinical chemistry 做一版 reduced external-proxy model，再决定是否推进受控访问或作者合作。

## 2. 为什么当前不能直接叫 strict external validation

| 维度 | 当前项目 | 三 biobanks 论文 | 结论 |
| --- | --- | --- | --- |
| 人群 | 儿童运动干预 | 北欧成人一般人群 | 不匹配 |
| 终点 | responder / non-responder | 慢病发病风险 | 不匹配 |
| 平台 | species-level lipidomics | Nightingale NMR 36 biomarker | 不匹配 |
| 标签来源 | 当前 responder 标签需保持谨慎口径 | 随访/EHR 终点 | 不可直接等同 |

因此，这三个库当前更适合支持 **proxy validation / transportability assessment**，而不是严格同任务外部验证。

## 3. overlap-feature 结果

### 3.1 总体结论

- paper `Age + sex + metabolomics` 模型对应 **36 个 metabolomic biomarkers**；
- 与本地 species-level lipidomics **直接同名 overlap = 0**；
- 但在本地临床化学字段中可构建：
  - **8 个 exact-like overlap biomarkers**；
  - **1 个 partial proxy biomarker**；
  - **3 个基础 transport covariates**（age、sex、BMI）。

### 3.2 可迁移小模型草案

#### Model A：`transport_core_8`

- `age_enroll`
- `Gender`
- `BMI`
- `serum_TG`
- `serum_HDL.C`
- `serum_LDL.C`
- `serum_ApoA1`
- `serum_ApoB`

#### Model B：`transport_extended_12`

在 `transport_core_8` 基础上增加：

- `serum_ALB`
- `serum_Cr`
- `serum_Glu`
- `serum_T.CHO`

### 3.3 当前完整性

| feature set | baseline labeled complete cases | out-phase complete cases |
| --- | ---: | ---: |
| transport_core_8 | 281 | 287 |
| transport_extended_12 | 281 | 287 |

这说明 reduced external-proxy 路线的主要限制不在缺失值，而在于人群、终点与平台的一致性边界。

## 4. 与当前正式主结果的关系

当前项目正式主结果仍然是 strict nested CV outer-test performance：

| experiment | mean_auc | std_auc | mean_train_auc |
| --- | ---: | ---: | ---: |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 |

需要继续坚持：

- 正式主结果仍是 **outer-test performance**；
- `AUC≈0.8` 属于训练侧指标；
- reduced external-proxy 路线属于**新一层补充分析设计**，不改变主结果锚点。

## 5. “数据能不能要到”的现实判断

### 5.1 一句话判断

**原则上可以申请，但都是受控访问，不是短期、默认批准、也不是直接索取个体级原始数据。**

### 5.2 三个资源的现实优先级

| biobank | 当前现实性 | 说明 |
| --- | --- | --- |
| UK Biobank | 最高 | 访问路径最成熟，最值得优先做 feasibility |
| Estonian Biobank | 中等 | 可申请，但流程更重、合规要求更强 |
| THL / Finnish route | 中等 | 原则可行，更偏合作或官方网关推进 |

### 5.3 更推荐的推进方式

1. 先联系作者或合作方，争取**最小可复现资源**：变量定义、模型说明、系数、或代跑 reduced model。
2. 若正式申请，优先考虑 **UK Biobank**。
3. 对申请目标的写法，优先采用：
   - `external-proxy validation`
   - `transportability assessment`
   - `targeted replication feasibility`

## 6. 可以说什么 / 不能说什么

| 可以说 | 不能说 |
| --- | --- |
| 三个 biobanks 可作为第二阶段 proxy 候选 | 三个 biobanks 已完成当前 responder 模型外部验证 |
| overlap-feature reduced model 具有迁移可行性 | species-level lipidomics 模型可直接无缝迁移 |
| 当前结果支持 transportability feasibility | 当前结果已经证明 responder 标签跨人群泛化 |

## 7. 包内配套文件

- `overlap_feature_mapping.csv`
- `reduced_external_proxy_model_feature_set.csv`
- `strict_nested_cv_performance_summary.csv`
- `analysis_code/`
- `analysis_data/`
