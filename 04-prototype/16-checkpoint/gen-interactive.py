#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-interactive.py —— 交互全景图生成器（13-interactive/index.html）

形态：组级视图 + 点击下钻 + 深链（#group=<gid> / #node=<nid>）。
自包含例外：本目录是唯一允许引用同目录 `vendor/` 下本地脚本的目录，⛔ 例外不得扩散。
页面外壳仍走 gen-common.page_shell（全站唯一模板）。

★ 本轮形态变更一（H2 硬规则 5 / H3 G2「色相不承载身份」）：
  - **撤掉 11 组彩虹色**：组节点统一用品牌色，⛔ 不按组分配色相；
  - 「当前选中组」由**同一色相的深浅 + 描边**表达（品牌色 vs 品牌深色 + 更粗描边）；
  - 组身份改由**文字与中性序号**承载（节点标签含 G 序号 + 名称）；
  - 画布色值直接取自站点调色板字面值（⛔ 不用 getComputedStyle 读自定义属性——
    其计算值是不求值的 token 流，直接当画布颜色会静默失效）。

★ 本轮形态变更二（DESIGN-CONTRACT R-16 / G3「结构化布局」；用户反馈 #3-4：
  「交互全景图建议向 deepseek harness 插件 dag 依赖图项目学习，结构化位置的优点还是很大」）：
  组级视图由 **cytoscape + dagre 自由布局**改为**确定性分层网格 + preset 坐标**。
  取经对象与可移植做法见下方「结构化布局」常量区的七条注释与 `_assign_slots()` 的注释；
  坐标**全部在 Python 侧算好并逐条 assert**，渲染期零随机（`layout:{name:'preset'}`），
  与参照项目 `deepseek-harness-plugin-dag` 的
  `07-checkpoint/gen-overview.py:824`（`layout:{name:'preset'}`）与
  `:328-356`（包围盒 / 标签内嵌 / 两两不重叠 / zoom 断言）同源。
