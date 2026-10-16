#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_b1_emit_review.py —— 生成 B-1「67 条 boundary 改判」的**留档表**（⛔ 不改任何数据、⛔ 不是判据）。

## 它在链条里的位置
`_b1_prefill_boundary.py` 做**机械预填**（与渲染同源的显式标记切分）；**人工读校**的结论由本件落成
`16-checkpoint/_b1_boundary_review.md`，作为 `CRITERIA-CHANGE-P05-R5.md` §1/§3 的可核证据。

## ⛔ 诚实边界
本件**只把现态数据摆成表**（字段长度、是否为空、是否与正文重复、是否残留引导串）。
「这句到底是不是一条合格的适用性限定」**不可机检**，由人读该表逐条核 —— ⛔ 不得把本表当内容评审结论。

用法：
    python3 _b1_emit_review.py            # 打印到 stdout
    python3 _b1_emit_review.py --write    # 写 16-checkpoint/_b1_boundary_review.md
"""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DAG = os.path.normpath(os.path.join(HERE, "..", "10-dag-data", "dag.json"))
OUT = os.path.join(HERE, "_b1_boundary_review.md")

CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-'.]*")
SENT_END = "。！？!?"
BM = re.compile(r"适用边界是|适用边界必须写清")
# ★ 9 个「why + intro 双标记」节点（改判时统一保留 why 版、移除 intro 版）——见登记件 §3 C2
DUAL = ("PE-R-02", "PE-R-03", "PE-R-07", "PE-C-01", "PE-A-01", "PE-P-02", "PE-P-06", "PE-N-01", "PE-N-03")
INTRO_MIN = {"complete": 150, "registered": 120}
WHY_MIN = {"complete": 80, "registered": 60}


def caliber(s):
    return len(CJK.findall(s or "")) + len(LATIN_WORD.findall(s or ""))


def rows(nodes):
    out = []
    for n in nodes:
        bd = (n.get("boundary") or "").strip()
        flags = []
        if not bd:
            flags.append("空")
        if BM.search(n.get("why", "")) or BM.search(n.get("intro", "")):
            flags.append("正文残留引导串")
        if bd and any(x.strip() == bd for x in re.split(r"(?<=[。！？!?])", n.get("why", ""))):
            flags.append("与 why 整句重复")
        if n["id"] in DUAL:
            flags.append("双标记：保留 why 版、移除 intro 版")
        out.append((n["id"], n["content_status"], caliber(bd), caliber(n.get("why", "")),
                    caliber(n.get("intro", "")), "；".join(flags)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    doc = json.load(open(DAG, encoding="utf-8"))
    nodes = doc["nodes"]
    rs = rows(nodes)
    lines = []
    lines.append("# B-1 改判表：67 条 `boundary` 字段化（★ 人读；⛔ 不可机检的内容判断）")
    lines.append("")
    lines.append("> 生成件：`16-checkpoint/_b1_emit_review.py`（只读 `dag.json` 摆表，⛔ 不改数据）")
    lines.append("> 上游：`CRITERIA-CHANGE-P05.md` §3 C3（`boundary` 由可选转必填）· `CONTINUE-PROMPT-D4.md` §B-1")
    lines.append("> 登记：`CRITERIA-CHANGE-P05-R5.md`")
    lines.append("")
    lines.append("## 改判纪律（逐条核的就是这三条）")
    lines.append("")
    lines.append("1. **切分口径与渲染同源**：`gen-common.split_boundary` 的**显式标记**查找"
                 "（`适用边界是`；`PE-R-02` 用变体 `适用边界必须写清：`）。⛔ 不新写关键词正则 —— "
                 "实测 `…而是边界：` 是**主题词**会被误捕（`PE-F-03`），而真正的边界句反而漏捕。")
    lines.append("2. **双标记节点的合并规则**：9 个节点在 `why` 与 `intro` 两处各写了一遍边界，"
                 "两版**近乎重复**。统一**保留 `why` 版、移除 `intro` 版** —— 理由：逐条比对后 "
                 "`why` 版一致地更完整（`PE-R-02` 两版逐字相同，属纯去重）。⛔ 该规则是**可复核的取舍**，"
                 "不是唯一正确解；如有异议按下表逐条改。")
    lines.append("3. **两条 `complete` 节点的 intro 补写**：移除 intro 版边界后，`PE-R-02` 的 intro 主体降到 "
                 "122、`PE-P-02` 降到 143，**跌破 `complete` 的 intro 下限 150** ⇒ 按「⛔ 不降下限」的纪律，"
                 "改为**补写机制句**（分别 +82 / +50 caliber，内容 += 判据的落地方式 / 两条原则的对冲关系），"
                 "改写后为 204 / 193。")
    lines.append("")
    lines.append("## 表（%d 行；caliber 口径 = 汉字数 + 拉丁词数）" % len(rs))
    lines.append("")
    lines.append("| 节点 | 状态 | boundary | why 主体 | intro 主体 | 备注（人核） |")
    lines.append("|---|---|---:|---:|---:|---|")
    for r in rs:
        lines.append("| `%s` | %s | %d | %d | %d | %s |" % (r[0], r[1], r[2], r[3], r[4], r[5] or "—"))
    lines.append("")
    lines.append("## 统计")
    lines.append("")
    lines.append("- 行数：%d" % len(rs))
    lines.append("- `boundary` 为空的：%d" % len([r for r in rs if r[2] == 0]))
    lines.append("- 正文残留引导串的：%d" % len([r for r in rs if "残留" in r[5]]))
    lines.append("- boundary caliber 区间：%d – %d" % (min(r[2] for r in rs), max(r[2] for r in rs)))
    lines.append("- `why` 主体 caliber 区间：%d – %d（下限：complete 80 / registered 60）"
                 % (min(r[3] for r in rs), max(r[3] for r in rs)))
    lines.append("- `intro` 主体 caliber 区间：%d – %d（下限：complete 150 / registered 120）"
                 % (min(r[4] for r in rs), max(r[4] for r in rs)))
    lines.append("- 跌破各自下限的：%d（由 `gate_prototype.py` P05 与 `10-dag-data/_selfcheck.py` C28c 逐条机检）"
                 % len([r for r in rs
                        if r[3] < (80 if r[1] == "complete" else 60)
                        or r[4] < (150 if r[1] == "complete" else 120)]))
    lines.append("")
    text = "\n".join(lines) + "\n"
    if a.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        back = open(OUT, encoding="utf-8").read()
        print("[write] %s（%d 字节；回读行数 %d）" % (os.path.relpath(OUT, HERE), len(back.encode("utf-8")),
                                                  len(back.splitlines())))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
