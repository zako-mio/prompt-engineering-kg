#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_selfcheck_p35_fixtures.py —— P35 负例夹具的**对应关系**与**阈值边界**自检（⛔ 只读，不写产物）。

为什么需要它：`gate_prototype.py --selftest` 只报「负例是否触发」，⛔ 不报「触发的是不是
它该触发的那一条」，也⛔ 不报「阈值另一侧会不会误判」。本脚本做四件事：

  ① 正向复跑：`check_p35` 在真实产物上必须 PASS；
  ② 逐条跑 `mut_p35` 的夹具并打印 bad 明细 —— 核对「夹具 → 子断言」的一一对应
     （防「负例触发了、但触发在别处」这种假自检）；
  ③ ★ **阈值边界探针**（G4 新增，针对 ⑫ 代理判据）：在组页 #sec-nodes 里分别注入
     **3 列**与 **4 列**横表 —— 3 列必须仍然 PASS、4 列必须 FAIL。
     没有这一对，⑫ 的「列数 ≤3」就可能实际是「有表即 FAIL」或「永不 FAIL」两种失效形态之一。
  ④ ★ **② 的阈值两侧探针**（2026-10-16 第 7 轮 N1 新增，见 `CRITERIA-CHANGE-R01.md`）：
     h1 里的拉丁缩写分四档逐条验 —— **已登记 ⇒ PASS**（ReAct / RAG）· **未登记 ⇒ FAIL**（Kubernetes）·
     **低于「≥3 字母」触发阈值 ⇒ 不触发**（AI）。
     没有这一组，② 的新口径仍可能退化成两种失效形态之一：「有拉丁词就一律 FAIL」（N1 的立意当场落空）
     或「有拉丁词就一律放过」（判据恒真）。

★ 与 `_selfcheck_switches.mjs` 同一性质：验证**装置自身**的脚本，⛔ 不是产物生成器。

用法：python3 _selfcheck_p35_fixtures.py
"""
import copy
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pekg_gate_probe", os.path.join(HERE, "gate_prototype.py"))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

base = G.load_ctx(with_probe=False)
ok, detail = G.check_p35(copy.deepcopy(base))
print("正向：%s | %s" % ("PASS" if ok else "FAIL", detail))
if not ok:
    sys.exit(1)

muts = G.mut_p35(copy.deepcopy(base))
print("P35 负例夹具总数 =", len(muts))
bad_all = 0
for i, m in enumerate(muts, 1):
    ok2, d2 = G.check_p35(m)
    if ok2:
        print("  夹具#%-2d 未触发（判据仍 PASS）—— 判据疑似恒真" % i)
        bad_all += 1
        continue
    print("  夹具#%-2d 已触发 | %s" % (i, str(d2)[:220]))

# ---- ③ 阈值边界探针：⑫ 的代理阈值 3（3 列 PASS / 4 列 FAIL）----
BOUNDARY = (
    ("3 列横表（应仍 PASS：阈值另一侧）",
     '<div class="kv-blocks"><table><tr><td>a</td><td>b</td><td>c</td></tr></table>'),
    ("4 列横表（应 FAIL：越界一侧）",
     '<div class="kv-blocks"><table><tr><td>a</td><td>b</td><td>c</td><td>d</td></tr></table>'),
)
print("")
print("⑫ 代理判据阈值边界探针（对象 = 组页 #sec-nodes）：")
boundary_bad = 0
for label, inject in BOUNDARY:
    c = G._sub_in_section(copy.deepcopy(base), "sec-nodes", '<div class="kv-blocks">',
                          inject, kind="group")
    ok3, d3 = G.check_p35(c)
    cols = G._table_cols(inject)
    want_pass = cols <= G.G4_TABLE_COL_MAX
    good = (ok3 == want_pass)
    if not good:
        boundary_bad += 1
    print("  %-28s 列数 %d ⇒ 判据 %s（期望 %s）%s"
          % (label, cols, "PASS" if ok3 else "FAIL", "PASS" if want_pass else "FAIL",
             "" if good else "  ← 边界不符"))
    if not ok3:
        print("       违例：%s" % str(d3)[:200])

# ---- ④ ★ 2026-10-16 第 7 轮（N1 裁决）：② 的**阈值两侧探针**（见 CRITERIA-CHANGE-R01.md）----
#   `mut_p35` 只能证明「未登记缩写 ⇒ FAIL」。若不测**另一侧**，② 仍可能是两种失效形态之一：
#     (a) 退化成「h1 有拉丁词就一律 FAIL」⇒ 已登记缩写也被误杀（N1 的立意当场落空）；
#     (b) 退化成「h1 有拉丁词就一律放过」⇒ 台账命中不了照样绿（判据恒真）。
#   ⇒ 这里逐条验：已登记 ⇒ PASS / 未登记 ⇒ FAIL / 低于 3 字母 ⇒ 不触发（沿用旧触发阈值）。
R01_BOUNDARY = (
    ("h1 含**已登记**缩写（ReAct）", "ReAct 概率采样与确定性边界", True,  "已登记 ⇒ 应 PASS"),
    ("h1 含**已登记**缩写（RAG）",   "RAG 提示模式",              True,  "已登记 ⇒ 应 PASS"),
    ("h1 含**未登记**缩写（Kubernetes）", "Kubernetes 采样与边界", False, "台账查不到 ⇒ 应 FAIL"),
    ("h1 含 2 字母拉丁词（AI）",      "AI 采样与确定性边界",       True,  "低于 ≥3 阈值 ⇒ 不触发"),
)
print("")
print("② h1 拉丁缩写口径的阈值两侧探针（对象 = 节点页 11-node-pages/pe-f-01.html 的 h1）：")
h1_bad = 0
for label, new_h1, want_pass, why in R01_BOUNDARY:
    c = G._patch_strict(copy.deepcopy(base), "11-node-pages/pe-f-01.html",
                        "<h1>概率采样与确定性边界</h1>", "<h1>%s</h1>" % new_h1)
    ok4, d4 = G.check_p35(c)
    toks = [t for t in G.LATIN_WORD.findall(new_h1) if len(G.re.findall(r"[A-Za-z]", t)) >= 3]
    good = (ok4 == want_pass)
    if not good:
        h1_bad += 1
    print("  %-34s 触发 token %-22s ⇒ 判据 %s（期望 %s）  %s%s"
          % (label, "、".join(toks) or "（无）", "PASS" if ok4 else "FAIL",
             "PASS" if want_pass else "FAIL", why, "" if good else "  ← 边界不符"))
    if not ok4:
        print("       违例：%s" % str(d4)[:200])

print("")
print("== 自检结论：%s ==（%d 条夹具全部触发；正向 PASS；⑫ 阈值边界 %d 处不符；② 阈值边界 %d 处不符）"
      % ("PASS" if (bad_all == 0 and boundary_bad == 0 and h1_bad == 0) else "FAIL",
         len(muts), boundary_bad, h1_bad))
sys.exit(0 if (bad_all == 0 and boundary_bad == 0 and h1_bad == 0) else 1)