"""

import importlib.util
import itertools
import json
import math
import os
import re
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

# ★ 画布字体族取自令牌值（⛔ 不再手写第二套字体栈）
FONT_STACK = C.palette_css_value("font.sans", "light")

# ---------------------------------------------------------------- 结构化布局（组级视图）
#
# ★ 为什么这样定坐标（逐条可核，⛔ 不是「看着调」）：
#
#   ① 行 = 依赖层（rank）。原始组级边集**不是 DAG**：`order` 逆序的边有 3 条
#      （G04→G02 / G06→G03 / G06→G05），且它们与正向边互为正反 ⇒ 严格拓扑分层对
#      **原始**边集无良定义（diagram-lite 判据索引：有环/跨层图无良定义拓扑分层）。
#      处置：先把 3 对互为正反的边合成**一条双向边**（见 `_merge_mutual`，同时消掉
#      「两条直线段完全重合」的边压边），合成后**画出来的**边集 25 条全部 `order` 正向
#      ⇒ 在其上取**最长路径**得 rank，rank 有唯一解。`_ranks()` 仍按「只用 order 正向边」
#      的口径计算：这不是多余——它保证将来若出现**非互为反向**的环（真环）时，
#      分层依然良定义、不会死循环，而原始回边由 `layout.rawBackEdges` 逐条登记、⛔ 不静默丢弃。
#
#   ② 行内 = 课程顺序。行内自左向右 `groups[].order` 递增 ⇒「先学什么」与阅读方向一致
#      （参照项目同款不变量：行主序填充网格 ⇒ layer 沿阅读方向单调不减，
#      `gen-overview.py:18`）。
#
#   ③ 列 = 8 槽网格上的**确定性分配**，由 `_assign_slots()` 搜索得到；目标函数是
#      「边弦穿过第三方节点框」的条数 = 0（组级视图**硬断言**，见 `_group_layout`）。
#      ⛔ 不是力导向、⛔ 不是 dagre 自由布局、⛔ 渲染期零随机。
#
#   ④ 画布口径（默认视口 = 宽屏 ≥1180px、视口高 900px）：
#        内容列宽 804px（与 P34 的「宽屏内容列 804px」同源）
#        `#cy` 高 = min(72vh, 40rem) = 640px
#        内边距 18px（与 cytoscape 侧 `DATA.layout.pad` 同值）
#        ⇒ 可用 768 x 604。本布局实测 763 x 590 ⇒ 反推 zoom = 1.000
#        ⇒ 默认视口下**无需缩放、无需拖拽**即可看全 11 个组节点。
#
#   ⑤ 标签不靠 cytoscape 折行：cytoscape **没有标签避让**、且只按空格折行、不会断开长
#      token（参照项目实测结论）。故 label 的每一行都在 Python 侧按**字符 advance 上界**
#      折好并写死 '\n'，`text-max-width` 留 8% 余量使 cytoscape 不会二次折行
#      （同源做法：`gen-overview.py:21-22`）。
#
#   ⑥ 边标签（依赖条数）**独立渲染成标签节点**并按几何避让摆放：cytoscape 没有边标签避让，
#      故由 Python 侧算好坐标并断言「标签两两不重叠、且不压任何节点框」
#      （同源做法：cytoscape-dag-visualization「边标签一律改用独立标签节点，天然不叠」）。
#
#   ⑦ 边一律 `curve-style:'straight'`：直线段的几何是**无歧义**的，Python 侧的
#      「边弦不穿节点框 / 两两不共线重叠」断言因此**描述的就是实际渲染的几何**。
#      ⛔ 不用 bezier/segments —— 其控制点语义无法在本会话（无浏览器）实测，
#      断言会退化为「对想象中的曲线断言」（装置自身的错）。

VIEW_W = 804.0          # 默认视口下的内容列宽（与 P34 同源）
VIEW_H = 640.0          # 默认视口下 #cy 的 CSS 高度 min(72vh, 40rem)
PAD = 18.0              # 画布内边距
USABLE_W = VIEW_W - 2 * PAD
USABLE_H = VIEW_H - 2 * PAD

G_SLOTS = 8             # 组级 x 槽位数
G_PITCH_X = 89.0        # 槽距（相邻槽 89 < 节点宽 140 ⇒ 同行必须隔槽，见 G_MIN_GAP）
G_PITCH_Y = 77.0        # 行距（行 = rank）；行间净空 25px = 58-52+19 ⇒ 容得下 16px 边标签
G_W, G_H = 140.0, 52.0  # 组节点尺寸（高 52 = 3 行 12px 文字 49.4px 上取整）
G_FS = 12.0             # 组节点字号
G_HPAD, G_VPAD = 10.0, 4.0
G_MIN_GAP = 2           # 同行槽位最小间隔（2 槽 = 178px ≥ 节点宽 140px + 38px 间隙）
G_LINE_H = 1.15         # 与 cytoscape 侧 line-height 同值

D_W, D_H = 168.0, 58.0  # 下钻节点尺寸（高度不足时按行数上调，见 _drill_layout）
D_GAP_X, D_GAP_Y = 28.0, 24.0
D_FS = 12.0
D_COLS = 3
D_MIN_LINE_H = 1.15

WRAP_SAFETY = 0.92      # 折行预算 = 节点内宽 x 该系数（留 8% 余量给字体度量误差）

# ★ 字符 advance 的**上界**模型（单位：em）。
#   为什么是上界而不是实测值：★ 2026-10-16 更正 —— 此处的旧理由写「本会话浏览器不可用
#   （VERIFY-CONSTRAINT.md）」，**该前提已被推翻**（真因是 snap 启动层的能力缺失；非 snap 内核一直可用，
#   本会话复跑 `_probe_env.py` 再次证伪，且 `_probe_thresholds.py` 已用同一内核取得真实渲染读数）。
#   ⇒ 保留上界模型的理由改为**它自身的工程取舍**：本模型的输入是「静态字符集 × 上界 advance」，
#   不依赖渲染期状态 ⇒ 生成器在**无浏览器**时也能给出保守断言（可复现性优先于紧致性）。
#   ⛔ 不得据此声称「布局已用渲染实测验证过」——那需要把 `measureText` 读数纳入判据（尚未做，见台账 G20）。
#   取「常见 sans 栈实际 advance 的上界」：DejaVu Sans 最宽字母 W = 0.989em、
#   数字 = 0.636em、空格 = 0.318em、连字符 = 0.361em；CJK 字体对 CJK 码位恒为 1.0em。
#   ⇒ 估计宽 ≥ 实测宽，故「估计宽 ≤ 节点内宽」是**保守成立**的断言（不会假绿）。
_ADV_UPPER = {
    "digit": 0.64, "upper": 0.99, "lower": 0.99, "space": 0.35,
    "hyphen": 0.40, "other_ascii": 0.70, "wide": 1.00,
}


def _adv_em(ch):
    o = ord(ch)
    if o > 0x2E80:                       # CJK / 全角标点：CJK 字体恒 1.0em
        return _ADV_UPPER["wide"]
    if ch.isdigit():
        return _ADV_UPPER["digit"]
    if ch.isalpha():
        return _ADV_UPPER["upper"] if ch.isupper() else _ADV_UPPER["lower"]
    if ch == " ":
        return _ADV_UPPER["space"]
    if ch in "-‐–":
        return _ADV_UPPER["hyphen"]
    return _ADV_UPPER["other_ascii"]


def _text_w(s, fs):
    """字符串渲染宽度的**上界**（px）。"""
    return sum(_adv_em(ch) for ch in s) * fs


_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\./+]*|.")


def _wrap(text, max_w, fs):
    """按字符/ASCII 词元贪心折行，返回行列表（⛔ 不改动任何字符，只决定在哪里断）。

    ⛔ 不靠 cytoscape 折行：它只按空格断行、且长 token 会溢出节点框。
    """
    lines, cur = [], ""
    for tok in _TOKEN_RE.findall(text or ""):
        if cur and _text_w(cur + tok, fs) > max_w:
            lines.append(cur.rstrip())
            cur = "" if tok.isspace() else tok
        else:
            cur += tok
    if cur.strip():
        lines.append(cur.rstrip())
    return lines or [""]


def _seg_hits_box(p, q, box):
    """线段 p→q 是否穿过 box 内部（box 内缩 1px，避免「擦边」被判成穿越）。Liang-Barsky。"""
    x0, y0, x1, y1 = box
    x0 += 1.0
    y0 += 1.0
    x1 -= 1.0
    y1 -= 1.0
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
            continue
        t = qq / pp
        if pp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return t1 > t0 + 1e-9


def _box(p, w, h):
    return (p[0] - w / 2.0, p[1] - h / 2.0, p[0] + w / 2.0, p[1] + h / 2.0)


def _overlap(a, b, margin=0.0):
    return (a[0] < b[2] - margin and b[0] < a[2] - margin
            and a[1] < b[3] - margin and b[1] < a[3] - margin)


def _ranks(ids, edges, order):
    """rank = 「order 正向子图」上的最长路径（该子图无环 ⇒ rank 唯一）。"""
    rank = {i: 0 for i in ids}
    fwd = [(a, b) for a, b in edges if order[a] < order[b]]
    for _ in range(len(ids)):
        for a, b in fwd:
            if rank[b] < rank[a] + 1:
                rank[b] = rank[a] + 1
    return rank, [e for e in edges if e not in fwd]


def _count_edge_node_hits(pos, sizes, edges, rank, row_members):
    """返回 (穿越条数, 明细)：边弦是否穿过**第三方**节点框。"""
    n, det = 0, []
    for a, b in edges:
        pa, pb = pos[a], pos[b]
        lo, hi = (rank[a], rank[b]) if rank[a] <= rank[b] else (rank[b], rank[a])
        for r in range(lo, hi + 1):
            for gid in row_members[r]:
                if gid in (a, b):
                    continue
                if _seg_hits_box(pa, pb, _box(pos[gid], sizes[0], sizes[1])):
                    n += 1
                    det.append((a, b, gid))
    return n, det


def _assign_slots(row_members, edges, rank, order, nslot, pitch_x, pitch_y, w, h, min_gap):
    """在「rank 行 x nslot 槽」网格上求一组**确定性**列分配，使「边弦穿过第三方节点框」= 0。

    ★ 为什么用搜索而不是写死坐标：写死坐标在数据变化（增删组/改边）后会**静默失效**
      （坐标仍然合法，但边开始压节点，而没有任何判据看得见）。改为「搜索 + 硬断言」后，
      数据一变要么重新解出合法坐标、要么当场 assert 失败（fail-closed）。
    ★ 确定性：LCG 定种子 + 固定起点序 + 字典序 tie-break ⇒ 同输入必得同坐标
      （P16 幂等判据覆盖）。
    """
    combos = []
    for mem in row_members:
        k = len(mem)
        combos.append([c for c in itertools.combinations(range(nslot), k)
                       if all(b - a >= min_gap for a, b in zip(c, c[1:]))])
    for cs in combos:
        if not cs:
            raise SystemExit("[FAIL] 结构化布局：某行在 %d 个槽位下放不下" % nslot)

    def x_of(s):
        return (s - (nslot - 1) / 2.0) * pitch_x

    def y_of(r):
        return r * pitch_y

    def evaluate(assign):
        pos = {}
        for r, mem in enumerate(row_members):
            for gid, s in zip(mem, assign[r]):
                pos[gid] = (x_of(s), y_of(r))
        n, det = _count_edge_node_hits(pos, (w, h), edges, rank, row_members)
        return n, det, pos

    best = None
    seed = 20261015
    for st in range(160):
        if st == 0:                                  # 起点 1：每行取居中的那个槽位组合
            assign = [cs[len(cs) // 2] for cs in combos]
        else:
            assign = []
            for cs in combos:
                seed = (seed * 1103515245 + 12345) % (1 << 31)
                assign.append(cs[seed % len(cs)])
        cur, det, _pos = evaluate(assign)
        for _p in range(30):
            improved = False
            for r in range(len(row_members)):
                for cand in combos[r]:
                    if cand == assign[r]:
                        continue
                    trial = list(assign)
                    trial[r] = cand
                    n2, d2, _p2 = evaluate(trial)
                    if n2 < cur:
                        assign, cur, det, improved = trial, n2, d2, True
            if not improved:
                break
        key = (cur, tuple(assign))
        if best is None or key < best[0]:
            best = (key, list(assign), cur, det)
        if best[2] == 0:
            break
    return best, combos


def _group_layout(groups, group_edges, raw_edges=()):
    """组级视图的确定性分层网格（行 = rank / 行内 = order / 列 = 搜索得到的槽位）。"""
    ids = [g["id"] for g in groups]
    order = {g["id"]: g["order"] for g in groups}
    edges = [(e["source"], e["target"]) for e in group_edges]
    rank, back_edges = _ranks(ids, edges, order)
    nrow = max(rank.values()) + 1
    row_members = [[] for _ in range(nrow)]
    for gid in sorted(ids, key=lambda x: (rank[x], order[x])):
        row_members[rank[gid]].append(gid)

    (key, assign, hits, detail), combos = _assign_slots(
        row_members, edges, rank, order, G_SLOTS, G_PITCH_X, G_PITCH_Y,
        G_W, G_H, G_MIN_GAP)

    pos = {}
    for r, mem in enumerate(row_members):
        for gid, s in zip(mem, assign[r]):
            pos[gid] = ((s - (G_SLOTS - 1) / 2.0) * G_PITCH_X, r * G_PITCH_Y)

    # ★ 把内容包围盒**居中到原点**：这样「是否落在可用区」就是一条对称区间断言
    #   （±USABLE/2），标签摆放的边界检查也与之同源；⛔ 不留「坐标原点在左上角」的隐式约定。
    _bx1 = min(pos[g][0] for g in ids) - G_W / 2.0
    _by1 = min(pos[g][1] for g in ids) - G_H / 2.0
    _bx2 = max(pos[g][0] for g in ids) + G_W / 2.0
    _by2 = max(pos[g][1] for g in ids) + G_H / 2.0
    _cx, _cy = (_bx1 + _bx2) / 2.0, (_by1 + _by2) / 2.0
    for g in ids:
        pos[g] = (pos[g][0] - _cx, pos[g][1] - _cy)

    # ---- 硬断言 1：边弦不穿第三方节点框 ----
    assert hits == 0, "组级布局：边弦穿过第三方节点框 %d 处 %s（搜索未解出合法坐标）" % (hits, detail[:6])
    # ---- 硬断言 2：两两 bbox 不相交（留 8px 视觉间隙）----
    boxes = {g: _box(pos[g], G_W, G_H) for g in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            assert not _overlap(boxes[a], boxes[b], margin=-8.0), \
                "组级布局：节点重叠 %s / %s" % (a, b)
    # ---- 硬断言 3：包围盒落在默认视口可用区内（⇒ 反推 zoom = 1.000）----
    x1 = min(b[0] for b in boxes.values())
    y1 = min(b[1] for b in boxes.values())
    x2 = max(b[2] for b in boxes.values())
    y2 = max(b[3] for b in boxes.values())
    vw, vh = x2 - x1, y2 - y1
    assert vw <= USABLE_W + 1e-6, "组级布局：内容宽 %.1f > 可用宽 %.1f" % (vw, USABLE_W)
    assert vh <= USABLE_H + 1e-6, "组级布局：内容高 %.1f > 可用高 %.1f" % (vh, USABLE_H)
    zoom = min(1.0, USABLE_W / vw, USABLE_H / vh)
    assert zoom >= 1.0 - 1e-9, "组级布局：默认视口下 zoom %.4f < 1" % zoom
    # ---- 硬断言 4：行内 order 递增（阅读方向 = 课程顺序）----
    for r, mem in enumerate(row_members):
        os_ = [order[g] for g in mem]
        assert os_ == sorted(os_), "组级布局：第 %d 行 order 非递增 %s" % (r, mem)
    return {
        "rank": rank, "backEdges": back_edges, "rowMembers": row_members,
        "rawBackEdges": [(e["source"], e["target"]) for e in raw_edges
                         if order[e["source"]] >= order[e["target"]]],
        "pos": pos, "boxes": boxes, "viewW": vw, "viewH": vh, "zoom": zoom,
        "crossings": hits, "assign": assign, "combos": combos,
        "slots": G_SLOTS, "pitchX": G_PITCH_X, "pitchY": G_PITCH_Y,
        "nodeW": G_W, "nodeH": G_H, "fs": G_FS,
    }


def _place_edge_labels(group_edges, layout):
    """把「依赖条数」标签摆成独立标签节点：沿边弦取候选点，逐个试到不压任何东西为止。

    ★ 只在 count >= 2 的边上标注：1 条的边占 19/28，全标会在画布上撒 28 个「1」，
      既压线又无信息量；图例写明「未标注 = 1 条」⇒ 信息不丢，只是不重复画同一个默认值。
    ★ 摆法确定性：候选点按 |t-0.5| 升序、再按垂直偏移升序；命中第一个合法点即用。
      ⛔ 不做随机重试、⛔ 不做「看起来差不多」的目测。
    """
    placed, out = [], []
    node_boxes = list(layout["boxes"].values())
    for e in sorted(group_edges, key=lambda x: (-x["count"], x["source"], x["target"])):
        if e["count"] < 2:
            continue
        pa, pb = layout["pos"][e["source"]], layout["pos"][e["target"]]
        text = str(e["count"])
        tw = _text_w(text, 10.0)
        bw, bh = tw + 12.0, 16.0
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        length = math.hypot(dx, dy) or 1.0
        ux, uy = -dy / length, dx / length           # 弦的单位法向
        best = None
        for dt in (0.5, 0.45, 0.55, 0.4, 0.6, 0.35, 0.65, 0.3, 0.7, 0.25, 0.75):
            for off in (0.0, 12.0, -12.0, 24.0, -24.0, 36.0, -36.0, 48.0, -48.0, 60.0, -60.0):
                cx = pa[0] + dx * dt + ux * off
                cy = pa[1] + dy * dt + uy * off
                bx = _box((cx, cy), bw, bh)
                if bx[0] < -USABLE_W / 2.0 or bx[2] > USABLE_W / 2.0:
                    continue
                if bx[1] < -USABLE_H / 2.0 or bx[3] > USABLE_H / 2.0:
                    continue
                if any(_overlap(bx, nb, margin=-2.0) for nb in node_boxes):
                    continue
                if any(_overlap(bx, pb2, margin=-2.0) for pb2 in placed):
                    continue
                best = ((cx, cy), bx)
                break
            if best:
                break
        assert best is not None, \
            "边标签无法避让：%s→%s（%d 条）在全部候选点上都与节点或其它标签重叠" % (
                e["source"], e["target"], e["count"])
        placed.append(best[1])
        out.append({"id": "EL:%s>%s" % (e["source"], e["target"]),
                    "source": e["source"], "target": e["target"],
                    "label": text, "x": round(best[0][0], 2), "y": round(best[0][1], 2),
                    "w": bw, "h": bh, "fs": 10.0})
    return out


def _drill_layout(members):
    """组内下钻视图：行主序确定性网格（排序键 (layer, id) ⇒ layer 沿阅读方向单调不减）。

    ★ 与参照项目同款口径（`gen-overview.py:216-221`）：网格尺寸由「装进画布 + 标签整体
      落在节点框内 + 节点不重叠」反推，并在 Python 侧 assert。
    """
    seq = sorted(members, key=lambda n: (n["layer"], n["id"]))
    n = len(seq)
    if n == 0:
        return None
    cols = min(D_COLS, n)
    rows = int(math.ceil(n / float(cols)))
    inner = D_W - 2 * G_HPAD
    budget = inner * WRAP_SAFETY
    labels, max_lines = [], 1
    for nd in seq:
        name = re.sub(r"（.*?）", "", nd["name"]).strip()
        lines = _wrap(name, budget, D_FS) + ["%s · 第 %d 层" % (nd["id"], nd["layer"])]
        for ln in lines:
            assert _text_w(ln, D_FS) <= budget, \
                "下钻标签行宽超预算：%s %r" % (nd["id"], ln)
        labels.append("\n".join(lines))
        max_lines = max(max_lines, len(lines))
    h = max(D_H, max_lines * D_FS * D_MIN_LINE_H + 2 * G_VPAD)
    pos, out = {}, []
    for i, nd in enumerate(seq):
        col, row = i % cols, i // cols
        cx = (col - (cols - 1) / 2.0) * (D_W + D_GAP_X)
        cy = row * (h + D_GAP_Y)
        pos[nd["id"]] = (cx, cy)
        out.append({"id": nd["id"], "x": round(cx, 2), "y": round(cy, 2),
                    "label": labels[i], "w": D_W, "h": h, "fs": D_FS,
                    "mw": inner})
    # 与组级视图同规：内容包围盒居中到原点（「是否落在可用区」= 对称区间断言）
    _y1 = min(pos[x["id"]][1] for x in out) - h / 2.0
    _y2 = max(pos[x["id"]][1] for x in out) + h / 2.0
    _cy = (_y1 + _y2) / 2.0
    for x in out:
        x["y"] = round(x["y"] - _cy, 2)
        pos[x["id"]] = (pos[x["id"]][0], pos[x["id"]][1] - _cy)
    boxes = [_box(pos[x["id"]], D_W, h) for x in out]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            assert not _overlap(boxes[i], boxes[j], margin=-8.0), \
                "下钻节点重叠 %s / %s" % (out[i]["id"], out[j]["id"])
    x1 = min(b[0] for b in boxes)
    y1 = min(b[1] for b in boxes)
    x2 = max(b[2] for b in boxes)
    y2 = max(b[3] for b in boxes)
    vw, vh = x2 - x1, y2 - y1
    assert vw <= USABLE_W + 1e-6 and vh <= USABLE_H + 1e-6, \
        "下钻布局超可用区 %.1f x %.1f" % (vw, vh)
    lay = [nd["layer"] for nd in seq]
    assert lay == sorted(lay), "下钻序列 layer 非单调不减"
    return {"nodes": out, "pos": pos, "cols": cols, "rows": rows, "h": h,
            "w": D_W, "fs": D_FS, "mw": inner, "viewW": vw, "viewH": vh,
            "count": n}


def _merge_mutual(group_edges, order):
    """把「互为正反」的两条组间边合成**一条双向边**。

    ★ 为什么必须合：正反两条边落在同一对节点之间 ⇒ 直线段**完全重合**，渲染上是
      「一条边压在另一条上」——读者既看不出这是双向，也数不出条数。这正是用户反馈 #3-4
      要消掉的「边互相压盖」，也是本页几何复算唯一抓到的重叠（3 对，实测重叠长度
      277.88 / 501.38 / 539.52 px）。
    ★ 为什么不改成弯曲偏移：弯曲（bezier/segments）的控制点语义**无法在本会话实测**，
      几何断言会退化为「对想象中的曲线断言」（见文件头注释 ⑦）。合边则保持直线段，
      几何仍可精确复算。
    ★ 合成后的语义：箭头**双向**（两个方向都有依赖，与数据一致）；条数取两向之和；
      顺向端点 = `order` 较小的一端（与阅读方向一致）。⛔ 不丢信息：fwdCount/backCount
      两个分量一并下发，供图例与详情面板解释。
    """
    by = {(e["source"], e["target"]): e for e in group_edges}
    out, used = [], set()
    for e in group_edges:
        a, b = e["source"], e["target"]
        if (a, b) in used:
            continue
        if (b, a) in by:
            used.add((a, b))
            used.add((b, a))
            fwd, back = ((e, by[(b, a)]) if order[a] < order[b] else (by[(b, a)], e))
            out.append({"source": fwd["source"], "target": fwd["target"],
                        "count": fwd["count"] + back["count"],
                        "fwdCount": fwd["count"], "backCount": back["count"],
                        "bidir": True,
                        "rels": sorted(set(fwd["rels"]) | set(back["rels"]))})
        else:
            used.add((a, b))
            out.append({"source": a, "target": b, "count": e["count"],
                        "fwdCount": e["count"], "backCount": 0, "bidir": False,
                        "rels": list(e["rels"])})
    return sorted(out, key=lambda x: (x["source"], x["target"]))


def build_data():
    """装配注入页面的 DATA（由真相源派生，⛔ 不在页面里手写数据）。"""
    data = C.load_sources()
    dag = data["dag"]
    pal = C.palette_values()
    nodes = dag["nodes"]
    groups = sorted(dag["groups"], key=lambda g: g["order"])
    edges = dag["edges"]

    theme = {"light": {}, "dark": {}}
    for role in pal:
        key = C.palette_names()[role].lstrip("-")
        for mode in ("light", "dark"):
            theme[mode][key] = pal[role][mode]

    gnode = {n["id"]: n["group"] for n in nodes}
    out_groups = []
    for g in groups:
        mem = [n for n in nodes if n["group"] == g["id"]]
        out_groups.append({
            "id": g["id"], "name": g["name"], "en": g["en"], "order": g["order"],
            "intro": g["intro"], "nodeCount": len(mem),
            "completeCount": sum(1 for n in mem if n["content_status"] == "complete"),
            "layerMin": min(n["layer"] for n in mem), "layerMax": max(n["layer"] for n in mem),
            "label": "%s %s" % (g["id"], g["name"]),
        })
    agg = {}
    for e in edges:
        a, b = gnode[e["source"]], gnode[e["target"]]
        if a == b:
            continue
        k = (a, b)
        agg.setdefault(k, {"count": 0, "rels": set()})
        agg[k]["count"] += 1
        agg[k]["rels"].add(e["rel"])
    group_edges_raw = [{"source": a, "target": b, "count": v["count"], "rels": sorted(v["rels"])}
                       for (a, b), v in sorted(agg.items())]
    # ★ 互为正反的两条边合成一条双向边（否则直线段完全重合 = 边压边，见 _merge_mutual）
    group_edges = _merge_mutual(group_edges_raw, {g["id"]: g["order"] for g in out_groups})

    # ---------------- 结构化布局（组级） ----------------
    gl = _group_layout(out_groups, group_edges, group_edges_raw)
    inner = G_W - 2 * G_HPAD
    budget = inner * WRAP_SAFETY
    for g in out_groups:
        gid = g["id"]
        lines = _wrap(g["name"], budget, G_FS)
        lines.append("%s · %d 节点" % (gid, g["nodeCount"]))
        for ln in lines:
            assert _text_w(ln, G_FS) <= budget, "组标签行宽超预算：%s %r" % (gid, ln)
        assert len(lines) * G_FS * G_LINE_H + 2 * G_VPAD <= G_H + 1e-9, \
            "组标签 %d 行放不进节点高 %.0f：%s" % (len(lines), G_H, gid)
        g["cyLabel"] = "\n".join(lines)
        g["pos"] = {"x": round(gl["pos"][gid][0], 2), "y": round(gl["pos"][gid][1], 2)}
        g["w"], g["h"], g["fs"], g["mw"] = G_W, G_H, G_FS, inner
        g["rank"] = gl["rank"][gid]
    edge_labels = _place_edge_labels(group_edges, gl)
    # 标签节点也必须在画布内（它们参与 cytoscape 侧 boundingBox ⇒ 直接决定 zoom）
    for el in edge_labels:
        bx = _box((el["x"], el["y"]), el["w"], el["h"])
        assert bx[0] >= -USABLE_W / 2.0 - 1e-9 and bx[2] <= USABLE_W / 2.0 + 1e-9, \
            "边标签越界（横向）：%s" % el["id"]
        assert bx[1] >= -USABLE_H / 2.0 - 1e-9 and bx[3] <= USABLE_H / 2.0 + 1e-9, \
            "边标签越界（纵向）：%s" % el["id"]
    # ★ 硬断言 5：**全部画布元素**（节点 + 边标签）的包围盒仍在可用区内
    #   —— cytoscape 侧的 boundingBox 含标签节点，只断言节点包围盒会漏掉标签越界
    #   （「判据取的范围若窄于对象的实际渲染形态，附属物会被漏检」）。
    all_boxes = list(gl["boxes"].values()) + \
        [_box((el["x"], el["y"]), el["w"], el["h"]) for el in edge_labels]
    ex1 = min(b[0] for b in all_boxes)
    ey1 = min(b[1] for b in all_boxes)
    ex2 = max(b[2] for b in all_boxes)
    ey2 = max(b[3] for b in all_boxes)
    assert ex2 - ex1 <= USABLE_W + 1e-6 and ey2 - ey1 <= USABLE_H + 1e-6, \
        "组级视图全元素包围盒 %.1f x %.1f 超可用区 %.0f x %.0f" % (
            ex2 - ex1, ey2 - ey1, USABLE_W, USABLE_H)

    # ---------------- 结构化布局（下钻，逐组） ----------------
    drills = {}
    drill_stats = []
    for g in groups:
        mem = [{"id": n["id"], "name": n["name"], "layer": n["layer"],
                "status": n["content_status"]} for n in nodes if n["group"] == g["id"]]
        d = _drill_layout(mem)
        if d is None:
            continue
        drills[g["id"]] = d
        drill_stats.append((g["id"], d["count"], d["cols"], d["rows"], d["h"]))

    layout = {
        "kind": "layered-grid-preset",
        "pad": PAD, "canvasW": VIEW_W, "canvasH": VIEW_H,
        "usableW": USABLE_W, "usableH": USABLE_H,
        "viewW": round(gl["viewW"], 2), "viewH": round(gl["viewH"], 2),
        "zoom": round(gl["zoom"], 4),
        "rows": len(gl["rowMembers"]), "slots": gl["slots"],
        "pitchX": gl["pitchX"], "pitchY": gl["pitchY"],
        "nodeW": gl["nodeW"], "nodeH": gl["nodeH"], "fs": gl["fs"],
        "rowMembers": gl["rowMembers"], "rankOf": gl["rank"],
        "backEdges": [list(x) for x in gl["backEdges"]],
        "rawBackEdges": [list(x) for x in gl["rawBackEdges"]],
        "edgeNodeCrossings": gl["crossings"],
        "edgeLabelMinCount": 2,
        "viewport": "宽屏 ≥1180px、视口高 900px（内容列 804px，#cy 高 min(72vh,40rem)=640px）",
    }

    return {
        "meta": {"mission": dag["meta"]["mission"], "as_of": dag["meta"]["as_of"],
                 "edition": dag["meta"]["edition"], "nodeCount": len(nodes),
                 "edgeCount": len(edges), "groupCount": len(groups),
                 "layerCount": dag["meta"]["layer_count"], "audience": dag["meta"]["audience"],
                 "directionRule": dag["meta"]["direction_rule"],
                 "huePolicy": "组身份由序号与名称承载；画布统一用品牌色，⛔ 不按组分配色相"},
        "groups": out_groups,
        "groupEdges": group_edges,
        "groupEdgesRaw": len(group_edges_raw),
        "groupEdgesBidir": sum(1 for e in group_edges if e["bidir"]),
        "edgeLabels": edge_labels,
        "layout": layout,
        "drillStats": [{"group": a, "nodes": b, "cols": c, "rows": d, "nodeH": e}
                       for a, b, c, d, e in drill_stats],
        "drills": drills,
        "theme": theme,
        "nodes": [{"id": n["id"], "name": n["name"], "en": n["en"], "group": n["group"],
                   "layer": n["layer"], "status": n["content_status"],
                   "tags": n.get("tags", [])} for n in sorted(nodes, key=lambda x: x["id"])],
        "nodeEdges": [{"source": e["source"], "target": e["target"], "rel": e["rel"],
                       "note": e.get("note", "")} for e in edges],
    }


APP_JS = r"""
(function(){
  var DATA;
  try { DATA = JSON.parse(document.getElementById("cy-data").textContent); }
  catch (e) { DATA = null; }
  var cyEl = document.getElementById("cy");
  var detailEl = document.getElementById("cy-detail");
  var viewEl = document.getElementById("cy-view-label");
  var hintEl = document.getElementById("cy-hint");
  var backBtn = document.getElementById("cy-back");
  var FONT = __FONT__;
  if (!DATA || typeof cytoscape === "undefined") {
    if (cyEl) { cyEl.innerHTML = '<p class="lede" style="padding:var(--space-3)">交互图未能装配；'
      + '下方「分组与节点清单」提供等价的文字导航。</p>'; }
    return;
  }
  // ★ 结构化布局（R-16）：坐标全部由生成器在 Python 侧算好并逐条 assert，
  //   渲染期用 cytoscape 的 preset 布局**原样取用**，⛔ 不做任何布局计算、⛔ 无随机。
  //   ⇒ 已不再需要 cytoscape-dagre（自由布局扩展已撤除，见 gen-interactive.py 头部注释）。
  var PAD = (DATA.layout && DATA.layout.pad) || 18;

  function mode(){ var t = document.documentElement.getAttribute("data-theme");
    if (t === "light" || t === "dark") { return t; }
    return (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light"; }
  function tok(k){ var t = DATA.theme && DATA.theme[mode()]; return (t && t[k]) || "#888888"; }

  var cy = null, current = {kind:"overview", id:null};

  function styleSheet(){
    var raised = tok("surface-raised");
    var muted = tok("text-secondary");
    var rule = tok("border-line");
    var brand = tok("brand-primary");
    var label = tok("text-primary");
    return [
      {selector:"node", style:{
        "shape":"round-rectangle", "background-color":"data(color)", "color":"data(labelColor)",
        "label":"data(label)", "font-family":FONT, "font-size":"data(fs)", "font-weight":600,
        "text-wrap":"wrap", "text-max-width":"data(mw)", "text-valign":"center", "text-halign":"center",
        "line-height":1.15, "width":"data(w)", "height":"data(h)",
        "border-width":1, "border-color":rule, "overlay-opacity":0}},
      {selector:'node[kind="group"]', style:{
        "border-width":2, "padding":"0"}},
      {selector:'node[kind="edgeLabel"]', style:{
        "shape":"round-rectangle", "background-color":raised, "background-opacity":0.86,
        "color":muted, "font-weight":400, "font-size":"data(fs)", "text-wrap":"wrap",
        "text-max-width":"data(mw)", "border-width":0, "events":"no"}},
      {selector:'node[status="registered"]', style:{
        "border-style":"dashed", "border-width":2, "border-color":muted, "opacity":0.92}},
      {selector:'node[status="complete"]', style:{"border-style":"solid", "border-width":3,
        "border-color":label}},
      {selector:"node:selected", style:{"border-width":4, "border-color":label}},
      // ★ 边一律 straight：直线段的几何无歧义 ⇒ Python 侧的「不穿节点框 / 不共线重叠」
      //   断言描述的就是实际渲染的几何（⛔ 不用 bezier/segments，其控制点语义无法在本
      //   会话实测，断言会退化为对想象中的曲线断言）。
      {selector:"edge", style:{
        "width":1.4, "line-color":rule, "target-arrow-color":rule, "target-arrow-shape":"triangle",
        "curve-style":"straight", "arrow-scale":0.9, "overlay-opacity":0}},
      {selector:'edge[kind="groupEdge"]', style:{
        "width":"data(width)", "line-color":brand, "target-arrow-color":brand, "opacity":0.5}},
      // ★ 双向边（互为正反的两条组间边合成）：两端都画箭头。
      //   不这么做就得画两条完全重合的直线段 ⇒ 「边压边」（几何复算实测 3 对）。
      {selector:'edge[bidir="1"]', style:{"source-arrow-shape":"triangle",
        "source-arrow-color":brand, "arrow-scale":0.9}},
      {selector:'edge[rel="UPGRADE"]', style:{"line-style":"dashed"}},
      {selector:":active", style:{"overlay-opacity":0}}
    ];
  }

  // ★ 默认视口下 zoom = 1.000（生成器已断言内容 763x590 ⊆ 可用 768x604）：
  //   ① 只增不减地给画布补足内容高度（宁让页面滚动，也不把图缩小）；
  //   ② zoom 与 pan **显式算出**（⛔ 不用 cy.fit 的 padding 语义——其「总内边距/单边」
  //      口径无法在本会话实测，显式算才能与 Python 侧断言同源）；
  //   ③ zoom 上限夹到 1：内容比画布小时不放大（放大只会让字更大而图更挤）。
  function fitPreset(){
    if (!cy) { return; }
    var bb = cy.elements().boundingBox();
    if (!(bb.w > 0) || !(bb.h > 0)) { return; }
    var need = Math.round(bb.h + 2 * PAD);
    if (need > cyEl.clientHeight) { cyEl.style.height = need + "px"; }
    cy.resize();
    var W = cy.width(), H = cy.height();
    var z = Math.min(1, (W - 2 * PAD) / bb.w, (H - 2 * PAD) / bb.h);
    if (!(z > 0)) { z = 1; }
    cy.zoom(z);
    cy.pan({x: W / 2 - z * (bb.x1 + bb.x2) / 2, y: H / 2 - z * (bb.y1 + bb.y2) / 2});
    if (viewEl) { viewEl.setAttribute("data-zoom", z.toFixed(3)); }
  }

  function overview(){
    current = {kind:"overview", id:null};
    var els = [];
    DATA.groups.forEach(function(g){
      els.push({data:{id:"G:" + g.id, gid:g.id, kind:"group", label:g.cyLabel,
        color:tok("brand-primary"), labelColor:tok("on-brand"),
        w:g.w, h:g.h, fs:g.fs, mw:g.mw,
        count:g.nodeCount, name:g.name, intro:g.intro, rank:g.rank,
        layerMin:g.layerMin, layerMax:g.layerMax, completeCount:g.completeCount},
        position:{x:g.pos.x, y:g.pos.y}});
    });
    DATA.groupEdges.forEach(function(e){
      els.push({data:{id:"GE:" + e.source + ">" + e.target, source:"G:" + e.source,
        target:"G:" + e.target, kind:"groupEdge", count:e.count, bidir:e.bidir ? 1 : 0,
        width:Math.min(1 + e.count * 0.7, 6), rels:e.rels.join("/")}});
    });
    DATA.edgeLabels.forEach(function(el){
      els.push({data:{id:el.id, kind:"edgeLabel", label:el.label, fs:el.fs,
        mw:el.w - 6, w:el.w, h:el.h, color:tok("surface-raised"), labelColor:tok("text-secondary")},
        position:{x:el.x, y:el.y}});
    });
    render(els);
    if (viewEl) { viewEl.textContent = "组级总览 · " + DATA.groups.length + " 个分组 / "
      + DATA.groupEdgesRaw + " 条组间依赖（画成 " + DATA.groupEdges.length + " 条连线，其中 "
      + DATA.groupEdgesBidir + " 条双向）· 按依赖层分 " + DATA.layout.rows + " 行"; }
    if (hintEl) { hintEl.textContent = "行 = 依赖层（自上而下加深）；行内自左向右 = 课程顺序。"
      + "点击任一分组下钻到组内节点；滚轮缩放、拖拽平移。"; }
    if (backBtn) { backBtn.disabled = true; }
    showGroupDetail(null);
  }

  function drill(gid){
    var g = DATA.groups.filter(function(x){ return x.id === gid; })[0];
    var d = DATA.drills[gid];
    if (!g || !d) { return; }
    current = {kind:"group", id:gid};
    var mem = DATA.nodes.filter(function(n){ return n.group === gid; });
    var ids = {};
    mem.forEach(function(n){ ids[n.id] = true; });
    var els = [];
    d.nodes.forEach(function(nd){
      var src = mem.filter(function(n){ return n.id === nd.id; })[0] || {};
      els.push({data:{id:"N:" + nd.id, nid:nd.id, group:gid, kind:"node",
        status:src.status, label:nd.label, fullName:src.name, layer:src.layer,
        w:nd.w, h:nd.h, fs:nd.fs, mw:nd.mw,
        color:tok("brand-primary"), labelColor:tok("on-brand"),
        tags:(src.tags || []).join("、")},
        position:{x:nd.x, y:nd.y}});
    });
    DATA.nodeEdges.forEach(function(e){
      if (ids[e.source] && ids[e.target]) {
        els.push({data:{id:"E:" + e.source + ">" + e.target, source:"N:" + e.source, target:"N:" + e.target,
          kind:"edge", rel:e.rel, note:e.note}});
      }
    });
    if (!els.length) { els.push({data:{id:"N:empty", kind:"node", label:"本组暂无可下钻节点",
      w:168, h:58, fs:12, mw:148, color:tok("brand-primary"), labelColor:tok("on-brand")},
      position:{x:0, y:0}}); }
    render(els);
    if (viewEl) { viewEl.textContent = "下钻 · " + g.id + " " + g.name + " · " + mem.length + " 个节点"; }
    if (hintEl) { hintEl.textContent = "行主序网格（第 1 行起自左向右 = 依赖层由浅到深）；"
      + "虚线边框表示内容待填充的节点。点击空白处或「返回总览」回到组级视图。"; }
    if (backBtn) { backBtn.disabled = false; }
    showGroupDetail(g);
  }

  function render(els){
    if (cy) { cy.destroy(); cy = null; }
    if (cyEl) { cyEl.innerHTML = ""; cyEl.removeAttribute("data-placeholder"); }
    cy = cytoscape({container:cyEl, elements:els, style:styleSheet(),
      layout:{name:"preset"},
      wheelSensitivity:0.25, minZoom:0.2, maxZoom:3, boxSelectionEnabled:false});
    cy.layout({name:"preset"}).run();
    cy.on("tap", 'node[kind="group"]', function(ev){ var d = ev.target.data(); drill(d.gid); setHash("group", d.gid); });
    cy.on("tap", 'node[kind="node"]', function(ev){ var d = ev.target.data(); showNodeDetail(d.nid); setHash("node", d.nid); });
    cy.on("tap", function(ev){ if (ev.target === cy) { showGroupDetail(current.kind === "group" ? byId(current.id) : null); } });
    fitPreset();
  }

  function byId(gid){ return DATA.groups.filter(function(x){ return x.id === gid; })[0]; }

  function gseq(gid){ return '<span class="gseq">' + esc(gid) + '</span>'; }

  function showGroupDetail(g){
    if (!detailEl) { return; }
    if (!g) {
      detailEl.innerHTML = '<h3>分组详情</h3><p class="lede">点击图中任一分组节点，或从下方清单选择一个分组。</p>';
      return;
    }
    var mem = DATA.nodes.filter(function(n){ return n.group === g.id; });
    var rows = mem.map(function(n){
      var link = n.status === "complete"
        ? '<a href="../11-node-pages/' + n.id.toLowerCase() + '.html">' + n.id + '</a>'
        : '<span class="nid">' + n.id + '</span> <span class="badge badge--pending">架构在册</span>';
      return "<tr><td>" + link + "</td><td>" + esc(n.name) + "</td><td>第 " + n.layer + " 层</td></tr>";
    }).join("");
    detailEl.innerHTML = '<h3>' + gseq(g.id) + ' ' + esc(g.name) + '</h3>'
      + '<p class="lede">' + esc(g.intro) + '</p>'
      + '<p class="meta-line"><span>节点 ' + g.nodeCount + ' 个</span><span>已写满 ' + g.completeCount
      + '</span><span>第 ' + g.layerMin + ' – ' + g.layerMax + ' 层</span>'
      + '<span>依赖层第 ' + (g.rank + 1) + ' 行</span></p>'
      + '<div class="table-scroll"><table><thead><tr><th>节点</th><th>名称</th><th>依赖深度</th></tr></thead><tbody>'
      + rows + '</tbody></table></div>'
      + '<p><a href="../12-groups/' + g.id.toLowerCase() + '.html">打开该分组的完整组页</a></p>';
  }

  function showNodeDetail(nid){
    var n = DATA.nodes.filter(function(x){ return x.id === nid; })[0];
    if (!n || !detailEl) { return; }
    var ins = DATA.nodeEdges.filter(function(e){ return e.target === nid; });
    var outs = DATA.nodeEdges.filter(function(e){ return e.source === nid; });
    var li = function(list, key){
      return list.map(function(e){
        var o = key === "source" ? e.source : e.target;
        return "<li><span class=\"nid\">" + o + "</span> <span class=\"tier\">" + e.rel + "</span> " + esc(e.note) + "</li>";
      }).join("") || "<li>无</li>";
    };
    detailEl.innerHTML = '<h3>' + esc(n.name) + '</h3>'
      + '<p class="meta-line"><span class="nid">' + n.id + '</span>'
      + gseq(n.group)
      + '<span>第 ' + n.layer + ' 层</span>'
      + (n.status === "complete" ? '<span class="badge badge--ok">内容已写满</span>'
         : '<span class="badge badge--pending">架构在册 · 内容待填充</span>') + '</p>'
      + '<div class="two-col"><div class="card--flat"><h3>前置</h3><ul class="tight">' + li(ins, "source") + '</ul></div>'
      + '<div class="card--flat"><h3>后继</h3><ul class="tight">' + li(outs, "target") + '</ul></div></div>'
      + (n.status === "complete"
         ? '<p><a href="../11-node-pages/' + n.id.toLowerCase() + '.html">打开节点页</a></p>'
         : '<p class="lede">该节点本轮为架构在册，节点页待后续波次填充。</p>')
      + '<p><a href="../12-groups/' + n.group.toLowerCase() + '.html">打开所属组页</a></p>';
  }

  function esc(s){ return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }

  function setHash(k, v){
    var h = "#" + k + "-" + encodeURIComponent(v);
    try { history.replaceState(null, "", h); } catch (e) { try { location.hash = h; } catch (e2) {} }
  }
  function clearHash(){
    try { history.replaceState(null, "", location.pathname + location.search); }
    catch (e) { try { location.hash = ""; } catch (e2) {} }
  }
  function readHash(){
    var h = location.hash.replace(/^#/, "");
    var m = /^group-(.+)$/.exec(h);
    if (m) { var g = decodeURIComponent(m[1]); if (byId(g)) { drill(g); return true; } }
    m = /^node-(.+)$/.exec(h);
    if (m) {
      var nid = decodeURIComponent(m[1]);
      var n = DATA.nodes.filter(function(x){ return x.id === nid; })[0];
      if (n) { drill(n.group); showNodeDetail(nid); return true; }
    }
    return false;
  }

  if (backBtn) { backBtn.addEventListener("click", function(){ overview(); clearHash(); }); }
  window.addEventListener("hashchange", function(){ if (!readHash()) { overview(); } });
  window.addEventListener("resize", function(){ fitPreset(); });

  if (!readHash()) { overview(); }

  // 主题/动效档变化时重建画布配色（画布色值取自 DATA.theme 的两套字面值）
  var mo = new MutationObserver(function(){
    if (!cy) { return; }
    cy.style().fromJson(styleSheet()).update();
    fitPreset();
  });
  mo.observe(document.documentElement, {attributes:true, attributeFilter:["data-theme"]});
})();
"""


def interactive_page(page_rel=None):
    data = build_data()
    groups = data["groups"]
    lay = data["layout"]
    fallback = []
    for g in groups:
        mem = [n for n in data["nodes"] if n["group"] == g["id"]]
        items = "".join('<li id="node-%s"><span class="nid">%s</span> %s %s</li>'
                        % (C.esc(n["id"]), C.esc(n["id"]),
                           C.esc(n["name"]),
                           "" if n["status"] == "complete" else '<span class="badge badge--pending">架构在册</span>')
                        for n in sorted(mem, key=lambda x: (x["layer"], x["id"])))
        fallback.append('<details class="card--flat" id="group-%s"><summary>%s %s（%d 个节点）</summary>'
                        '<ul class="tight node-list">%s</ul>'
                        '<p><a href="%s">打开该分组的完整组页</a></p></details>'
                        % (C.esc(g["id"]), C.group_mark(g["id"]), C.esc(g["name"]),
                           g["nodeCount"], items, C.esc(BASE + C.group_page_rel(g["id"]))))
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("交互全景图", None)]))
    body.append("<h1>交互全景图</h1>")
    # ★ SH4：本页导语提成局部变量 ⇒ `description` 与页首 `.lede` **同源**
    #   （⛔ 不为搜索引擎另写一句，避免同一页两种口径）
    lede = ('%s。本页先给出 <strong>组级总览</strong>（%d 个分组节点与它们之间的依赖），'
            '分组节点按<strong>依赖层分行</strong>摆放：行自上而下依赖逐层加深，行内自左向右是课程顺序，'
            '因此无需缩放或拖拽即可一眼看全。点击任一分组即下钻到该组的全部节点；'
            '虚线边框表示内容待填充的节点，实线边框表示内容已写满。'
            '依赖方向约定：A→B 表示先学 A 再学 B；双向箭头表示两个方向都有依赖'
            '（互为正反的两条依赖合成一条连线，避免两条边完全重合）。组身份由序号与名称承载，'
            '画布统一使用品牌色，不按分组分配色相。'
            % (C.esc(data["meta"]["audience"]), data["meta"]["groupCount"]))
    body.append('<p class="lede">%s</p>' % lede)
    body.append('<p class="meta-line"><span>节点 %d</span><span>边 %d</span><span>分组 %d</span>'
                "<span>依赖深度层 %d</span><span>数据时点 %s</span><span>版次 %s</span></p>"
                % (data["meta"]["nodeCount"], data["meta"]["edgeCount"], data["meta"]["groupCount"],
                   data["meta"]["layerCount"], C.esc(data["meta"]["as_of"]), C.esc(data["meta"]["edition"])))
    body.append('<div class="cy-wrap"><div class="cy-bar">'
                '<div><button type="button" class="cy-bar__btn" id="cy-back" disabled>返回总览</button> '
                '<span class="hint" id="cy-view-label">正在装配交互图…</span></div>'
                '<span class="hint" id="cy-hint">滚轮缩放、拖拽平移；点击分组下钻。</span></div>'
                '<div id="cy" data-placeholder="1" role="img" aria-label="知识分组依赖交互图">'
                '<p class="lede" style="padding:var(--space-3)">正在装配交互图…若长时间未出现，请查看下方'
                "「分组与节点清单」。</p></div></div>")
    body.append('<div class="card--flat" id="cy-detail"><h3>分组详情</h3>'
                '<p class="lede">点击图中任一分组节点，或从下方清单选择一个分组。</p></div>')
    body.append("<h2>图例</h2>")
    body.append('<div class="legend" data-reveal="1" style="--i:0">%s</div>'
                % "".join(C.group_chip(g["id"], g["name"]) for g in groups))
    body.append('<div class="legend" data-reveal="1" style="--i:1">'
                '<span class="badge badge--ok">内容已写满</span>'
                '<span class="badge badge--pending">架构在册 · 内容待填充</span>'
                '<span class="tier">虚线边 = 概念升级</span>'
                '<span class="tier">双向箭头 = 两个方向都有依赖</span>'
                '<span class="tier">数字 = 该连线上的依赖条数（≥%d 才标注，未标注 = 1 条）</span>'
                '<span class="tier">行 = 依赖层（自上而下加深）</span>'
                '<span class="tier">行内自左向右 = 课程顺序</span></div>'
                % lay["edgeLabelMinCount"])
    body.append("<h2>分组与节点清单（无脚本时的等价导航）</h2>")
    body.append("\n".join(fallback))
    body.append('<script type="application/json" id="cy-data">%s</script>'
                % json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/"))
    body.append("<script>%s</script>" % APP_JS.replace("__FONT__", json.dumps(FONT_STACK)))
    head_extra = '<script src="vendor/cytoscape.min.js"></script>\n'
    return C.page_shell(BASE, "interactive", "INTERACTIVE", "交互全景图", "\n".join(body),
                        head_extra=head_extra,
                        # ★ SH4：description 取本页导语首句（与页首 `.lede` 同源）。
                        #   ★ 但**首句是受众从句**（「面向…工程师。」），它 ① 只有 20 字
                        #     ② 与站点标语高度近义 ⇒ 对搜索引擎等于没有信息（`og:description`
                        #     也失去摘要价值）。⇒ 判据 `gate_seo_meta.py` 的 S11 会对
                        #     「过短」与「与站点标语近义」判 FAIL，故这里传**整段导语**，
                        #     由 `clip_desc` 截到 160 字 —— 它才是这一页真正在讲什么。
                        meta_desc=lede,
                        page_rel=page_rel or C._derive_page_rel("interactive", "INTERACTIVE"))


def generate(root=None):
    # ★ SH4：把**产物路径本身**传给页面构建器 ⇒ canonical 与产物同源（⛔ 不在别处另推一份）
    rel = "%s/index.html" % C.DIR_INTERACTIVE
    return {rel: interactive_page(page_rel=rel)}


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
