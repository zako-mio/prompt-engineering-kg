#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r9_ledger_update.py —— 把**第 9 轮**对象追加进 `ROUND-LEDGER.json`（⛔ 不回改 round 1–8 的字节）。

## 为什么继续用**文本手术**（照 `_r8_ledger_update.py`）
本文件的缩进（根键 1 空格 / 轮次对象 2 空格 / 其下键 3 空格）**不是**任何单次 `json.dumps` 的产物
—— 它是历轮**逐次文本追加**的结果。⇒ 本轮沿用第 8 轮的同一手法：只在本文件**末尾的 `]` 之前**插入
第 9 轮对象，其余字节**一个都不动**。三道守卫（任何一道不过即 abort，⛔ 不写盘）：
  ① 末尾形态 fail-closed（文件必须以 `\\n ]\\n}\\n` 收尾，否则拒绝手术）；
  ② **字节级**前缀比对（`new_raw` 的前缀必须与原文前缀逐字节相同 + sha256 相同）；
  ③ `guards()` 的**语义**比对（历史轮次的 round 序列、内容、schema、轮次数 +1）。

## 契约依据（`DESIGN-CONTRACT.md` §轮次执行协议 ③④）
- 每条 claim 必须标 `source`（`self-report` / `main-agent-rerun`）并附 `raw_output` **原文**；
- `main-agent-rerun` 的 `raw_output` 必须带原始输出标记（`===`）；
- `rs_touched` 必须逐条声明本轮触碰的 R-xx（⛔ 不得为空、⛔ 不得写契约规则表外的 id）。
机检判据 = **P40**（只断言结构与自洽，⛔ 不验证自述是否如实）。

## 本脚本**额外**加的一道自证（★ 第 9 轮新增）
`raw_output` 的每一行**非节标签**内容，都必须在它声明的 `_probe/r9_*.txt` 源件里**逐字找得到**
（口径 = 空白归一化后逐字相等，与 P13 的 G13 镜像比对同源；长行可用 `…（截断）` 结尾，此时只校验
其左侧前缀）⇒ 防「凭记忆转述」与「拼接引文」。`===` 开头的行是**节标签**（可重写、不参与比对）。

## 用法
    python3 _r9_ledger_update.py            # dry-run：预校验 + 文本手术模拟 + 结论，⛔ 不落盘
    python3 _r9_ledger_update.py --write    # 落盘（★ 本轮的落盘由主 Agent 决定）

⛔ 本脚本不跑 `build-all.py` / `gate_*.py` / `_wave1_apply.py`，也不触碰任何产物。
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # 任务根（04-prototype 的上一层）
LEDGER = os.path.join(HERE, "ROUND-LEDGER.json")
PROBE = os.path.join(HERE, "_probe")
SCHEMA = "pekg/round-ledger/1"

# ---------------------------------------------------------------- 第 9 轮对象的**确定值**

STARTED = "2026-10-19T19:59:00+08:00"
ENDED = "2026-10-19T23:55:00+08:00"

RS_TOUCHED = ["R-07", "R-08", "R-09", "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"]

# 长行截断标记（只出现在 raw_output 里；带标记时按「左侧前缀」比对，见 docstring）
TRUNC = " …（截断）"

