#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r11_ledger_update.py —— 第 11 轮轮次对象落盘（**默认 dry-run**，只有 `--write` 才写盘）。

★ 体例照 `_r10_ledger_update.py`：**文本手术**（只在 `rounds` 数组末尾追加一个对象，前缀字节零改动），
  ⛔ 不整体 `json.dumps` 重排（那会产生与内容无关的巨 diff）。
★ 每条 claim 的 `raw_output` 都**从 `_probe/r11_*.txt` 现读现摘**（⛔ 不手抄、⛔ 不转述），
  且都带 `===` 标记（`P40` 对 `main-agent-rerun` 的硬要求）。

用法：
    python3 _r11_ledger_update.py            # dry-run
    python3 _r11_ledger_update.py --write    # 落盘（先备份到 _probe/r11_backup/）
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
    dict(id="C-R11-01", source="main-agent-rerun",
         claim="开工实测（⛔ 不采信上一轮自述）：内容 67/67 · HTML 83 / MD 82 · 图件 78（156 件）· 判据 43（P01–P43）/ "
               "夹具 182+9+18；gate / a11y / seo 三套 PASS；数据侧 PASS（WARN 3）；dry-run 0/0/0；远端 e2f4cf0 与 origin 同步、"
               "最近两次 workflow 均 success。★ 同时定位三处真实缺陷：README 仍写「已写满 35 / 在册 32」、"
               "判据编号范围在 13 源文本 + 1 生成物里全是 P01–P41、G51 的单元级缺口。",
         raw_output=grab("r11_baseline.txt", r"结论：|门控结论|自检结论|added|modified|deleted|unchanged", 8)
                    + "\n" + grab("r11_c1_first_red.txt", r"FAIL|不一致", 4)),
    dict(id="C-R11-02", source="main-agent-rerun",
         claim="新增 P44（规模读数 ⟺ 实算）：引入当天**首跑报出 31 处不一致**（README 的 8 个读数 + 13 源文本的编号范围），"
               "修产物后归零。口径经两次自我修正：首版把「自带夹具字面量」与「SCHEMA 子范围」当当前读数（假阳）⇒ "
               "夹具改拼接构造、子范围改引号提及（⛔ 未放宽断言）。",
         raw_output=grab("r11_c1_first_red.txt", r"P44|不一致 31", 4)
                    + "\n" + grab("r11_step3_gate.txt", r"\[PASS\] P44|不一致 0 处", 3)),
    dict(id="C-R11-03", source="main-agent-rerun",
         claim="新增 P45（清单 ⟺ 实现 ⟺ 执行入口，收 K1/K2）：首版把 A/S 两段误判成「full 档漏跑」（22 条假阳，口径错误）⇒ "
               "改为「只比 P 段」后剩 4 条真缺陷（P44/P45 未登记 + 未进 full 档）；补齐接线后 0 条。"
               "★ 这正是「判据首版必有假阳，必须拿真实产物跑一遍」的又一次实证。",
         raw_output=grab("r11_c1_first_red.txt", r"P45|不一致 22|清单缺登记", 4)
                    + "\n" + grab("r11_step3_gate.txt", r"\[PASS\] P45|不一致 0 条", 3)),
    dict(id="C-R11-04", source="main-agent-rerun",
         claim="扩 P35 ⑨（逐散文单元枚举覆盖，收 G51 真残余）：页级计数会掩盖「某单元出现枚举标记却切不出列表」⇒ "
               "新增单元级断言 + 1 条夹具（在**已有 .enum-list 的页**上追加跨句枚举 ⇒ 页级全绿、单元级 FAIL）；"
               "P35 夹具 34 → 35，全站 190 条夹具全部触发。",
         raw_output=grab("r11_step4_selftest.txt", r"自检结论|P35 ", 3)
                    + "\n" + grab("r11_p35_fixtures.txt", r"自检结论", 2)),
    dict(id="C-R11-05", source="main-agent-rerun",
         claim="文档读数修正并同批接线：README 的 8 个读数改为实算（67/67/0 · 83 页 · 78 图件 / 156 件）且改为单态文案；"
               "13 处 `P01–P41` → `P01–P45`；`gen-state.GATE_DECL` 由**写死字符串**改为 AST 派生（`len(CHECKS)`）"
               "⇒ PUBLISH-STATE 的 gates.prototype 现为 P01–P45；`round` 10 → 11。",
         raw_output=grab("r11_step3_gate.txt", r"\[PASS\] P44|不一致 0 处", 3)
                    + "\n" + grab("r11_step5_build.txt", r"实际写入|二次比对|unchanged", 3)),
    dict(id="C-R11-06", source="main-agent-rerun",
         claim="可扫性收口（U5/G8 报告项，⛔ 不改阈值）：四处最长游程 153/130/121/113 → **105**（全站最长）/93/80/76；"
               "`> 110` 的页 0 个。切句只动标点与从句边界、⛔ 不改主张；组页 G01 的首句仍是 read-map 结论来源（P35 ⑭ 复算 PASS）。",
         raw_output=grab("r11_step3_gate.txt", r"P35 报告项", 2)),
    dict(id="C-R11-07", source="main-agent-rerun",
         claim="T6 只读语义审核（1 路 subagent，⛔ 不改盘）：10 条 findings，其中 **high × 3** 全部处置 —— "
               "① G08 组页导语把多模态写成既成结论（G52 同型）② 术语台账 `位置敏感与注意力耗散` 的界定把待验假设写成事实"
               "（与 PE-V-03 同一术语两个口径）③ PE-E-09 证据 3 的 claim「以成本换质量」与引文方向相反。"
               "其余 6 条（1 medium 同源同质化 + 5 条引文语境外推）⛔ 本轮未改（改 claim 需重取一手引文）⇒ 登记 G60。",
         raw_output=grab("r11_review.txt", r"high|verdict|findings 共", 4)
                    + "\n" + grab("r11_step3_gate.txt", r"门控结论", 2)),
    dict(id="C-R11-08", source="main-agent-rerun",
         claim="G58 收口（契约前置，⛔ 零判据变更）：`AUTHORING-SPEC.md` 新增 §2.5「完成态门槛（交付即达标）」8 条，"
               "把 P05/P22/C28–C33/C58 的门槛前置到部件契约；G57 已证并改写文档（cron 表达式 17 3 * * 1，"
               "实测触发 2026-10-26T08:54Z / 2026-11-02T11:04Z ⇒ 平台侧 5.5–7.8h 延迟，⛔ 不保证准点）。",
         raw_output=grab("r11_g57_g58.txt", r"schedule|### 2.5|cron|不保证准点", 8)),
    dict(id="C-R11-09", source="main-agent-rerun",
         claim="收口六步 ＋ 三套门控 ＋ 两档（本机）：env PASS / 渲染 83 页横向溢出 0（96.0s）/ gate P01–P45 PASS（FAIL 0）/ "
               "selftest PASS（45 判据 / 190 夹具）/ build 二次比对干净（168 unchanged）/ 几何 PASS；"
               "A 段 A1–A7 PASS、S 段 S1–S11 PASS（各带 --selftest）；`_ci_gate.sh fast` 与 `full` 在本机**各自真跑并全 PASS**。",
         raw_output=grab("r11_step2_channel.txt", r"全站|结论", 3)
                    + "\n" + grab("r11_step3_gate.txt", r"门控结论", 2)
                    + "\n" + grab("r11_step4_selftest.txt", r"自检结论", 2)
                    + "\n" + grab("r11_step6_geom.txt", r"几何复算结论", 2)
                    + "\n" + grab("r11_ci_fast.txt", r"_ci_gate.sh \[fast\] 结论", 2)
                    + "\n" + grab("r11_ci_full.txt", r"_ci_gate.sh \[full\] 结论", 2)),
    dict(id="C-R11-10", source="main-agent-rerun",
         claim="数据侧与图件面：`../10-dag-data/_selfcheck.py` PASS（FAIL 0 / WARN 3，C58 逐片段回源仍 PASS）；"
               "`gen-figs.py --check` 156 件一致；`_selfcheck_figs_spec.py` 78 张全部合规。"
               "★ 本轮内容侧改动（四处切句 + G08/术语/PE-E-09 三处 high 修正）均未触碰任何 `evidence.quote`。",
         raw_output=grab("r11_data_selfcheck.txt", r"自检：|C58", 3)
                    + "\n" + grab("r11_figs_check.txt", r"PASS", 2)
                    + "\n" + grab("r11_figs_spec.txt", r"结论", 2)),
]

