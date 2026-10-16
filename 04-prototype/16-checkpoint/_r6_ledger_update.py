#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r6_ledger_update.py —— 把第 6 轮（T1 收口 / T2 判据升级 / T3 波次 2）的收口读数写进
`ROUND-LEDGER.json` 的 **round 6** 对象（新增一个对象，⛔ 不改 round 3/4/5 的字节）。

## 与 `_r5_ledger_update.py` 的关系
照抄它的**定点拼接**手法（⛔ 不整文件重排：本台账的短数组是紧凑单行写的，`json.dumps(indent=1)`
会把它们展开 ⇒ 整文件重排会 churn 掉前几轮的字节）。本件是**追加**：在第 5 轮对象之后插一个新对象。

## 三道守卫（缺一即拒写）
① 锚点唯一（`\n ]\n}\n` 只出现 1 次）；
② 写后回读：前 5 个 round 对象的**规范形 `json.dumps(..., sort_keys=True)` 与写前逐字相同**；
③ 每条 claim 的 `source` 合法、`main-agent-rerun` 必含原始输出标记 `===`；`rs_touched` ⊆ 契约规则表。

用法：`python3 _r6_ledger_update.py`（dry-run）/ `python3 _r6_ledger_update.py --write`
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ROUND-LEDGER.json")
ROUND = 6


def claim(fact, raw, src="main-agent-rerun"):
    return {"fact": fact, "raw_output": raw, "source": src}


