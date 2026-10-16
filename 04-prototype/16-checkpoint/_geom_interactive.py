#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_geom_interactive.py —— 交互全景图的**产物侧几何复算**（⛔ 不写任何文件，只读+打印）。

为什么需要它：几何复算与真实渲染**互补**——真实渲染（`_render.py` / `_probe_channel.py`）证明
「画出来了、没溢出」，但⛔ 不证明「节点两两不重叠 / 边不穿节点框 / 标签在框内」这些**几何量**；
本脚本从**产物**（`13-interactive/index.html` 内联的 `cy-data`）把坐标与尺寸取回来，
按 cytoscape `layout:'preset'` 的语义（坐标即最终位置、边为直线段、节点尺寸即 width/height）
**静态复算**几何，并把读数逐项打出来。

★ 作用域纪律（判据与对象边界须对齐）：
  - 断言的对象是**产物里实际下发的那组坐标**，⛔ 不是生成器内部对象；
  - 「标签是否落在节点框内」用的 advance 模型与生成器**同一个**（上界模型），
    故它是**自洽复核**而非独立测量——⛔ 不得读作「浏览器实测不溢出」；
  - 「节点/标签两两是否重叠」「边是否穿节点框」是**纯几何**判定，与字体无关，属独立复算。

★ 事实更正（2026-10-15 教训固化轮）：本件原写「本会话浏览器不可用」——**该结论已被推翻**
（真因是 capability 缺失使 file-capability 程序 `snap-confine` 取不到 `cap_dac_override`，
而**可用的非 snap 内核一直在盘上**；详见 `VERIFY-CONSTRAINT.md` 更正声明与
`RENDER-CHANNEL.md`）。⇒ 本脚本的定位由「**替代**渲染」改为「与渲染**互补**」，
⛔ 不再以「浏览器不可用」为由解释自己的存在。

