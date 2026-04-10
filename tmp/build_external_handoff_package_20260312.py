from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
BASE = ROOT / 'outputs' / '20260311_responder_followup'
TEACHER = BASE / 'teacher_report_package'
FORMAL = BASE / 'sequencing_company_formal_report_package'
EXTERNAL = BASE / 'external_handoff_formal_package'
ZIP_PATH = BASE / '20260312_responder_external_handoff_formal_package.zip'


def extract_from(text: str, heading: str) -> str:
    if heading not in text:
        raise ValueError(f'heading not found: {heading}')
    return heading + text.split(heading, 1)[1]


def replace_line(text: str, old: str, new: str) -> str:
    if old not in text:
        return text
    return text.replace(old, new)


def build_md_01(src: str) -> str:
    body = extract_from(src, '## 一页结论')
    body = replace_line(
        body,
        '4. **最后看 protocol 与 blocked**：知道当前主文能写到哪一步，哪些细节应该放补充材料或等后续数据到位再写。',
        '4. **最后看 protocol 与数据条件**：明确当前主文可写到哪一步，以及哪些细节更适合放在补充材料或待后续数据到位后补充。',
    )
    body = replace_line(body, '## 新分析放在哪里', '## 交接材料索引')
    body = replace_line(body, '- 对接思路定位页：`followup_plan_alignment.md`', '- 总交接页：`02_combined_formal_report.html`')
    body = replace_line(body, '- 文献与 protocol 说明：`03_literature_followup_note.md`', '- school split 与 protocol 说明：`03_school_split_protocol_note.html`')
    body = replace_line(body, '- 作用是告诉老师：这不是单次切分偶然得到的结果，但它也没有显示出强泛化。', '- 它说明：这不是单次切分偶然得到的结果，但它也没有显示出强泛化。')
    body = replace_line(body, '[02_combined_report.html](02_combined_report.html)', '[02_combined_formal_report.html](02_combined_formal_report.html)')
    body = replace_line(body, '[03_literature_followup_note.html](03_literature_followup_note.html)', '[03_school_split_protocol_note.html](03_school_split_protocol_note.html)')

    intro = '''# Responder follow-up 正式交接报告（school split + out-phase）

> 本页用于外部正式交接：在不改变 strict nested CV 主结果的前提下，补充真实 school grouped split 与 out-phase internal temporal validation 的结果解释、边界说明与引用路径。

**交接摘要：**

> 当前 follow-up 的作用是补充稳健性与解释边界，而不是替代正式主结果。strict nested CV outer-test AUC 仍约 0.50–0.54；真实 `leave-one-school-out` 与 `outphase_leave_one_school_out` 已补跑，但均属于内部验证链路，不能写成 external validation；AUC≈0.8 仅对应 `mean_train_auc`。

'''
    return intro + body


def build_md_02(src: str) -> str:
    body = extract_from(src, '## 建议阅读顺序')
    body = replace_line(body, '## 三层汇报口径', '## 三层正式表述边界')
    body = replace_line(body, '## 怎么用这一包做汇报', '## 如何使用这一包进行交接')
    body = replace_line(body, '- **第 1 分钟**：', '- **第一步**：')
    body = replace_line(body, '- **第 2–4 分钟**：', '- **第二步**：')
    body = replace_line(body, '- **第 5–6 分钟**：', '- **第三步**：')
    body = replace_line(body, '- **最后 1 分钟**：', '- **第四步**：')
    body = replace_line(body, '> 如果老师只想听一句话：', '> 如果接收方只需要一句话：')
    body = replace_line(body, '### 第三层：内部时相验证 + 写作边界', '### 第三层：时相验证 + 写作边界')
    body = replace_line(body, '## 学校 split 与 protocol 写法对应页', '## school split 与 protocol 说明页')
    body = replace_line(body, '- 学校 / 社区 split 的新分析位置： [followup_plan_alignment.md](followup_plan_alignment.md)', '- school / community split 说明页： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)')
    body = replace_line(body, '## 当前仍未闭环的内容', '## 当前仍待补充的数据条件')
    body = replace_line(body, '文献与 protocol 写法说明： [03_literature_followup_note.html](03_literature_followup_note.html)', 'school split 与 protocol 说明： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)')
    body = replace_line(body, '如果老师现在更关心', '如果接收方现在更关心')
    if '## 包内文件' in body:
        body = body.split('## 包内文件', 1)[0].rstrip() + '\n\n'
    body += '''## 包内文件

- 总交接页： [02_combined_formal_report.html](02_combined_formal_report.html)
- follow-up 正式交接页： [01_followup_formal_report.html](01_followup_formal_report.html)
- school split / protocol 说明： [03_school_split_protocol_note.html](03_school_split_protocol_note.html)
- fixed school combo sensitivity： [04_fixed_school_combo_note.html](04_fixed_school_combo_note.html)
- strict nested CV 指标说明： [strict_nested_cv_key_metrics.csv](strict_nested_cv_key_metrics.csv)
- 学校 grouped holdout 汇总： [school_group_holdout_summary.csv](school_group_holdout_summary.csv)
- self-validation 汇总： [self_validation_summary.csv](self_validation_summary.csv)
- out-phase 汇总： [outphase_validation_summary.csv](outphase_validation_summary.csv)
- fixed school combo 对比： [fixed_school_combo_result_comparison.csv](fixed_school_combo_result_comparison.csv)
'''

    intro = '''# Responder 外部正式交接包（基线主结果 + school split follow-up）

> 本页是外部正式交接的总入口，按“正式主结果 → grouped split follow-up → out-phase temporal validation → protocol 与写作边界”的顺序组织，适合发送给外部协作方、顾问或公司端接收方。

**交接摘要：**

> 本包的核心价值不是把 headline AUC 做高，而是把当前最关键的科学边界讲清楚：strict nested CV outer-test AUC 仍约 0.50–0.54；真实 school split 与 out-phase 已完成补跑，但均属于内部验证证据链，不构成 external validation；AUC≈0.8 仅对应 `mean_train_auc`。

'''
    return intro + body


