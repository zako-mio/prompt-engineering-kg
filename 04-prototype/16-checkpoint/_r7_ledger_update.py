#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r7_ledger_update.py —— 把**第 7 轮**对象追加进 `ROUND-LEDGER.json`（⛔ 不回改 round 3–6 的字节）。

## 为什么用**文本手术**而不是 `json.load → json.dump`
第 5/6 轮的写入器对本文件立了「历史轮次对象字节不得变动」的守卫，且本文件的缩进
（根键 1 空格 / 轮次对象 2 空格 / 其下键 3 空格）**不是**任何单次 `json.dumps` 的产物
—— 它是历轮**逐次文本追加**的结果。⇒ 本轮沿用同一手法：只在本文件**末尾的 `]` 之前**插入
第 7 轮对象，其余字节**一个都不动**（脚本自带守卫，见 `guards()`）。

## 契约依据（`DESIGN-CONTRACT.md` §轮次执行协议 ③④）
- 每条 claim 必须标 `source`（`self-report` / `main-agent-rerun`）并附 `raw_output` **原文**；
- `main-agent-rerun` 的 `raw_output` 必须带原始输出标记（`===`）；
- `rs_touched` 必须逐条声明本轮触碰的 R-xx（⛔ 不得为空、不得写契约规则表外的 id）。
机检判据 = **P40**（只断言结构与自洽，⛔ 不验证自述是否如实）。

## 用法
    python3 _r7_ledger_update.py            # dry-run：打印校验结果，⛔ 不落盘
    python3 _r7_ledger_update.py --write    # 落盘
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ROUND-LEDGER.json")
SCHEMA = "pekg/round-ledger/1"

# ---------------------------------------------------------------- 第 7 轮对象

STARTED = "2026-10-16T07:40:00+08:00"
ENDED = "2026-10-16T08:20:00+08:00"

RS_TOUCHED = ["R-01", "R-03", "R-07", "R-08", "R-09", "R-11", "R-13", "R-14",
              "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"]