ARTIFACTS = [
    "04-prototype/16-checkpoint/gate_prototype.py（+P44/+P45 ＋ P35 ⑨ 逐单元断言 ＋ 8 条夹具）",
    "04-prototype/16-checkpoint/gate-manifest.json（judges +P44/P45、generated_by、mode_note 45 条）",
    "04-prototype/16-checkpoint/_ci_gate.sh（FAST_ONLY / FULL_ONLY_NO_P38 +P44,P45；三处读数 P01–P45）",
    "04-prototype/16-checkpoint/gen-state.py（GATE_DECL 改 AST 派生、CHANGE_DECL_15、ROUND=11、gates.criteria_change_R11）",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R11.md（六段范式登记件）",
    "04-prototype/README.md（进度表 8 处读数 + 单态文案 + 3 处判据范围）",
    "04-prototype/16-checkpoint/DESIGN-CONTRACT.md（§3 模板：现有 45 条判据 P01–P45）",
    "04-prototype/16-checkpoint/AUTHORING-SPEC.md（§2.5 完成态门槛；G58）",
    ".github/workflows/pages.yml（schedule 注释按实测改写；G57）",
    "04-prototype/10-dag-data/dag.json（四处切句 + G08 组页导语 + PE-V-01 术语 + PE-E-09 claim）",
    "04-prototype/10-dag-data/glossary.json（`位置敏感与注意力耗散` 的 definition 与 dag 对齐）",
    "04-prototype/PUBLISH-STATE.json（重生成：round 11 / 判据 P01–P45 / criteria_change_R11）",
    "04-prototype/11-node-pages/{pe-n-04,pe-n-02,pe-m-02,pe-e-09,pe-v-01,pe-a-06,pe-p-01}.html 与 12-groups/g08.html（重生成）",
    "04-prototype/16-checkpoint/_probe/r11_*.txt（16 份收口原始输出 + 首跑红读数 + 审核原文）",
]

