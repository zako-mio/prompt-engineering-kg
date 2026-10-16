#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-views.py —— 视图页生成器

输出（全部经 gen-common.page_shell 产出）：
  - `14-views/01-learning-path.html`：按拓扑层序的学习路径，每层列出节点与「为什么在这层」
  - `14-views/02-frontier.html`：新一代模块，由 frontier.json 驱动；
      edition / as_of / 每条 status 徽标 / supersedes 指向 / 未实测标注

★ 形态 v2（2026-10-15，契约 DESIGN-CONTRACT §2 G4 收口）：两页都改用 `gen-nodes.py` 的
  **阅读单元**（⛔ 不照抄节点内容）：
  ① 页首先给结论：`.read-map`（结论 = 本页导语**首句**）＋ 可跳转的结构地图；
  ② 区块带连续序号：`section(title, no, sid)` ⇒ `01..0n`，锚点与导读**双向闭合**；
  ③ 散文切成可扫单元：页级导语过 `gen-common.prose_html`（主张句 + 展开点）；
  ④ 依赖关系可读：层块内的每条依赖边是一行 `.relchain`（前置 → 本节点 + 理由）。

★ 章区块的锚点为什么用罗马小写字母（`sec-chapter-i`）：全站区块 id 的口径是 `sec-[a-z-]+`
  （P35 ④ 的正则），⛔ 不去改判据正则来迁就命名 ⇒ 章号改用罗马小写字母；
  章数超出命名表即 **fail-closed**（`SystemExit`），⛔ 不静默生成一个判据抓不到的 id。

★ 本轮形态变更：分组标识改为「中性序号 + 文字标题」（⛔ 色相不承载身份）；
  层块与条目卡挂 `data-reveal` 参与错峰进场（每页实例数受动效预算上界约束）。
