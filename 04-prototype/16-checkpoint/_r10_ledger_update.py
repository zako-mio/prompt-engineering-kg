#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r10_ledger_update.py —— 第 10 轮轮次对象落盘（**默认 dry-run**，只有 `--write` 才写盘）。

★ 为什么是「文本手术」而不是整体重写：`ROUND-LEDGER.json` 的排版是历史混合风格（round 3 的数组内联，
round 5 的数组展开），`json.dumps` 会把整份文件重排 ⇒ 与内容无关的巨 diff（本仓 R-24 的口径：
留档件的 diff 必须是**语义 diff**）。⇒ 只在 `rounds` 数组末尾追加一个对象，前缀字节零改动。

★ 每条 claim 的 `raw_output` 都是**从 `_probe/*.txt` 现读现摘**（⛔ 不手抄、⛔ 不转述），
且都带 `===` 标记（`P40` 对 `main-agent-rerun` 的硬要求）。

用法：
    python3 _r10_ledger_update.py            # dry-run：打印本轮对象的摘要与将写入的位置
    python3 _r10_ledger_update.py --write    # 落盘（先备份到 _probe/r10_backup/）
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
    """从 `_probe/<name>` 里摘出匹配行（原始输出，⛔ 不改写）。"""
    path = os.path.join(PROBE, name)
    if not os.path.exists(path):
        return "=== %s ===\n[缺失：该原始输出件不在盘上]" % name
    rx = re.compile(pattern)
    lines = [l.rstrip() for l in open(path, encoding="utf-8", errors="replace") if rx.search(l)]
    body = "\n".join(lines[:limit])[:maxlen]
    return "=== %s ===\n%s" % (name, body)


CLAIMS = [
    dict(id="C-R10-01", source="main-agent-rerun",
         claim="开工四件套全部落地：环境探测 PASS（R-21）／部署复核（根页自报 48/19，三个第 9 轮新页全 200）／"
               "基线 fast 档 PASS／波次目录与 .gitignore 三条已建。",
         raw_output=grab("r10_env.txt", r"结论|PASS", 3)
                    + "\n" + grab("r10_deploy_check.txt", r"200|已写满", 6)
                    + "\n" + grab("r10_baseline_fast.txt", r"结论：PASS|自检结论", 2)),
    dict(id="C-R10-02", source="main-agent-rerun",
         claim="取证落盘：sources.json 115→124（S-0116–S-0124）＋ 新私密包 A8 共 19 条 metas；"
               "每条引文按省略号拆片段、逐片段在本地保存的源件正文里逐字命中（⛔ 未编造任何一句）。",
         raw_output=grab("r10_evidence_check.txt", r"结论|回读|OK  ", 10)),
    dict(id="C-R10-03", source="main-agent-rerun",
         claim="G23 处置：frontier 两片「作者期注记」换成可逐字回源原文（S-0034 / 新 S-0120）⇒ "
               "C58b 由常驻 WARN 转为 PASS（0 片坏）；C59 双载体身份层一致（4 个节点 ⟺ 4 条条目）。",
         raw_output=grab("r10_final_selfcheck.txt", r"C58b|C59|C58-quote|自检：", 4)),
    dict(id="C-R10-04", source="main-agent-rerun",
         claim="波 A（G04 编排 8 节点）：8 个部件过合并器四项闸并落盘，complete 48→56；8 对图件（pe-o-01…08）"
               "成对登记；生成器幂等（build 后 dry-run 差集 0/0/0）。",
         raw_output=grab("r10_merge_recheck.txt", r"=== wave 5|结论", 3)
                    + "\n" + grab("r10_waveA_build1.txt", r"实际写入|二次比对", 2)),
    dict(id="C-R10-05", source="main-agent-rerun",
         claim="波 B（GD-N 4 节点）：4 个部件落盘，complete 56→60；3 张新图 ＋ 补 NODE_FIG[PE-N-01]（图注两处逐字节同文）。",
         raw_output=grab("r10_merge_recheck.txt", r"=== wave 6|结论", 3)
                    + "\n" + grab("r10_waveB_build2.txt", r"实际写入|二次比对", 2)),
    dict(id="C-R10-06", source="main-agent-rerun",
         claim="波 C（G03 上下文 7 节点）：7 个部件落盘，complete 60→67（图谱写完）；7 对图件 pe-c-01…07。",
         raw_output=grab("r10_merge_recheck.txt", r"=== wave 7|结论", 3)
                    + "\n" + grab("r10_waveC_build2.txt", r"实际写入|二次比对", 2)),
    dict(id="C-R10-07", source="main-agent-rerun",
         claim="新增判据 P43（图注跨登记表逐字同文）**引入当天即报出真实存量缺陷** pe-f-06，修后 0 处；"
               "P42（内容状态文案与真相源一致）首版有假阳（子串 `待填充 0` 命中章节号 03），改正则后归零。",
         raw_output=grab("r10_waveA_gate.txt", r"\[FAIL\] P43|两处图注不同文", 3)
                    + "\n" + grab("r10_pre_closure_gate.txt", r"结论：PASS", 2)),
    dict(id="C-R10-08", source="main-agent-rerun",
         claim="两态→单态文案收敛：新增 gen-common.content_state_copy() 单一出口，六个生成器全部改读它；"
               "67/67 后根页/学习路径/交互页/页脚/MD 镜像再无「架构在册」可见文案（只剩代码分支）。",
         raw_output=grab("r10_final_gate.txt", r"\[PASS\] P42|节点 67", 3)
                    + "\n" + grab("r10_final_selfcheck.txt", r"自检：", 2)),
    dict(id="C-R10-09", source="main-agent-rerun",
         claim="夹具与数据状态解绑：67/67 后 P05/P22 的 registered 夹具 `next(...)` 抛 StopIteration，"
               "selftest 由 PASS 变 FAIL ⇒ 改为「取不到就现造一个」（⛔ 未改任何断言），修后两条全触发。",
         raw_output=grab("r10_final_selftest.txt", r"自检结论|\[PASS\] P05|\[PASS\] P22", 4)),
    dict(id="C-R10-10", source="main-agent-rerun",
         claim="收口六步 ＋ 三套门控 ＋ 图件两侧探针全绿：gate P01–P43 PASS／a11y A1–A7 PASS／seo S1–S11 PASS，"
               "数据侧 C01–C59 PASS（WARN 3）；图件 156 件一致；几何复算 0 超区 0 重叠。",
         raw_output=grab("r10_final_gate.txt", r"结论：PASS", 2)
                    + "\n" + grab("r10_final_selfcheck.txt", r"自检：", 2)
                    + "\n" + grab("r10_final_figs.txt", r"图件 156|结论：PASS", 3)
                    + "\n" + grab("r10_final_geom.txt", r"几何复算结论", 2)),
    dict(id="C-R10-11", source="main-agent-rerun",
         claim="执行通道两档在本机各自真跑：fast（含新进档的 P42/P43）与 full（本机有 _probe/channel.json ⇒ 含 P38）"
               "均 PASS；★ 两条读数分别指明环境（本机），⛔ 不混读。",
         raw_output=grab("r10_final_ci_fast.txt", r"结论：PASS|结论：FAIL", 2)
                    + "\n" + grab("r10_final_ci_full.txt", r"结论：PASS|结论：FAIL", 2)),
    dict(id="C-R10-12", source="main-agent-rerun",
         claim="上线验证（⛔ 不把「已 push」读作「已上线」）：push 后三 job 全绿，且 curl 本轮三个新页全 200、"
               "根页自报 67 / 0 —— 只有这两条同时成立才写「已上线」。",
         raw_output=grab("r10_live_check.txt", r"200|已写满|架构", 8)),
]