CLAIMS = [
    {
        "id": "C-R9-01",
        "claim": "内容波次 4 落盘：13 节点 `complete`（35→48 / registered 32→19），合并器 `--reapply` 全绿。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== _wave1_apply.py：内容波次合并（13 个节点；来源 = 部件目录 16-checkpoint/_wave4_parts（13 个部件））===\n"
            "   回源引文库：7 个文件 / 126 条唯一引文\n"
            "\n"
            "   [PE-M-01] ★ 重放（节点已 complete；--reapply 已声明）\n"
            "   [PE-M-01] S-0011   tier=official  片段 2/2 回源  A reasoning model is like →A1-official-specs.json；"
            "A GPT model is like a juni→A1-official-specs.json\n"
            "   [PE-M-01] lab 2 条 / evidence 3 条 / pitfalls 4 条\n"
            "   [PE-V-03] ★ 重放（节点已 complete；--reapply 已声明）\n"
            "   [PE-V-03] S-0064   tier=paper     片段 1/1 回源  the LiM effect is stronges→A2-academic-frontier.json\n"
            "   [PE-V-03] lab 2 条 / evidence 3 条 / pitfalls 5 条\n"
            "\n"
            "== 结论：PASS ==（回源、台账注入、长度、结构四项全过）\n"
            "[write] dag.json 已落盘；回读：JSON 合法 / 节点 67 / complete 48 个 "
            "['PE-A-01', 'PE-A-02', 'PE-A-03', 'PE-A-04'," + TRUNC + "\n",
    },
    {
        "id": "C-R9-02",
        "claim": "三门控全 PASS：P01–P41（178 夹具）/ A1–A7（9）/ S1–S11（18），夹具全部触发。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== [full] gate_prototype P01–P41（全量；本机存在 _probe/channel.json ⇒ 含 P38） ===\n"
            "== 门控结论：PASS ==  FAIL 0 项 []\n"
            "=== [full] gate_prototype --selftest（逐条负例） ===\n"
            "== 自检结论：PASS ==（41 条判据 / 178 条负例夹具，全部须正向 PASS 且负例触发）\n"
            "=== [full] 无障碍门控 gate_a11y.py（A1–A7） ===\n"
            "== 门控结论：PASS ==  FAIL 0 项 []\n"
            "=== [full] 无障碍门控 --selftest ===\n"
            "== 自检结论：PASS ==（7 条判据 / 9 条负例夹具）\n"
            "=== [full] 元数据门控 gate_seo_meta.py（S1–S11） ===\n"
            "== 门控结论：PASS ==  FAIL 0 项 []\n"
            "=== [full] 元数据门控 --selftest ===\n"
            "== 自检结论：PASS ==（11 条判据 / 18 条负例夹具）\n",
    },
    {
        "id": "C-R9-03",
        "claim": "两档都真跑：`_ci_gate.sh fast` PASS、`_ci_gate.sh full` **首次** PASS（含 P38/C58 本机口径）。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== _probe/r9_gate_fast.txt：[fast] 档整条通道的结论行 ===\n"
            "== _ci_gate.sh [fast] 结论：PASS ==\n"
            "=== [full] 数据侧自检 ../10-dag-data/_selfcheck.py（输入层在盘上 ⇒ 含 C58 逐片段回源） ===\n"
            "[PASS] C58-quote-provenance evidence 引文逐片段可在引文库逐字回源"
            "（节点侧 159 条 evidence / 库内 126 条唯一引文，源件 7 个；坏：[]）\n"
            "== 自检：PASS ==  (FAIL 0 项 / WARN 4 项)\n"
            "=== [full] P38（本机存在 _probe/channel.json ⇒ full 档照跑，⛔ 不排除） ===\n"
            "manifest `16-checkpoint/_probe/channel.json`（schema pekg/channel-probe/1）；能力声明与事实一致；"
            "实检渲染 8 条（判据自己解码）；横向溢出页/元素 0 处；违例 0 处 []\n"
            "== _ci_gate.sh [full] 结论：PASS ==\n",
    },
    {
        "id": "C-R9-04",
        "claim": "执行通道两缺陷（数据侧自检路径笔误 / P38 对象在 CI 不存在）＋ C58 对象条件，含三项对照实验。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== _probe/r9_baseline_full.txt：[full] 基线档（修前）= FAIL（F1 路径笔误） ===\n"
            "python3: can't open file '/home/zako-mio/opencode/archive/Mission-file/2026-10/"
            "1014-新一代提示词工程知识全景图与教程/04-prototype/16-checkpoint/10-dag-data/_selfcheck.py': "
            "[Errno 2] No such file or directory\n"
            "== _ci_gate.sh [full] 结论：FAIL ==\n"
            "=== _probe/r9_c58_switch_probe.txt：C58 对象条件的三项对照实验 ===\n"
            "=== ① 模拟无输入层 + 不设开关（期望 FAIL / 退出码 1）===\n"
            "python 退出码=1\n"
            "[FAIL] C58-quote-provenance evidence 引文逐片段可在引文库逐字回源"
            "（节点侧 0 条 evidence / 库内 0 条唯一引文，源件 0 个；"
            "坏：[('(引文库)', '01-research/evidence/A*.json 一个都读不到 ⇒ fail-closed')]）\n"
            "== 自检：FAIL ['C58-quote-provenance'] ==  (FAIL 1 项 / WARN 4 项)\n"
            "=== ② 模拟无输入层 + PEKG_INPUT_LIBRARY_ABSENT=1（期望 [SKIP] + PASS / 退出码 0）===\n"
            "python 退出码=0\n"
            "[SKIP] C58-quote-provenance 本 checkout 无输入层（`01-research/evidence/A*.json` 不在盘上） "
            "⇒ 本判据**无对象**；★ 由调用方显式声明（`PEKG_INPUT_LIBRARY_ABSENT=1`），"
            "⛔ 不是静默通过、⛔ 不得读作「引文回源已覆盖」\n"
            "[SKIP] C58b-frontier-quotes 本 checkout 无输入层 ⇒ 该**报告项**无对象"
            "（⛔ 不得读作「frontier 引文已全部回源」）\n"
            "== 自检：PASS ==  (FAIL 0 项 / WARN 3 项)\n"
            "=== ③ 本机（输入层在盘上）+ PEKG_INPUT_LIBRARY_ABSENT=1（期望开关无效、C58 照跑）===\n"
            "python 退出码=0\n"
            "[PASS] C58-quote-provenance evidence 引文逐片段可在引文库逐字回源"
            "（节点侧 159 条 evidence / 库内 126 条唯一引文，源件 7 个；坏：[]）\n"
            "== 自检：PASS ==  (FAIL 0 项 / WARN 4 项)\n",
    },
    {
        "id": "C-R9-05",
        "claim": "图件：13 张成对新增、`--check` 120 件一致、盘上 60 张全合规。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== gen-figs.py --check ===\n"
            "[PASS] 图件 120 件与派生结果一致\n"
            "=== _selfcheck_figs_spec.py ===\n"
            "[OK  ] 盘上真实图件 60 张全部合规（逐一复算，⛔ 不抽样）\n"
            "== 结论：PASS ==（四发合成探针 + 盘上 60 张真实图件；不符 0 处）\n",
    },
    {
        "id": "C-R9-06",
        "claim": "真实渲染 5 张凭证（3 张核对图含 13 图 + 2 页实拍），逐张看过。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== 渲染证据（本机 _render.py，非 snap Chrome）===\n"
            "  r9_sheet_1.png                     1440x2225  440418 B  sha256=7b0e0d7b54d6c242\n"
            "  r9_sheet_2.png                     1440x2437  473446 B  sha256=80fccbe3e5502453\n"
            "  r9_sheet_3.png                     1440x1472  277075 B  sha256=a1b394139b0c71bd\n"
            "  r9_page_pe-p-04.png                1440x5598  1172749 B  sha256=683db8e6c9fdecbb\n"
            "  r9_page_pe-v-03.png                1440x6045  1374746 B  sha256=719e98b0f96f2ed9\n",
    },
    {
        "id": "C-R9-07",
        "claim": "全站通道探针：64 页横向溢出 0（视口 1440×900）。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== _probe/r9_channel_probe.txt：全站横向溢出普查（直接量 scrollWidth − clientWidth） ===\n"
            "== _probe_channel.py：验证通道探测 + 产物非退化读数 ==\n"
            "-- D. 全站横向溢出普查（视口 1440×900；64 页）--\n"
            "   [PASS] 全站 64 页：文档级与元素级横向溢出均为 0\n"
            "== 结论：PASS ==（用时 71.2s；manifest → 16-checkpoint/_probe/channel.json）\n",
    },
    {
        "id": "C-R9-08",
        "claim": "构建幂等：写盘后复跑 `build-all --dry-run`，130 个预期产物的 added / modified / deleted 全 **0**（差集 0/0/0）。",
        "source": "main-agent-rerun",
        "raw_output":
            "=== _probe/r9_build_dryrun.txt：写盘后的幂等复核（第二次 dry-run）= \n"
            "预期产物 130 个文件\n"
            "  added      0\n"
            "  modified   0\n"
            "  deleted    0\n"
            "=== _probe/r9_build_write2.txt：上一次写盘的落盘读数（同批在册，供对照）= \n"
            "  实际写入 2 个 / 实际删除 0 个 / 孤儿残留 0 个\n"
            "  二次比对干净：True\n",
    },
]

