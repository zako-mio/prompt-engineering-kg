#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-md.py —— Markdown 镜像生成器

输出（`15-md/`）：index / groups（含 index 与每组成员）/ nodes（已写满节点）/ learning-path / frontier。
镜像为纯 Markdown：⛔ 不含 HTML 标签、⛔ 不引用 .html（人类入口一律是 HTML 页）。
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

STATUS_MD = {"complete": "内容已写满", "registered": "架构在册 · 内容待填充"}
FSTATUS_MD = {"confirmed": "已确认", "disputed": "有争议", "unverified": "未证实"}


def _md_escape(s):
    return str(s if s is not None else "").replace("\n", " ")


def node_md(node, groups_by_id):
    g = groups_by_id[node["group"]]
    L = []
    L.append("# %s" % _md_escape(node["name"]))
    L.append("")
    L.append("- 节点标识：%s" % node["id"])
    L.append("- 英文名：%s" % _md_escape(node.get("en", "")))
    L.append("- 所属分组：%s %s" % (node["group"], _md_escape(g["name"])))
    L.append("- 依赖深度：第 %d 层" % node["layer"])
    L.append("- 内容状态：%s" % STATUS_MD.get(node["content_status"], node["content_status"]))
    L.append("- 标签：%s" % "、".join(node.get("tags", []) or ["无"]))
    L.append("")
    L.append("## 为什么需要它")
    L.append("")
    L.append(_md_escape(node.get("why", "")))
    L.append("")
    # ★ 2026-10-16（B-1）：`boundary` 已升为节点级一等字段 ⇒ MD 镜像必须同批跟上。
    #   ⛔ 否则 HTML 页有「适用边界」块、MD 镜像没有——同一份内容的两个出口不一致，
    #   而且这一面**无判据覆盖**（P13 只断言镜像存在，不比对内容）。
    if node.get("boundary"):
        L.append("**适用边界**")
        L.append("")
        L.append(_md_escape(node.get("boundary")))
        L.append("")
    L.append("## 机制说明")
    L.append("")
    L.append(_md_escape(node.get("intro", "")))
    L.append("")
    L.append("## 何时该用 / 何时不该用")
    L.append("")
    for w in node.get("when", []):
        L.append("- %s" % _md_escape(w))
    L.append("")
    L.append("## 实验台")
    L.append("")
    for it in node.get("lab", []):
        L.append("### %s（%s）" % (_md_escape(it.get("kind", "")), _md_escape(it.get("lang", ""))))
        L.append("")
        L.append("```%s" % _md_escape(it.get("lang", "")))
        L.append(str(it.get("text", "")))
        L.append("```")
        L.append("")
        L.append("预期观察：%s" % _md_escape(it.get("expect", "")))
        L.append("")
    if not node.get("lab"):
        L.append("本轮未写。")
        L.append("")
    L.append("## 证据")
    L.append("")
    for ev in node.get("evidence", []):
        L.append("- **%s**（%s，%s）" % (_md_escape(ev.get("claim", "")), ev.get("source_id", ""), ev.get("tier", "")))
        L.append("  - 出处：%s" % ev.get("url", ""))
        L.append("  - 原文关键句：%s" % _md_escape(ev.get("quote", "")))
    if not node.get("evidence"):
        L.append("本轮未写。")
    L.append("")
    L.append("## 术语")
    L.append("")
    for t in node.get("terms", []):
        head, _, tail = str(t).partition("：")
        L.append("- **%s**：%s" % (_md_escape(head), _md_escape(tail)))
    if not node.get("terms"):
        L.append("本轮未写。")
    L.append("")
    L.append("## 失效模式")
    L.append("")
    for p in node.get("pitfalls", []):
        L.append("- %s" % _md_escape(p))
    if not node.get("pitfalls"):
        L.append("本轮未写。")
    L.append("")
    L.append("## 一句话小结")
    L.append("")
    L.append(_md_escape(node.get("summary", "")))
    L.append("")
    L.append("## 在本站知识结构中的位置")
    L.append("")
    L.append("- 前置：%s" % ("、".join(node.get("prereq", [])) or "无"))
    L.append("- 后继：%s" % ("、".join(node.get("successors", [])) or "无"))
    L.append("")
    return "\n".join(L)


