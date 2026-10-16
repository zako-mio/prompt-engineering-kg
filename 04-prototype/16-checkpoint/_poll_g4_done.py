#!/usr/bin/env python3
"""_poll_g4_done.py —— 等 G4 **完全收口**（不只是产物落地，还要装置自检转绿）。

为什么需要：v2 判据（产物含 `<section class="read-map">`）在 17:15 就满足了，但随后实测
`gate_prototype.py --selftest` = **exit 1 / FAIL**（P35 负例 #10 未触发），且 `gate_prototype.py`
的 mtime 只比现在早 31s ⇒ **委派方仍在改判据装置**。此刻开写报告会得到一份与产物不符的档案。

收口判据（三条全满足）：
  1. 全部受管源与产物**静默** ≥ QUIET 秒（没人在写）
  2. `CRITERIA-CHANGE-P35-G4.md` 已落盘（G4 的判据变更登记件，gen-groups.py 已引用它）
  3. `gate_prototype.py --selftest` 退出码 = 0

用法：python3 _poll_g4_done.py [max_wait_seconds]
退出码：0 = 完全收口；2 = 已静默但自检仍红；1 = 窗口内未静默
⛔ 只读（除自检自身），不写任何产物。
"""
import subprocess
import sys
import time
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PROTO = HERE.parent

SOURCES = ["gen-common.py", "gen-groups.py", "gen-views.py", "gen-nodes.py",
           "gen-root.py", "gen-md.py", "gen-figs.py", "gen-tokens.py",
           "gen-interactive.py", "gen-state.py", "build-all.py", "gate_prototype.py"]
HTML_GLOBS = ["index.html", "11-node-pages/*.html", "12-groups/*.html",
              "13-interactive/index.html", "14-views/*.html"]
DOC = HERE / "CRITERIA-CHANGE-P35-G4.md"

QUIET = 180.0
INTERVAL = 30.0
MAX_WAIT = float(sys.argv[1]) if len(sys.argv) > 1 else 480.0

watched = [HERE / s for s in SOURCES]
for g in HTML_GLOBS:
    watched.extend(sorted(PROTO.glob(g)))


def newest_age():
    now = time.time()
    newest, who = -1.0, "-"
    for p in watched:
        try:
            age = now - p.stat().st_mtime
        except OSError:
            continue
        if newest < 0 or age < newest:
            newest, who = age, p.name
    return newest, who


t0 = time.time()
n = 0
last_rc = None
while True:
    n += 1
    age, who = newest_age()
    el = time.time() - t0
    stamp = time.strftime("%H:%M:%S")
    doc = DOC.is_file()
    print(f"[{stamp}] poll#{n} elapsed={el:.0f}s quiet={age:.0f}s (newest={who}) "
          f"doc={doc} selftest_rc={last_rc}", flush=True)
    if age >= QUIET and doc:
        r = subprocess.run([sys.executable, "gate_prototype.py", "--selftest"],
                           capture_output=True, text=True, cwd=str(HERE), timeout=900)
        last_rc = r.returncode
        tail = [ln for ln in (r.stdout or "").splitlines() if ln.startswith("== 自检结论")]
        print(f"        selftest rc={last_rc} | {tail[-1] if tail else '(无结论行)'}", flush=True)
        if last_rc == 0:
            print(f"G4_DONE=yes elapsed={el:.1f}s", flush=True)
            sys.exit(0)
        print(f"G4_DONE=settled_but_selftest_red elapsed={el:.1f}s", flush=True)
        sys.exit(2)
    if el + INTERVAL > MAX_WAIT:
        print(f"G4_DONE=no (window {MAX_WAIT:.0f}s exhausted) elapsed={el:.1f}s "
              f"quiet={age:.0f}s doc={doc} selftest_rc={last_rc}", flush=True)
        sys.exit(1)
    time.sleep(INTERVAL)
