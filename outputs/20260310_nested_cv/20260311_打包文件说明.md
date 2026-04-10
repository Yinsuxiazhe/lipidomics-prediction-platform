# 给淑贤的 strict nested CV 说明包

## 建议阅读顺序

1. 先打开 `20260311_给淑贤_详细分析汇报与打包说明.html`
2. 再看 `01_主图与主结果/` 下的主图和主结果 CSV
3. 若要了解本次补充优化，再看 `02_补充小模型与审计/`
4. 若要核对实现位置，再看 `03_关键代码与配置/`

## 目录说明

- `00_先看这里/`：最适合直接阅读和转发的 HTML / Markdown / README
- `01_主图与主结果/`：当前论文主图与主结果数据
- `02_补充小模型与审计/`：本轮小模型压缩、标签/队列审计、补充诊断
- `03_关键代码与配置/`：实现 strict nested CV 与 Figure 6-4 的关键代码
- `04_背景说明/`：上一轮中文说明和 handoff

## 当前最核心的定位

- 论文主图与主结果：继续使用 `Figure6-4_Honest_NestedCV` 这一版 strict nested CV 结果
- 本轮小模型与标签审计：更适合放 Discussion / Limitations / Supplement
- 旧版更高分结果：只能作为 exploratory / development-stage internal validation