# claim id → raw_output 的**逐字**来源件（⛔ 不得凭空写；见 docstring 的自证段）
RAW_SOURCES = {
    "C-R9-01": ["r9_apply_reapply2.txt"],
    "C-R9-02": ["r9_final_full.txt"],
    "C-R9-03": ["r9_gate_fast.txt", "r9_final_full.txt"],
    "C-R9-04": ["r9_baseline_full.txt", "r9_c58_switch_probe.txt"],
    "C-R9-05": ["r9_figs_check.txt"],
    "C-R9-06": ["r9_render_evidence.txt"],
    "C-R9-07": ["r9_channel_probe.txt"],
    "C-R9-08": ["r9_build_dryrun.txt", "r9_build_write2.txt"],
}

ARTIFACTS = [
    "04-prototype/10-dag-data/dag.json",
    "04-prototype/10-dag-data/figures/",
    "04-prototype/11-node-pages/",
    "04-prototype/15-md/nodes/",
    "04-prototype/10-dag-data/_selfcheck.py",
    "04-prototype/16-checkpoint/_ci_gate.sh",
    "04-prototype/16-checkpoint/gate-manifest.json",
    "04-prototype/16-checkpoint/gate_prototype.py",
    "04-prototype/16-checkpoint/gen-figs.py",
    "04-prototype/16-checkpoint/gen-nodes.py",
    "04-prototype/16-checkpoint/gen-state.py",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R09.md",
    "04-prototype/PUBLISH-STATE.json",
    "04-prototype/README.md",
    ".gitignore",
]

