from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

ROOT = Path(__file__).resolve().parent.parent
RESULT_DIR = ROOT / '01_主图与主结果'
OUT_DIR = Path(__file__).resolve().parent

name_map = {
    'clinical_slim_logistic': 'Clinical baseline',
    'clinical_full_elastic_net': 'Expanded clinical',
    'lipid_elastic_net': 'Lipid-only',
    'fusion_elastic_net': 'Clinical + lipid fusion',
    'fusion_full_elastic_net': 'Expanded fusion',
}
color_map = {
    'Clinical baseline': '#4C78A8',
    'Expanded clinical': '#9ECAE9',
    'Lipid-only': '#F58518',
    'Clinical + lipid fusion': '#54A24B',
    'Expanded fusion': '#B279A2',
}

perf = pd.read_csv(RESULT_DIR / 'performance_summary.csv')
fold = pd.read_csv(RESULT_DIR / 'fold_metrics.csv')
perf['model'] = perf['experiment'].map(name_map).fillna(perf['experiment'])
feat = fold.groupby('experiment')['selected_feature_count'].agg(['min','max','mean']).reset_index()
perf = perf.merge(feat, on='experiment', how='left')
perf['gap'] = perf['mean_train_auc'] - perf['mean_auc']
order = ['Clinical baseline', 'Expanded clinical', 'Lipid-only', 'Clinical + lipid fusion', 'Expanded fusion']
perf['model'] = pd.Categorical(perf['model'], categories=order, ordered=True)
perf = perf.sort_values('model').reset_index(drop=True)

# 1) grouped horizontal bar
fig, ax = plt.subplots(figsize=(10, 5.8))
y = range(len(perf))
bar_h = 0.36
ax.barh([i + bar_h/2 for i in y], perf['mean_train_auc'], height=bar_h, color='#F39B7F', label='训练 AUC')
ax.barh([i - bar_h/2 for i in y], perf['mean_auc'], height=bar_h, color='#3C5488', label='外层测试 AUC')
for i, row in perf.iterrows():
    ax.text(row['mean_train_auc'] + 0.005, i + bar_h/2, f"{row['mean_train_auc']:.3f}", va='center', fontsize=9)
    ax.text(row['mean_auc'] + 0.005, i - bar_h/2, f"{row['mean_auc']:.3f}", va='center', fontsize=9)
    ax.text(max(row['mean_train_auc'], row['mean_auc']) + 0.07, i, f"差值 {row['gap']:.3f}", va='center', fontsize=9, color='#7A1F1F')
ax.set_yticks(list(y))
ax.set_yticklabels(perf['model'])
ax.set_xlim(0.35, 1.0)
ax.set_xlabel('AUC')
ax.set_title('主模型训练 AUC 与外层测试 AUC 对照')
ax.legend(frameon=False, loc='lower right')
ax.grid(axis='x', alpha=0.25)
ax.set_axisbelow(True)
plt.tight_layout()
fig.savefig(OUT_DIR / '20260311_训练AUC_vs_外层测试AUC_条形图.png', bbox_inches='tight')
fig.savefig(OUT_DIR / '20260311_训练AUC_vs_外层测试AUC_条形图.pdf', bbox_inches='tight')
plt.close(fig)

# 2) dumbbell plot
fig, ax = plt.subplots(figsize=(10, 5.8))
for i, row in perf.iterrows():
    y0 = i
    ax.plot([row['mean_auc'], row['mean_train_auc']], [y0, y0], color='#B0B0B0', linewidth=2.5, zorder=1)
    ax.scatter(row['mean_auc'], y0, s=85, color='#3C5488', zorder=3)
    ax.scatter(row['mean_train_auc'], y0, s=85, color='#F39B7F', zorder=3)
    ax.text(row['mean_train_auc'] + 0.008, y0 + 0.10, f"训练 {row['mean_train_auc']:.3f}", fontsize=9, color='#A14A28')
    ax.text(row['mean_auc'] + 0.008, y0 - 0.22, f"测试 {row['mean_auc']:.3f}", fontsize=9, color='#223D73')
ax.set_yticks(range(len(perf)))
ax.set_yticklabels(perf['model'])
ax.set_xlim(0.35, 1.0)
ax.set_xlabel('AUC')
ax.set_title('主模型泛化差距（训练 AUC 与测试 AUC 连线图）')
ax.grid(axis='x', alpha=0.25)
ax.set_axisbelow(True)
ax.legend(handles=[
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#F39B7F', markersize=9, label='训练 AUC'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#3C5488', markersize=9, label='外层测试 AUC'),
], frameon=False, loc='lower right')
plt.tight_layout()
fig.savefig(OUT_DIR / '20260311_泛化差距_dumbbell图.png', bbox_inches='tight')
fig.savefig(OUT_DIR / '20260311_泛化差距_dumbbell图.pdf', bbox_inches='tight')
plt.close(fig)

