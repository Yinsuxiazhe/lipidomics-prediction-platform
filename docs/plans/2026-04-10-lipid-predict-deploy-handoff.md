# 脂质组学预测网站 — 部署上线 Handoff

> 接手人：Claude Code / 其他模型
> 发起时间：2026-04-10
> 项目根目录（Mac 本地）：`/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型`

---

## 0. 2026-04-20 最新上线状态回填

> **状态说明**：本文原始主体写于 2026-04-10，下面这一节用于回填 **截至 2026-04-20 的真实上线结果**。2026-04-19 已完成 192-model multi-type / cross-gender 指标上线；2026-04-20 又补了一轮 **Gender 示例值热修复 + metadata 回写**。如果下文仍保留 64-model / 78-file 的旧部署口径，请以本节为准；旧内容保留为历史部署参考。

### 0.1 当前线上状态
- **公网地址（主）**：`https://lipid-predict.medaibox.com`
- **公网地址（备用）**：`https://xulab.medaibox.com`
- **GitHub 仓库**：`https://github.com/Yinsuxiazhe/lipidomics-prediction-platform`
- **当前线上 release**：`/var/www/lipid-predict/releases/20260420-141552`
- **当前 symlink**：`/var/www/lipid-predict/current -> /var/www/lipid-predict/releases/20260420-141552`
- **上一轮完整功能 release**：`/var/www/lipid-predict/releases/20260419-184105`
- **systemd service**：`lipid-predict.service`
- **gunicorn 监听**：`127.0.0.1:5010`

### 0.2 当前实际部署资产
- 当前 authoritative runtime bundle 为 `website/trained_models/`；
- 当前线上模型数为 **192**（8 indicators × 2 groupings × 3 model types × 4 algorithms）；
- 网站运行时优先加载 `website/trained_models/model_metadata.json` 与同目录 `.pkl`，并在该 bundle 存在时跳过 legacy `website/models/`；
- 2026-04-19 的 cross-gender 指标回填修复仍然在线：缺失值不会再被伪装成 `0.000`，真实可计算模型会返回真实 `M→F / F→M AUC`；
- 2026-04-20 新增热修复已在线：`Use Example` 不会再把 `Gender` 显示为小数。

### 0.3 2026-04-20 本轮新增修复
1. **生成端修复**：`src/multi_indicator_glm5/multi_type_assets.py` 中 `Gender` sample 不再取均值，改为离散二值众数（mode）；
2. **网站端兜底**：`website/app.py` 会把 legacy metadata / API fallback 里的 `Gender` 统一规范成 `0/1`，即使旧资产中残留小数，也不会再显示为小数；
3. **metadata 回写**：已回写以下两个文件中的 `sample_values.Gender`，均已离散化：
   - `website/trained_models/model_metadata.json`
   - `outputs/20260419_multi_type_glm5/trained_models/model_metadata.json`

### 0.4 2026-04-20 实际回归结果
- 本地 targeted tests：
  - `pytest tests/multi_indicator_glm5/test_multi_type_assets.py tests/website/test_app_display_logic.py -q` → **25 passed**
- 本地 Flask smoke：
  - `/api/sample_data/BMI_Q_fusion_RF` → `Gender=0`
  - `/api/sample_data/PBF_T_fusion_RF` → `Gender=0`
- 线上服务状态：`systemctl is-active lipid-predict.service` → **active**
- 服务器本机接口验证：`curl http://127.0.0.1:5010/api/sample_data/BMI_Q_fusion_RF` → `sample_values.Gender = 0`
- 公网接口验证：`curl https://lipid-predict.medaibox.com/api/sample_data/BMI_Q_fusion_RF` → `sample_values.Gender = 0`
- 公网页面关键文本命中：主页面已命中 `Use Example`、`Δ = outroll - enroll`、`clinical-only / lipid-only / fusion` 等最新文案。

### 0.5 本次上线解决的问题
1. **A：** “Use Example” 自动填充值里的 `Gender` 不再出现 `0.319148936...` 这类均值小数；
2. **B：** 旧 metadata 即使残留小数 `Gender`，网站 API 仍会输出离散 `0/1`；
3. **C：** 训练导出端、网站运行端、部署 metadata 三层口径已重新对齐，后续重新导出资产时也不会复发。

## 一、项目概述

这是一个基于 Flask 的多指标脂质组学预测平台，提供：

- **单样本预测**：输入脂质组数据，返回高/低响应分类
- **批量预测**：上传 CSV，批量预测并下载结果
- **模型性能展示**：各模型的 AUC、灵敏度、特异度等指标
- **名词解释**：脂质类别、临床指标、机器学习术语说明
- **中英文切换**

