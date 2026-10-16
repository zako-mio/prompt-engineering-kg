#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_b1_prefill_boundary.py —— B-1「`boundary` 字段化」的**预填 + 改判表**助手（⛔ 不是判据、⛔ 不做内容裁决）。

## 为什么需要它
`boundary` 由「渲染期从句切出」升为「一等数据字段」（`CRITERIA-CHANGE-P05.md` §3 C3 的 C3 项，
本轮 `CONTINUE-PROMPT-D4.md` §B-1 执行）。切分口径**必须与渲染同源**——即 `gen-common.split_boundary`
的**显式标记查找**，⛔ 不得另写关键词正则：实测反例是 `…而是边界：`（**主题词**）被正则误捕，
而真正的边界句反而漏捕（`CRITERIA-CHANGE-P05.md` §3）。

## 它做什么 / ⛔ 不做什么
* 做：按**显式标记**把 `why`（以及 `intro`）切成「主体 + 边界从句」，把边界从句搬到 `boundary` 字段，
  并打印 **67 行改判表**（所用标记 / 边界 caliber / 主体 caliber / 是否双标记 / 主体是否跌破下限）；
* ⛔ 不做：**不判断**「切出来的这句到底是不是适用性限定」——那是内容判断，由人逐条核（B-1 的 67 条改判）。
  标记缺失、或切出形态可疑（边界句不以句末标点收尾 / 主体跌破下限 / 双标记两版不一致）的节点
  一律进 `NEEDS_MANUAL`，由人改写后再落盘。

## 用法
    python3 _b1_prefill_boundary.py            # dry-run：只打印（⛔ 不写盘）
    python3 _b1_prefill_boundary.py --write    # 落盘 dag.json（序列化口径 = json.dumps(indent=2, ensure_ascii=False) + "\n"）
    python3 _b1_prefill_boundary.py --json     # 附机器可读改判表（供人工结论回填）

★ 本件与 `gate_prototype.py` / `_probe_*.py` 同类：**只读真相源 + 只打印**；`--write` 是唯一的写入口，
  且写前后各自复算一次（幂等校验在第 2 步之后由 `build-all.py --dry-run` 与门控独立复核）。
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

# ★ 显式标记（⛔ 关键词猜测）：按**最长优先**试探，取**最早出现**者为切点。
#   `适用边界必须写清：` 是 `PE-R-02` 实际使用的变体（本轮实测：67 个节点里唯一不用标准串的那个）。
MARKERS = ("适用边界必须写清：", "适用边界必须写清", "适用边界是")
LEAD_STRIP = "—－-：: \u3000\t "
CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-'.]*")
SENT_END = "。！？!?"

# 与 `gate_prototype.py` 的 WHY_MIN 同值（⛔ 不另立一套阈值）
WHY_MIN = {"complete": 80, "registered": 60}


def caliber(s):
    """唯一口径（SCHEMA §3）：汉字数 + 拉丁词数。"""
    return len(CJK.findall(s or "")) + len(LATIN_WORD.findall(s or ""))


def find_marker(text):
    """返回 (切点下标, 命中的标记串)；无命中返回 (-1, None)。取**最早出现**者。"""
    best = (-1, None)
    for mk in MARKERS:
        i = (text or "").find(mk)
        if i >= 0 and (best[0] < 0 or i < best[0]):
            best = (i, mk)
    return best


def split_at(text, mark):
    """与 `gen-common.split_boundary` 同口径：head = 标记前，tail = 标记后并剥掉引导标点。"""
    i = text.find(mark)
    head = text[:i].strip()
    tail = text[i + len(mark):].lstrip(LEAD_STRIP).strip()
    return head, tail