ARTIFACTS = [
    "04-prototype/10-dag-data/dag.json（19 节点翻 complete ＋ lab/evidence/pitfalls ＋ 少量 why/intro 补写）",
    "04-prototype/10-dag-data/frontier.json（G23：两片引文换成可回源原文）",
    "04-prototype/10-dag-data/sources.json（S-0116–S-0124，meta.count 115→124）",
    "04-prototype/10-dag-data/_selfcheck.py（新增 C59；C58b 改条件 WARN）",
    "04-prototype/10-dag-data/figures/（+18 对 .dot/.svg ⇒ 156 件）",
    "04-prototype/16-checkpoint/gen-figs.py / gen-nodes.py（+18 FIGS，+19 NODE_FIG，pe-f-06 图注统一）",
    "04-prototype/16-checkpoint/gen-common.py（content_state_copy 单一出口 ＋ 页脚）",
    "04-prototype/16-checkpoint/gen-root.py / gen-views.py / gen-md.py / gen-state.py / gen-interactive.py（改读单一出口）",
    "04-prototype/16-checkpoint/gate_prototype.py（+P42/+P43 ＋ 4 条夹具；P05/P22 夹具解绑数据状态）",
    "04-prototype/16-checkpoint/gate-manifest.json（+P42/P43 的 judge；selftest 不再自报夹具数）",
    "04-prototype/16-checkpoint/_ci_gate.sh（fast/full 两档显式集合 +P42,P43）",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R10.md（本轮判据变更登记件）",
    "04-prototype/16-checkpoint/ROUND-LEDGER.json（本轮对象）",
    ".gitignore（+_wave5/6/7_parts）",
    "report.md §十三 / report.html（留档双版本）",
]