G_LIST = {
    "G1": "✅ 已消（第 1 轮）· 第 9 轮复跑仍 PASS：R-10 的判据 = P35 ⑨ —— 命中枚举模式的页 **12** 个 / "
          "`.enum-list` 12 个（本轮 8→12：新增 13 节点带来 4 页）。★ 本轮在 ⑨ 上只做**内容侧**处置（见 `G51`），"
          "⛔ 未放宽判据。",
    "G2": "✅ 已消（第 1 轮）· 第 9 轮复跑仍 PASS：R-11 的判据 = P35 ⑩ —— 竖表区块实检 **96** 个（本轮 70→96），"
          "区内 `<table>` 0。",
    "G3": "✅ 已消（第 1 轮）· 第 9 轮复跑仍 PASS：R-16 的判据 = P37 —— 组节点 11 / 组间边 25 / "
          "包围盒 763.0 x 591.0 ⊆ 可用 768 x 604 ⇒ zoom 1.0000、最小间隙 25.0px、违例 0。",
    "G4": "未动（本轮不涉）：P35 ⑪–⑭ 的读数随 P35 全量跑出（违例 0），本轮未改这几条判据。"
          "★ 阈值边界探针 `_selfcheck_p35_fixtures.py` 本轮**未留证据件**（`_probe/r9_*` 清单里没有它）"
          "⇒ 按 `G50` 的判别句（没有它自己跑出来的原始输出件 ＝ 没跑过），⛔ 不写成「已复跑」。",
    "G5": "★ 第 9 轮**刷新证据**：真实渲染通道重跑 —— `_probe_channel.py` 8 张全部 PASS（64 页横向溢出 0）；"
          "本机 `_render.py` 另出 **5 张**凭证（3 张核对图 + 2 页实拍），逐张看过（见 claim C-R9-06 / C-R9-07）。",
    "G6": "✅ 已消（第 4 轮修 `pre` 换行）· 第 9 轮 **64 页**复测仍 0：全站文档级与元素级横向溢出均为 0"
          "（⛔ 未放宽 P38）。",
    "G7": "✅ 已消（第 4 轮补登记件）· 第 9 轮 P39 复跑仍 PASS：引用点 3 处 / 被引用登记件 **13** 个"
          "（本轮新增 `CRITERIA-CHANGE-R09.md`）/ 磁盘登记件 13 个 / 结构化出口键 13 个；断链 0 / 孤儿 0。",
    "G8": "**仍在**（留行）：长文可扫性**不可机检** ⇒ 仍为 P35 报告项。本轮读数：受检页 **62**、"
          "最长 130（`12-groups/g01.html`）、> 110 的页 2 个 [('12-groups/g01.html', 130), "
          "('11-node-pages/pe-m-02.html', 121)]；⛔ 不判 FAIL。",
    "G9": "**仍在（第 9 轮未动）**：窄视口交互图 zoom < 1（`canvas_768` cyW 718 ⇒ 视口 768 时 0.8755）。"
          "P37 的 `zoom=1` 只在**声明画布**口径下成立。",
    "G10": "★ 第 9 轮增量：`PUBLISH-STATE.gates` 新增结构化出口键 `criteria_change_R09` ⇒ 结构化出口键 "
           "12 → **13**，与磁盘登记件 13 个、三处引用 13 个**双向闭合**（P39 实测）。`gates.prototype` "
           "仍为 P01–P41（本轮判据数未变）。",
    "G11": "**保留更正（第 5/6 轮）**：能力集是**逐进程读数**、⛔ 不可跨会话沿用。★ 第 9 轮复跑 "
           "`_probe_channel.py` 读到 `CapPrm/CapEff = 0000000000000000`、`CapBnd = 000001ffffffffff`、"
           "`NoNewPrivs = 1` ⇒ 只作**该次运行**的读数，⛔ 不写成「本会话」。",
    "G12": "✅ 已消（第 6 轮，挂在 P13）· 第 9 轮 `counts` 逐项 **13** 项全现算，违例 0。",
    "G13": "✅ 已消（第 6 轮，挂在 P13）· 第 9 轮镜像内容比对 **535** 项（本轮 384→535），违例 0"
           "（缺镜像由上方断言负责）。",
    "G14": "✅ 已消（第 6 轮 → 数据侧 C58）· 第 9 轮本机 C58 **PASS**（159 条 evidence / 126 条唯一引文 / "
           "7 个源件）。★ 但它在本机之外的 checkout 上**被显式声明为无对象**（`G49`）⇒ "
           "⛔ 不得读作「引文回源已在 CI 覆盖」。",
    "G15": "✅ 已消（第 8 轮）· 本轮未动：发布级强化与建仓发布已于第 8 轮落地并线上验证。"
           "★ 跨仓议题（本站 `--border` 对底色 1.0:1 / 1.06:1）仍在，⛔ 不属本仓。",
    "G16": "**仍未解决（第 9 轮取证失败）**：`PE-C-03`（图检索/GraphRAG）与 `PE-C-06`（提示缓存）在源池"
           "**无源可依** —— 本轮派出的 `oc_search` worker **无网络出口**且无写工具 ⇒ 取证**失败**、"
           "⛔ **未编造引文**；主 Agent 侧 `web_fetch` 可用（详见 `G55`）。G16 仍开。",
    "G17": "未动（本轮不涉）：契约 §4③ 标题「六步」与其下命令块条数一致（第 7 轮已修）。",
    "G18": "第 9 轮逐项：⑧ P35 ⑫ 代理判据仍未退役（留行）；⑨ 分组索引 6 列短值表仍未被判据覆盖（留行）；"
           "⑩ 组页 `intro` 无枚举模式（留行）；⑪ P40 只断结构、如实性不可机检（明文登记）；"
           "⑫ P38 不判 PNG 新鲜度（留行）；⑬ `report.html` 的 `<title>` 仍写「第 1 轮」（**刻意不改**，"
           "属历史原文）；⑭ A/S 两段是两个独立脚本、漏调其中一个**无任何报警**（**本轮未做**，见 "
           "`CRITERIA-CHANGE-R09.md` §4）；⑮ `gate-manifest.json` 自身无判据校验编号集合与实现一致"
           "（**本轮未做**，同上）；⑯ `_probe/` 目录无判据管辖（留行）—— ★ 但本轮把「`_probe/` 整层不入库」"
           "这一**直接原因**写进了 `gate-manifest.json` 的 `not_covered` 归因与 `_ci_gate.sh` 的对象条件"
           "（`G47`/`G48`），清单与实现的漂移**少一处**、⛔ 不假装该缺口已堵。",
    "G19": "✅ 已消（第 6 轮，用户裁决 B″）· 本轮未动：R-07 作用域 = 知识承载页（节点页 / 组页）；"
           "本轮 13 个新节点页全部有图（P35 ⑧ 违例 0）。",
    "G20": "✅ 已消（第 6 轮 → 判据 P41）· 第 9 轮复跑：扫描面 **38** 个（豁免 1）、历史句命中 **9** 行"
           "（有正当出处 9）、违例 0。★ 本轮新增 `_r9_ledger_update.py` 后顶层 `*.py` 将达 **40** 个"
           "（扫描 39：本脚本 ⛔ 不含该历史句，`main()` 有自检）。",
    "G21": "✅ 已修（第 5 轮）· 本轮未动：内容列口径 = `.layout > main` 的 border-box 内宽 804px，"
           "与 P34/P36 的复算一致。",
    "G22": "✅ 已消（第 6 轮）· 本轮未动：判据 / 契约 / 产物同批的纪律保持不变。",
    "G23": "**未解决（留行）**：`C58` 的对象只有节点侧；`frontier.json` 侧 **2** 片引文仍无法在 A 池逐字回源"
           " ⇒ 本轮 `C58b` 仍以 WARN 常驻（终读数 WARN 4 项之一），⛔ 未改 `frontier.json`。",
    "G24": "✅ 已消（第 6 轮）· 本轮未动：图件规格两侧探针四发全绿，盘上 **60** 张逐张合规（⛔ 不抽样）。",
    "G25": "**未解决（第 9 轮未动）**：`P41` 仍是**窄版**（⛔ 不判「任何措辞」）。",
    "G26": "未动（本轮不涉）：`R-25` 的可机检部分不变；「是否真按三件套走」仍**不可机检**。",
    "G27": "✅ 已修（第 6 轮）· 本轮未动：合并器本轮以 `--reapply` 重放 13 个部件，回源/台账/长度/结构"
           "四项校验全过（见 claim C-R9-01）。",
    "G28": "✅ 已消（第 7 轮，用户裁决 N1）· 本轮未动：P35 ② 违例 0 —— h1 含 ≥3 字母拉丁 token 的页 "
           "**3** 个，其 token 全部在 `glossary.json` 逐字命中；13 个新节点页均未触发该条。",
    "G29": "未动（本轮不涉）：机检边界不变 —— P40 报不出「行文里的数字与事实不符」。",
    "G30": "未动（本轮不涉）：动某文件前先确认其写者已停手的纪律不变。",
    "G31": "✅ 已消（第 8 轮）· 本轮未动：`R-08` 的内容列口径已写入契约 R-08 行。",
    "G32": "**已处置（留行以免被读作已消）**：审核/取证委派的**工具面**须与任务匹配。★ 第 9 轮**再次撞上"
           "同型**：取证委派（`oc_search` worker）既**无网络出口**也无写工具 ⇒ 属**委派权限面缺陷**"
           "（详见 `G55`）⇒ 该纪律需要写进委派模板，⛔ 不能只靠叮嘱。",
    "G33": "**仍在（第 9 轮未动）**：`_wave_pick_quotes.py` 的 URL→id 映射假阴性（`setdefault` 建索引）。"
           "判「引文可用性」仍应以 `_wave1_apply.py` 的 dry-run 为准。",
    "G34": "未动（本轮不涉）：夹具随产物演变成假夹具的教训不变；本轮 178 条夹具**全部触发**（自检原文在册）。",
    "G35": "未动（本轮不涉）：内部标注记号纪律不变；P33 本轮 64 页可见文案命中 0 处。",
    "G36": "未动（本轮不涉）：顶层临时 `.py` 的卫生纪律不变；本轮临时件全部落在 `_probe/`。",
    "G37": "未动（本轮不涉）：清理脚本只许匹配自己前缀的纪律不变。",
    "G38": "**仍在（第 9 轮未动）**：`PE-E-03` / `PE-A-05` 的核心机制句在引文库中无一手可引用原文；"
           "本轮 ⛔ 未改数据、⛔ 未编造。",
    "G39": "**仍在（第 9 轮未扩面）**：任务根的两个探针与 `_probe/` 下的脚本仍不在 P41 扫描面内；"
           "本轮 `_probe/r9_*` 又新增多件（取证/探针/渲染凭证）⇒ 留行。",
    "G40": "未动（本轮不涉）：游离物证已登记在 `_probe/README.md` §三。",
    "G41": "未动（本轮不涉）：`_r6_backup/` 的边界登记已补，本轮未再生新的快照目录。",
    "G42": "★ **第 9 轮被加强**（本轮最值钱的一条）：第 8 轮的认识是「判据对象 ≠ 断言对象」；本轮三条新缺陷"
           "（`G47`/`G48`/`G49`）把它推进为 —— **判据的对象不只存在于产物里，也存在于「执行环境」里**："
           "同一条判据在**本机**与**CI**上是**两个扫描面**（`_probe/` 与 `01-research/` 按 `.gitignore` "
           "整层不入库）。⇒ 判别句：*这条判据读的东西，在 CI 的 checkout 里存在吗？*",
    "G43": "★ **第 9 轮升级为加强版**：第 8 轮说「fast ≠ full，所以两档都要真跑」；本轮实证"
           "**同档不同环境也 ≠** —— `_ci_gate.sh full` 这条通道**从未被行使**（第 8 轮只留下 fast 档证据件），"
           "它的两条**恒 FAIL** 缺陷因此潜伏了一整个发布周期（`G50`）。⇒ 说「某档绿」必须**指明环境**。",
    "G44": "✅ 已处置（第 8 轮）· 本轮未动：本轮临时件全部落在 `_probe/`。",
    "G45": "未动（本轮不涉）：临时只读参照物须显式告知删除时点的纪律不变。",
    "G46": "**仍在（装置欠账，本轮未削）**：`build_probes()` 仍真跑 **4 次** `build-all` 子进程 ⇒ 一次全量门控"
           "要跑 5 遍生成链路。★ 第 9 轮 `full` 档**首次真跑**，这笔开销第一次落在同一条通道上（未做优化）。",
    "G47": "★ **第 9 轮新增（装置缺陷，已修）**：`_ci_gate.sh` 数据侧自检**路径笔误** —— 脚本已 `cd` 到 "
           "`16-checkpoint/`，该步仍写 `10-dag-data/_selfcheck.py`（相对**发布根**的路径）⇒ `full` 档"
           "**恒 FAIL**（连 C01–C58 共 61 条一条都没跑成）。已修为 `../10-dag-data/_selfcheck.py`"
           "（`CRITERIA-CHANGE-R09.md` §3.1）。★ 效果是**断言面扩大**（数据侧自检终于真被这条通道行使），"
           "⛔ 不是放宽。",
    "G48": "★ **第 9 轮新增（声明与实现相反，已修）**：P38 的对象 `_probe/channel.json` 在 CI **不存在**"
           "（`.gitignore` 规则②把过程证据整层排除）⇒ 判据与其负例夹具**双双 FAIL**、CI full 档恒 FAIL"
           "（线上 `schedule` run `39225734249` 即此形态）。⇒ 已改为**显式排除 + 打印理由**"
           "（`FULL_P38_NOTRUN_REASON`）：对象在盘上 ⇒ 照跑全量 P38；不在 ⇒ `--only`（P01–P41 减 P38）"
           "并打印理由。⛔ P38 的断言**一个字节未动**；⛔ CI 全绿不得读作「像素层已验证」"
           "（`CRITERIA-CHANGE-R09.md` §3.2）。",
    "G49": "★ **第 9 轮新增（同族第二条，已声明）**：C58 依赖 `01-research/evidence/A*.json`（`.gitignore` "
           "规则①整层排除）且 **fail-closed** ⇒ **修好 `G47` 的当天**它就会红。⇒ 已改为**显式声明**："
           "本机（输入层在盘上）照跑且必须 PASS；新 checkout 且调用方显式 `PEKG_INPUT_LIBRARY_ABSENT=1` ⇒ "
           "打印 `[SKIP]` 并给理由；未声明 ⇒ 仍 **FAIL**（fail-closed 语义保留）。三项对照实验在册"
           "（`_probe/r9_c58_switch_probe.txt`，见 claim C-R9-04）。★ 排除面精确到**判据**、⛔ 不整步豁免"
           "（否则 C01–C57 共 57 条会一并跑不成）。",
    "G50": "★ **第 9 轮新增（本轮最刺的一条）**：第 8 轮报告称「两档都真跑过」，但 `_probe/` 只有 **fast 档**"
           "证据件（`r8_t3_ci_gate_fast.txt`），**full 档实测跑不过**（`G47`/`G48` 两条恒 FAIL）。"
           "⇒ **装置没跑 ＝ 没验证**：一条执行通道若从未被行使，它的正确性**没有任何判据**。"
           "判别句：*这条档/通道，有没有留下过它自己跑出来的原始输出件？*",
    "G51": "★ **第 9 轮新增（判据对象 > 渲染器覆盖面）**：P35 ⑨ 的判据只判「`其[一二三四五六七八九十]，` "
           "模式是否出现」，而渲染器 `split_enum` 要求**同句 ≥2 个分号项**才出 `.enum-list` ⇒ 判据点得亮、"
           "渲染器却不生成列表（判据绿而版面没动）。⇒ 本轮以**改内容**（把分项并成同句）处置，"
           "⛔ **未放宽判据**；渲染器侧仍留行（该面仍未被判据覆盖）。",
    "G52": "★ **第 9 轮新增（图注与正文口径不一致，已同批修）**：`pe-v-01` / `pe-v-03` 的**图内文字**把"
           "**文本侧**实测写成**多模态既成事实** ⇒ 已同批修图注 + 图内文字（图与正文口径对齐）。",
    "G53": "★ **第 9 轮新增（登记不改）**：`pe-p-07` 图内「五面」vs 正文「四处」—— 这是**两种切法**"
           "（同一材料的两个归纳粒度），**非事实错误** ⇒ **登记不改**。",
    "G54": "★ **第 9 轮新增（存量缺口，留行）**：`pe-f-06` 的 `FIGS.caption` 与 `NODE_FIG` 图注**不同文**"
           "（存量、非本波产物）⇒ 登记留行，本轮不改。",
    "G55": "★ **第 9 轮新增（委派权限面缺陷）**：`oc_search` worker 本会话**无网络出口**且**无写工具** ⇒ "
           "G16 取证**失败**（⛔ 未编造引文）；主 Agent 侧 `web_fetch` 可用 ⇒ 属**委派权限面**缺陷"
           "（与 `G32` 同族），G16 仍开。",
}

