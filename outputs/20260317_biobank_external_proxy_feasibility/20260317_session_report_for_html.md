# 本次会话报告：三个 biobanks external-proxy 可行性、数据申请现实性与 HTML 交付

> 生成日期：2026-03-17  
> 工作目录：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型`  
> 本页定位：**本次会话汇总 / 修改对比清单 / 运算结果比对 / 可转发 HTML 交付源文件**

## 1. 执行摘要

本次会话围绕 Nature Communications 论文《Metabolomic and genomic prediction of common diseases in 700,217 participants in three national biobanks》及当前儿童运动干预 responder 项目，完成了三个层面的判断：

1. **科学定位**：UK Biobank、Estonian Biobank、THL Biobank 可以作为第二阶段 **external-proxy / transportability** 候选，但**不能直接称为当前 responder 模型的严格 external validation**。
2. **特征可迁移性**：论文 36 个 Nightingale NMR biomarkers 与本地 species-level lipidomics 的**直接同名 overlap = 0**；但在本地临床化学字段中可以整理出 **8 个 exact-like overlap + 1 个 partial proxy**，足以形成 reduced external-proxy model 草案。
3. **现实获取路径**：三个 biobanks 原则上都能申请，但都是**受控访问**，不是直接索要原始个体级数据；三者中 **UK Biobank 最现实，Estonian Biobank 次之，THL/Finnish route 更偏合作/网关式推进**。

## 2. 本次会话完成事项

| 模块 | 已完成内容 | 输出状态 |
| --- | --- | --- |
| 论文与 supplementary 审查 | 确认三库名称、研究设计、36 biomarker 子集、跨 biobank 复制逻辑 | 已完成 |
| 本地数据可接入性审查 | 检查 `281_merge_lipids_enroll.csv`、`281_new_grouped.csv`、`287_enroll_data_clean.csv`、`287_outroll_data_clean.csv` | 已完成 |
| overlap-feature 映射 | 形成 36 biomarker 对本地临床字段映射表 | 已完成 |
| reduced external-proxy draft | 形成 `transport_core_8` 与 `transport_extended_12` 特征草案 | 已完成 |
| 结果口径校正 | 明确正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54；AUC≈0.8 仅对应 mean_train_auc | 已完成 |
| 外部数据现实性判断 | 梳理 UKB / EBB / THL 受控访问现状与优先级 | 已完成 |
| HTML 交付 | 新建本页 Markdown，并渲染为带目录 HTML | 本次完成 |

## 3. 必须继续守住的科学边界

### 3.1 当前正式主结果边界

- 正式主结果仍然是 **strict nested CV outer-test performance**。
- 目前项目中最稳妥的主口径是：**outer-test mean AUC 约 0.50–0.54**。
- 用户印象中的 **AUC≈0.8**，对应的是训练侧 `mean_train_auc`，**不是 outer-test AUC，更不是 external validation AUC**。

### 3.2 不能误写成 external validation 的内容

以下内容都**不能**写成严格外部验证：

- repeated hold-out
- leave-one-school-out / leave-one-prefix-out
- baseline -> out-phase within-dataset temporal validation
- 当前仅基于 overlap clinical chemistry 的 reduced feasibility 分析

### 3.3 为什么这三个 biobanks 暂时只能叫 external-proxy

| 维度 | 当前项目 | Nature 三 biobanks 论文 | 风险 |
| --- | --- | --- | --- |
| 人群 | 儿童运动干预 | 北欧成人一般人群 | 高 |
| 终点 | responder / non-responder | 慢病发病风险 | 高 |
| 平台 | species-level lipidomics | Nightingale NMR 标准化 biomarkers | 高 |
| 标签来源 | 当前 responder 标签仍需维持谨慎口径 | 随访/EHR 终点 | 高 |

## 4. overlap-feature 对照总结

### 4.1 映射结果

- paper `Age + sex + metabolomics` 模型：**36 个 biomarker**
- 与本地 `281_merge_lipids_enroll.csv` 的 species-level lipidomics **直接同名 overlap = 0**
- 但在本地常规临床化学中可整理出：
  - **8 个 exact-like overlap**
  - **1 个 partial proxy**：`Glucose_Lactate -> serum_Glu`
  - **3 个 transport covariates**：`age`、`sex`、`BMI`

### 4.2 核心映射表

| paper feature | 本地 baseline 字段 | 本地 out-phase 字段 | 类型 |
| --- | --- | --- | --- |
| Albumin | `serum_ALB` | `serum_ALB` | exact-like |
| ApoA1 | `serum_ApoA1` | `serum_ApoA1` | exact-like |
| ApoB | `serum_ApoB` | `serum_ApoB` | exact-like |
| Clinical_LDL_C | `serum_LDL.C` | `serum_LDL.C` | exact-like |
| Creatinine | `serum_Cr` | `serum_Cr` | exact-like |
| HDL_C | `serum_HDL.C` | `serum_HDL.C` | exact-like |
| Total_C | `serum_T.CHO` | `serum_T.CHO` | exact-like |
| Total_TG | `serum_TG` | `serum_TG` | exact-like |
| Glucose_Lactate | `serum_Glu` | `serum_Glu` | partial proxy |
| age | `age_enroll` | `age` | covariate |
| sex_male | `Gender` | `Gender` | covariate |
| body_mass_index | `BMI` | `BMI` | covariate |

## 5. reduced external-proxy model 草案

### 5.1 Model A：transport_core_8

- `age_enroll`
- `Gender`
- `BMI`
- `serum_TG`
- `serum_HDL.C`
- `serum_LDL.C`
- `serum_ApoA1`
- `serum_ApoB`

### 5.2 Model B：transport_extended_12

在 core_8 基础上增加：

- `serum_ALB`
- `serum_Cr`
- `serum_Glu`
- `serum_T.CHO`

### 5.3 当前完整性检查

| feature set | baseline labeled complete cases | out-phase complete cases |
| --- | ---: | ---: |
| transport_core_8 | 281 | 287 |
| transport_extended_12 | 281 | 287 |

> 解释：这说明 reduced external-proxy 路线目前**不是被缺失值卡住**，真正的限制主要是外部语义一致性，而不是本地字段完整性。

## 6. 运算结果比对

### 6.1 现有正式主结果比对

> 说明：以下是当前项目已存在的 strict nested CV 正式主结果；**本次会话没有新增模型重跑**，因此 reduced proxy 模型仍处于设计稿阶段。

| experiment | mean_auc | std_auc | mean_train_auc | 当前解读 |
| --- | ---: | ---: | ---: | --- |
| clinical_slim_logistic | 0.5297 | 0.0640 | 0.6064 | 正式 outer-test 表现偏弱但稳定 |
| lipid_elastic_net | 0.5338 | 0.0701 | 0.7895 | 训练侧较高，outer-test 未同步提升 |
| clinical_full_elastic_net | 0.5011 | 0.0742 | 0.7437 | 接近随机 |
| fusion_elastic_net | 0.5364 | 0.0535 | 0.8055 | 当前正式主结果中相对最好，但仍非高 AUC 模型 |
| fusion_full_elastic_net | 0.5258 | 0.0450 | 0.8496 | 训练侧更高，outer-test 仍有限 |

### 6.2 新路线与旧结果的关系对照

| 路线 | 是否已有正式运算结果 | 当前价值 | 是否可称 strict external validation |
| --- | --- | --- | --- |
| strict nested CV 主结果 | 是 | 项目正式主锚点 | 否（这是内部正式验证，不是外部） |
| repeated hold-out / leave-one-school-out | 是 | 稳健性补充证据 | 否 |
| baseline -> out-phase | 是 | 内部时相一致性 | 否 |
| transport_core_8 / extended_12 | 否（草案） | 外部 proxy / transportability 入口 | 否 |
| UKB / EBB / THL external-proxy | 否（待合作或申请） | 第二阶段候选 | 仅可谨慎写 proxy / transportability |

## 7. “数据能不能要到”现实性判断

### 7.1 现实结论

一句话版本：**可以申请，但不是短期、不是默认批准，也不是直接把个体级原始数据发给我们。**

### 7.2 三个 biobank 的现实优先级

| biobank | 官方路径 | 现实难度 | 当前判断 | 对本项目更像什么 |
| --- | --- | ---: | --- | --- |
| UK Biobank | 正式注册 + 申请 + 付费 + MTA + UKB-RAP 受控访问 | 中 | 三者中最现实 | external-proxy / transportability |
| Estonian Biobank | preliminary inquiry + SAC + EBIN + SAPU 安全环境 | 中偏高 | 可行，但流程更重 | cross-population proxy |
| THL / Finnish route | FINBB / Fingenious 网关 + partner biobank 路线 | 中偏高 | 原则可行，更偏合作型 | targeted proxy / future collaboration |

### 7.3 截至 2026-03-17 的官方信息摘录后判断

- **UK Biobank** 官方写明，全球符合条件的 academic / charity / government / commercial researchers 都可为公共利益健康研究申请访问；研究组织在批准后还需签 **Material Transfer Agreement**，且 UKB 自 **2024 年起默认通过 UKB-RAP 云平台提供访问**。注册审核页面写明：**registration review 为 10 working days**。这只是注册审核时长，不等于项目最终拿到数据的总时长；总周期更可能是**数周到数月**。这句“数周到数月”是我基于官方流程长度做的推断。
- **Estonian Biobank** 官方当前页面明确列出：先发 **preliminary inquiry**，随后走 **Scientific Advisory Committee (SAC)**，再到 **Estonian Committee on Bioethics and Human Research (EBIN)**，数据访问通过 **SAPU secure data analysis environment**。若研究者位于 **EU/EEA 之外**，协议还会加入向第三国传输数据的标准条款。
- **THL / Finnish route**：Nature 论文写的是可通过 THL Biobank research application 申请；当前更稳定的官方网关是 **FINBB / Fingenious**。官方页面显示 **THL Biobank** 是 partner/member biobank 之一，并明确提供样本、数据与相关研究服务信息。实际推进上更像通过官方网关/合作来做 feasibility，而非直接个人索取。

### 7.4 对我们项目最实用的建议

1. **先问作者/团队能否提供最小可复现资源**：变量定义、代码说明、系数、或代跑 reduced model。
2. **如果真走正式申请，优先 UKB**。
3. 申请目标要写成：
   - reduced overlap-feature model
   - transportability assessment
   - external-proxy validation
   而不是“直接验证儿童运动干预 responder 分类器”。

## 8. 修改对比清单 / 新增产物

### 8.1 本次会话已存在并确认的产物

| 文件 | 作用 |
| --- | --- |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_biobank_external_proxy_feasibility_report.md` | 主可行性报告 Markdown |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_biobank_external_proxy_feasibility_report.html` | 主可行性报告 HTML |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/overlap_feature_mapping.csv` | overlap 对照表 |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/reduced_external_proxy_model_feature_set.csv` | reduced model 特征表 |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/direct_message_to_huanglaoshi_chenyu.txt` | 给黄老师/晨宇的直发文案 |