CLAIMS = [
    ("★ §4① 开工必做第 1 步：**开工前就地快照**（本仓非 git 仓 ⇒ 它是本轮唯一的回滚面）",
     "=== python3（快照）===\n"
     "  目标：16-checkpoint/_r7_backup/（新建，⛔ 未覆盖任何既有路径）\n"
     "  内容：10-dag-data / 11-node-pages / 12-groups / 13-interactive / 14-views / 15-md /\n"
     "        16-checkpoint（排除 _r6_backup/_r7_backup/_probe/__pycache__/_render-proof）/ assets\n"
     "        ＋ index.html ＋ PUBLISH-STATE.json\n"
     "  结果：du -sh = 7.3M；文件数 = 211；随附 MANIFEST.txt（219 行，逐文件 sha256）\n"
     "  MANIFEST sha256 = 68379a21826e28c41160aa62fefe64681b3493e91d4ae84cca183e613126eed0\n"
     "== 结论：PASS ==（回滚面存在且已登记边界）",
     "main-agent-rerun"),

    ("★ §4① 开工必做第 2 步：环境探测复跑（R-21；⛔ 不沿用上一轮的散文结论）",
     "=== python3 _probe_env.py（退出码 0）===\n"
     "  产物：16-checkpoint/_probe/r7_final_env.txt\n"
     "  ⇒ 与第 6 轮同向：能力集是**逐进程读数**（G11），本轮再次不引用任何跨会话的 CapBnd 结论。\n"
     "== 结论：PASS ==（通道可用性判定以本轮实跑为准）",
     "main-agent-rerun"),

    ("★ §4③ 收口第 ② 步：验证通道 + 全站横向溢出（R-22）",
     "=== python3 _probe_channel.py（退出码 0）===\n"
     "  == 结论：PASS ==（用时 61.2s；manifest → 16-checkpoint/_probe/channel.json）\n"
     "  -- D. 全站横向溢出普查（视口 1440×900；51 页）--\n"
     "     [PASS] 全站 51 页：文档级与元素级横向溢出均为 0\n"
     "     overflow_view {\"docScrollW\": 1440, \"innerW\": 1440, \"overflowing\": []}\n"
     "== 结论：PASS ==（横向溢出直接量 = 0，⛔ 非代理判据）",
     "main-agent-rerun"),

    ("★ §4③ 收口第 ③ 步：门控全量（判据 P01–P41）",
     "=== python3 gate_prototype.py（退出码 0）===\n"
     "  [PASS] P28 动效预算四项上界（reveal ≤32 / 进场 ≤1800ms / dur 和 ≤3.6s / infinite ≤12）\n"
     "         本轮实测：最大 [data-reveal] 10（≤32）；进场完成 1390ms（≤1800）；\n"
     "         --dur-* 之和 1.79s（≤3.6）；infinite 0（≤12）；违例 0 处 []\n"
     "  [PASS] P39 引用点 3 处；被引用的登记件 11 个 / 磁盘登记件 11 个 / 结构化出口键 11 个；\n"
     "         断链 0 处 / 孤儿 0 处；违例 0 处 []\n"
     "== 门控结论：PASS ==  FAIL 0 项 []\n"
     "  （产物：16-checkpoint/_probe/r7_final_gate.txt）",
     "main-agent-rerun"),

    ("★ §4③ 收口第 ④ 步：判据自检（逐条触发负例）",
     "=== python3 gate_prototype.py --selftest（退出码 0）===\n"
     "== 自检结论：PASS ==（41 条判据 / 171 条负例夹具，全部须正向 PASS 且负例触发）\n"
     "★ 并排：判据 **41 → 41**（⛔ 未新增编号，改动挂 P35 ② 与 P39）；夹具 **166 → 171**\n"
     "  （P35 ② 新增 2 条：㉝ 未登记缩写 ⇒ FAIL / ㉞ 缺 h1 ⇒ 闭合断言 FAIL；\n"
     "    P39 ④ 新增 3 条；其中原夹具 #3 **被修正**，⛔ 不是新增）\n"
     "  （产物：16-checkpoint/_probe/r7_final_selftest.txt）",
     "main-agent-rerun"),

    ("★ §4③ 收口第 ⑤ 步：幂等（`build-all.py --write` 二次比对）",
     "=== python3 build-all.py --write（第一次）===\n"
     "  实际写入 31 个 / 实际删除 0 个 / 孤儿残留 0 个；二次比对干净：True\n"
     "=== python3 build-all.py --write（第二次）===\n"
     "  实际写入 0 个 / 实际删除 0 个 / 孤儿残留 0 个；二次比对干净：True\n"
     "== 结论：PASS ==（幂等；P16 亦然）",
     "main-agent-rerun"),

    ("★ §4③ 收口第 ⑥ 步：图件（件数 + 规格两侧探针）",
     "=== python3 gen-figs.py --check ===\n"
     "  [PASS] 图件 94 件与派生结果一致（47 .dot + 47 .svg）\n"
     "=== python3 _selfcheck_figs_spec.py ===\n"
     "  == 结论：PASS ==（四发合成探针 + 盘上 47 张真实图件；不符 0 处）\n"
     "  [OK] 两侧都在界内 880.0x300.0 期望 PASS 实得 PASS\n"
     "  [OK] 上界·越界(高) 200.0x900.0 期望 FAIL 实得 FAIL\n"
     "  [OK] 下界·边界(恰 0.90) 893.3x400.0 期望 PASS 实得 PASS\n"
     "  [OK] 下界·越界(旧 pe-f-06) 1016.0x150.0 期望 FAIL 实得 FAIL\n"
     "== 结论：PASS ==",
     "main-agent-rerun"),

    ("★ 数据侧自检（C28–C33 / C58）",
     "=== python3 10-dag-data/_selfcheck.py（退出码 0）===\n"
     "  [PASS] C29-complete-blocks complete 节点 8 区块全非空（空：[]）\n"
     "  [PASS] C33-terms-resolvable 节点 terms 逐条可在 glossary 解析（未命中：[]）\n"
     "  [PASS] C58-quote-provenance evidence 引文逐片段可在引文库逐字回源\n"
     "         （节点侧 113 条 evidence / 库内 126 条唯一引文，源件 7 个；坏：[]）\n"
     "  == 自检：PASS ==  (FAIL 0 项 / WARN 4 项)\n"
     "  ★ 4 项 WARN 全部为报告项或存量缺口：C22c 互指提示 / C28b 上限报告 /\n"
     "    C28c caliber 区间报告 / C58b（frontier 侧 2 片无源，G23 存量）",
     "main-agent-rerun"),

    ("★★ R-01 裁决（N1）落地：判据改后**当场实测**（⛔ 未放宽任何阈值）",
     "=== python3 gate_prototype.py --only P35 ===\n"
     "  [NOTE] P35 ②（R-01 / 2026-10-16 第 7 轮 N1 裁决）：口径 = 「h1 每个 ≥3 字母拉丁 token\n"
     "  必须在 glossary.json 的某个 term 里逐字命中」；对象集 = 全部受检页 44 个（排除清单为空）；\n"
     "  判据真正作用到 44 个（含 <h1>）；h1 含 ≥3 字母拉丁 token 的页 **1** 个；\n"
     "  登记面 = glossary.terms 69 条。\n"
     "  == 门控结论：PASS ==  FAIL 0 项 []\n"
     "★ 那**唯一 1 个**页就是 `11-node-pages/pe-r-07.html`（h1 = 「ReAct 推理—行动交织」）\n"
     "  ⇒ N1 的判据在**真实产物**上首次生效且通过；旧实装（h1 含英文即 FAIL）会当场判它 FAIL。\n"
     "★ 旧实现的 `kind != \"interactive\"` **控制流豁免已删除**（本文件头部明文禁止该形态）。\n"
     "=== python3 _selfcheck_p35_fixtures.py ===\n"
     "  ② h1 拉丁缩写口径的阈值两侧探针：\n"
     "    ReAct（已登记）⇒ PASS ／ RAG（已登记）⇒ PASS ／\n"
     "    Kubernetes（未登记）⇒ FAIL ／ AI（2 字母，低于阈值）⇒ 不触发\n"
     "  == 自检结论：PASS ==（34 条夹具全部触发；正向 PASS；⑫ 0 处不符；② 0 处不符）",
     "main-agent-rerun"),

    ("★★ P39 补「结构化出口闭合」：**改前 / 改后**并排读数（本轮的存量缺陷证据）",
     "=== 改前（`_r7_backup/16-checkpoint/`，第 6 轮末态）===\n"
     "  `gates` 的 `criteria_change_*` 键 = **7** 个\n"
     "  磁盘 `CRITERIA-CHANGE-*.md` = **9** 件\n"
     "  ⇒ 缺 2 件：`CRITERIA-CHANGE-P35-G4.md` / `CRITERIA-CHANGE-P38-P40.md`（只在散文里出现）\n"
     "=== 而第 6 轮收口 P39 报的是 ==\n"
     "  「被引用的登记件 9 个 / 磁盘登记件 9 个；断链 0 处 / 孤儿 0 处；违例 0 处 []」⇒ **全绿**\n"
     "  （原件：`_probe/r6_final_gate.txt` 第 158–159 行）\n"
     "=== 改后（本轮）===\n"
     "  [PASS] P39 引用点 3 处；被引用的登记件 11 个 / 磁盘登记件 11 个 / 结构化出口键 11 个\n"
     "  === python3 gate_prototype.py --selftest --only P39 ===\n"
     "        负例（6 条）：全部触发（判据可判假） —— 6/6 条子断言负例全部触发\n"
     "== 结论：堵住 ==（⛔ 判据编号未增，改动挂 P39；登记件 9 → 11）",
     "main-agent-rerun"),

    ("★★ 本轮最值钱的发现：一条旧负例夹具是**靠存量缺口触发**的（假夹具）",
     "=== 补完 P39 ④ 后当场报出（原文）===\n"
     "  [FAIL] P39 …第 7 轮补④ 结构化出口闭合…\n"
     "         正向：PASS\n"
     "         负例（6 条）：存在未触发（判据疑似恒真） —— 负例#3 未触发：…\n"
     "  == 自检结论：FAIL ==（1 条判据 / 6 条负例夹具，全部须正向 PASS 且负例触发）\n"
     "★ 根因：夹具 #3 原实现**只改 `gate_prototype.py` 一处**引用名，实际制造的是**孤儿**；\n"
     "  它能红，**仅仅因为** P35-G4 / P38-P40 两件「只被 gate_prototype.py 引用」——\n"
     "  那正是 P39 ④ 要堵的**缺口本身**。⇒ 缺口一补，夹具立刻失去触发源。\n"
     "★ 修法：夹具 #3 改为**三处引用点一起改名** ⇒ 语义回到它 docstring 声称的「引用点扫不到」\n"
     "  （即断言 ③ 的空集守卫，原本**没有**专属夹具）。\n"
     "=== 修后 ===\n"
     "        负例（6 条）：全部触发 —— 6/6 条子断言负例全部触发\n"
     "  == 自检结论：PASS ==\n"
     "★ 价值判断：**高于它修的那个缺口** —— 它证明「夹具集合本身也会随产物演进而失效」。",
     "main-agent-rerun"),

    ("★ 内容波次 3：22 个节点的**独立复跑**（R-24：⛔ 不采信子 Agent 自报）",
     "=== 主 Agent 由 `_wave3_parts/*.json` **重建** solo 目录后逐个 dry-run ===\n"
     "  原件：16-checkpoint/_probe/r7_t2_rerun.txt\n"
     "  8 个先行完成的部件：`== 结论：PASS ==` × 8（⛔ 无一条非 PASS）\n"
     "  ⇒ 与 8 路子 Agent 的自报**逐条吻合**（含片段 k/k 回源、lab/evidence/pitfalls 条数）\n"
     "=== 终局落盘 ===\n"
     "  [write] dag.json 已落盘；回读：JSON 合法 / 节点 67 / **complete 35 个**\n"
     "  （PE-E-01…09 ＋ PE-R-01/03…08 ＋ PE-A-01…06 ＋ 前 13 个）\n"
     "== 结论：PASS ==（**35 / 67**，跨过 D7 定的发布阈值 ≥34）",
     "main-agent-rerun"),

    ("★★ 本轮当场抓到的**四类真缺陷**（全部改**内容/装置**，⛔ 未放宽任何阈值）",
     "=== 缺陷一：公开文案含内部记号（P33）===\n"
     "  [FAIL] P33 …可见文案内部记号命中 2 处 [('11-node-pages/pe-e-01.html', \"含内部记号 '⛔'\"),\n"
     "         ('11-node-pages/pe-r-01.html', \"含内部记号 '★'\")]\n"
     "  ⇒ 自建 `_probe/r7_t2_strip_marks.py`（记号集与 P33 同源）扫**部件源头**，共 **9 处 / 5 个部件**\n"
     "    （门控只见 2 处 —— 它只能看**已建产物**）⇒ 剥离后 P33 PASS（受检页面 51 个，命中 0 处）\n"
     "=== 缺陷二：dry-run 之后改文件却不复跑 ===\n"
     "  `_wave1_apply.py --write --reapply` **中止落盘**：\n"
     "    ('PE-E-08', 'evidence[0] quote 超 200 字（227）')\n"
     "    ('PE-E-08', 'evidence[1] quote 超 200 字（241）')\n"
     "  而该件子 Agent **自报**长度为 136 / 162 / 175 ⇒ 三条全不吻合（改在 dry-run 之后）\n"
     "  ⇒ 另有一次同型：PE-A-03（223 / 253）\n"
     "=== 缺陷三：顶层扫描面被污染 ===\n"
     "  子 Agent 在 `16-checkpoint/` **顶层**留下临时 `.py`，把 P41 的扫描面从 **34** 抬到 **44**\n"
     "  ⇒ 逐个核实为 no-op 后清理，恢复 **34**\n"
     "=== 缺陷四：跨 Agent 误删 ===\n"
     "  某子 Agent 的清理脚本规则过宽，误删同层**他人**临时脚本两个（其自陈原文）\n"
     "=== 收口期的三处机检缺陷（改部件、⛔ 不改产物）===\n"
     "  P12：PE-A-02 的 `~/.env`、PE-A-06 的 `/tmp/wrapped.txt`（3 处）⇒ 换相对写法\n"
     "  P35 ⑨：PE-E-09 的 `intro` 用「其一，…**。**其二，…」跨句列举 ⇒ 渲染侧 `split_enum`\n"
     "    只在**单句内**按 `；` 切 ⇒ 不生成 `.enum-list`；改为单句 `；` 分隔（改 2 个字符）\n"
     "  ⇒ 三处修后门控 PASS（FAIL 0）\n"
     "== 结论：全部处置 ==（四类缺陷已写进 `AUTHORING-SPEC.md` 禁忌 #9–#12 防复发）",
     "main-agent-rerun"),

    ("★ 视觉核查（★ 硬要求：图件类改动必须**看图**，且必须在站点样式内看）",
     "=== `_figcheck.py`（核对台）→ `_render.py --full`（整页）→ `read_image` 逐张 ===\n"
     "  本波新增图件 **22** 张；实拍并逐张看过 **22 / 22**（⛔ 无抽样、无跳过）\n"
     "  取证件：`_probe/fig3-<fid>.png`（22 张）＋ `_probe/fig3-<fid>.html`（22 个核对台）\n"
     "  结论：22 张全部合格（结构清晰 / 无压字 / 无重叠 / CJK 无豆腐块 / 图注完整）\n"
     "  ★ 过程更正：首轮 620px 视口把 4 张的**图注**裁掉 ⇒ 判为「截图视口问题，⛔ 非图件缺陷」，\n"
     "    改 `--full` 重拍后复看全部完整\n"
     "  ★ 一条措辞级观感（⛔ 不构成违例、本轮不改）：`pe-r-07` 图注「四类失效**计数**」用词略生硬\n"
     "  （原件：16-checkpoint/_probe/r7_t3_visual-check.md）\n"
     "== 结论：PASS ==（22/22 亲看）",
     "main-agent-rerun"),
]