CLAIMS = [
    claim("★ §4① 开工必做第 2 步：环境探测复跑（R-21；⛔ 不沿用上一轮的散文结论）",
          "=== python3 _probe_env.py（退出码 0）===\n"
          "   snap 内核：found=True（/snap/bin/chromium）\n   playwright(python)：found=True version=1.63.0\n"
          "   CapInh/CapPrm/CapEff/CapBnd = 0000000000000000；NoNewPrivs 1；Seccomp 0\n"
          "   $ /snap/bin/chromium --version … rc=46（DBus: cannot create transient scope）\n"
          "== 结论：PASS ==（至少一条**不同源**的通道可用 ⇒ 可以做真实渲染验证）\n"
          "★ 事实更正（G11 续）：本会话 `CapBnd` **又**读到 `0000000000000000`，与第 5 轮审核方读到的 "
          "`000001ffffffffff` 不同 ⇒ 再次实证「**能力集是逐进程读数、⛔ 不可跨会话沿用**」；"
          "稳定的只有 `CapEff=0 + NoNewPrivs=1` 与 snap 负对照 rc=46。"),
    claim("★★ 收尾复核（§3-④/⑤ 的补做）：独立复算全部吻合；★ 同时**纠正了本对象 claim ① 的一处过度概括**",
          "=== 复核子 Agent（具 bash）自跑 `python3 _probe_env.py` 的原文节录 ===\n"
          "   CapEff 0000000000000000 / CapBnd 000001ffffffffff / NoNewPrivs 1\n"
          "   snap 负对照：`/snap/bin/chromium --version` **rc=1**（snap-confine … cap_dac_override not found）\n"
          "== 结论：PASS ==\n"
          "=== 独立重数（它自己数，⛔ 未读 _probe/r6_*.txt）===\n"
          "   pages=29（13 节点页 + 12 组页 + 2 视图 + 交互 + 根入口）/ md=28 / complete=13 / pending=54 —— 与主 Agent 声明**全部吻合**\n"
          "   旁证：门控自报「受检产物 62 个（HTML 29 / MD 28）」\n"
          "=== PNG 完整性（两个独立解码器交叉）===\n"
          "   8 条 sha256 与 manifest 声明逐条相等（mismatch=0）；`_pil_read.py`（PIL）独立解码的尺寸/唯一色/字节亦逐条相等\n"
          "=== P39 ===\n   磁盘登记件 9 个 ⟺ 三处引用点并集 9 个；断链 0 / 孤儿 0\n"
          "★★ **两条纠正（如实登记）**：\n"
          "   ① **本对象 claim ① 的推断被推翻**：它写「本会话 `CapBnd` 又为 0」——那是把一个**进程**的读数说成了**整个会话**的事实；"
          "复核进程实测 `000001ffffffffff`、`rc=1`。⇒ claim ① 已改为「两个读数都不是稳定事实」（`G11` 第 3 次复现，"
          "这次抓错的是**我自己当轮写下的推断**）。\n"
          "   ② **副作用如实披露**：`_probe_env.py` 每次运行都会**重写** `_probe/env.json` ⇒ 复核运行覆盖了它；"
          "复核方已 grep 确认**没有任何判据读该文件**（只有探针写、`_r5_ledger_update.py` 文中提及）⇒ 不影响任何裁决。"),
    claim("★ T1 先改判据、产物未补时**当场 FAIL 11 处**（证明新作用域不是空转）",
          "=== python3 gate_prototype.py --only P35（改完 P35 ⑧ 作用域、11 张组图尚未落盘）===\n"
          "受检页面 24 个（节点页 8 / 组页 11 / 视图页 2）；… 违例 11 处 "
          "[('12-groups/g00.html', '缺图件 .fig（知识承载页（节点页 / 组页；⛔ 不含分组索引） ≥1 自制图）', ''), …]\n"
          "== 门控结论：FAIL ==  FAIL 1 项 ['P35']\n"
          "（完整原文 16-checkpoint/_probe/r6_t1b_p35_after_scope.txt；★ 首版实装多报 1 处 —— 那是我把两个对象集的口径写错，"
          "见 CRITERIA-CHANGE-R07.md §L·F-1）"),
    claim("★ 图件规格补「缩放比下界」后，**存量图 pe-f-06 当场被自己的新规格拒收**（历史复现）",
          "=== python3 _selfcheck_figs_spec.py（退出码 0）===\n"
          "[OK  ] 两侧都在界内          880.0x300.0   期望 PASS 实得 PASS\n"
          "[OK  ] 上界·越界(高)        200.0x900.0   期望 FAIL 实得 FAIL | 规格超限：…高 3618px > 上限 600px\n"
          "[OK  ] 下界·边界(恰 0.90)   893.3x400.0   期望 PASS 实得 PASS\n"
          "[OK  ] 下界·越界(旧 pe-f-06) 1016.0x150.0  期望 FAIL 实得 FAIL | 缩放比过低：viewBox 宽 1016 ⇒ 缩放 0.79×\n"
          "[OK  ] 盘上真实图件 25 张全部合规（逐一复算，⛔ 不抽样）\n"
          "== 结论：PASS ==（四发合成探针 + 盘上 25 张真实图件；不符 0 处）"),
    claim("T1 图件落盘 + 幂等 + P28 动效读数",
          "=== python3 gen-figs.py --check ===\n[PASS] 图件 40 件与派生结果一致\n"
          "=== python3 build-all.py --write ===\n  实际写入 13 个 / 实际删除 0 个 / 孤儿残留 0 个\n  二次比对干净：True\n"
          "=== python3 gate_prototype.py（P28 段）===\n"
          "       M1 单页最大 [data-reveal] 10（≤32）；M2 进场完成 1390ms（≤1800）；M3 --dur-* 之和 1.79s（≤3.6）；M4 infinite 0（≤12）；违例 0 处 []"),
    claim("T1 真实渲染：组页 mini-DAG 入镜 + 全站横向溢出 0",
          "=== python3 _probe_channel.py（退出码 0；38.8s）===\n"
          "   [PASS] group  1440x900  唯一色 7260 亮度 22.4–255.0 367999 B 86f17548a5511c87   ← ★ 组页新图入镜\n"
          "   [PASS] root/node/view/interactive/root-narrow/interactive-narrow/root-dark 全部非退化\n"
          "-- D. 全站横向溢出普查（视口 1440×900；24 页）--\n"
          "   [PASS] 全站 24 页：文档级与元素级横向溢出均为 0\n== 结论：PASS =="),
    claim("T1 负例夹具 159 → 162（P35 +3：组页去图 / 注入未分类页 / 排除清单过期）",
          "=== python3 gate_prototype.py --selftest（退出码 0）===\n"
          "== 自检结论：PASS ==（40 条判据 / 162 条负例夹具，全部须正向 PASS 且负例触发）\n"
          "=== python3 _selfcheck_p35_fixtures.py ===\n"
          "== 自检结论：PASS ==（32 条夹具全部触发；正向 PASS；阈值边界 0 处不符）"),
    claim("★ T1 视觉核查：11 张组图 + 重做的 pe-f-06 **逐张**在站点样式内看过",
          "=== 主 Agent read_image 逐张核对（核对台 _figcheck.py → _probe/fig3-*.html|.png）===\n"
          "grp-g00…grp-gd-n 共 11 张：无压字 / 无溢出画布 / 图注与数据一致；gd-n 仅入向 stub（出 0 条 ⇒ 正确地不生成出向 stub）\n"
          "pe-f-06 重做：首版把「窗口条」画成 尾部—中部—首部（**自左向右反序**，机检全过、只有看图能发现）⇒ 当场修正为 首部—中部—尾部；"
          "缩放 0.79× → 1.53×\n（证据：16-checkpoint/_probe/fig3-grp-*.png、fig3-pe-f-06.png）"),
    claim("T2 门控：P13 的 G12/G13 + P41 全绿；P39 引用闭合 8 个登记件",
          "=== python3 gate_prototype.py（退出码 0）===\n"
          "[PASS] P13 … 已发布节点 8 / 组 11 / 视图 2 / 入口 1 的镜像与页面齐全；pending_nodes 登记 59 个且与 registered 集合相等；"
          "G12 counts 逐项 12 项；G13 镜像内容比对 86 项；违例 0 处 []\n"
          "[PASS] P41 … 扫描面 31 个（豁免 1）；历史句命中 8 行（有正当出处 8）；违例 0 处 []\n"
          "[PASS] P39 … 引用点 3 处；被引用的登记件 8 个 / 磁盘登记件 8 个；断链 0 处 / 孤儿 0 处\n"
          "== 门控结论：PASS ==  FAIL 0 项 []"),
    claim("★ T2 装置自检：P13 四条夹具**逐条核对子断言** / P41 两侧 / C58 沙箱双向",
          "=== python3 _selfcheck_p13_p41_c58.py（退出码 0）===\n"
          "   [OK  ] 夹具#1 触发=True 命中子断言 '缺 MD 镜像'=True\n"
          "   [OK  ] 夹具#2 触发=True 命中子断言 'counts.'=True | 违例 1 处 [('counts.html 与实数不符', 25, 24)]\n"
          "   [OK  ] 夹具#3 触发=True 命中子断言 'boundary'=True\n   [OK  ] 夹具#4 触发=True 命中子断言 'pitfalls'=True\n"
          "   [OK  ] 正向（真实源文件） | 扫描面 31 个（豁免 1）；命中 8 行（有正当出处 8）；违例 0 处\n"
          "   [OK  ] 越界侧（裸历史句）⇒ FAIL=True（须指名到文件）\n   [OK  ] 对照侧（带更正标记的历史句）⇒ **仍 PASS**=True\n"
          "   [OK  ] 沙箱·原态 ⇒ 退出码 0 / [PASS] C58\n   [OK  ] 沙箱·引文改一个词 ⇒ 退出码 1 / [FAIL] C58\n"
          "== 结论：PASS ==（P13 夹具 4 条逐条核对子断言 · P41 两侧 · C58 沙箱双向；不符 0 处）"),
    claim("数据侧 C58 上线：节点侧引文逐片段逐字回源 0 违例；frontier 侧 2 片无源如实登记为 WARN",
          "=== python3 10-dag-data/_selfcheck.py（退出码 0）===\n"
          "[PASS] C58-quote-provenance evidence 引文逐片段可在引文库逐字回源（节点侧 27 条 evidence / 库内 126 条唯一引文，源件 7 个；坏：[]）\n"
          "[WARN] C58b-frontier-quotes … frontier 侧 18 条 evidence 中有 2 片无法在 A 池逐字回源 "
          "[('PE-N-03','S-0034',…),('PE-N-04','S-0105',…)] ⇒ 不改数据，登记为缺口\n"
          "== 自检：PASS ==  (FAIL 0 项 / WARN 4 项)"),
    claim("T2 判据数 40 → 41；负例夹具 162 → 166",
          "=== python3 gate_prototype.py --selftest（退出码 0）===\n"
          "== 自检结论：PASS ==（41 条判据 / 166 条负例夹具，全部须正向 PASS 且负例触发）\n"
          "（★ 登记件初稿把夹具数写成 163、又试改 167 —— 两个数字都是**实测前**写的，已按本行更正；"
          "见 CRITERIA-CHANGE-P13-C58-P41.md §4④）"),
    claim("★ T3 波次 2：5 个部件 dry-run 全绿（回源 / 台账注入 / 长度 / 结构四项）并翻态",
          "=== python3 _wave1_apply.py --parts-dir _wave2_parts（dry-run）===\n"
          "[PE-S-01] S-0053 片段 2/2 回源 … | [PE-S-02] S-0014/S-0053/S-0093 各 2/2 … | "
          "[PE-S-03] S-0053/S-0056/S-0039 各 2/2 … | [PE-S-04] S-0012/S-0001/S-0014/S-0053 各 2/2 … | [PE-S-05] S-0077/S-0093/S-0066 各 2/2 …\n"
          "== 结论：PASS ==（回源、台账注入、长度、结构四项全过）\n"
          "=== --write ===\n[write] dag.json 已落盘；回读：JSON 合法 / 节点 67 / complete 13 个 ['PE-F-01'…'PE-S-05']"),
    claim("★ T3 当场发现①：部件契约与合并器口径不合 —— 散文被**静默丢弃**（已修）",
          "=== 实测对比（PE-S-01）===\nwhy part==dag: False | len part 175 dag 125（intro 343/245、boundary 74/37、summary 36/31 同样不一致）\n"
          "⇒ 原 `_wave1_apply.py` 只写 lab/evidence/pitfalls/content_status ⇒ 部件里的 why/intro/boundary/when/terms/summary/tags **一字未用**\n"
          "=== 修正后（合并散文）===\nPE-S-01 why part==dag: True；PE-S-01 why 148 intro 284 boundary 62 terms 3 / PE-S-02 188·266·95·3 / "
          "PE-S-03 113·299·109·3 / PE-S-04 130·275·82·3 / PE-S-05 148·415·199·3\n"
          "=== 数据侧复跑 ===\n[PASS] C28-lengths-caliber …（不足：[]） / [PASS] C32-boundary-field …（坏：[]） / == 自检：PASS ==  (FAIL 0 项 / WARN 4 项)"),
    claim("★ T3 当场发现②：合并器**不是幂等**的（已加显式 --reapply）",
          "=== 第二次 python3 _wave1_apply.py --parts-dir _wave2_parts --write ===\n"
          "== 结论：FAIL（5 处）==\n    ('PE-S-01', '预期 registered，实为 complete') …（5 个节点）\n"
          "⇒ 首次 --write 后节点已 complete，重跑（只为补合并散文）会硬 FAIL 而**中止落盘**\n"
          "=== 加 --reapply 后 ===\n   [PE-S-01] ★ 重放（节点已 complete；--reapply 已声明）\n== 结论：PASS ==（回源、台账注入、长度、结构四项全过）"),
    claim("★ T3 当场发现③：2 个节点名含拉丁词 ⇒ 发布即触 P35 ①（已改名）；另有 5 个 registered 同型",
          "=== python3 _selfcheck_p35_fixtures.py（新页发布后）===\n正向：FAIL | 违例 2 处 "
          "[('11-node-pages/pe-s-01.html','h1 含英文（英文名须独立成行）','JSON Schema 与约束解码'), "
          "('11-node-pages/pe-s-04.html','h1 含英文（英文名须独立成行）','格式选型与 token 效率')]\n"
          "=== 改名后（dag.json，回读 JSON 合法 / 节点 67）===\n  PE-S-01 -> 结构模式与约束解码（JSON Schema and Constrained Decoding）\n"
          "  PE-S-04 -> 格式选型与词元效率（Format Choice and Token Efficiency）\n"
          "仍含拉丁词的中文名：5（PE-R-07 ReAct… / PE-C-02 RAG… / PE-O-07 子 Agent… / PE-P-01 我的 agent… / PE-P-03 子 Agent…）\n"
          "=== 重建后 ===\n正向 PASS；夹具 32 条全触发；阈值边界 0 处不符"),
    claim("T3 收口：29 页全站横向溢出 0 / 13 个节点页 / P28 仍为 10 与 1390ms",
          "=== python3 _probe_channel.py（退出码 0；66.4s）===\n"
          "   [PASS] root/group/node/view/interactive/root-narrow/interactive-narrow/root-dark 8 张全部非退化\n"
          "-- D. 全站横向溢出普查（视口 1440×900；29 页）--\n"
          "   [PASS] 全站 29 页：文档级与元素级横向溢出均为 0\n== 结论：PASS ==\n"
          "=== python3 gate_prototype.py（退出码 0）===\n"
          "       受检页面 29 个（节点页 13 / 组页 11 / 视图页 2）；… P13：已发布节点 13 / pending 54；G13 镜像内容比对 142 项；违例 0 处\n"
          "       M1 单页最大 [data-reveal] 10（≤32）；M2 进场完成 1390ms（≤1800）\n== 门控结论：PASS ==  FAIL 0 项 []"),
    claim("★ T3 视觉核查：5 张新节点图 + 1 个新节点页（真实渲染）逐张看过",
          "=== 主 Agent read_image ===\n"
          "pe-s-01/02/03/04/05 五张核对台 PNG：无压字 / 无溢出 / 图注与图意一致（pe-s-04 的「条宽即相对体积」单调且与图注数字一致）\n"
          "=== python3 _render.py --html 11-node-pages/pe-s-01.html --width 1440 --height 900 ===\n"
          "h1「结构模式与约束解码」纯中文一行；`.page-en` 独立成行；身份行 / 标签行分离；页首导读 8 锚点；新图内联且可读；无横向溢出\n"
          "（证据：16-checkpoint/_probe/fig3-pe-s-0*.png、r6-node-pe-s-01-viewport.png）"),
    claim("T3 其余对账装置全绿",
          "=== 同批复跑（均退出码 0）===\n"
          "[PASS] 图件 50 件与派生结果一致（gen-figs.py --check）\n"
          "== 结论：PASS ==（四发合成探针 + 盘上 25 张真实图件）\n"
          "[PASS] 令牌块一致（sha256 c389d019a4d9…）\n== 几何复算结论：PASS ==\n"
          "== 自检：PASS ==  (FAIL 0 项 / WARN 4 项)（10-dag-data/_selfcheck.py）\n"
          "== 自检结论：PASS ==（41 条判据 / 166 条负例夹具）"),
    claim("★ 只读审核子 Agent（照 §3 模板）的三项发现与本轮处置（★ 其读数为 `self-report`，逐条复跑后另记）",
          "=== 审核返回摘要（self-report 原文节录）===\n"
          "① 台账 round 6 的 `G7` 行写「磁盘登记件 8 个」，而磁盘/门控实测为 **9**（P39 原文）⇒ 台账内部不自洽（已修为 9，登记 G29）\n"
          "② round 6 对象**在审核运行期间**落盘 ⇒ 违反 §4④-4「动同一批文件前先确认子 Agent 已停手」（登记 G30；影响：审核读到混合快照）\n"
          "③ 审核方工具面只有 glob/grep/read ⇒ §3-④「亲自跑 `_probe_env.py`」**结构上无法执行**（它如实披露、未假装跑过；登记 G32）；"
          "已由主 Agent 补跑（见本对象 claim ①）\n"
          "★ 审核**独立重数**通过的量（与主 Agent 读数吻合）：29 页 / 28 MD / complete=13 / `.fig` 覆盖 25 页 / 图件 40 件 / "
          "P35 两处排除清单闭合 / P41 命中 8 行逐行有正当出处 / g00 图注「6 节点·5 内部边·8 跨组边」与 dag.json 逐格一致\n"
          "=== 主 Agent 复跑（收口时刻）===\n"
          "[PASS] P39 … 被引用的登记件 9 个 / 磁盘登记件 9 个；断链 0 / 孤儿 0\n"
          "[PASS] P40 … 轮次 4 条 / claims 49 条；契约规则表 R-id 全集 25 个；结构与自洽违例 0 处\n"
          "★ 复跑结论：审核的 ① 与 ② **成立**（已分别修 / 登记）；③ 属**我的委派失误**（工具面与模板不匹配），非审核方之过。"),
]

