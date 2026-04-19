"""
多指标脂质组预测网站 — Flask 后端
运行方式: python app.py
访问地址: http://127.0.0.1:5000
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from flask import (
    Flask, render_template, request,
    jsonify, send_file, abort
)
import base64
from io import BytesIO

# ── Flask Setup ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
APP_DIR = BASE_DIR
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# ── 全局模型缓存 ────────────────────────────────────────────────────
MODELS_DIR = BASE_DIR / "models"
DATA_DIR   = BASE_DIR / "data"

_models = {}       # key → {model, features, ...}
_model_info = {}   # key → metadata dict

# ── 指标中文名 ───────────────────────────────────────────────────────
_INDICATOR_CN = {
    "BMI": "BMI", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}

_INDICATOR_META = {
    "BMI": {
        "display_en": "ΔBMI",
        "display_cn": "ΔBMI",
        "full_en": "BMI change",
        "full_cn": "BMI 变化量",
    },
    "weight": {
        "display_en": "ΔWeight",
        "display_cn": "Δ体重",
        "full_en": "Body weight change",
        "full_cn": "体重变化量",
    },
    "bmi_z": {
        "display_en": "ΔBMI z-score",
        "display_cn": "ΔBMI z-score",
        "full_en": "BMI z-score change",
        "full_cn": "BMI z-score 变化量",
    },
    "waistline": {
        "display_en": "ΔWaist Circumference",
        "display_cn": "Δ腰围",
        "full_en": "Waist circumference change",
        "full_cn": "腰围变化量",
    },
    "hipline": {
        "display_en": "ΔHip Circumference",
        "display_cn": "Δ臀围",
        "full_en": "Hip circumference change",
        "full_cn": "臀围变化量",
    },
    "WHR": {
        "display_en": "ΔWHR",
        "display_cn": "ΔWHR",
        "full_en": "Waist-to-hip ratio change",
        "full_cn": "腰臀比变化量",
    },
    "PBF": {
        "display_en": "ΔPBF",
        "display_cn": "ΔPBF",
        "full_en": "Percent body fat change",
        "full_cn": "体脂率变化量",
    },
    "PSM": {
        "display_en": "ΔPSM",
        "display_cn": "ΔPSM",
        "full_en": "Percent skeletal muscle change",
        "full_cn": "肌肉率变化量",
    },
}

_GROUP_META = {
    "Q": {
        "group_code": "Q",
        "group_display_en": "Q (Q1 vs Q4)",
        "group_display_cn": "Q（Q1 vs Q4）",
        "group_strategy_en": "Quartile extreme-grouping",
        "group_strategy_cn": "四分位极端分组",
    },
    "T": {
        "group_code": "T",
        "group_display_en": "T (T1 vs T3)",
        "group_display_cn": "T（T1 vs T3）",
        "group_strategy_en": "Tertile extreme-grouping",
        "group_strategy_cn": "三分位极端分组",
    },
}

# ── 模型全称与公式说明（供前端展示）──────────────────────────────────
MODEL_DOCS = {
    "EN_LR": {
        "name_en": "Elastic Net Logistic Regression",
        "name_cn": "弹性网络逻辑回归",
        "abbrev": "EN_LR",
        "formula_en": r"P(y=1|x) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + ... + \beta_n x_n)}}",
        "formula_cn": r"P(y=1|x) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + ... + \beta_n x_n)}}",
        "description_en": (
            "Combines L1 (Lasso) and L2 (Ridge) regularization to simultaneously perform feature selection "
            "and handle multicollinearity. The loss function is: "
            r"\min_{\beta} \left\|y - X\beta\right\|^2 + \lambda_1\|\beta\|_1 + \lambda_2\|\beta\|_2^2"
        ),
        "description_cn": "融合 L1（Lasso）和 L2（Ridge）正则化，在进行特征选择的同时处理多重共线性问题。",
        "pros_en": ["Built-in feature selection", "Handles multicollinearity", "Interpretable coefficients", "Sparse solution"],
        "pros_cn": ["内置特征选择", "处理多重共线性", "系数可解释", "稀疏解"],
        "cons_en": ["Linear decision boundary", "Sensitive to hyperparameter C and l1_ratio"],
        "cons_cn": ["线性决策边界", "对超参数 C 和 l1_ratio 敏感"],
        "type": "Linear",
        "interpretability": "High",
        "params_en": "C=0.1, l1_ratio=0.5, solver=saga",
        "params_cn": "C=0.1, l1_ratio=0.5, solver=saga",
    },
    "XGBoost": {
        "name_en": "eXtreme Gradient Boosting",
        "name_cn": "极端梯度提升",
        "abbrev": "XGBoost",
        "formula_en": r"F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x),\quad h_m = \text{ CART tree}",
        "formula_cn": r"F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x),\quad h_m = \text{ CART 树}",
        "description_en": (
            "An ensemble method that builds decision trees sequentially. Each tree corrects the errors of "
            "the previous ones. Uses gradient descent to minimize a regularized objective: "
            r"\mathcal{L}(\phi) = \sum_i l(\hat{y}_i, y_i) + \sum_k \Omega(f_k)"
        ),
        "description_cn": "集成方法，通过顺序构建决策树，每棵新树纠正前一棵树的错误。使用梯度下降最小化正则化目标函数。",
        "pros_en": ["Non-linear, captures complex interactions", "Handles missing values", "Robust to outliers", "State-of-the-art performance"],
        "pros_cn": ["非线性，可捕获复杂交互", "处理缺失值", "对离群点鲁棒", "性能领先"],
        "cons_en": ["Black box, less interpretable", "Requires careful tuning", "Prone to overfitting without regularization"],
        "cons_cn": ["黑盒，可解释性低", "需仔细调参", "无正则化易过拟合"],
        "type": "Tree Ensemble",
        "interpretability": "Low",
        "params_en": "n_estimators=200, max_depth=4, learning_rate=0.05",
        "params_cn": "n_estimators=200, max_depth=4, learning_rate=0.05",
    },
    "RF": {
        "name_en": "Random Forest",
        "name_cn": "随机森林",
        "abbrev": "RF",
        "formula_en": r"\hat{y} = \text{mode}\{h_1(x), h_2(x), ..., h_K(x)\},\quad h_k = \text{ CART tree trained on bootstrap}",
        "formula_cn": r"\hat{y} = \text{mode}\{h_1(x), h_2(x), ..., h_K(x)\},\quad h_k = \text{ 在bootstrap样本上训练的 CART 树}",
        "description_en": (
            "An ensemble of decision trees, each trained on a bootstrap sample with random feature subsets (bagging). "
            "Predictions are aggregated by majority voting. Reduces variance compared to single trees: "
            r"\text{Var}(\bar{X}) = \rho \sigma^2 + \frac{1-\rho}{n}"
        ),
        "description_cn": "由多棵决策树组成的集成，每棵树在自助采样和随机特征子集上训练（bagging），通过多数投票聚合预测。相比单棵树降低了方差。",
        "pros_en": ["Non-linear, handles complex interactions", "Built-in randomness reduces overfitting", "Handles missing values", "Feature importance scores"],
        "pros_cn": ["非线性，捕获复杂交互", "内置随机性减少过拟合", "处理缺失值", "有特征重要性评分"],
        "cons_en": ["Black box", "Can be memory-intensive for large n_estimators", "Less accurate than boosting methods"],
        "cons_cn": ["黑盒", "大 n_estimators 时内存消耗大", "精度一般低于 boosting 方法"],
        "type": "Tree Ensemble",
        "interpretability": "Medium",
        "params_en": "n_estimators=200, max_depth=10, random_state=42",
        "params_cn": "n_estimators=200, max_depth=10, random_state=42",
    },
    "LR_L2": {
        "name_en": "Logistic Regression (L2 Regularization)",
        "name_cn": "逻辑回归（L2 正则化）",
        "abbrev": "LR_L2",
        "formula_en": r"P(y=1|x) = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_j x_j)}},\quad \text{penalty} = \lambda\|\beta\|_2^2",
        "formula_cn": r"P(y=1|x) = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_j x_j)}},\quad \text{penalty} = \lambda\|\beta\|_2^2",
        "description_en": (
            "Standard logistic regression with L2 (Ridge) regularization. Shrinks coefficients toward zero "
            "to reduce overfitting while keeping all features. The objective is: "
            r"\min_{\beta} -\frac{1}{N}\sum_i [y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)] + \frac{\lambda}{2}\|\beta\|_2^2"
        ),
        "description_cn": "标准逻辑回归加上 L2（Ridge）正则化，将系数向零收缩以减少过拟合，同时保留所有特征。",
        "pros_en": ["Interpretable coefficients", "Probabilistic output", "Stable and robust", "Fast training"],
        "pros_cn": ["系数可解释", "概率输出", "稳定鲁棒", "训练速度快"],
        "cons_en": ["Linear decision boundary", "Cannot capture complex non-linear relationships"],
        "cons_cn": ["线性决策边界", "无法捕获复杂非线性关系"],
        "type": "Linear",
        "interpretability": "High",
        "params_en": "C=1.0, penalty=l2, solver=lbfgs",
        "params_cn": "C=1.0, penalty=l2, solver=lbfgs",
    },
}

# ── 缩写全称说明（供前端名词解释页）──────────────────────────────────
ABBREV_GLOSSARY = {
    # ── 临床指标 ──
    "BMI": {
        "full_en": "Body Mass Index",
        "full_cn": "身体质量指数",
        "description_en": "A person's weight in kilograms divided by the square of height in meters. Used to classify underweight, normal weight, overweight, and obesity in children and adults.",
        "description_cn": "体重（公斤）除以身高（米）的平方。用于在儿童和成人中分类体重过轻、正常体重、超重和肥胖。",
    },
    "BMI z-score": {
        "full_en": "BMI-for-Age Z-Score",
        "full_cn": "BMI 年龄别 Z 评分",
        "description_en": "The number of standard deviations a child's BMI is above or below the average BMI for their age and gender. Recommended by WHO for assessing child adiposity.",
        "description_cn": "儿童 BMI 相对于同年龄同性别人群平均值的标准差个数。由 WHO 推荐用于评估儿童肥胖程度。",
    },
    "PBF": {
        "full_en": "Percent Body Fat",
        "full_cn": "体脂率",
        "description_en": "The proportion of body weight that is fat mass, expressed as a percentage. Typically measured by bioelectrical impedance analysis (BIA) or skinfold calipers.",
        "description_cn": "脂肪质量占体重的比例，以百分比表示。通常通过生物电阻抗分析（BIA）或皮褶厚度计测量。",
    },
    "WHR": {
        "full_en": "Waist-to-Hip Ratio",
        "full_cn": "腰臀比",
        "description_en": "Waist circumference divided by hip circumference. A measure of central (abdominal) adiposity; higher values indicate more visceral fat.",
        "description_cn": "腰围除以臀围。衡量中心性（腹部）肥胖的指标；数值越高表示内脏脂肪越多。",
    },
    "PSM": {
        "full_en": "Percent Skeletal Muscle",
        "full_cn": "肌肉率",
        "description_en": "The proportion of skeletal muscle mass relative to total body weight. Important for assessing body composition and metabolic health.",
        "description_cn": "骨骼肌质量相对于总体重的比例。对于评估身体成分和代谢健康非常重要。",
    },
    # ── 评估指标 ──
    "AUC": {
        "full_en": "Area Under the Receiver Operating Characteristic Curve",
        "full_cn": "受试者工作特征曲线下面积",
        "description_en": "Measures the model's ability to discriminate between two classes (high vs low responder). AUC=1.0 means perfect separation; AUC=0.5 means random guessing.",
        "description_cn": "衡量模型区分两类人群（高响应者 vs 低响应者）的能力。AUC=1.0 表示完美分离；AUC=0.5 表示随机猜测。",
    },
    "AUPRC": {
        "full_en": "Area Under the Precision-Recall Curve",
        "full_cn": "精确率-召回率曲线下面积",
        "description_en": "Measures precision vs recall trade-off. More informative than AUC when classes are imbalanced.",
        "description_cn": "衡量精确率与召回率的权衡。在类别不平衡时比 AUC 更有信息量。",
    },
    "ROC": {
        "full_en": "Receiver Operating Characteristic",
        "full_cn": "受试者工作特征",
        "description_en": "A curve plotting True Positive Rate (Sensitivity) against False Positive Rate (1 - Specificity) at various threshold settings.",
        "description_cn": "在多个阈值设置下，绘制真阳性率（灵敏度）对假阳性率（1-特异度）的曲线图。",
    },
    "Sens / Sensitivity": {
        "full_en": "Sensitivity (True Positive Rate, Recall)",
        "full_cn": "灵敏度（真阳性率/召回率）",
        "description_en": "Proportion of actual high-responders correctly identified. Sens = TP / (TP + FN).",
        "description_cn": "正确识别的实际高响应者比例。Sens = TP / (TP + FN)。",
    },
    "Spec / Specificity": {
        "full_en": "Specificity (True Negative Rate)",
        "full_cn": "特异度（真阴性率）",
        "description_en": "Proportion of actual low-responders correctly identified. Spec = TN / (TN + FP).",
        "description_cn": "正确识别的实际低响应者比例。Spec = TN / (TN + FP)。",
    },
    "M→F": {
        "full_en": "Male-to-Female Cross-Gender Validation",
        "full_cn": "男→女跨性别验证",
        "description_en": "Model trained on male subjects, tested on female subjects. Measures cross-gender generalizability.",
        "description_cn": "用男性数据训练，女性数据测试。衡量跨性别泛化能力。",
    },
    "F→M": {
        "full_en": "Female-to-Male Cross-Gender Validation",
        "full_cn": "女→男跨性别验证",
        "description_en": "Model trained on female subjects, tested on male subjects.",
        "description_cn": "用女性数据训练，男性数据测试。",
    },
    "Nested CV": {
        "full_en": "Nested Cross-Validation",
        "full_cn": "嵌套交叉验证",
        "description_en": "An outer loop (5-fold) for performance estimation and an inner loop (3-fold) for hyperparameter tuning, preventing information leakage.",
        "description_cn": "外层循环（5折）用于性能估计，内层循环（3折）用于超参数调优，防止信息泄露。",
    },
    "CV": {
        "full_en": "Cross-Validation",
        "full_cn": "交叉验证",
        "description_en": "A resampling procedure using different subsets of data to train and validate a model multiple times, providing a more robust performance estimate.",
        "description_cn": "使用数据的不同子集多次训练和验证模型的重采样过程，提供更稳健的性能估计。",
    },
    "k-fold CV": {
        "full_en": "k-Fold Cross-Validation",
        "full_cn": "k 折交叉验证",
        "description_en": "Data is divided into k subsets (folds). Each fold serves as the validation set once while the model trains on the remaining k-1 folds.",
        "description_cn": "数据被分成 k 个子集（折）。每次用 k-1 折训练，1 折验证，循环 k 次。",
    },
    "Δ": {
        "full_en": "Change Score (outroll - enroll)",
        "full_cn": "变化量（干预后 - 干预前）",
        "description_en": "All current website indicators refer to intervention change scores calculated as outroll minus enroll, rather than a single absolute measurement.",
        "description_cn": "当前网站中的指标默认都指干预变化量，计算方式为干预后减去干预前，而不是某一次单独测量的绝对值。",
    },
    "Q (Quartile)": {
        "full_en": "Quartile Grouping (Q1 vs Q4)",
        "full_cn": "四分位分组（Q1 vs Q4）",
        "description_en": "Participants are divided into 4 groups by indicator change magnitude. Q1 (bottom 25%) and Q4 (top 25%) are used as binary classes.",
        "description_cn": "按指标变化量将参与者分为4组，使用 Q1（后25%）和 Q4（前25%）作为二分类类别。",
    },
    "T (Tertile)": {
        "full_en": "Tertile Grouping (T1 vs T3)",
        "full_cn": "三分位分组（T1 vs T3）",
        "description_en": "Participants are divided into 3 groups. T1 (bottom 33%) and T3 (top 33%) are used as binary classes.",
        "description_cn": "按指标变化量将参与者分为3组，使用 T1（后33%）和 T3（前33%）作为二分类类别。",
    },
    # ── 机器学习术语 ──
    "CART": {
        "full_en": "Classification and Regression Tree",
        "full_cn": "分类与回归树",
        "description_en": "A decision tree algorithm used for both classification and regression tasks. Each node splits the data based on a feature value to minimize impurity.",
        "description_cn": "一种用于分类和回归任务的决策树算法。每个节点根据特征值分割数据以最小化不纯度。",
    },
    "Bagging": {
        "full_en": "Bootstrap Aggregating",
        "full_cn": "自助聚合",
        "description_en": "An ensemble technique that trains multiple models on different bootstrap samples and aggregates their predictions (e.g., majority voting for classification).",
        "description_cn": "一种集成技术，在不同的自助采样上训练多个模型并聚合预测（如分类的多数投票）。",
    },
    "Boosting": {
        "full_en": "Gradient Boosting",
        "full_cn": "梯度提升",
        "description_en": "An ensemble technique that builds trees sequentially, where each tree corrects the errors of the previous ones. Reduces bias and variance.",
        "description_cn": "一种集成技术，顺序构建树，每棵新树纠正前一棵树的错误。同时降低偏差和方差。",
    },
    "L1 (Lasso)": {
        "full_en": "L1 Regularization (Least Absolute Shrinkage and Selection Operator)",
        "full_cn": "L1 正则化（最小绝对收缩和选择算子）",
        "description_en": "Adds the sum of absolute coefficient values as a penalty to the loss function, encouraging sparsity (some coefficients become exactly zero, performing feature selection).",
        "description_cn": "在损失函数中加入系数绝对值之和作为惩罚项，促使系数稀疏化（部分系数变为零，实现特征选择）。",
    },
    "L2 (Ridge)": {
        "full_en": "L2 Regularization (Ridge Regression)",
        "full_cn": "L2 正则化（岭回归）",
        "description_en": "Adds the sum of squared coefficient values as a penalty to the loss function, shrinking all coefficients toward zero without eliminating any, improving numerical stability.",
        "description_cn": "在损失函数中加入系数平方和作为惩罚项，将所有系数向零收缩但不消除任何特征，提高数值稳定性。",
    },
    "Elastic Net": {
        "full_en": "Elastic Net Regularization",
        "full_cn": "弹性网络正则化",
        "description_en": "Combines L1 (Lasso) and L2 (Ridge) penalties: λ₁||β||₁ + λ₂||β||₂². Balances feature selection (L1) with coefficient shrinkage (L2).",
        "description_cn": "同时使用 L1（Lasso）和 L2（Ridge）惩罚项：λ₁||β||₁ + λ₂||β||₂²。兼顾特征选择（L1）和系数收缩（L2）。",
    },
    "AUROC": {
        "full_en": "Area Under the Receiver Operating Characteristic Curve",
        "full_cn": "受试者工作特征曲线下面积",
        "description_en": "Same as AUC. Used interchangeably with AUC in clinical and machine learning literature.",
        "description_cn": "与 AUC 相同。在临床和机器学习文献中与 AUC 可互换使用。",
    },
    "Bootstrap": {
        "full_en": "Bootstrap Sampling",
        "full_cn": "自助采样",
        "description_en": "A resampling technique where multiple datasets are created by sampling with replacement from the original dataset, each of the same size as the original.",
        "description_cn": "一种重采样技术，通过有放回地从原始数据集中抽样创建多个新数据集，每个新数据集的大小与原始数据集相同。",
    },
    "Hyperparameter": {
        "full_en": "Hyperparameter",
        "full_cn": "超参数",
        "description_en": "A parameter whose value is set before the learning process begins (e.g., tree depth, learning rate). Contrasts with model parameters learned from data.",
        "description_cn": "在学习过程开始前设置的参数（如树的深度、学习率）。区别于从数据中学习的模型参数。",
    },
    # ── 脂质类别 ──
    "SM": {
        "full_en": "Sphingomyelin",
        "full_cn": "鞘磷脂",
        "description_en": "A type of phospholipid found in cell membranes, especially abundant in the nervous system. Composed of ceramide linked to a phosphocholine head group.",
        "description_cn": "细胞膜中的一类磷脂，在神经系统中含量丰富。由神经酰胺连接磷酸胆碱头基组成。",
    },
    "TG": {
        "full_en": "Triacylglycerol (Triglyceride)",
        "full_cn": "甘油三酯",
        "description_en": "The main form of fat storage in the body, composed of three fatty acids and glycerol. Elevated TG levels are associated with metabolic syndrome.",
        "description_cn": "人体脂肪存储的主要形式，由三个脂肪酸和一个甘油组成。甘油三酯升高与代谢综合征相关。",
    },
    "PC": {
        "full_en": "Phosphatidylcholine",
        "full_cn": "磷脂酰胆碱",
        "description_en": "The most abundant phospholipid in eukaryotic cell membranes. Also a major component of pulmonary surfactant and the precursor for the neurotransmitter acetylcholine.",
        "description_cn": "真核细胞膜中最丰富的磷脂。也是肺表面活性剂的主要成分和神经递质乙酰胆碱的前体。",
    },
    "PE": {
        "full_en": "Phosphatidylethanolamine",
        "full_cn": "磷脂酰乙醇胺",
        "description_en": "A phospholipid involved in membrane fusion and cell signaling. Highly abundant in the inner leaflet of the plasma membrane and in mitochondrial membranes.",
        "description_cn": "参与膜融合和细胞信号传导的磷脂。在质膜内叶和线粒体膜中含量丰富。",
    },
    "Cer": {
        "full_en": "Ceramide",
        "full_cn": "神经酰胺",
        "description_en": "A central hub in lipid metabolism, involved in cell signaling, apoptosis, and stress response. Formed by condensation of sphingosine and a fatty acid.",
        "description_cn": "脂质代谢的核心枢纽，参与细胞信号传导、凋亡和应激反应。由鞘氨醇与脂肪酸缩合而成。",
    },
    "LPC": {
        "full_en": "Lysophosphatidylcholine",
        "full_cn": "溶血磷脂酰胆碱",
        "description_en": "A bioactive lipid involved in inflammation and cell proliferation. Produced by hydrolysis of PC by phospholipase A2.",
        "description_cn": "参与炎症和细胞增殖的生物活性脂质。由磷脂酶 A2 水解 PC 产生。",
    },
    "LPE": {
        "full_en": "Lysophosphatidylethanolamine",
        "full_cn": "溶血磷脂酰乙醇胺",
        "description_en": "A lysophospholipid involved in cellular processes. Produced by hydrolysis of PE.",
        "description_cn": "参与细胞过程的溶血磷脂。由 PE 水解产生。",
    },
    "DG": {
        "full_en": "Diacylglycerol",
        "full_cn": "甘油二酯",
        "description_en": "A lipid signaling molecule and intermediate in triglyceride synthesis. An important second messenger involved in protein kinase C (PKC) activation.",
        "description_cn": "脂质信号分子，也是甘油三酯合成的中间产物。是蛋白激酶 C（PKC）激活的重要第二信使。",
    },
    "Hex": {
        "full_en": "Hexosylceramide",
        "full_cn": "己糖基神经酰胺",
        "description_en": "A ceramide with a hexose sugar head group. Includes glucosylceramide (GlcCer) and galactosylceramide (GalCer), important for membrane structure and signaling.",
        "description_cn": "带己糖的神经酰胺。包括葡萄糖神经酰胺（GlcCer）和半乳糖神经酰胺（GalCer），对膜结构和信号传导重要。",
    },
    "PI": {
        "full_en": "Phosphatidylinositol",
        "full_cn": "磷脂酰肌醇",
        "description_en": "Involved in cell signaling and as a precursor for second messengers (e.g., PIP2, IP3, DAG). Critical for insulin signaling and calcium homeostasis.",
        "description_cn": "参与细胞信号传导，是第二信使（如 PIP2、IP3、DAG）的前体。对胰岛素信号传导和钙稳态至关重要。",
    },
    "PS": {
        "full_en": "Phosphatidylserine",
        "full_cn": "磷脂酰丝氨酸",
        "description_en": "A phospholipid involved in apoptosis and blood coagulation. Normally localized to the inner leaflet; externalization is an early apoptotic marker.",
        "description_cn": "参与细胞凋亡和血液凝固的磷脂。通常定位于质膜内叶；外翻是细胞早期凋亡的标志。",
    },
    "PA": {
        "full_en": "Phosphatidic Acid",
        "full_cn": "磷脂酸",
        "description_en": "A key intermediate in phospholipid and triacylglycerol biosynthesis. Also acts as a signaling lipid involved in cell growth and membrane trafficking.",
        "description_cn": "磷脂和甘油三酯生物合成的关键中间体。也作为参与细胞生长和膜运输的信号脂质。",
    },
    "CL": {
        "full_en": "Cardiolipin",
        "full_cn": "心磷脂",
        "description_en": "A unique phospholipid with four fatty acid chains, almost exclusively found in the inner mitochondrial membrane. Essential for mitochondrial cristae structure.",
        "description_cn": "一种具有四个脂肪酸链的特殊磷脂，几乎专门存在于线粒体内膜。对线粒体嵴结构至关重要。",
    },
    "PC ae": {
        "full_en": "Phosphatidylcholine, Alkyl/Acyl, Ether Lipid",
        "full_cn": "醚键磷脂酰胆碱（烷基-酰基型）",
        "description_en": "Ether-linked phosphatidylcholine where one fatty acid chain is attached via an ether bond (not ester). Often used as biomarkers in metabolomics studies.",
        "description_cn": "通过醚键连接脂肪酸链的磷脂酰胆碱。在代谢组学研究中常用作生物标志物。",
    },
    "PC ae C": {
        "full_en": "Phosphatidylcholine, Alkyl/Acyl, with additional Acyl chain (Diacyl)",
        "full_cn": "磷脂酰胆碱（烷基-酰基型，含额外酰基链）",
        "description_en": "A subclass of ether PC lipids with an additional acyl chain on the sn-1 position. Annotated in metabolomics as PC ae followed by carbon:double-bond counts.",
        "description_cn": "醚键 PC 脂质的亚类，在 sn-1 位有一个额外的酰基链。在代谢组学中标注为 PC ae 后跟碳数:双键数。",
    },
    "SM (OH)": {
        "full_en": "Hydroxysphingomyelin",
        "full_cn": "羟基鞘磷脂",
        "description_en": "Sphingomyelin with an additional hydroxyl group on the long-chain base or N-acyl chain. Modified form of SM found in metabolomics profiling.",
        "description_cn": "在长链碱基或 N-酰基链上带有一个额外羟基的鞘磷脂。代谢组学分析中发现的一种 SM 修饰形式。",
    },
    "LPC O": {
        "full_en": "Lysophosphatidylcholine, Ether-linked",
        "full_cn": "醚键溶血磷脂酰胆碱",
        "description_en": "Lysophosphatidylcholine with an ether bond (instead of ester) at the sn-1 position. Less common than standard LPC in plasma.",
        "description_cn": "在 sn-1 位通过醚键（而非酯键）连接的溶血磷脂酰胆碱。在血浆中比标准 LPC 少见。",
    },
    "Cer (dC)": {
        "full_en": "Ceramide (dihydroceramide)",
        "full_cn": "二氢神经酰胺",
        "description_en": "A dihydroceramide with a saturated sphingoid base (sphinganine). Precursor for all complex sphingolipids.",
        "description_cn": "具有饱和鞘氨醇碱基的二氢神经酰胺。所有复杂鞘脂的前体。",
    },
    "HexCer": {
        "full_en": "Hexosylceramide",
        "full_cn": "己糖基神经酰胺",
        "description_en": "Ceramide with one or more hexose sugars attached (glucose or galactose). Key component of myelin and involved in cell recognition.",
        "description_cn": "连接有一个或多个己糖（葡萄糖或半乳糖）的神经酰胺。是髓鞘的关键成分，参与细胞识别。",
    },
}

def normalize_group_code(group: str | None) -> str:
    raw = (group or "").strip().lower()
    if raw in {"q", "q4", "quartile"}:
        return "Q"
    if raw in {"t", "q3", "t3", "tertile"}:
        return "T"
    return "Q"


def infer_indicator_direction(indicator: str | None) -> str:
    return "positive" if indicator == "PSM" else "negative"


def get_indicator_display_meta(indicator: str | None) -> dict:
    indicator = indicator or ""
    meta = _INDICATOR_META.get(indicator, {})
    display_en = meta.get("display_en", f"Δ{indicator}" if indicator else "ΔIndicator")
    display_cn = meta.get("display_cn", f"Δ{_INDICATOR_CN.get(indicator, indicator or '指标')}")
    return {
        "indicator": indicator,
        "indicator_display": display_en,
        "indicator_display_en": display_en,
        "indicator_display_cn": display_cn,
        "indicator_full_en": meta.get("full_en", f"{indicator} change" if indicator else "Indicator change"),
        "indicator_full_cn": meta.get("full_cn", f"{_INDICATOR_CN.get(indicator, indicator or '指标')}变化量"),
        "indicator_short_cn": _INDICATOR_CN.get(indicator, indicator),
    }


def get_group_display_meta(group: str | None) -> dict:
    code = normalize_group_code(group)
    meta = _GROUP_META[code]
    return {
        "group": group,
        "group_code": meta["group_code"],
        "group_display": meta["group_display_en"],
        "group_display_en": meta["group_display_en"],
        "group_display_cn": meta["group_display_cn"],
        "group_strategy_en": meta["group_strategy_en"],
        "group_strategy_cn": meta["group_strategy_cn"],
        "group_cn": meta["group_display_cn"],
    }


def build_target_description(indicator_display_en: str, indicator_display_cn: str, group_display_en: str, group_display_cn: str, direction: str) -> tuple[str, str]:
    if direction == "negative":
        direction_en = "High response means the indicator decreases more after intervention."
        direction_cn = "高响应表示该指标在干预后下降更多。"
    else:
        direction_en = "High response means the indicator increases more after intervention."
        direction_cn = "高响应表示该指标在干预后上升更多。"
    description_en = (
        f"Predicts high vs low exercise response for {indicator_display_en} under {group_display_en}. "
        f"{direction_en}"
    )
    description_cn = (
        f"在 {group_display_cn} 分组下预测 {indicator_display_cn} 的高/低响应。"
        f"{direction_cn}"
    )
    return description_en, description_cn


def build_prediction_copy(info: dict, pred: int) -> dict:
    indicator_display_en = info.get("indicator_display_en", info.get("indicator_display", "ΔIndicator"))
    indicator_display_cn = info.get("indicator_display_cn", info.get("indicator_display", "Δ指标"))
    direction = info.get("direction", "positive")

    if pred == 1:
        label_en = "High Response"
        label_cn = "高响应"
        if direction == "negative":
            detail_en = (
                f"{indicator_display_en} is expected to decrease more after intervention, "
                "consistent with the high-response group."
            )
            detail_cn = f"{indicator_display_cn} 预计在干预后下降更多，属于高响应组。"
        else:
            detail_en = (
                f"{indicator_display_en} is expected to increase more after intervention, "
                "consistent with the high-response group."
            )
            detail_cn = f"{indicator_display_cn} 预计在干预后上升更多，属于高响应组。"
    else:
        label_en = "Low Response"
        label_cn = "低响应"
        if direction == "negative":
            detail_en = (
                f"{indicator_display_en} is expected to decrease less after intervention or even increase, "
                "consistent with the low-response group."
            )
            detail_cn = f"{indicator_display_cn} 预计在干预后下降较少，甚至可能升高，属于低响应组。"
        else:
            detail_en = (
                f"{indicator_display_en} is expected to increase less after intervention or even decrease, "
                "consistent with the low-response group."
            )
            detail_cn = f"{indicator_display_cn} 预计在干预后上升较少，甚至可能下降，属于低响应组。"

    return {
        "label_en": label_en,
        "label_cn": label_cn,
        "label_detail_en": detail_en,
        "label_detail_cn": detail_cn,
    }


def build_model_metadata(model_key: str, info: dict | None = None, data: dict | None = None) -> dict:
    info = info or {}
    data = data or {}

    indicator = data.get("indicator") or info.get("indicator") or model_key
    group_raw = data.get("group") or info.get("group") or "q4"
    direction = data.get("direction") or info.get("direction") or infer_indicator_direction(indicator)
    features = data.get("features") or info.get("features") or []

    indicator_meta = get_indicator_display_meta(indicator)
    group_meta = get_group_display_meta(group_raw)
    description_en, description_cn = build_target_description(
        indicator_display_en=indicator_meta["indicator_display_en"],
        indicator_display_cn=indicator_meta["indicator_display_cn"],
        group_display_en=group_meta["group_display_en"],
        group_display_cn=group_meta["group_display_cn"],
        direction=direction,
    )

    return {
        **info,
        "key": model_key,
        "indicator": indicator,
        "indicator_cn": indicator_meta["indicator_short_cn"],
        "direction": direction,
        "model_name": data.get("model_name") or info.get("model_name", ""),
        "full_auc": data.get("full_auc", info.get("full_auc", 0)),
        "m2f_auc": data.get("m2f_auc", info.get("m2f_auc", 0)),
        "f2m_auc": data.get("f2m_auc", info.get("f2m_auc", 0)),
        "sens": data.get("sens", info.get("sens", 0)),
        "spec": data.get("spec", info.get("spec", 0)),
        "n_feat": len(features) or info.get("n_feat", 0),
        "features": features,
        "description": info.get("description", description_cn),
        "description_en": description_en,
        "description_cn": description_cn,
        "target_definition_en": f"{indicator_meta['indicator_display_en']} = outroll - enroll",
        "target_definition_cn": f"{indicator_meta['indicator_display_cn']} = 干预后 - 干预前",
        **indicator_meta,
        **group_meta,
    }


def get_model_metadata(model_key: str) -> dict:
    normalized = build_model_metadata(
        model_key,
        info=_model_info.get(model_key, {}),
        data=_models.get(model_key, {}),
    )
    if normalized:
        _model_info[model_key] = normalized
    return normalized


def load_all_models():
    """Load all .pkl model files at startup."""
    info_path = DATA_DIR / "model_info.json"
    if info_path.exists():
        with open(info_path, encoding="utf-8") as f:
            _model_info.update(json.load(f))

    for pkl_file in MODELS_DIR.glob("*.pkl"):
        key = pkl_file.stem
        with open(pkl_file, "rb") as f:
            data = pickle.load(f)
        _models[key] = data
        if key not in _model_info:
            _model_info[key] = {
                "indicator": data.get("indicator", key),
                "model_name": data.get("model_name", "?"),
                "path": str(pkl_file.relative_to(BASE_DIR)),
            }
    print(f"[App] Loaded {len(_models)} models: {sorted(_models.keys())}")

    # Also try loading from GLM5 trained_models directory
    glm5_model_dir = BASE_DIR / "trained_models"
    glm5_meta_path = glm5_model_dir / "model_metadata.json"
    _glm5_metadata = {}
    if glm5_meta_path.exists():
        with open(glm5_meta_path, encoding="utf-8") as f:
            _glm5_metadata = json.load(f)

    if glm5_model_dir.exists():
        for pkl_file in glm5_model_dir.glob("*.pkl"):
            key = pkl_file.stem
            if key not in _models:
                try:
                    with open(pkl_file, "rb") as f:
                        raw_model = pickle.load(f)
                    # GLM5 models are raw sklearn objects; wrap with metadata
                    meta = _glm5_metadata.get(key, {})
                    features = meta.get("features", [])
                    perf = meta.get("performance", {})
                    # Normalize indicator name
                    parts = key.split("_")
                    model_abbrev = parts[-1] if len(parts) >= 3 else "?"
                    indicator = "_".join(parts[:-2])
                    _models[key] = {
                        "model": raw_model,
                        "features": features,
                        "indicator": indicator,
                        "group": parts[-2] if len(parts) >= 2 else "Q",
                        "model_name": model_abbrev,
                        "full_auc": perf.get("full_auroc", 0),
                        "m2f_auc": perf.get("m2f_auroc", 0),
                        "f2m_auc": perf.get("f2m_auroc", 0),
                        "sens": perf.get("full_sens", 0),
                        "spec": perf.get("full_spec", 0),
                        "is_glm5": True,
                    }
                    _model_info[key] = {
                        "indicator": indicator,
                        "indicator_cn": _INDICATOR_CN.get(indicator, indicator),
                        "model_name": model_abbrev,
                        "group": parts[-2] if len(parts) >= 2 else "Q",
                        "group_cn": "四分位" if parts[-2] == "Q" else "三分位",
                        "full_auc": perf.get("full_auroc", 0),
                        "m2f_auc": perf.get("m2f_auroc", 0),
                        "f2m_auc": perf.get("f2m_auroc", 0),
                        "sens": perf.get("full_sens", 0),
                        "spec": perf.get("full_spec", 0),
                        "n_feat": len(features),
                        "features": features,
                        "path": str(pkl_file.relative_to(APP_DIR)),
                    }
                except Exception as e:
                    print(f"[App] Failed to load {pkl_file}: {e}")
        print(f"[App] Total models loaded: {len(_models)}")

    for key in list(set(_models) | set(_model_info)):
        _model_info[key] = build_model_metadata(
            key,
            info=_model_info.get(key, {}),
            data=_models.get(key, {}),
        )

# ── 脂质名称标准化 ──────────────────────────────────────────────────
def normalize_lipid_name(name: str) -> str:
    """Strip whitespace and normalize lipid feature name for matching."""
    return name.strip()

def find_lipid_value(lipid_name: str, request_data: dict) -> float | None:
    """Find lipid value from request data, trying multiple name variants."""
    name = normalize_lipid_name(lipid_name)
    for key, val in request_data.items():
        if normalize_lipid_name(key) == name:
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
    return None

# ── 预测核心 ─────────────────────────────────────────────────────────
def predict_single(model_key: str, lipid_values: dict) -> dict:
    """Run single-sample prediction using a specific model."""
    if model_key not in _models:
        return {"error": f"Model '{model_key}' not found"}

    data = _models[model_key]
    model = data["model"]
    features = data["features"]

    # Build feature vector
    X = []
    missing = []
    for feat in features:
        val = find_lipid_value(feat, lipid_values)
        if val is None:
            missing.append(feat)
            val = 0.0  # default fallback
        X.append(val)
    X = np.array(X).reshape(1, -1)

    # Predict
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]

    info = get_model_metadata(model_key)
    copy = build_prediction_copy(info, int(pred))

    return {
        "model_key": model_key,
        "prediction": int(pred),
        "label": copy["label_cn"],
        "label_en": copy["label_en"],
        "label_cn": copy["label_cn"],
        "label_detail": copy["label_detail_cn"],
        "label_detail_en": copy["label_detail_en"],
        "label_detail_cn": copy["label_detail_cn"],
        "confidence": float(max(proba)),
        "prob_high_response": float(proba[1]) if len(proba) > 1 else 0.0,
        "prob_low_response": float(proba[0]) if len(proba) > 0 else 0.0,
        "missing_features": missing,
        "model_info": {
            "indicator": info.get("indicator", ""),
            "indicator_cn": info.get("indicator_cn", ""),
            "indicator_display": info.get("indicator_display", ""),
            "indicator_display_en": info.get("indicator_display_en", ""),
            "indicator_display_cn": info.get("indicator_display_cn", ""),
            "group": info.get("group", ""),
            "group_code": info.get("group_code", ""),
            "group_cn": info.get("group_cn", ""),
            "group_display_en": info.get("group_display_en", ""),
            "group_display_cn": info.get("group_display_cn", ""),
            "model_name": info.get("model_name", ""),
            "full_auc": info.get("full_auc", 0),
            "m2f_auc": info.get("m2f_auc", 0),
            "f2m_auc": info.get("f2m_auc", 0),
            "sens": info.get("sens", 0),
            "spec": info.get("spec", 0),
            "n_feat": len(features),
            "features": features,
        }
    }

# ── API Routes ───────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/models", methods=["GET"])
def api_models():
    """Return list of available models with metadata."""
    models = {key: get_model_metadata(key) for key in sorted(_model_info)}
    return jsonify({
        "count": len(models),
        "models": models,
    })

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """Single sample prediction."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    model_key = data.get("model_key", "")
    lipid_values = {k: v for k, v in data.items() if k != "model_key"}
    result = predict_single(model_key, lipid_values)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)