本文最初写于本地部署阶段；截至 2026-04-19，项目已经部署到公网并可访问，详细状态见上方 §0。

---

## 二、部署包清单（必传文件）

### 2.1 代码层（website/ 目录）

| 文件路径 | 说明 | 大小 |
|---|---|---|
| `website/app.py` | Flask 后端主程序，**需先修复硬编码路径**（见 §4） | ~41 KB |
| `website/templates/index.html` | 前端页面（已修复 JS 全角引号语法错误） | ~1400 行 |
| `website/static/` | 静态资源目录，**当前为空**，如需 logo 等资源放此 | — |
| `website/data/model_info.json` | 模型元数据，供前端展示 | ~4 KB |

### 2.2 模型文件（78 个 .pkl）

#### 旧版模型（14 个）
```
website/models/
├── BMI_q3_LR.pkl
├── BMI_q4_RF.pkl
├── PBF_q3_RF.pkl
├── PBF_q4_LR.pkl
├── PSM_q4_RF.pkl
├── WHR_q3_RF.pkl
├── WHR_q4_SVM.pkl
├── bmi_z_q3_RF.pkl
├── hipline_q3_RF.pkl
├── hipline_q4_RF.pkl
├── waistline_q3_RF.pkl
├── waistline_q4_KNN.pkl
├── weight_q3_KNN.pkl
└── weight_q4_LR.pkl
```

#### 新版模型（64 个，来自 GLM5 训练流水线）
```
outputs/20260410_multi_indicator_glm5/trained_models/
├── model_metadata.json          ← 必须同时上传
├── BMI_Q_EN_LR.pkl  ...  BMI_Q_XGBoost.pkl    (4个)
├── BMI_T_EN_LR.pkl  ...  BMI_T_XGBoost.pkl    (4个)
├── PBF_Q_EN_LR.pkl  ...  PBF_T_XGBoost.pkl    (8个)
├── PSM_Q_EN_LR.pkl  ...  PSM_T_XGBoost.pkl    (8个)
├── WHR_Q_EN_LR.pkl  ...  WHR_T_XGBoost.pkl    (8个)
├── bmi_z_Q_EN_LR.pkl ...  bmi_z_T_XGBoost.pkl (8个)
├── hipline_Q_EN_LR.pkl ... hipline_T_XGBoost.pkl (8个)
├── waistline_Q_EN_LR.pkl ... waistline_T_XGBoost.pkl (8个)
└── weight_Q_EN_LR.pkl ... weight_T_XGBoost.pkl   (8个)
```

### 2.3 训练数据（示例值 API 依赖）

| 文件路径 | 说明 | 大小 |
|---|---|---|
| `281_merge_lipids_enroll.csv` | 训练队列脂质组数据（n=281），用于计算示例均值 | ~4.8 MB |

> ⚠️ **必须上传**：如果缺少此文件，`/api/sample_data/<model_key>` 接口会返回 404，前端"使用示例"功能无法工作。

---

## 三、目录结构（部署到服务器后的目标布局）

```
/opt/lipid_predict/           ← 服务器部署根目录（可自定义）
├── app.py                    ← Flask 后端
├── templates/
│   └── index.html            ← 前端页面
├── static/                   ← 静态资源（可为空）
├── data/
│   └── model_info.json
├── models/                   ← 旧版 14 个 pkl
│   ├── BMI_q3_LR.pkl
│   └── ...
├── trained_models/           ← 新版 64 个 pkl + metadata
│   ├── model_metadata.json
│   ├── BMI_Q_EN_LR.pkl
│   └── ...
└── 281_merge_lipids_enroll.csv   ← 示例数据（放在根目录）

# app.py 中的路径会自动适配：
# - MODELS_DIR = BASE_DIR / "models"           (旧版模型)
# - BASE_DIR / "trained_models"                (新版模型，从 APP_DIR 拼接)
# - APP_DIR / "281_merge_lipids_enroll.csv"   (示例数据)
```

---

## 四、部署前必须修复：app.py 硬编码路径

`app.py` 第 21 行和第 426 行有 **Mac 本地路径**，部署到服务器后必须修复。

### 修复前（第 21 行）
```python
APP_DIR = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
```

### 修复后（推荐）
```python
APP_DIR = BASE_DIR   # 将 APP_DIR 改为与 BASE_DIR 同级，指向 app.py 所在目录
```

### 修复前（第 426 行）
```python
glm5_model_dir = APP_DIR / "outputs" / "20260410_multi_indicator_glm5" / "trained_models"
```

### 修复后
```python
glm5_model_dir = BASE_DIR / "trained_models"
```

### 简化版完整部署目录布局（推荐）

将所有模型文件统一放到 `app.py` 同级目录下，目录结构如下：