G_LIST = {
    "G51": "✅ 已消（P35 ⑨ 逐散文单元断言 + 1 条夹具）。★ 同时**更正第 9 轮的描述**：原文写「判据只判模式出现」"
           "与实现不符（页级已断言渲染口径应有数）；真残余是**页级聚合掩盖单元级缺口**。",
    "G57": "✅ 已证并改写文档：cron 表达式 `17 3 * * 1`，实测触发 2026-10-26T08:54Z / 2026-11-02T11:04Z "
           "（延迟 5.5–7.8h）⇒ `pages.yml` 注释改为「⛔ 不保证准点，判断是否跑过只看 run 列表」。",
    "G58": "✅ 已消（契约前置）：`AUTHORING-SPEC.md` §2.5 把完成态门槛（8 区块 / caliber / boundary / summary / terms / 回源 / lab 闭集）"
           "前置到部件交付时，⛔ 零判据变更。",
    "G59": "新登记（两个扫描面）：审核方用 `_probe_metrics.py` 测到的游程（pe-p-05 168 等，扫**全部散文**）"
           "与本轮 P35 报告项（只取 `.claim` / `.points li`，最长 105）**不是同一个面** ⇒ ⛔ 两个数不得互引；"
           "引用时必须写明取数口径与日期。",
    "G60": "新登记（内容面欠账，未改）：T6 审核报出 1 条同源同质化（PE-A-06 两条 evidence 同引 S-0032 同段）+ "
           "5 条引文语境外推（PE-A-06 权限、PE-O-02 先后、PE-E-01 外推、PE-E-03 对象跳转、PE-A-04 收益侧）+ 1 条 low。"
           "⛔ 未改：改 claim 需重取一手引文，⛔ 不编造。",
    "G8": "**仍在**（报告项）：长文可扫性不可机检。★ 本轮读数（P35 报告项，`.claim`/`.points li` 口径）："
          "受检页 81、最长 **105**、`> 110` 的页 **0**（四处切句前为 153/130/121/113）。",
    "K1": "✅ 已消（P45 ③）：`_ci_gate.sh` 里三个门控脚本的调用齐备由判据断言 ⇒ 「漏调一个脚本没有任何报警」不再成立。",
    "K2": "✅ 已消（P45 ①）：`gate-manifest.json` 的编号集合 ⟺ 三脚本 `CHECKS`（双向）从此被机检。",
    "K3": "仍在：`_probe/` 目录无判据管辖（本轮又增 20+ 件）。",
    "K4": "仍在：P35 ⑫ 代理判据未退役（需先有更严的直接量判据替代）。",
    "K5": "仍在：分组索引 6 列短值表未被判据覆盖。",
    "K7": "仍在：`G25`（P41 窄版），本轮未动。",
    "K9": "仍在：契约 §4① 的流程偏离（开工期落盘 vs 收口期一次性）仍未裁决；本轮第四次沿用收口期落盘并在 note 明示。",
    "G38": "仍在：`PE-E-03` / `PE-A-05` 的核心机制句无一手可引用原文（本轮 ⛔ 未改、⛔ 未编造）。",
    "G39": "仍在：任务根两个探针与 `_probe/` 脚本不在 P41 扫描面内。",
}