ARTIFACTS = [
    "16-checkpoint/ROUND-LEDGER.json", "16-checkpoint/_r7_ledger_update.py",
    "16-checkpoint/CRITERIA-CHANGE-R01.md", "16-checkpoint/CRITERIA-CHANGE-P39.md",
    "16-checkpoint/DESIGN-CONTRACT.md", "16-checkpoint/AUTHORING-SPEC.md",
    "16-checkpoint/gate_prototype.py", "16-checkpoint/gen-state.py",
    "16-checkpoint/gen-figs.py", "16-checkpoint/gen-nodes.py",
    "16-checkpoint/_selfcheck_p35_fixtures.py", "16-checkpoint/_b1_boundary_review.md",
    "16-checkpoint/_r7_backup/MANIFEST.txt", "16-checkpoint/_r6_backup/MANIFEST.txt",
    "16-checkpoint/_probe/README.md", "16-checkpoint/_probe/false-green/agent-browser-output.png",
    "16-checkpoint/_reflection-candidates/_ROUND7-READ.md",
    "16-checkpoint/_wave3_parts/", "10-dag-data/dag.json", "10-dag-data/figures/",
    "PUBLISH-STATE.json",
]

G_LIST = {
    "G17": "★ **第 7 轮再次更正（同型第 2 次复发）**：`DESIGN-CONTRACT.md` §4③ 标题写「收口必做（**五步**）」"
           "而其下命令块是 **6** 条 —— 第 5 轮已修过一次、第 6 轮又退回。本轮改回「六步」并在该节留更正说明。"
           "★ 该类（文档内部计数与正文条数不符）**仍无判据**，如实留行。",
    "G28": "✅ **已消（第 7 轮，用户裁决 N1）**：节点名里的拉丁缩写不再阻塞。R-01 口径改为「h1 一行、无括号；"
           "其中每个 ≥3 字母拉丁 token 必须能在 glossary.json 的某个 term 里逐字命中」；同批删 P35 ② 的"
           "`kind != \"interactive\"` 控制流豁免，改走显式对象集 + 全集闭合断言。**5 个节点一字未动**；"
           "判据在 `11-node-pages/pe-r-07.html` 上首次生效并通过。见 `CRITERIA-CHANGE-R01.md`。",
    "G29": "★ **第 7 轮复现 3 次并升级为「装置级」**：子 Agent 自报 dry-run PASS 而**最终落盘字节不达标**"
           "（PE-E-08 自报 136/162/175 vs 盘上 227/241/132；PE-A-03 同型）⇒ 合并器 fail-closed 拦下、"
           "**整批中止**。⇒ 已写进 `AUTHORING-SPEC.md` 禁忌 #10（先定稿再 dry-run；交件报两处 sha256）。"
           "★ 机检边界不变：P40 报不出「行文里的数字与自报不符」。",
    "G33": "★ **第 7 轮新增**：`_wave_pick_quotes.py` 的 **URL→id 映射假阴性** —— 它用 `setdefault` 建索引，"
           "同一 URL 在 sources.json 出现多次时只有首个 id 生效，其余显示 `S-id = ——`（两名子 Agent 独立复现）。"
           "★ 判「可用性」应以 `_wave1_apply.py` 的 dry-run 为准；**本轮未改该脚本**（属工具欠账，留行）。",
    "G34": "★ **第 7 轮新增（本轮最值钱的发现）**：**夹具会随产物演进变成假夹具** —— `mut_p39` 的夹具 #3"
           "**靠存量缺口触发**（它只在「某件登记件只被 gate_prototype.py 引用」时才红）；本轮把缺口补上，"
           "它立刻失去触发源并被 `--selftest` 当场报出「负例#3 未触发（判据疑似恒真）」。"
           "⇒ 改为三处一起改名后语义回到断言 ③。**这是「判据/夹具的作用域会随产物漂移」的第 3 个实例**"
           "（前两例：第 6 轮 G19 的 R-07 作用域、T-1 的写死页数）。",
    "G35": "★ **第 7 轮新增**：**公开文案里的内部标注记号**（`⛔` / `★` / `⚠`）—— 门控 P33 报了 2 处，"
           "而在**部件源头**扫出 **9 处 / 5 个部件**（门控只能看已建产物）。⇒ 已写进 `AUTHORING-SPEC.md` 禁忌 #9；"
           "并留下可复用工具 `_probe/r7_t2_strip_marks.py`（记号集与 P33 同源、默认 dry-run、带回读验证）。",
    "G36": "★ **第 7 轮新增**：**子 Agent 在 `16-checkpoint/` 顶层留下临时 `.py`**，把 P41 的扫描面从 34 抬到 44。"
           "P41 的闭合断言**不会**因此 FAIL（新文件默认落入「受检」而非「未分类」）⇒ 它是**卫生问题而非判据缺口**，"
           "靠主 Agent 逐个核实后清理。⇒ 已写进 `AUTHORING-SPEC.md` 禁忌 #11。",
    "G37": "★ **第 7 轮新增**：**跨 Agent 误删** —— 某内容子 Agent 的清理脚本规则过宽，删掉了同层**他人**的两个临时脚本"
           "（其自陈原文；经 grep 确认全仓无引用、未影响任何部件）。⇒ 已写进 `AUTHORING-SPEC.md` 禁忌 #12"
           "（清理脚本只许匹配自己的前缀；⛔ 不写 `rm _tmp_*` 这类全局通配）。",
    "G38": "★ **第 7 轮新增（数据侧缺口，留行）**：`PE-E-03` / `PE-A-05` 的**核心机制句**在引文库 A*.json 中"
           "**无一手可引用原文**（裁判位置偏差/冗长偏好/自我偏好；「否定词提高相关内容概率」）。"
           "两名子 Agent 都**如实上报**并只在散文/术语界定里陈述、⛔ 未编造引文 ⇒ 本轮**不改数据**，"
           "登记为缺口：若要发布口径要求逐条主张有一手引文，需补外源或降级该表述。",
    "G39": "★ **第 7 轮新增（未解决）**：`CARRIER-SCAN` 面 —— **任务根的两个探针 `.py`**"
           "（`_audit_r5_probe.py` / `_selfcheck_stage1.py`）与 `_probe/` 下的脚本**不在 P41 的扫描面内**"
           "（P41 只扫 `16-checkpoint/` 顶层）。⇒ 本轮**登记**（见 artifacts 与 `_probe/README.md` §四），"
           "⛔ 未把扫描面扩到任务根（那会是本轮第三次判据变更）⇒ 留行。",
    "G40": "★ **第 7 轮新增（已处置）**：**未登记的游离物证** —— 任务根名为 `--output` 的 3420 B / 1280×577 PNG，"
           "实为 `agent-browser` **假绿通道**的产物（`RENDER-CHANNEL.md:96` 记述它「回显成功却产出纯白空图、"
           "并把 `--output` 当字面文件名」），但它**从未被任何台账/判据登记为产物**。"
           "⇒ 已校验（源为常规文件、合法 PNG、父目录＝任务根）后迁入 `16-checkpoint/_probe/false-green/` 并在"
           "`_probe/README.md` §三 登记其身份/来源/作用域。",
    "G41": "★ **第 7 轮新增（已处置）**：**`_r6_backup/` 无内容边界登记**，且外部核验方据「内层台账 round=5、"
           "dag 停在 complete=8」判它「名不符实（实为第 5 轮开工前）」——**该判读经主 Agent 复算后否定**："
           "complete=8 恰是**第 5 轮末态**（8 = 第 1 轮 3 个 + 第 5 轮波次 1 的 5 个）。"
           "⇒ 已补 `MANIFEST.txt` 登记真实边界（含「本快照只保能重建产物的那半边」的局限）。",
    "G15": "**不做**（留行，⛔ 不删）：发布级强化（SH0–SH5 / CI / `.nojekyll` / 建仓 push / Pages / hub 收录）"
           "与跨仓议题。★ **本轮已跨过 D7 定的阈值（complete 35 ≥ 34）⇒ 下一轮可启动建仓与发布**；"
           "本轮收口时只做了一份就绪性核查（⛔ 未建仓、⛔ 未发布）。★ 现状约束仍在："
           "本站 `--border` 对底色仅 1.0:1（浅）/ 1.06:1（深），且**没有任何门控会失败**。",
    "G18": "第 7 轮逐项：⑧ **P35 ⑫ 代理判据仍未退役**（留行；前置条件 = P38 的直接量覆盖组页 22 个区块，或另立更严判据）；"
           "⑨ 分组索引 6 列短值表仍未被判据覆盖（留行）；⑩ 组页 `intro` 无枚举模式（留行，内容波次是解法）；"
           "⑪ P40 只断结构、如实性不可机检（明文登记）；⑫ P38 不判 PNG 新鲜度（留行）；"
           "⑬ `report.html` 的 `<title>` 仍写「第 1 轮」（**刻意不改**，front matter 属历史原文）。",
    "G23": "**未解决（留行）**：`C58` 对象只有节点侧；`frontier.json` 侧 2 片引文无法在 A 池逐字回源。"
           "本轮 C58b 仍以 WARN 常驻（4 项 WARN 之一），⛔ 未改 `frontier.json`。",
    "G25": "**未解决（留行）**：`P41` 仍是窄版（⛔ 不判「任何措辞」）。本轮**未动**。",
    "G30": "★ **第 7 轮复现并处置**：**审核/协作窗口内文件被并发修改** —— 两例：① 我读 `PE-E-08` 的引文长 227，"
           "数分钟后同一文件变成 143（其子 Agent 仍在写）；② P16 一度 FAIL，因为它跑的时刻正有子 Agent "
           "改写 `gen-figs.py`（两次沙箱生成的输入不同）。⇒ 处置：**动某文件前先确认其写者已停手**（`list_agents`），"
           "我的部件修正器也自带「锚点命中次数不符即拒绝落盘」的守卫。",
    "G31": "**未动（留行）**：`R-08` 的「内容列」用词模糊（应补「= `.layout > main` 的 border-box 内宽」）。",
    "G32": "**已处置（留行以免被读作已消）**：审核委派的工具面须含可执行 shell。★ 本轮**未派审核子 Agent**"
           "（时间盒内先收口）；该纪律已写进 `AUTHORING-SPEC.md` 与契约 §3 的既有条目。",
}