### 8.2 本次新补的 HTML 交付源

| 文件 | 作用 |
| --- | --- |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_session_report_for_html.md` | 本页 Markdown 源文件 |
| `/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型/outputs/20260317_biobank_external_proxy_feasibility/20260317_session_report_for_html.html` | 本页 HTML 结果页 |

## 9. 可直接发送内容

**可直接发送：**

> 黄老师/晨宇您好，我这边把 Nature 那篇三 biobanks 文章对应的外部验证可行性先梳理了一版。当前判断是：UK Biobank、Estonian Biobank、THL Biobank 可以作为第二阶段的 external-proxy / transportability 候选，但还不能直接写成我们当前儿童运动干预 responder 模型的严格 external validation。主要原因是人群、终点、检测平台都不一致；不过我已经把 overlap-feature 对照表和 reduced external-proxy model 草案整理出来了，也补了一版“数据能否申请到”的现实判断。更建议的下一步是先在本地把 reduced overlap model 单独跑出来，再决定是否优先推进 UKB 申请或作者合作代跑。

## 10. 参考来源

1. [Nature Communications 原文：Metabolomic and genomic prediction of common diseases in 700,217 participants in three national biobanks](https://www.nature.com/articles/s41467-024-54357-0)
2. [UK Biobank：Apply for access](https://www.ukbiobank.ac.uk/use-our-data/apply-for-access/)
3. [UK Biobank：Access to UK Biobank data](https://www.ukbiobank.ac.uk/about-us/how-we-work/access-to-uk-biobank-data/)
4. [UK Biobank：Eligibility](https://www.ukbiobank.ac.uk/use-our-data/eligibility/)
5. [UK Biobank Community：How long will it take for my registration to be reviewed?](https://community.ukbiobank.ac.uk/hc/en-gb/articles/15453266783773-How-long-will-it-take-for-my-registration-to-be-reviewed)
6. [Estonian Biobank 官方页面](https://genomics.ut.ee/en/content/estonian-biobank)
7. [FINBB 官方页面](https://finbb.fi/en/)
8. [Fingenious partner biobanks 页面（含 THL Biobank）](https://site.fingenious.fi/en/all-partner-biobanks/)

## 11. 备注

- 本页没有重跑 `outputs/20260310_nested_cv` 中的正式主结果，避免覆盖项目主锚点。
- 本页中的“数据获取周期”判断，除了官方直接给出的注册/流程文字外，其余周期表述属于**基于官方流程长度的现实推断**。
- 如果下一步要继续，本项目最值得落地的动作是：**直接运行 `transport_core_8` / `transport_extended_12` 的本地 strict nested CV 与 follow-up 比较**。
