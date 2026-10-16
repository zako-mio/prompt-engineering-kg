#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_selfcheck_figs_spec.py —— **图件规格判据自身**的可判假性自检（⛔ 只读、⛔ 不写任何产物）。

## 为什么需要它
`gen-figs.check_spec` 是 R-08 的唯一实装，它现在有**两条**界：
  ① 渲染高度上界（≤ 600px）—— 第 5 轮首次实测出来的真实缺陷；
  ② **缩放比下界**（`804 / viewBox 宽 ≥ 0.90`）—— 2026-10-16 第 6 轮补，见 `CRITERIA-CHANGE-R07.md`。
「有阈值的判据」最典型的两种失效形态是：**恒真**（永不报错）与**过宽**（把正常图也判死）。
本件用**合成 viewBox** 把两条界的**两侧**各打一发，证明它们真的在判、且阈值位置正确：

    · 上界另一侧：矮图（宽而矮）          ⇒ 必须 **PASS**
    · 上界越界侧：高图（200×900）          ⇒ 必须 **FAIL**
    · 下界另一侧：窄图（宽 893，scale=0.900）⇒ 必须 **PASS**（边界取 `>=`）
    · 下界越界侧：宽图（1016×150，即第 5 轮 `pe-f-06` 的旧形态，scale=0.79）⇒ 必须 **FAIL**
    · 正向：磁盘上真实图件**逐件**必须 PASS（⛔ 不容忍任何一件在盘上越界）

★ 与 `_selfcheck_p35_fixtures.py` / `_figcheck.py` 同一性质：**验证装置自身**的脚本，⛔ 不是产物生成器。
★ 第 4 条那一发是**历史复现**：`pe-f-06` 在补下界之前正是 1016×150（缩到 0.79×、13pt 文字约 10px），
   靠「高度只有 150px 所以看不出来」通过了旧规格 —— 本条把它固化成不会重犯的负例。

用法：`python3 _selfcheck_figs_spec.py`（退出码 0 = 四发全部符合预期 + 盘上真实图件全部合规）
"""
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))
FIGDIR = os.path.join(SITE, "10-dag-data", "figures")

spec = importlib.util.spec_from_file_location("pekg_gen_figs_probe", os.path.join(HERE, "gen-figs.py"))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

SVG = '<svg class="fig__svg" role="img" viewBox="0 0 %g %g"></svg>'


def probe(label, w, h, expect_pass):
    """对合成 viewBox 跑 check_spec，返回是否与预期一致。"""
    try:
        G.check_spec("(合成 %s)" % label, SVG % (w, h))
        got_pass, msg = True, "PASS"
    except SystemExit as e:
        got_pass, msg = False, str(e)[:150]
    ok = (got_pass == expect_pass)
    print("[%s] %-22s %8.1fx%-7.1f 期望 %-4s 实得 %-4s %s"
          % ("OK  " if ok else "BAD ", label, w, h, "PASS" if expect_pass else "FAIL",
             "PASS" if got_pass else "FAIL", "" if got_pass else ("| " + msg)))
    return ok


print("== 图件规格判据（gen-figs.check_spec）阈值两侧自检 ==")
print("   内容列宽 %gpx / 高度上界 %gpx / 缩放比下界 %.2f"
      % (G.CONTENT_COL_PX, G.FIG_MAX_H_PX, G.MIN_SCALE))
print("")
bad = 0
# ① 两侧都在界内（宽 880 ⇒ scale 0.914；高 300 ⇒ 渲染高 274px）
#    ★ 首版这里写的是 900×300 —— 它**已在缩放比下界之下**（scale 0.893）⇒ 当场被判 FAIL。
#      那一发不是判据坏了，而是**本探针自己算错了**：两条界是**同时**生效的，
#      「矮」不等于「合规」。此处保留该教训（改对数值 + 留痕），见 `CRITERIA-CHANGE-R07.md` §L·F-2。
bad += not probe("两侧都在界内", 880, 300, True)
# ② 上界越界侧（高图：宽 200 / 高 900 ⇒ 渲染高 3618px）
bad += not probe("上界·越界(高)", 200, 900, False)
# ③ 下界另一侧（宽恰为 804/0.90 = 893.33 ⇒ scale 恰 0.90，边界取 >=）
w_edge = G.CONTENT_COL_PX / G.MIN_SCALE
bad += not probe("下界·边界(恰 0.90)", w_edge, 400, True)
# ④ 下界越界侧（★ 第 5 轮 pe-f-06 的旧 viewBox：1016×150 ⇒ scale 0.79）
bad += not probe("下界·越界(旧 pe-f-06)", 1016, 150, False)

# ⑤ 盘上真实图件逐件合规（⛔ 空集守卫：一张都读不到就说明路径错了，必须显式 FAIL）
svgs = sorted(f for f in os.listdir(FIGDIR) if f.endswith(".svg"))
if not svgs:
    print("[BAD ] 盘上真实图件：%s 下 0 张 svg（空集守卫）" % os.path.relpath(FIGDIR, SITE))
    bad += 1
else:
    printed = 0
    for fn in svgs:
        svg = open(os.path.join(FIGDIR, fn), encoding="utf-8").read()
        try:
            G.check_spec(fn[:-4], svg)
        except SystemExit as e:
            print("[BAD ] 盘上真实图件 %-16s 越界：%s" % (fn, str(e)[:130]))
            bad += 1
            continue
        printed += 1
    print("[OK  ] 盘上真实图件 %d 张全部合规（逐一复算，⛔ 不抽样）" % printed)

print("")
print("== 结论：%s ==（四发合成探针 + 盘上 %d 张真实图件；不符 %d 处）"
      % ("PASS" if bad == 0 else "FAIL", len(svgs), bad))
sys.exit(0 if bad == 0 else 1)
