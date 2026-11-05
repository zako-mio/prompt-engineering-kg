#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_manifest.py —— `_probe/` 过程证据目录的**台账生成器 + 单一扫描口径**（2026-11-05 第 13 轮，`K3`）。

## 为什么需要它

`_probe/` 是取证件与核对台的存放地（`_probe/README.md` 第 7 轮新建了目录级说明）。
但它按 `.gitignore` 规则②**整层不入库**，且**没有任何判据管辖**（台账 `K3` / `G18` ⑯）：
每轮都会新增十几件，删改与替换不留痕，`README` 里的五类寿命表只能靠人读。

本文件把「哪一件存在、属于哪一类、属于哪一轮、内容指纹是什么」变成一份可机检的台账
`_probe/MANIFEST.json`，并**只定义一次扫描口径**（`scan()` / `classify()` / `round_of()`）：
`gate_prototype.py` 的 `P47` ⛔ 不另写一份扫描规则 —— 两处各写一份必然漂移。

## 口径（★ 判据只断「结构闭合 + 指纹一致」，⛔ 不断言分类语义正确）

- **分类**由**命名约定**机器推断（`CLASS_ENUM` 六类），⛔ 不是人工裁定；语义是否正确靠人读。
- **轮次**取路径/文件名里的 `r<N>_` 前缀；取不到的记为 `legacy`（历史件，建目录之前的产物）。
- **可删性**：默认 `false`；只有 `render`（渲染件）为 `true` —— 照 `_probe/README.md` §一 的寿命列：
  渲染件可替换，但须在台账写明「哪一轮的取证已被新一轮替换」；其余一律不可删。
- **排除**：台账自身、解释器缓存、系统垃圾（`.DS_Store`）不登记 —— 它们是产物而非证据。

## 用法

    python3 _probe_manifest.py --check     # 只比对（打印漂移；退出码 1 = 有漂移）
    python3 _probe_manifest.py --write     # 重新生成台账（每轮收口跑一次）
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_DIR = os.path.join(HERE, "_probe")
MANIFEST_NAME = "MANIFEST.json"
MANIFEST_PATH = os.path.join(PROBE_DIR, MANIFEST_NAME)

#: 六类对象（来源：`_probe/README.md` §一 的五类寿命表；`doc` 为目录级说明本身）
CLASS_ENUM = ("manifest", "render", "bench", "evidence", "tool", "doc", "other")
#: 不进台账的目录 / 文件（产物而非证据）
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_FILES = {MANIFEST_NAME, ".DS_Store"}

ROUND_RE = re.compile(r"^r(\d+)_")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

SCHEMA_NOTE = ("过程证据台账：每条 = 相对路径 / 类 / 轮次 / 字节 / sha256 / 可否删除。"
               "★ 由 `_probe_manifest.py` 生成；判据 `P47` 断「清单 ⟺ 磁盘」双向闭合与逐件指纹一致。"
               "⛔ 本台账不是站点产物、不参与发布；`_probe/` 按 .gitignore 规则②整层不入库。")


def classify(rel):
    """按命名约定推断类（⛔ 不做内容分析：判据不断言语义，语义靠人读）。"""
    base = rel.rsplit("/", 1)[-1]
    top = rel.split("/")[0] if "/" in rel else ""
    if top == "false-green":
        return "evidence"
    if base in ("channel.json", "env.json"):
        return "manifest"
    if base.endswith(".png"):
        return "render"
    if base.startswith(("fig2-", "fig3-")):
        return "bench"
    if base.endswith(".py"):
        return "tool"
    if base == "README.md":
        return "doc"
    if base.endswith(".txt"):
        return "evidence"
    return "other"


def round_of(rel):
    """取第一个 `r<N>_` 前缀；取不到 = legacy。"""
    for part in rel.split("/"):
        m = ROUND_RE.match(part)
        if m:
            return "r%s" % m.group(1)
    return "legacy"


