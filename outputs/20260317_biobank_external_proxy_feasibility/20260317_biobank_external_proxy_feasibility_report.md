# 三个 biobanks 外部验证可行性评估与 overlap-feature 草案

> 生成日期：2026-03-17  
> 适用对象：黄老师 / 晨宇  
> 结论定位：**external-proxy / transportability feasibility**，不是严格 external validation 结论

## 1. 本次一句话结论

基于当前儿童运动干预 responder 项目与 Nature Communications 这篇三 biobanks 论文的对照，**UK Biobank、Estonian Biobank、THL Biobank 可以作为第二阶段的 reduced external-proxy / transportability 候选资源，但暂时不能直接写成当前 responder 模型的严格 external validation**。

当前更合理的路线是：

1. 先在本地用 overlap clinical-chemistry features 建一个 **reduced external-proxy model**；
2. 再决定是否推进 UKB/EBB/THL 的受控访问或合作；
3. 对外表述上坚持“proxy validation / transportability / targeted replication feasibility”，不要提前写成 strict external validation。

## 2. 可直接发送版本

微信超短版

> 黄老师/晨宇您好，我把这篇 Nature 文章里提到的三个 biobanks 快速对了一下。我的判断是，这三个库可以作为第二阶段的 external-proxy / transportability 候选，但暂时不能直接写成我们当前儿童运动干预 responder 模型的严格 external validation。主要问题是人群、终点和检测平台都不一致；不过我已经整理出一版 overlap-feature reduced model 草案，下一步可以先在我们本地把这条 reduced 路线单独跑出来，再决定是否推进 UKB 或其他外部资源。

可直接发送

> 黄老师/晨宇您好，
> 
> 我基于 Nature Communications 文章《Metabolomic and genomic prediction of common diseases in 700,217 participants in three national biobanks》（2024-11-21）以及我们当前 responder 项目的本地数据结构，初步做了一版“三个 biobanks 是否可用于外部验证”的可行性审查。
> 
> 当前结论是：**这三个 biobanks（UK Biobank、Estonian Biobank、THL Biobank）可以作为第二阶段的 external-proxy / transportability 候选资源，但暂时不宜直接表述为我们当前儿童运动干预 responder 模型的严格 external validation。**
> 
> 主要边界如下：
> 1. **人群边界**：我们的队列是儿童运动干预，而三个 biobanks 基本是北欧成人一般人群；
> 2. **终点边界**：对方主要是慢病发病风险，不是运动干预 responder / non-responder；
> 3. **平台边界**：论文使用 Nightingale NMR 标准化 36 项代谢指标，而我们当前主结果主要来自 species-level lipidomics，不能直接一一映射；
> 4. **标签边界**：我们当前 responder 标签仍需维持“会议纪要级证据链，而非原始真值表”的谨慎口径。
> 
> 但从 overlap-feature 角度看，这三个库并非完全不能用。我这边已整理出一版 reduced external-proxy model 草案：在 paper 的 36 个 metabolomic biomarkers 中，可从我们现有常规临床中稳定映射出 9 个 overlap biomarkers，再联合 age、sex、BMI 组成可迁移的小模型候选。这样的路线更适合回答“是否存在可外推的广义心代谢信号”，而不是直接宣称“当前 responder 分类器已获外部验证”。
> 
> 如果您认可，我建议下一步先做两件事：
> - **第一步**：在我们本地先把 overlap-feature reduced model 单独跑出来，形成内部 strict nested CV / hold-out 结果；
> - **第二步**：再决定是优先推进 UK Biobank 的 external-proxy feasibility，还是继续找更贴近儿童运动干预场景的 targeted external cohort。
> 

## 3. 为什么现在不能直接叫“严格 external validation”

### 3.1 人群不匹配

- 我们当前本地队列是**儿童运动干预** responder / non-responder 预测。
- 论文里的三个 biobanks 是**北欧成人一般人群**：
  - UK Biobank：38–71 岁；
  - Estonian Biobank：成人一般人群；
  - THL Biobank：25–98 岁。

这会带来明显的 external validity / transportability 风险，不能把成人一般人群的风险建模，直接等同为儿童干预 responder 标签验证。

### 3.2 终点不匹配

- 当前项目终点：**运动干预后的 responder / non-responder**。
- 论文终点：**慢病发生风险 / disease onset**，基于随访与 EHR。