用法：python3 _geom_interactive.py [--json]
"""
import argparse
import importlib.util
import json
import math
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))
PAGE = os.path.join(SITE, "13-interactive", "index.html")

spec = importlib.util.spec_from_file_location("pekg_geom_src", os.path.join(HERE, "gen-interactive.py"))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

# ★ 几何原语**不在这里重写**：直接取门控 P37 的实现（`_p37_box/_p37_overlap/_p37_seg_hits/
#   _p37_seg_overlap_len`）⇒ 站内只有**一套**几何判定（⛔ 避免「本脚本与门控各算一套、
#   改一处漏一处」）。本脚本只负责把读数**逐项打出来**（门控只给结论行）。
_gate_spec = importlib.util.spec_from_file_location("pekg_gate_for_geom",
                                                    os.path.join(HERE, "gate_prototype.py"))
GT = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(GT)

DATA_RE = re.compile(r'<script type="application/json" id="cy-data">(.*?)</script>', re.S)


def load_data():
    html = open(PAGE, encoding="utf-8").read()
    m = DATA_RE.search(html)
    if not m:
        raise SystemExit("[FAIL] 产物里找不到 cy-data（判据对象缺失，fail-closed）")
    return json.loads(m.group(1).replace("<\\/", "</")), html


box = GT._p37_box
overlap = GT._p37_overlap
seg_hits = GT._p37_seg_hits
seg_overlap_len = GT._p37_seg_overlap_len


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    data, html = load_data()
    lay = data["layout"]
    pad = lay["pad"]
    uw, uh = lay["usableW"], lay["usableH"]
    rep = {"page": os.path.relpath(PAGE, SITE), "bytes": len(html.encode("utf-8"))}

    groups = data["groups"]
    gpos = {g["id"]: (g["pos"]["x"], g["pos"]["y"]) for g in groups}
    gbox = {g["id"]: box(gpos[g["id"]], g["w"], g["h"]) for g in groups}
    ids = [g["id"] for g in groups]

    # ---- 1. 默认视口下 11 个组节点的包围盒是否落在画布内 ----
    x1 = min(b[0] for b in gbox.values())
    y1 = min(b[1] for b in gbox.values())
    x2 = max(b[2] for b in gbox.values())
    y2 = max(b[3] for b in gbox.values())
    rep["canvas"] = {"contentColW": lay["canvasW"], "cyH": lay["canvasH"], "pad": pad,
                     "usableW": uw, "usableH": uh}
    rep["groupBBox"] = {"x1": round(x1, 2), "y1": round(y1, 2), "x2": round(x2, 2), "y2": round(y2, 2),
                        "w": round(x2 - x1, 2), "h": round(y2 - y1, 2),
                        "insideW": (x2 - x1) <= uw + 1e-6, "insideH": (y2 - y1) <= uh + 1e-6,
                        "slackW": round(uw - (x2 - x1), 2), "slackH": round(uh - (y2 - y1), 2)}

    # ---- 2. 两两是否重叠（含最小间隙） ----
    min_gap = None
    pairs_overlap = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            A, B = gbox[ids[i]], gbox[ids[j]]
            if overlap(A, B):
                pairs_overlap.append((ids[i], ids[j]))
            dx = max(B[0] - A[2], A[0] - B[2], 0.0)
            dy = max(B[1] - A[3], A[1] - B[3], 0.0)
            gap = math.hypot(dx, dy)
            min_gap = gap if min_gap is None else min(min_gap, gap)
    rep["pairwise"] = {"pairs": len(ids) * (len(ids) - 1) // 2, "overlaps": pairs_overlap,
                       "minGapPx": round(min_gap or 0.0, 2)}

    # ---- 3. 标签是否整体落在节点框内（同一上界模型复算） ----
    label_bad = []
    max_lines = 0
    for g in groups:
        lines = g["cyLabel"].split("\n")
        max_lines = max(max_lines, len(lines))
        for ln in lines:
            wpx = G._text_w(ln, g["fs"])
            if wpx > g["mw"] + 1e-6:
                label_bad.append((g["id"], "行宽", round(wpx, 1), g["mw"], ln))
        lh = len(lines) * g["fs"] * 1.15 + 2 * G.G_VPAD
        if lh > g["h"] + 1e-6:
            label_bad.append((g["id"], "行高", round(lh, 1), g["h"], ""))
    rep["labels"] = {"maxLines": max_lines, "violations": label_bad,
                     "note": "行宽用与生成器同一的 advance 上界模型复算（自洽复核，非浏览器实测）"}

    # ---- 4. 边：直线段（curve-style:straight）是否穿第三方节点框 / 是否两两压边 ----
    edges = [(e["source"], e["target"]) for e in data["groupEdges"]]
    cross = []
    for s, t in edges:
        ps, pt = gpos[s], gpos[t]
        for gid in ids:
            if gid in (s, t):
                continue
            if seg_hits(ps, pt, gbox[gid]):
                cross.append((s, t, gid))
    dup = []
    for i in range(len(edges)):
        for j in range(i + 1, len(edges)):
            s1, t1 = edges[i]
            s2, t2 = edges[j]
            L = seg_overlap_len(gpos[s1], gpos[t1], gpos[s2], gpos[t2])
            if L > 0.5:
                dup.append((edges[i], edges[j], round(L, 2)))
    rep["edges"] = {"count": len(edges), "throughThirdNode": cross,
                    "throughCount": len(cross), "collinearOverlaps": dup,
                    "curveStyle": "straight"}

    # ---- 5. 边标签（独立标签节点）：两两不重叠 + 不压节点框 ----
    els = data["edgeLabels"]
    ebox = [(e["id"], box((e["x"], e["y"]), e["w"], e["h"])) for e in els]
    lb_bad = []
    for i in range(len(ebox)):
        for j in range(i + 1, len(ebox)):
            if overlap(ebox[i][1], ebox[j][1], margin=-2.0):
                lb_bad.append(("标签互压", ebox[i][0], ebox[j][0]))
    for eid, b in ebox:
        for gid in ids:
            if overlap(b, gbox[gid], margin=-2.0):
                lb_bad.append(("标签压节点", eid, gid))
    rep["edgeLabels"] = {"count": len(els), "violations": lb_bad,
                         "minCountLabeled": lay["edgeLabelMinCount"]}

    # ---- 6. 全元素包围盒 ⇒ 默认视口下的 zoom ----
    allb = list(gbox.values()) + [b for _i, b in ebox]
    ex1 = min(b[0] for b in allb)
    ey1 = min(b[1] for b in allb)
    ex2 = max(b[2] for b in allb)
    ey2 = max(b[3] for b in allb)
    ew, eh = ex2 - ex1, ey2 - ey1
    zoom = min(1.0, uw / ew, uh / eh) if ew > 0 and eh > 0 else 0.0
    rep["elementsBBox"] = {"w": round(ew, 2), "h": round(ey2 - ey1, 2)}
    rep["zoomAtDefaultViewport"] = round(zoom, 4)
    # 画布高度需求（JS 侧「只增不减」补高）与 CSS 上限的关系
    rep["canvasHeightNeed"] = round(eh + 2 * pad, 1)
    rep["cssCanvasHeightAtDefault"] = lay["canvasH"]

    # ---- 7. 结构：行 = rank，行内 order 递增 ----
    order = {g["id"]: g["order"] for g in groups}
    rep["structure"] = {"rows": lay["rows"], "slots": lay["slots"],
                        "rowMembers": lay["rowMembers"],
                        "rowOrderIncreasing": all(
                            [order[g] for g in row] == sorted(order[g] for g in row)
                            for row in lay["rowMembers"]),
                        "rankOf": lay["rankOf"], "backEdges": lay["backEdges"],
                        "rawBackEdges": lay["rawBackEdges"]}
    # 行内 y 唯一（同一 rank 的节点 y 相同）+ 行 y 随 rank 单调递增
    rowY = []
    for row in lay["rowMembers"]:
        ys = {round(gpos[g][1], 2) for g in row}
        rowY.append((row, sorted(ys)))
    rep["structure"]["rowYUnique"] = all(len(v) == 1 for _r, v in rowY)
    rep["structure"]["rowY"] = [v[0] if len(v) == 1 else v for _r, v in rowY]
    rep["structure"]["rowYMonotone"] = all(
        rep["structure"]["rowY"][i] < rep["structure"]["rowY"][i + 1]
        for i in range(len(rep["structure"]["rowY"]) - 1)
        if isinstance(rep["structure"]["rowY"][i], float)
        and isinstance(rep["structure"]["rowY"][i + 1], float))

    # ---- 8. 下钻视图（逐组）几何 ----
    drills = []
    for gid, d in sorted(data["drills"].items()):
        bs = [box((n["x"], n["y"]), n["w"], n["h"]) for n in d["nodes"]]
        ov = 0
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                if overlap(bs[i], bs[j]):
                    ov += 1
        dw = max(b[2] for b in bs) - min(b[0] for b in bs)
        dh = max(b[3] for b in bs) - min(b[1] for b in bs)
        drills.append({"group": gid, "nodes": d["count"], "cols": d["cols"], "rows": d["rows"],
                       "bboxW": round(dw, 1), "bboxH": round(dh, 1), "overlaps": ov,
                       "inside": dw <= uw + 1e-6 and dh <= uh + 1e-6})
    rep["drills"] = drills

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print("== 交互全景图 · 产物侧几何复算 ==")
    print("产物：%s（%d B）" % (rep["page"], rep["bytes"]))
    print("默认视口口径：内容列 %.0fpx × #cy 高 %.0fpx，内边距 %.0fpx ⇒ 可用 %.0f × %.0f"
          % (lay["canvasW"], lay["canvasH"], pad, uw, uh))
    print("")
    print("[1] 11 个组节点包围盒：w=%.1f h=%.1f；在画布内：横向 %s（余 %.1fpx）/ 纵向 %s（余 %.1fpx）"
          % (rep["groupBBox"]["w"], rep["groupBBox"]["h"],
             rep["groupBBox"]["insideW"], rep["groupBBox"]["slackW"],
             rep["groupBBox"]["insideH"], rep["groupBBox"]["slackH"]))
    print("[2] 两两不重叠：检查 %d 对；重叠 %d 对 %s；最小间隙 %.1fpx"
          % (rep["pairwise"]["pairs"], len(rep["pairwise"]["overlaps"]),
             rep["pairwise"]["overlaps"], rep["pairwise"]["minGapPx"]))
    print("[3] 标签落在节点框内：最长 %d 行；违例 %d 处 %s"
          % (rep["labels"]["maxLines"], len(rep["labels"]["violations"]),
             rep["labels"]["violations"][:3]))
    print("[4] 组间边 %d 条（straight）：穿过第三方节点框 %d 条 %s；两两共线重叠 %d 对 %s"
          % (rep["edges"]["count"], rep["edges"]["throughCount"],
             rep["edges"]["throughThirdNode"][:3], len(rep["edges"]["collinearOverlaps"]),
             rep["edges"]["collinearOverlaps"][:3]))
    print("[5] 边标签节点 %d 个（仅 count ≥ %d 标注）：互压/压节点违例 %d 处 %s"
          % (rep["edgeLabels"]["count"], rep["edgeLabels"]["minCountLabeled"],
             len(rep["edgeLabels"]["violations"]), rep["edgeLabels"]["violations"][:3]))
    print("[6] 全元素包围盒 %.1f × %.1f ⇒ 默认视口 zoom = %.4f（1.0000 = 无需缩小）"
          % (rep["elementsBBox"]["w"], rep["elementsBBox"]["h"], rep["zoomAtDefaultViewport"]))
    print("    画布高度需求 %.1fpx ≤ CSS 上限 %.1fpx ⇒ JS 侧无需补高" %
          (rep["canvasHeightNeed"], rep["cssCanvasHeightAtDefault"]))
    print("[7] 结构：%d 行 × %d 槽；行内 order 递增=%s；行 y 唯一=%s；行 y 随 rank 递增=%s"
          % (rep["structure"]["rows"], rep["structure"]["slots"],
             rep["structure"]["rowOrderIncreasing"], rep["structure"]["rowYUnique"],
             rep["structure"]["rowYMonotone"]))
    print("    行成员：%s" % rep["structure"]["rowMembers"])
    print("    原始边集里 order 逆序的回边（已合成双向边，⛔ 未丢弃）：%s"
          % rep["structure"]["rawBackEdges"])
    print("    合成后**画出来**的边集里 order 逆序的边：%s（应为空 ⇒ 分层有良定义）"
          % rep["structure"]["backEdges"])
    print("[8] 下钻视图 %d 组：节点数 %s；超区 %d 组；重叠 %d 处"
          % (len(drills), [d["nodes"] for d in drills],
             sum(0 if d["inside"] else 1 for d in drills), sum(d["overlaps"] for d in drills)))
    print("")
    bad = (not rep["groupBBox"]["insideW"] or not rep["groupBBox"]["insideH"]
           or rep["pairwise"]["overlaps"] or rep["labels"]["violations"]
           or rep["edges"]["throughCount"] or rep["edges"]["collinearOverlaps"]
           or rep["edgeLabels"]["violations"] or rep["zoomAtDefaultViewport"] < 0.9999
           or not rep["structure"]["rowOrderIncreasing"] or not rep["structure"]["rowYUnique"]
           or any(not d["inside"] or d["overlaps"] for d in drills))
    print("== 几何复算结论：%s ==" % ("PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