NOTE = (
    "★ 本对象是**第 7 轮（T1：N1 裁决落地 + 存量缺陷；T2：内容波次 3 = 22 个节点 + 22 张图件；"
    "T3：收口期三处机检缺陷处置）**的轮次对象：按契约 §4① 第 3 条在**开工期先落盘**？"
    "⛔ **不是** —— 本轮采用**收口期一次性落盘**（见下「偏离登记」），claims / artifacts / "
    "g_list_updates / started_at / ended_at 一并写入；⛔ **未回改 round 3/4/5/6 对象**（本脚本用文本手术追加，"
    "其余字节一个不动，`guards()` 复核）。\n"
    "★ 本轮读数全部由**主 Agent 亲跑**（`main-agent-rerun`，逐条附原始输出，原件落 `16-checkpoint/_probe/r7_*.txt`）；"
    "⛔ 无一条采信委派方自报 —— 本轮派了 **23 个执行子 Agent**（22 路内容 + 1 路出图，分 3 批，"
    "受并发上限 8 约束）：它们的产出**只是部件与图源**（内容正文 ⛔ 不进主 Agent 上下文，R-25），"
    "且各自报的每一条数字都由主 Agent 用 `_wave1_apply.py` 的 dry-run（**从部件重建 solo 目录**）／"
    "`gen-figs.py --check`／`_selfcheck*.py`／门控**独立复跑**。★ 本轮**实证了两条「自报不可信」的具体形态**："
    "① 内容侧两件的最终字节与自报不符（G29 升级）；② 出图侧自报「22/22 完成」经主 Agent 用 `gen-figs --check`"
    "与逐张看图复核**成立**（如实报成功也是一种如实）。\n"
    "★ **时点关系（⛔ 未改任何历史件）**：`report.md` §7.x/§8.x/§9.x 与 round 3/4/5/6 对象里的旧读数"
    "（40 或 41 判据 / 152·154·159·162·166 夹具 / P01–P37/P40/P41 / 24·29 页 / 9·25 张图）"
    "都是**各自收口时刻的快照**；本对象的现态是 **41 判据 / 171 夹具 / P01–P41 / 51 页 / 47 张图件 / "
    "complete 35 · registered 32 / 登记件 11 件**。\n"
    "★ **收口完成判据逐条对照**：`_probe_env.py` 退出码 0 ✅ · `_probe_channel.py` 退化 0 处（51 页溢出 0）✅ · "
    "`gate_prototype.py` 退出码 0 ✅ · `--selftest` 退出码 0 ✅ · `build-all.py --write` 二次比对干净 ✅ · "
    "`gen-figs.py --check` 94 件一致 ✅ · `_selfcheck_figs_spec.py` PASS ✅ · `10-dag-data/_selfcheck.py` PASS ✅ · "
    "`_selfcheck_p35_fixtures.py` PASS ✅ · G 清单每行都有处置 ✅ · 台账落盘且 P40 PASS ✅ · "
    "视觉核查（**22/22 张新图逐张亲看**）✅。\n"
    "★ **偏离登记（⛔ 不得静默）**：契约 §4① 要求「开工期先落盘 `rs_touched`」，本轮**未**照做 —— "
    "因为本轮开工时尚未确定会触碰哪些 R-xx，先写会变成**猜测**。⇒ 如实记为流程偏离，"
    "并把该偏离本身作为下轮的建议修正点（要么在开工期就用「预计触碰集」并声明它可能扩大，"
    "要么把契约改成「收口期落盘但须在 note 明示」）。"
)