因此，即使能访问这三个库，也没有与我们完全同义的 responder 标签；更现实的是做 **proxy endpoint**、**broad cardiometabolic transportability** 或 **targeted replication feasibility**。

### 3.3 平台不匹配

- 论文主分析用的是 **Nightingale NMR** 的 **36 个标准化 metabolomic biomarkers**，强调跨队列可直接转移的绝对浓度单位。
- 我们当前正式主结果主要来自 **species-level lipidomics**，稳定特征如 `PA(28:0)`、`PC(38:7e)`、`Cer(d19:1_24:1)`、`Hex1Cer(d18:0_20:4)` 等，**不能直接一一映射到 paper 的 36 项 NMR biomarker**。

### 3.4 标签边界也要继续守住

根据本地分组审计文件，当前 responder 标签仍需坚持：

- `281_new_grouped.csv` 提供的是当前二分类结果；
- 分组依据目前只能回溯到**会议纪要级证据**；
- 还**不是原始真值表**。

所以在标签源头尚未完全封口之前，不宜过早对外宣称已经进入“外部验证完成”阶段。

## 4. 三个 biobanks 的现实定位

| biobank | 是否适合直接做 strict external validation | 当前更合理定位 | 备注 |
| --- | --- | --- | --- |
| UK Biobank | 否 | external-proxy / transportability 候选 | 数据生态最成熟，repeat-visit 子样本丰富，最值得先做 feasibility |
| Estonian Biobank | 否 | broad replication / cross-population comparison | 适合看广义代谢风险模式，不适合直接 responder 标签验证 |
| THL Biobank | 否 | broad replication / targeted panel feasibility | 人群与平台优势存在，但与儿童运动干预终点仍不对题 |

## 5. overlap-feature 审查结果

### 5.1 定量结论

- 论文纯 `Age + sex + metabolomics` 模型涉及 **36** 个标准化 metabolomic biomarkers。
- 这 36 个 biomarker 与我们本地 `281_merge_lipids_enroll.csv` 的 **species-level lipidomics 同名直接 overlap = 0**。
- 但在本地常规临床化学中，可以稳定映射出：
  - **8 个 exact-like overlap biomarkers**；
  - **1 个 partial proxy biomarker**（`Glucose_Lactate -> serum_Glu`，缺 lactate）；
- 再加上 `age`、`sex`、`BMI` 这 3 个基础 covariates，可以组成一条现实可执行的 reduced external-proxy 路线。

### 5.2 候选 overlap-feature 对照表

| paper_feature | paper36 | baseline_field | outphase_field | mapping_type | notes |
| --- | --- | --- | --- | --- | --- |
| Albumin | yes | serum_ALB | serum_ALB | exact_like | 血清白蛋白，语义基本一致 |
| ApoA1 | yes | serum_ApoA1 | serum_ApoA1 | exact_like | 载脂蛋白A1，可直接作为 overlap 候选 |
| ApoB | yes | serum_ApoB | serum_ApoB | exact_like | 载脂蛋白B，可直接作为 overlap 候选 |
| Clinical_LDL_C | yes | serum_LDL.C | serum_LDL.C | exact_like | 临床 LDL-C，命名不同但含义一致 |
| Creatinine | yes | serum_Cr | serum_Cr | exact_like | 肌酐，临床化学指标 |
| Glucose_Lactate | yes | serum_Glu | serum_Glu | partial_proxy | 本地只有葡萄糖，无 lactate 组合项 |
| HDL_C | yes | serum_HDL.C | serum_HDL.C | exact_like | 临床 HDL-C，可直接映射 |
| Total_C | yes | serum_T.CHO | serum_T.CHO | exact_like | 总胆固醇，命名格式不同 |
| Total_TG | yes | serum_TG | serum_TG | exact_like | 总甘油三酯，命名格式不同 |
| age | no | age_enroll | age | core_covariate | 外部 proxy 模型基础协变量；本地基线/出组字段名不同 |
| sex_male | no | Gender | Gender | core_covariate | 需统一编码方向（建议 male=1） |
| body_mass_index | no | BMI | BMI | core_covariate | 用于 reduced proxy 模型，不计入 paper 的 36 个 metabolomic biomarkers |