def plan_node(n):
    """算出单个节点的 {boundary 取值 + why/intro 主体 + 可疑标记}。⛔ 不写盘。"""
    why, intro = n.get("why", ""), n.get("intro", "")
    wi, wmk = find_marker(why)
    ii, imk = find_marker(intro)
    rec = {"id": n["id"], "status": n["content_status"],
           "why_marker": wmk, "intro_marker": imk,
           "why_head": None, "why_tail": None, "intro_head": None, "intro_tail": None,
           "boundary": None, "boundary_src": None, "flags": []}
    if wi >= 0:
        rec["why_head"], rec["why_tail"] = split_at(why, wmk)
    if ii >= 0:
        rec["intro_head"], rec["intro_tail"] = split_at(intro, imk)
    # boundary 取值优先级：why 从句（主陈述）> intro 从句
    if rec["why_tail"]:
        rec["boundary"], rec["boundary_src"] = rec["why_tail"], "why"
    elif rec["intro_tail"]:
        rec["boundary"], rec["boundary_src"] = rec["intro_tail"], "intro"
    # ---- 可疑标记（进 NEEDS_MANUAL 的理由；⛔ 不是判据，只是待人工看的面）
    if not rec["boundary"]:
        rec["flags"].append("无显式标记 ⇒ 须人工撰写边界")
    else:
        if rec["boundary"][-1] not in SENT_END:
            rec["flags"].append("边界句不以句末标点收尾")
    if rec["why_head"] is not None:
        if caliber(rec["why_head"]) < WHY_MIN.get(n["content_status"], 60):
            rec["flags"].append("why 主体跌破下限 %d" % WHY_MIN.get(n["content_status"], 60))
    if rec["why_tail"] and rec["intro_tail"] and rec["why_tail"] != rec["intro_tail"]:
        rec["flags"].append("双标记且两版文字不一致 ⇒ 须人工择一并合并")
    return rec


def apply_rec(n, rec):
    """把改判结果写回节点 dict（⛔ 只在 --write 路径调用）。"""
    if rec["boundary"]:
        n["boundary"] = rec["boundary"]
    if rec["why_head"] is not None:
        n["why"] = rec["why_head"]
    if rec["intro_head"] is not None:
        n["intro"] = rec["intro_head"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="落盘 dag.json（默认只打印）")
    ap.add_argument("--json", action="store_true", help="附机器可读改判表")
    a = ap.parse_args()

    doc = json.load(open(DAG, encoding="utf-8"))
    nodes = doc["nodes"]
    recs = [plan_node(n) for n in nodes]

    manual = [r for r in recs if r["flags"]]
    print("== _b1_prefill_boundary.py：B-1 预填改判表（%d 个节点）==" % len(nodes))
    print("-- 逐条改判表（★ 结论由人核；列 = 节点 / 状态 / 标记 / 边界来源 / 边界 caliber / why 主体 caliber）--")
    for r in recs:
        bc = caliber(r["boundary"]) if r["boundary"] else 0
        hc = caliber(r["why_head"]) if r["why_head"] is not None else caliber(
            next(x["why"] for x in nodes if x["id"] == r["id"]))
        mk = r["why_marker"] or ("intro:" + str(r["intro_marker"]) if r["intro_marker"] else "NONE")
        print("   %-8s %-11s %-14s src=%-6s boundary=%-4d why主体=%-4d %s"
              % (r["id"], r["status"], mk, str(r["boundary_src"]), bc, hc,
                 ("；".join(r["flags"]) if r["flags"] else "")))
    print()
    print("-- 统计 --")
    print("   有显式标记并切出边界：%d / %d" % (len([r for r in recs if r["boundary"]]), len(recs)))
    print("   仅 why 有标记：%d；仅 intro 有标记：%d；两处都有标记：%d"
          % (len([r for r in recs if r["why_marker"] and not r["intro_marker"]]),
             len([r for r in recs if r["intro_marker"] and not r["why_marker"]]),
             len([r for r in recs if r["why_marker"] and r["intro_marker"]])))
    print("   NEEDS_MANUAL（须人工看/改写）：%d 个" % len(manual))
    for r in manual:
        print("      %-8s %s" % (r["id"], "；".join(r["flags"])))

    if a.json:
        print()
        print("== JSON（改判表）==")
        print(json.dumps(recs, ensure_ascii=False, indent=1))

    if a.write:
        for n, r in zip(nodes, recs):
            apply_rec(n, r)
        text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        old = open(DAG, encoding="utf-8").read()
        if text == old:
            print("\n[write] 无变化（已是最新）")
        else:
            with open(DAG, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            back = json.load(open(DAG, encoding="utf-8"))
            assert len(back["nodes"]) == len(nodes), "回读节点数不一致"
            got = sum(1 for x in back["nodes"] if x.get("boundary"))
            print("\n[write] dag.json 已落盘；回读校验：JSON 合法、节点 %d 个、含 boundary 的 %d 个"
                  % (len(back["nodes"]), got))
    else:
        print("\n[dry-run] ⛔ 未写盘（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