NOTE = (
    "★ 本对象是**第 9 轮（内容波次 4 = 13 个节点 + 13 张成对图档（26 件）→ 收口期第一次真的行使 "
    "`_ci_gate.sh full` 这条执行通道，并当场翻出两条恒 FAIL 缺陷）**的轮次对象：采用"
    "**收口期一次性落盘**（与第 7/8 轮同口径；见下「偏离登记」）。\n"
    "★ 本轮读数全部由**主 Agent 亲跑**（`main-agent-rerun`，逐条附原始输出，原件落 "
    "`16-checkpoint/_probe/r9_*.txt`）；8 条 claim 的 `raw_output` 由 `_r9_ledger_update.py` "
    "**逐行回源校验**（口径：`===` 开头的行是节标签、不参与比对；其余行必须**逐字（空白归一化）**"
    "出现在声明的 `_probe/` 源件里，长行可截断但只校验其左侧前缀）。\n"
    "★ **本轮末态读数**：complete **48** / registered **19**（合计 67 = 全量注册数）· 发布面 **64** 页"
    "（HTML 64 / MD 64）· 图件 **60** 张（`gen-figs --check` 派生件 **120** 件一致）· 判据 **41** 条 / "
    "负例夹具 **178** 条 · A1–A7（7 条 / 9 夹具）· S1–S11（11 条 / 18 夹具）· 门控登记件 **13** 件 · "
    "生成产物 **130** 个。\n"
    "★ **有一路委派产出的取证结论不予采用**：`oc_search` worker 本会话**无网络出口**且**无写工具** ⇒ "
    "G16 取证**失败**，⛔ 未编造任何引文（见 `G55`）。★ 内容侧按 `R-25` 走「并行产出部件 → 机器合并 → "
    "主 Agent 复跑」（部件目录 `16-checkpoint/_wave4_parts`，13 个部件；合并与四项校验的原始输出见 "
    "claim C-R9-01）；★ 本轮 8 条 claim 的读数**无一**来自委派方自报 —— 全部由主 Agent 亲跑并留原始输出件。\n"
    "★ **偏离登记**：契约 §4① 第 3 条要求「开工期先落盘 `rs_touched`」，本轮（与第 7/8 轮同）采用"
    "**收口期一次性落盘** —— 开工时确实还不知道会触碰哪些 R-xx（本轮开工后的第一个动作是跑基线 `full` 档，"
    "它把 R-20/R-21/R-22/R-23 的触碰面一次性打开）。★ 该项自第 7 轮起登记为待裁决，本轮**仍未裁决**，"
    "如实续留。\n"
    "★ **本轮的定位**：把内容从 35 推到 48（知识库主体过半），并第一次让「分档 CI 的 full 档」这条"
    "**执行通道**真的被行使 —— 代价是当场承认第 8 轮「两档都真跑过」这句话**没有证据件**（`G50`）。"
    "⇒ 本轮最值钱的认识不是新增了什么，而是 **「装置没跑 = 没验证」**：恒 FAIL 与恒真一样，"
    "都能潜伏一整个发布周期（因为没人看每周一的那条红）。"
)