完整 CSV：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/overlap_feature_mapping.csv`

### 5.3 本地可用样本完整性

| feature set | baseline labeled complete cases | out-phase complete cases | 备注 |
| --- | ---: | ---: | --- |
| transport_core_8 | 281 | 287 | 基线 281 例带标签样本全部可用 |
| transport_extended_12 | 281 | 287 | 当前常规临床字段完整性足够，不是主要阻塞 |

## 6. reduced external-proxy model 草案

### 6.1 目标重新定义

这条 reduced 路线不是为了证明：

- “当前 responder 分类器已经完成 strict external validation”。

而是为了回答更现实的问题：

1. **我们在儿童运动干预里看到的广义心代谢信号，是否具有跨人群可迁移性？**
2. **在只保留 overlap clinical/metabolic features 后，是否还能保留一定区分信息？**
3. **是否值得继续申请或合作获取 UKB / EBB / THL 数据做二阶段 external-proxy 验证？**

### 6.2 推荐特征集

| model_variant | order | local_feature | role | strict_overlap_or_proxy | note |
| --- | --- | --- | --- | --- | --- |
| transport_core_8 | 1 | age_enroll | baseline demographic anchor | Yes | Use age in out-phase / external |
| transport_core_8 | 2 | Gender | baseline demographic anchor | Yes | Recode male=1 consistently |
| transport_core_8 | 3 | BMI | body size anchor | Yes | Shared across local/external settings |
| transport_core_8 | 4 | serum_TG | core lipid chemistry | Yes | Mapped to paper Total_TG |
| transport_core_8 | 5 | serum_HDL.C | core lipid chemistry | Yes | Mapped to paper HDL_C |
| transport_core_8 | 6 | serum_LDL.C | core lipid chemistry | Yes | Mapped to paper Clinical_LDL_C |
| transport_core_8 | 7 | serum_ApoA1 | apolipoprotein | Yes | Mapped to paper ApoA1 |
| transport_core_8 | 8 | serum_ApoB | apolipoprotein | Yes | Mapped to paper ApoB |
| transport_extended_12 | 1 | age_enroll | baseline demographic anchor | Yes | Use age in out-phase / external |
| transport_extended_12 | 2 | Gender | baseline demographic anchor | Yes | Recode male=1 consistently |
| transport_extended_12 | 3 | BMI | body size anchor | Yes | Shared across local/external settings |
| transport_extended_12 | 4 | serum_TG | core lipid chemistry | Yes | Mapped to paper Total_TG |
| transport_extended_12 | 5 | serum_HDL.C | core lipid chemistry | Yes | Mapped to paper HDL_C |
| transport_extended_12 | 6 | serum_LDL.C | core lipid chemistry | Yes | Mapped to paper Clinical_LDL_C |
| transport_extended_12 | 7 | serum_ApoA1 | apolipoprotein | Yes | Mapped to paper ApoA1 |
| transport_extended_12 | 8 | serum_ApoB | apolipoprotein | Yes | Mapped to paper ApoB |
| transport_extended_12 | 9 | serum_ALB | clinical chemistry | Yes | Mapped to paper Albumin |
| transport_extended_12 | 10 | serum_Cr | clinical chemistry | Yes | Mapped to paper Creatinine |
| transport_extended_12 | 11 | serum_Glu | clinical chemistry proxy | Partial | Paper variable is Glucose_Lactate; local lacks lactate |
| transport_extended_12 | 12 | serum_T.CHO | clinical chemistry | Yes | Mapped to paper Total_C |

完整 CSV：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/reduced_external_proxy_model_feature_set.csv`

### 6.3 建议模型结构

#### Model A：transport_core_8

- 输入：`age_enroll`, `Gender`, `BMI`, `serum_TG`, `serum_HDL.C`, `serum_LDL.C`, `serum_ApoA1`, `serum_ApoB`
- 推荐算法：**ridge / elastic-net logistic**
- 用途：
  - 本地先做 responder 的 reduced overlap feasibility；
  - 外部若只有基础临床化学，也能较容易迁移。

#### Model B：transport_extended_12

- 在 core_8 基础上增加：`serum_ALB`, `serum_Cr`, `serum_Glu`, `serum_T.CHO`
- 推荐算法：**elastic-net logistic**
- 备注：
  - `serum_Glu` 仅是 `Glucose_Lactate` 的 partial proxy；
  - `Total_C` 与 LDL/HDL/ApoB 可能存在共线性，建议用正则化而非普通回归。