def build_md_03(src: str) -> str:
    body = extract_from(src, '## 怎么读这页')
    body = replace_line(body, '- 如果把 02 页看成“汇报总页”，那这页就是“老师追问时的解释页”。', '- 如果把 02 页看成“总交接页”，那这页就是用于补充方法学解释与写作边界的正式说明页。')
    body = replace_line(body, '- 对接思路定位页：`followup_plan_alignment.md`', '- 总交接页：`02_combined_formal_report.html`')
    body = replace_line(body, '- 文献与 protocol 说明：`03_literature_followup_note.md`', '- 正式说明页：`03_school_split_protocol_note.html`')
    body = replace_line(body, '4. `followup_plan_alignment.md`：把新建议、学校 split、protocol 写法和当前阻塞项放在一页里。', '4. `02_combined_formal_report.html`：汇总当前结论边界、页面入口与正式交接顺序。')
    body = replace_line(body, '- 真实映射来自：`运动与发育项目中英文变量缩写及文件历史迭代说明.xlsx` 的 `运动强度分组_401人` sheet。', '- 真实映射来自项目原始学校-强度对应表。')
    body = replace_line(body, '## 如果老师追问，可以怎么回答', '## 常见问答（对外版）')
    body = replace_line(body, '- **问：学校 / 社区 split 现在到底做了没有？**  ', '- **问：school / community split 是否已经完成？**  ')
    body = replace_line(body, '- **问：那为什么还不能叫 external validation？**  ', '- **问：为什么这些结果仍不能写成 external validation？**  ')
    body = replace_line(body, '- **问：运动 protocol 为什么不在主文里一次写很细？**  ', '- **问：为什么运动 protocol 不建议在主文中一次铺开所有强度细节？**  ')
    body = replace_line(body, '- 如果老师或审稿人追问，再引用 `id_school_intensity_mapping.csv` 中的学校-强度对应关系，说明这套信息已经在内部整理完成。', '- 如对方进一步问询，再引用 `id_school_intensity_mapping.csv` 中的学校-强度对应关系，说明这套信息已整理为可审计映射文件。')
    body = replace_line(body, '答：已经做了，真实学校映射来自 `运动强度分组_401人`，结果落在 `school_group_holdout_summary.csv`、`self_validation_summary.csv` 和 `outphase_validation_summary.csv`。', '答：已经完成，真实学校映射来自项目原始学校-强度对应表，结果落在 `school_group_holdout_summary.csv`、`self_validation_summary.csv` 和 `outphase_validation_summary.csv`。')
    body = replace_line(body, '答：因为主文当前更需要先把主结果与验证边界讲清楚；学校-强度细节已经内部整理完成，更适合放补充材料或答审时展开。', '答：因为主文当前更需要先把主结果与验证边界讲清楚；学校-强度细节已整理为可审计映射文件，更适合放补充材料或答审时展开。')
    body = replace_line(body, '## 8. 一句话结论', '## 8. 一句话结论')
    body = re.sub(
        r'> 学校 / 社区 split 对应的新分析已经落在 `school_group_holdout_summary\.csv`、`self_validation_summary\.csv`、`outphase_validation_summary\.csv` 和 `followup_plan_alignment\.md` 里；当前结果支持“真实学校 grouped split 已补跑，但整体 AUC 仍在 0\.50 左右”，不支持把它升级成 external validation。运动 protocol 的主文写法则建议继续从方案编号、周期、频次入手，把强度细节放到补充材料或答审中。',
        '> 学校 / 社区 split 对应的新分析已整合到 `school_group_holdout_summary.csv`、`self_validation_summary.csv`、`outphase_validation_summary.csv` 与 `02_combined_formal_report.html` 中；当前结果支持“真实学校 grouped split 已补跑，但整体 AUC 仍在 0.50 左右”，不支持将其升级表述为 external validation。运动 protocol 的主文写法则建议继续从方案编号、周期、频次入手，把强度细节放到补充材料或答审中。',
        body,
    )

    intro = '''# 学校 / 社区 split 与运动 protocol 正式说明（外部交接版）

> 本页基于两篇参考文献与当前项目已完成分析整理，目的不是重写正式主结果，而是把“学校 / 社区 split 放在哪里、能怎么写、不能怎么写、运动 protocol 如何稳妥落地”整理成对外可引用的正式说明。

'''
    return intro + body


