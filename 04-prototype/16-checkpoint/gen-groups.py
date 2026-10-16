#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-groups.py —— 组页生成器（11 组全出 + 分组索引）

输出：`12-groups/index.html` + `12-groups/<gid 小写>.html`，全部经 gen-common.page_shell 产出。

★ 形态 v2（2026-10-15，契约 DESIGN-CONTRACT §2 G4 收口）：把 `gen-nodes.py` 的**阅读单元**
  复用到组页（⛔ 不照抄内容），组页与节点页因此共用同一套形态语言：
  ① 标题区：`h1` = 纯中文组名（一行）＋ 英文名独立成行（`.page-en`）；
  ② 一行一件事：身份行 `.meta-line` 独占一行（组号 · 节点数 · 层范围 · 组内边数）；
  ③ 页首先给结论：`.read-map`（结论 = 组导读**首句**）＋ 可跳转的结构地图；
  ④ 区块带连续序号：`section(title, no, sid)` ⇒ `01..0n`，锚点与导读**双向闭合**；
  ⑤ 散文切成可扫单元：组导读过 `gen-common.prose_html`（主张句 + 展开点 + 适用边界）；
  ⑥ 依赖关系可读：组间前后继与组内依赖边都是 `.relchain` **一行结构**（⛔ 不长句罗列）；
  ⑦ ★ **本组 mini-DAG**（2026-10-16 第 6 轮 / G19·B″）：`.read-map` 之后一张**由 `dag.json` 数据派生**
    的自制图（本组内部依赖 + 对外接口 stub），与 `gen-figs.group_figs` **同源**（caption 也取自它，
     ⛔ 不在本文件另写一份文案）。位置与 `gen-nodes.py` 的图件同一体例。

★ R-11（长文字段一律竖表）在本页的**判定与理由**（⛔ 不是「见表就换竖表」）：
  · 「组内节点」→ 竖表。字段含**节点中文名 + 英文名**（实测最长 60+ 字符）；内容列 804px 下
    4 列横表的名称列只剩约 (804 − 5×16)/4 ≈ 180px ⇒ 必然折成 3–5 行并与邻列错位，
    「能一眼看齐」的前提不成立 ⇒ 转竖表（每节点一块、字段纵向排列）。
  · 「指向组外的前置」→ 竖表。字段含「为什么先学前者」（整句长文）⇒ 同上。
  · 「分组索引」的 6 列横表**保留**：字段全为短值（序号 4 + 组名 ≤12 字 + 三个计数 +
    层范围 9 字 ≈ 34 汉字 ≈ 510px，加 6×2×8px 内边距与边框 ≈ 620px < 804px）
    ⇒ **能一眼看齐**，横表在此确有优势。★ 该判定**未被判据覆盖**（⑫ 的对象只有组页的
    节点区 / 前后继区），作为局限如实登记在 `CRITERIA-CHANGE-P35-G4.md`。

★ 本轮形态变更（H2 硬规则 5 / H3 G2）：**撤掉 11 组彩虹色**。组身份改由
  「**中性色序号标记 + 文字标题**」承载（`.gseq` + `.gchip__name`），⛔ 不按组分配色相。
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
F = _imp(os.path.join(HERE, "gen-figs.py"), "pekg_gen_figs")

BASE = "../"

# 组页区块：**站点级约定**（⛔ 不是逐组内容），顺序即阅读顺序；序号 01..0n 由 section() 落。
SECTIONS = (
    ("sec-intro", "本组导读", 1),
    ("sec-nodes", "组内节点", 2),
    ("sec-path", "本组学习路径", 3),
    ("sec-rel", "组间前后继", 4),
)

# 分组索引区块（同一套约定）
INDEX_SECTIONS = (
    ("sec-intro", "本页导读", 1),
    ("sec-groups", "分组一览", 2),
    ("sec-howto", "怎么用这些组", 3),
)

