#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_wave1_apply.py —— 把内容波次的草稿合并进 `10-dag-data/dag.json`（**全部波次**的合并器）。

★ **文件名为历史名**：它首次用于波次 1（`_wave1_content.json`），但本件是**每一个波次**的合并器 ——
  波次 N 由 `--content <file>` 或 `--parts-dir <dir>` 指定（见用法）。⛔ 不新建第二份回源校验逻辑
  （两处同源规则 ⇒ 漂移面，本仓最贵的一类教训）。★ 契约见 `AUTHORING-SPEC.md`（R-25 的部件契约）。

## 它做四件事（缺一件即不落盘）
1. **回源校验（★ 本件的核心价值）**：每条 `evidence.quote` 按省略号拆成若干**片段**，每个片段必须能在
   `01-research/evidence/A*.json` 的已回源 `quote` 里**逐字定位**（空白归一化后比对）。
   ⇒ 这一步把「引文是不是编造的」从**不可检**变成**提交前可拦**。
   ★ 诚实边界：它挡的是「凭空写一句」；⛔ 挡不住「引文库本身被改错」（那需要回源到原始 URL）。
   ★ 2026-10-16 第 6 轮：同一断言已**搬进数据侧判据 `C58`**（`10-dag-data/_selfcheck.py`）
     —— 本件是**提交前**的闸，`C58` 是**常驻**的闸，两者同源同口径。
2. **台账注入**：`url` / `tier` 一律从 `10-dag-data/sources.json` 按 `source_id` **注入**（⛔ 不手抄），
   并断言 `source_id` 可解析、`quote ≤ 200` 字（与门控 P06 / 数据侧 C31 同口径）。
3. **结构契约**：`lab` 每条含 `kind/lang/text/expect`；`pitfalls` 非空；`content_status` 翻 `complete`。
4. **落盘 + 回读**：按 `json.dumps(ensure_ascii=False, indent=2) + "\n"` 原样序列化（与盘上格式一致），
   写完立即 `json.load` 回读并逐条断言。

用法：
    python3 _wave1_apply.py                                    # 波次 1 那三个节点的 dry-run
    python3 _wave1_apply.py --content _wave2_content.json      # 指定波次的内容文件
    python3 _wave1_apply.py --parts-dir _wave2_parts           # ★ 部件目录（R-25：子 Agent 只写部件）
    python3 _wave1_apply.py --parts-dir _wave2_parts --write
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
DAG = os.path.join(SITE, "10-dag-data", "dag.json")
SOURCES = os.path.join(SITE, "10-dag-data", "sources.json")
CONTENT = os.path.join(HERE, "_wave1_content.json")
PACKS = sorted(glob.glob(os.path.join(SITE, "..", "01-research", "evidence", "A*.json")))

ELISION = re.compile(r"\s*\.\.\.\s*|\s*…\s*")