def group_md(g, members, groups, edges, node_group):
    ids = {m["id"] for m in members}
    L = []
    L.append("# %s %s" % (g["id"], _md_escape(g["name"])))
    L.append("")
    L.append("- 英文名：%s" % _md_escape(g["en"]))
    L.append("- 分区序号：%d" % g["order"])
    L.append("- 组内节点：%d 个（已写满 %d）"
             % (len(members), sum(1 for m in members if m["content_status"] == "complete")))
    L.append("- 层范围：第 %d – %d 层" % (min(m["layer"] for m in members), max(m["layer"] for m in members)))
    L.append("")
    L.append("## 本组导读")
    L.append("")
    L.append(_md_escape(g.get("intro", "")))
    L.append("")
    L.append("## 组内节点")
    L.append("")
    L.append("| 依赖深度 | 节点 | 名称 | 内容状态 |")
    L.append("|---|---|---|---|")
    for n in sorted(members, key=lambda x: (x["layer"], x["id"])):
        L.append("| %d | %s | %s | %s |"
                 % (n["layer"], n["id"], _md_escape(n["name"]),
                    STATUS_MD.get(n["content_status"], n["content_status"])))
    L.append("")
    L.append("## 本组学习路径")
    L.append("")
    by_layer = {}
    for n in members:
        by_layer.setdefault(n["layer"], []).append(n)
    for lv in sorted(by_layer):
        L.append("### 第 %d 层" % lv)
        L.append("")
        for n in sorted(by_layer[lv], key=lambda x: x["id"]):
            L.append("- %s %s" % (n["id"], _md_escape(n["name"])))
        L.append("")
        for n in sorted(by_layer[lv], key=lambda x: x["id"]):
            ins = [e for e in edges if e["target"] == n["id"]]
            if not ins:
                L.append("- 为什么在这层：起点层，无前置依赖。")
            for e in sorted(ins, key=lambda x: x["source"]):
                L.append("- 为什么在这层：%s ← %s（%s）%s"
                         % (n["id"], e["source"], e.get("rel", ""), _md_escape(e.get("note", ""))))
        L.append("")
    L.append("## 组间前后继")
    L.append("")
    order = [x["id"] for x in groups]
    i = order.index(g["id"])
    prev_g = groups[i - 1] if i > 0 else None
    next_g = groups[i + 1] if i < len(groups) - 1 else None
    L.append("- 上一组：%s" % (("%s %s" % (prev_g["id"], prev_g["name"])) if prev_g else "无"))
    L.append("- 下一组：%s" % (("%s %s" % (next_g["id"], next_g["name"])) if next_g else "无"))
    L.append("")
    L.append("## 指向组外的前置")
    L.append("")
    incoming = [e for e in edges if e["target"] in ids and e["source"] not in ids]
    if incoming:
        L.append("| 来源分组 | 组外节点 | 组内节点 | 关系 | 为什么先学前者 |")
        L.append("|---|---|---|---|---|")
        for e in sorted(incoming, key=lambda x: (x["source"], x["target"])):
            L.append("| %s | %s | %s | %s | %s |"
                     % (node_group.get(e["source"], ""), e["source"], e["target"],
                        e.get("rel", ""), _md_escape(e.get("note", ""))))
    else:
        L.append("无（本组不依赖其他分组的节点）。")
    L.append("")
    return "\n".join(L)


def groups_index_md(groups, nodes, edges):
    L = ["# 知识分组", "",
         "全站按知识分区划为 %d 组。分组编号与依赖深度是两套彼此独立的编号。"
         "分组身份由序号与名称承载，不用颜色区分分组。" % len(groups), "",
         "| 分组 | 名称 | 节点数 | 层范围 | 组内边 | 已写满 |", "|---|---|---|---|---|---|"]
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        ids = {m["id"] for m in mem}
        L.append("| %s | %s | %d | 第 %d – %d 层 | %d | %d |"
                 % (g["id"], _md_escape(g["name"]), len(mem), min(n["layer"] for n in mem),
                    max(n["layer"] for n in mem),
                    sum(1 for e in edges if e["source"] in ids and e["target"] in ids),
                    sum(1 for n in mem if n["content_status"] == "complete")))
    L.append("")
    for g in groups:
        L.append("- [%s %s](%s.md)" % (g["id"], _md_escape(g["name"]), g["id"].lower()))
    L.append("")
    return "\n".join(L)


def learning_path_md(dag, page_exists):
    nodes = dag["nodes"]
    edges = dag["edges"]
    by_layer = {}
    for n in nodes:
        by_layer.setdefault(n["layer"], []).append(n)
    L = ["# 学习路径", "",
         "按依赖深度（拓扑层）逐层展开全站 %d 个节点。层序由边方向推导：A→B 表示先学 A 再学 B。"
         "同一层内的节点彼此没有先后约束。" % len(nodes), ""]
    for lv in sorted(by_layer):
        L.append("## 第 %d 层 · %d 个节点" % (lv, len(by_layer[lv])))
        L.append("")
        for n in sorted(by_layer[lv], key=lambda x: x["id"]):
            mark = "" if n["id"] in page_exists else "（架构在册）"
            L.append("- %s %s %s%s" % (n["id"], n["group"], _md_escape(n["name"]), mark))
        L.append("")
        for n in sorted(by_layer[lv], key=lambda x: x["id"]):
            ins = [e for e in edges if e["target"] == n["id"]]
            if not ins:
                L.append("- 为什么在这层：%s 为起点层，无前置依赖。" % n["id"])
            for e in sorted(ins, key=lambda x: x["source"]):
                L.append("- 为什么在这层：%s ← %s（%s）%s"
                         % (n["id"], e["source"], e.get("rel", ""), _md_escape(e.get("note", ""))))
        L.append("")
    return "\n".join(L)


