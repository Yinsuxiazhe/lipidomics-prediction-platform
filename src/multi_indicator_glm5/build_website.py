"""
Phase 6: Static HTML website generator.
GLM5 execution — 2026-04-10

Generates a single interactive HTML page with:
- Indicator selector
- Cutoff toggle (Q/T)
- Model comparison charts (AUC bars)
- ROC curves
- Cross-gender validation results
- Feature importance tables
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import base64

PROJECT = Path("/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型")
OUT_DIR = PROJECT / "outputs" / "20260410_multi_indicator_glm5"
WEBSITE_DIR = OUT_DIR / "website_v1"

INDICATORS = ["BMI", "weight", "bmi_z", "waistline", "hipline", "WHR", "PBF", "PSM"]
INDICATOR_CN = {
    "BMI": "BMI", "weight": "体重", "bmi_z": "BMI z-score",
    "waistline": "腰围", "hipline": "臀围", "WHR": "腰臀比",
    "PBF": "体脂率", "PSM": "肌肉率",
}
MODELS = ["EN_LR", "XGBoost", "RF", "LR_L2"]
MODEL_LABELS = {"EN_LR": "Elastic Net", "XGBoost": "XGBoost", "RF": "Random Forest", "LR_L2": "LR (L2)"}
MODEL_COLORS = {"EN_LR": "#4C78A8", "XGBoost": "#F58518", "RF": "#E45756", "LR_L2": "#72B7B2"}


def img_to_base64(path):
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_data_json():
    """Build all data as JSON for embedding in HTML."""
    master = pd.read_csv(OUT_DIR / "phase5_master_results.csv")

    # ROC data
    roc_dir = OUT_DIR / "phase3_roc_data"

    # Feature data
    feat_dir = OUT_DIR / "phase2_selected_features"

    data = {}
    for indicator in INDICATORS:
        data[indicator] = {"cn": INDICATOR_CN[indicator], "cutoffs": {}}
        for cutoff in ["Q", "T"]:
            sub = master[(master["indicator"] == indicator) & (master["cutoff"] == cutoff)]
            models_data = []
            for _, row in sub.iterrows():
                model_name = row["model"]
                # ROC data
                roc_file = roc_dir / f"roc_{indicator}_{cutoff}_{model_name}.csv"
                roc_points = []
                if roc_file.exists():
                    roc_df = pd.read_csv(roc_file)
                    roc_points = [{"x": float(r["fpr"]), "y": float(r["tpr"])} for _, r in roc_df.iterrows()]

                # Feature data
                feat_file = feat_dir / f"features_{indicator}_{cutoff}.csv"
                features = []
                if feat_file.exists():
                    ff = pd.read_csv(feat_file)
                    features = [{"name": str(r["feature"]), "imp": float(r["importance"])} for _, r in ff.iterrows()]

                models_data.append({
                    "name": model_name,
                    "label": MODEL_LABELS.get(model_name, model_name),
                    "color": MODEL_COLORS.get(model_name, "#999"),
                    "full_auroc": round(float(row["mean_auroc"]), 3) if not np.isnan(row["mean_auroc"]) else None,
                    "full_std": round(float(row["std_auroc"]), 3) if not np.isnan(row["std_auroc"]) else None,
                    "full_auprc": round(float(row["mean_auprc"]), 3) if not np.isnan(row["mean_auprc"]) else None,
                    "full_sens": round(float(row["mean_sensitivity"]), 3) if not np.isnan(row["mean_sensitivity"]) else None,
                    "full_spec": round(float(row["mean_specificity"]), 3) if not np.isnan(row["mean_specificity"]) else None,
                    "m2f_auroc": round(float(row["m2f_auroc"]), 3) if not np.isnan(row.get("m2f_auroc", np.nan)) else None,
                    "f2m_auroc": round(float(row["f2m_auroc"]), 3) if not np.isnan(row.get("f2m_auroc", np.nan)) else None,
                    "cross_avg": round(float(row["cross_avg_auroc"]), 3) if not np.isnan(row.get("cross_avg_auroc", np.nan)) else None,
                    "n_features": int(row["n_features"]),
                    "is_best": bool(row.get("is_best", False)),
                    "roc": roc_points,
                    "features": features,
                })
            data[indicator]["cutoffs"][cutoff] = models_data

    return json.dumps(data, ensure_ascii=False)


def generate_html(data_json):
    """Generate the full HTML page."""
    heatmap_q_b64 = img_to_base64(OUT_DIR / "phase5_figures" / "heatmap_Q.png")
    heatmap_t_b64 = img_to_base64(OUT_DIR / "phase5_figures" / "heatmap_T.png")
    comparison_b64 = img_to_base64(OUT_DIR / "phase5_figures" / "best_model_comparison.png")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>减重指标脂质组学预测 — 结果展示 [GLM5]</title>
<style>
:root {{
  --bg: #f8f9fa; --card: #fff; --border: #dee2e6; --primary: #2c3e50;
  --accent: #3498db; --good: #27ae60; --warn: #f39c12; --bad: #e74c3c;
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font); background: var(--bg); color: #333; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: #fff; padding: 2rem 1rem; text-align: center; }}
.header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
.header .subtitle {{ opacity: 0.85; font-size: 0.95rem; }}
.header .badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 0.2rem 0.8rem; border-radius: 12px; font-size: 0.8rem; margin-top: 0.5rem; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 1.5rem; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.card h2 {{ font-size: 1.2rem; color: var(--primary); margin-bottom: 1rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }}
.controls {{ display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }}
.controls label {{ font-weight: 600; font-size: 0.9rem; }}
.controls select, .controls button {{ padding: 0.5rem 1rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.9rem; }}
.controls button.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
.controls button {{ background: #fff; cursor: pointer; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
th, td {{ padding: 0.6rem 0.8rem; text-align: center; border-bottom: 1px solid #eee; }}
th {{ background: #f1f3f5; font-weight: 600; }}
td.left {{ text-align: left; }}
.best {{ background: #e8f5e9; font-weight: 700; }}
.auc-good {{ color: var(--good); font-weight: 700; }}
.auc-warn {{ color: var(--warn); }}
.auc-bad {{ color: var(--bad); }}
.roc-container {{ position: relative; width: 100%; max-width: 600px; }}
canvas {{ width: 100%; height: auto; }}
.figures-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
.figures-grid img {{ width: 100%; border-radius: 4px; }}
.footer {{ text-align: center; padding: 2rem; color: #999; font-size: 0.8rem; }}
.feature-list {{ columns: 2; column-gap: 1rem; font-size: 0.82rem; }}
.feature-list li {{ margin-bottom: 0.2rem; }}
.legend {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
.legend-item {{ display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
@media (max-width: 768px) {{
  .figures-grid {{ grid-template-columns: 1fr; }}
  .feature-list {{ columns: 1; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>减重指标基线脂质组学预测结果</h1>
  <div class="subtitle">8 减重指标 × 4 ML 模型 × 2 分组策略 | Strict Nested CV + 性别交叉验证</div>
  <div class="badge">GLM5 | 2026-04-10 | n=281</div>
</div>

<div class="container">

  <!-- Overview Figures -->
  <div class="card">
    <h2>总览：AUROC 热力图与最佳模型对比</h2>
    <div class="figures-grid">
      <img src="data:image/png;base64,{heatmap_q_b64}" alt="Heatmap Q">
      <img src="data:image/png;base64,{heatmap_t_b64}" alt="Heatmap T">
    </div>
    <div style="margin-top:1rem;">
      <img src="data:image/png;base64,{comparison_b64}" alt="Best model comparison" style="width:100%;border-radius:4px;">
    </div>
  </div>

  <!-- Interactive Detail -->
  <div class="card">
    <h2>详细结果 — 选择指标与分组策略</h2>
    <div class="controls">
      <label>指标：</label>
      <select id="indicatorSelect" onchange="update()">
        {"".join(f'<option value="{i}">{INDICATOR_CN[i]} ({i})</option>' for i in INDICATORS)}
      </select>
      <label>分组：</label>
      <button id="btnQ" class="active" onclick="setCutoff('Q')">四分位 (Q)</button>
      <button id="btnT" onclick="setCutoff('T')">三分位 (T)</button>
    </div>
    <div class="legend">
      {"".join(f'<div class="legend-item"><div class="legend-dot" style="background:{c}"></div>{MODEL_LABELS[m]}</div>' for m, c in MODEL_COLORS.items())}
    </div>
    <div id="resultTable"></div>
  </div>

  <!-- ROC Curves -->
  <div class="card">
    <h2>ROC 曲线</h2>
    <div class="roc-container">
      <canvas id="rocCanvas" width="600" height="600"></canvas>
    </div>
  </div>

  <!-- Features -->
  <div class="card">
    <h2>关键脂质特征</h2>
    <div id="featureList"></div>
  </div>

</div>

<div class="footer">
  需求方：Shuxian Zhang | 分析提供方：Chenyu Fan | 参考：Chen et al., Cell Reports Medicine (2026)<br>
  本页面由 GLM5 自动生成
</div>

<script>
const DATA = {data_json};
let currentCutoff = 'Q';

function setCutoff(c) {{
  currentCutoff = c;
  document.getElementById('btnQ').className = c === 'Q' ? 'active' : '';
  document.getElementById('btnT').className = c === 'T' ? 'active' : '';
  update();
}}

function aucClass(v) {{
  if (v === null) return '';
  if (v >= 0.8) return 'auc-good';
  if (v >= 0.65) return 'auc-warn';
  return 'auc-bad';
}}

function update() {{
  const ind = document.getElementById('indicatorSelect').value;
  const d = DATA[ind].cutoffs[currentCutoff];

  // Table
  let html = '<table><tr><th>模型</th><th>全队列 AUROC</th><th>AUPRC</th><th>Sens</th><th>Spec</th><th>M→F AUROC</th><th>F→M AUROC</th><th>交叉均值</th><th>特征数</th></tr>';
  d.forEach(m => {{
    const bestClass = m.is_best ? ' class="best"' : '';
    html += `<tr${{bestClass}}>`;
    html += `<td>${{m.label}}${{m.is_best ? ' ★' : ''}}</td>`;
    html += `<td class="${{aucClass(m.full_auroc)}}">${{m.full_auroc !== null ? m.full_auroc.toFixed(3) + '±' + m.full_std.toFixed(3) : '—'}}</td>`;
    html += `<td class="${{aucClass(m.full_auprc)}}">${{m.full_auprc !== null ? m.full_auprc.toFixed(3) : '—'}}</td>`;
    html += `<td>${{m.full_sens !== null ? m.full_sens.toFixed(3) : '—'}}</td>`;
    html += `<td>${{m.full_spec !== null ? m.full_spec.toFixed(3) : '—'}}</td>`;
    html += `<td class="${{aucClass(m.m2f_auroc)}}">${{m.m2f_auroc !== null ? m.m2f_auroc.toFixed(3) : '—'}}</td>`;
    html += `<td class="${{aucClass(m.f2m_auroc)}}">${{m.f2m_auroc !== null ? m.f2m_auroc.toFixed(3) : '—'}}</td>`;
    html += `<td class="${{aucClass(m.cross_avg)}}">${{m.cross_avg !== null ? m.cross_avg.toFixed(3) : '—'}}</td>`;
    html += `<td>${{m.n_features}}</td></tr>`;
  }});
  html += '</table>';
  document.getElementById('resultTable').innerHTML = html;

  // ROC
  drawROC(d);

  // Features (from best model)
  const best = d.find(m => m.is_best) || d[0];
  let fhtml = '<p style="margin-bottom:0.5rem;font-weight:600;">最佳模型：' + best.label + ' (' + best.n_features + ' 个脂质特征)</p>';
  fhtml += '<ul class="feature-list">';
  best.features.forEach(f => fhtml += `<li>${{f.name}} <span style="color:#999;">(importance: ${{f.imp.toFixed(4)}})</span></li>`);
  fhtml += '</ul>';
  document.getElementById('featureList').innerHTML = fhtml;
}}

function drawROC(models) {{
  const canvas = document.getElementById('rocCanvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const pad = 60;
  ctx.clearRect(0, 0, W, H);

  // Axes
  ctx.strokeStyle = '#333'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, pad); ctx.lineTo(pad, H-pad); ctx.lineTo(W-pad, H-pad); ctx.stroke();

  // Grid
  ctx.strokeStyle = '#eee'; ctx.lineWidth = 0.5;
  for (let i = 0; i <= 10; i++) {{
    const x = pad + (W-2*pad)*i/10, y = pad + (H-2*pad)*i/10;
    ctx.beginPath(); ctx.moveTo(x, H-pad); ctx.lineTo(x, pad); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(W-pad, y); ctx.stroke();
  }}

  // Diagonal
  ctx.strokeStyle = '#ccc'; ctx.lineWidth = 1; ctx.setLineDash([4,4]);
  ctx.beginPath(); ctx.moveTo(pad, H-pad); ctx.lineTo(W-pad, pad); ctx.stroke();
  ctx.setLineDash([]);

  // Labels
  ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center';
  ctx.fillText('False Positive Rate', W/2, H-10);
  ctx.save(); ctx.translate(15, H/2); ctx.rotate(-Math.PI/2); ctx.fillText('True Positive Rate', 0, 0); ctx.restore();
  for (let i = 0; i <= 10; i += 2) {{
    ctx.fillText((i/10).toFixed(1), pad + (W-2*pad)*i/10, H-pad+18);
    ctx.textAlign = 'right'; ctx.fillText((1-i/10).toFixed(1), pad-8, pad + (H-2*pad)*i/10 + 4); ctx.textAlign = 'center';
  }}

  // Curves
  models.forEach(m => {{
    if (!m.roc || m.roc.length < 2) return;
    ctx.strokeStyle = m.color; ctx.lineWidth = 2;
    ctx.beginPath();
    m.roc.forEach((p, i) => {{
      const x = pad + p.x * (W-2*pad), y = H - pad - p.y * (H-2*pad);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }});
    ctx.stroke();
    // Label
    if (m.full_auroc !== null) {{
      const lp = m.roc[Math.min(30, m.roc.length-1)];
      ctx.fillStyle = m.color; ctx.font = 'bold 11px sans-serif';
      ctx.fillText(m.label + ' ' + m.full_auroc.toFixed(3), pad + lp.x*(W-2*pad) + 5, H - pad - lp.y*(H-2*pad) - 5);
    }}
  }});
}}

update();
</script>
</body>
</html>"""
    return html


def main():
    WEBSITE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 6: Static HTML Website  [GLM5]")
    print("=" * 60)

    print("\n[1/2] Building data JSON ...")
    data_json = build_data_json()
    print(f"  {len(data_json)} chars")

    print("[2/2] Generating HTML ...")
    html = generate_html(data_json)
    output = WEBSITE_DIR / "index.html"
    output.write_text(html, encoding="utf-8")
    print(f"  saved: {output}")

    # Also copy figures
    import shutil
    assets_dir = WEBSITE_DIR / "assets"
    assets_dir.mkdir(exist_ok=True)
    for f in (OUT_DIR / "phase5_figures").glob("*"):
        shutil.copy2(f, assets_dir / f.name)
    print(f"  copied figures to assets/")

    print("\n" + "=" * 60)
    print("Phase 6 complete. [GLM5]")
    print(f"Website: {WEBSITE_DIR}/index.html")
    print("=" * 60)


if __name__ == "__main__":
    main()
