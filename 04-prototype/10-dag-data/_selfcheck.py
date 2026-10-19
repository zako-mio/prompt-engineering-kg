#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读自检：10-dag-data 五个真相源文件的结构 / 无环 / 分层 / 引用 / 长度配额 / 对比度。

★ 2026-10-16 一并更正两处陈旧表述（⛔ 未改任何断言的作用域）：
   ① 路径 `05-dag-data` → `10-dag-data`（目录早已更名，此处是残留笔误）；
   ② C23–C27 由「content_status 配额」改为「**状态↔内容一致性**」
      （登记件：16-checkpoint/CRITERIA-CHANGE-P22.md，与门控 P22 同批同源）。

仅读取，不写任何文件；退出码 0 = 全部 PASS，非 0 = 存在 FAIL。
对比度按 WCAG 2.x 公式 (L1+0.05)/(L2+0.05) 现场复算，不采信登记值。
"""
import json
import os
import re
import sys
from collections import deque
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent

REL_ENUM = {"PREREQ", "CONTAINS", "UPGRADE", "FLOW"}
COMPLETE_MIN = 3
# ★ 原 REGISTERED_MIN = 60 已于 2026-10-16 撤销（见 16-checkpoint/CRITERIA-CHANGE-P22.md）：
#   数量配额无因果依据，且其适用阶段（注册期）在内容填充期结束 ⇒ 换成 C27 的双向一致性断言。
BODY_MIN_CONTRAST = 4.5

fails = []
warns = []


def chk(cid, ok, msg):
    print(f"[{'PASS' if ok else 'FAIL'}] {cid} {msg}")
    if not ok:
        fails.append(cid)


def warn(cid, msg):
    print(f"[WARN] {cid} {msg}")
    warns.append(cid)


def load(name):
    p = HERE / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        chk(f"JSON::{name}", False, f"读取或解析失败：{e}")
        return None


# ---------- 对比度（WCAG 2.x 相对亮度） ----------
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(hexcolor):
    h = hexcolor.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


# ---------- 读文件 ----------
dag = load("dag.json")
frontier = load("frontier.json")
glossary = load("glossary.json")
sources = load("sources.json")
tokens = load("site-tokens.json")
if not all([dag, frontier, glossary, sources, tokens]):
    print("\n== 自检 FAIL（存在无法解析的 JSON） ==")
    sys.exit(1)

meta = dag["meta"]
groups = dag["groups"]
nodes = dag["nodes"]
edges = dag["edges"]
layers = dag["layers"]
src_list = sources["sources"]
terms = glossary["terms"]
items = frontier["items"]

node_by_id = {n["id"]: n for n in nodes}
src_by_id = {s["id"]: s for s in src_list}
term_names = {t["term"] for t in terms}

# ---------- C01 计数一致性 ----------
chk("C01-counts-nodes", meta["node_count"] == len(nodes),
    f"node_count={meta['node_count']} 与实际 {len(nodes)} 一致")
chk("C02-counts-edges", meta["edge_count"] == len(edges),
    f"edge_count={meta['edge_count']} 与实际 {len(edges)} 一致")
chk("C03-counts-groups", meta["group_count"] == len(groups),
    f"group_count={meta['group_count']} 与实际 {len(groups)} 一致")
chk("C04-counts-layers", meta["layer_count"] == len(layers),
    f"layer_count={meta['layer_count']} 与实际 {len(layers)} 一致")
chk("C05-meta-fixed", meta["as_of"] == "2026-10" and meta["edition"] == "v1"
    and meta["acyclic"] is True
    and meta["audience"] == "有工程基础、提示词工程未系统化的工程师",
    "meta.as_of=2026-10 / edition=v1 / acyclic=true / audience 逐字一致")
chk("C06-direction-rule", "先学 A" in meta.get("direction_rule", ""),
    "meta.direction_rule 写明 A→B 表示先学 A")

# ---------- C07 id 唯一 ----------
ids = [n["id"] for n in nodes]
dup = sorted({i for i in ids if ids.count(i) > 1})
chk("C07-id-unique", not dup, f"节点 id 唯一（重复：{dup}）")
chk("C08-group-id-unique", len({g["id"] for g in groups}) == len(groups),
    "分组 id 唯一")

# ---------- C09 组归属与每组非空 ----------
gids = {g["id"] for g in groups}
bad_group = [n["id"] for n in nodes if n["group"] not in gids]
chk("C09-group-resolvable", not bad_group, f"节点 group 均在 groups 中（越界：{bad_group}）")
for g in groups:
    n_in = [n["id"] for n in nodes if n["group"] == g["id"]]
    if len(n_in) != g["node_count"]:
        chk(f"C10-G-{g['id']}", False, f"{g['id']} node_count={g['node_count']} 与实为 {len(n_in)} 不符")
    else:
        chk(f"C10-G-{g['id']}", len(n_in) >= 1, f"{g['id']} 节点数 {len(n_in)} 且与登记一致")

# ---------- C11 rel 闭集与边端点可解析 ----------
bad_rel = [e for e in edges if e["rel"] not in REL_ENUM]
chk("C11-rel-enum", not bad_rel, f"edges[].rel 全部 ∈ {sorted(REL_ENUM)}（越界：{len(bad_rel)}）")
bad_ep = [e for e in edges if e["source"] not in node_by_id or e["target"] not in node_by_id]
chk("C12-edge-endpoints", not bad_ep, f"边两端节点均可解析（坏边：{len(bad_ep)}）")
selfloop = [e for e in edges if e["source"] == e["target"]]
chk("C13-no-selfloop", not selfloop, f"无自环（自环：{len(selfloop)}）")

# ---------- C14 无环（Kahn 拓扑排序） ----------
adj = {n["id"]: [] for n in nodes}
indeg = {n["id"]: 0 for n in nodes}
for e in edges:
    if e["source"] in adj and e["target"] in indeg:
        adj[e["source"]].append(e["target"])
        indeg[e["target"]] += 1
q = deque([i for i, d in indeg.items() if d == 0])
seen = 0
while q:
    u = q.popleft()
    seen += 1
    for v in adj[u]:
        indeg[v] -= 1
        if indeg[v] == 0:
            q.append(v)
chk("C14-acyclic", seen == len(nodes), f"Kahn 拓扑覆盖 {seen}/{len(nodes)} 节点（无环）")

# ---------- C15 边方向与 layer 一致 ----------
layer_of = {}
for lk, arr in layers.items():
    for nid in arr:
        layer_of[nid] = int(lk)
not_in_layers = [i for i in ids if i not in layer_of]
chk("C15-layer-covers-all", not not_in_layers, f"layers 覆盖全部节点（缺：{not_in_layers[:8]}）")
bad_layers_field = [n["id"] for n in nodes
                    if n["id"] in layer_of and n["layer"] != layer_of[n["id"]]]
chk("C16-layer-field-consistent", not bad_layers_field,
    f"节点 layer 字段与 layers 映射一致（不一致：{bad_layers_field[:8]}）")
viol = []
for e in edges:
    a, b = e["source"], e["target"]
    if a in layer_of and b in layer_of and not layer_of[a] < layer_of[b]:
        viol.append((a, b, layer_of[a], layer_of[b]))
chk("C17-layer-order", not viol, f"每条边 A→B 满足 layer(A)<layer(B)（违例：{len(viol)} 条）")

# 最长路径分层复核（拓扑层 = 最长路径长度）
depth = {i: 0 for i in ids}
order = []
indeg2 = {i: 0 for i in ids}
for e in edges:
    indeg2[e["target"]] += 1
q2 = deque([i for i, d in indeg2.items() if d == 0])
while q2:
    u = q2.popleft()
    order.append(u)
    for v in adj[u]:
        depth[v] = max(depth[v], depth[u] + 1)
        indeg2[v] -= 1
        if indeg2[v] == 0:
            q2.append(v)
mismatch = [i for i in ids if i in layer_of and depth[i] != layer_of[i]]
if mismatch:
    warn("C18-longest-path",
         f"{len(mismatch)} 个节点的 layer 不等于最长路径长度（不违例，仅提示）：{mismatch[:10]}")
else:
    chk("C18-longest-path", True, "全部节点 layer 等于自根节点的最长路径长度")

# ---------- C19 无孤立节点（layer 0 除外） ----------
has_edge = set()
for e in edges:
    has_edge.add(e["source"])
    has_edge.add(e["target"])
orphan = [n["id"] for n in nodes if n["id"] not in has_edge and layer_of.get(n["id"], 0) != 0]
chk("C19-no-orphan", not orphan, f"非 layer0 节点均有边（孤立：{orphan}）")
orphan0 = [n["id"] for n in nodes if n["id"] not in has_edge and layer_of.get(n["id"], 0) == 0]
if orphan0:
    warn("C19b-layer0-orphan", f"layer0 中的孤立节点（允许）：{orphan0}")

# ---------- C20 prereq / successors 双向一致 ----------
prereq_bad, succ_bad = [], []
succ_from_edges = {i: [] for i in ids}
pre_from_edges = {i: [] for i in ids}
for e in edges:
    succ_from_edges[e["source"]].append(e["target"])
    pre_from_edges[e["target"]].append(e["source"])
for n in nodes:
    for p in n.get("prereq", []):
        if p not in node_by_id:
            prereq_bad.append((n["id"], p))
    for s in n.get("successors", []):
        if s not in node_by_id:
            succ_bad.append((n["id"], s))
chk("C20-prereq-resolvable", not prereq_bad, f"prereq 指向存在节点（坏：{prereq_bad[:6]}）")
chk("C21-succ-resolvable", not succ_bad, f"successors 指向存在节点（坏：{succ_bad[:6]}）")
# prereq / successors 是导航提示，允许是 edges 的子集；⛔ 不得出现 edges 之外的条目
extra_p = [(n["id"], p) for n in nodes for p in n.get("prereq", [])
           if p not in pre_from_edges[n["id"]]]
extra_s = [(n["id"], s) for n in nodes for s in n.get("successors", [])
           if s not in succ_from_edges[n["id"]]]
chk("C22-prereq-subset", not extra_p, f"prereq 是入边的子集（越界：{extra_p[:6]}）")
chk("C22b-succ-subset", not extra_s, f"successors 是出边的子集（越界：{extra_s[:6]}）")
mutual = []
for n in nodes:
    for p in n.get("prereq", []):
        if n["id"] not in node_by_id[p].get("successors", []):
            mutual.append((n["id"], "prereq", p))
    for s in n.get("successors", []):
        if n["id"] not in node_by_id[s].get("prereq", []):
            mutual.append((n["id"], "successor", s))
if mutual:
    warn("C22c-mutual-nav", f"{len(mutual)} 处 prereq/successors 非互指（提示项）：{mutual[:6]}")
else:
    chk("C22c-mutual-nav", True, "prereq 与 successors 互指一致")

# ---------- C23 content_status **状态↔内容一致性** ----------
# ★ 2026-10-16 判据变更（与门控 P22 同批、同源同值；登记件 16-checkpoint/CRITERIA-CHANGE-P22.md）：
#   撤销旧形 C24「complete 恰好 3 个」、C25「registered = 全量-3」、C27「固定名单」与 C26 的
#   `registered ≥60` 半句 —— 后者无因果依据，且其适用阶段（注册期）在内容填充期结束。
#   换成**双向一致性**：complete ⟺ 8 区块全非空（见 C29）；registered ⟹ lab/evidence/pitfalls 必须为空。
complete = [n["id"] for n in nodes if n["content_status"] == "complete"]
registered = [n["id"] for n in nodes if n["content_status"] == "registered"]
other = [n["id"] for n in nodes if n["content_status"] not in ("complete", "registered")]
chk("C23-status-enum", not other, f"content_status 仅两态（越界：{other}）")
chk("C24-complete-count", len(complete) >= COMPLETE_MIN,
    f"complete ≥{COMPLETE_MIN}（实为 {len(complete)}：{complete}）")
chk("C25-registered-count", len(registered) == len(nodes) - len(complete),
    f"registered = 全量 - complete（实为 {len(registered)}，应为 {len(nodes) - len(complete)}）")
chk("C26-two-state-sum", len(complete) + len(registered) == len(nodes),
    f"两态合计 = 全量注册数（{len(complete)} + {len(registered)} = {len(nodes)}）")
_mislabel = [(n["id"], [b for b in ("lab", "evidence", "pitfalls") if n.get(b)]) for n in nodes
             if n["content_status"] == "registered"
             and any(n.get(b) for b in ("lab", "evidence", "pitfalls"))]
chk("C27-content-status-consistent", not _mislabel,
    f"内容已填即须翻 complete（仍标 registered 而三块非空：{_mislabel[:6]}）")

# ---------- C28 长度约束（★ 2026-10-16：口径统一为 **caliber**，⛔ 废除 len() 口径） ----------
# ★ 触发事实（本轮当场踩到，登记在 16-checkpoint/CRITERIA-CHANGE-P05-R5.md §5）：补写 PE-R-02 的机制句后，
#   **len 口径**下 intro = 270 > 250 报 WARN，而 **caliber 口径**下 = 204 ≤ 250 ⇒ 同一字段、两条阈值、
#   两种单位，必然漂移。而 SCHEMA §3 的「口径定义（唯一，全站一致）」早已写死 caliber
#   ⇒ 数据侧自检同批统一，并与门控 P05 / P22 **同源同值**。
import re as _re


def _caliber(s):
    """契约口径：汉字数 + 拉丁词数（不计标点与空白）。"""
    return len(_re.findall(r"[\u4e00-\u9fff]", s)) + len(_re.findall(r"[A-Za-z][A-Za-z0-9\-'.]*", s))


WHY_LO = {"complete": 80, "registered": 60}
INTRO_LO = {"complete": 150, "registered": 120}
# ★ 2026-10-16（P05-R5 的 B-2）：上限由**真实渲染**重导 —— 一屏可读量（1440×900）实测下界，
#   取证装置 = 16-checkpoint/_probe_thresholds.py。⛔ 两者都是**报告项**，⛔ 不判 FAIL。
WHY_UP_REPORT = 693
INTRO_UP_REPORT = 777
SUMMARY_UP_REPORT = 80          # ★ 本轮未重导（B-2 的对象是 why 上限与 intro 下限）
short = []
why_report = []
for n in nodes:
    st = n["content_status"]
    why_report.append((n["id"], st, _caliber(n.get("why", "")), _caliber(n.get("intro", ""))))
    if _caliber(n.get("why", "")) < WHY_LO.get(st, 60):
        short.append((n["id"], "why", _caliber(n.get("why", "")), WHY_LO.get(st, 60)))
    if _caliber(n.get("intro", "")) < INTRO_LO.get(st, 120):
        short.append((n["id"], "intro", _caliber(n.get("intro", "")), INTRO_LO.get(st, 120)))
chk("C28-lengths-caliber", not short,
    f"why / intro 下限（caliber 口径，与门控 P05 同源同值）全部满足（不足：{short[:6]}）")
long_viol = [(n["id"], "why", _caliber(n["why"])) for n in nodes if _caliber(n["why"]) > WHY_UP_REPORT] \
    + [(n["id"], "intro", _caliber(n["intro"])) for n in nodes if _caliber(n["intro"]) > INTRO_UP_REPORT] \
    + [(n["id"], "summary", _caliber(n["summary"])) for n in nodes
       if _caliber(n["summary"]) > SUMMARY_UP_REPORT]
warn("C28b-upper-report",
     f"上限**报告项**（caliber 口径；实测一屏可读量 = why {WHY_UP_REPORT} / intro {INTRO_UP_REPORT}；"
     f"summary {SUMMARY_UP_REPORT} 本轮未重导）：超出 {len(long_viol)} 处 {long_viol[:6]}")

# ---------- C28c why/intro 口径逐条打印（★ 阈值已上收到 C28，此处只出**读数**） ----------
# ★ 2026-10-16：原 C28c 自己带一份 why 下限阈值 ⇒ 与 C28 形成两处阈值 ⇒ 同批**只留一处**：
#   阈值在 C28（与门控同值），C28c 退回为「逐条打印」（报告项），消除漂移面。
_sm = [_caliber(n.get("summary", "")) for n in nodes]
print("-- 长度口径逐条（汉字 + 拉丁词；下限 complete 80/150 · registered 60/120）--")
for _i, _s, _w, _n in why_report:
    print(f"   {_i:10s} {_s:11s} why {_w:4d}  intro {_n:4d}")
warn("C28c-caliber-report",
     f"why 实测区间 {min(x[2] for x in why_report)}–{max(x[2] for x in why_report)}；"
     f"intro 实测区间 {min(x[3] for x in why_report)}–{max(x[3] for x in why_report)}；"
     f"summary 实测区间 {min(_sm)}–{max(_sm)}（均为报告项，⛔ 不判 FAIL）")

# ---------- C29 complete 节点 8 区块全非空 ----------
BLOCKS = ["why", "intro", "when", "lab", "evidence", "terms", "pitfalls", "summary"]
empty_detail = []
for n in nodes:
    if n["content_status"] != "complete":
        continue
    for b in BLOCKS:
        v = n.get(b)
        if v is None or (isinstance(v, (list, str)) and len(v) == 0):
            empty_detail.append((n["id"], b))
chk("C29-complete-blocks", not empty_detail, f"complete 节点 8 区块全非空（空：{empty_detail}）")

# ---------- C30 registered 允许为空但三段必填且非空洞 ----------
HOLLOW = re.compile(r"(待填充|TBD|TODO|待补|占位|待定)")
hollow = []
for n in nodes:
    if n["content_status"] != "registered":
        continue
    for f in ("why", "intro", "summary"):
        if HOLLOW.search(n.get(f, "")):
            hollow.append((n["id"], f))
chk("C30-no-hollow", not hollow, f"registered 节点三段无空洞占位（命中：{hollow}）")

# ---------- C31 evidence 契约 ----------
ev_bad = []
for n in nodes:
    for ev in n.get("evidence", []):
        keys = {"claim", "source_id", "url", "quote", "tier"}
        if not keys.issubset(ev.keys()):
            ev_bad.append((n["id"], "字段缺失", sorted(keys - set(ev.keys()))))
            continue
        if ev["source_id"] not in src_by_id:
            ev_bad.append((n["id"], "source_id 不可解析", ev["source_id"]))
            continue
        if src_by_id[ev["source_id"]]["url"] != ev["url"]:
            ev_bad.append((n["id"], "url 与台账不一致", ev["source_id"]))
        if src_by_id[ev["source_id"]]["tier"] != ev["tier"]:
            ev_bad.append((n["id"], "tier 与台账不一致", ev["source_id"]))
        if len(ev["quote"]) > 200:
            ev_bad.append((n["id"], "quote 超 200 字", len(ev["quote"])))
        if not ev["claim"].strip():
            ev_bad.append((n["id"], "claim 为空", ""))
chk("C31-evidence-contract", not ev_bad, f"evidence 每条字段齐全且可回源（坏：{ev_bad[:6]}）")

# ---------- C32 `boundary` 字段必填且不重复（★ 2026-10-16 B-1：由子串探测改为字段断言） ----------
# ★ 旧形的失效面（登记在 16-checkpoint/CRITERIA-CHANGE-P05-R5.md）：`BOUNDARY_HINT` 里那个粗粒度的
#   「边界」会命中的**主题词**（实测 PE-F-03 的「…而是边界：」），而真正的适用边界句反而可能不命中
#   ⇒ 探测口径与对象脱钩。现改为字段断言：① 非空；② 整句不得与 why/intro 的整句逐字相同；
#   ③ why/intro 中不得残留引导串（否则渲染会切出第二个「适用边界」块）。
def _sentences(s):
    return [x for x in re.split(r"(?<=[。！？!?])", (s or "").strip()) if x.strip()]


def _norm_sent(s):
    return re.sub(r"\s+", "", s or "").strip()


_BOUNDARY_MARK = re.compile(r"适用边界是|适用边界必须写清")
_bad_bd = []
for n in nodes:
    _bd = (n.get("boundary") or "").strip()
    if not _bd:
        _bad_bd.append((n["id"], "boundary 为空"))
        continue
    _dups = [_norm_sent(x) for x in _sentences(n.get("why", "")) + _sentences(n.get("intro", ""))]
    if _norm_sent(_bd) in _dups:
        _bad_bd.append((n["id"], "boundary 与 why/intro 整句重复"))
    for _f in ("why", "intro"):
        if _BOUNDARY_MARK.search(n.get(_f, "") or ""):
            _bad_bd.append((n["id"], _f + " 残留引导串"))
chk("C32-boundary-field", not _bad_bd,
    f"每个节点 boundary 非空 / 不与 why·intro 整句重复 / 正文不残留引导串（坏：{_bad_bd[:6]}）")

# ---------- C33 术语解析 ----------
term_bad = []
for n in nodes:
    for t in n.get("terms", []):
        head = t.split("：")[0].strip()
        if head not in term_names:
            term_bad.append((n["id"], head[:28]))
chk("C33-terms-resolvable", not term_bad,
    f"节点 terms 逐条可在 glossary 解析（未命中：{term_bad[:6]}）")
ref_bad = []
for t in terms:
    for r in t["node_refs"]:
        if r not in node_by_id:
            ref_bad.append((t["term"], r))
chk("C34-glossary-refs", not ref_bad, f"glossary.node_refs 均可解析（坏：{ref_bad[:6]}）")
chk("C35-glossary-count", len(terms) >= 35, f"术语数 {len(terms)} ≥ 35")
term_dup = sorted({t["term"] for t in terms if [x["term"] for x in terms].count(t["term"]) > 1})
chk("C36-term-unique", not term_dup, f"术语表述唯一（重复：{term_dup}）")

# ---------- C37 sources 台账 ----------
chk("C37-sources-count", len(src_list) >= 40, f"引用台账 {len(src_list)} 条 ≥ 40")
sid_dup = sorted({s["id"] for s in src_list if [x["id"] for x in src_list].count(s["id"]) > 1})
chk("C38-source-id-unique", not sid_dup, f"source id 唯一（重复：{sid_dup}）")
sid_fmt = [s["id"] for s in src_list if not re.fullmatch(r"S-\d{4}", s["id"])]
chk("C39-source-id-format", not sid_fmt, f"source id 形如 S-0001（异常：{sid_fmt[:5]}）")
tier_bad = [s["id"] for s in src_list if s["tier"] not in ("official", "paper", "vendor", "community")]
chk("C40-source-tier", not tier_bad, f"tier 属四值闭集（越界：{tier_bad[:5]}）")
field_bad = [s["id"] for s in src_list
             if not all(k in s for k in ("title", "url", "tier", "date", "note")) or not s["url"].startswith("http")]
chk("C41-source-fields", not field_bad, f"台账每条字段齐全且 url 为 http(s)（缺：{field_bad[:5]}）")
date_bad = [s["id"] for s in src_list
            if s["date"] is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s["date"]))]
chk("C42-source-date", not date_bad, f"date 为 YYYY-MM-DD 或 null（异常：{date_bad[:5]}）")
chk("C43-source-declared-count", sources["meta"]["count"] == len(src_list),
    f"sources.meta.count={sources['meta']['count']} 与实为 {len(src_list)} 一致")

# ---------- C44 frontier ----------
chk("C44-frontier-anchors", frontier["as_of"] == "2026-10" and frontier["edition"] == "2026-10"
    and frontier["previous_edition"] is None,
    "frontier as_of=2026-10 / edition=2026-10 / previous_edition=null")
chk("C45-tracking-sources", len(frontier["tracking_sources"]) >= 4,
    f"tracking_sources {len(frontier['tracking_sources'])} 条 ≥ 4")
ts_kind_bad = [t for t in frontier["tracking_sources"] if t.get("kind") not in ("preprint", "official", "conference")]
chk("C46-tracking-kind", not ts_kind_bad, f"tracking kind 属闭集（越界：{len(ts_kind_bad)}）")
n_ids = [n["id"] for n in nodes if n["group"] == "GD-N"]
f_ids = [i["id"] for i in items]
chk("C47-frontier-items", sorted(n_ids) == sorted(f_ids),
    f"frontier.items 恰为 GD-N 四节点（差集：{set(n_ids) ^ set(f_ids)}）")
st_bad = [i["id"] for i in items if i["status"] not in ("confirmed", "disputed", "unverified")]
chk("C48-frontier-status", not st_bad, f"status 属三值闭集（越界：{st_bad}）")
sup_bad = [(i["id"], s) for i in items for s in i["supersedes"] if s not in node_by_id]
chk("C49-frontier-supersedes", not sup_bad, f"supersedes 均可解析（坏：{sup_bad[:5]}）")
fev_bad = []
for i in items:
    if i["status"] == "unverified" and not i.get("offline_repro"):
        fev_bad.append((i["id"], "unverified 缺 offline_repro"))
    if len(i.get("evidence", [])) < 1:
        fev_bad.append((i["id"], "evidence 为空"))
    for ev in i.get("evidence", []):
        if ev["source_id"] not in src_by_id:
            fev_bad.append((i["id"], f"source_id 不可解析 {ev['source_id']}"))
        elif src_by_id[ev["source_id"]]["url"] != ev["url"]:
            fev_bad.append((i["id"], f"url 与台账不一致 {ev['source_id']}"))
chk("C50-frontier-evidence", not fev_bad, f"frontier 条目证据契约成立（坏：{fev_bad[:5]}）")
chk("C51-frontier-has-repro", all(i.get("offline_repro") for i in items),
    "每条 frontier 条目都给出离线复现步骤或未实测标注")

# ---------- C52 令牌与对比度 ----------
tk_list = tokens["tokens"]
chk("C52-token-names", all(k in {t["name"] for t in tk_list} for k in ("--warn", "--danger")),
    "--warn / --danger 均已登记")
group_tokens = [t for t in tk_list if t["name"].startswith("--group-")]
chk("C53-group-tokens", len(group_tokens) == len(groups),
    f"组配色令牌 {len(group_tokens)} 个，与分组数 {len(groups)} 一致")
tk_field_bad = [t["name"] for t in tk_list
                if not all(k in t for k in ("name", "light", "dark", "usage_tier", "contrast_checked"))
                or t["usage_tier"] not in ("body", "non-body", "non-text")]
chk("C54-token-fields", not tk_field_bad, f"每条令牌字段齐全且用途档合法（异常：{tk_field_bad[:5]}）")

measured = []
body_fail = []
declared_mismatch = []
for t in tk_list:
    for mode, bg in (("light", tokens["reference_backgrounds"]["light"]),
                     ("dark", tokens["reference_backgrounds"]["dark"])):
        c = contrast(t[mode], bg)
        measured.append((t["name"], mode, c))
        cov = t.get("contrast_checked", {})
        dec = (cov.get("measured") or {}).get(mode)
        if dec is None or abs(float(dec) - c) > 0.02:
            declared_mismatch.append((t["name"], mode, dec, c))
        if t["usage_tier"] == "body" and c < BODY_MIN_CONTRAST:
            body_fail.append((t["name"], mode, c))
chk("C55-body-contrast", not body_fail,
    f"正文类令牌对底色 ≥ {BODY_MIN_CONTRAST}:1（不达标：{body_fail}）")
chk("C56-declared-contrast", not declared_mismatch,
    f"登记对比度与现场复算一致（偏差：{declared_mismatch[:6]}）")

# 组配色上的标签前景色（由亮度择优）
label_fail = []
for t in group_tokens:
    for mode, bg in (("light", tokens["reference_backgrounds"]["light"]),
                     ("dark", tokens["reference_backgrounds"]["dark"])):
        fg = "#000000" if contrast(t[mode], "#000000") >= contrast(t[mode], "#ffffff") else "#ffffff"
        c = contrast(t[mode], fg)
        if c < 4.5:
            label_fail.append((t["name"], mode, fg, c))
chk("C57-group-label-contrast", not label_fail,
    f"组配色上由亮度择优的标签色 ≥4.5:1（不达标：{label_fail}）")

# ---------- C58 引文回源（★ 2026-10-16 第 6 轮：G14「机制已建但未升级为判据」的判据化） ----------
# 机制来源：作者期助手 `16-checkpoint/_wave1_apply.py` 的 `load_pack_quotes()` + 片段比对
#   —— 第 5 轮它只存在于**提交前**（构建链与门控都不跑）⇒ 本轮**搬到数据侧**成为 C58。
# 断言：每条 `evidence.quote` 按省略号（`...` / `…`）拆片段，逐片段须能在
#   `01-research/evidence/A*.json` 的 `metas[].quote` 里**逐字定位**（空白归一化后子串命中）。
# ⛔ fail-closed：引文库一个文件都读不到（路径错/被删）⇒ **FAIL**，⛔ 不静默放行。
# ★ 诚实边界（必读）：
#   ① 本条挡的是「**凭空写一句**」；⛔ **挡不住**「引文库本身被改错」（那需要回源到原始 URL）；
#   ② 本条对象**只有节点侧**；`frontier.json` 的引文实测有 **2 条**无法在 A 池逐字回源
#      （形态是作者期注记而非原文引用）⇒ 登记为 **WARN**（report-only），⛔ 既不改数据、也不假装已覆盖。
#      见 `16-checkpoint/CRITERIA-CHANGE-P13-C58-P41.md` 的局限登记。
_ELISION = _re.compile(r"\s*\.\.\.\s*|\s*…\s*")


def _ws(s):
    return _re.sub(r"\s+", " ", (s or "")).strip()


_PACKS = sorted((HERE.parent.parent / "01-research" / "evidence").glob("A*.json"))
_pack_quotes = {}
_pack_err = []
for _p in _PACKS:
    try:
        _d = json.loads(_p.read_text(encoding="utf-8"))
    except Exception as _e:  # noqa: BLE001
        _pack_err.append((_p.name, f"{type(_e).__name__}: {_e}"[:70]))
        continue
    for _m in _d.get("metas", []):
        _q = _ws(_m.get("quote", ""))
        if _q:
            _pack_quotes.setdefault(_q, []).append(_p.name)

_q_bad = list(_pack_err)
_n_quotes = 0
# ★ 2026-10-19 第 9 轮（见 `16-checkpoint/CRITERIA-CHANGE-R09.md`）：**C58 的对象条件**。
#   引文库 `01-research/` 按 `.gitignore` 规则①**整层不入库** ⇒ 任何**新 checkout**（CI 或新克隆）
#   都没有它。此时 C58 **无对象**：既不能判「逐字回源」（无从比对），也**不得静默算通过**。
#   ⇒ 处置：**只有**在「库确实不存在」且**调用方显式声明**（环境变量）时，本条打印 `[SKIP]` 并给出理由；
#     库在盘上时**开关无效**（fail-closed 语义原样保留：读不到库 ⇒ FAIL）。
#   ★ 这是「显式不跑」而非「放宽」：本判据在**本机**（库在）仍必须跑、仍必须 PASS。
_NO_LIB_DECLARED = (not _PACKS) and (os.environ.get("PEKG_INPUT_LIBRARY_ABSENT") == "1")
if _NO_LIB_DECLARED:
    print("[SKIP] C58-quote-provenance 本 checkout 无输入层（`01-research/evidence/A*.json` 不在盘上）"
          " ⇒ 本判据**无对象**；★ 由调用方显式声明（`PEKG_INPUT_LIBRARY_ABSENT=1`），"
          "⛔ 不是静默通过、⛔ 不得读作「引文回源已覆盖」")
else:
    if not _PACKS:
        _q_bad.append(("(引文库)", "01-research/evidence/A*.json 一个都读不到 ⇒ fail-closed"))
    else:
        for _n in nodes:
            for _i, _ev in enumerate(_n.get("evidence", []) or []):
                _n_quotes += 1
                _frags = [f for f in _ELISION.split(_ws(_ev.get("quote", ""))) if f.strip()]
                if not _frags:
                    _q_bad.append((_n["id"], _i, "quote 为空（无可比对片段）"))
                    continue
                for _f in _frags:
                    if not any(_f in _pq for _pq in _pack_quotes):
                        _q_bad.append((_n["id"], _i, _f[:56]))
    chk("C58-quote-provenance", not _q_bad,
        f"evidence 引文逐片段可在引文库逐字回源（节点侧 {_n_quotes} 条 evidence / "
        f"库内 {len(_pack_quotes)} 条唯一引文，源件 {len(_PACKS)} 个；坏：{_q_bad[:5]}）")

# ---- C58 的 frontier 侧：**报告项**（⛔ 不判 FAIL，⛔ 不得读作「已覆盖」）----
_frontier = load("frontier.json")
_f_bad = []
_f_n = 0
for _it in (_frontier or {}).get("items", []):
    for _ev in _it.get("evidence", []) or []:
        _f_n += 1
        for _f in [x for x in _ELISION.split(_ws(_ev.get("quote", ""))) if x.strip()]:
            if not any(_f in _pq for _pq in _pack_quotes):
                _f_bad.append((_it["id"], _ev.get("source_id", ""), _f[:40]))
if _NO_LIB_DECLARED:
    # ★ 同上：库不在盘上时本报告项无意义（空库会把命中率算成 100%），显式声明而不静默给出误导读数。
    print("[SKIP] C58b-frontier-quotes 本 checkout 无输入层 ⇒ 该**报告项**无对象"
          "（⛔ 不得读作「frontier 引文已全部回源」）")
else:
    warn("C58b-frontier-quotes",
         f"**报告项**（⛔ 不判 FAIL）：frontier 侧 {_f_n} 条 evidence 中有 {len(_f_bad)} 片无法在 A 池逐字回源 "
         f"{_f_bad[:4]}；形态为作者期注记而非原文引用 ⇒ 本轮**不改数据**，如实登记为缺口"
         f"（见 CRITERIA-CHANGE-P13-C58-P41.md）")

print("\n-- 实测对比度（对页面底色，WCAG 2.x） --")
for name, mode, c in measured:
    print(f"  {name:<24} {mode:<5} {c:>6.2f}:1")
if group_tokens:
    print("-- 组配色上的标签色（亮度择优） --")
    for t in group_tokens:
        vals = []
        for mode in ("light", "dark"):
            fg = "#000000" if contrast(t[mode], "#000000") >= contrast(t[mode], "#ffffff") else "#ffffff"
            vals.append(f"{mode}: {fg} on {t[mode]} = {contrast(t[mode], fg):.2f}:1")
        print(f"  {t['name']:<16} " + " | ".join(vals))

print(f"\n== 自检：{'PASS' if not fails else 'FAIL ' + str(fails)} ==  "
      f"(FAIL {len(fails)} 项 / WARN {len(warns)} 项)")
sys.exit(0 if not fails else 1)
