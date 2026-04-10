# responder external formal handoff package

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan
- 交付定位：面向外部协作方 / 公司端 / 顾问端的正式交接包；保留本轮 follow-up 的解释层，但统一改为中性、正式、可转发口吻。

## 建议阅读顺序

1. 先打开 `index.html`：这是总交接页，按“正式主结果 → school split follow-up → out-phase temporal validation → protocol / 写作边界”组织。
2. 如需单看 follow-up 解释层，打开 `01_followup_formal_report.html`。
3. 如需单看 school / community split 与 protocol 写法，打开 `03_school_split_protocol_note.html`。
4. 如需单看固定校区 train/test 组合与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。

## 包内主要文件

- `index.html`
- `01_followup_formal_report.html`
- `02_combined_formal_report.html`
- `03_school_split_protocol_note.html`
- `04_fixed_school_combo_note.html`
- `strict_nested_cv_key_metrics.csv`
- `school_group_holdout_summary.csv`
- `self_validation_summary.csv`
- `outphase_validation_summary.csv`
- `fixed_school_combo_result_comparison.csv`
- `fixed_school_combo_scheme_design.csv`
- `id_school_intensity_mapping.csv`
- `assets/`

## 当前必须坚持的科学边界

- 正式主结果仍是 strict nested CV 的 outer-test AUC，约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- `repeated hold-out`、`leave-one-school-out`、固定校区组合版 split、`outphase_leave_one_school_out` 均属于补充验证证据链，不能写成 `external validation`。
- 当前 package 支持的是“边界更清楚、解释更完整、交接更稳妥”，不支持“强跨校区泛化已被证明”。

## 当前仍待补充的数据条件

- responder 定义源头核对 / alternative grouping sensitivity：仍缺原始连续终点文件。
- 心血管表型桥接：仍缺整理后的心血管表型表。

## 一句话摘要

- 这是一份可直接对外发送的正式交接包：它保留了 strict nested CV 主锚点，并把真实 school grouped split、out-phase temporal validation、fixed school combo sensitivity 与 protocol 写法边界整理成了统一、可转发的正式说明。
