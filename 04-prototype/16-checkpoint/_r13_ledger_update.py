#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r13_ledger_update.py —— 第 13 轮轮次对象落盘（**默认 dry-run**，只有 `--write` 才写盘）。

★ 体例照 `_r12_ledger_update.py`：文本手术（只在 `rounds` 末尾追加一个对象，前缀字节零改动）；
  raw_output 一律从 `_probe/r13_*.txt` 现读现摘（⛔ 不手抄）。
用法：python3 _r13_ledger_update.py [--write]
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
    dict(id="C-R13-01", source="main-agent-rerun",
         claim="开工实测：内容 67/67 · 判据 46（P01–P46）· 三套门控 PASS · 站点 83 页。"
               "★ 本轮两类触发都来自**上一轮自己登记的欠账**：① `G38` —— `PE-E-03` / `PE-A-05` 的"
               "核心机制句**无一手可引用原文**（第 7 轮起）；② `K3` —— `_probe/` 目录（350 件）"
               "按 `.gitignore` 规则②整层不入库且**没有任何判据管辖**。",
         raw_output=grab("r13_step1_env.txt", r"结论", 2)
                    + "\n" + grab("r13_step3_gate.txt", r"门控结论", 2)),
    dict(id="C-R13-02", source="main-agent-rerun",
         claim="`G38` 处置（主 Agent 亲自取证，⛔ 未委派、⛔ 未编造）：① `PE-E-03` 补 **`S-0125`**"
               "（MT-Bench / Chatbot Arena：位置 / 冗长 / 自我偏好三类偏差的一手出处）；"
               "② `PE-A-05` 补 **`S-0126`**（White Bear：压制需要先激活 ⇒ 「不要提到 X」后立即出现讽刺性反弹；"
               "边界「单一预印本 / 开源模型 / 限定指令形态」写进发布面 claim）。"
               "两条引文**逐字取自 arXiv 摘要页**（原始件 `_probe/r13_src/*.src`，私密包 "
               "`01-research/evidence/A9-round13-g38.json`）。`C58` 复跑 PASS（215 条 evidence / 147 条唯一引文 / 9 个源件）。",
         raw_output=grab("r13_data_selfcheck.txt", r"C58|C31|C33|C29|自检：", 6)),
    dict(id="C-R13-03", source="main-agent-rerun",
         claim="新增 **P47** 过程证据台账闭合（`_probe/MANIFEST.json` ⟺ 磁盘件：双向闭合 + 逐件字节/sha256 + "
               "字段域），扫描口径只在 `_probe_manifest.py` 一处；6 条负例（孤儿 / 断链 / 指纹不符 / 类越界 ＋ "
               "两条空集守卫）全部触发。★ 两件必须分开写的事：① **首跑即 PASS，且是构造性绿**（台账与磁盘同批生成）；"
               "② **本轮之内它已抓到第一次真实漂移** —— 作者改 `_probe/README.md`（夹具条数 4→6）却忘了重建台账，"
               "自检当场判「指纹不符」FAIL，`--write` 后归零（366 ⟺ 366）⇒ 它不是形式主义，抓的正是「改完不回写」。"
               "⛔ 第 ① 条不得与「引入即报红」并列；第 ② 条才是真命中。",
         raw_output=grab("r13_step3_gate.txt", r"\[PASS\] P47|清单 \d+ 件", 3)
                    + "\n" + grab("r13_step4_selftest.txt", r"\[PASS\] P47|自检结论", 3)),
    dict(id="C-R13-04", source="main-agent-rerun",
         claim="读数跟随：加 P47 后 `P44` **当场**报出 1 处未跟随（`PUBLISH-STATE.json` 仍写 `P01–P46`）⇒ "
               "重建生成物后 0 处；`P45` 的并集 65（P47/A7/S11）、fast 43 ⊆ full 45、对象条件豁免集扩为 {P38, P47}；"
               "`P39` 登记件集合 16 → **17**（断链 0 / 孤儿 0）；`gen-state` 增 `CHANGE_DECL_17`、`ROUND` 12→13。"
               "★ 本轮只 1 处（上一轮 13 处）：因为**先读了上轮教训**，加判据前就把 README / 三脚本 / 入口 / 清单 / 契约改成 P01–P47。",
         raw_output=grab("r13_step3_gate.txt", r"\[PASS\] P44|\[PASS\] P45|\[PASS\] P39|不一致 0 处|被引用的登记件", 6)),
    dict(id="C-R13-05", source="main-agent-rerun",
         claim="收口六步 ＋ 三套门控 ＋ 两档（本机）：env PASS / 渲染 83 页横向溢出 0（111.5s）/ gate P01–P47 PASS"
               "（FAIL 0）/ selftest PASS / build 二次比对干净 / 几何 PASS；A 段与 S 段各 PASS（含 `--selftest`）；"
               "`_ci_gate.sh fast` 与 `full` 在本机各自真跑。★ P47 的读数为收口运行时刻（353 件）；"
               "本轮日志落盘后台账重建为最终件数 —— 已在 `CRITERIA-CHANGE-R13.md` §4.1 如实标注。",
         raw_output=grab("r13_step2_channel.txt", r"结论", 2)
                    + "\n" + grab("r13_step3_gate.txt", r"门控结论", 2)
                    + "\n" + grab("r13_step4_selftest.txt", r"自检结论", 2)
                    + "\n" + grab("r13_step6_geom.txt", r"几何复算结论", 2)),
    dict(id="C-R13-06", source="main-agent-rerun",
         claim="`K4`（`P35 ⑫` 代理判据退役）**本轮不做**并给出依据：前置条件「CI 可跑的直接量」不成立 —— "
               "CI 无浏览器、`P38` 的对象 `_probe/channel.json` 按规则②不入库 ⇒ 渲染面在 CI 上整体缺席；"
               "把浏览器塞进 CI 等于新增一整套渲染通道（成本与 flake 面高于一条代理判据）⇒ 需单独立项。"
               "⛔ 未用「做不到」搪塞，也⛔ 未把代理判据说成直接量。",
         raw_output=grab("r13_step3_gate.txt", r"P35 ⑪⑫⑬|代理判据", 3)),
]

