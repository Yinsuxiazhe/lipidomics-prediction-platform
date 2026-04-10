# 固定校区组合版 split 方案设计

## 候选方案总览

| scheme | train_schools | test_schools | train_n | test_n | train_response_rate | test_response_rate | abs_response_rate_gap | train_intensity_count | test_intensity_count | recommended |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_5train_2test_balanced_rate | 中关村、冷泉、唐家岭校区、本部、百旺 | 六里屯、华清校区 | 195 | 86 | 0.5744 | 0.5930 | 0.0187 | 3 | 2 | sensitivity |
| B_4train_3test_all_intensity | 六里屯、冷泉、本部、百旺 | 中关村、华清校区、唐家岭校区 | 161 | 120 | 0.5590 | 0.6083 | 0.0493 | 3 | 3 | selected |

## 选择结论

- 方案 A（5 train + 2 test）更接近“response rate 最平衡”的备选方案。
- 方案 B（4 train + 3 test）虽然 train/test response rate gap 略大，但 **train/test 两侧都覆盖 3 种 intensity**，test 样本量也更大，更像真正的多校区固定 hold-out。
- 因此本轮实施选择 **方案 B：中关村 + 华清校区 + 唐家岭校区 作为固定 test；六里屯 + 冷泉 + 本部 + 百旺 作为 train**。

## 为什么没有优先选“按 intensity 组 train/test”

- intensity 只有 3 组，组数太少，且它本身更像 protocol / exposure 维度，而不是独立来源校区维度。
- 如果直接按 intensity 分 train/test，解释会混入干预强度差异，不适合作为当前“跨校区泛化”问题的第一优先固定 split。

## 新增进展（2026-03-12）

- 方案 A（5 train + 2 test）现已按 sensitivity analysis 补跑，主要用于检验“更平衡的 response rate 切法”是否改变结论。
