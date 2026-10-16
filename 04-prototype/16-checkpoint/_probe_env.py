#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_env.py —— 环境能力探测（**开工第一步必跑**；⛔ 不是判据，不写站点产物）。

为什么必须是一个脚本而不是一段散文（本轮最贵的一条教训，见 `report.md §6.5.5`）：
  `VERIFY-CONSTRAINT.md` 原件把「本会话内无法进行任何浏览器截图验证」写成了**已确立的事实**，
  真因却是一个**被误诊的根因**（`CapEff=0000000000000000` + `NoNewPrivs=1` 使 file-capability
  程序 `snap-confine` 取不到 `cap_dac_override`，失败在**启动层**，早于创建 `XDG_RUNTIME_DIR`），
  而**可用的非 snap 内核一直在盘上**（`~/.cache/ms-playwright/chromium-1243/`）。
  ⇒ 「环境能力不可用」这个结论**本身也要复核**，且复核必须是**可复跑的动作**，不是一段结论文字。

本件做四件事（全部只读）：
  A. **枚举候选通道**（非 snap 内核逐个 stat；snap 内核；node 驱动提示）⇒ 逐条给「存在/不存在」。
  B. **驱动可用性**（playwright python 是否可 import；版本）。
  C. **进程能力集**（`/proc/self/status` 的 CapEff/CapPrm/CapBnd/NoNewPrivs）⇒ 解释 snap 通道
     为何结构性不可用（⛔ 不是「目录只读」那类兜底文案）。
  D. **负对照**：直接调 snap 通道一次，把**原始报错逐字**留下（证明「失败文案 ≠ 失败现场」）。

用法：python3 _probe_env.py [--json]
退出码：0 = 至少存在一条**不同源**的可用通道；1 = 全部候选都不可用
        （⇒ 本轮必须**停下并如实登记为局限**，⛔ 不得静默降级、⛔ 不得沿用上一轮的结论）。
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "_probe", "env.json")


def find_chromiums():
    """枚举非 snap 的 Chromium 内核（playwright 自带缓存；⛔ 不依赖任何包管理器）。"""
    home = os.path.expanduser("~")
    found = []
    roots = [
        os.path.join(home, ".cache", "ms-playwright"),
        os.path.join(home, ".cache", "puppeteer"),
        os.path.join(home, ".local", "share", "chromium"),
    ]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn in ("chrome", "headless_shell", "chromium"):
                    p = os.path.join(dirpath, fn)
                    if os.access(p, os.X_OK) and os.path.isfile(p):
                        found.append(p)
            if dirpath.count(os.sep) - root.count(os.sep) > 3:
                dirnames[:] = []
    return sorted(set(found))


def caps():
    out = {}
    try:
        for line in open("/proc/self/status", encoding="utf-8"):
            k = line.split(":")[0]
            if k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp"):
                out[k] = line.split(":", 1)[1].strip()
    except OSError as exc:
        out["error"] = str(exc)
    return out


def snap_negative_control():
    """负对照：直接调 snap 通道，留**原始报错**（⛔ 不改环境、⛔ 不重试多次）。"""
    rows = []
    for cmd in (["/snap/bin/chromium", "--version"],
                ["/usr/bin/chromium-browser", "--headless", "--disable-gpu",
                 "--no-sandbox", "--screenshot=/tmp/_probe_env.png", "about:blank"]):
        if not os.path.isfile(cmd[0]):
            rows.append({"cmd": cmd[0], "rc": None, "lines": ["（该路径不存在）"]})
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            txt = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
            rows.append({"cmd": " ".join(cmd[:2]), "rc": r.returncode, "lines": txt[:5]})
        except Exception as exc:  # noqa: BLE001
            rows.append({"cmd": " ".join(cmd[:2]), "rc": None,
                         "lines": ["EXC %s: %s" % (type(exc).__name__, exc)]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    chromes = find_chromiums()
    drv_ok, drv_ver, drv_path = False, None, None
    try:
        spec = importlib.util.find_spec("playwright")
        drv_ok = spec is not None
        drv_path = spec.origin if spec else None
        if drv_ok:
            import playwright  # noqa: F401
            drv_ver = getattr(playwright, "__version__", None)
            if drv_ver is None:
                from importlib.metadata import version as _v
                drv_ver = _v("playwright")
    except Exception as exc:  # noqa: BLE001
        drv_ok = False
        drv_ver = "import 失败：%s" % exc
    snap = os.path.isfile("/snap/bin/chromium")
    c = caps()
    neg = snap_negative_control()
    usable = bool(chromes) and drv_ok
    doc = {"probe": "env", "site_root": SITE_ROOT,
           "non_snap_chromium": {"found": bool(chromes), "candidates": chromes},
           "snap_chromium": {"found": snap, "path": "/snap/bin/chromium" if snap else None},
           "playwright_python": {"found": drv_ok, "version": drv_ver, "path": drv_path},
           "caps": c, "snap_negative_control": neg,
           "verdict": "PASS" if usable else "FAIL",
           "note": ("至少一条**不同源**的通道可用 ⇒ 可以做真实渲染验证"
                    if usable else
                    "⛔ 全部候选不可用 ⇒ 本轮必须停下并**如实登记为局限**（⛔ 不得静默降级）")}
    print("== _probe_env.py：环境能力探测（开工第一步）==")
    print("站点根：%s\n" % SITE_ROOT)
    print("-- A. 候选通道 --")
    print("   非 snap 内核：found=%s（%d 个候选）" % (bool(chromes), len(chromes)))
    for p in chromes:
        print("      %s" % p)
    print("   snap 内核：found=%s（%s）" % (snap, "/snap/bin/chromium" if snap else "-"))
    print("-- B. 驱动 --")
    print("   playwright(python)：found=%s version=%s" % (drv_ok, drv_ver))
    print("-- C. 进程能力集（解释 snap 通道为何结构性不可用）--")
    for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp"):
        if k in c:
            print("   %-11s %s" % (k, c[k]))
    print("-- D. 负对照（snap 通道原始报错；★ 「失败文案 ≠ 失败现场」）--")
    for r in neg:
        print("   $ %s … rc=%s" % (r["cmd"], r["rc"]))
        for ln in r["lines"]:
            print("      %s" % ln)
    print("\n== 结论：%s ==（%s）" % (doc["verdict"], doc["note"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("   事实已落盘：%s" % os.path.relpath(OUT, SITE_ROOT))
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True))
    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
