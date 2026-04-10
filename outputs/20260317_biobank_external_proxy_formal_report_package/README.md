# 三个 biobanks external-proxy 可行性正式报告包

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan

## 建议阅读顺序

1. 先打开 `index.html`：这是本包总览页，用于快速理解结构、主要结论与当前边界。
2. 再看 `01_biobank_external_proxy_formal_report.html`：这是本次结果的主报告页。
3. 如需查看补充说明、结果比对与后续建议，再看 `02_supplementary_note.html`。
4. 如需复核表格，查看根目录下 CSV 文件。
5. 如需查看代码与数据说明，查看 `analysis_code/` 与 `analysis_data/`。

## 包内主要页面

- `index.html`
- `01_biobank_external_proxy_formal_report.html`
- `02_supplementary_note.html`

## 代码与数据

- `analysis_code/`：本次正式报告包直接对应的主要分析代码副本与说明。
- `analysis_data/`：本次正式报告包直接对应的数据说明、衍生表格及输入来源清单。

## 当前必须坚持的结论边界

- 正式主结果仍是：strict nested CV outer-test performance，当前 mean AUC 约 0.50–0.54。
- 补充分析用于说明：external-proxy / transportability feasibility，不改变正式主结果锚点。
- 以下内容不能升级表述为：strict external validation、当前 responder 模型已完成外部验证。
- 本包支持的是：三个 biobanks 作为第二阶段 proxy 候选资源的可行性说明。
- 本包不支持的是：将当前 species-level lipidomics responder 模型直接等同迁移到外部成人 biobank。

## 主要清单

- `overlap_feature_mapping.csv`
- `reduced_external_proxy_model_feature_set.csv`
- `strict_nested_cv_performance_summary.csv`
- `analysis_code/`
- `analysis_data/`