```
/opt/lipid_predict/
├── app.py
├── templates/index.html
├── static/
├── data/model_info.json
├── models/              ← 14 个旧版 pkl
├── trained_models/      ← 64 个新版 pkl + model_metadata.json
├── 281_merge_lipids_enroll.csv
└── requirements.txt
```

对应 `app.py` 的路径修复：

```python
# BASE_DIR 已正确指向 app.py 所在目录，无需修改
BASE_DIR = Path(__file__).parent   # 第 20 行，默认正确

# APP_DIR 改为指向 BASE_DIR（服务器部署根目录）
APP_DIR = BASE_DIR                # 修复第 21 行

# GLM5 模型目录改为 BASE_DIR 下的 trained_models
glm5_model_dir = BASE_DIR / "trained_models"   # 修复第 426 行
```

---

## 五、Python 环境要求

### 5.1 依赖包（requirements.txt 内容）

```txt
flask>=3.0.0
gunicorn>=21.0.0
numpy>=1.26.0
pandas>=2.0.0
scikit-learn>=1.4.0
werkzeug>=3.0.0
```

### 5.2 建议部署命令

```bash
pip install -r requirements.txt
gunicorn -w 2 -b 0.0.0.0:5000 app:app --timeout 120
```

> `gunicorn` 用于生产环境替换 Flask 内置开发服务器；`-w 2` 开启 2 个 worker，`--timeout 120` 设置 120 秒超时（模型加载和预测可能较慢）。

---

## 六、部署方案参考

### 方案 A：Docker 部署（推荐）

在部署根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /opt/lipid_predict

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app", "--timeout", "120"]
```

构建并运行：
```bash
docker build -t lipid-predict .
docker run -d -p 5000:5000 --name lipid-predict lipid-predict
```

### 方案 B：SSH 到服务器直接部署

```bash
# 1. 在服务器上创建目录
mkdir -p /opt/lipid_predict/{templates,static,data,models,trained_models}

# 2. 用 scp 上传所有文件（本地执行）
scp -r website/app.py user@your-server:/opt/lipid_predict/
scp -r website/templates/index.html user@your-server:/opt/lipid_predict/templates/
scp -r website/data/model_info.json user@your-server:/opt/lipid_predict/data/
scp -r website/models/*.pkl user@your-server:/opt/lipid_predict/models/
scp -r outputs/20260410_multi_indicator_glm5/trained_models/ user@your-server:/opt/lipid_predict/trained_models/
scp 281_merge_lipids_enroll.csv user@your-server:/opt/lipid_predict/

# 3. 在服务器上安装依赖并启动
ssh user@your-server
cd /opt/lipid_predict
pip install -r requirements.txt
gunicorn -w 2 -b 0.0.0.0:5000 app:app --timeout 120 --daemon
```

### 方案 C：极空间 NAS 部署

极空间 NAS 型号 `192.168.1.107`，SSH 端口 `10000`，管理员账号 `17851180809`。

> ⚠️ **注意**：极空间 NAS 可能是基于 Arm 架构的轻量 Linux，Python 和 pip 可能需要通过 Docker 或 Entware 安装。部署前需确认 NAS 上的 Python 环境。

---

## 七、部署后验证清单

部署完成后，请依次验证以下功能：

- [ ] `http://<服务器IP>:5000/` 页面正常加载，无 JS 报错
- [ ] 模型卡片正常显示（不出现"Loading model data..."卡死）
- [ ] Tab 切换按钮（单样本预测/批量预测/模型性能/帮助）正常工作
- [ ] 选择一个模型，点击"使用示例"能自动填充数值
- [ ] 点击"开始预测"能返回预测结果
- [ ] `/api/models` 接口返回模型列表（78 个）
- [ ] 批量上传 CSV 能返回下载结果
- [ ] 中英文切换功能正常

---

## 八、已知问题和修复记录

| 日期 | 问题 | 修复方式 |
|---|---|---|
| 2026-04-10 | JS 全角引号 `」` 导致 `<script>` 块语法错误，页面一直 loading | 全局替换 `」` → `"`，共 118 处，已修复 |
| 2026-04-10 | `app.py` 中 APP_DIR 和 glm5_model_dir 硬编码 Mac 本地路径 | 见 §4 路径修复说明 |

---

## 九、联系人与背景信息

- **需求方**：Shuxian Zhang
- **分析提供方**：Chenyu Fan
- **模型说明**：本系统用于儿童运动干预脂质组学 responder/non-responder 预测，基于 EXCITING 研究队列（n=281）数据训练
- **当前正式主结果**：strict nested CV outer-test mean AUC ≈ 0.50–0.54（正式泛化性能），训练均值 AUC 约 0.8（训练折内表现，非泛化性能）