"""

import importlib.util
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_common")

BASE = "../"

UNVERIFIED_NOTE = "本条尚未在本机实测；请按离线复现步骤自行验证后再采信。"

# 前沿条目的自制图（键 = 条目 id；图件由 `gen-figs.py` 预渲染入库）
FRONTIER_FIG = {
    "PE-N-01": ("pe-n-01", "时间轴：三代范式的重心迁移——叠加而非替代。"),
}

LAYERS_PER_CHAPTER = 4

# ---- 散文来源（★ 与 P35 ⑨/⑭ 的判据**同源**：门控直接调下面的函数/常量取来源文本，
#      ⛔ 不在门控里另抄一份文案；⛔ 也不把「节点数」写死在文案里（写死会随数据漂移）。）

LEARNING_PATH_INTRO = (
    "本页按依赖深度（拓扑层）逐层展开全站 {n} 个节点：层序由边方向推导，A→B 表示先学 A 再学 B，"
    "因此第 N 层的每个节点都只依赖第 N 层之前的节点。同一层内的节点彼此没有先后约束，"
    "可按任意顺序学。读法有三条：其一，先看每层块里的「前置」一行，它给出该节点在本页内的"
    "全部前置与理由；其二，同层节点按节点编号排序，不表示学习顺序；其三，本页按每章最多四层"
    "分章，分章只影响进场动画的错峰单元，不改变层序与内容。"
)

FRONTIER_INTRO = (
    "本模块只含数据、不含教程正文，是本站唯一被设计为「每次大更新只刷新一处」的分区："
    "条目带时间锚、版次、状态与取代关系，刷新动作被定义为改条目集合与时间锚、重跑生成器与门控，"
    "不改任何页面模板。"
)

LP_SECTIONS = (("sec-intro", "本页导读", 1),)

FRONTIER_SECTIONS = (
    ("sec-intro", "本页导读", 1),
    ("sec-items", "条目", 2),
    ("sec-tracking", "跟踪渠道", 3),
    ("sec-refresh", "刷新流程", 4),
)

ROMAN = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii")


def learning_path_intro(dag):
    """学习路径页的导语（唯一来源；门控 P35 ⑨/⑭ 直接调用本函数取散文来源）。"""
    return LEARNING_PATH_INTRO.format(n=len(dag["nodes"]))


def chapter_sid(i):
    """章区块锚点 id（`sec-chapter-i` …）。超出命名表即 fail-closed，⛔ 不静默降级。"""
    if not (1 <= i <= len(ROMAN)):
        raise SystemExit("[FAIL] 章数 %d 超出锚点命名表（%d 章）—— 请扩展 ROMAN，"
                         "并复核 P35 ④ 的 id 口径" % (i, len(ROMAN)))
    return "sec-chapter-%s" % ROMAN[i - 1]


def learning_path_page(dag, page_exists, page_rel=None):
    nodes = dag["nodes"]
    edges = dag["edges"]
    by_layer = {}
    for n in nodes:
        by_layer.setdefault(n["layer"], []).append(n)
    layers = sorted(by_layer)
    nxt = C.reveal_seq()
    intro = learning_path_intro(dag)
    # ★ 分章：每 %d 层一章。分章的作用是把**进场错峰**的实例数收进动效预算上界
    #   （P28：单页 [data-reveal] ≤16、进场完成 ≤1800ms）。⛔ 不是「少讲内容」——
    #   所有层都在页内，只是每章作为一次进场单元；层块本身**不再**挂 data-reveal。
    chapters = [layers[i:i + LAYERS_PER_CHAPTER] for i in range(0, len(layers), LAYERS_PER_CHAPTER)]
    sections = list(LP_SECTIONS) + [(chapter_sid(ci + 1), "第 %d – %d 层" % (ch[0], ch[-1]), ci + 2)
                                    for ci, ch in enumerate(chapters)]
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("学习路径", None)]))
    body.append("<h1>学习路径</h1>")
    body.append('<p class="meta-line"><span>层数 %d</span><span>节点 %d</span><span>边 %d</span>'
                '<span>已写满 %d</span><span>架构在册 %d</span></p>'
                % (len(by_layer), len(nodes), len(edges),
                   sum(1 for n in nodes if n["content_status"] == "complete"),
                   sum(1 for n in nodes if n["content_status"] == "registered")))
    body.append(C.read_map_html(C.lead_sentence(intro), tuple(sections), reveal=nxt()))
    body.append(C.section("本页导读", 1, "sec-intro"))
    body.append(C.prose_html(intro))
    for ci, ch in enumerate(chapters):
        body.append('<section class="layer-chapter" data-reveal="1" style="--i:%d">' % nxt())
        body.append(C.section("第 %d – %d 层" % (ch[0], ch[-1]), ci + 2, chapter_sid(ci + 1)))
        for lv in ch:
            ns = sorted(by_layer[lv], key=lambda x: x["id"])
            body.append(C.layer_block_html(lv, ns, edges, page_exists, BASE, show_group=True))
        body.append("</section>")
    return C.page_shell(BASE, "view", "01-learning-path", "学习路径", "\n".join(body),
                        # ★ SH4：description 取本页导语首句（与 `.read-map` 同源）
                        meta_desc=C.lead_sentence(intro),
                        page_rel=page_rel or C._derive_page_rel("view", "01-learning-path"))


def _item_html(item, as_of, edition, nxt):
    """条目卡 v2（2026-10-15 用户走查反馈 #1：此前是「标题 + 一大段 summary + dl 元信息」的文字墙）。

    ★ 形态：主张句（加重）→ 展开点（每句一行；其中**显式枚举**（其一/其二/…）渲染为
      `.enum-list` 有序列表）→ 自制图 → **元信息独占一行** → 证据表 → 复现说明。
      ⛔ 元信息不再与正文混排。
    """
    nid = item["id"]
    sup = item.get("supersedes") or []
    sup_html = "、".join('<a href="%s">%s</a>' % (C.esc(BASE + C.node_page_rel(s)), C.esc(s))
                        if s in _PUBLISHED else '<span class="nid">%s</span>' % C.esc(s)
                        for s in sup) or "无"
    # ★ 2026-10-15（R-10 / 契约 G1 收口）
    #   ⛔ 不再自己拼「主张句 + 平铺 li」。理由：该条目的 summary 里就有显式枚举标记
    #   （「争议三处：其一，…；其二，…；其三，…」），而旧写法把它渲染成三个平铺 li
    #   ⇒ **层次仍由「其一/其二/其三」这几个字承担**，正是 R-10 要消除的形态。
    #   改走同一渲染函数后，站内散文只有**一个**切分口径（P35 ⑨ 与它同源）。
    prose_html = C.prose_html(item.get("summary", ""))
    fig = ""
    if nid in FRONTIER_FIG:
        fid, cap = FRONTIER_FIG[nid]
        fig = C.figure_html(fid, cap)
    ev = C.ev_table_html(item.get("evidence")) if item.get("evidence") else ""
    repro = item.get("offline_repro", "")
    unverified = (item.get("status") == "unverified" or not repro
                  or "未在本机实测" in repro or "未实测" in repro)
    return ('<section class="card--flat" data-reveal="1" style="--i:%d" '
            'data-frontier-item="%s" data-as-of="%s" data-edition="%s">'
            '<h3>%s <span class="nid">%s</span> %s</h3>'
            '%s'
            '%s'
            '<p class="meta-line"><span>时间锚 %s</span><span>版次 %s</span>'
            '<span>取代关系 %s</span></p>'
            '%s'
            '<div class="%s"><p><strong>离线复现：</strong>%s</p></div>'
            "</section>"
            % (nxt(), C.esc(nid), C.esc(as_of), C.esc(edition), C.esc(item.get("title", "")),
               C.esc(nid), C.frontier_status_badge(item.get("status", "")), prose_html,
               fig, C.esc(as_of), C.esc(edition), sup_html, ev,
               "danger-note" if unverified else "notice", C.esc(repro)))


_PUBLISHED = set()


def frontier_page(frontier, page_exists, page_rel=None):
    global _PUBLISHED
    _PUBLISHED = set(page_exists)
    as_of = frontier.get("as_of", "")
    edition = frontier.get("edition", "")
    items = frontier.get("items", [])
    nxt = C.reveal_seq()
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("新一代模块", None)]))
    body.append("<h1>新一代模块</h1>")
    body.append('<p class="meta-line"><span>时间锚 %s</span><span>版次 %s</span>'
                '<span>上一般次 %s</span><span>条目 %d 条</span></p>'
                % (C.esc(as_of), C.esc(edition), C.esc(frontier.get("previous_edition") or "无"),
                   len(items)))
    body.append(C.read_map_html(C.lead_sentence(FRONTIER_INTRO), FRONTIER_SECTIONS, reveal=nxt()))
    body.append(C.section("本页导读", 1, "sec-intro"))
    body.append(C.prose_html(FRONTIER_INTRO))

    body.append(C.section("条目", 2, "sec-items"))
    counts = {}
    for it in items:
        counts[it.get("status", "")] = counts.get(it.get("status", ""), 0) + 1
    body.append('<div class="legend">%s</div>'
                % "".join("%s × %d" % (C.frontier_status_badge(k), counts[k]) for k in sorted(counts)))
    body.append('<div class="notice"><strong>状态三值口径：</strong>已确认 = 多源同向且可复核；'
                "有争议 = 存在反向证据或未获权威裁定，本站不代读者裁定；"
                "未证实 = 尚未取得足以支撑的独立证据。<strong>未实测标注</strong>指该条未在本机跑通，"
                "只给出可执行的复现步骤。</div>")
    for it in sorted(items, key=lambda x: x.get("id", "")):
        body.append(_item_html(it, as_of, edition, nxt))

    body.append(C.section("跟踪渠道", 3, "sec-tracking"))
    body.append('<div class="table-scroll"><table><caption>四类最小跟踪集；刷新时按渠道逐条回源并记录日期。</caption>'
                "<thead><tr><th>渠道</th><th>类型</th><th>用途与使用纪律</th></tr></thead><tbody>")
    for ts in frontier.get("tracking_sources", []):
        body.append("<tr><td><a href=\"%s\" rel=\"noopener noreferrer\">%s</a></td><td>%s</td><td>%s</td></tr>"
                    % (C.esc(ts.get("url", "")), C.esc(ts.get("name", "")), C.esc(ts.get("kind", "")),
                       C.esc(ts.get("note", ""))))
    body.append("</tbody></table></div>")

    body.append(C.section("刷新流程", 4, "sec-refresh"))
    body.append('<ol class="tight"><li>只改新一代模块的条目集合文件：版次、时间锚与条目状态或取代关系。</li>'
                "<li>重跑生成器；除本模块外的产物不应发生变化。</li>"
                "<li>过门控：条目必备字段、状态取值域、取代关系可解析、其余产物摘要变化数须为 0。</li></ol>")
    body.append('<p class="lede">本模块对应分组 <a href="%s">%s</a>；'
                "条目对应的知识节点在 <a href=\"%s\">交互全景图</a> 中可定位。</p>"
                % (C.esc(BASE + C.group_page_rel("GD-N")), C.group_chip("GD-N", "新一代模块"),
                   C.esc(BASE + C.DIR_INTERACTIVE + "/index.html#group-GD-N")))
    return C.page_shell(BASE, "view", "02-frontier", "新一代模块", "\n".join(body),
                        # ★ SH4：description 取本页导语首句（与 `.read-map` 同源）
                        meta_desc=C.lead_sentence(FRONTIER_INTRO),
                        page_rel=page_rel or C._derive_page_rel("view", "02-frontier"))


def generate(root=None):
    data = C.load_sources()
    dag = data["dag"]
    page_exists = {n["id"] for n in dag["nodes"] if n["content_status"] == "complete"}
    # ★ SH4：把**产物路径本身**传给页面构建器 ⇒ canonical 与产物同源（⛔ 不在别处另推一份）
    lp_rel = "%s/01-learning-path.html" % C.DIR_VIEWS
    fr_rel = "%s/02-frontier.html" % C.DIR_VIEWS
    return {
        lp_rel: learning_path_page(dag, page_exists, page_rel=lp_rel),
        fr_rel: frontier_page(data["frontier"], page_exists, page_rel=fr_rel),
    }


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
