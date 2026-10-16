#!/usr/bin/env python3
"""_g4_settle.py —— G4 落地后的「静默期」侦察：确认另一个子 Agent 已停手。

为什么需要：留档轮要跑 `build-all.py --write`（幂等读数）。若委派方仍在写同一批文件，
两边会互相覆盖（第 1 轮已实测过一次并发写冲突）。故先看「最近有没有人在写」。

输出：
  * 最近 N 秒内被修改的文件清单（按 mtime 降序）
  * G4 相关新件的存在性
用法：python3 _g4_settle.py [window_seconds]
退出码：0 = 静默（无文件在窗口内被改）；1 = 仍在写
⛔ 只读，不写任何产物。
"""
import sys
import time
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE.parent.parent
WINDOW = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
SKIP_DIRS = {".git", "__pycache__", "node_modules"}

now = time.time()
recent = []
for p in WS.rglob("*"):
    if not p.is_file():
        continue
    if any(part in SKIP_DIRS for part in p.parts):
        continue
    try:
        age = now - p.stat().st_mtime
    except OSError:
        continue
    if age <= WINDOW:
        recent.append((age, p.relative_to(WS).as_posix()))

recent.sort()
print(f"窗口 {WINDOW:.0f}s 内被修改的文件：{len(recent)} 个")
for age, rel in recent[:60]:
    print(f"  {age:7.1f}s  {rel}")

print("\nG4 相关件存在性：")
for name in ("CRITERIA-CHANGE-P35-G4.md", "CRITERIA-CHANGE-P35.md",
             "CONTENT-V2.md", "DESIGN-CONTRACT.md"):
    p = HERE / name
    print(f"  {'YES' if p.is_file() else 'NO ':>3}  {name}"
          + (f"  ({p.stat().st_size} B)" if p.is_file() else ""))

still = [rel for age, rel in recent if not rel.startswith("04-prototype/16-checkpoint/_")]
print(f"\n非本子 Agent 自身脚本的近期改动：{len(still)} 个")
print("SETTLE=" + ("yes" if not still else "no"))
sys.exit(0 if not still else 1)