def load_parts(parts_dir):
    """把部件目录里的 `*.json` 合并为 `{node_id: spec}`（★ R-25 的部件契约第 1 条）。

    ★ 部件形状（`AUTHORING-SPEC.md` 定义）：`{"node_id": "PE-S-01", "spec": {...}}`
      —— 每个部件**自带 node_id**（⛔ 不靠文件名推断，避免「文件名写错但内容对」的静默错配）。
    ⛔ 重复 node_id ⇒ 直接报错（fail-closed）：两个子 Agent 交了同一个节点，必须显式暴露。
    ⛔ 部件目录为空 ⇒ 报错（空集守卫）：⛔ 不静默当作「没有要合并的内容」。
    """
    if not os.path.isdir(parts_dir):
        raise SystemExit("[FAIL] 部件目录不存在：%s" % parts_dir)
    files = sorted(glob.glob(os.path.join(parts_dir, "*.json")))
    if not files:
        raise SystemExit("[FAIL] 部件目录为空（空集守卫）：%s" % parts_dir)
    out = {}
    for p in files:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            raise SystemExit("[FAIL] 部件 JSON 非法：%s（%s: %s）"
                             % (os.path.basename(p), type(e).__name__, e))
        nid = d.get("node_id")
        if not nid:
            raise SystemExit("[FAIL] 部件缺 `node_id`：%s" % os.path.basename(p))
        if nid in out:
            raise SystemExit("[FAIL] 部件 node_id 重复：%s（%s 与先前的部件冲突）"
                             % (nid, os.path.basename(p)))
        if not isinstance(d.get("spec"), dict):
            raise SystemExit("[FAIL] 部件缺 `spec`（对象）：%s" % os.path.basename(p))
        out[nid] = d["spec"]
    return out


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def load_pack_quotes():
    """{归一化后的已回源引文: [来源件名, ...]}"""
    out = {}
    for p in PACKS:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for m in d.get("metas", []):
            q = norm(m.get("quote", ""))
            if q:
                out.setdefault(q, []).append(os.path.basename(p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--content", default=None,
                    help="内容草稿文件（默认 %s）" % os.path.basename(CONTENT))
    ap.add_argument("--parts-dir", default=None,
                    help="★ 部件目录（R-25：每部件一个 json，形状 {node_id, spec}）；与 --content 互斥")
    ap.add_argument("--reapply", action="store_true",
                    help="★ 允许对**已经 complete** 的节点重放同一波次的部件（默认 ⛔ 拒绝，见下）")
    a = ap.parse_args()
    if a.content and a.parts_dir:
        raise SystemExit("[FAIL] --content 与 --parts-dir 互斥（⛔ 不接受两个真相源）")

    dag = json.load(open(DAG, encoding="utf-8"))
    nodes = {n["id"]: n for n in dag["nodes"]}
    if a.parts_dir:
        parts_dir = a.parts_dir if os.path.isabs(a.parts_dir) else os.path.join(HERE, a.parts_dir)
        content = load_parts(parts_dir)
        origin = "部件目录 %s（%d 个部件）" % (os.path.relpath(parts_dir, SITE), len(content))
    else:
        cpath = a.content or CONTENT
        cpath = cpath if os.path.isabs(cpath) else os.path.join(HERE, cpath)
        content = json.load(open(cpath, encoding="utf-8"))["nodes"]
        origin = "内容文件 %s" % os.path.relpath(cpath, SITE)
    src = {s["id"]: s for s in json.load(open(SOURCES, encoding="utf-8"))["sources"]}
    packs = load_pack_quotes()

    bad = []
    print("== _wave1_apply.py：内容波次合并（%d 个节点；来源 = %s）==" % (len(content), origin))
    print("   回源引文库：%d 个文件 / %d 条唯一引文" % (len(PACKS), len(packs)))
    print()
    for nid, spec in sorted(content.items()):
        n = nodes.get(nid)
        if n is None:
            bad.append((nid, "节点不存在"))
            continue
        if n["content_status"] != "registered":
            # ★ 2026-10-16 第 6 轮：本件原本**不是幂等**的 —— 第一次 `--write` 之后 nodes 翻成 complete，
            #   第二次跑（例如只想补合并散文）会硬 FAIL「预期 registered，实为 complete」而**中止落盘**。
            #   ⇒ 处置：默认仍**拒绝**（该断言的价值是抓「把波次 N 的件打到已被上一波发布的节点上」这类错配）；
            #     需要**重放同一波次**（补字段 / 修正内容）时显式加 `--reapply`，并在日志里标出来。
            if not a.reapply:
                bad.append((nid, "预期 registered，实为 %s（如需重放同一波次请加 --reapply）"
                            % n["content_status"]))
            else:
                print("   [%s] ★ 重放（节点已 complete；--reapply 已声明）" % nid)
        # ---- lab ----
        for i, it in enumerate(spec.get("lab", [])):
            for k in ("kind", "lang", "text", "expect"):
                if not it.get(k):
                    bad.append((nid, "lab[%d] 缺 %s" % (i, k)))
        # ---- evidence（回源 + 台账注入 + 长度）----
        evs = []
        for i, ev in enumerate(spec.get("evidence", [])):
            sid = ev.get("source_id")
            if sid not in src:
                bad.append((nid, "evidence[%d] source_id 不可解析 %s" % (i, sid)))
                continue
            q = norm(ev.get("quote", ""))
            if not q:
                bad.append((nid, "evidence[%d] quote 为空" % i))
                continue
            if len(ev.get("quote", "")) > 200:
                bad.append((nid, "evidence[%d] quote 超 200 字（%d）" % (i, len(ev["quote"]))))
            # ★ 回源：按省略号拆片段，逐片段在引文库里定位
            frags = [f for f in ELISION.split(q) if f.strip()]
            hit = []
            for f in frags:
                where = []
                for pq, pks in packs.items():
                    if f in pq:
                        where.extend(pks)
                where = sorted(set(where))
                hit.append((f[:40], where[:2]))
                if not where:
                    bad.append((nid, "evidence[%d] 片段无法回源：%s" % (i, f[:60])))
            evs.append({"claim": ev["claim"], "source_id": sid, "url": src[sid]["url"],
                        "quote": ev["quote"], "tier": src[sid]["tier"],
                        **({"quote_truncated": True} if ev.get("quote_truncated") else {})})
            print("   [%s] %-8s tier=%-9s 片段 %d/%d 回源  %s"
                  % (nid, sid, src[sid]["tier"], sum(1 for _, h in hit if h), len(hit),
                     "；".join("%s→%s" % (f[:26], ",".join(h)) for f, h in hit)))
        if not evs:
            bad.append((nid, "evidence 为空"))
        if not spec.get("pitfalls"):
            bad.append((nid, "pitfalls 为空"))
        print("   [%s] lab %d 条 / evidence %d 条 / pitfalls %d 条"
              % (nid, len(spec.get("lab", [])), len(evs), len(spec.get("pitfalls", []))))
        # ---- 应用（内存）----
        n["lab"] = spec["lab"]
        n["evidence"] = evs
        n["pitfalls"] = spec["pitfalls"]
        # ★ 2026-10-16 第 6 轮修正（波次 2 当场发现）：**散文字段也要合并**。
        #   原实现只写 lab / evidence / pitfalls / content_status ⇒ 部件里的
        #   `why` / `intro` / `boundary` / `when` / `terms` / `summary` / `tags` 被**静默丢弃**
        #   （波次 2 实测：5 个部件的这四项与盘上**全不相同** —— 作者花了力气写、产物却一字未用）。
        #   ⇒ 这是「部件契约说要 8 区块、合并器只收 3 个」的两处口径不合（R-23 同族）。
        #   ★ 兼容性：只在部件**确有该字段且非空**时覆盖 ⇒ 旧件（如波次 1 的内容文件不含散文）行为不变。
        for k in ("why", "intro", "boundary", "when", "terms", "summary", "tags"):
            if spec.get(k) not in (None, "", [], {}):
                n[k] = spec[k]
        n["content_status"] = "complete"

    print()
    if bad:
        print("== 结论：FAIL（%d 处）==" % len(bad))
        for b in bad:
            print("   ", b)
        return 1
    print("== 结论：PASS ==（回源、台账注入、长度、结构四项全过）")

    text = json.dumps(dag, ensure_ascii=False, indent=2) + "\n"
    if a.write:
        with open(DAG, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        back = json.load(open(DAG, encoding="utf-8"))
        got = {x["id"]: x for x in back["nodes"]}
        assert len(got) == len(nodes), "回读节点数不一致"
        for nid in content:
            assert got[nid]["content_status"] == "complete", nid
            assert got[nid]["evidence"] and got[nid]["lab"] and got[nid]["pitfalls"], nid
        comp = [i for i, x in got.items() if x["content_status"] == "complete"]
        print("[write] dag.json 已落盘；回读：JSON 合法 / 节点 %d / complete %d 个 %s"
              % (len(got), len(comp), sorted(comp)))
    else:
        print("[dry-run] ⛔ 未写盘（加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