ARTIFACTS = [
    "04-prototype/16-checkpoint/gate_prototype.py（+P47 区块 ＋ 4 条负例；P45 对象条件豁免集 {P38, P47}）",
    "04-prototype/16-checkpoint/_probe_manifest.py（新增：过程证据台账的生成器与单一扫描口径）",
    "04-prototype/16-checkpoint/_probe/MANIFEST.json（新增：350 → 收口 353 件；不入库）",
    "04-prototype/16-checkpoint/gate-manifest.json（judges +P47、47 条、full 档第三条对象条件）",
    "04-prototype/16-checkpoint/_ci_gate.sh（P01–P47；P47 不进任何 CI 档并给理由）",
    "04-prototype/16-checkpoint/gen-state.py（CHANGE_DECL_17、ROUND=13、gates.criteria_change_R13）",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R13.md（六段范式登记件）",
    "04-prototype/16-checkpoint/_probe/README.md（§四：本目录已有判据管辖；收口须重建台账）",
    "04-prototype/README.md（3 处判据范围 P01–P47）",
    "04-prototype/16-checkpoint/gate_a11y.py / gate_seo_meta.py / DESIGN-CONTRACT.md（各 1 处读数）",
    "04-prototype/10-dag-data/sources.json（+S-0125 / S-0126；count 124 → 126）",
    "04-prototype/10-dag-data/dag.json（PE-E-03 / PE-A-05 各 +1 条 evidence）",
    "04-prototype/11-node-pages/{pe-e-03,pe-a-05}.html 与 15-md 镜像（重生成）",
    "04-prototype/PUBLISH-STATE.json（重生成：round 13 / 判据 P01–P47 / criteria_change_R13）",
    "04-prototype/16-checkpoint/_probe/r13_*.txt（收口原始输出 ＋ 新增 4 份 P47 夹具证据）",
    "01-research/evidence/A9-round13-g38.json（主 Agent 亲自取回的一手引文包；不入库）",
]

