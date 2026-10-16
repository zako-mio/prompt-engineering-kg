#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_figcheck.py —— 图件**人工核对台**生成器（⛔ 只读产物、⛔ 不是判据、⛔ 不写站点产物）。

## 为什么需要它（第 5 轮实测教训，务必遵守）
图件的色值是 `var(--…)`（P36 ③ 要求令牌化、随主题）。⇒ **把单张 `<svg>` 从页面里抠出来裸看，
必然退化成「纯黑盒子 + 黑底黑字看不见」**——第 5 轮第一次自建核对页时正是这样，一度误判「图坏了」。
正确做法：把真实页面的 `<style>` 块（含 `GENERATED:tokens` 区）一起内联，让 `var(--…)` 有值。

## 它做什么
从任一**真实产物页**取 ① 站点 `<style>` 块 ② 目标图件的 `<figure class="fig" id="fig-<fid>">`，
合成一个最小核对页 `_probe/fig3-<fid>.html`（浅色档）。再用 `_render.py` 截成 PNG 供人/主 Agent 看。

## 用法
    python3 _figcheck.py --list                 # 列出产物里所有图件 id 及其所在页
    python3 _figcheck.py grp-g00 grp-g01 …      # 生成核对页
    python3 _figcheck.py --all                  # 为全部图件生成核对页

★ 与 `_selfcheck_p35_fixtures.py` / `_selfcheck_switches.mjs` 同一性质：**验证装置自身**的脚本。
"""
import argparse
import os
import re
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "_probe")
STYLE_SRC = os.path.join(SITE, "12-groups", "g00.html")   # 全站同一样式块（P15 断言模板标识唯一）
FIG_RE = re.compile(r'<figure class="fig" id="fig-([^"]+)".*?</figure>', re.S)
STYLE_RE = re.compile(r"<style>.*?</style>", re.S)

RIG = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<title>FIGCHECK %(fid)s</title>
%(style)s
</head>
<body>
<div class="layout"><main>
<section id="sec-fig"><h2 id="sec-fig"><span class="sec-no">01</span>%(fid)s</h2>
%(figure)s
</main></div>
</body>
</html>
"""


def collect():
    """{fid: figure_html}（扫全部产物页；repeat 出现的以第一次为准）。"""
    out = {}
    for sub in ("12-groups", "11-node-pages", "14-views", ""):
        d = os.path.join(SITE, sub) if sub else SITE
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".html"):
                continue
            p = os.path.join(d, fn)
            for m in FIG_RE.finditer(open(p, encoding="utf-8").read()):
                out.setdefault(m.group(1), (m.group(0), os.path.relpath(p, SITE)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    figs = collect()
    if not figs:
        print("[FAIL] 全站产物里找不到任何 `<figure class=\"fig\" id=\"fig-…\">`（空集守卫）")
        return 1
    if a.list:
        for fid, (_h, rel) in sorted(figs.items()):
            print("%-12s %s" % (fid, rel))
        print("共 %d 张图件" % len(figs))
        return 0

    style = STYLE_RE.search(open(STYLE_SRC, encoding="utf-8").read()).group(0)
    want = sorted(figs) if (a.all or not a.fids) else a.fids
    missing = [f for f in want if f not in figs]
    if missing:
        print("[FAIL] 产物里没有这些图件：%s（⛔ 不静默跳过）" % missing)
        return 1
    os.makedirs(OUT, exist_ok=True)
    for fid in want:
        html = RIG % dict(fid=fid, style=style, figure=figs[fid][0])
        p = os.path.join(OUT, "fig3-%s.html" % fid)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("[OK] %s（%d B；图件源页 %s）" % (os.path.relpath(p, SITE), len(html.encode()),
                                               figs[fid][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
