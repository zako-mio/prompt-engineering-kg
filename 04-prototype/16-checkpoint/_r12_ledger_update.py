#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r12_ledger_update.py —— 第 12 轮轮次对象落盘（**默认 dry-run**，只有 `--write` 才写盘）。

★ 体例照 `_r11_ledger_update.py`：文本手术（只在 `rounds` 末尾追加一个对象，前缀字节零改动）；
  raw_output 一律从 `_probe/r12_*.txt` 现读现摘（⛔ 不手抄）。
用法：python3 _r12_ledger_update.py [--write]
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, "_probe")
LEDGER = os.path.join(HERE, "ROUND-LEDGER.json")


def grab(name, pattern, limit=6, maxlen=700):
    path = os.path.join(PROBE, name)
    if not os.path.exists(path):
        return "=== %s ===\n[缺失：该原始输出件不在盘上]" % name
    rx = re.compile(pattern)
    lines = [l.rstrip() for l in open(path, encoding="utf-8", errors="replace") if rx.search(l)]
    return "=== %s ===\n%s" % (name, "\n".join(lines[:limit])[:maxlen])


CLAIMS = [
    dict(id="C-R12-01", source="main-agent-rerun",
         claim="开工实测：内容 67/67 · 判据 45（P01–P45）· 三套门控 PASS · 远端与 origin 同步（6016e08）· 站点 200。"
               "★ 本轮两类触发都来自**上一轮自己登记的欠账**：① `K5`/`G18` ⑨ —— 分组索引的 6 列短值表"
               "不在任何判据的作用域内（`P35 ⑫` 的切片只到组页的 `#sec-nodes`/`#sec-rel`）；"
               "② `G60` —— 第 11 轮只读审核报出的 6 条引文语境外推 ＋ 1 条同源同质化。",
         raw_output=grab("r12_step1_env.txt", r"结论", 2)
                    + "\n" + grab("r12_step3_gate.txt", r"门控结论", 2)),
    dict(id="C-R12-02", source="main-agent-rerun",
         claim="`G60` 处置（⛔ 未编造、⛔ 未补源，全部靠**改作者归纳**或**合并同源证据**）："
               "① `PE-A-06` 两条同引 `S-0032` 的 evidence **合并为一条**（用库里已存的合并引文，3 个 `...` 片段逐字可回源）"
               "⇒ 该节点 4 条 evidence 对应 4 个**独立** `source_id`；② 5 条 claim 收回到引文范围内"
               "（`PE-A-06` 收窄权限 / `PE-O-02` 先后 / `PE-E-01` 放在之前 / `PE-E-03` 对象跳到裁判 / `PE-A-04` 对抗指标）。"
               "★ `C58` 复跑 PASS（节点侧 213 条 evidence / 库内 145 条唯一引文 / 坏 0），⛔ 未动任何 `quote`。",
         raw_output=grab("r12_data_selfcheck.txt", r"C58|C31|C33|C29|自检：", 6)),
    dict(id="C-R12-03", source="main-agent-rerun",
         claim="新增 **P46** 分组索引表 = 6 列短值表（直接量：表数恰 1 / 列数 = 6 / 逐单元格 caliber ≤ 24 / "
               "`.table-scroll` 容器），3 条负例全部触发；★ **如实标注：首跑即 PASS，未在引入当天报红**"
               "（那张表本来就合规）⇒ 它的价值是「把没人管的一格纳入管辖」，⛔ 不得与 P42/P43/P44 的「引入即红」并列。"
               "★ 同时实证了上一轮的机制：加 P46 后 **P44 当场报出 13 处读数未跟随**。",
         raw_output=grab("r12_step3_gate.txt", r"\[PASS\] P46|表数 1；列数 6", 3)
                    + "\n" + grab("r12_step4_selftest.txt", r"\[PASS\] P46|自检结论", 3)),
    dict(id="C-R12-04", source="main-agent-rerun",
         claim="13 处判据编号读数按 P44 的报错改到位（README 3 / `gate_prototype.py` 2 / `gate_a11y.py` 1 / "
               "`gate_seo_meta.py` 1 / `_ci_gate.sh` 3 / `gate-manifest.json` 2 / `DESIGN-CONTRACT.md` 1），"
               "`gen-state` 增 `CHANGE_DECL_16`、`ROUND` 11→12、`gates.criteria_change_R12`；P44 复跑 **0 处不一致**，"
               "P39 的登记件集合 15 → **16**（断链 0 / 孤儿 0），P45 的清单并集 63 → **64**。",
         raw_output=grab("r12_step3_gate.txt", r"\[PASS\] P44|\[PASS\] P45|\[PASS\] P39|不一致 0 处|登记件", 5)),
    dict(id="C-R12-05", source="main-agent-rerun",
         claim="收口六步 ＋ 三套门控 ＋ 两档（本机）：env PASS / 渲染 83 页横向溢出 0（87.4s）/ "
               "gate P01–P46 PASS（FAIL 0）/ selftest PASS（**46 判据 / 193 夹具**）/ build 二次比对干净 / 几何 PASS；"
               "A 段与 S 段各 PASS（含 --selftest）；`_ci_gate.sh fast` 与 `full` 在本机各自真跑并全 PASS。",
         raw_output=grab("r12_step2_channel.txt", r"全站|结论", 3)
                    + "\n" + grab("r12_step3_gate.txt", r"门控结论", 2)
                    + "\n" + grab("r12_step4_selftest.txt", r"自检结论", 2)
                    + "\n" + grab("r12_step6_geom.txt", r"几何复算结论", 2)
                    + "\n" + grab("r12_ci_fast.txt", r"\[fast\] 结论", 2)
                    + "\n" + grab("r12_ci_full.txt", r"\[full\] 结论", 2)),
    dict(id="C-R12-06", source="main-agent-rerun",
         claim="数据侧与图件面未回归：`_selfcheck.py` PASS（FAIL 0 / WARN 3）；`gen-figs.py --check` 156 件一致；"
               "`_selfcheck_figs_spec.py` 78 张全部合规；`P35` 报告项（长文可扫性，`.claim`/`.points li` 口径）"
               "读数见原始件（⛔ 不与 `_probe_metrics.py` 的口径互引，见台账 `G59`）。",
         raw_output=grab("r12_data_selfcheck.txt", r"自检：", 2)
                    + "\n" + grab("r12_figs_check.txt", r"PASS", 2)
                    + "\n" + grab("r12_figs_spec.txt", r"结论", 2)
                    + "\n" + grab("r12_step3_gate.txt", r"P35 报告项", 1)),
]