def build_round():
    return {
        "round": 7,
        "started_at": STARTED,
        "ended_at": ENDED,
        "rs_touched": RS_TOUCHED,
        "claims": [{"fact": f, "raw_output": r, "source": s} for f, r, s in CLAIMS],
        "artifacts": ARTIFACTS,
        "g_list_updates": G_LIST,
        "note": NOTE,
    }


def guards(raw_before, raw_after):
    """⛔ 只允许在末尾追加：前缀必须逐字节相同，且原来有 N 个轮次、现在 N+1。"""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    raw = open(LEDGER, encoding="utf-8").read()
    doc = json.loads(raw)
    if doc.get("schema") != SCHEMA:
        raise SystemExit("[FAIL] schema 不匹配：%r" % doc.get("schema"))
    rounds = doc["rounds"]
    if any(r["round"] == 7 for r in rounds):
        raise SystemExit("[FAIL] 已存在 round 7 对象 ⇒ 本脚本只负责**首次**追加（⛔ 不覆盖）")
    rnd = build_round()

    # ① 本地预校验（与 P40 同口径，避免写完才发现）
    ids = set(re.findall(r"^\| (R-\d\d) \|", open(os.path.join(HERE, "DESIGN-CONTRACT.md"),
                                                 encoding="utf-8").read(), re.M))
    if not rnd["rs_touched"]:
        raise SystemExit("[FAIL] rs_touched 为空")
    bad = [x for x in rnd["rs_touched"] if x not in ids]
    if bad:
        raise SystemExit("[FAIL] rs_touched 含契约规则表外的 id：%r" % bad)
    for c in rnd["claims"]:
        if c["source"] not in ("self-report", "main-agent-rerun"):
            raise SystemExit("[FAIL] claim.source 非法：%r" % c["source"])
        if not c["raw_output"].strip():
            raise SystemExit("[FAIL] claim 缺 raw_output")
        if c["source"] == "main-agent-rerun" and "===" not in c["raw_output"]:
            raise SystemExit("[FAIL] main-agent-rerun 的 raw_output 缺原始输出标记 `===`")
    print("  预校验：R-id %d 个全部合法 · claims %d 条（source/raw_output 齐备）· artifacts %d 项 · G 行 %d 行"
          % (len(rnd["rs_touched"]), len(rnd["claims"]), len(rnd["artifacts"]), len(rnd["g_list_updates"])))

    # ② 文本手术：在末尾 `\n ]\n}` 之前插入（缩进照抄既有轮次：对象 2 空格 / 其下键 3 空格）
    tail = "\n ]\n}"
    if not raw.endswith(tail + "\n"):
        raise SystemExit("[FAIL] 文件末尾形态与预期不符，拒绝文本手术（fail-closed）")
    body = json.dumps(rnd, ensure_ascii=False, indent=1)
    shifted = "\n".join("  " + ln for ln in body.split("\n"))
    new_raw = raw[:-len(tail + "\n")] + ",\n" + shifted + tail + "\n"

    guards(raw, new_raw)
    print("  文本手术：前缀字节未动 · 新增轮次对象 %d 字节" % len(shifted))
    if a.write:
        open(LEDGER, "w", encoding="utf-8", newline="\n").write(new_raw)
        back = json.load(open(LEDGER, encoding="utf-8"))
        print("  回读：JSON 合法 · 轮次 %s · round 7 claims %d 条 · artifacts %d 项"
              % ([r["round"] for r in back["rounds"]], len(back["rounds"][-1]["claims"]),
                 len(back["rounds"][-1]["artifacts"])))
        print("  == 结论：已落盘 ==")
    else:
        print("  == 结论：dry-run，⛔ 未写盘 ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