### 6.4 推荐验证口径

#### 本地阶段（可以做）

1. 用 `transport_core_8` / `transport_extended_12` 在本地跑 **strict nested CV**；
2. 再补 **repeated hold-out** 与 **leave-one-school-out**；
3. 若需要，再看 baseline -> out-phase internal temporal validation 的方向一致性。

#### 外部阶段（只能做 proxy / transportability）

1. 不能直接要求外部也有 responder / non-responder 标签；
2. 可以评估 reduced score 与：
   - broad cardiometabolic risk；
   - obesity / dyslipidemia / diabetes related endpoint；
   - repeat-measure change pattern；
   的关系；
3. 最终表述必须写成：
   - **external-proxy validation**；
   - **transportability assessment**；
   - **targeted replication feasibility**。

### 6.5 允许说什么 / 不能说什么

| 可以说 | 不能说 |
| --- | --- |
| 三个 biobanks 可作为第二阶段 external-proxy 候选 | 三个 biobanks 已完成当前 responder 模型外部验证 |
| overlap-feature reduced model 具有跨队列迁移可行性 | 当前 species-level lipidomics 模型可直接迁移到 UKB/EBB/THL |
| 这条路线可用于评估 broad cardiometabolic transportability | UKB / EBB / THL 直接验证了儿童运动干预 responder 标签 |

## 7. 与当前项目主结果的关系边界

当前正式主结果仍然是本地 strict nested CV：

| experiment | mean_auc | std_auc | mean_train_auc |
| --- | --- | --- | --- |
| clinical_slim_logistic | 0.5297 | 0.064 | 0.6064 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 |
| fusion_full_elastic_net | 0.5258 | 0.045 | 0.8496 |

需要继续坚持的口径：

- 正式主结果是 **strict nested CV outer-test performance**；
- `AUC≈0.8` 对应的是训练侧 `mean_train_auc`，不是外部验证 AUC；
- repeated hold-out、leave-one-school-out、out-phase internal temporal validation 都不能写成 external validation。

## 8. 建议下一步

### 优先顺序（推荐）

1. **先在本地实现 reduced overlap model**（core_8 / extended_12）；
2. 形成独立的小结：
   - strict nested CV
   - repeated hold-out
   - leave-one-school-out
   - baseline -> out-phase
3. 再决定：
   - 是否推进 UK Biobank feasibility；
   - 还是继续寻找更贴近儿童运动干预场景的 targeted external cohort。

### 如果只选一个外部资源先评估

优先建议：**UK Biobank**。

原因：

- 数据生态与文档最成熟；
- 论文中已有 repeat-visit 子样本应用；
- 更适合先做 external-proxy feasibility，而不是直接宣称 strict external validation。

## 9. 本次新增产物清单

| 产物 | 作用 | 路径 |
| --- | --- | --- |
| 中文可行性说明 Markdown | 主报告 | `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_biobank_external_proxy_feasibility_report.md` |
| HTML 展示页 | 可转发汇报页 | `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_biobank_external_proxy_feasibility_report.html` |
| overlap-feature 映射表 | 36 biomarker 与本地字段对照 | `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/overlap_feature_mapping.csv` |
| reduced model 特征集 | core_8 / extended_12 草案 | `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/reduced_external_proxy_model_feature_set.csv` |
| 直接发送文本 | 给黄老师/晨宇的可复制版本 | `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/direct_message_to_huanglaoshi_chenyu.txt` |

## 10. 参考来源

- [Nature Communications 论文页面](https://www.nature.com/articles/s41467-024-54357-0)
- [Supplementary Data 1–10 XLSX](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-024-54357-0/MediaObjects/41467_2024_54357_MOESM4_ESM.xlsx)
- [UK Biobank access](https://www.ukbiobank.ac.uk/enable-your-research/apply-for-access)
- [Estonian Biobank](https://genomics.ut.ee/en/content/estonian-biobank)
- [THL Biobank](https://thl.fi/en/web/thl-biobank)
- 本地分组审计：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260311_responder_followup/group_definition_audit.md`
- 本地 strict nested CV 结果：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260310_nested_cv/performance_summary.csv`