# 分组索引的散文来源：★ 与 P35 ⑨/⑭ 的判据**同源**（门控直接调 groups_index_intro()），
# ⛔ 不在门控里另抄一份文本，也⛔ 不把「组数」写死在文案里（写死会随数据漂移）。
GROUPS_INDEX_INTRO = (
    "本页是全站知识分区的索引：全站按知识分区划为 {n} 组，分组编号与依赖深度（layer）是"
    "两套彼此独立的编号——前者是知识分区，后者是学习顺序的拓扑深度。"
    "分组身份由序号与名称承载，颜色在本站不承载任何可读信息。"
)

GROUPS_INDEX_HOWTO = (
    "按分组读适合「我关心某个方向」的读者：先在分组一览里定位方向，再进组页看它的节点与路径。"
    "按学习路径读适合「我按依赖顺序系统学一遍」的读者：那条路径与本页由同一份数据派生，"
    "不会与本页互相漂移。"
)


def groups_index_intro(groups):
    """分组索引的导读（唯一来源；门控 P35 ⑨/⑭ 直接调用本函数取散文来源）。"""
    return GROUPS_INDEX_INTRO.format(n=len(groups))


def _name_cell(n, page_exists):
    """节点名称格：中文名（可点）＋ 英文名（次级），⛔ 不把两者挤在同一行主文里。"""
    cn, en = C.split_name(n["name"], n.get("en", ""))
    nid = n["id"]
    if nid in page_exists:
        name = '<a href="%s">%s</a>' % (C.esc(BASE + C.node_page_rel(nid)), C.esc(cn))
    else:
        name = '%s <span class="badge badge--pending">架构在册</span>' % C.esc(cn)
    if en:
        name += ' <span class="nid">%s</span>' % C.esc(en)
    return name


def _node_blocks(members, page_exists):
    """组内节点 → **竖表**（R-11：节点名与英文名是长文字段，⛔ 不进横表）。"""
    blocks = []
    for n in sorted(members, key=lambda x: (x["layer"], x["id"])):
        blocks.append([
            ("节点", '<span class="nid">%s</span>' % C.esc(n["id"])),
            ("名称", _name_cell(n, page_exists)),
            ("依赖深度", "第 %d 层" % n["layer"]),
            ("内容状态", C.status_badge(n["content_status"])),
        ])
    return C.kv_blocks_html(blocks)


def _incoming_blocks(incoming, groups_by_id, node_group, page_exists):
    """指向组外的前置 → **竖表**（R-11：「为什么先学前者」是整句长文）。

    ★ 无入边时**不省略竖表**：改为一行「结论」块。理由是判据 P35 ⑪ 断言该区块内存在
      `.kv-blocks`（⛔ 不因数据为空而让判据在该页退化为恒真），且「无」本身就是一个值。
    """
    if not incoming:
        return C.kv_blocks_html([[("指向组外的前置", "无（本组不依赖其他分组的节点）")]])
    blocks = []
    for e in sorted(incoming, key=lambda x: (x["source"], x["target"])):
        src_g = node_group.get(e["source"], "")
        g = groups_by_id.get(src_g)
        src_g_cell = (C.group_chip(src_g, g["name"], BASE + C.group_page_rel(src_g))
                      if g else C.esc(src_g))
        blocks.append([
            ("来源分组", src_g_cell),
            ("组外节点", C.node_chip(e["source"], page_exists, BASE)),
            ("组内节点", C.node_chip(e["target"], page_exists, BASE)),
            ("关系", '<span class="tier">%s</span>' % C.esc(e.get("rel", ""))),
            ("为什么先学前者", C.esc(e.get("note", ""))),
        ])
    return C.kv_blocks_html(blocks)