G_LIST = {
    "K3": "✅ 已消（2026-11-05 第 13 轮）：`_probe/MANIFEST.json`（350 → 353 件）＋ `_probe_manifest.py`（唯一扫描口径）"
          "＋ **P47**（双向闭合 / 逐件指纹 / 字段域 / 4 条负例）＋ `_probe/README.md` §四 的台账化更新。",
    "G18": "第 13 轮逐项：⑯ `_probe/` 无判据管辖 → ✅ 已消（同 `K3`，P47）；⑧ P35 ⑫ 代理判据仍未退役（`K4` 的裁决见下）；"
           "⑩ 组页 `intro` 无枚举模式（留行）；⑪ P40 只断结构、如实性不可机检（明文登记）；"
           "⑫ P38 不判 PNG 新鲜度（留行）；⑬ `report.html` 的 `<title>`（刻意不改）；⑭ A/S 两段是两个独立脚本（P45 机检化）。",
    "G38": "✅ 已消（2026-11-05 第 13 轮）：`PE-E-03` 补 `S-0125`、`PE-A-05` 补 `S-0126`，两条引文逐字取自 arXiv 摘要页"
           "（`_probe/r13_src/*.src`），`C58` 逐片段回源 PASS；★ 边界（单一预印本 / 开源模型 / 限定指令形态）"
           "写进 `PE-A-05` 的发布面 claim，⛔ 不冒充学界共识。",
    "K4": "**仍在**（本轮**裁决不做**）：前置条件「CI 可跑的直接量」不成立 —— CI 无浏览器、渲染面整体缺席；"
          "把浏览器塞进 CI = 新增一整套渲染通道，成本与 flake 面高于一条代理判据 ⇒ 需单独立项。"
          "`P35 ⑫` 继续以**代理判据**形态运行并在输出里自陈，⛔ 不得读作直接量。",
    "K7": "仍在：`G25`（`P41` 窄版：只判已登记的历史句），本轮未动。",
    "K8": "仍在：`G39`（任务根两个探针与 `_probe/` 脚本不在 `P41` 扫描面内）—— ★ 本轮新增的 `_probe_manifest.py` 在 "
          "`16-checkpoint/` 顶层，**在** P41 扫描面内；但 `_probe/r13_evidence_add.py` 仍不在。",
    "K9": "仍在：契约 §4① 的流程偏离（开工期落盘 vs 收口期一次性）仍未裁决；第 13 轮第六次沿用收口期落盘并在 note 明示。",
    "G39": "仍在（同 `K8`）：P41 的扫描面只含 `16-checkpoint/*.py` 顶层。",
    "G59": "仍在（两个扫描面）：`_probe_metrics.py`（全部散文）与 P35 报告项（`.claim`/`.points li`）口径不同 ⇒ "
           "引用游程读数必须写明口径与日期，⛔ 不得互引。",
    "G8": "**仍在**（报告项）：长文可扫性不可机检；本轮 P35 报告项读数见 `_probe/r13_step3_gate.txt`"
          "（⛔ 不与 `G59` 的另一口径混用）。",
    "G61": "已消（第 12 轮改法保留）：本轮新增的判据文案（P47 的 CHECKS 标题与 P44 的触发事实句）一律写"
           "「触发事实 / 守护什么」，⛔ 未写会过期的现状。",
}

NOTE = (
    "★ 本轮定位：**内容面唯一还开着的实质欠账收口（G38）＋ 一个「没人管的目录」判据化（K3）**，仍不加节点。"
    "三件最值钱的：① `G38` 不是「再找一条凑数」——两条新引文分别直击两个节点**自己的机制句**"
    "（裁判三类偏差 / 否定指令的讽刺性反弹），且边界写进发布面 claim；"
    "② `P47` 把 `_probe/` 从「人读的寿命表」变成「可判假的台账」，但它**首跑即构造性绿**，价值在后续轮次 —— "
    "这一点在登记件与台账里都如实标注；"
    "③ `K4` 被**显式裁决不做**并给出成本依据，⛔ 不用「做不到」搪塞，也⛔ 不把代理判据说成直接量。"
    "★ 如实登记的偏差：P47 的验收读数（353 件）与最终台账件数差 = 本轮日志件数（台账在日志落盘后重建）；"
    "P47 在本轮内**抓到一次真实漂移**（改 `_probe/README.md` 未重建台账 ⇒ 指纹不符 FAIL），已写进登记件 §4.1b；"
    "`P47` 不进任何 CI 档（对象按规则②不入库，与 P38 同一处置）；`K4/K7/K8/K9/G39/G59/G8` 仍开。"
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
    if any(r["round"] == 13 for r in rounds):
        raise SystemExit("[FAIL] 台账里已有 round 13 ⇒ 重复落盘会破坏台账")

    obj = dict(round=13,
               started_at="2026-11-05T09:37:00+08:00",
               ended_at="2026-11-05T10:30:00+08:00",
               rs_touched=["R-10", "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"],
               claims=CLAIMS,
               artifacts=ARTIFACTS,
               g_list_updates=G_LIST,
               note=NOTE)

    print("  轮次 13 / rs_touched %d / claims %d / artifacts %d / G 更新 %d"
          % (len(obj["rs_touched"]), len(obj["claims"]), len(obj["artifacts"]), len(obj["g_list_updates"])))
    missing = [c["id"] for c in CLAIMS if "===" not in c["raw_output"] or "缺失" in c["raw_output"]]
    print("  raw_output 缺 === 或原始件缺失的 claims：%s" % (missing or "无"))
    block = dumps_round(obj)
    print("  将写入 %d 行" % block.count("\n"))
    if not a.write:
        print("\n（dry-run；加 --write 落盘）")
        return

    os.makedirs(os.path.join(PROBE, "r13_backup"), exist_ok=True)
    shutil.copy2(LEDGER, os.path.join(PROBE, "r13_backup", "ROUND-LEDGER.json.bak"))
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
