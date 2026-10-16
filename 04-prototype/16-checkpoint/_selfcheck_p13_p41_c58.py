#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_selfcheck_p13_p41_c58.py —— 第 6 轮 T2 三条判据的**装置自检**（⛔ 只读站点产物；沙箱只写临时目录）。

## 为什么需要它
`gate_prototype.py --selftest` 只回答「负例有没有让判据变红」，⛔ 不回答两件更要紧的事：
  ① **红的是不是它该红的那一条**（负例触发了、但触发在别处 = 假自检）；
  ② **阈值另一侧会不会误判**（判据有没有退化成「有输入即 FAIL」）。
本件按 `_selfcheck_p35_fixtures.py` 的同一体例，为 T2 新落的三条判据各做两侧探针：

| 判据 | 正例 | 负例（必须 FAIL） | **对照组（必须仍 PASS）** |
|---|---|---|---|
| P13 的 G12 | 真实产物 | `counts.html` +1 | —— |
| P13 的 G13 | 真实产物 | 镜像去 `boundary` / 去 `pitfalls` 前缀 | —— |
| P41 | 真实源文件 | 裸历史句（无更正标记） | **带更正标记的历史句** |
| C58 | 真实数据 | 引文改一个词（临时沙箱内） | 未改数据的沙箱副本 |

★ 与 `_selfcheck_p35_fixtures.py` / `_selfcheck_figs_spec.py` / `_figcheck.py` 同一性质：**验证装置自身**的脚本。
★ 用法：`python3 _selfcheck_p13_p41_c58.py`（退出码 0 = 三组探针全部符合预期）
"""
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, ".."))
MISSION = os.path.normpath(os.path.join(SITE, ".."))


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bad = 0
print("== 装置自检：P13（G12/G13） · P41 · C58 ==")

# ---------------------------------------------------------------- ① P13 的四条夹具：逐条核对「红在哪」
G = _imp(os.path.join(HERE, "gate_prototype.py"), "pekg_gate_probe")
base = G.load_ctx(with_probe=False)
ok, detail = G.check_p13(copy.deepcopy(base))
print("\n-- P13 正向 --")
print("   %s | %s" % ("PASS" if ok else "FAIL", detail[:200]))
if not ok:
    bad += 1
muts = G.mut_p13(copy.deepcopy(base))
print("-- P13 夹具 %d 条：逐条核对「红在它该红的那一条」--" % len(muts))
EXPECT = ("缺 MD 镜像", "counts.", "boundary", "pitfalls")
for i, mctx in enumerate(muts):
    ok2, d2 = G.check_p13(mctx)
    want = EXPECT[i] if i < len(EXPECT) else ""
    hit = (not ok2) and (want in str(d2))
    print("   [%s] 夹具#%d 触发=%s 命中子断言 %r=%s | %s"
          % ("OK  " if hit else "BAD ", i + 1, not ok2, want, want in str(d2), str(d2)[:150]))
    if not hit:
        bad += 1

# ---------------------------------------------------------------- ② P41 两侧探针
print("\n-- P41 两侧探针（历史句「本会话浏览器不可用」）--")
p41_ok, p41_d = G.check_p41(copy.deepcopy(base))
print("   [%s] 正向（真实源文件） | %s" % ("OK  " if p41_ok else "BAD ", p41_d[:170]))
if not p41_ok:
    bad += 1
# 越界侧：裸历史句（无更正标记）⇒ 必须 FAIL
c = copy.deepcopy(base)
c.files["16-checkpoint/zz_p41_probe.py"] = G.p41_probe_line(marked=False) + "\n"
neg_ok, neg_d = G.check_p41(c)
probe_ok = (not neg_ok) and ("zz_p41_probe.py" in str(neg_d))
print("   [%s] 越界侧（裸历史句）⇒ FAIL=%s（须指名到文件）| %s"
      % ("OK  " if probe_ok else "BAD ", not neg_ok, str(neg_d)[:130]))
if not probe_ok:
    bad += 1
# 对照组：带更正标记的历史句 ⇒ 必须**仍然 PASS**（证明本条不是「见到历史句就 FAIL」）
c = copy.deepcopy(base)
c.files["16-checkpoint/zz_p41_probe.py"] = G.p41_probe_line(marked=True) + "\n"
ctl_ok, ctl_d = G.check_p41(c)
print("   [%s] 对照侧（带更正标记的历史句）⇒ 仍 PASS=%s | %s"
      % ("OK  " if ctl_ok else "BAD ", ctl_ok, str(ctl_d)[:130]))
if not ctl_ok:
    bad += 1

# ---------------------------------------------------------------- ③ C58 双向（临时沙箱：⚠ 不碰真实数据）
print("\n-- C58 双向探针（沙箱 = 临时目录，⛔ 不写真实数据）--")
tmp = tempfile.mkdtemp(prefix="pekg-c58-")
try:
    # ★ 目录形状必须与真实仓一致：`<root>/04-prototype/10-dag-data/_selfcheck.py`
    #   + `<root>/01-research/evidence/A*.json`（因为 `_selfcheck.py` 用 `HERE.parent.parent` 定位引文库）
    shutil.copytree(os.path.join(SITE, "10-dag-data"), os.path.join(tmp, "04-prototype", "10-dag-data"))
    shutil.copytree(os.path.join(MISSION, "01-research", "evidence"),
                    os.path.join(tmp, "01-research", "evidence"))
    script = os.path.join(tmp, "04-prototype", "10-dag-data", "_selfcheck.py")
    r1 = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=300)
    line1 = [l for l in r1.stdout.splitlines() if "C58-quote-provenance" in l]
    pos = (r1.returncode == 0) and line1 and line1[0].startswith("[PASS]")
    print("   [%s] 沙箱·原态 ⇒ 退出码 %d / %s"
          % ("OK  " if pos else "BAD ", r1.returncode, (line1[0][:150] if line1 else "（未见 C58 行）")))
    if not pos:
        bad += 1
    # 改一个词：把某个 complete 节点的首条 evidence quote 的第一个片段改掉
    dagp = os.path.join(tmp, "04-prototype", "10-dag-data", "dag.json")
    doc = json.load(open(dagp, encoding="utf-8"))
    target = None
    for n in doc["nodes"]:
        if n["content_status"] == "complete" and n.get("evidence") and n["evidence"][0].get("quote"):
            target = n
            break
    assert target is not None, "沙箱里找不到可改的 evidence（fail-closed）"
    q = target["evidence"][0]["quote"]
    target["evidence"][0]["quote"] = ("（篡改）" + q[4:]) if len(q) > 8 else "（篡改）"
    with open(dagp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    r2 = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=300)
    line2 = [l for l in r2.stdout.splitlines() if "C58-quote-provenance" in l]
    neg = (r2.returncode != 0) and line2 and line2[0].startswith("[FAIL]")
    print("   [%s] 沙箱·引文改一个词 ⇒ 退出码 %d / %s"
          % ("OK  " if neg else "BAD ", r2.returncode, (line2[0][:150] if line2 else "（未见 C58 行）")))
    if not neg:
        bad += 1
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== 结论：%s ==（P13 夹具 %d 条逐条核对子断言 · P41 两侧 · C58 沙箱双向；不符 %d 处）"
      % ("PASS" if bad == 0 else "FAIL", len(muts), bad))
sys.exit(0 if bad == 0 else 1)