ARTIFACTS = [
    "04-prototype/16-checkpoint/gate_prototype.py（+P46 ＋ 3 条夹具；P44 的 CHECKS 标题改为「触发事实」措辞）",
    "04-prototype/16-checkpoint/gate-manifest.json（judges +P46、generated_by / full / mode_note 的 46 条）",
    "04-prototype/16-checkpoint/_ci_gate.sh（FAST_ONLY / FULL_ONLY_NO_P38 +P46；三处读数 P01–P46）",
    "04-prototype/16-checkpoint/gen-state.py（CHANGE_DECL_16、ROUND=12、gates.criteria_change_R12）",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R12.md（六段范式登记件）",
    "04-prototype/README.md（3 处判据范围 P01–P46）",
    "04-prototype/16-checkpoint/gate_a11y.py / gate_seo_meta.py / DESIGN-CONTRACT.md（各 1 处读数）",
    "04-prototype/10-dag-data/dag.json（PE-A-06 合并两条 evidence ＋ 5 条 claim 收回引文范围）",
    "04-prototype/PUBLISH-STATE.json（重生成：round 12 / 判据 P01–P46 / criteria_change_R12）",
    "04-prototype/11-node-pages/{pe-a-06,pe-o-02,pe-e-01,pe-e-03,pe-a-04}.html 与 15-md 镜像（重生成）",
    "04-prototype/16-checkpoint/_probe/r12_*.txt（16 份收口原始输出 ＋ 新增 3 份 P46 夹具证据）",
]

G_LIST = {
    "K5": "✅ 已消（P46：分组索引表的 6 列 / 逐单元格 caliber / 容器三组直接量断言 ＋ 3 条夹具）。",
    "G18": "第 12 轮逐项：⑨ **分组索引 6 列短值表** → ✅ 已消（同 `K5`，P46）；"
           "⑧ P35 ⑫ 代理判据仍未退役（留行，需先有 CI 可用的直接量）；⑩ 组页 `intro` 无枚举模式（留行）；"
           "⑪ P40 只断结构、如实性不可机检（明文登记）；⑫ P38 不判 PNG 新鲜度（留行）；"
           "⑬ `report.html` 的 `<title>` 仍写「第 1 轮」（刻意不改）；⑭ A/S 两段是两个独立脚本（第 11 轮由 P45 机检化）。",
    "G60": "✅ 已消（2026-11-05 第 12 轮）：6 条引文语境外推**全部**靠改写 claim 收回到引文范围"
           "（`PE-A-06` 收窄权限 / `PE-O-02` 先后 / `PE-E-01` 放在之前 / `PE-E-03` 对象跳到裁判 / `PE-A-04` 对抗指标 ＋ 1 条 low），"
           "同源同质化（`PE-A-06` 两条 `S-0032`）**合并为一条**、该节点 4 条 evidence 对应 4 个独立 `source_id`；"
           "★ ⛔ 未补新源、⛔ 未编造引文（改 claim 不需要新证据，这是本轮的处置原则）。",
    "G59": "仍在（两个扫描面）：`_probe_metrics.py`（全部散文）与 P35 报告项（`.claim`/`.points li`）口径不同 ⇒ "
           "引用游程读数必须写明口径与日期，⛔ 不得互引。",
    "G8": "**仍在**（报告项）：长文可扫性不可机检；本轮 P35 报告项读数见 `_probe/r12_step3_gate.txt`（⛔ 不与 G59 的另一口径混用）。",
    "G61": "新登记（判据文案的时效性）：`P44` 的 CHECKS 标题原写「README 仍写…」这类**现状断言**，"
           "修好后它每次运行都在打印一句已不成立的话 ⇒ 本轮改为「触发事实」措辞。"
           "★ 教训：判据/生成器的**运行期文案**要写「触发事实」或「守护什么」，⛔ 不写会过期的现状断言。",
    "K3": "仍在：`_probe/` 目录无判据管辖（本轮又增 20+ 件）。",
    "K4": "仍在：`P35 ⑫` 代理判据未退役（需先有 CI 可用的直接量替代；`P38` 依赖不入库的 `_probe/channel.json`）。",
    "K7": "仍在：`G25`（`P41` 窄版），本轮未动。",
    "K9": "仍在：契约 §4① 的流程偏离（开工期落盘 vs 收口期一次性）仍未裁决；第 12 轮第五次沿用收口期落盘并在 note 明示。",
    "G38": "仍在：`PE-E-03` / `PE-A-05` 的核心机制句无一手可引用原文（⛔ 未改、⛔ 未编造）。",
    "G39": "仍在：任务根两个探针与 `_probe/` 脚本不在 `P41` 扫描面内。",
}