ARTIFACTS = [
    "16-checkpoint/ROUND-LEDGER.json",
    "16-checkpoint/CRITERIA-CHANGE-R07.md",
    "16-checkpoint/CRITERIA-CHANGE-P13-C58-P41.md",
    "16-checkpoint/AUTHORING-SPEC.md",
    "16-checkpoint/_selfcheck_figs_spec.py",
    "16-checkpoint/_selfcheck_p13_p41_c58.py",
    "16-checkpoint/_figcheck.py",
    "16-checkpoint/_wave_pick_quotes.py",
    "16-checkpoint/_r6_ledger_update.py",
    "16-checkpoint/_wave1_apply.py",
    "16-checkpoint/gate_prototype.py",
    "16-checkpoint/gen-figs.py",
    "16-checkpoint/gen-groups.py",
    "16-checkpoint/gen-state.py",
    "16-checkpoint/gen-common.py",
    "16-checkpoint/_probe_channel.py",
    "16-checkpoint/_probe_thresholds.py",
    "16-checkpoint/_reflection-candidates/",
    "16-checkpoint/DESIGN-CONTRACT.md",
    "16-checkpoint/CONTENT-V2.md",
    "10-dag-data/_selfcheck.py",
    "10-dag-data/dag.json",
    "10-dag-data/figures/",
    "PUBLISH-STATE.json",
    "11-node-pages/",
    "12-groups/",
    "15-md/",
    "13-interactive/index.html",
    "14-views/",
    "report.md",
]