NOTE = (
    "★ 本轮定位：**内容收口后的第一轮质量纵深** —— 不加节点，收「同一事实写多处」的最后一类欠账（**规模读数**）"
    "与装置自洽。三件最值钱的：① **新判据当天就要报真缺陷**：P44 首跑 31 处、P45 首跑 4 条（口径修正后），"
    "两条都不是空转；② **判据扫源码时会扫到自己**：P44 首版把自带夹具的字面量当读数，与 P41 第 6 轮同型 —— "
    "「夹具字面量必须构造、⛔ 不得写字面量」应成为所有「读源码」的判据的通用纪律；"
    "③ **两个扫描面不算两个真相**：审核方报的「G8 读数过期」其实是 `_probe_metrics.py`（全部散文）与 "
    "P35 报告项（只取 `.claim`/`.points li`）的口径差 ⇒ 登记 G59，⛔ 不互相引用。"
    "★ 如实登记的偏差：P45 首版口径错（A/S 段）报 22 条假阳；P44 首版假阳（夹具字面量 + 子范围）；"
    "T6 的 6 条 medium/low 未改（改 claim 需重取一手引文，⛔ 不编造）⇒ G60。"
)


def dumps_round(obj):
    """按现有排版风格（缩进 1、数组展开）序列化**单个 round 对象**。"""
    raw = json.dumps([obj], ensure_ascii=False, indent=1)
    lines = raw.split("\n")[1:-1]          # 去掉外层 "[", "]"
    return "\n".join((" " + ln) if ln.strip() else ln for ln in lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    ledger = json.load(open(LEDGER, encoding="utf-8"))
    rounds = ledger["rounds"]
    print("== 台账现态 ==  轮次 %s / claims %d"
          % ([r["round"] for r in rounds], sum(len(r["claims"]) for r in rounds)))
    if any(r["round"] == 11 for r in rounds):
        raise SystemExit("[FAIL] 台账里已有 round 11 ⇒ 重复落盘会破坏台账（请先人工确认）")

    obj = dict(round=11,
               started_at="2026-11-03T11:54:00+08:00",
               ended_at="2026-11-03T12:45:00+08:00",
               rs_touched=["R-10", "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"],
               claims=CLAIMS,
               artifacts=ARTIFACTS,
               g_list_updates=G_LIST,
               note=NOTE)

    print("== 本轮对象 ==")
    print("  轮次 11 / rs_touched %d / claims %d / artifacts %d / G 更新 %d"
          % (len(obj["rs_touched"]), len(obj["claims"]), len(obj["artifacts"]), len(obj["g_list_updates"])))
    missing = [c["id"] for c in CLAIMS if "===" not in c["raw_output"] or "缺失" in c["raw_output"]]
    print("  raw_output 缺 === 或原始件缺失的 claims：%s" % (missing or "无"))
    block = dumps_round(obj)
    print("  将写入 %d 行（前缀字节零改动）" % block.count("\n"))

    if not a.write:
        print("\n（dry-run；加 --write 落盘）")
        return

    os.makedirs(os.path.join(PROBE, "r11_backup"), exist_ok=True)
    shutil.copy2(LEDGER, os.path.join(PROBE, "r11_backup", "ROUND-LEDGER.json.bak"))
    src_text = open(LEDGER, encoding="utf-8").read()
    prefix_len = len(src_text)
    idx = src_text.rstrip().rfind("\n ]")
    if idx < 0:
        raise SystemExit("[FAIL] 找不到 rounds 数组的收尾")
    new_text = src_text[:idx] + ",\n" + block + src_text[idx:]
    open(LEDGER, "w", encoding="utf-8", newline="\n").write(new_text)

    # 守卫：前缀字节必须零改动（除插入点后移）
    chk_text = open(LEDGER, encoding="utf-8").read()
    print("  前缀零改动：", chk_text[:idx] == src_text[:idx], "｜原长 %d → 现长 %d" % (prefix_len, len(chk_text)))
    chk = json.load(open(LEDGER, encoding="utf-8"))
    print("  回读：轮次 %s / claims %d"
          % ([r["round"] for r in chk["rounds"]], sum(len(r["claims"]) for r in chk["rounds"])))
    print("  回读：round 11 的 claims %d 条，artifacts %d 条，G 更新 %d 条"
          % (len(chk["rounds"][-1]["claims"]), len(chk["rounds"][-1]["artifacts"]),
             len(chk["rounds"][-1]["g_list_updates"])))


if __name__ == "__main__":
    main()