G_LIST = {
    "G23": "✅ 已消（PASS）：frontier 两片作者期注记换成可逐字回源原文（S-0034 / S-0120），C58b 由 WARN 转 PASS",
    "G51": "仍在（判据面）：渲染器枚举覆盖面的不对称未加判据；本轮只在内容侧按「同句 ≥2 个分号」处置",
    "G54": "✅ 已消（PASS）：pe-f-06 两处图注统一，并由新判据 P43 常驻守着",
    "G56": "新登记：夹具不得依赖会归零的数据子集（本轮 P05/P22 的 registered 夹具在 67/67 时抛 StopIteration ⇒ 自检 FAIL）",
    "G57": "新登记：.github/workflows/pages.yml 注释写「每周一 03:17 UTC」，两次实测均在 08:5x UTC 触发（GitHub 侧延迟或 cron 漂移，未证）",
    "G58": "新登记：注册期字段只要求「导读能读」，完成期要求「八区块达标」⇒ 19 个节点里 8 个在翻 complete 时才被 P05 拦住；下一轮应在部件契约里前置完成态门槛",
    "K2": "✅ 已消：gate-manifest 不再自报夹具数（重复事实已删），编号集合这一层仍无判据（如实留行）",
}

NOTE = (
    "★ 本轮的定位**：把内容从 48 推到 **67/67**（G04 8 ＋ GD-N 4 ＋ G03 7 ＝ 19 节点），"
    "并在同一条链上收掉四处「同一事实写两处」的欠账（图注 / 内容状态文案 / 清单夹具数 / 双载体身份层）。"
    "⇒ 本轮最值钱的认识不是「写完了」，而是两条：① **判据的价值在第 N 次实证** —— P43 引入当天就报出挂了一整轮的 G54，"
    "P42 第一次跑就撞上「registered 归零」这个从未被覆盖的第三态；"
    "② **夹具的可判假性会被数据状态绑架** —— 67/67 之后 P05/P22 的 registered 夹具直接 StopIteration，"
    "判据没坏、是夹具的前提没了（G56）。★ 另两处如实登记的偏差：P42 首版子串口径命中章节号（假阳 3 处）、"
    "G23 的两条替代来源是 Azure/AWS/Gemini 而非 Anthropic/OpenAI（两个最大的官方口径域本轮不可达）。"
)


def dumps_round(obj):
    """按现有排版风格（缩进 1、数组展开）序列化**单个 round 对象**。"""
    raw = json.dumps([obj], ensure_ascii=False, indent=1)
    lines = raw.split("\n")[1:-1]          # 去掉外层 "[", "]"
    out = []
    for ln in lines:
        out.append((" " + ln) if ln.strip() else ln)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    ledger = json.load(open(LEDGER, encoding="utf-8"))
    rounds = ledger["rounds"]
    print("== 台账现态 ==  轮次 %s / claims %d" % ([r["round"] for r in rounds], sum(len(r["claims"]) for r in rounds)))
    if any(r["round"] == 10 for r in rounds):
        raise SystemExit("[FAIL] 台账里已有 round 10 ⇒ 重复落盘会破坏台账（请先人工确认）")

    obj = dict(round=10,
               started_at="2026-11-02T12:25:00+08:00",
               ended_at="2026-11-02T13:45:00+08:00",
               rs_touched=["R-01", "R-07", "R-08", "R-10", "R-19", "R-21", "R-22", "R-23", "R-24", "R-25"],
               claims=CLAIMS,
               artifacts=ARTIFACTS,
               g_list_updates=G_LIST,
               note=NOTE)

    print("== 本轮对象 ==")
    print("  轮次 10 / rs_touched %d / claims %d / artifacts %d / G 更新 %d"
          % (len(obj["rs_touched"]), len(obj["claims"]), len(obj["artifacts"]), len(obj["g_list_updates"])))
    missing = [c["id"] for c in CLAIMS if "===" not in c["raw_output"] or "缺失" in c["raw_output"]]
    print("  raw_output 缺 === 或原始件缺失的 claims：%s" % (missing or "无"))
    block = dumps_round(obj)
    print("  将写入 %d 行（前缀字节零改动）" % block.count("\n"))

    if not a.write:
        print("\n（dry-run；加 --write 落盘）")
        return

    os.makedirs(os.path.join(PROBE, "r10_backup"), exist_ok=True)
    shutil.copy2(LEDGER, os.path.join(PROBE, "r10_backup", "ROUND-LEDGER.json.bak"))
    src_text = open(LEDGER, encoding="utf-8").read()
    tail = src_text.rstrip()
    if not tail.endswith("]\n}") and not tail.endswith("]"):
        raise SystemExit("[FAIL] 台账尾部结构不符合预期")
    idx = src_text.rstrip().rfind("\n ]")
    if idx < 0:
        raise SystemExit("[FAIL] 找不到 rounds 数组的收尾")
    new_text = src_text[:idx] + ",\n" + block + src_text[idx:]
    open(LEDGER, "w", encoding="utf-8").write(new_text)

    chk = json.load(open(LEDGER, encoding="utf-8"))
    print("  回读：轮次 %s / claims %d" % ([r["round"] for r in chk["rounds"]],
                                          sum(len(r["claims"]) for r in chk["rounds"])))
    print("  回读：round 10 的 claims %d 条，artifacts %d 条"
          % (len(chk["rounds"][-1]["claims"]), len(chk["rounds"][-1]["artifacts"])))


if __name__ == "__main__":
    main()
