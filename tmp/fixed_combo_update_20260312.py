from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from bs4 import BeautifulSoup

from run_pipeline import load_pipeline_config
from src.data.build_cohort import build_analysis_cohorts
from src.followup.outphase_validation import (
    _run_outphase_fixed_group_split,
    _summarize_rows as summarize_outphase_rows,
    _write_outphase_report,
    build_outphase_analysis_cohorts,
)
from src.followup.school_split import load_school_mapping, resolve_fixed_group_split, resolve_group_series
from src.followup.self_validation import _run_fixed_group_split, _summarize_rows as summarize_self_rows
from src.io.load_data import load_project_tables
from src.models.run_nested_cv import _merge_cv_config, build_default_experiment_registry

OUTPUT_ROOT = ROOT / 'outputs' / '20260311_responder_followup'
TEACHER_DIR = OUTPUT_ROOT / 'teacher_report_package'
TEMPLATE_HTML = TEACHER_DIR / '03_literature_followup_note.html'
CONFIG_PATH = ROOT / 'config' / 'analysis.yaml'

SCHEMES: dict[str, dict[str, Any]] = {
    'A_5train_2test_balanced_rate': {
        'scheme_id': 'A_5train_2test_balanced_rate',
        'display_name': '方案 A：5 校区 train + 2 校区 test',
        'train_schools': ['中关村', '冷泉', '唐家岭校区', '本部', '百旺'],
        'test_groups': ['六里屯', '华清校区'],
        'output_dir': OUTPUT_ROOT / 'fixed_school_combo_balanced_5train2test',
        'split_label': 'balanced_5train2test_balanced_rate',
        'role': 'sensitivity',
    },
    'B_4train_3test_all_intensity': {
        'scheme_id': 'B_4train_3test_all_intensity',
        'display_name': '方案 B：4 校区 train + 3 校区 test',
        'train_schools': ['六里屯', '冷泉', '本部', '百旺'],
        'test_groups': ['中关村', '华清校区', '唐家岭校区'],
        'output_dir': OUTPUT_ROOT / 'fixed_school_combo_balanced_4train3test',
        'split_label': 'balanced_4train3test_all_intensity',
        'role': 'selected',
    },
}


def fmt_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '（空）'
    printable = frame.copy()
    for column in printable.columns:
        printable[column] = printable[column].map(
            lambda value: f'{value:.4f}' if isinstance(value, float) and pd.notna(value) else value
        )
    headers = [str(column) for column in printable.columns]
    rows = printable.astype(object).where(pd.notna(printable), '').values.tolist()
    header_line = '| ' + ' | '.join(headers) + ' |'
    separator_line = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
    body_lines = ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows]
    return '\n'.join([header_line, separator_line, *body_lines])


def compute_scheme_design(group_frame: pd.DataFrame, mapping_path: str, mapping_sheet: str) -> pd.DataFrame:
    mapping = load_school_mapping(mapping_path, sheet_name=mapping_sheet)
    group = group_frame[['ID', 'Group']].copy()
    group['ID'] = group['ID'].astype(str)
    merged = group.merge(mapping, on='ID', how='inner')
    merged['is_response'] = merged['Group'].astype(str).eq('response').astype(int)
    school_summary = (
        merged.groupby('school', dropna=False)
        .agg(
            baseline_n=('ID', 'size'),
            response_n=('is_response', 'sum'),
            intensity=('intensity', lambda s: ' | '.join(sorted(set(map(str, s.dropna()))))),
        )
        .reset_index()
    )
    school_summary['noresponse_n'] = school_summary['baseline_n'] - school_summary['response_n']
    school_summary['response_rate'] = school_summary['response_n'] / school_summary['baseline_n']

    rows = []
    for scheme in SCHEMES.values():
        test_schools = set(map(str, scheme['test_groups']))
        train_schools = school_summary.loc[~school_summary['school'].isin(test_schools)].copy()
        test_schools_frame = school_summary.loc[school_summary['school'].isin(test_schools)].copy()
        rows.append(
            {
                'scheme': scheme['scheme_id'],
                'train_schools': '、'.join(scheme['train_schools']),
                'test_schools': '、'.join(scheme['test_groups']),
                'train_n': int(train_schools['baseline_n'].sum()),
                'test_n': int(test_schools_frame['baseline_n'].sum()),
                'train_response_rate': float(train_schools['response_n'].sum() / train_schools['baseline_n'].sum()),
                'test_response_rate': float(test_schools_frame['response_n'].sum() / test_schools_frame['baseline_n'].sum()),
                'abs_response_rate_gap': float(
                    abs(
                        train_schools['response_n'].sum() / train_schools['baseline_n'].sum()
                        - test_schools_frame['response_n'].sum() / test_schools_frame['baseline_n'].sum()
                    )
                ),
                'train_intensity_count': int(train_schools['intensity'].nunique()),
                'test_intensity_count': int(test_schools_frame['intensity'].nunique()),
                'recommended': 'selected' if scheme['role'] == 'selected' else 'sensitivity',
            }
        )
    return pd.DataFrame(rows)


def run_fixed_only_analyses(config: dict[str, Any], scheme_key: str) -> None:
    scheme = SCHEMES[scheme_key]
    output_dir = Path(scheme['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = config['paths']
    raw_tables = load_project_tables(
        group_path=paths['group'],
        lipid_path=paths['lipid'],
        clinical_full_path=paths['clinical_full'],
        clinical_slim_path=paths['clinical_slim'],
    )
    cohorts = build_analysis_cohorts(raw_tables)
    positive_label = config.get('target', {}).get('positive_label', 'response')
    model_configs = config['followup']['models']
    self_cfg = config['followup']['self_validation']
    out_cfg = config['followup']['outphase_validation']

    registry = build_default_experiment_registry()
    self_global_cv = _merge_cv_config(self_cfg.get('cv_config'))
    out_global_cv = _merge_cv_config(out_cfg.get('cv_config'))

    self_rows: list[dict[str, Any]] = []
    exported_mapping_frame: pd.DataFrame | None = None
    for model_config in model_configs:
        experiment = model_config['experiment']
        model_label = model_config['model_label']
        spec = registry[experiment]
        frame = getattr(cohorts, spec.cohort_key)
        cv_config = self_global_cv.copy()
        cv_config.update(model_config.get('cv_overrides') or {})
        group_values, group_meta = resolve_group_series(
            frame,
            group_by=str(self_cfg['pseudo_external'].get('group_by', 'school')),
            mapping_path=self_cfg['pseudo_external'].get('mapping_path'),
            mapping_sheet_name=str(self_cfg['pseudo_external'].get('mapping_sheet_name') or '运动强度分组_401人'),
        )
        if exported_mapping_frame is None:
            exported_mapping_frame = group_meta.get('mapping_frame')
        fixed_meta = resolve_fixed_group_split(
            group_values,
            group_meta=group_meta,
            fixed_group_split_config={
                'enabled': True,
                'test_groups': scheme['test_groups'],
                'split_label': scheme['split_label'],
            },
        )
        self_rows.extend(
            _run_fixed_group_split(
                frame=frame,
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                group_values=group_values,
                validation_scheme=str(fixed_meta['validation_scheme']),
                test_groups=list(fixed_meta['test_groups']),
                holdout_group_label=str(fixed_meta['holdout_group_label']),
                split_label=str(fixed_meta['split_label']),
            )
        )

    self_folds = pd.DataFrame(self_rows)
    self_summary = summarize_self_rows(self_folds)
    self_folds.to_csv(output_dir / 'self_validation_fold_metrics.csv', index=False)
    self_summary.to_csv(output_dir / 'self_validation_summary.csv', index=False)
    if exported_mapping_frame is not None:
        exported_mapping_frame.to_csv(output_dir / 'id_school_intensity_mapping.csv', index=False)

    outphase_cohorts, metadata = build_outphase_analysis_cohorts(
        group_frame=raw_tables.group,
        out_lipid_path=out_cfg['out_lipid_path'],
        out_clinical_full_path=out_cfg['out_clinical_full_path'],
        clinical_anchor_mapping=out_cfg.get('clinical_anchor_mapping'),
    )
    out_rows: list[dict[str, Any]] = []
    grouped_validation_note = (
        '本轮固定校区组合 split 仍属于内部 grouped validation / internal temporal validation，不是 external validation。'
    )
    for model_config in model_configs:
        experiment = model_config['experiment']
        model_label = model_config['model_label']
        spec = registry[experiment]
        baseline_frame = getattr(cohorts, spec.cohort_key)
        outphase_frame = getattr(outphase_cohorts, spec.cohort_key)
        cv_config = out_global_cv.copy()
        cv_config.update(model_config.get('cv_overrides') or {})
        group_values, group_meta = resolve_group_series(
            baseline_frame,
            group_by=str(out_cfg['pseudo_external'].get('group_by', 'school')),
            mapping_path=out_cfg['pseudo_external'].get('mapping_path'),
            mapping_sheet_name=str(out_cfg['pseudo_external'].get('mapping_sheet_name') or '运动强度分组_401人'),
        )
        fixed_meta = resolve_fixed_group_split(
            group_values,
            group_meta=group_meta,
            fixed_group_split_config={
                'enabled': True,
                'test_groups': scheme['test_groups'],
                'split_label': scheme['split_label'],
            },
        )
        out_rows.extend(
            _run_outphase_fixed_group_split(
                baseline_frame=baseline_frame,
                outphase_frame=outphase_frame,
                spec=spec,
                experiment=experiment,
                model_label=model_label,
                positive_label=positive_label,
                cv_config=cv_config,
                group_values=group_values,
                validation_scheme=f"outphase_{fixed_meta['validation_scheme']}",
                test_groups=list(fixed_meta['test_groups']),
                holdout_group_label=str(fixed_meta['holdout_group_label']),
                split_label=str(fixed_meta['split_label']),
            )
        )

    out_folds = pd.DataFrame(out_rows)
    out_summary = summarize_outphase_rows(out_folds)
    out_folds.to_csv(output_dir / 'outphase_validation_fold_metrics.csv', index=False)
    out_summary.to_csv(output_dir / 'outphase_validation_summary.csv', index=False)
    _write_outphase_report(
        output_dir=output_dir,
        summary=out_summary,
        metadata=metadata,
        grouped_validation_note=grouped_validation_note,
    )


def load_fixed_scheme_rows(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    self_summary = pd.read_csv(output_dir / 'self_validation_summary.csv')
    out_summary = pd.read_csv(output_dir / 'outphase_validation_summary.csv')
    self_folds = pd.read_csv(output_dir / 'self_validation_fold_metrics.csv')
    out_folds = pd.read_csv(output_dir / 'outphase_validation_fold_metrics.csv')
    return (
        self_summary[self_summary['validation_scheme'] == 'fixed_school_combo_holdout'].reset_index(drop=True),
        out_summary[out_summary['validation_scheme'] == 'outphase_fixed_school_combo_holdout'].reset_index(drop=True),
        self_folds[self_folds['validation_scheme'] == 'fixed_school_combo_holdout'].reset_index(drop=True),
        out_folds[out_folds['validation_scheme'] == 'outphase_fixed_school_combo_holdout'].reset_index(drop=True),
    )


def write_scheme_a_summary(design_df: pd.DataFrame) -> None:
    scheme = SCHEMES['A_5train_2test_balanced_rate']
    output_dir = Path(scheme['output_dir'])
    self_summary, out_summary, self_folds, out_folds = load_fixed_scheme_rows(output_dir)
    comparison_table = design_df.copy()
    selected_row = comparison_table.loc[comparison_table['scheme'] == scheme['scheme_id']].iloc[0]
    lines = [
        '# 固定校区组合 split 结果（方案 A / sensitivity）',
        '',
        '> 本目录对应 5 校区 train + 2 校区 test 的 sensitivity analysis，独立于主 follow-up 输出，不覆盖 strict nested CV 主锚点。',
        '',
        '## 实施方案',
        '',
        f"- train schools：{selected_row['train_schools']}",
        f"- test schools：{selected_row['test_schools']}",
        f"- train_n={int(selected_row['train_n'])}，test_n={int(selected_row['test_n'])}",
        f"- train_response_rate={selected_row['train_response_rate']:.4f}，test_response_rate={selected_row['test_response_rate']:.4f}",
        f"- abs_response_rate_gap={selected_row['abs_response_rate_gap']:.4f}",
        f"- train/test intensity 覆盖：{int(selected_row['train_intensity_count'])} / {int(selected_row['test_intensity_count'])}",
        '',
        '## 候选方案对比',
        '',
        fmt_markdown_table(comparison_table),
        '',
        '## self-validation 固定校区组合结果',
        '',
        fmt_markdown_table(self_summary[['experiment','model_label','validation_scheme','n_total_splits','n_completed','mean_auc','mean_train_auc','mean_gap']]),
        '',
        '## out-phase 固定校区组合结果',
        '',
        fmt_markdown_table(out_summary[['experiment','model_label','validation_scheme','n_total_splits','n_completed','mean_auc','mean_train_auc','mean_gap']]),
        '',
        '## split 级别明细',
        '',
        '### self-validation fold',
        '',
        fmt_markdown_table(self_folds[['experiment','model_label','validation_scheme','split_id','holdout_group','status','auc','train_auc','n_train','n_test']]),
        '',
        '### out-phase fold',
        '',
        fmt_markdown_table(out_folds[['experiment','model_label','validation_scheme','split_id','holdout_group','status','auc','train_auc','n_train','n_test']]),
        '',
        '## sensitivity interpretation',
        '',
        '- 方案 A 的价值在于 response rate 更平衡，适合作为 sensitivity analysis。',
        '- 若方案 A 与方案 B 都没有把 AUC 提升到新的量级，则可以更稳妥地说明：当前跨校区泛化结论整体仍偏弱。',
        '- 本 fixed school combo split、leave-one-school-out、repeated hold-out、out-phase fixed school combo 都不是 external validation。',
        '',
        '## 口径边界',
        '',
        '- 正式主结果仍是 strict nested CV outer-test AUC 约 0.50–0.54。',
        '- AUC≈0.8 仅对应 strict nested CV 中的 mean_train_auc。',
        '- 本固定校区组合 split 仍属于 internal grouped validation / internal temporal validation。',
    ]
    (output_dir / 'fixed_school_combo_summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def build_comparison_outputs(design_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    rows = []
    for scheme_key, scheme in SCHEMES.items():
        output_dir = Path(scheme['output_dir'])
        self_summary, out_summary, _, _ = load_fixed_scheme_rows(output_dir)
        meta = design_df.loc[design_df['scheme'] == scheme_key].iloc[0]
        for stage_label, frame in [('self_validation', self_summary), ('outphase', out_summary)]:
            for _, row in frame.iterrows():
                rows.append(
                    {
                        'scheme': scheme_key,
                        'scheme_role': scheme['role'],
                        'stage': stage_label,
                        'train_schools': meta['train_schools'],
                        'test_schools': meta['test_schools'],
                        'train_n': int(meta['train_n']),
                        'test_n': int(meta['test_n']),
                        'train_response_rate': float(meta['train_response_rate']),
                        'test_response_rate': float(meta['test_response_rate']),
                        'abs_response_rate_gap': float(meta['abs_response_rate_gap']),
                        'train_intensity_count': int(meta['train_intensity_count']),
                        'test_intensity_count': int(meta['test_intensity_count']),
                        'experiment': row['experiment'],
                        'model_label': row['model_label'],
                        'validation_scheme': row['validation_scheme'],
                        'mean_auc': float(row['mean_auc']),
                        'mean_train_auc': float(row['mean_train_auc']),
                        'mean_gap': float(row['mean_gap']),
                    }
                )
    frame = pd.DataFrame(rows).sort_values(['scheme','stage','model_label']).reset_index(drop=True)
    comparison_csv = OUTPUT_ROOT / 'fixed_school_combo_result_comparison.csv'
    frame.to_csv(comparison_csv, index=False)

    lines = [
        '# 固定校区组合 split 对比（A sensitivity vs B selected）',
        '',
        '## 方案设计总览',
        '',
        fmt_markdown_table(design_df),
        '',
        '## 结果对比',
        '',
        fmt_markdown_table(frame),
        '',
        '## 一句话结论',
        '',
        '- 方案 B 仍更适合作为主固定校区组合版 split，因为 train/test 两侧都覆盖 3 种 intensity，且 test 样本量更大。',
        '- 方案 A 作为 sensitivity analysis 的补跑结果，可用于说明：即便选更平衡的 response-rate 组合，结论边界也没有根本改变。',
        '- 两个方案都仍属于 internal grouped validation / internal temporal validation，不是 external validation。',
    ]
    comparison_md = OUTPUT_ROOT / 'fixed_school_combo_scheme_comparison.md'
    comparison_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return frame, lines[-3]


def copy_teacher_support_files(design_df: pd.DataFrame, comparison_frame: pd.DataFrame) -> None:
    design_md = OUTPUT_ROOT / 'fixed_school_combo_design.md'
    if design_md.exists():
        shutil.copy2(design_md, TEACHER_DIR / 'fixed_school_combo_design.md')
    comparison_frame.to_csv(TEACHER_DIR / 'fixed_school_combo_result_comparison.csv', index=False)
    design_df.to_csv(TEACHER_DIR / 'fixed_school_combo_scheme_design.csv', index=False)


def render_markdown_into_template(
    md_path: Path,
    html_path: Path,
    *,
    page_title: str,
    badge: str,
    hero_title: str,
    subtitle: str,
    meta_items: list[tuple[str, str]],
    nav_links: list[tuple[str, str]],
    footer_links: list[tuple[str, str]],
    footer_note: str,
) -> None:
    soup = BeautifulSoup(TEMPLATE_HTML.read_text(encoding='utf-8'), 'html.parser')
    soup.title.string = page_title
    hero = soup.select_one('.hero')
    hero.select_one('.badge').string = badge
    hero.find('h1').string = hero_title
    hero.select_one('.subtitle').string = subtitle

    meta_row = hero.select_one('.meta-row')
    meta_row.clear()
    for text, kind in meta_items:
        cls = 'meta-pill' if kind == 'pill' else 'path-chip'
        span = soup.new_tag('span', attrs={'class': cls})
        span.string = text
        meta_row.append(span)

    nav_row = hero.select_one('.nav-row.doc-toolbar')
    nav_row.clear()
    for label, href in nav_links:
        a = soup.new_tag('a', href=href, attrs={'class': 'nav-link'})
        a.string = label
        nav_row.append(a)

    rendered = subprocess.check_output(['pandoc', '-f', 'gfm', '-t', 'html5', str(md_path)], text=True)
    rendered_soup = BeautifulSoup(rendered, 'html.parser')
    main = soup.select_one('main.content')
    main.clear()
    for child in list(rendered_soup.contents):
        if getattr(child, 'name', None) is None and not str(child).strip():
            continue
        main.append(child)

    toc_list = soup.select_one('.sidebar-toc-list')
    toc_list.clear()
    for heading in main.find_all(['h2', 'h3']):
        target = heading.get('id')
        if not target:
            continue
        li = soup.new_tag('li', attrs={'class': 'sidebar-toc-item'})
        a_classes = 'sidebar-toc-link sub-item' if heading.name == 'h3' else 'sidebar-toc-link'
        a = soup.new_tag('a', href=f'#{target}', attrs={'class': a_classes, 'data-target': target})
        a.string = heading.get_text(' ', strip=True)
        li.append(a)
        toc_list.append(li)

    footer_links_div = soup.select_one('.footer-links')
    footer_links_div.clear()
    for label, href in footer_links:
        a = soup.new_tag('a', href=href, attrs={'class': 'footer-link'})
        a.string = label
        footer_links_div.append(a)
    soup.select_one('.footer-note').string = footer_note
    html_path.write_text(str(soup), encoding='utf-8')


def write_teacher_note(design_df: pd.DataFrame) -> None:
    comparison = pd.read_csv(OUTPUT_ROOT / 'fixed_school_combo_result_comparison.csv')
    selected_self = comparison[(comparison['scheme'] == 'B_4train_3test_all_intensity') & (comparison['stage'] == 'self_validation')].copy()
    selected_out = comparison[(comparison['scheme'] == 'B_4train_3test_all_intensity') & (comparison['stage'] == 'outphase')].copy()
    sens_self = comparison[(comparison['scheme'] == 'A_5train_2test_balanced_rate') & (comparison['stage'] == 'self_validation')].copy()
    sens_out = comparison[(comparison['scheme'] == 'A_5train_2test_balanced_rate') & (comparison['stage'] == 'outphase')].copy()

    md_path = TEACHER_DIR / '04_fixed_school_combo_note.md'
    lines = [
        '# 固定校区组合版 split：主方案 + sensitivity analysis',
        '',
        '> 这一页单独回答“如果固定若干校区训练、另外若干校区测试，会怎样”，并把已选主方案 B 与补跑的 sensitivity 方案 A 放在一起，方便老师快速看。',
        '',
        '## 1. 为什么要单独做固定校区组合版 split',
        '',
        '- `leave_one_school_out` 是逐校区留一，更像系统的 grouped validation。',
        '- 固定校区组合版 split 则更贴近现在讨论的实际表述：**若干校区训练，另外若干校区测试**。',
        '- 但它的定位仍是 internal grouped validation / internal temporal validation，**不是 external validation**。',
        '',
        '## 2. 两个固定校区方案',
        '',
        fmt_markdown_table(design_df),
        '',
        '### 当前主方案：B（4 train + 3 test）',
        '',
        '- 选择理由：train/test 两侧都覆盖 3 种 intensity；test 样本量更大；更像多校区固定 hold-out。',
        '',
        '## 3. 方案 B 结果（已选主方案）',
        '',
        '### self-validation',
        '',
        fmt_markdown_table(selected_self[['model_label','validation_scheme','mean_auc','mean_train_auc','mean_gap','train_schools','test_schools','train_n','test_n']]),
        '',
        '### out-phase',
        '',
        fmt_markdown_table(selected_out[['model_label','validation_scheme','mean_auc','mean_train_auc','mean_gap','train_schools','test_schools','train_n','test_n']]),
        '',
        '解读：',
        '',
        '- `clinical_baseline_main` 在方案 B 的 self-validation AUC 约 **0.5940**，但 out-phase 约 **0.5325**。',
        '- `compact_fusion` 与 `ultra_sparse_lipid` 的 train AUC 仍高于 test AUC 很多，说明 fixed split 下 generalization gap 依旧存在。',
        '',
        '## 4. 方案 A 结果（补跑 sensitivity analysis）',
        '',
        '### self-validation',
        '',
        fmt_markdown_table(sens_self[['model_label','validation_scheme','mean_auc','mean_train_auc','mean_gap','train_schools','test_schools','train_n','test_n']]),
        '',
        '### out-phase',
        '',
        fmt_markdown_table(sens_out[['model_label','validation_scheme','mean_auc','mean_train_auc','mean_gap','train_schools','test_schools','train_n','test_n']]),
        '',
        '解读：',
        '',
        '- 方案 A 的优点是 response rate gap 更小，更适合作为 sensitivity analysis。',
        '- 如果方案 A 与方案 B 的结论方向一致，就可以更稳妥地说明：**固定校区组合怎么切，当前信号都没有上升到强跨校区泛化的层级**。',
        '',
        '## 5. 当前最稳妥的老师口径',
        '',
        '1. strict nested CV outer-test AUC 约 **0.50–0.54** 仍是正式主结果。',
        '2. AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`。',
        '3. 固定校区组合版 split、leave-one-school-out、repeated hold-out、out-phase 都只能写成内部验证，不是 external validation。',
        '4. 方案 B 适合作为当前主固定 split 展示；方案 A 可作为 sensitivity analysis 证明结论不依赖单一切法。',
        '',
        '## 6. 包内可直接打开的文件',
        '',
        '- 统一汇报页： [02_combined_report.html](02_combined_report.html)',
        '- 文献 / protocol 说明： [03_literature_followup_note.html](03_literature_followup_note.html)',
        '- 固定校区组合结果对比 CSV： [fixed_school_combo_result_comparison.csv](fixed_school_combo_result_comparison.csv)',
        '- 固定校区组合方案设计 CSV： [fixed_school_combo_scheme_design.csv](fixed_school_combo_scheme_design.csv)',
    ]
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    render_markdown_into_template(
        md_path,
        TEACHER_DIR / '04_fixed_school_combo_note.html',
        page_title='固定校区组合版 split：主方案 + sensitivity analysis',
        badge='Fixed school combo · 2026-03-12',
        hero_title='固定校区组合版 split：主方案 B + 方案 A sensitivity',
        subtitle='把固定校区 train/test 组合的两套最合理方案、已选主方案 B，以及补跑的方案 A sensitivity 放在一页里。',
        meta_items=[
            ('主口径仍是 strict nested CV outer-test AUC≈0.50–0.54', 'pill'),
            ('方案 B 为主固定 split，方案 A 为 sensitivity', 'pill'),
            ('fixed combo / out-phase 均非 external validation', 'pill'),
            ('来源文件：04_fixed_school_combo_note.md', 'path'),
            ('新增页：固定校区组合版 split 汇报', 'path'),
        ],
        nav_links=[
            ('统一汇报', '02_combined_report.html'),
            ('文献与protocol', '03_literature_followup_note.html'),
            ('结果对比CSV', 'fixed_school_combo_result_comparison.csv'),
        ],
        footer_links=[
            ('统一汇报页', '02_combined_report.html'),
            ('结果对比CSV', 'fixed_school_combo_result_comparison.csv'),
        ],
        footer_note='Fixed school combo note refreshed on 2026-03-12.',
    )


def update_markdown_links() -> None:
    readme = TEACHER_DIR / 'README.md'
    text = readme.read_text(encoding='utf-8')
    target = '- 如要回答“学校/社区 split 的新分析放在哪里、运动 protocol 怎么写”，打开 `03_literature_followup_note.html`。\n'
    replacement = target + '- 如要直接汇报“固定若干校区训练、另外若干校区测试”的两套方案与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。\n'
    if '04_fixed_school_combo_note.html' not in text:
        text = text.replace(target, replacement)
    readme.write_text(text, encoding='utf-8')

    combined_md = TEACHER_DIR / '02_combined_report.md'
    text = combined_md.read_text(encoding='utf-8')
    section = "## 固定校区组合版 split（新增补充页）\n\n- 如果老师现在更关心‘固定若干校区训练、另外若干校区测试’的写法，直接打开 [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)。\n- 该页同时放了当前主方案 **B（4 train + 3 test）**，以及补跑的 **方案 A（5 train + 2 test）sensitivity analysis**。\n- 两个方案都仍属于 internal grouped validation / internal temporal validation，不能写成 external validation。\n\n"
    marker = '## 当前仍未闭环的内容\n'
    if '04_fixed_school_combo_note.html' not in text:
        text = text.replace(marker, section + marker)
        text = text.replace(
            '- 文献与 protocol 写法说明： [03_literature_followup_note.html](03_literature_followup_note.html)\n',
            '- 文献与 protocol 写法说明： [03_literature_followup_note.html](03_literature_followup_note.html)\n- 固定校区组合版 split： [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)\n',
        )
        text = text.replace(
            '- school split / protocol 说明： [03_literature_followup_note.html](03_literature_followup_note.html)\n',
            '- school split / protocol 说明： [03_literature_followup_note.html](03_literature_followup_note.html)\n- fixed school combo split： [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)\n',
        )
    combined_md.write_text(text, encoding='utf-8')


def insert_html_section_before_marker(soup: BeautifulSoup, marker_text: str, html_fragment: str) -> None:
    target_h2 = None
    for h2 in soup.select('main.content h2'):
        if h2.get_text(' ', strip=True) == marker_text:
            target_h2 = h2
            break
    if target_h2 is None:
        return
    if soup.select_one('a[href="04_fixed_school_combo_note.html"]') and '固定校区组合版 split（新增补充页）' in soup.get_text(' ', strip=True):
        return
    fragment = BeautifulSoup(html_fragment, 'html.parser')
    for node in list(fragment.contents):
        target_h2.insert_before(node)


def update_combined_html() -> None:
    combined_html = TEACHER_DIR / '02_combined_report.html'
    soup = BeautifulSoup(combined_html.read_text(encoding='utf-8'), 'html.parser')

    title_tag = soup.title
    if title_tag and '固定校区组合' not in title_tag.get_text():
        pass

    meta_row = soup.select_one('.meta-row')
    meta_texts = [x.get_text(' ', strip=True) for x in meta_row.select('span')]
    if not any('固定校区组合 split 已补跑' in t for t in meta_texts):
        new_span = soup.new_tag('span', attrs={'class': 'meta-pill'})
        new_span.string = '固定校区组合 split 已补跑（B 主方案 + A sensitivity）'
        meta_row.append(new_span)

    nav_row = soup.select_one('.nav-row.doc-toolbar')
    if nav_row and not nav_row.select_one('a[href="04_fixed_school_combo_note.html"]'):
        a = soup.new_tag('a', href='04_fixed_school_combo_note.html', attrs={'class': 'nav-link'})
        a.string = '固定校区split'
        nav_row.append(a)

    html_fragment = """
<h2 id="固定校区组合版-split新增补充页">固定校区组合版 split（新增补充页）</h2>
<ul>
<li>如果老师现在更关心“固定若干校区训练、另外若干校区测试”的写法，直接打开 <a href="04_fixed_school_combo_note.html">04_fixed_school_combo_note.html</a>。</li>
<li>该页同时放了当前主方案 <strong>B（4 train + 3 test）</strong>，以及补跑的 <strong>方案 A（5 train + 2 test）sensitivity analysis</strong>。</li>
<li>两个方案都仍属于 internal grouped validation / internal temporal validation，不能写成 external validation。</li>
</ul>
"""
    insert_html_section_before_marker(soup, '当前仍未闭环的内容', html_fragment)

    changed = False
    for ul in soup.select('main.content ul'):
        text = ul.get_text(' ', strip=True)
        if '文献与 protocol 写法说明' in text and not ul.select_one('a[href="04_fixed_school_combo_note.html"]'):
            li = soup.new_tag('li')
            li.append('固定校区组合版 split： ')
            a = soup.new_tag('a', href='04_fixed_school_combo_note.html')
            a.string = '04_fixed_school_combo_note.html'
            li.append(a)
            ul.append(li)
            changed = True
        if 'follow-up 图文页' in text and not ul.select_one('a[href="04_fixed_school_combo_note.html"]'):
            li = soup.new_tag('li')
            li.append('fixed school combo split： ')
            a = soup.new_tag('a', href='04_fixed_school_combo_note.html')
            a.string = '04_fixed_school_combo_note.html'
            li.append(a)
            ul.append(li)
            changed = True
    combined_html.write_text(str(soup), encoding='utf-8')
    shutil.copy2(combined_html, TEACHER_DIR / 'index.html')


def update_literature_note_html_nav() -> None:
    lit_html = TEACHER_DIR / '03_literature_followup_note.html'
    soup = BeautifulSoup(lit_html.read_text(encoding='utf-8'), 'html.parser')
    nav_row = soup.select_one('.nav-row.doc-toolbar')
    if nav_row and not nav_row.select_one('a[href="04_fixed_school_combo_note.html"]'):
        a = soup.new_tag('a', href='04_fixed_school_combo_note.html', attrs={'class': 'nav-link'})
        a.string = '固定校区split'
        nav_row.append(a)
        lit_html.write_text(str(soup), encoding='utf-8')


def update_root_design_note(design_df: pd.DataFrame) -> None:
    design_md = OUTPUT_ROOT / 'fixed_school_combo_design.md'
    if not design_md.exists():
        return
    text = design_md.read_text(encoding='utf-8')
    note = '\n- 方案 A（5 train + 2 test）现已按 sensitivity analysis 补跑，主要用于检验“更平衡的 response rate 切法”是否改变结论。\n'
    if '现已按 sensitivity analysis 补跑' not in text:
        text = text.rstrip() + '\n' + note
        design_md.write_text(text, encoding='utf-8')


def main() -> None:
    config = load_pipeline_config(CONFIG_PATH)
    mapping_path = config['followup']['self_validation']['pseudo_external']['mapping_path']
    mapping_sheet = str(config['followup']['self_validation']['pseudo_external'].get('mapping_sheet_name') or '运动强度分组_401人')

    raw_tables = load_project_tables(
        group_path=config['paths']['group'],
        lipid_path=config['paths']['lipid'],
        clinical_full_path=config['paths']['clinical_full'],
        clinical_slim_path=config['paths']['clinical_slim'],
    )
    design_df = compute_scheme_design(raw_tables.group, mapping_path, mapping_sheet)

    run_fixed_only_analyses(config, 'A_5train_2test_balanced_rate')
    write_scheme_a_summary(design_df)
    comparison_frame, _ = build_comparison_outputs(design_df)
    copy_teacher_support_files(design_df, comparison_frame)
    write_teacher_note(design_df)
    update_markdown_links()
    update_combined_html()
    update_literature_note_html_nav()
    update_root_design_note(design_df)


if __name__ == '__main__':
    main()