NOTE = (
    "★ 本轮定位：**内容语义收口 ＋ 一个「没人管的对象」判据化**，仍不加节点。三件最值钱的："
    "① **P44 第一次被真实使用** —— 加 P46 后它当场报出 13 处读数未跟随，第 11 轮建的机制在第 12 轮立刻兑现；"
    "② **`G60` 的处置原则** —— 引文语境外推**不必补新源**：把作者归纳收回到引文范围即可（⛔ 不编造），"
    "同源同质化的正解是**合并**而不是「再找一条凑数」；"
    "③ **判据的运行期文案不能写现状** —— `P44` 的标题曾写「README 仍写 35/32」，修好之后它每次运行都在打印一句已不成立的话 ⇒ `G61`。"
    "★ 如实登记的偏差：P46 **首跑即绿**（对象本来就合规），与 P42/P43/P44 的「引入即红」形态不同，⛔ 不得并列引用；"
    "`K3/K4/K7/K9/G38/G39/G59` 仍开。"
)


def dumps_round(obj):
    raw = json.dumps([obj], ensure_ascii=False, indent=1)
    lines = raw.split("\n")[1:-1]
    return "\n".join((" " + ln) if ln.strip() else ln for ln in lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    ledger = json.load(open(LEDGER, encoding="utf-8"))
    rounds = ledger["rounds"]
    print("== 台账现态 ==  轮次 %s / claims %d"
          % ([r["round"] for r in rounds], sum(len(r["claims"]) for r in rounds)))
    if any(r["round"] == 12 for r in rounds):
        raise SystemExit("[FAIL] 台账里已有 round 12 ⇒ 重复落盘会破坏台账")

    obj = dict(round=12,
               started_at="2026-11-05T00:17:00+08:00",
               ended_at="2026-11-05T00:40:00+08:00",
               rs_touched=["R-10", "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"],
               claims=CLAIMS,
               artifacts=ARTIFACTS,
               g_list_updates=G_LIST,
               note=NOTE)

    print("  轮次 12 / rs_touched %d / claims %d / artifacts %d / G 更新 %d"
          % (len(obj["rs_touched"]), len(obj["claims"]), len(obj["artifacts"]), len(obj["g_list_updates"])))
    missing = [c["id"] for c in CLAIMS if "===" not in c["raw_output"] or "缺失" in c["raw_output"]]
    print("  raw_output 缺 === 或原始件缺失的 claims：%s" % (missing or "无"))
    block = dumps_round(obj)
    print("  将写入 %d 行" % block.count("\n"))
    if not a.write:
        print("\n（dry-run；加 --write 落盘）")
        return

    os.makedirs(os.path.join(PROBE, "r12_backup"), exist_ok=True)
    shutil.copy2(LEDGER, os.path.join(PROBE, "r12_backup", "ROUND-LEDGER.json.bak"))
    src = open(LEDGER, encoding="utf-8").read()
    idx = src.rstrip().rfind("\n ]")
    if idx < 0:
        raise SystemExit("[FAIL] 找不到 rounds 数组的收尾")
    new = src[:idx] + ",\n" + block + src[idx:]
    open(LEDGER, "w", encoding="utf-8", newline="\n").write(new)
    chk_text = open(LEDGER, encoding="utf-8").read()
    print("  前缀零改动：", chk_text[:idx] == src[:idx])
    chk = json.load(open(LEDGER, encoding="utf-8"))
    print("  回读：轮次 %s / claims %d"
          % ([r["round"] for r in chk["rounds"]], sum(len(r["claims"]) for r in chk["rounds"])))


if __name__ == "__main__":
    main()
