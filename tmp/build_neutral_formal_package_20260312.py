from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
BASE = ROOT / 'outputs' / '20260311_responder_followup'
SOURCE = BASE / 'external_handoff_formal_package'
PACKAGE = BASE / 'responder_formal_delivery_package'
ZIP_PATH = BASE / '20260312_responder_formal_delivery_package.zip'

CODE_FILES = [
    ROOT / 'config' / 'analysis.yaml',
    ROOT / 'run_pipeline.py',
    ROOT / 'src' / 'followup' / 'run_followup.py',
    ROOT / 'src' / 'followup' / 'outphase_validation.py',
    ROOT / 'src' / 'followup' / 'make_figures.py',
]

DATA_FILES = [
    ROOT / '287_enroll_data_clean.csv',
    ROOT / '281_merge_lipids_enroll.csv',
    ROOT / '281_new_grouped.csv',
    ROOT / '287_outroll_data_clean.csv',
    ROOT / '281_merge_lipids_out.csv',
    BASE / 'teacher_report_package' / 'id_school_intensity_mapping.csv',
]

PAGE_MAP = {
    '01_followup_formal_report': {
        'title': 'Responder follow-up 结果说明（school split + out-phase）',
        'badge': '正式报告 · 2026-03-12',
        'subtitle': '在不改变 strict nested CV 主结果的前提下，补充真实 school grouped split 与 out-phase internal temporal validation 的解释层。',
        'meta': [
            ('meta-pill', '需求方：Shuxian Zhang'),
            ('meta-pill', '分析提供方：Chenyu Fan'),
            ('meta-pill', '主锚点：strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', 'AUC≈0.8 仅指 mean_train_auc'),
            ('path-chip', '来源文件：01_followup_formal_report.md'),
        ],
        'nav': [
            ('总览页', '02_combined_formal_report.html'),
            ('school split / protocol', '03_school_split_protocol_note.html'),
            ('分析代码', 'analysis_code/README.md'),
            ('分析数据', 'analysis_data/README.md'),
        ],
        'footer': 'Formal report package refreshed on 2026-03-12.',
        'footer_links': [('总览页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
    '02_combined_formal_report': {
        'title': 'Responder 正式报告包（基线主结果 + school split follow-up）',
        'badge': '正式报告 · 总览页',
        'subtitle': '先给出 strict nested CV 正式主结果，再补充 school grouped split、out-phase temporal validation 与 protocol / 写作边界说明。',
        'meta': [
            ('meta-pill', '需求方：Shuxian Zhang'),
            ('meta-pill', '分析提供方：Chenyu Fan'),
            ('meta-pill', '主锚点：strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', 'school split / out-phase 均非 external validation'),
            ('path-chip', '来源文件：02_combined_formal_report.md'),
        ],
        'nav': [
            ('Follow-up 页', '01_followup_formal_report.html'),
            ('school split / protocol', '03_school_split_protocol_note.html'),
            ('固定校区 split', '04_fixed_school_combo_note.html'),
            ('README', 'README.md'),
        ],
        'footer': 'Formal report package refreshed on 2026-03-12.',
        'footer_links': [('Follow-up 页', '01_followup_formal_report.html'), ('README', 'README.md')],
    },
    '03_school_split_protocol_note': {
        'title': '学校 / 社区 split 与运动 protocol 说明',
        'badge': '方法说明 · 2026-03-12',
        'subtitle': '说明 school/community split 当前落点、可写与不可写边界，以及 protocol 的正式写法。',
        'meta': [
            ('meta-pill', '需求方：Shuxian Zhang'),
            ('meta-pill', '分析提供方：Chenyu Fan'),
            ('meta-pill', '学校-强度映射已整理为 CSV'),
            ('meta-pill', '均属 internal validation，不是 external validation'),
            ('path-chip', '来源文件：03_school_split_protocol_note.md'),
        ],
        'nav': [
            ('总览页', '02_combined_formal_report.html'),
            ('学校映射 CSV', 'id_school_intensity_mapping.csv'),
            ('分析代码', 'analysis_code/README.md'),
            ('分析数据', 'analysis_data/README.md'),
        ],
        'footer': 'Formal report package refreshed on 2026-03-12.',
        'footer_links': [('总览页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
    '04_fixed_school_combo_note': {
        'title': '固定校区组合版 split：结果说明 + sensitivity analysis',
        'badge': '敏感性分析 · 2026-03-12',
        'subtitle': '把固定校区 train/test 组合的两套合理方案、已选主方案 B 与方案 A sensitivity 放在同一页，便于正式材料直接引用。',
        'meta': [
            ('meta-pill', '需求方：Shuxian Zhang'),
            ('meta-pill', '分析提供方：Chenyu Fan'),
            ('meta-pill', '主口径仍是 strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', 'fixed combo / out-phase 均非 external validation'),
            ('path-chip', '来源文件：04_fixed_school_combo_note.md'),
        ],
        'nav': [
            ('总览页', '02_combined_formal_report.html'),
            ('结果对比 CSV', 'fixed_school_combo_result_comparison.csv'),
            ('分析代码', 'analysis_code/README.md'),
            ('分析数据', 'analysis_data/README.md'),
        ],
        'footer': 'Formal report package refreshed on 2026-03-12.',
        'footer_links': [('总览页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
}

ROOT_README = '''# responder formal delivery package

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan

## 建议阅读顺序

1. 先打开 `index.html`：这是总览页，按“正式主结果 → school split follow-up → out-phase temporal validation → protocol / 写作边界”组织。
2. 如需单看 follow-up 解释层，打开 `01_followup_formal_report.html`。
3. 如需单看 school / community split 与 protocol 写法，打开 `03_school_split_protocol_note.html`。
4. 如需单看固定校区 train/test 组合与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。

## 包内主要页面

- `index.html`
- `01_followup_formal_report.html`
- `02_combined_formal_report.html`
- `03_school_split_protocol_note.html`
- `04_fixed_school_combo_note.html`

## 代码与数据

- `analysis_code/`：本次报告包对应的分析代码。
- `analysis_data/`：本次报告包对应的主要分析输入数据。

## 当前必须坚持的科学边界

- 正式主结果仍是 strict nested CV 的 outer-test AUC，约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- `repeated hold-out`、`leave-one-school-out`、固定校区组合版 split、`outphase_leave_one_school_out` 均属于补充验证证据链，不能写成 `external validation`。
- 当前 package 支持的是“边界更清楚、解释更完整、材料更完整”，不支持“强跨校区泛化已被证明”。

## 主要清单

- `strict_nested_cv_key_metrics.csv`
- `school_group_holdout_summary.csv`
- `self_validation_summary.csv`
- `outphase_validation_summary.csv`
- `fixed_school_combo_result_comparison.csv`
- `fixed_school_combo_scheme_design.csv`
- `id_school_intensity_mapping.csv`
- `analysis_code/`
- `analysis_data/`
- `assets/`
'''

CODE_README = '''# analysis code

本目录纳入本次报告包直接对应的主要分析代码：

- `run_pipeline.py`：总入口
- `config_analysis.yaml`：分析参数配置
- `run_followup.py`：follow-up 主流程
- `outphase_validation.py`：out-phase internal temporal validation
- `make_figures.py`：图件生成与版式修复
'''

DATA_README = '''# analysis data

本目录纳入本次报告包直接对应的主要分析输入数据：

- `287_enroll_data_clean.csv`：baseline / enroll 临床数据
- `281_merge_lipids_enroll.csv`：baseline / enroll 脂质组数据
- `281_new_grouped.csv`：当前 responder 分组数据
- `287_outroll_data_clean.csv`：out-phase / outroll 临床数据
- `281_merge_lipids_out.csv`：out-phase / outroll 脂质组数据
- `id_school_intensity_mapping.csv`：学校-强度映射表
'''


def replace_text(text: str) -> str:
    replacements = {
        'Responder follow-up 正式交接报告（school split + out-phase）': 'Responder follow-up 结果说明（school split + out-phase）',
        'Responder 外部正式交接包（基线主结果 + school split follow-up）': 'Responder 正式报告包（基线主结果 + school split follow-up）',
        '学校 / 社区 split 与运动 protocol 正式说明（外部交接版）': '学校 / 社区 split 与运动 protocol 说明',
        '固定校区组合版 split：正式说明 + sensitivity analysis': '固定校区组合版 split：结果说明 + sensitivity analysis',
        '本页用于外部正式交接：': '本页用于正式结果说明：',
        '本页是外部正式交接的总入口，': '本页是正式报告的总入口，',
        '本页用于外部正式交接，': '本页用于正式结果说明，',
        '整理成对外可引用的正式说明。': '整理成可直接引用的正式说明。',
        '正式交接页': '正式说明页',
        '正式交接': '正式说明',
        '交接摘要': '摘要',
        '总交接页': '总览页',
        '交接材料索引': '材料索引',
        '如何使用这一包进行交接': '如何阅读这一包',
        '常见问答（对外版）': '常见问答',
        '可直接用于正式交接的一句话': '可直接引用的一句话',
        '如果接收方只需要一句话': '如果只需要一句话',
        '交接用途：follow-up explanation layer': '页面用途：follow-up explanation layer',
        '交接用途：external handoff master page': '页面用途：formal master page',
        'External formal handoff package refresh on 2026-03-12.': 'Formal report package refreshed on 2026-03-12.',
        '外部协作方、顾问或公司端接收方': '协作方或项目接收方',
        '可转发': '正式材料',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def enrich_md(stem: str, text: str) -> str:
    if stem == '02_combined_formal_report':
        insert_block = '''## 项目角色

- 需求方：`Shuxian Zhang`
- 分析提供方：`Chenyu Fan`

## 随包附带的分析代码与分析数据

- 分析代码目录：`analysis_code/`
- 分析数据目录：`analysis_data/`
- 代码目录包含：`run_pipeline.py`、`config_analysis.yaml`、`run_followup.py`、`outphase_validation.py`、`make_figures.py`
- 数据目录包含：baseline / out-phase 临床数据、baseline / out-phase 脂质组数据、当前 responder 分组数据与学校-强度映射表

'''
        marker = '## 建议阅读顺序'
        if marker in text and '## 项目角色' not in text:
            text = text.replace(marker, insert_block + marker, 1)
    return text


def build_meta_row(soup: BeautifulSoup, items: list[tuple[str, str]]):
    row = soup.new_tag('div', attrs={'class': 'meta-row'})
    for klass, text in items:
        tag = soup.new_tag('span', attrs={'class': klass})
        tag.string = text
        row.append(tag)
    return row


def build_nav_row(soup: BeautifulSoup, items: list[tuple[str, str]]):
    row = soup.new_tag('div', attrs={'class': 'nav-row doc-toolbar'})
    for text, href in items:
        a = soup.new_tag('a', attrs={'class': 'nav-link', 'href': href})
        a.string = text
        row.append(a)
    return row


def build_footer_links(soup: BeautifulSoup, items: list[tuple[str, str]]):
    row = soup.new_tag('div', attrs={'class': 'footer-links'})
    for text, href in items:
        a = soup.new_tag('a', attrs={'class': 'footer-link', 'href': href})
        a.string = text
        row.append(a)
    return row


def reset_package():
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)
    shutil.copytree(SOURCE / 'assets', PACKAGE / 'assets')
    for name in [
        'strict_nested_cv_key_metrics.csv',
        'school_group_holdout_summary.csv',
        'self_validation_summary.csv',
        'outphase_validation_summary.csv',
        'small_model_followup_comparison.csv',
        'fixed_school_combo_result_comparison.csv',
        'fixed_school_combo_scheme_design.csv',
        'id_school_intensity_mapping.csv',
    ]:
        shutil.copy2(SOURCE / name, PACKAGE / name)
    (PACKAGE / 'README.md').write_text(ROOT_README, encoding='utf-8')

    code_dir = PACKAGE / 'analysis_code'
    code_dir.mkdir()
    for src in CODE_FILES:
        target_name = src.name if src.name != 'analysis.yaml' else 'config_analysis.yaml'
        shutil.copy2(src, code_dir / target_name)
    (code_dir / 'README.md').write_text(CODE_README, encoding='utf-8')

    data_dir = PACKAGE / 'analysis_data'
    data_dir.mkdir()
    for src in DATA_FILES:
        shutil.copy2(src, data_dir / src.name)
    (data_dir / 'README.md').write_text(DATA_README, encoding='utf-8')


def render_page(stem: str):
    src_md = SOURCE / f'{stem}.md'
    src_html = SOURCE / f'{stem}.html'
    out_md = PACKAGE / f'{stem}.md'
    out_html = PACKAGE / f'{stem}.html'
    cfg = PAGE_MAP[stem]

    md_text = replace_text(src_md.read_text(encoding='utf-8'))
    md_text = enrich_md(stem, md_text)
    out_md.write_text(md_text, encoding='utf-8')

    soup = BeautifulSoup(src_html.read_text(encoding='utf-8'), 'html.parser')
    rendered = subprocess.check_output(['pandoc', '-f', 'gfm', '-t', 'html5', str(out_md)], text=True)
    rendered_soup = BeautifulSoup(rendered, 'html.parser')

    if soup.title:
        soup.title.string = cfg['title']
    badge = soup.select_one('.badge')
    if badge:
        badge.string = cfg['badge']
    h1 = soup.select_one('.hero h1')
    if h1:
        h1.string = cfg['title']
    subtitle = soup.select_one('.subtitle')
    if subtitle:
        subtitle.string = cfg['subtitle']

    meta_row = soup.select_one('.meta-row')
    if meta_row:
        meta_row.replace_with(build_meta_row(soup, cfg['meta']))
    nav_row = soup.select_one('.nav-row')
    if nav_row:
        nav_row.replace_with(build_nav_row(soup, cfg['nav']))

    main = soup.select_one('main.content')
    main.clear()
    for child in list(rendered_soup.contents):
        if getattr(child, 'name', None) is None and not str(child).strip():
            continue
        main.append(child)

    toc_list = soup.select_one('.sidebar-toc-list')
    if toc_list is not None:
        toc_list.clear()
        for heading in main.find_all(['h2', 'h3']):
            target = heading.get('id')
            if not target:
                continue
            li = soup.new_tag('li', attrs={'class': 'sidebar-toc-item'})
            a_cls = 'sidebar-toc-link sub-item' if heading.name == 'h3' else 'sidebar-toc-link'
            a = soup.new_tag('a', href=f'#{target}', attrs={'class': a_cls, 'data-target': target})
            a.string = heading.get_text(' ', strip=True)
            li.append(a)
            toc_list.append(li)

    footer_note = soup.select_one('.footer-note')
    if footer_note:
        footer_note.string = cfg['footer']
    footer_links = soup.select_one('.footer-links')
    if footer_links:
        footer_links.replace_with(build_footer_links(soup, cfg['footer_links']))

    out_html.write_text(str(soup), encoding='utf-8')


def build():
    reset_package()
    for stem in PAGE_MAP:
        render_page(stem)
    shutil.copy2(PACKAGE / '02_combined_formal_report.html', PACKAGE / 'index.html')
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    subprocess.run(['zip', '-rqX', ZIP_PATH.name, PACKAGE.name], cwd=BASE, check=True)


if __name__ == '__main__':
    build()
