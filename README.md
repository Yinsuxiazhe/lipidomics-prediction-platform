# 脂质组学运动响应预测平台

儿童运动干预脂质组学 responder / non-responder 预测模型与在线预测平台。

## 项目背景

基于 EXCITING 研究队列（n=281）儿童的基线脂质组学数据，构建多指标运动响应预测模型，涵盖：

- **临床指标**：BMI、BMI z-score、体脂率（PBF）、腰围、臀围、腰臀比（WHR）、肌肉率（PSM）、体重
- **分组方式**：四分位（Q1 vs Q4）、三分位（T1 vs T3）
- **模型算法**：弹性网络逻辑回归（EN_LR）、随机森林（RF）、XGBoost、逻辑回归（L2 正则化）

## 主要结果

| 指标 | strict nested CV outer-test AUC |
|---|---|
| BMI | ~0.52 |
| PBF | ~0.53 |
| WHR | ~0.50–0.54 |
| PSM | ~0.51 |

> 注：正式泛化性能（outer-test AUC）约为 0.50–0.54；训练折内均值 AUC 约 0.8，不属于泛化性能指标。

## 在线预测平台

部署地址：**https://lipid-predict.medaibox.com**

功能：
- 单样本脂质组预测
- 批量 CSV 上传预测
- 模型性能指标展示
- 脂质类别与临床指标中英文名词解释

## 目录结构

```
├── website/                  # Flask 预测平台
│   ├── app.py              # 后端 API
│   ├── templates/          # 前端页面
│   ├── models/             # 旧版模型（14个）
│   └── data/               # 模型元数据
├── outputs/                # 分析输出
│   ├── 20260410_multi_indicator_glm5/   # GLM5 训练流水线
│   └── 20260310_nested_cv/              # strict nested CV 结果
├── src/                    # 分析代码
│   ├── followup/           # follow-up 验证
│   └── multi_indicator_glm5/  # 多指标训练
├── docs/                   # 方案文档与报告
├── config/                 # 配置文件
└── CLAUDE.md              # 项目说明
```

## 环境依赖

```bash
pip install flask gunicorn numpy pandas scikit-learn werkzeug
```

## 本地运行

```bash
cd website
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000
```

## 部署

详见 `docs/plans/2026-04-10-lipid-predict-deploy-handoff.md`

## 联系人

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan
