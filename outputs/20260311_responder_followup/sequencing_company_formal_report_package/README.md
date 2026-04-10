# responder sequencing company formal report package

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan

- 建议先打开 `index.html` 或 `00_cover_note.html`：这是面向对外发送的 **1 分钟封面说明页**，用于先统一“正式主结果 / AUC≈0.8 来源 / 当前结论边界”三项口径。
- 再打开 `01_formal_report.html`：这是完整正式报告页，包含 8 张主图与对应解读。
- `assets/` 目录包含 8 张图对应的 PNG 与 PDF 文件，可用于单独引用、归档或插入正式材料。
- 本包聚焦当前已交付数据支持的正式主结果、strict nested CV 训练/测试口径补充、补充稳健性证据、post-intervention 时相验证与 response label audit。
- `strict_nested_cv_key_metrics.csv` 已纳入本包，用于直接解释 strict nested CV 中为什么会看到 `AUC≈0.8` 的数值。
- 术语边界说明：`repeated hold-out`、`leave-one-prefix-out` 与 `post-intervention within-dataset temporal validation` 均属于补充验证路线，不属于 external validation。
- strict nested CV 口径说明：`AUC≈0.8` 对应的是 `mean_train_auc`；正式性能声明仍以 `outer-test mean AUC` 为准。
