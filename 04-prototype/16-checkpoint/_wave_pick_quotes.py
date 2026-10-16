#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_wave_pick_quotes.py —— **引文选料器**：按关键词列出「可用作 evidence」的已回源引文（⛔ 只读）。

## 它在链条里的位置（★ R-25 的三件套之一）
内容生产是「**子 Agent 并行产出部件 → 机器校验 → 主 Agent 独立复跑**」。其中最易出错、最耗人的一步是
「找一条**能逐字回源**的引文」：作者必须从 `01-research/evidence/A*.json` 的 `metas[].quote` 里
**逐字复制**，且该条必须能在 `10-dag-data/sources.json` 里按 **URL** 映射到一个 `source_id`（S-XXXX）
—— 否则 `_wave1_apply.py` 的台账注入与数据侧 `C58` 都会拦下。
本件把这三件事（关键词检索 / URL→S-id 映射 / 台账字段一并打印）一次做完，
⇒ 子 Agent 只需**复制粘贴**，⛔ 不需要自己拼 URL 或猜 S-id。

## 用法
    python3 _wave_pick_quotes.py 结构化输出 json_schema        # 多关键词 = OR
    python3 _wave_pick_quotes.py --tier official 约束解码
    python3 _wave_pick_quotes.py --full 校验                   # 打印完整引文（默认截 140 字）

## ⛔ 它不做什么
* ⛔ 不改任何文件、⛔ 不生成 evidence、⛔ 不判断「哪条引文更贴题」（那是内容判断）。
* ⛔ 不替代 `_wave1_apply.py` / `C58` 的**逐字回源校验**：本件只按**关键词**粗筛，
  真正的判定是「quote 的每一片段逐字出现在某条 metas[].quote 里」。
* 打印 `S-id = ——` 的行**不可用作 evidence**（该 URL 不在引用台账内 ⇒ 无 `source_id` 可注入）。
"""
import argparse
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))
PACKS = sorted(glob.glob(os.path.join(SITE, "..", "01-research", "evidence", "A*.json")))
SOURCES = os.path.join(SITE, "10-dag-data", "sources.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="+", help="关键词（多个 = OR，大小写不敏感）")
    ap.add_argument("--tier", default=None, help="只列某档（official / academic / toolchain / tutorial …）")
    ap.add_argument("--full", action="store_true", help="打印完整引文")
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()

    src = json.load(open(SOURCES, encoding="utf-8"))["sources"]
    byurl = {}
    for s in src:
        byurl.setdefault(s["url"], s["id"])
    pat = re.compile("|".join(re.escape(k) for k in a.keywords), re.I)
    rows, n_usable = [], 0
    for p in PACKS:
        d = json.load(open(p, encoding="utf-8"))
        for m in d.get("metas", []):
            q = (m.get("quote") or "").strip()
            if not q:
                continue
            blob = json.dumps(m, ensure_ascii=False)
            if not pat.search(blob):
                continue
            if a.tier and m.get("tier") != a.tier:
                continue
            sid = byurl.get(m.get("url"))
            if sid:
                n_usable += 1
            rows.append((m.get("id") or "-", sid, m.get("tier") or "-", m.get("date") or "-",
                         os.path.basename(p), m.get("source") or "", q))
    if not rows:
        print("[空集] 关键词 %s 在 %d 个引文库文件里没有命中" % (a.keywords, len(PACKS)))
        return 1
    print("== 引文选料：关键词 %s ⇒ 命中 %d 条（其中**可注入 source_id** 的 %d 条）=="
          % (a.keywords, len(rows), n_usable))
    print("   ⛔ `S-id = ——` 的行不可用作 evidence（URL 不在 sources.json 台账内）")
    print("")
    for mid, sid, tier, date, pack, source, q in rows[:a.limit]:
        print("[%s] S-id=%-7s tier=%-10s %s  <%s>" % (mid, sid or "——", tier, date, pack))
        print("    来源：%s" % source[:90])
        print("    引文：%s" % (q if a.full else (q[:140] + ("…" if len(q) > 140 else ""))))
    if len(rows) > a.limit:
        print("…（还有 %d 条，用 --limit 调整；本件只粗筛，⛔ 不是判据）" % (len(rows) - a.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