def build_md_04(src: str) -> str:
    body = extract_from(src, '## 怎么读这页')
    body = replace_line(body, '## 5. 当前最稳妥的老师口径', '## 5. 当前最稳妥的正式表述')
    body = replace_line(body, '## 如果老师追问：为什么不直接改成方案 A？', '## 如对方问询：为什么不直接采用方案 A？')
    body = replace_line(body, '因此它更适合作为当前对老师汇报的主固定 split。', '因此它更适合作为当前正式交接的主固定 split。')
    body = replace_line(body, '> 可直接给老师的一句话：', '> 可直接用于正式交接的一句话：')
    body = replace_line(body, '[02_combined_report.html](02_combined_report.html)', '[02_combined_formal_report.html](02_combined_formal_report.html)')
    body = replace_line(body, '[03_literature_followup_note.html](03_literature_followup_note.html)', '[03_school_split_protocol_note.html](03_school_split_protocol_note.html)')

    intro = '''# 固定校区组合版 split：正式说明 + sensitivity analysis

> 本页用于外部正式交接，单独回答“若固定若干校区训练、另外若干校区测试，结论会怎样变化”，并把已选主方案 B 与补跑的 sensitivity 方案 A 放在同一页中，便于接收方快速理解 train/test 组合设计与边界判断。

'''
    return intro + body