# 3) bubble plot gap vs mean_auc with feature count
fig, ax = plt.subplots(figsize=(8.8, 6.6))
size = perf['mean'] * 18
for _, row in perf.iterrows():
    c = color_map[str(row['model'])]
    ax.scatter(row['mean_auc'], row['gap'], s=size[perf.index[perf['model'] == row['model']][0]], color=c, alpha=0.75, edgecolors='white', linewidth=1.2)
    feature_label = f"{int(row['min'])}-{int(row['max'])}" if row['min'] != row['max'] else f"{int(row['min'])}"
    ax.text(row['mean_auc'] + 0.002, row['gap'] + 0.004, f"{row['model']}\n特征数 {feature_label}", fontsize=9)
ax.axhline(0.1, linestyle='--', color='#999999', linewidth=1, alpha=0.8)
ax.set_xlabel('外层测试 mean AUC')
ax.set_ylabel('训练-测试 AUC 差值')
ax.set_title('模型复杂度、外层测试 AUC 与泛化差距关系')
ax.grid(alpha=0.25)
plt.tight_layout()
fig.savefig(OUT_DIR / '20260311_AUC差值_vs_特征规模_气泡图.png', bbox_inches='tight')
fig.savefig(OUT_DIR / '20260311_AUC差值_vs_特征规模_气泡图.pdf', bbox_inches='tight')
plt.close(fig)

# 4) combined figure
fig, axes = plt.subplots(2, 2, figsize=(15, 11))
# A bar
ax = axes[0,0]
y = range(len(perf))
bar_h = 0.36
ax.barh([i + bar_h/2 for i in y], perf['mean_train_auc'], height=bar_h, color='#F39B7F', label='训练 AUC')
ax.barh([i - bar_h/2 for i in y], perf['mean_auc'], height=bar_h, color='#3C5488', label='外层测试 AUC')
ax.set_yticks(list(y)); ax.set_yticklabels(perf['model']); ax.set_xlim(0.35, 1.0); ax.set_xlabel('AUC'); ax.set_title('A. 训练 vs 外层测试')
ax.grid(axis='x', alpha=0.25); ax.legend(frameon=False, loc='lower right')
# B dumbbell
ax = axes[0,1]
for i, row in perf.iterrows():
    ax.plot([row['mean_auc'], row['mean_train_auc']], [i, i], color='#B0B0B0', linewidth=2.5)
    ax.scatter(row['mean_auc'], i, s=70, color='#3C5488')
    ax.scatter(row['mean_train_auc'], i, s=70, color='#F39B7F')
ax.set_yticks(range(len(perf))); ax.set_yticklabels(perf['model']); ax.set_xlim(0.35, 1.0); ax.set_xlabel('AUC'); ax.set_title('B. 泛化差距')
ax.grid(axis='x', alpha=0.25)
# C bubble
ax = axes[1,0]
for idx, row in perf.iterrows():
    c = color_map[str(row['model'])]
    ax.scatter(row['mean_auc'], row['gap'], s=row['mean'] * 18, color=c, alpha=0.75, edgecolors='white', linewidth=1.2)
    ax.text(row['mean_auc'] + 0.002, row['gap'] + 0.004, str(row['model']), fontsize=8.5)
ax.axhline(0.1, linestyle='--', color='#999999', linewidth=1, alpha=0.8)
ax.set_xlabel('外层测试 mean AUC'); ax.set_ylabel('训练-测试 AUC 差值'); ax.set_title('C. 差值与特征规模'); ax.grid(alpha=0.25)
# D gap rank
ax = axes[1,1]
gap_df = perf.sort_values('gap', ascending=True)
ax.barh(gap_df['model'], gap_df['gap'], color=[color_map[m] for m in gap_df['model']])
for i, v in enumerate(gap_df['gap']):
    ax.text(v + 0.005, i, f"{v:.3f}", va='center', fontsize=9)
ax.set_xlabel('训练-测试 AUC 差值'); ax.set_title('D. 哪些模型更容易过拟合')
ax.grid(axis='x', alpha=0.25)
plt.tight_layout()
fig.savefig(OUT_DIR / '20260311_训练AUC与泛化差距_组合图.png', bbox_inches='tight')
fig.savefig(OUT_DIR / '20260311_训练AUC与泛化差距_组合图.pdf', bbox_inches='tight')
plt.close(fig)

print('done')
