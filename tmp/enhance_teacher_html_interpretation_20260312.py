from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path('/Users/angus/Downloads/20260310_张淑贤_脂质组学预测的模型')
TEACHER = ROOT / 'outputs' / '20260311_responder_followup' / 'teacher_report_package'


def insert_before_once(text: str, marker: str, block: str, unique: str) -> str:
    if unique in text:
        return text
    if marker not in text:
        raise ValueError(f'marker not found: {marker}')
    return text.replace(marker, block.rstrip() + '\n\n' + marker, 1)


def patch_markdown() -> None:
    # 01_followup_report.md
    p = TEACHER / '01_followup_report.md'
    text = p.read_text(encoding='utf-8')
    block = '''## 怎么读这页

1. **先看主锚点**：strict nested CV outer-test AUC≈0.50–0.54 仍没变，这决定了正式主结论的上限。
2. **再看 grouped split / out-phase 数字**：核心不是看有没有某一格分数更高，而是看信号在更严切法下还能不能站住。
3. **再看 F1–F6**：这些图的作用是解释“为什么不能只报最高 AUC”，以及“为什么要同时看 gap、split-level 分布、时相迁移”。
4. **最后看 protocol 与 blocked**：知道当前主文能写到哪一步，哪些细节应该放补充材料或等后续数据到位再写。

## 结构性解读

- `repeated_random_holdout` 普遍高于 `leave_one_school_out`，说明**随机切分更乐观**，而真实学校 grouped split 更接近来源异质性的检验。
- `clinical_baseline_main` 的上限不是最高，但 **generalization gap 最小**，因此它更适合作为当前最稳妥、最防守的主叙事。
- `compact_fusion` 往往能给出更高的 train AUC，但 school split / out-phase 下 gap 更大，说明它更像“容量更高但稳定性更弱”的路线。
- `outphase_leave_one_school_out` 进一步下降，提示**时相迁移比同相 grouped split 更难**；这支持“信号 modest but not robust enough”，不支持“强泛化已建立”。

## 不能过度宣称的点

- 这里所有补充分析都属于**内部验证**，不是 external validation。
- 用户记得的 **AUC≈0.8** 仍然只对应 strict nested CV 的 `mean_train_auc`，不是 outer-test AUC。
- 这页的价值是把“边界、稳定性、风险”讲清楚，而不是把 headline 从 0.53 改写成更高的 test AUC。'''
    text = insert_before_once(text, '## 新分析放在哪里', block, '## 怎么读这页')
    p.write_text(text, encoding='utf-8')

    # 02_combined_report.md
    p = TEACHER / '02_combined_report.md'
    text = p.read_text(encoding='utf-8')
    block = '''## 怎么用这一包做汇报

- **第 1 分钟**：先讲 strict nested CV outer-test AUC≈0.50–0.54 仍是正式主结果，AUC≈0.8 只对应 mean_train_auc。
- **第 2–4 分钟**：用 Figure 2–4 说明，真实 school split 补跑以后，模型之间更重要的差别是“稳不稳”，不是“谁偶尔更高一点”。
- **第 5–6 分钟**：用 Figure 5–6 说明 out-phase internal temporal validation 已经接进来，但时相迁移仍更难。
- **最后 1 分钟**：用 Figure 7 + protocol 写法说明，把当前能写什么、还缺什么、不能过度说什么一次讲清楚。

> 如果老师只想听一句话：这套包的核心价值，不是把分数做高，而是把“正式主结果 + grouped split + out-phase + protocol 边界”串成一条能防守的解释链。'''
    text = insert_before_once(text, '## Figure 1. 基线主图：既有 strict nested CV 正式主结果锚点', block, '## 怎么用这一包做汇报')

    block = '''## 把 7 张图串起来看

- **Figure 1** 负责定锚：正式主结果仍是 strict nested CV，而不是 follow-up 里任何单次切法。
- **Figure 2–3** 负责比较模型路线：它们告诉我们为什么不能只拿最高 AUC 当主结论，而要同时看 gap 和稳健性。
- **Figure 4** 负责看 split-level 稳定性：证明不是一次随机切分碰巧得到的数字。
- **Figure 5–6** 负责看时相迁移：提醒我们 baseline → out-phase 的问题比同相 grouped split 更难。
- **Figure 7** 负责交代标签边界：当前 responder 标签还能先用，但并不代表 alternative grouping sensitivity 已完成。

## 不能过度宣称的点

- school split、fixed school combo split、repeated hold-out、out-phase internal temporal validation 都**不能写成 external validation**。
- 这套包支持的是“当前信号 modest、边界更清楚、表达更稳妥”，不支持“跨校区强泛化已被证明”。
- 新增的 fixed school combo 页面（`04_fixed_school_combo_note.html`）也只是把 train/test 组合切法讲得更具体，**不会改变正式主结果锚点**。'''
    text = insert_before_once(text, '## 学校 split 与 protocol 写法对应页', block, '## 把 7 张图串起来看')
    p.write_text(text, encoding='utf-8')

    # 03_literature_followup_note.md
    p = TEACHER / '03_literature_followup_note.md'
    text = p.read_text(encoding='utf-8')
    block = '''## 怎么读这页

- 这页不是用来展示“又做出了一个更高的 AUC”，而是用来回答两个更实际的问题：**学校 / 社区 split 现在到底放在哪里了？运动 protocol 正文该怎么写才稳妥？**
- 因此它的阅读顺序应该是：**先看文献启发 → 再看本地已落地分析 → 最后看现在能怎么写、不能怎么写**。
- 如果把 02 页看成“汇报总页”，那这页就是“老师追问时的解释页”。'''
    text = insert_before_once(text, '## 1. 这轮新增分析现在放在哪里', block, '## 怎么读这页')

    block = '''## 结构性解读：文献启发怎样映射到本项目

- 徐爱民团队那篇文章真正给我们的启发，不是“借一句 external validation 说法”，而是：**如果来源分组是真实且可审计的，就优先做 grouped split / cohort-style checking**。
- Nature Medicine 那篇文章给的启发则是：**cohort 内 repeated cross-validation 和内部验证本身也可以成为 honest evidence**，前提是口径不能越界。
- 放到我们项目里，当前最合理的落点就是：**真实学校 grouped split + out-phase internal temporal validation** 已经补上，但它们仍然都在同一项目框架内，因此不能升级表述为 external validation。
- 这也是为什么运动 protocol 的正文写法要保守：当前 prediction 的核心任务还是守住主结果边界，而不是在主文里过早铺开所有场地/强度细节。'''
    text = insert_before_once(text, '## 5. 现在可以怎么写，不能怎么写', block, '## 结构性解读：文献启发怎样映射到本项目')

    block = '''## 如果老师追问，可以怎么回答

- **问：学校 / 社区 split 现在到底做了没有？**  
  答：已经做了，真实学校映射来自 `运动强度分组_401人`，结果落在 `school_group_holdout_summary.csv`、`self_validation_summary.csv` 和 `outphase_validation_summary.csv`。
- **问：那为什么还不能叫 external validation？**  
  答：因为这些 split 仍然来自同一项目内部，只是按真实 school/source grouping 与时相去切，不是独立新 cohort。
- **问：运动 protocol 为什么不在主文里一次写很细？**  
  答：因为主文当前更需要先把主结果与验证边界讲清楚；学校-强度细节已经内部整理完成，更适合放补充材料或答审时展开。'''
    text = insert_before_once(text, '## 8. 一句话结论', block, '## 如果老师追问，可以怎么回答')
    p.write_text(text, encoding='utf-8')

    # 04_fixed_school_combo_note.md
    p = TEACHER / '04_fixed_school_combo_note.md'
    text = p.read_text(encoding='utf-8')
    block = '''## 怎么读这页

1. **先看方案设计**：不要一上来只盯某一格 AUC，而要先看 train/test 样本量、response rate gap、intensity 覆盖是否合理。
2. **再看 B 为什么是主方案**：它不是因为“所有数字都最高”，而是因为更像真正的多校区固定 hold-out。
3. **最后再看 A 的 sensitivity 价值**：A 的作用不是取代 B，而是检验“换一种更平衡的切法，结论会不会根本改变”。

> 这页真正要回答的不是“哪一套切法赢了”，而是“固定校区 train/test 组合之后，我们的结论边界有没有改变”。'''
    text = insert_before_once(text, '## 1. 为什么要单独做固定校区组合版 split', block, '## 怎么读这页')

    block = '''## A / B 并排后的真正结论

- **方案 B** 在 `clinical_baseline_main` 上更好，尤其 out-phase 仍能保持在 **0.5325** 左右，因此它更适合作为当前对老师汇报的主固定 split。
- **方案 A** 在 response rate 上更平衡，也让 `compact_fusion` 的数值看起来稍好一些，但这并没有消除它的大 gap 问题。
- 两套切法下，模型排序会有一些细节变化，但**没有任何一个模型在 A/B 两套方案下都表现出一致、强而稳定的跨校区泛化**。
- 因此 A/B 并排之后最重要的收获不是“挑出更高分的一套”，而是可以更稳妥地说：**固定校区 train/test 的具体切法会影响局部数值，但不会把当前结论从 modest signal 改写成 strong generalization**。'''
    text = insert_before_once(text, '## 5. 当前最稳妥的老师口径', block, '## A / B 并排后的真正结论')

    block = '''## 如果老师追问：为什么不直接改成方案 A？

- 因为 **B 的结构更合理**：test 侧样本量更大，而且 train/test 两边都覆盖 3 种 intensity，更接近“多校区固定 hold-out”的主问题。
- 因为 **A 的定位本来就是 sensitivity**：它更像在问“如果用更平衡的 response rate 组合切一次，结论会不会变”。
- 现在 A 已经补跑，所以我们可以更从容地说：**不是没试过别的切法，而是试过以后，边界并没有根本变化。**

> 可直接给老师的一句话：固定校区组合版 split 我们现在已经有主方案 B，也补跑了方案 A 做 sensitivity；两套切法结论方向一致——当前信号可以说存在，但还不足以写成强跨校区泛化或 external validation。'''
    text = insert_before_once(text, '## 6. 包内可直接打开的文件', block, '## 如果老师追问：为什么不直接改成方案 A？')
    p.write_text(text, encoding='utf-8')


def render_page(md_path: Path, html_path: Path) -> None:
    soup = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')
    rendered = subprocess.check_output(['pandoc', '-f', 'gfm', '-t', 'html5', str(md_path)], text=True)
    rendered_soup = BeautifulSoup(rendered, 'html.parser')

    main = soup.select_one('main.content')
    if main is None:
        raise ValueError(f'main.content not found in {html_path}')
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

    html_path.write_text(str(soup), encoding='utf-8')


def render_all() -> None:
    pages = [
        '01_followup_report',
        '02_combined_report',
        '03_literature_followup_note',
        '04_fixed_school_combo_note',
    ]
    for stem in pages:
        render_page(TEACHER / f'{stem}.md', TEACHER / f'{stem}.html')
    shutil.copy2(TEACHER / '02_combined_report.html', TEACHER / 'index.html')


if __name__ == '__main__':
    patch_markdown()
    render_all()