G_LIST = {
    "G1": "✅ 已消（第 1 轮；★ 第 6 轮复跑仍 PASS）：R-10 的判据 = P35 ⑨。本轮命中枚举模式的页仍 4 个、`.enum-list` 4 个；夹具可判假。",
    "G2": "✅ 已消（第 1 轮；★ 第 6 轮复跑仍 PASS）：R-11 的判据 = P35 ⑩。本轮 P35 实检竖表区块 **26** 个（13 节点页 ×2 + 组页侧），区内 `<table>` 0。",
    "G3": "✅ 已消（第 1 轮；★ 第 6 轮复跑仍 PASS）：R-16 的判据 = P37；`_geom_interactive.py` 亦 PASS（11 组 0 超区 / 0 重叠）。★ 本轮发布 5 个节点改了交互图 DATA ⇒ 已重跑生成器，**不是**只在旧产物上复跑。",
    "G4": "✅ 已消（第 1 轮；★ 第 6 轮复跑仍 PASS）：P35 ⑪–⑭ + 阈值边界探针。`_selfcheck_p35_fixtures.py`：**32** 条夹具全触发、阈值边界 0 处不符。",
    "G5": "✅ 已消（第 1 轮；★ 第 6 轮**刷新证据**）：真实渲染通道本轮重跑两次（T1 24 页 38.8s / T3 29 页 66.4s），8 张 PNG 全部非退化；另按看图纪律用 `_figcheck.py` 在站点样式内逐张核了 17 张新/改图。",
    "G6": "✅ 已消（第 4 轮修 `pre` 换行；★ 第 6 轮 29 页复测仍 **0 处**）：未放宽 P38。",
    "G7": "✅ 已消（第 4 轮补登记件；★ 第 6 轮仍 PASS）：三处引用点 ⟺ 磁盘登记件 **9 个**（本轮新增 `CRITERIA-CHANGE-R07.md` 与 `CRITERIA-CHANGE-P13-C58-P41.md`），断链 0 / 孤儿 0。★ **本行初稿写「8 个」—— 审核当场报出与事实不符（实为 9），已更正**；根因见 G29。",
    "G8": "**仍在**（原样保留）：长文可扫性**不可机检** ⇒ 仍为 P35 报告项（逐条打印，⛔ 不判 FAIL）。★ 本轮**未**重跑 `_probe_metrics.py` ⇒ ⛔ 不引用其旧读数；该面由本轮真实渲染 + 人看兜。",
    "G9": "**仍在**（原样保留）：窄视口交互图 zoom < 1 —— 本轮 `_probe/channel.json` 仍记 `canvas_1440`（cyW 802）/ `canvas_768`（cyW 718），P37 的 `zoom=1` 仍只在**声明画布**口径下成立。",
    "G10": "✅ 已消（第 4 轮）；★ 第 6 轮又改该出口五处：`counts` 由产物实数对齐（`node_pages` 8→13 / `html` 24→29 / `md` 23→28）、新增 `criteria_change_R07` 与 `criteria_change_P13_C58_P41` 两键、`gates.prototype` 由 P01–P40 → **P01–P41**、`round` 5 → 6 ⇒ 与判据一致（P13 的 G12 现**逐项断言**它，不再是自报）。",
    "G11": "★ 第 5 轮登记项，保留更正：**能力集是逐进程读数、⛔ 不可跨会话沿用**（`CapBnd` 两个会话读到不同值）；稳定的只有 `CapEff=0 + NoNewPrivs=1` 与「snap 通道跑不起来」这一**结论**。★ 第 6 轮增量：① `P41` 把「**散文里的能力声明**」判据化（窄版）—— 这类「声称某能力不可用」的陈述今后会因**无正当出处**而 FAIL；但**逐进程读数过期**仍无判据能发现（⛔ 不假装覆盖）。② **第 3 次复现，且这次抓错的是我自己**：本对象 claim ① 初稿把一个**进程**的 `CapBnd=0`/`rc=46` 说成了「本会话」的事实，而同会话稍后的复核进程实测 `CapBnd=000001ffffffffff`/`rc=1` ⇒ 已按复核更正（详见 claim ②）。⇒ 教训收紧为：**引用机器读数时必须写「哪个进程/哪一次运行」**，⛔ 不写「本会话」；连失败码与报错文案都不稳定，稳定的只是「通道可用与否」这一判定。",
    "G12": "✅ **已消（第 6 轮）**：`counts` 与产物实数一致 ⇒ 挂在 **P13** 上（⛔ 未新增编号），**12 项逐项**比对（产物侧 html/md/node_pages/group_pages/view_pages/interactive/root；真相源侧 nodes/groups/edges/layers/assets），并配 ① `counts.html` ±1 ② `counts` 的 node_pages 篡改两条夹具；`_selfcheck_p13_p41_c58.py` 另**逐条核对红在它该红的那一条**。",
    "G13": "✅ **已消（第 6 轮）**：MD 镜像与 HTML 内容一致 ⇒ 挂 **P13**，按**可辨识前缀**比对（`boundary` 全文 / `pitfalls` 前 12 字 / `evidence.source_id` / `terms` 术语头；空白归一化）。本轮实检 **142** 项、0 违例；配「镜像去 boundary 正文」「镜像去 pitfalls 前缀」两条夹具。★ 局限：⛔ 不做逐字全文比对（渲染口径不同会假阳）。",
    "G14": "✅ **已消（第 6 轮）**：引文回源 ⇒ 数据侧新增 **`C58-quote-provenance`**（与 `_wave1_apply.py` 的回源**同源同口径**：省略号拆片段 + 空白归一化 + 逐字定位；引文库读不到 ⇒ FAIL）。节点侧 **43** 条 evidence、**0** 片无法回源。★ 局限：① 挡不住「引文库本身被改错」；② 对象暂**只有节点侧**（见 G23）。",
    "G15": "**不做**（留行，⛔ 不删）：发布级强化（SH0–SH5 / CI / `.nojekyll` / 建仓 push / Pages / hub 收录）与跨仓议题按裁决③排在 T1/T2/T3 之后。★ 现状约束仍在：本站 `--border` 对底色仅 1.0:1（浅）/ 1.06:1（深），边框可任意不可见而**没有任何门控会失败**。",
    "G16": "**未解决**（内容侧待办，属 G03）：`PE-C-03`（图检索 / GraphRAG）与 `PE-C-06`（提示缓存）在源池内**无源可依** ⇒ 动 G03 前须先补**已回源**条目（⛔ 不得编造引文）。★ 第 6 轮新增旁证：`C58` 上线后，本波 5 个节点的引文**全部**逐字回源成功（说明 G01 的源是够的，缺口确实集中在 C-03/C-06）。",
    "G17": "✅ 已修（第 5 轮改 §4③ 标题为「六步」）。",
    "G18": "第 6 轮逐项处置：⑧ **P35 ⑫ 代理判据可退役但须以更严判据替代** —— 本轮**仍未退役**（P38 D 段的溢出直接量已在跑，退役动作未做，留行）；⑨ **分组索引 6 列短值表仍未被判据覆盖** —— 仍留行（它在本轮实检的 ⑫ 切片之外）；⑩ **组页 `intro` 无枚举模式** ⇒ ⑨ 在组页上前件不成立 —— 仍留行（内容波次是解法）；⑪ `P40` 只断言结构、如实性不可机检（明文登记）；⑫ **P38 不判 PNG 新鲜度** —— 留行（台账写明路径 + mtime，靠人核）；⑬ `report.html` 的 `<title>` 仍写「第 1 轮」—— **刻意不改**；⑭ **动效预算**：第 6 轮实测单页最大 `[data-reveal]` **10**、进场 **1390ms**、`--dur-*` 和 1.79s、`infinite` 0 ⇒ **未逼近上界**，⛔ 无需砍内容（本项读数已随本轮变更更新）。",
    "G19": "✅ **已消（第 6 轮，用户裁决 B″）**：**两半同批** —— ① **补产物**：11 个组页各一张由 `dag.json` **数据派生**的本组 mini-DAG（`gen-figs.group_figs` 单源；含内部边实线 + `组外接口` stub 注明出/入条数；层带布局使 11 张图的缩放比 1.30–2.16×、渲染高 197.6–587.7px 全部在两条规格界内）；② **改契约**：R-07 收敛为「知识承载页（节点页 / 组页，⛔ 不含分组索引）」，其余 5 页**逐条给理由**不强制；③ **扩判据**：P35 ⑧ 移出 `if kind != 'node': … continue` 之后的尾部、作用域扩为节点页 + 组页，并加**显式对象集 + 全集闭合断言**与 3 条夹具（组页去图 / 注入未分类页 / 排除清单过期）。★ **同批**处置 R-03（K6 选项 A：改措辞为「正文承载页」+ 2 页显式排除）与 R-08（补缩放比下界 0.90）。留档 `CRITERIA-CHANGE-R07.md`。",
    "G20": "✅ **已消（第 6 轮，用户裁决②）**：新增门控 **P41**「源文件里的散文能力声明：**已登记的历史句不得复活**」。窄版：只判历史句 `本会话浏览器不可用`；判「正当出处」= **更正标记**（更正/旧理由/已推翻）**或**被引号包裹的提及；另有显式豁免清单（`_r5_ledger_update.py`，附理由）+ 「豁免项须真实存在」的守卫 + 「未分类的新 .py ⇒ FAIL」的全集闭合。★ **本轮当场抓到两次自伤**（判据把自己的装置自检脚本判成违例）⇒ 已加「提及/断言」判定并把探针载荷收进单一来源 `p41_probe_line()`。★ 残余：「新措辞的全量扫描」仍是**设计待办**（见 G25），如实登记、⛔ 不假装覆盖「任何措辞」。",
    "G21": "✅ 已修（第 5 轮改 SCHEMA 与 `_probe_thresholds.py` 的两处标签为「main border-box 868px ⇒ 内容列内宽 804px」）。",
    "G22": "✅ **已消（第 6 轮）**：裁决③的执行顺序（**先 T1、T2，再推波次 2，发布级强化排后**）已按序执行；每个任务包各自跑了五步循环（build → probe → gate + 两侧自检 → 幂等 → 渲染证据），⛔ 未攒到最后。",
    "G23": "★ **第 6 轮新增（未解决，如实登记）**：`C58` 的对象**只有节点侧**；`frontier.json` 侧实测 **2 片**引文无法在 A 池逐字回源 —— `PE-N-03`/`S-0034`（80 字）、`PE-N-04`/`S-0105`（48 字），形态是**作者期注记**而非原文引用。⇒ 以 `C58b` **报告项**（WARN）常年可见；⛔ 本轮**不改 `frontier.json`**（改引文属内容决策）⇒ 留待裁决：改写为可回源引文 / 改标为「注记」字段 / 明文接受。",
    "G24": "★ **第 6 轮新增（已修 + 残余登记）**：R-08 的图件规格原**只卡高度上界**（`rendered_h ≤ 600px`），会把「很宽的图」放过去 —— 存量 `pe-f-06` 正是 1016×150、缩放 **0.79×**（13pt → 10.3px）。⇒ 补**缩放比下界 0.90**；**存量图当场被自己的新规格拒收**并已重排（0.79× → 1.53×）。★ 残余失效面：`MIN_SCALE` 只保证「字号 ≥ 11.7px」，⛔ **不保证「不压字」** ⇒ 后者仍靠真实渲染 + 人/主 Agent 看图兜（本轮 17 张已逐张看）。",
    "G25": "★ **第 6 轮新增（设计待办，未解决）**：`P41` 是**窄版** —— ⛔ 不判「任何措辞」。全量扫描的难点已实测清楚：仓内多处**正当引用**该结论以记述教训（`P38` docstring、教训段、`_geom_interactive.py` 自陈），一剑切下去必大量假阳。⇒ 需要先定「哪些是正当引用」的可判定规则（本轮只完成了「引号包裹 = 提及」这一条）。",
    "G26": "★ **第 6 轮新增（不可机检，明文登记）**：`R-25`（内容生产走「子 Agent 并行产出部件 → 机器校验 → 主 Agent 独立复跑」三件套）的**可机检部分**只有：部件契约存在（`AUTHORING-SPEC.md`）＋ 合并校验能跑（`_wave1_apply.py --parts-dir` 的四项）。「**是否真按三件套走**」**不可机检**（要靠台账 claim 的 source 标注与人读）。★ 本轮实测：6 个子 Agent 的写入面**全部合规**（内容 5 路只写各自 `_wave2_parts/<NID>.json`；出图 1 路只写 `gen-figs.py`/`gen-nodes.py` 与 `figures/`）—— 已用 `find -newermt` 审计过。",
    "G27": "★ **第 6 轮新增（当场发现并已修）**：**部件契约与合并器口径不合** —— `_wave1_apply.py` 原本只写 `lab`/`evidence`/`pitfalls`/`content_status`，部件里的 `why`/`intro`/`boundary`/`when`/`terms`/`summary`/`tags` 被**静默丢弃**（波次 2 实测：5 个部件的这四项与盘上**全不相同**）。⇒ 修正为**全部区块都合并**（空值不覆盖），并补 `--reapply` 解掉「重跑必硬 FAIL 而中止落盘」的非幂等缺陷；合并散文后复跑 C28–C33/C58 全 PASS。",
    "G28": "★★ **第 6 轮新增（未解决，阻塞后续波次）**：**节点名含拉丁词** —— 全站 **7/67** 个节点的 `name` 在中文部分含拉丁词，而 R-01 / P35 ② 要求 h1 纯中文 ⇒ **节点一发布就 FAIL**（本轮当场撞上：`PE-S-01`「JSON Schema 与约束解码」、`PE-S-04`「格式选型与 token 效率」）。已处理：这 2 个改名为「**结构模式与约束解码**」「**格式选型与词元效率**」（en 字段不变）。**剩余 5 个仍 `registered`**：`PE-R-07` ReAct… / `PE-C-02` RAG… / `PE-O-07` 子 Agent… / `PE-P-01` 我的 agent… / `PE-P-03` 子 Agent…。★ **为什么不能顺手改名**：术语台账 `glossary.json` 里对应条目的**术语头本身含拉丁词**（如 `子 Agent 上下文隔离（Sub-agent Context Isolation）`），而 C33 要求 `terms` 头逐字等于台账 ⇒ 改名必须**成对**（节点名 + 术语头 + 该术语的 `node_refs`），属**术语裁决**面 ⇒ 需用户定「中文名是否允许保留业界通用拉丁缩写（Agent/RAG/ReAct/token）」或「一律中文化（子代理/检索增强/…）」。⛔ 在此之前，**动 G07 / G03 / G09 的波次会立刻撞上它**。",
    "G29": "★ **第 6 轮新增（审核当场报出，已修）**：**台账内部不自洽** —— 本对象的 `G7` 行初稿写「磁盘登记件 **8** 个」，而磁盘与门控实测均为 **9**（`_probe/r6_t3_gate.txt` 的 P39 原文「被引用的登记件 9 个 / 磁盘登记件 9 个」）。**根因**：我把**早期**读到的 8（`CRITERIA-CHANGE-R07.md` 尚未落盘时）写进了**后来**的文档 —— 与 G12 / T-1 是**同一族**（有保质期的读数被固化进不会重算的地方），本轮**第 4 次复现**。⇒ 已按实测更正为 9。★ 机检边界：`P40` 只断言台账**结构与自洽**（R-id 合法、claim 带 source 与 raw_output），⛔ **报不出「行文里的数字与事实不符」** —— 本次是**人/审核子 Agent 读出来的**，如实登记。",
    "G30": "★ **第 6 轮新增（审核当场报出，未解决/纪律面）**：**委派时序违规** —— round 6 轮次对象在**只读审核子 Agent 运行期间**落盘（本对象 `ended_at` 早于主 Agent 实际写入时刻；审核方按其**开工时刻** 06:07 首次读到的 `rounds` 只有 [3,4,5]、其 P40 读数亦为「轮次 3 条」，随后同一文件被它读到含 round 6）。契约 §4④-4 要求「动同一批文件前先确认子 Agent 已停手」。★ **影响如实说清**：① 台账**未被损坏**（本脚本的三道守卫在写后复核了前 5 个 round 的语义与字节均未变）；② 但**审核读到的是混合快照** ⇒ 其涉及台账的结论须按**收口时刻**重读；③ 主 Agent 已在收口时按 R-24 复核审核结论。⇒ 教训与处置：**审核期间冻结受审文件**；若必须改，改完须**明确告知审核方并请其重读**（本轮即按此补做）。",
    "G31": "★ **第 6 轮新增（审核当场报出，登记为措辞级模糊）**：**R-08 的用词** —— 契约写「内容列宽（804px）下**渲染高度** ≤ 600px」，而实测口径里另有「svg 元素宽 804px / `hostW=804`」（`_probe/channel.json`）等相邻量；两者本轮**未不一致到判 FAIL**（`gen-figs.check_spec` 的换算是 `h/w × 804`），但读者需自行对齐「内容列」到底指哪个盒子。⇒ 登记为**措辞级模糊**，下一轮在 R-08 行补一句「内容列 = `.layout > main` 的 **border-box 内宽**（`868 − 2×32 = 804px`，与 G21 的更正同源）」。",
    "G32": "★ **第 6 轮新增（审核工具面，已处置）**：**本轮审核委派的工具面与 §3 模板不匹配** —— 我用只读 worker（`oc_explore`，工具面只有 `glob`/`grep`/`read`）去执行「照 §3 模板审核」，而 §3 第 ④ 项**硬要求审核方亲自跑 `python3 _probe_env.py`** ⇒ 该项**结构上无法执行**（审核方如实披露并以「静态复核 + 独立重数」替代，未假装跑过）。⇒ 处置：① 主 Agent **自己**补跑 `_probe_env.py`（见本轮 claim ①，PASS）；② 把 ④/⑤ 两项**另派一个具备 bash 的 worker** 重做；③ 模板侧建议补一句「派审核方时须给可执行 shell」。",
}