def build_round():
    return {
        "round": 9,
        "started_at": STARTED,
        "ended_at": ENDED,
        "rs_touched": RS_TOUCHED,
        "claims": CLAIMS,
        "artifacts": ARTIFACTS,
        "g_list_updates": G_LIST,
        "note": NOTE,
    }


# ---------------------------------------------------------------- 守卫与预校验

def _norm(s):
    """空白归一化（与 P13 的 G13 镜像比对同口径）：只压空白，⛔ 不动任何字词。"""
    return re.sub(r"\s+", " ", s).strip()


def _hit(line, pool):
    """该行是否**逐字**出自源件；带 `…（截断）` 时只校验其左侧前缀。"""
    n = _norm(line)
    if n in pool:
        return True
    if n.endswith(TRUNC.strip()):
        head = n[:-len(TRUNC.strip())].rstrip()
        return bool(head) and any(p.startswith(head) for p in pool)
    return False


def check_raw_sources(claims):
    """★ 第 9 轮的自证：raw_output 必须是声明的 `_probe/` 源件的逐字截取（⛔ 不接受转述）。"""
    used, nlines = [], 0
    for c in claims:
        files = RAW_SOURCES.get(c["id"])
        if not files:
            raise SystemExit("[FAIL] %s 未声明 raw_output 的来源件" % c["id"])
        pool = set()
        for fn in files:
            p = os.path.join(PROBE, fn)
            if not os.path.isfile(p):
                raise SystemExit("[FAIL] %s 声明的来源件不存在：_probe/%s" % (c["id"], fn))
            with open(p, encoding="utf-8") as fh:
                for ln in fh:
                    pool.add(_norm(ln))
            used.append("_probe/" + fn)
        body = [ln for ln in c["raw_output"].split("\n")
                if ln.strip() and not ln.lstrip().startswith("===")]
        if not body:
            raise SystemExit("[FAIL] %s 的 raw_output 只有节标签、没有任何原始输出行" % c["id"])
        miss = [ln for ln in body if not _hit(ln, pool)]
        if miss:
            raise SystemExit("[FAIL] %s 的 raw_output 有 %d 行不是来源件的逐字截取（首行：%r）"
                             % (c["id"], len(miss), miss[0][:100]))
        nlines += len(body)
    return used, nlines