def scan(probe_dir=PROBE_DIR):
    """扫磁盘：{相对路径: {bytes, sha256}}（⛔ 不含台账自身与缓存）。"""
    files = {}
    if not os.path.isdir(probe_dir):
        return files
    for dirpath, dirnames, filenames in os.walk(probe_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fn in sorted(filenames):
            if fn in EXCLUDE_FILES:
                continue
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, probe_dir).replace(os.sep, "/")
            with open(ap, "rb") as f:
                data = f.read()
            files[rel] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return files


def build(probe_dir=PROBE_DIR):
    """生成台账对象（entries 按路径排序；counts 按类计）。"""
    files = scan(probe_dir)
    entries = []
    for rel in sorted(files):
        cls = classify(rel)
        entries.append({
            "path": rel,
            "class": cls,
            "round": round_of(rel),
            "bytes": files[rel]["bytes"],
            "sha256": files[rel]["sha256"],
            "deletable": cls == "render",
        })
    counts = {}
    for e in entries:
        counts[e["class"]] = counts.get(e["class"], 0) + 1
    return {
        "schema": "probe-evidence-manifest/1",
        "schema_note": SCHEMA_NOTE,
        "generated_by": "16-checkpoint/_probe_manifest.py（2026-11-05 第 13 轮，台账 `K3`）",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "probe_dir": "16-checkpoint/_probe",
        "count": len(entries),
        "counts": counts,
        "entries": entries,
    }


def snapshot(probe_dir=PROBE_DIR):
    """给判据用的快照：{manifest, manifest_error, files}（⛔ 失败不抛，交由判据判）。"""
    snap = {"manifest": None, "manifest_error": None, "files": scan(probe_dir)}
    if not os.path.isdir(probe_dir):
        snap["manifest_error"] = "_probe/ 不存在"
        return snap
    try:
        with open(os.path.join(probe_dir, MANIFEST_NAME), encoding="utf-8") as f:
            snap["manifest"] = json.load(f)
    except FileNotFoundError:
        snap["manifest_error"] = "MANIFEST.json 不存在"
    except Exception as e:                    # noqa: BLE001 —— 坏 JSON 也要成为可判假的观测
        snap["manifest_error"] = "%s: %s" % (type(e).__name__, e)
    return snap


def drift(probe_dir=PROBE_DIR):
    """人读用的漂移报告（P47 是机检版；这里给 --check）。"""
    snap = snapshot(probe_dir)
    if snap["manifest"] is None:
        return {"error": snap["manifest_error"], "missing": [], "orphan": [], "fingerprint": []}
    man = {e.get("path"): e for e in snap["manifest"].get("entries", [])}
    disk = snap["files"]
    missing = sorted(set(man) - set(disk))
    orphan = sorted(set(disk) - set(man))
    fp = sorted(p for p in set(man) & set(disk)
                if man[p].get("sha256") != disk[p]["sha256"] or man[p].get("bytes") != disk[p]["bytes"])
    return {"error": None, "missing": missing, "orphan": orphan, "fingerprint": fp}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="重新生成 MANIFEST.json")
    g.add_argument("--check", action="store_true", help="只比对，不写盘")
    a = ap.parse_args()

    if a.write:
        doc = build()
        if not doc["entries"]:
            print("== 结论：FAIL ==（`_probe/` 扫不到任何文件 ⇒ ⛔ 不写空台账）")
            return 1
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已写 %s：%d 件（%s）" % (
            os.path.relpath(MANIFEST_PATH, HERE), doc["count"],
            " / ".join("%s %d" % (k, v) for k, v in sorted(doc["counts"].items()))))
        return 0

    d = drift()
    if d["error"]:
        print("== 结论：FAIL ==（%s；先跑 `--write` 建台账）" % d["error"])
        return 1
    n = len(snapshot()["files"])
    bad = len(d["missing"]) + len(d["orphan"]) + len(d["fingerprint"])
    print("清单 ⟺ 磁盘：磁盘 %d 件；清单有磁盘无 %d / 磁盘有清单无 %d / 指纹不符 %d"
          % (n, len(d["missing"]), len(d["orphan"]), len(d["fingerprint"])))
    for label in ("missing", "orphan", "fingerprint"):
        for p in d[label][:10]:
            print("  [%s] %s" % (label, p))
    print("== 结论：%s ==" % ("PASS" if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