def frontier_md(frontier):
    L = ["# 新一代模块", "",
         "- 时间锚：%s" % frontier.get("as_of", ""),
         "- 版次：%s" % frontier.get("edition", ""),
         "- 上一般次：%s" % (frontier.get("previous_edition") or "无"),
         "- 条目数：%d" % len(frontier.get("items", [])), "",
         "状态三值口径：已确认 = 多源同向且可复核；有争议 = 存在反向证据或未获权威裁定；"
         "未证实 = 尚未取得足以支撑的独立证据。未实测标注指该条未在本机跑通，只给出可执行的复现步骤。", ""]
    for it in sorted(frontier.get("items", []), key=lambda x: x.get("id", "")):
        L.append("## %s %s" % (it["id"], _md_escape(it.get("title", ""))))
        L.append("")
        L.append("- 状态：%s" % FSTATUS_MD.get(it.get("status", ""), it.get("status", "")))
        L.append("- 时间锚：%s" % frontier.get("as_of", ""))
        L.append("- 版次：%s" % frontier.get("edition", ""))
        L.append("- 取代：%s" % ("、".join(it.get("supersedes", [])) or "无"))
        L.append("")
        L.append(_md_escape(it.get("summary", "")))
        L.append("")
        for e in it.get("evidence", []):
            L.append("- 证据（%s，%s）：%s" % (e.get("source_id", ""), e.get("tier", ""), e.get("url", "")))
            L.append("  - 原文关键句：%s" % _md_escape(e.get("quote", "")))
        L.append("")
        L.append("离线复现：%s" % _md_escape(it.get("offline_repro", "")))
        L.append("")
    L.append("## 跟踪渠道")
    L.append("")
    for ts in frontier.get("tracking_sources", []):
        L.append("- **%s**（%s）：%s —— %s"
                 % (_md_escape(ts.get("name", "")), ts.get("kind", ""), ts.get("url", ""),
                    _md_escape(ts.get("note", ""))))
    L.append("")
    return "\n".join(L)


def index_md(dag, frontier, page_exists):
    nodes = dag["nodes"]
    groups = sorted(dag["groups"], key=lambda g: g["order"])
    meta = dag["meta"]
    complete = [n for n in nodes if n["content_status"] == "complete"]
    registered = [n for n in nodes if n["content_status"] == "registered"]
    L = ["# %s（Markdown 镜像）" % meta["mission"], "",
         "本目录是站点的纯文本镜像，供检索与引用；人类阅读入口是 HTML 页面。", "",
         "- 读者锚点：%s" % meta["audience"],
         "- 数据时点：%s" % meta["as_of"],
         "- 版次：%s" % meta["edition"],
         "- 节点 %d / 边 %d / 分组 %d / 依赖深度层 %d" % (len(nodes), len(dag["edges"]), len(groups), meta["layer_count"]),
         "- 边语义：%s" % "、".join(meta["edge_semantics"]),
         "- 依赖方向：A→B 表示先学 A 再学 B；层序由该方向推导",
         "- 无环：是",
         "- 内容状态：已写满 %d 个 / 架构在册 %d 个" % (len(complete), len(registered)), "",
         "## 目录", "",
         "- [知识分组](groups/index.md)",
         "- [学习路径](learning-path.md)",
         "- [新一代模块](frontier.md)",
         "- [已写满的节点](nodes/)", ""]
    L.append("## 已写满的节点")
    L.append("")
    for n in sorted(complete, key=lambda x: x["layer"]):
        L.append("- [%s %s](nodes/%s.md)" % (n["id"], _md_escape(n["name"]), C.id_slug(n["id"])))
    L.append("")
    L.append("## 知识分组一览")
    L.append("")
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        L.append("- [%s %s](groups/%s.md)：%d 个节点" % (g["id"], _md_escape(g["name"]), g["id"].lower(), len(mem)))
    L.append("")
    L.append("## 新一代模块")
    L.append("")
    L.append("- [新一代模块条目镜像](frontier.md)：只含数据、不含教程正文；条目带时间锚、版次、"
             "状态与取代关系，大更新时只刷新该处。")
    L.append("")
    return "\n".join(L)


def generate(root=None):
    data = C.load_sources()
    dag = data["dag"]
    nodes = dag["nodes"]
    groups = sorted(dag["groups"], key=lambda g: g["order"])
    edges = dag["edges"]
    groups_by_id = {g["id"]: g for g in groups}
    node_group = {n["id"]: n["group"] for n in nodes}
    page_exists = {n["id"] for n in nodes if n["content_status"] == "complete"}
    out = {}
    out["%s/index.md" % C.DIR_MD] = index_md(dag, data["frontier"], page_exists)
    out["%s/groups/index.md" % C.DIR_MD] = groups_index_md(groups, nodes, edges)
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        out["%s/groups/%s.md" % (C.DIR_MD, g["id"].lower())] = group_md(g, mem, groups, edges, node_group)
    for n in sorted(nodes, key=lambda x: x["id"]):
        if n["content_status"] == "complete":
            out["%s/nodes/%s.md" % (C.DIR_MD, C.id_slug(n["id"]))] = node_md(n, groups_by_id)
    out["%s/learning-path.md" % C.DIR_MD] = learning_path_md(dag, page_exists)
    out["%s/frontier.md" % C.DIR_MD] = frontier_md(data["frontier"])
    return out


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
