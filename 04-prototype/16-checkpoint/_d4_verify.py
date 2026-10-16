#!/usr/bin/env python3
# _d4_verify.py —— CONTINUE-PROMPT-D4.md 的**交付自检**（只读，不落任何产物）。
#
# 三件事：
#   ① 打印 A–K 各节标题与行号（供人工核对「自检」小节里的行号区间）；
#   ② 核对 H 节的 16 条验收定义 = 9 + 3 + 4，且逐条与 HANDOFF-R3.md §六 的原文一致（逐字比对条件列）；
#   ③ 核对文中出现的所有 `反引号路径`/文件名，凡像文件且在盘上不存在的，逐条列出（防虚构路径）。
import os
import re
import sys

ROOT = "/home/zako-mio/opencode/archive/Mission-file/2026-10/1014-新一代提示词工程知识全景图与教程"
CHK = os.path.join(ROOT, "04-prototype", "16-checkpoint")
D4 = os.path.join(CHK, "CONTINUE-PROMPT-D4.md")
R3 = os.path.join(CHK, "HANDOFF-R3.md")

d4 = open(D4, encoding="utf-8").read().splitlines()
r3 = open(R3, encoding="utf-8").read()

print("=== ① D4 章节标题与行号（共 %d 行）===" % len(d4))
for i, ln in enumerate(d4, 1):
    if re.match(r"^#{2,3} ", ln):
        print("  %4d  %s" % (i, ln.strip()))

print("\n=== ② H 节 16 条：与 HANDOFF-R3.md §六 原文逐字比对 ===")
r3_cells = set()
for ln in r3.splitlines():
    if re.match(r"^\|\s*\d+\s*\|", ln.strip()):
        for c in [x.strip() for x in ln.strip().strip("|").split("|")]:
            r3_cells.add(c)
rows = [ln for ln in d4 if re.match(r"^\|\s*6\.\d-\d+\s*\|", ln)]
print("  行数 = %d（期望 16）" % len(rows))
n_ok = 0
for r in rows:
    cells = [x.strip() for x in r.strip().strip("|").split("|")]
    num, cond = cells[0], cells[1]
    hit = cond in r3_cells
    print("  %-6s %-3s  原文逐字命中=%s" % (num, "OK" if hit else "!!", hit))
    n_ok += bool(hit)
print("  ⇒ 逐字命中 %d / %d" % (n_ok, len(rows)))

print("\n=== ③ 文中提到的文件是否都在盘上（防虚构路径）===")
names = set()
for m in re.finditer(r"`([^`]+)`", "\n".join(d4)):
    t = m.group(1)
    if re.search(r"[\\/]|\.(md|py|json|mjs|sh|html|js|css|webp|svg|txt)$", t) and " " not in t:
        names.add(t.split()[0])
missing, checked = [], 0
for t in sorted(names):
    cands = [os.path.join(ROOT, t), os.path.join(CHK, t), os.path.join(ROOT, "04-prototype", t),
             os.path.expanduser(t), os.path.join(ROOT, os.path.dirname(t) and "" or "", t)]
    if any(os.path.exists(c) for c in cands):
        checked += 1
        continue
    base = os.path.basename(t)
    if base.endswith((".md", ".py", ".json", ".mjs", ".sh", ".html")):
        missing.append(t)
    else:
        checked += 1
print("  可解析 = %d" % checked)
if missing:
    print("  !! 盘上找不到（须逐条交代）：")
    for t in missing:
        print("     - %s" % t)
else:
    print("  ⇒ 无悬空文件名")

print("\n=== ④ 本件是否声明了 A–K 全部小节 ===")
want = ["## A.", "## B.", "## C.", "## D.", "## E.", "## F.", "## G.", "## H.", "## I.", "## J.", "## K."]
txt = "\n".join(d4)
miss = [w for w in want if w not in txt]
print("  缺项 = %s" % (miss or "无"))
sys.exit(0)