@app.route("/api/batch_predict", methods=["POST"])
def api_batch_predict():
    """Batch prediction from CSV upload."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    model_key = request.form.get("model_key", "")

    if model_key not in _models:
        return jsonify({"error": f"Model '{model_key}' not found"}), 404

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"CSV parse error: {str(e)}"}), 400

    data = _models[model_key]
    features = data["features"]
    results = []
    for idx, row in df.iterrows():
        lipid_values = row.to_dict()
        result = predict_single(model_key, lipid_values)
        result["row_id"] = idx + 1
        results.append(result)

    # Save results to CSV
    rows = []
    for r in results:
        rows.append({
            "row_id": r.get("row_id"),
            "prediction": r.get("label", "ERROR"),
            "prob_high_response": round(r.get("prob_high_response", 0), 4),
            "prob_low_response": round(r.get("prob_low_response", 0), 4),
            "confidence": round(r.get("confidence", 0), 4),
            "missing_features": ",".join(r.get("missing_features", [])) if r.get("missing_features") else "",
        })
    result_df = pd.DataFrame(rows)
    tmp_path = DATA_DIR / "batch_results.csv"
    result_df.to_csv(tmp_path, index=False)
    return send_file(tmp_path, mimetype="text/csv",
                     as_attachment=True, download_name="predictions.csv")

@app.route("/api/model_detail/<model_key>", methods=["GET"])
def api_model_detail(model_key: str):
    """Return detailed info for a specific model."""
    if model_key not in _model_info:
        return jsonify({"error": "Model not found"}), 404

    info = get_model_metadata(model_key)
    data = _models.get(model_key, {})
    features = data.get("features", [])

    # Lipid class description (simplified)
    def lipid_class(name: str) -> str:
        for cls in ["TG", "PC", "PE", "SM", "Cer", "LPC", "LPE", "DG", "Hex", "PI", "PS", "PA", "CL"]:
            if name.startswith(cls):
                return cls
        return "Other"

    lipid_info = []
    for i, feat in enumerate(features[:20], 1):
        lipid_info.append({
            "rank": i,
            "name": feat,
            "class": lipid_class(feat),
        })

    return jsonify({
        "key": model_key,
        "indicator": info.get("indicator", ""),
        "indicator_cn": info.get("indicator_cn", ""),
        "indicator_display": info.get("indicator_display", ""),
        "indicator_display_en": info.get("indicator_display_en", ""),
        "indicator_display_cn": info.get("indicator_display_cn", ""),
        "group": info.get("group", ""),
        "group_code": info.get("group_code", ""),
        "group_cn": info.get("group_cn", ""),
        "group_display_en": info.get("group_display_en", ""),
        "group_display_cn": info.get("group_display_cn", ""),
        "model_name": info.get("model_name", ""),
        "full_auc": info.get("full_auc", 0),
        "m2f_auc": info.get("m2f_auc", 0),
        "f2m_auc": info.get("f2m_auc"),
        "sens": info.get("sens", 0),
        "spec": info.get("spec", 0),
        "n_feat": len(features),
        "description": info.get("description_cn", info.get("description", "")),
        "description_en": info.get("description_en", ""),
        "description_cn": info.get("description_cn", ""),
        "target_definition_en": info.get("target_definition_en", ""),
        "target_definition_cn": info.get("target_definition_cn", ""),
        "direction": info.get("direction", ""),
        "features": lipid_info,
        "model_doc": MODEL_DOCS.get(info.get("model_name", ""), MODEL_DOCS.get(model_key, {})),
    })


@app.route("/api/sample_data/<model_key>", methods=["GET"])
def api_sample_data(model_key: str):
    """Return sample (mean) lipid values for a given model as example input."""
    if model_key not in _models:
        return jsonify({"error": f"Model '{model_key}' not found"}), 404

    data = _models[model_key]
    features = data.get("features", [])
    if not features:
        return jsonify({"error": "No features found for this model"}), 404

    # Load training data to compute feature means
    candidate_paths = [
        APP_DIR / "281_merge_lipids_enroll.csv",
        BASE_DIR.parent / "281_merge_lipids_enroll.csv",
        Path.cwd() / "281_merge_lipids_enroll.csv",
    ]
    lipid_csv = next((path for path in candidate_paths if path.exists()), None)
    if lipid_csv is None:
        return jsonify({"error": "Training data not found"}), 404

    try:
        df = pd.read_csv(lipid_csv)
        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        sample_values = {}
        for feat in features:
            # Try exact match first
            col_name = None
            for col in df.columns:
                if col.strip() == feat.strip():
                    col_name = col
                    break
            if col_name is not None:
                vals = pd.to_numeric(df[col_name], errors="coerce").dropna()
                if len(vals) > 0:
                    sample_values[feat] = round(float(vals.mean()), 6)
                else:
                    sample_values[feat] = 0.0
            else:
                sample_values[feat] = 0.0

        return jsonify({
            "model_key": model_key,
            "sample_values": sample_values,
            "note_en": "These are mean lipid concentrations from the training cohort (n=281) as example inputs. You can modify any value before prediction.",
            "note_cn": "以下为训练队列（n=281）的脂质平均浓度，作为示例输入。预测前可自行修改任意数值。",
        })
    except Exception as e:
        return jsonify({"error": f"Failed to compute sample data: {str(e)}"}), 500


@app.route("/api/glossary", methods=["GET"])
def api_glossary():
    """Return abbreviation glossary."""
    return jsonify({
        "model_docs": MODEL_DOCS,
        "abbrev_glossary": ABBREV_GLOSSARY,
    })

# ── Startup ──────────────────────────────────────────────────────────
load_all_models()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("多指标脂质组预测网站")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5001, debug=True)