PAGE_CONFIG = {
    '01_followup_formal_report': {
        'template': TEACHER / '01_followup_report.html',
        'badge': 'External formal handoff · 2026-03-12',
        'title': 'Responder follow-up 正式交接报告（school split + out-phase）',
        'subtitle': '对外正式交接页：在不改变 strict nested CV 主结果的前提下，补充真实 school grouped split 与 out-phase internal temporal validation 的解释层。',
        'meta': [
            ('meta-pill', '主锚点：strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', 'AUC≈0.8 仅指 mean_train_auc'),
            ('meta-pill', 'school split / out-phase 均非 external validation'),
            ('path-chip', '来源文件：01_followup_formal_report.md'),
            ('path-chip top-note', '交接用途：follow-up explanation layer'),
        ],
        'nav': [
            ('统一交接总页', '02_combined_formal_report.html'),
            ('school split / protocol', '03_school_split_protocol_note.html'),
            ('学校汇总 CSV', 'school_group_holdout_summary.csv'),
            ('fixed school combo', '04_fixed_school_combo_note.html'),
        ],
        'footer': 'External formal handoff package refresh on 2026-03-12.',
        'footer_links': [('总交接页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
    '02_combined_formal_report': {
        'template': TEACHER / '02_combined_report.html',
        'badge': 'External formal handoff · unified view',
        'title': 'Responder 外部正式交接包（基线主结果 + school split follow-up）',
        'subtitle': '对外正式交接总页：先给出 strict nested CV 正式主结果，再补充 school grouped split、out-phase temporal validation 与 protocol / 写作边界说明。',
        'meta': [
            ('meta-pill', '主锚点：strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', '真实学校 grouped split 已补跑'),
            ('meta-pill', 'school split / repeated hold-out / out-phase 均非 external validation'),
            ('path-chip', '来源文件：02_combined_formal_report.md'),
            ('path-chip top-note', '交接用途：external handoff master page'),
            ('meta-pill', '固定校区组合 split 已补跑（B 主方案 + A sensitivity）'),
        ],
        'nav': [
            ('Follow-up 正式页', '01_followup_formal_report.html'),
            ('school split / protocol', '03_school_split_protocol_note.html'),
            ('学校汇总 CSV', 'school_group_holdout_summary.csv'),
            ('fixed school combo', '04_fixed_school_combo_note.html'),
        ],
        'footer': 'External formal handoff package refresh on 2026-03-12.',
        'footer_links': [('Follow-up 正式页', '01_followup_formal_report.html'), ('README', 'README.md')],
    },
    '03_school_split_protocol_note': {
        'template': TEACHER / '03_literature_followup_note.html',
        'badge': 'External method note · 2026-03-12',
        'title': '学校 / 社区 split 与运动 protocol 正式说明（外部交接版）',
        'subtitle': '说明 school/community split 当前落点、可写与不可写边界，以及 protocol 的正式写法。',
        'meta': [
            ('meta-pill', 'school_group_holdout_summary.csv 已纳入'),
            ('meta-pill', '学校-强度映射已整理为 CSV'),
            ('meta-pill', '均属 internal validation，不是 external validation'),
            ('path-chip', '来源文件：03_school_split_protocol_note.md'),
        ],
        'nav': [
            ('总交接页', '02_combined_formal_report.html'),
            ('Follow-up 正式页', '01_followup_formal_report.html'),
            ('学校映射 CSV', 'id_school_intensity_mapping.csv'),
            ('fixed school combo', '04_fixed_school_combo_note.html'),
        ],
        'footer': 'External formal handoff package refresh on 2026-03-12.',
        'footer_links': [('总交接页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
    '04_fixed_school_combo_note': {
        'template': TEACHER / '04_fixed_school_combo_note.html',
        'badge': 'External sensitivity note · 2026-03-12',
        'title': '固定校区组合版 split：正式说明 + sensitivity analysis',
        'subtitle': '把固定校区 train/test 组合的两套合理方案、已选主方案 B 与方案 A sensitivity 放在同一页，便于正式交接时直接引用。',
        'meta': [
            ('meta-pill', '主口径仍是 strict nested CV outer-test AUC≈0.50–0.54'),
            ('meta-pill', '方案 B 为主固定 split，方案 A 为 sensitivity'),
            ('meta-pill', 'fixed combo / out-phase 均非 external validation'),
            ('path-chip', '来源文件：04_fixed_school_combo_note.md'),
        ],
        'nav': [
            ('总交接页', '02_combined_formal_report.html'),
            ('school split / protocol', '03_school_split_protocol_note.html'),
            ('结果对比 CSV', 'fixed_school_combo_result_comparison.csv'),
            ('方案设计 CSV', 'fixed_school_combo_scheme_design.csv'),
        ],
        'footer': 'External formal handoff package refresh on 2026-03-12.',
        'footer_links': [('总交接页', '02_combined_formal_report.html'), ('README', 'README.md')],
    },
}


README_TEXT = '''# responder external formal handoff package

- 需求方：Shuxian Zhang
- 分析提供方：Chenyu Fan
- 交付定位：面向外部协作方 / 公司端 / 顾问端的正式交接包；保留本轮 follow-up 的解释层，但统一改为中性、正式、可转发口吻。

## 建议阅读顺序

1. 先打开 `index.html`：这是总交接页，按“正式主结果 → school split follow-up → out-phase temporal validation → protocol / 写作边界”组织。
2. 如需单看 follow-up 解释层，打开 `01_followup_formal_report.html`。
3. 如需单看 school / community split 与 protocol 写法，打开 `03_school_split_protocol_note.html`。
4. 如需单看固定校区 train/test 组合与 sensitivity analysis，打开 `04_fixed_school_combo_note.html`。

## 包内主要文件

- `index.html`
- `01_followup_formal_report.html`
- `02_combined_formal_report.html`
- `03_school_split_protocol_note.html`
- `04_fixed_school_combo_note.html`
- `strict_nested_cv_key_metrics.csv`
- `school_group_holdout_summary.csv`
- `self_validation_summary.csv`
- `outphase_validation_summary.csv`
- `fixed_school_combo_result_comparison.csv`
- `fixed_school_combo_scheme_design.csv`
- `id_school_intensity_mapping.csv`
- `assets/`

## 当前必须坚持的科学边界

- 正式主结果仍是 strict nested CV 的 outer-test AUC，约 0.50–0.54。
- AUC≈0.8 仅对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- `repeated hold-out`、`leave-one-school-out`、固定校区组合版 split、`outphase_leave_one_school_out` 均属于补充验证证据链，不能写成 `external validation`。
- 当前 package 支持的是“边界更清楚、解释更完整、交接更稳妥”，不支持“强跨校区泛化已被证明”。

## 当前仍待补充的数据条件

- responder 定义源头核对 / alternative grouping sensitivity：仍缺原始连续终点文件。
- 心血管表型桥接：仍缺整理后的心血管表型表。

## 一句话摘要

- 这是一份可直接对外发送的正式交接包：它保留了 strict nested CV 主锚点，并把真实 school grouped split、out-phase temporal validation、fixed school combo sensitivity 与 protocol 写法边界整理成了统一、可转发的正式说明。
'''


COPY_FILES = [
    TEACHER / 'school_group_holdout_summary.csv',
    TEACHER / 'self_validation_summary.csv',
    TEACHER / 'outphase_validation_summary.csv',
    TEACHER / 'small_model_followup_comparison.csv',
    TEACHER / 'id_school_intensity_mapping.csv',
    TEACHER / 'fixed_school_combo_result_comparison.csv',
    TEACHER / 'fixed_school_combo_scheme_design.csv',
    FORMAL / 'strict_nested_cv_key_metrics.csv',
]


def reset_package() -> None:
    if EXTERNAL.exists():
        shutil.rmtree(EXTERNAL)
    EXTERNAL.mkdir(parents=True)
    shutil.copytree(TEACHER / 'assets', EXTERNAL / 'assets')
    for src in COPY_FILES:
        shutil.copy2(src, EXTERNAL / src.name)
    (EXTERNAL / 'README.md').write_text(README_TEXT, encoding='utf-8')


def write_markdown() -> None:
    src01 = (TEACHER / '01_followup_report.md').read_text(encoding='utf-8')
    src02 = (TEACHER / '02_combined_report.md').read_text(encoding='utf-8')
    src03 = (TEACHER / '03_literature_followup_note.md').read_text(encoding='utf-8')
    src04 = (TEACHER / '04_fixed_school_combo_note.md').read_text(encoding='utf-8')

    (EXTERNAL / '01_followup_formal_report.md').write_text(build_md_01(src01), encoding='utf-8')
    (EXTERNAL / '02_combined_formal_report.md').write_text(build_md_02(src02), encoding='utf-8')
    (EXTERNAL / '03_school_split_protocol_note.md').write_text(build_md_03(src03), encoding='utf-8')
    (EXTERNAL / '04_fixed_school_combo_note.md').write_text(build_md_04(src04), encoding='utf-8')


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


def render_page(stem: str) -> None:
    cfg = PAGE_CONFIG[stem]
    template_path = cfg['template']
    md_path = EXTERNAL / f'{stem}.md'
    html_path = EXTERNAL / f'{stem}.html'

    soup = BeautifulSoup(template_path.read_text(encoding='utf-8'), 'html.parser')
    rendered = subprocess.check_output(['pandoc', '-f', 'gfm', '-t', 'html5', str(md_path)], text=True)
    rendered_soup = BeautifulSoup(rendered, 'html.parser')

    if soup.title:
        soup.title.string = cfg['title']

    badge = soup.select_one('.badge')
    if badge:
        badge.string = cfg['badge']
    hero_h1 = soup.select_one('.hero h1')
    if hero_h1:
        hero_h1.string = cfg['title']
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
    if main is None:
        raise ValueError(f'main.content not found in template {template_path}')
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
        footer_links.replace_with(build_footer_links(soup, cfg.get('footer_links', [])))

    html_path.write_text(str(soup), encoding='utf-8')


def render_all() -> None:
    for stem in PAGE_CONFIG:
        render_page(stem)
    shutil.copy2(EXTERNAL / '02_combined_formal_report.html', EXTERNAL / 'index.html')


def build_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    subprocess.run(['zip', '-rqX', str(ZIP_PATH.name), EXTERNAL.name], cwd=BASE, check=True)


if __name__ == '__main__':
    reset_package()
    write_markdown()
    render_all()
    build_zip()