def guards(raw_before, raw_after):
    """⛔ 只允许在末尾追加：历史轮次的内容必须逐字节（语义）相同，且原来 N 个轮次、现在 N+1。"""
    b, a = json.loads(raw_before), json.loads(raw_after)
    if b["schema"] != a["schema"]:
        raise SystemExit("[FAIL] schema 被改动")
    rb, ra = b["rounds"], a["rounds"]
    if [r["round"] for r in rb] != [r["round"] for r in ra[:len(rb)]]:
        raise SystemExit("[FAIL] 历史轮次的 round 编号序列被改动")
    if json.dumps(rb, ensure_ascii=False, sort_keys=True) != \
       json.dumps(ra[:len(rb)], ensure_ascii=False, sort_keys=True):
        raise SystemExit("[FAIL] 历史轮次对象**内容**被改动（guards 拒绝）")
    if len(ra) != len(rb) + 1:
        raise SystemExit("[FAIL] 轮次数不是 +1")
    if ra[-1].get("round") != 9:
        raise SystemExit("[FAIL] 追加的轮次不是 round 9")


def preflight(rnd):
    raw = open(LEDGER, encoding="utf-8").read()
    doc = json.loads(raw)
    if doc.get("schema") != SCHEMA:
        raise SystemExit("[FAIL] schema 不匹配：%r" % doc.get("schema"))
    if any(r["round"] == 9 for r in doc["rounds"]):
        raise SystemExit("[FAIL] 已存在 round 9 对象 ⇒ 本脚本只负责**首次**追加（⛔ 不覆盖）")
    seq = [r["round"] for r in doc["rounds"]]
    if len(seq) < 5 or seq != sorted(seq) or len(set(seq)) != len(seq) or seq[-1] != 8:
        raise SystemExit("[FAIL] 既有轮次编号序列不合预期（须严格递增、末条为 round 8）：%r" % seq)

    # ① R-id：必须逐条落在契约规则表里（★ 与契约同源，⛔ 不写死）
    contract = open(os.path.join(HERE, "DESIGN-CONTRACT.md"), encoding="utf-8").read()
    ids = set(re.findall(r"^\| (R-\d\d) \|", contract, re.M))
    if len(ids) < 20:
        raise SystemExit("[FAIL] 契约规则表只扫到 %d 个 R-id ⇒ 预校验失效（fail-closed）" % len(ids))
    if not rnd["rs_touched"]:
        raise SystemExit("[FAIL] rs_touched 为空")
    if len(set(rnd["rs_touched"])) != len(rnd["rs_touched"]):
        raise SystemExit("[FAIL] rs_touched 有重复项")
    bad = [x for x in rnd["rs_touched"] if x not in ids]
    if bad:
        raise SystemExit("[FAIL] rs_touched 含契约规则表外的 id：%r" % bad)

    # ② claims：P40 的四项 + 本轮的「id 齐备且连续」+ 逐字回源
    want = ["C-R9-%02d" % i for i in range(1, 9)]
    if [c["id"] for c in rnd["claims"]] != want:
        raise SystemExit("[FAIL] claim id 不是 C-R9-01..08 连续：%r" % [c["id"] for c in rnd["claims"]])
    for c in rnd["claims"]:
        if c["source"] not in ("self-report", "main-agent-rerun"):
            raise SystemExit("[FAIL] claim.source 非法：%r" % c["source"])
        if not (c.get("claim") or "").strip():
            raise SystemExit("[FAIL] %s 缺 claim 正文" % c["id"])
        if not c["raw_output"].strip():
            raise SystemExit("[FAIL] %s 缺 raw_output" % c["id"])
        if c["source"] == "main-agent-rerun" and "===" not in c["raw_output"]:
            raise SystemExit("[FAIL] %s 的 raw_output 缺原始输出标记 `===`" % c["id"])
    used, nlines = check_raw_sources(rnd["claims"])

    # ③ artifacts：逐条为相对路径且**在盘上真存在**（fail-closed）
    if not rnd["artifacts"]:
        raise SystemExit("[FAIL] artifacts 为空")
    for p in rnd["artifacts"]:
        if os.path.isabs(p):
            raise SystemExit("[FAIL] artifacts 里出现绝对路径：%r" % p)
        if not os.path.exists(os.path.join(ROOT, p)):
            raise SystemExit("[FAIL] artifacts 里登记的路径在盘上不存在：%r" % p)

    # ④ g_list_updates：键必须是 G1..G55 连续（⛔ 不得漏行、不得跳号）
    gkeys = list(rnd["g_list_updates"])
    if gkeys != ["G%d" % i for i in range(1, len(gkeys) + 1)]:
        raise SystemExit("[FAIL] g_list_updates 的键不是 G1..G%d 连续：%r" % (len(gkeys), gkeys[:6]))
    if any(not str(v).strip() for v in rnd["g_list_updates"].values()):
        raise SystemExit("[FAIL] g_list_updates 有空行（每行必须有本轮处置）")

    # ⑤ 自证：本脚本 ⛔ 不含 P41 扫描面的历史句（★ 拆成两段写，避免自己成为命中源）
    me = open(os.path.abspath(__file__), encoding="utf-8").read()
    hist = "本会话" + "浏览器不可用"
    if hist in me:
        raise SystemExit("[FAIL] 本脚本自身含 P41 扫描面的历史句 ⇒ 会被判违例（拒绝落盘）")

    return raw, doc, len(ids), used, nlines