def group_page(g, members, groups, edges, page_exists, node_group, groups_by_id, grp_figs):
    gid = g["id"]
    nxt = C.reveal_seq()
    cn_name, en_name = C.split_name(g["name"], g.get("en", ""))
    mem_ids = {m["id"] for m in members}
    inner_edges = sum(1 for e in edges if e["source"] in mem_ids and e["target"] in mem_ids)
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("知识分组", C.DIR_GROUPS + "/index.html"),
                                (g["name"], None)]))
    # ---- 标题区：中文名一行 / 英文名独立一行 / 身份行（各自独占一行）
    body.append('<h1>%s</h1>' % C.esc(cn_name))
    if en_name:
        body.append('<p class="page-en">%s</p>' % C.esc(en_name))
    body.append('<p class="meta-line">%s<span>组内节点 %d 个</span><span>层范围 第 %d – %d 层</span>'
                '<span>组内边 %d 条</span></p>'
                % (C.group_chip(gid, g["name"], BASE + C.group_page_rel(gid)), len(members),
                   min(n["layer"] for n in members), max(n["layer"] for n in members), inner_edges))
    # ---- 页首导读：一句话结论（组导读首句）+ 结构地图（先给结论，再给地图）
    body.append(C.read_map_html(C.lead_sentence(g.get("intro", "")), SECTIONS, reveal=nxt()))
    # ---- ★ 本组 mini-DAG（2026-10-16 第 6 轮 / G19·B″）：由 `dag.json` 数据派生，与 gen-figs 同源。
    #   位置与 `gen-nodes.py` 的图件同一体例（`.read-map` 之后、第一个编号区块之前）。
    #   ★ 两处**成对 fail-closed**（⛔ 不沿用 `figure_html` 对缺失 fid 静默返回空串的旧隐患：
    #     那会让「组页有图」这条判据在**构建期**看起来正常、只在门控期才报红，排查成本更高）：
    #     ① 派生表里必须有该 fid；② 磁盘上必须已渲染出该图（⇒ 构建链要求先跑 `gen-figs.py --write`）。
    fid = "grp-" + gid.lower()
    spec = grp_figs.get(fid)
    if spec is None:
        raise SystemExit("[FAIL] 组 %s 的派生图 %s 不存在（gen-figs.group_figs 未覆盖该组）" % (gid, fid))
    if fid not in C.load_figures():
        raise SystemExit("[FAIL] 图件 %s 未渲染：请先跑 `python3 gen-figs.py --write`" % fid)
    body.append(C.figure_html(fid, spec["caption"], reveal=nxt()))

    # 01 本组导读（主张句 + 展开点 + 适用边界）
    body.append(C.section("本组导读", 1, "sec-intro"))
    body.append(C.prose_html(g.get("intro", "")))
    # 02 组内节点（竖表：长文字段）
    body.append(C.section("组内节点", 2, "sec-nodes"))
    body.append('<p class="lede">按依赖深度（layer）升序；同层节点彼此无先后约束。</p>')
    body.append(_node_blocks(members, page_exists))
    # 03 本组学习路径（按层分组；依赖边一行一条）
    body.append(C.section("本组学习路径", 3, "sec-path"))
    body.append(_layer_blocks(members, edges, page_exists, nxt))
    # 04 组间前后继（一行结构）+ 指向组外的前置（竖表）
    body.append(C.section("组间前后继", 4, "sec-rel"))
    order = [x["id"] for x in groups]
    idx = order.index(gid)
    prev_g = groups[idx - 1] if idx > 0 else None
    next_g = groups[idx + 1] if idx < len(groups) - 1 else None
    body.append(C.group_relchain_html(gid, prev_g, next_g, BASE))
    body.append("<h3>指向组外的前置</h3>")
    incoming = [e for e in edges if e["target"] in mem_ids and e["source"] not in mem_ids]
    body.append(_incoming_blocks(incoming, groups_by_id, node_group, page_exists))
    return C.page_shell(BASE, "group", gid, "%s %s" % (gid, g["name"]), "\n".join(body),
                        nav_extra=[(BASE + C.DIR_GROUPS + "/index.html", "知识分组索引")])


def _layer_blocks(members, edges_all, page_exists, nxt):
    """本组学习路径：按 layer 升序，逐层列出节点与「为什么在这层」。

    ★ 依赖关系一律走 `.relchain` **一行结构**（一条边一行）。原实现把多条边拼成
      「A ← B：…；A ← C：…」的 run-on 长句（读者要自己切分），本轮改为每行一件事：
      「前置 → 本节点」是结构行，「理由：…」是随行的次级标签。
    ★ 入边不限于组内：组外前置同样是「为什么在这层」的依据（原实现的语义，保持不变）。
    """
    by_layer = {}
    for n in members:
        by_layer.setdefault(n["layer"], []).append(n)
    out = []
    for lv in sorted(by_layer):
        ns = sorted(by_layer[lv], key=lambda x: x["id"])
        out.append(C.layer_block_html(lv, ns, edges_all, page_exists, BASE, nxt()))
    return "\n".join(out)