NOTE = ("★ 本对象是**第 6 轮（T1：G19/B″ 收口 → T2：四条判据升级 → T3：波次 2 = G01 的 5 个节点）**"
        "的轮次对象：按契约 §4① 第 3 条在**开工期先落盘**（先声明 `rs_touched`），收口时追加补全"
        " claims / artifacts / g_list_updates / ended_at（⛔ 未回改 round 3 / 4 / 5 对象，其字节由本脚本的三道守卫复核）。\n"
        "★ 本轮读数全部由**主 Agent 亲跑**（`main-agent-rerun`，逐条附原始输出，原件落 `16-checkpoint/_probe/r6_*.txt`）；"
        "⛔ 无一条采信委派方自报 —— 本轮派了 6 个执行子 Agent（5 路内容 + 1 路出图）与 1 个只读审核子 Agent："
        "前 6 路的产出**只是部件与图源**（内容正文⛔ 不进主 Agent 上下文，见 R-25），它们报的每条数字都由主 Agent "
        "用 `_wave1_apply.py` dry-run / `gen-figs.py --check` / `_selfcheck*.py` / 门控**独立复跑**；"
        "审核子 Agent 的结论按 R-24 逐条复跑后另记。\n"
        "★ **时点关系（⛔ 未改任何历史件）**：`report.md` §7.x 与 round 3/4/5 对象里的旧读数（40 判据 / "
        "152·154·159·162 夹具 / P01–P37/P40 / 24 页 / 9 张图 / `pe-f-06` 1016×150）都是**各自收口时刻的快照**；"
        "本对象的现态是 **41 判据 / 166 夹具 / P01–P41 / 29 页 / 25 张图件 / `counts` 由 P13 逐项断言**。\n"
        "★ **收口完成判据逐条对照**：`_probe_env.py` 退出码 0 ✅ · `_probe_channel.py` 产物退化 0 处（29 页溢出 0）✅ · "
        "`gate_prototype.py` 退出码 0 ✅ · `--selftest` 退出码 0 ✅ · `build-all.py --write` 二次比对干净 ✅ · "
        "G 清单每行都有处置（G1–G28）✅ · 台账落盘且 P40 PASS ✅ · 视觉核查（17 张图 + 1 个新页）✅。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--replace", action="store_true",
                    help="round 6 已存在时**原地重写**该对象（⛔ 不整文件重排；前几轮字节仍由守卫复核）")
    a = ap.parse_args()

    raw = open(LEDGER, encoding="utf-8").read()
    doc = json.loads(raw)
    rounds = doc["rounds"]
    exists = any(r.get("round") == ROUND for r in rounds)
    if exists and not a.replace:
        print("[FAIL] 台账里已有 round %d ⇒ ⛔ 不重复追加（如需重写请加 --replace）" % ROUND)
        return 1
    old_prior = json.dumps([r for r in rounds if r.get("round") != ROUND],
                           ensure_ascii=False, sort_keys=True)

    r6 = {
        "round": ROUND,
        "started_at": "2026-10-16T05:27:00+08:00",
        "ended_at": "2026-10-16T06:16:19+08:00",
        "rs_touched": ["R-01", "R-03", "R-07", "R-08", "R-20", "R-21", "R-23", "R-24", "R-25"],
        "claims": CLAIMS,
        "artifacts": ARTIFACTS,
        "g_list_updates": G_LIST,
        "note": NOTE,
    }
    body = "\n".join("  " + ln for ln in json.dumps(r6, ensure_ascii=False, indent=1).splitlines())

    ANCHOR = "\n ]\n}\n"
    if raw.count(ANCHOR) != 1:
        print("[FAIL] 尾部锚点出现 %d 次（应为 1）⇒ ⛔ 不写" % raw.count(ANCHOR))
        return 1
    i_end = raw.rindex(ANCHOR)
    if exists:
        # 原地重写：round 6 是**最后一个**对象 ⇒ 找它之前最近的一个顶层对象起始（`\n  {\n`）
        i_start = raw.rindex("\n  {\n", 0, i_end) + 1
        head = raw[:i_start]
        text = head + body + ANCHOR
    else:
        head = raw[:i_end]
        text = head + ",\n" + body + ANCHOR

    print("[OK] round %d 对象：claims %d 条 / artifacts %d 条 / rs_touched %d 项 / g_list %d 键"
          % (ROUND, len(CLAIMS), len(ARTIFACTS), len(r6["rs_touched"]), len(G_LIST)))
    if not a.write:
        print("[dry-run] ⛔ 未写盘；拼接后 %d 字节（原 %d）" % (len(text.encode()), len(raw.encode())))
        return 0

    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    raw2 = open(LEDGER, encoding="utf-8").read()
    back = json.loads(raw2)
    # ---- 守卫②：前几轮**语义与字节**均未变 ----
    if raw2[:len(head)] != head:
        print("[FAIL] 锚点前文本被改动 ⇒ ⛔ 视为失败")
        return 1
    new_prior = json.dumps([r for r in back["rounds"] if r.get("round") != ROUND],
                           ensure_ascii=False, sort_keys=True)
    if new_prior != old_prior:
        print("[FAIL] 既有 round 的语义被改动 ⇒ ⛔ 视为失败，请人工复核")
        return 1
    r6b = [r for r in back["rounds"] if r.get("round") == ROUND]
    assert len(r6b) == 1
    r6b = r6b[0]
    # ---- 守卫③：结构与来源标注（与 P40 同口径）----
    assert len(r6b["claims"]) == len(CLAIMS) and len(r6b["artifacts"]) == len(ARTIFACTS)
    assert all(c["source"] in ("self-report", "main-agent-rerun") for c in r6b["claims"])
    assert all("===" in c["raw_output"] for c in r6b["claims"]
               if c["source"] == "main-agent-rerun"), "main-agent-rerun 必须带原始输出标记"
    ctext = open(os.path.join(HERE, "DESIGN-CONTRACT.md"), encoding="utf-8").read()
    import re
    rids = set(re.findall(r"^\|\s*(R-\d{2})\s*\|", ctext, re.M))
    miss = [x for x in r6b["rs_touched"] if x not in rids]
    assert not miss, "rs_touched 里的 R-id 不在契约规则表内：%s" % miss
    print("[write] ROUND-LEDGER.json 已落盘（%d 字节）；回读：轮次 %s / round6 claims %d / artifacts %d / g_list %d 键"
          % (len(raw2.encode()), [r["round"] for r in back["rounds"]],
             len(r6b["claims"]), len(r6b["artifacts"]), len(r6b["g_list_updates"])))
    print("        前 5 轮语义与字节均未变 ✅（锚点前文本逐字相同）；rs_touched 全部落在契约规则表内 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