def simulate_p40(doc, contract_rids):
    """★ 按 **P40** 的四项断言在**手术后的文档**上预演（⛔ 不跑 gate；只复刻同一组断言）。

    复刻的四项：① 每轮 round 为正整数 + 开工/收口时点齐备；② `rs_touched` 非空且逐条合法并落在契约
    规则表里；③ `artifacts` 非空；④ 每条 claim 的 `source` 合法、`raw_output` 非空、`main-agent-rerun`
    必须带 `===`。⇒ 本函数只回答「落盘后 P40 的结构面会不会红」，⛔ 不回答「自述是否如实」。
    """
    bad, nclaims = [], 0
    for r in doc["rounds"]:
        rid = r.get("round")
        if not isinstance(rid, int) or rid < 1:
            bad.append(("round", "轮次号非法：%r" % rid))
        if not (r.get("started_at") and r.get("ended_at")):
            bad.append(("round %s" % rid, "缺 started_at / ended_at"))
        rs = r.get("rs_touched") or []
        if not rs:
            bad.append(("round %s" % rid, "rs_touched 为空"))
        for x in rs:
            if not re.match(r"^R-\d{2}$", str(x)) or x not in contract_rids:
                bad.append(("round %s" % rid, "R-id 非法或不在契约规则表内：%r" % x))
        if not (r.get("artifacts") or []):
            bad.append(("round %s" % rid, "artifacts 为空"))
        claims = r.get("claims") or []
        if not claims:
            bad.append(("round %s" % rid, "claims 为空"))
        for c in claims:
            nclaims += 1
            src = c.get("source")
            if src not in ("self-report", "main-agent-rerun"):
                bad.append(("round %s" % rid, "claim.source 非法：%r" % src))
            if not (c.get("raw_output") or "").strip():
                bad.append(("round %s" % rid, "claim 缺 raw_output"))
            elif src == "main-agent-rerun" and "===" not in c["raw_output"]:
                bad.append(("round %s" % rid, "main-agent-rerun 的 raw_output 无 `===`"))
    return bad, nclaims


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    rnd = build_round()
    raw, doc, n_rid, used, nlines = preflight(rnd)

    print("  预校验：R-id %d 个全部合法 · claims %d 条 · artifacts %d 项 · G 行 %d 行"
          "（source/raw_output 齐备 · raw_output 共 %d 行逐字回源到 %d 个源件 · artifacts 全部在盘）"
          % (len(rnd["rs_touched"]), len(rnd["claims"]), len(rnd["artifacts"]),
             len(rnd["g_list_updates"]), nlines, len(set(used))))
    print("  契约 R-id 全集 %d 个；既有轮次 %s（%d 条）"
          % (n_rid, [r["round"] for r in doc["rounds"]], len(doc["rounds"])))

    # ---- 文本手术：只在本文件末尾的 `]` 之前插一条，其余字节一个不动 ----
    tail = "\n ]\n}"
    if not raw.endswith(tail + "\n"):
        raise SystemExit("[FAIL] 文件末尾形态与预期不符，拒绝文本手术（fail-closed）")
    body = json.dumps(rnd, ensure_ascii=False, indent=1)
    shifted = "\n".join("  " + ln for ln in body.split("\n"))
    cut = len(raw) - len(tail) - 1
    new_raw = raw[:cut] + ",\n" + shifted + tail + "\n"

    guards(raw, new_raw)
    # 手术后的别 parse 回来必须与本对象**逐字段相等**（防文本拼接把内容写丢/写串）
    back_last = json.loads(new_raw)["rounds"][-1]
    want_last = json.loads(json.dumps(rnd, ensure_ascii=False))
    if json.dumps(back_last, ensure_ascii=False, sort_keys=True) != \
       json.dumps(want_last, ensure_ascii=False, sort_keys=True):
        raise SystemExit("[FAIL] 文本手术后的第 9 轮对象与内存对象不等（内容在拼接中走样）")
    if new_raw[:cut] != raw[:cut]:
        raise SystemExit("[FAIL] 前缀字节被改动（字节级守卫）")
    h_before = hashlib.sha256(raw[:cut].encode("utf-8")).hexdigest()[:16]
    h_after = hashlib.sha256(new_raw[:cut].encode("utf-8")).hexdigest()[:16]
    if h_before != h_after:
        raise SystemExit("[FAIL] 前缀 sha256 不一致（%s ≠ %s）" % (h_before, h_after))
    print("  文本手术：前缀 %d 字节逐字节相同（sha256 %s）· 新增轮次对象 %d 字节 · 文件 %d → %d 字节"
          % (cut, h_before, len(shifted), len(raw), len(new_raw)))
    print("  守卫：schema 一致 · 历史轮次 %d 条内容零改动 · 轮次数 %d → %d · 末尾形态 fail-closed 已过"
          % (len(doc["rounds"]), len(doc["rounds"]), len(doc["rounds"]) + 1))

    # ---- P40 预演（在手术后的文档上复刻同一组结构断言；⛔ 不跑 gate_prototype）----
    contract_rids = set(re.findall(r"^\|\s*(R-\d\d)\s*\|",
                                   open(os.path.join(HERE, "DESIGN-CONTRACT.md"),
                                        encoding="utf-8").read(), re.M))
    bad, nclaims = simulate_p40(json.loads(new_raw), contract_rids)
    if bad:
        raise SystemExit("[FAIL] 落盘后 P40 的结构面会红（%d 处，首处 %r）⇒ 拒绝落盘" % (len(bad), bad[0]))
    print("  P40 预演（手术后）：轮次 %d 条 / claims %d 条 / 契约 R-id 全集 %d 个 / 结构违例 0 处"
          % (len(json.loads(new_raw)["rounds"]), nclaims, len(contract_rids)))

    if a.write:
        with open(LEDGER, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_raw)
        back = json.load(open(LEDGER, encoding="utf-8"))
        last = back["rounds"][-1]
        print("  回读：JSON 合法 · 轮次 %s · round %d claims %d 条 · artifacts %d 项 · G 行 %d 行"
              % ([r["round"] for r in back["rounds"]], last["round"], len(last["claims"]),
                 len(last["artifacts"]), len(last["g_list_updates"])))
        print("  == 结论：已落盘 ==")
    else:
        print("  == 结论：dry-run，⛔ 未写盘 ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
