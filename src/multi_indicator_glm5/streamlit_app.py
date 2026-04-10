"""
Phase 7: Streamlit Interactive Prediction Website.
GLM5 execution — 2026-04-10

Features:
- Select indicator + cutoff + model
- Input lipid values manually or upload CSV
- Real-time prediction with probability
- Interactive vector-quality ROC curves with Bootstrap 95% CI bands (Plotly)
- PRC (Precision-Recall) curves with CI bands
- Model performance comparison table with 95% CI
- Cross-gender validation results
- Follows Shiny reference project paradigm

Usage:
  cd /Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型
  streamlit run src/multi_indicator_glm5/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Config ──────────────────────────────────────────────────────────────
PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
MODEL_DIR = OUT_DIR / "trained_models"
DATA_DIR = PROJECT

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
INDICATOR_CN = {
    "BMI": "BMI", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}
MODELS = ["EN_LR", "XGBoost", "RF", "LR_L2"]
MODEL_LABELS = {
    "EN_LR": "Elastic Net LR",
    "XGBoost": "XGBoost",
    "RF": "Random Forest",
    "LR_L2": "Logistic Regression (L2)",
}
MODEL_COLORS = {
    "EN_LR": "#4C78A8",
    "XGBoost": "#F58518",
    "RF": "#E45756",
    "LR_L2": "#72B7B2",
}

TRIAL_TITLE = "EXCITING Study (NCT04984005)"
SUBTITLE = "儿童运动干预减重指标脂质组学预测模型"

# ── Page config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="脂质组学预测模型 — EXCITING Study",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load metadata ───────────────────────────────────────────────────────
@st.cache_data
def load_metadata():
    with open(MODEL_DIR / "model_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_feature_stats():
    lipid = pd.read_csv(DATA_DIR / "281_merge_lipids_enroll.csv")
    feat = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    stats = {}
    for col in feat.columns:
        vals = feat[col].dropna()
        stats[col] = {
            "mean": float(vals.mean()),
            "std": float(vals.std()),
            "min": float(vals.min()),
            "max": float(vals.max()),
            "q25": float(vals.quantile(0.25)),
            "q75": float(vals.quantile(0.75)),
        }
    return stats

@st.cache_resource
def load_model(run_id):
    pkl_path = MODEL_DIR / f"{run_id}.pkl"
    if pkl_path.exists():
        with open(pkl_path, "rb") as f:
            return pickle.load(f)
    return None

@st.cache_data
def load_reference_data():
    lipid = pd.read_csv(DATA_DIR / "281_merge_lipids_enroll.csv")
    feat = lipid.drop(columns=["NAME"]).select_dtypes(include=[np.number])
    feat.index = lipid["NAME"].values
    return feat


metadata = load_metadata()
feat_stats = load_feature_stats()
ref_data = load_reference_data()

# ── Helper: format CI ───────────────────────────────────────────────────
def fmt_ci(val, lower, upper):
    """Format value with 95% CI bracket."""
    if val is None:
        return "—"
    parts = [f"{val:.3f}"]
    if lower is not None and upper is not None:
        parts.append(f"[{lower:.3f}-{upper:.3f}]")
    return " ".join(parts)

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### {TRIAL_TITLE}")
    st.markdown(f"**{SUBTITLE}**")
    st.markdown("---")

    st.markdown("#### 参数设置")

    indicator = st.selectbox(
        "预测指标",
        INDICATORS,
        format_func=lambda x: f"{INDICATOR_CN[x]} ({x})",
        index=INDICATORS.index("PBF"),
    )

    cutoff = st.radio(
        "分组策略",
        ["Q", "T"],
        format_func=lambda x: "四分位 (Q1 vs Q4)" if x == "Q" else "三分位 (T1 vs T3)",
        horizontal=True,
    )

    model_name = st.selectbox(
        "预测模型",
        MODELS,
        format_func=lambda x: MODEL_LABELS[x],
        index=0,
    )

    auto_best = st.checkbox("自动选择最佳模型", value=True)
    if auto_best:
        best_auc = -1
        best_model = MODELS[0]
        for m in MODELS:
            run_id = f"{indicator}_{cutoff}_{m}"
            if run_id in metadata:
                auc = metadata[run_id]["performance"].get("full_auroc", 0)
                if auc > best_auc:
                    best_auc = auc
                    best_model = m
        model_name = best_model
        ci_lo = metadata.get(f"{indicator}_{cutoff}_{best_model}", {}).get("performance", {}).get("auroc_ci_lower")
        ci_hi = metadata.get(f"{indicator}_{cutoff}_{best_model}", {}).get("performance", {}).get("auroc_ci_upper")
        ci_str = f" [{ci_lo:.3f}-{ci_hi:.3f}]" if ci_lo and ci_hi else ""
        st.info(f"最佳模型: {MODEL_LABELS[best_model]} (AUROC={best_auc:.3f}{ci_str})")

    st.markdown("---")

    st.markdown("#### 数据输入方式")
    input_mode = st.radio(
        "输入方式",
        ["手动输入脂质值", "上传 CSV 文件", "选择参考样本"],
        index=2,
    )

    run_id = f"{indicator}_{cutoff}_{model_name}"
    model_meta = metadata.get(run_id, {})
    features = model_meta.get("features", [])

    input_values = {}

    if input_mode == "手动输入脂质值":
        st.markdown(f"**需要输入 {len(features)} 个脂质特征值**")
        for feat_name in features:
            stats = feat_stats.get(feat_name, {})
            default_val = stats.get("mean", 0.0)
            min_val = stats.get("min", 0.0)
            max_val = stats.get("max", default_val * 3)
            input_values[feat_name] = st.number_input(
                feat_name,
                value=round(default_val, 6),
                min_value=round(min_val, 6),
                max_value=round(max_val, 6),
                format="%.6f",
                key=f"input_{feat_name}",
            )

    elif input_mode == "选择参考样本":
        sample_ids = list(ref_data.index[:20])
        selected_sample = st.selectbox("选择参考样本 ID", sample_ids)
        if selected_sample:
            for feat_name in features:
                if feat_name in ref_data.columns:
                    input_values[feat_name] = float(ref_data.loc[selected_sample, feat_name])
                else:
                    input_values[feat_name] = 0.0
            st.caption(f"已加载样本 {selected_sample} 的脂质特征数据")

    elif input_mode == "上传 CSV 文件":
        uploaded = st.file_uploader("上传 CSV (需包含特征列)", type=["csv"])
        if uploaded:
            try:
                upload_df = pd.read_csv(uploaded)
                st.dataframe(upload_df.head(3), use_container_width=True)
                for feat_name in features:
                    if feat_name in upload_df.columns:
                        input_values[feat_name] = float(upload_df[feat_name].iloc[0])
                    else:
                        input_values[feat_name] = 0.0
                st.success(f"已加载 {len(upload_df)} 行数据（使用第一行预测）")
            except Exception as e:
                st.error(f"CSV 解析失败: {e}")

    st.markdown("---")
    st.markdown("**GLM5** | 2026-04-10 | n=281")
    st.caption("需求方: Shuxian Zhang | 分析提供方: Chenyu Fan")
    st.caption("参考: Chen et al., Cell Reports Medicine (2026)")

# ── Main content ────────────────────────────────────────────────────────

st.markdown(f"""
<div style='background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            padding: 1.5rem 2rem; border-radius: 8px; margin-bottom: 1.5rem;'>
<h1 style='color: white; margin: 0; font-size: 1.6rem;'>{TRIAL_TITLE}</h1>
<p style='color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0; font-size: 1rem;'>{SUBTITLE}</p>
<p style='color: rgba(255,255,255,0.6); margin: 0.3rem 0 0 0; font-size: 0.85rem;'>
8 减重指标 × 4 ML 模型 × 2 分组策略 | Strict Nested CV + 性别交叉验证 | Bootstrap 95% CI</p>
</div>
""", unsafe_allow_html=True)

# ── Prediction result ──────────────────────────────────────────────────
if input_values and features:
    model = load_model(run_id)
    if model is not None:
        feat_vals = [input_values.get(f, 0.0) for f in features]
        X_input = np.array(feat_vals).reshape(1, -1)

        try:
            prob = model.predict_proba(X_input)[0]
            pred_class = model.predict(X_input)[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                if pred_class == 1:
                    st.markdown(f"""
                    <div style='background: #fff3e0; border-left: 4px solid #f39c12;
                                padding: 1rem; border-radius: 6px;'>
                    <h3 style='margin:0; color: #e65100;'>预测结果：显著变化组 (高)</h3>
                    <p style='margin:0.3rem 0 0 0; font-size: 0.85rem; color: #666;'>
                    该样本基线脂质谱预测为 {INDICATOR_CN[indicator]} 变化四分位/三分位的高变化组</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #e8f5e9; border-left: 4px solid #27ae60;
                                padding: 1rem; border-radius: 6px;'>
                    <h3 style='margin:0; color: #1b5e20;'>预测结果：低变化组</h3>
                    <p style='margin:0.3rem 0 0 0; font-size: 0.85rem; color: #666;'>
                    该样本基线脂质谱预测为 {INDICATOR_CN[indicator]} 变化四分位/三分位的低变化组</p>
                    </div>
                    """, unsafe_allow_html=True)

            with col2:
                prob_high = prob[1] if len(prob) > 1 else prob[0]
                st.metric("高变化组概率", f"{prob_high:.1%}")
                st.progress(min(prob_high, 1.0))

            with col3:
                cutoff_label = "Q4 (高变化)" if cutoff == "Q" else "T3 (高变化)"
                cutoff_low = "Q1 (低变化)" if cutoff == "Q" else "T1 (低变化)"
                p = model_meta.get("performance", {})
                sens_ci = fmt_ci(p.get("sens_point"), p.get("sens_ci_lower"), p.get("sens_ci_upper"))
                spec_ci = fmt_ci(p.get("spec_point"), p.get("spec_ci_lower"), p.get("spec_ci_upper"))
                st.markdown(f"""
                **模型信息**
                - 指标: {INDICATOR_CN[indicator]} ({indicator})
                - 分组: {'四分位' if cutoff == 'Q' else '三分位'} ({cutoff_low} vs {cutoff_label})
                - 模型: {MODEL_LABELS[model_name]}
                - 特征数: {len(features)}
                - Sensitivity: {sens_ci}
                - Specificity: {spec_ci}
                """)

        except Exception as e:
            st.error(f"预测失败: {e}")
    else:
        st.warning(f"模型 {run_id} 未找到")

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 模型性能对比", "📈 ROC + PRC 曲线", "🔬 脂质特征详情",
    "👥 性别交叉验证", "📋 全部结果汇总"
])

# ── Tab 1: Model comparison (with CI) ───────────────────────────────────
with tab1:
    st.markdown(f"### {INDICATOR_CN[indicator]} — 模型性能对比 ({'四分位' if cutoff == 'Q' else '三分位'})")

    perf_data = []
    for m in MODELS:
        rid = f"{indicator}_{cutoff}_{m}"
        if rid in metadata:
            d = metadata[rid]
            p = d["performance"]
            perf_data.append({
                "模型": MODEL_LABELS[m],
                "AUROC [95% CI]": fmt_ci(p.get("full_auroc"), p.get("auroc_ci_lower"), p.get("auroc_ci_upper")),
                "AUPRC [95% CI]": fmt_ci(p.get("full_auprc"), p.get("auprc_ci_lower"), p.get("auprc_ci_upper")),
                "Sensitivity [95% CI]": fmt_ci(p.get("sens_point"), p.get("sens_ci_lower"), p.get("sens_ci_upper")),
                "Specificity [95% CI]": fmt_ci(p.get("spec_point"), p.get("spec_ci_lower"), p.get("spec_ci_upper")),
                "特征数": d["n_features"],
                "M→F AUROC": f"{p['m2f_auroc']:.3f}" if p.get("m2f_auroc") else "—",
                "F→M AUROC": f"{p['f2m_auroc']:.3f}" if p.get("f2m_auroc") else "—",
            })

    if perf_data:
        perf_df = pd.DataFrame(perf_data)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)

        # Bar chart with error bars
        fig = go.Figure()
        x_labels = [MODEL_LABELS[m] for m in MODELS]
        colors = [MODEL_COLORS[m] for m in MODELS]

        aucs, ci_lo, ci_hi = [], [], []
        for m in MODELS:
            rid = f"{indicator}_{cutoff}_{m}"
            if rid in metadata:
                p = metadata[rid]["performance"]
                aucs.append(p.get("full_auroc", 0))
                ci_lo.append(p.get("auroc_ci_lower", 0))
                ci_hi.append(p.get("auroc_ci_upper", 0))
            else:
                aucs.append(0); ci_lo.append(0); ci_hi.append(0)

        error_y = [auc - lo for auc, lo in zip(aucs, ci_lo)]
        error_y_plus = [hi - auc for auc, hi in zip(aucs, ci_hi)]

        fig.add_trace(go.Bar(
            x=x_labels, y=aucs,
            marker_color=colors,
            error_y=dict(type="data", symmetric=False, array=error_y_plus, arrayminus=error_y),
            text=[f"{v:.3f}" for v in aucs],
            textposition="outside",
            name="AUROC",
        ))

        fig.update_layout(
            title=f"{INDICATOR_CN[indicator]} — 各模型 AUROC 对比 ({'四分位' if cutoff == 'Q' else '三分位'})  |  误差棒 = 95% CI",
            yaxis=dict(title="AUROC", range=[0.2, 1.05]),
            xaxis_title="模型",
            showlegend=False,
            height=400,
            margin=dict(t=60, b=40),
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_hline(y=0.7, line_dash="dot", line_color="green", opacity=0.3)
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: ROC + PRC curves (vector quality, with CI bands) ────────────
with tab2:
    st.markdown(f"### {INDICATOR_CN[indicator]} — ROC 曲线 ({'四分位' if cutoff == 'Q' else '三分位'})")

    fig_roc = go.Figure()

    fig_roc.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines", line=dict(color="gray", dash="dash", width=1),
        showlegend=True, name="Random (AUC=0.500)",
    ))

    for m in MODELS:
        rid = f"{indicator}_{cutoff}_{m}"
        if rid in metadata:
            d = metadata[rid]
            roc = d.get("roc_data", [])
            ci_band = d.get("roc_ci_band", {})
            p = d["performance"]
            auc_val = p.get("full_auroc", 0)
            ci_lo = p.get("auroc_ci_lower")
            ci_hi = p.get("auroc_ci_upper")

            if roc and len(roc) > 1:
                fpr_vals = [pt["fpr"] for pt in roc]
                tpr_vals = [pt["tpr"] for pt in roc]
                color = MODEL_COLORS[m]

                # CI shading band
                if ci_band.get("fpr_grid"):
                    band_fpr = ci_band["fpr_grid"]
                    band_upper = ci_band["tpr_upper"]
                    band_lower = ci_band["tpr_lower"]
                    # Upper bound (forward) + Lower bound (reverse) to close polygon
                    fig_roc.add_trace(go.Scatter(
                        x=band_fpr + band_fpr[::-1],
                        y=band_upper + band_lower[::-1],
                        fill="toself",
                        fillcolor=color,
                        opacity=0.12,
                        line=dict(color="rgba(0,0,0,0)"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))

                # ROC curve
                ci_str = f" [{ci_lo:.3f}-{ci_hi:.3f}]" if ci_lo and ci_hi else ""
                fig_roc.add_trace(go.Scatter(
                    x=fpr_vals, y=tpr_vals,
                    mode="lines",
                    line=dict(color=color, width=2.5),
                    name=f"{MODEL_LABELS[m]} (AUC={auc_val:.3f}{ci_str})",
                    hovertemplate="FPR: %{x:.3f}<br>TPR: %{y:.3f}<extra></extra>",
                ))

    fig_roc.update_layout(
        title=dict(
            text=f"{INDICATOR_CN[indicator]} — ROC 曲线 ({'四分位 Q' if cutoff == 'Q' else '三分位 T'})  |  阴影区 = 95% CI",
            font=dict(size=15),
        ),
        xaxis=dict(
            title="False Positive Rate (1 - Specificity)",
            range=[-0.02, 1.02], scaleanchor="y", scaleratio=1,
            gridcolor="#eee", zeroline=False,
        ),
        yaxis=dict(
            title="True Positive Rate (Sensitivity)",
            range=[-0.02, 1.02],
            gridcolor="#eee", zeroline=False,
        ),
        width=600, height=600,
        legend=dict(x=0.98, y=0.02, xanchor="right", yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd", borderwidth=1,
                    font=dict(size=11)),
        margin=dict(l=60, r=30, t=50, b=50),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig_roc, use_container_width=True)

    # ── PRC curves ──
    st.markdown(f"### {INDICATOR_CN[indicator]} — PRC 曲线 (Precision-Recall)")

    fig_prc = go.Figure()

    for m in MODELS:
        rid = f"{indicator}_{cutoff}_{m}"
        if rid in metadata:
            d = metadata[rid]
            prc = d.get("prc_data", [])
            ci_band = d.get("prc_ci_band", {})
            p = d["performance"]
            ap_val = p.get("full_auprc", 0)
            ci_lo = p.get("auprc_ci_lower")
            ci_hi = p.get("auprc_ci_upper")
            color = MODEL_COLORS[m]

            if prc and len(prc) > 1:
                rec_vals = [pt["recall"] for pt in prc]
                prec_vals = [pt["precision"] for pt in prc]

                # CI band
                if ci_band.get("recall_grid"):
                    band_rec = ci_band["recall_grid"]
                    band_upper = ci_band["prec_upper"]
                    band_lower = ci_band["prec_lower"]
                    fig_prc.add_trace(go.Scatter(
                        x=band_rec + band_rec[::-1],
                        y=band_upper + band_lower[::-1],
                        fill="toself",
                        fillcolor=color,
                        opacity=0.12,
                        line=dict(color="rgba(0,0,0,0)"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))

                ci_str = f" [{ci_lo:.3f}-{ci_hi:.3f}]" if ci_lo and ci_hi else ""
                fig_prc.add_trace(go.Scatter(
                    x=rec_vals, y=prec_vals,
                    mode="lines",
                    line=dict(color=color, width=2.5),
                    name=f"{MODEL_LABELS[m]} (AP={ap_val:.3f}{ci_str})",
                    hovertemplate="Recall: %{x:.3f}<br>Precision: %{y:.3f}<extra></extra>",
                ))

    # Baseline (prevalence)
    n1 = model_meta.get("n_class1", 0)
    n0 = model_meta.get("n_class0", 0)
    if (n1 + n0) > 0:
        baseline = n1 / (n1 + n0)
        fig_prc.add_trace(go.Scatter(
            x=[0, 1], y=[baseline, baseline],
            mode="lines", line=dict(color="gray", dash="dash", width=1),
            showlegend=True, name=f"Baseline (prevalence={baseline:.2f})",
        ))

    fig_prc.update_layout(
        title=dict(
            text=f"{INDICATOR_CN[indicator]} — PRC 曲线  |  阴影区 = 95% CI",
            font=dict(size=15),
        ),
        xaxis=dict(title="Recall (Sensitivity)", range=[-0.02, 1.02], gridcolor="#eee", zeroline=False),
        yaxis=dict(title="Precision (PPV)", range=[-0.02, 1.02], gridcolor="#eee", zeroline=False),
        width=600, height=600,
        legend=dict(x=0.98, y=0.98, xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="#ddd", borderwidth=1,
                    font=dict(size=11)),
        margin=dict(l=60, r=30, t=50, b=50),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig_prc, use_container_width=True)

# ── Tab 3: Feature details ─────────────────────────────────────────────
with tab3:
    st.markdown(f"### {INDICATOR_CN[indicator]} — 脂质特征详情")
    st.markdown(f"模型: {MODEL_LABELS[model_name]} | 分组: {'四分位' if cutoff == 'Q' else '三分位'} | 特征数: {len(features)}")

    if features:
        feat_detail = []
        for feat_name in features:
            stats = feat_stats.get(feat_name, {})
            val = input_values.get(feat_name, "—")
            feat_detail.append({
                "脂质特征": feat_name,
                "输入值": f"{val:.6f}" if isinstance(val, float) else val,
                "参考均值": f"{stats.get('mean', 0):.6f}",
                "参考标准差": f"{stats.get('std', 0):.6f}",
                "参考范围": f"{stats.get('min', 0):.4f} ~ {stats.get('max', 0):.4f}",
            })
        feat_df = pd.DataFrame(feat_detail)
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

        fig_feat = go.Figure()
        fig_feat.add_trace(go.Bar(
            name="输入值",
            x=features,
            y=[input_values.get(f, 0) for f in features],
            marker_color="#3498db",
        ))
        fig_feat.add_trace(go.Bar(
            name="参考均值",
            x=features,
            y=[feat_stats.get(f, {}).get("mean", 0) for f in features],
            marker_color="#bdc3c7",
        ))
        fig_feat.update_layout(
            title="输入值 vs 参考均值",
            barmode="group",
            xaxis_tickangle=-45,
            height=400,
            margin=dict(b=120),
        )
        st.plotly_chart(fig_feat, use_container_width=True)

# ── Tab 4: Cross-gender validation ─────────────────────────────────────
with tab4:
    st.markdown(f"### {INDICATOR_CN[indicator]} — 性别交叉验证结果")

    cross_data = []
    for m in MODELS:
        rid = f"{indicator}_{cutoff}_{m}"
        if rid in metadata:
            p = metadata[rid]["performance"]
            cross_data.append({
                "模型": MODEL_LABELS[m],
                "AUROC [95% CI]": fmt_ci(p.get("full_auroc"), p.get("auroc_ci_lower"), p.get("auroc_ci_upper")),
                "Sens [95% CI]": fmt_ci(p.get("sens_point"), p.get("sens_ci_lower"), p.get("sens_ci_upper")),
                "Spec [95% CI]": fmt_ci(p.get("spec_point"), p.get("spec_ci_lower"), p.get("spec_ci_upper")),
                "M→F AUROC": f"{p['m2f_auroc']:.3f}" if p.get("m2f_auroc") else "—",
                "F→M AUROC": f"{p['f2m_auroc']:.3f}" if p.get("f2m_auroc") else "—",
                "交叉均值": f"{p['cross_avg']:.3f}" if p.get("cross_avg") else "—",
            })

    if cross_data:
        cross_df = pd.DataFrame(cross_data)
        st.dataframe(cross_df, use_container_width=True, hide_index=True)

        fig_cross_bar = go.Figure()
        x_labels = [MODEL_LABELS[m] for m in MODELS]

        full_aucs = [metadata.get(f"{indicator}_{cutoff}_{m}", {}).get("performance", {}).get("full_auroc", 0) for m in MODELS]
        m2f_aucs = [metadata.get(f"{indicator}_{cutoff}_{m}", {}).get("performance", {}).get("m2f_auroc", 0) or 0 for m in MODELS]
        f2m_aucs = [metadata.get(f"{indicator}_{cutoff}_{m}", {}).get("performance", {}).get("f2m_auroc", 0) or 0 for m in MODELS]

        fig_cross_bar.add_trace(go.Bar(name="全队列", x=x_labels, y=full_aucs, marker_color="#4C78A8"))
        fig_cross_bar.add_trace(go.Bar(name="Male→Female", x=x_labels, y=m2f_aucs, marker_color="#F58518"))
        fig_cross_bar.add_trace(go.Bar(name="Female→Male", x=x_labels, y=f2m_aucs, marker_color="#E45756"))

        fig_cross_bar.update_layout(
            barmode="group",
            title=f"{INDICATOR_CN[indicator]} — 性别交叉验证 AUROC 对比",
            yaxis=dict(title="AUROC", range=[0.3, 1.0]),
            height=400,
        )
        fig_cross_bar.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_cross_bar, use_container_width=True)

# ── Tab 5: All results summary (with CI) ────────────────────────────────
with tab5:
    st.markdown("### 全部指标预测结果汇总")

    all_data = []
    for ind in INDICATORS:
        for ct in ["Q", "T"]:
            best_auc = -1
            best_m = None
            for m in MODELS:
                rid = f"{ind}_{ct}_{m}"
                if rid in metadata:
                    auc = metadata[rid]["performance"].get("full_auroc", 0)
                    if auc > best_auc:
                        best_auc = auc
                        best_m = m
            if best_m:
                rid = f"{ind}_{ct}_{best_m}"
                p = metadata[rid]["performance"]
                all_data.append({
                    "指标": f"{INDICATOR_CN[ind]} ({ind})",
                    "分组": "四分位" if ct == "Q" else "三分位",
                    "最佳模型": MODEL_LABELS[best_m],
                    "AUROC [95% CI]": fmt_ci(p.get("full_auroc"), p.get("auroc_ci_lower"), p.get("auroc_ci_upper")),
                    "AUPRC [95% CI]": fmt_ci(p.get("full_auprc"), p.get("auprc_ci_lower"), p.get("auprc_ci_upper")),
                    "Sens [95% CI]": fmt_ci(p.get("sens_point"), p.get("sens_ci_lower"), p.get("sens_ci_upper")),
                    "Spec [95% CI]": fmt_ci(p.get("spec_point"), p.get("spec_ci_lower"), p.get("spec_ci_upper")),
                    "交叉均值": f"{p['cross_avg']:.3f}" if p.get("cross_avg") else "—",
                    "特征数": metadata[rid]["n_features"],
                })

    if all_data:
        all_df = pd.DataFrame(all_data)
        st.dataframe(all_df, use_container_width=True, hide_index=True)

        fig_all = go.Figure()
        q_data = all_df[all_df["分组"] == "四分位"].reset_index(drop=True)

        # Extract numeric AUROC for plotting
        q_aucs = []
        for _, row in q_data.iterrows():
            try:
                q_aucs.append(float(row["AUROC [95% CI]"].split()[0]))
            except (ValueError, IndexError):
                q_aucs.append(0)

        fig_all.add_trace(go.Bar(
            y=q_data["指标"], x=q_aucs,
            orientation="h",
            marker_color="#3498db",
            text=[f"{v:.3f}" for v in q_aucs],
            textposition="outside",
            name="四分位 (Q)",
        ))

        fig_all.update_layout(
            title="各指标最佳模型 AUROC (四分位)",
            xaxis=dict(title="AUROC", range=[0.3, 1.05]),
            height=400,
            margin=dict(l=150),
        )
        fig_all.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig_all.add_vline(x=0.7, line_dash="dot", line_color="green", opacity=0.3)
        st.plotly_chart(fig_all, use_container_width=True)