def index_page(groups, nodes, edges, page_exists):
    nxt = C.reveal_seq()
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("知识分组", None)]))
    body.append("<h1>知识分组</h1>")
    body.append('<p class="meta-line"><span>分组 %d 个</span><span>节点 %d 个</span>'
                '<span>组内边 %d 条</span></p>'
                % (len(groups), len(nodes),
                   sum(1 for e in edges if _same_group(e, nodes))))
    body.append(C.read_map_html(C.lead_sentence(groups_index_intro(groups)), INDEX_SECTIONS,
                                reveal=nxt()))
    body.append(C.section("本页导读", 1, "sec-intro"))
    body.append(C.prose_html(groups_index_intro(groups)))
    body.append(C.section("分组一览", 2, "sec-groups"))
    body.append('<div class="legend" data-reveal="1" style="--i:%d">%s</div>'
                % (nxt(), "".join(C.group_chip(g["id"], g["name"], BASE + C.group_page_rel(g["id"]))
                                  for g in groups)))
    body.append('<div class="table-scroll" data-reveal="1" style="--i:%d">'
                '<table><caption>组内节点数、层范围与组内边数。</caption>'
                "<thead><tr><th>序号</th><th>名称</th><th>节点数</th><th>层范围</th><th>组内边</th>"
                "<th>已写满</th></tr></thead><tbody>"
                % nxt())
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        ids = {m["id"] for m in mem}
        inner = sum(1 for e in edges if e["source"] in ids and e["target"] in ids)
        body.append("<tr><td>%s</td><td><a href=\"%s\">%s</a></td>"
                    "<td>%d</td><td>第 %d – %d 层</td><td>%d</td><td>%d</td></tr>"
                    % (C.group_mark(g["id"]),
                       C.esc(BASE + C.group_page_rel(g["id"])), C.esc(g["name"]), len(mem),
                       min(n["layer"] for n in mem), max(n["layer"] for n in mem), inner,
                       sum(1 for n in mem if n["content_status"] == "complete")))
    body.append("</tbody></table></div>")
    body.append(C.section("怎么用这些组", 3, "sec-howto"))
    body.append(C.prose_html(GROUPS_INDEX_HOWTO))
    body.append('<p class="lede">入口：<a href="%s">学习路径</a>（按依赖顺序读）。</p>'
                % C.esc(BASE + C.DIR_VIEWS + "/01-learning-path.html"))
    return C.page_shell(BASE, "group", "GROUPS-INDEX", "知识分组", "\n".join(body))


def _same_group(e, nodes):
    """边两端是否同组（供索引页的「组内边」计数；⛔ 只读真相源，不改数据）。"""
    g = {n["id"]: n["group"] for n in nodes}
    return g.get(e["source"]) is not None and g.get(e["source"]) == g.get(e["target"])


def generate(root=None):
    data = C.load_sources()
    dag = data["dag"]
    nodes = dag["nodes"]
    groups = sorted(dag["groups"], key=lambda g: g["order"])
    edges = dag["edges"]
    page_exists = {n["id"] for n in nodes if n["content_status"] == "complete"}
    node_group = {n["id"]: n["group"] for n in nodes}
    groups_by_id = {g["id"]: g for g in groups}
    out = {"%s/index.html" % C.DIR_GROUPS: index_page(groups, nodes, edges, page_exists)}
    grp_figs = F.group_figs(nodes, groups, edges)     # ★ 单源：caption 与 gen-figs 出图同源
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        out["%s/%s.html" % (C.DIR_GROUPS, g["id"].lower())] = group_page(
            g, mem, groups, edges, page_exists, node_group, groups_by_id, grp_figs)
    return out


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
