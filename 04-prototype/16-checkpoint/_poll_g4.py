#!/usr/bin/env python3
"""_poll_g4.py v2 —— 等 G4 **真正落地到产物**（不是只看生成器里出现某个词）。

为什么改判据：v1 只看 `gen-groups.py` 里有无 'read-map'，而该词可以只出现在**docstring 计划**
里（实测：17:14 命中 1 次，但那只是文件头第 11 行的说明，`12-groups/*.html` 里根本没有
`<section class="read-map">`）。按契约「⛔ 不得在 G4 落地前就开始写报告（会得到一份与产物
不符的档案）」，判据必须落在**产物侧**。

产物侧判据（全满足才算落地）：
  1. 全部 `12-groups/*.html` 都含 `<section class="read-map"`
  2. `14-views/01-learning-path.html` 含 `<section class="read-map"`
  3. 静默期：以上文件最近 mtime 距今 ≥ QUIET 秒（说明本轮 build 已停下，没人在写）

用法：python3 _poll_g4.py [max_wait_seconds]
退出码：0 = 已落地；1 = 窗口内未落地（超时）。
⛔ 本文件是等待工具，不参与产物生成，不写任何产物。
"""
import sys
import time
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PROTO = HERE.parent
GROUPS = PROTO / "12-groups"
LEARN = PROTO / "14-views" / "01-learning-path.html"
SECTION = '<section class="read-map"'
INTERVAL = 30.0
QUIET = 45.0
MAX_WAIT = float(sys.argv[1]) if len(sys.argv) > 1 else 560.0


def count_sections(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").count(SECTION)
    except Exception as exc:  # noqa: BLE001
        return f"ERR({exc})"


def report():
    group_files = sorted(GROUPS.glob("*.html"))
    per = {p.name: count_sections(p) for p in group_files}
    ok_groups = [n for n, c in per.items() if isinstance(c, int) and c > 0]
    learn = count_sections(LEARN)
    newest = 0.0
    for p in list(group_files) + [LEARN]:
        try:
            newest = max(newest, p.stat().st_mtime)
        except OSError:
            pass
    age = time.time() - newest if newest else -1.0
    return per, ok_groups, learn, age


t0 = time.time()
n = 0
while True:
    n += 1
    per, ok_groups, learn, age = report()
    el = time.time() - t0
    stamp = time.strftime("%H:%M:%S")
    print(f"[{stamp}] poll#{n} elapsed={el:.0f}s groups_with_readmap="
          f"{len(ok_groups)}/{len(per)} learn_sections={learn} "
          f"newest_mtime_age={age:.0f}s", flush=True)
    all_groups = len(per) > 0 and len(ok_groups) == len(per)
    learn_ok = isinstance(learn, int) and learn > 0
    quiet = age >= QUIET
    if all_groups and learn_ok and quiet:
        print(f"G4_LANDED=yes elapsed={el:.1f}s "
              f"(groups {len(ok_groups)}/{len(per)}, learn={learn}, quiet={age:.0f}s)", flush=True)
        sys.exit(0)
    if el + INTERVAL > MAX_WAIT:
        print(f"G4_LANDED=no (window {MAX_WAIT:.0f}s exhausted) elapsed={el:.1f}s "
              f"groups={len(ok_groups)}/{len(per)} learn={learn} age={age:.0f}s", flush=True)
        sys.exit(1)
    time.sleep(INTERVAL)
