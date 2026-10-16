#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r5_ledger_update.py —— 把第 5 轮的收口读数写进 `ROUND-LEDGER.json` 的 round 5 对象。

## 为什么要脚本（而不是手改 JSON）
台账里有多条**很长的中文 JSON 字符串**（raw_output 逐字贴原始输出）。手改易把引号/转义写坏，
而"台账写坏"这件事**恰恰是 P40 要防的**。⇒ 用脚本：先做**格式守卫**（确认盘上文件就是
`json.dumps(..., indent=1, ensure_ascii=False)` 的输出），再按 id 定位 round 5 对象替换字段，
写完立即回读校验。

## 纪律
* ⛔ **只改 round 5 对象**：round 3 / round 4 字节不动（D4 §D③：台账**追加**，不回过改旧对象）。
* 每条 claim 标 `source` 并附**原始输出**（`main-agent-rerun` 的 raw_output 必须含 `===`）。
* 本件是**一次性**收口件，跑完即完成使命（保留在盘的目的是可复核）。

用法：python3 _r5_ledger_update.py [--write]
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ROUND-LEDGER.json")


def claim(fact, raw, src="main-agent-rerun"):
    return {"fact": fact, "raw_output": raw, "source": src}


ARTIFACTS = [
    "16-checkpoint/ROUND-LEDGER.json",
    "16-checkpoint/CRITERIA-CHANGE-P22.md（新增：两态配额 → 状态↔内容一致性）",
    "16-checkpoint/CRITERIA-CHANGE-P05-R5.md（新增：boundary 字段化执行 + why 上限/intro 下限按真实渲染重导）",
    "16-checkpoint/_b1_boundary_review.md（新增：67 条 boundary 改判表）",
    "16-checkpoint/_b1_prefill_boundary.py（新增：预填助手，dry-run 默认）",
    "16-checkpoint/_b1_emit_review.py（新增：改判表生成件）",
    "16-checkpoint/_probe_thresholds.py（新增：阈值重导取证，只打印）",
    "16-checkpoint/_wave1_content.json（新增：波次 1 内容草稿的载体）",
    "16-checkpoint/_wave1_apply.py（新增：合并 + 引文回源校验）",
    "16-checkpoint/gate_prototype.py（P22 重写 / P05 加 boundary 三条 / P01 加 boundary / 上限常量重导 / 夹具）",
    "16-checkpoint/gen-common.py（prose_html 支持 boundary 字段）",
    "16-checkpoint/gen-nodes.py（sec-why 读 boundary 字段 + 5 条 NODE_FIG）",
    "16-checkpoint/gen-md.py（MD 镜像补「适用边界」块）",
    "16-checkpoint/gen-figs.py（新增 5 张自制图 pe-f-02…06）",
    "16-checkpoint/gen-state.py（CHANGE_DECL_4/5 + html_count 修 bug + ROUND=5 + pending_note 去轮次写死）",
    "16-checkpoint/SCHEMA.md（两态一致性与配额段重写 / boundary 入字段表 / 上限重导与口径统一）",
    "10-dag-data/_selfcheck.py（C23–C27 重写 / C28·C28b·C28c 口径统一 / C32 改字段断言）",
    "10-dag-data/dag.json（67 节点全部加 boundary；9 个双标记节点的 intro 边界移出；PE-R-02/PE-P-02 补写机制句；波次 1 的 5 个节点补 lab/evidence/pitfalls 并翻 complete）",
    "10-dag-data/figures/pe-f-02…pe-f-06 的 .dot 与 .svg（5 张新增自制图，入库产物）",
    "11-node-pages/pe-f-02.html … pe-f-06.html（5 个新节点页）",
    "15-md/nodes/pe-f-02.md … pe-f-06.md（5 个新 MD 镜像）",
    "04-prototype/PUBLISH-STATE.json（round=5、counts.html 改为派生、gates 新增两个登记件键、pending_nodes 64→59）",
    "16-checkpoint/_probe/channel.json + 8 张 PNG（本轮重跑）+ wave1-pe-f-02/06-1440x900.png（新增渲染证据）",
    "_audit_r5_probe.py（任务根；★ 本轮**审核子 Agent** 留下的只读探针：P22 是否更严 / boundary 能否绕过 / 两侧漂移 / MD 与 HTML 一致性，"
    "全部突变在内存 deepcopy 内做，⛔ 未写产物、⛔ 未改判据；与任务根既有的 `_selfcheck_stage1.py` 同一层）",
    "report.md（第 5 轮：追加 §八，含审核结果与处置）· report.html（同源重渲染）",
]

CLAIMS = [
    claim("门控全量跑 P01–P40：FAIL 0 项、退出码 0；受检产物 52 个（HTML 24 / MD 23）",
          "=== python3 gate_prototype.py（退出码 0）===\n受检产物：52 个（HTML 24 / MD 23）\n== 门控结论：PASS ==  FAIL 0 项 []\n（★ 19→24 页 / 18→23 镜像：本轮新落 5 个节点页与 5 个 MD 镜像）"),
    claim("负例自检：40 条判据 / 159 条夹具全部触发、退出码 0（夹具 154→159：P22 +2、P05 +3）",
          "=== python3 gate_prototype.py --selftest（退出码 0）===\n== 自检结论：PASS ==（40 条判据 / 159 条负例夹具，全部须正向 PASS 且负例触发）\n（★ 判据数仍为 40 ⇒ 与 CONTINUE-PROMPT-D4 §H-1 第 4 条的「判据 40 条」一致；新增可判假面只加夹具不加编号）"),
    claim("环境能力探测（收口复跑，R-21）：非 snap 内核在盘、playwright 1.63.0 可用；CapEff/CapBnd 均为 0 解释 snap 通道为何结构性不可用",
          "=== python3 _probe_env.py（收口复跑；退出码 0）===\n非 snap 内核：found=True（1 个候选）\n  /home/zako-mio/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome\nplaywright(python)：found=True version=1.63.0\n== 结论：PASS ==（至少一条**不同源**的通道可用 ⇒ 可以做真实渲染验证）\n   事实已落盘：16-checkpoint/_probe/env.json"),
    claim("验证通道 + 产物非退化 + 全站横向溢出：★ 在 build-all --write **之后**重跑（R-22），故 P38 读的是本轮 manifest；24 页溢出 0",
          "=== python3 _probe_channel.py（退出码 0）===\n-- D. 全站横向溢出普查（视口 1440×900；24 页）--\n   [PASS] 全站 24 页：文档级与元素级横向溢出均为 0\n== 结论：PASS ==（用时 38.6s；manifest → 16-checkpoint/_probe/channel.json）"),
    claim("幂等落盘：首次 --write 新增 10（5 节点页 + 5 MD）/ 修改 15；随即复跑作二次比对 ⇒ 写入 0 / 删除 0 / 孤儿 0 / 干净",
          "=== python3 build-all.py --write（退出码 0）===\n== build-all write ==\n预期产物 48 个文件\n  added      10\n      11-node-pages/pe-f-02.html … pe-f-06.html（5）\n      15-md/nodes/pe-f-02.md … pe-f-06.md（5）\n  modified   15\n      11-node-pages/pe-f-01.html（★ 对端节点已发布 ⇒ 兄弟 chip 由徽标变真链接）\n      12-groups/g00…g09/gd-n/index.html、14-views 2 页、13-interactive/index.html、index.html、PUBLISH-STATE.json\n  deleted    0\n（随后复跑一次）\n  实际写入 0 个 / 实际删除 0 个 / 孤儿残留 0 个\n  二次比对干净：True"),
    claim("数据侧自检（★ 本轮并入收口协议）：complete 8 / registered 59，C23–C33 全 PASS、FAIL 0 / WARN 3",
          "=== python3 10-dag-data/_selfcheck.py（退出码 0）===\n[PASS] C23-status-enum content_status 仅两态（越界：[]）\n[PASS] C24-complete-count complete ≥3（实为 8：['PE-F-01', 'PE-F-02', 'PE-F-03', 'PE-F-04', 'PE-F-05', 'PE-F-06', 'PE-R-02', 'PE-P-02']）\n[PASS] C25-registered-count registered = 全量 - complete（实为 59，应为 59）\n[PASS] C26-two-state-sum 两态合计 = 全量注册数（8 + 59 = 67）\n[PASS] C27-content-status-consistent 内容已填即须翻 complete（仍标 registered 而三块非空：[]）\n[PASS] C28-lengths-caliber why / intro 下限（caliber 口径，与门控 P05 同源同值）全部满足（不足：[]）\n[PASS] C29-complete-blocks complete 节点 8 区块全非空（空：[]）\n[PASS] C31-evidence-contract evidence 每条字段齐全且可回源（坏：[]）\n[PASS] C32-boundary-field 每个节点 boundary 非空 / 不与 why·intro 整句重复 / 正文不残留引导串（坏：[]）\n[WARN] C28b-upper-report 上限**报告项**（caliber 口径；实测一屏可读量 = why 693 / intro 777；summary 80 本轮未重导）：超出 0 处 []\n[WARN] C28c-caliber-report why 实测区间 61–147；intro 实测区间 129–228；summary 实测区间 23–38\n== 自检：PASS ==  (FAIL 0 项 / WARN 3 项)"),
    claim("解锁两态契约（P22 + C24–C27）：同一份 8/59 数据在两份实现下全绿；旧配额下本波必 FAIL",
          "=== gate --only P22 + _selfcheck C23–C27（改后同一份数据）===\n[PASS] P22 content_status 状态↔内容一致性（complete 8 区块非空 / registered 三块必空 / 禁半填）\n       complete 8 个（8 区块全非空）；registered 59 个（lab/evidence/pitfalls 必须为空；why ≥60 / intro ≥120 且 summary 通过结构性三条、无空洞占位）；两态合计 67 = 全量注册数；违例 0 处 []\n⇒ 改前：门控 `registered ≥60` 最多再翻 4 个；数据侧 C24「complete 恰好 3 个」+ C27 固定名单 ⇒ **一个都不能翻**。本波要翻 5 个 ⇒ 不开锁则第 1 步即 FAIL。"),
    claim("B-1 boundary 字段化：67/67 切出、8 个双标记节点人工择一、0 处跌破下限；★ 渲染平价（pe-f-01.html 逐字节不变）",
          "=== _b1_prefill_boundary.py（dry-run）+ _b1_emit_review.py --write + build-all --dry-run ===\n-- 统计 --\n   有显式标记并切出边界：67 / 67\n   仅 why 有标记：58；仅 intro 有标记：0；两处都有标记：9\n   NEEDS_MANUAL（须人工看/改写）：8 个（均为「双标记且两版文字不一致 ⇒ 须人工择一并合并」）\n[write] dag.json 已落盘；回读校验：JSON 合法、节点 67 个、含 boundary 的 67 个\n[write] _b1_boundary_review.md（5716 字节；回读行数 94）\n- boundary 为空的：0；正文残留引导串的：0；跌破各自下限的：0\n★ 渲染平价：build-all --dry-run 里 11-node-pages/pe-f-01.html 列在 unchanged ⇒ 字段化前后**逐字节相同**\n★ 两条 complete 节点因 C9 补写而预期变化：PE-R-02（intro 122→204）、PE-P-02（143→193）\n[PASS] P01 真相源 JSON 合法且必填字段齐全\n[PASS] P05 字段长度约束（caliber 口径）＋ summary 结构约束 ＋ `boundary` 必填/不重复/不残留"),
    claim("B-2 阈值按真实渲染重导：why 一屏可读量 693 / intro 777（均为报告项）；intro 下限无法由渲染导出（如实登记）",
          "=== python3 _probe_thresholds.py（退出码 0；⛔ 不落产物）===\n-- A. 版式实测 --\n   11-node-pages/pe-f-01.html     内容列宽  868.0px · 根字号 16px · 行高 28px\n-- B/C. 逐区块（视口 900px）--\n   pe-f-01 sec-why    行 5 · 块高 148.0px · caliber 114 · 每行 22.8 · px/caliber 1.298 · 一屏 693 caliber\n   pe-f-01 sec-intro  行 7 · 块高 208.0px · caliber 188 · 每行 26.9 · px/caliber 1.106 · 一屏 813 caliber\n   pe-r-02 sec-why    行 5 · 块高 152.0px · caliber 118 · px/caliber 1.288 · 一屏 698 caliber\n   pe-r-02 sec-intro  行 8 · 块高 236.0px · caliber 204 · px/caliber 1.157 · 一屏 777 caliber\n   pe-p-02 sec-why    行 4 · 块高 120.0px · caliber 114 · px/caliber 1.053 · 一屏 855 caliber\n   pe-p-02 sec-intro  行 7 · 块高 208.0px · caliber 193 · px/caliber 1.078 · 一屏 835 caliber\n-- D. 反解 --\n   why    一屏容量：min 693 / max 855 caliber\n   intro  一屏容量：min 777 / max 835 caliber\n⇒ WHY_UPPER_REPORT 120 → 693；INTRO_UPPER_REPORT 250 → 777（两者**只能作报告项**）；\n  intro 的**下限**渲染无法导出（只给上界）⇒ 保留内容侧理由并如实登记为未达成"),
    claim("波次 1 内容：5 个节点补齐 lab/evidence/pitfalls 并翻 complete；14 条引文**逐片段回源**通过",
          "=== python3 _wave1_apply.py --write（退出码 0）===\n   回源引文库：7 个文件 / 126 条唯一引文\n   [PE-F-02] S-0012 tier=official 片段 2/2 回源；S-0001 1/1；S-0004 1/1\n   [PE-F-03] S-0001 1/1；S-0019 1/1；S-0032 3/3\n   [PE-F-04] S-0038 2/2；S-0004 2/2\n   [PE-F-05] S-0013 1/1；S-0001 1/1；S-0002 1/1\n   [PE-F-06] S-0063 1/1；S-0001 1/1；S-0056 1/1\n== 结论：PASS ==（回源、台账注入、长度、结构四项全过）\n[write] dag.json 已落盘；回读：JSON 合法 / 节点 67 / complete 8 个 ['PE-F-01','PE-F-02','PE-F-03','PE-F-04','PE-F-05','PE-F-06','PE-P-02','PE-R-02']\n★ 回源口径：每条 quote 按省略号拆片段，逐片段在 01-research/evidence/A*.json 的已回源引文里逐字定位（⛔ 挡不住引文库本身写错）\n★ url/tier 一律由脚本按 source_id 从 sources.json **注入**（⛔ 不手抄）"),
    claim("几何复算（交互图产物侧）PASS：11 组下钻 0 超区 0 重叠",
          "=== python3 _geom_interactive.py（退出码 0）===\n[8] 下钻视图 11 组：节点数 [6, 5, 8, 7, 8, 9, 6, 4, 3, 7, 4]；超区 0 组；重叠 0 处\n== 几何复算结论：PASS =="),
    claim("令牌 / 图件对账：均 PASS（图件 8 → 18 件）",
          "=== python3 gen-tokens.py --check（退出码 0）===\n[PASS] 令牌块一致（sha256 c389d019a4d9…）\n=== python3 gen-figs.py --check（退出码 0）===\n[PASS] 图件 18 件与派生结果一致\n（★ 8 → 18 件 = 本轮新增 5 张自制图的 .dot + .svg）"),
    claim("P35 夹具自检（29 条全触发 / 阈值边界 0 处不符）与开关行为自检（37 例 FAIL 0）",
          "=== python3 _selfcheck_p35_fixtures.py（退出码 0）===\n== 自检结论：PASS ==（29 条夹具全部触发；正向 PASS；阈值边界 0 处不符）\n=== PATH=… node _selfcheck_switches.mjs（退出码 0）===\n== 开关行为自检：PASS（37 例，FAIL 0）=="),
    claim("★ 本轮渲染证据（新鲜度靠本行 + 人核：P38 **不判** PNG 新鲜度）",
          "=== _probe_channel.py 重新生成 8 张（含窄视口 768 与深色）+ 新增节点页实拍 ===\n_probe/wave1-pe-f-02-1440x900.png  1440x900 · 唯一色 4978 · 亮度 22.4–255.0 · 363281 B · sha256 d71026ff99fc833b… · 退化=[]\n_probe/wave1-pe-f-06-1440x900.png  1440x900 · 唯一色 5296 · 亮度 22.4–255.0 · 411557 B · sha256 a541695234da7a1f… · 退化=[]\n（mtime = 2026-10-16 04:06；`_probe/*.png` 由 `_probe_channel.py` 于本轮 38.6s 的一次运行内重写）"),
    claim("★ 本轮当场报出的三条真实缺陷（判据起作用的正例，⛔ 非回归）",
          "=== 本轮当场报出的三条真实缺陷 ===\n① **P12 自伤**：CHANGE_DECL_5 初稿把「第 3 节」写成内部编号记号（`§3`），而该文本会随 gen-state 落到公开产物 ⇒\n[FAIL] P12 公开产物无内部编号 / 绝对路径 / 主机名 / 令牌串\n       受检产物 42 个；命中 1 处 {'内部编号': [('PUBLISH-STATE.json', '§3')]}\n   处置：改写为「的 C3 裁决」⇒ 转绿（**修产物文本，⛔ 未放宽 P12**）\n② **图件规格**：`gen-figs.check_spec` 当场拒收 —— pe-f-05 首版 360.5x273（609px）、pe-f-04 第二版 435.5x353（652px）均 > 600px ⇒ 两次重排图件（⛔ 未用 CSS 缩放掩盖）\n③ **MD 镜像静默丢边界**：`gen-md.node_md` 原本只印 `why`，而边界原先寄生在 `why` 里 ⇒ 字段化后镜像会**静默丢失**边界，且该面**无判据覆盖**（P13 只断言镜像存在）⇒ 同批补上独立「适用边界」块"),
    claim("★ 本轮审核子 Agent（照 DESIGN-CONTRACT §3 模板）的结论：3 项违反 + 5 项未覆盖 + 3 项契约陈旧（★ 本条的读数为**委派方自报**，未由主 Agent 复跑的部分不得当读数用）",
          "=== 审核返回摘要（self-report，原文节录）===\n"
          "逐条复核 R-01…R-24：门控 P01–P40 全 PASS（退出码 0）、自检 40 判据/159 夹具全触发、数据侧 C01–C57 PASS。\n"
          "发现两条真实缺陷：① R-07「每页 ≥1 自制图」产物未满足——24 页仅 9 页含 figure，11 组页/根入口/交互页/学习路径页共 15 页无图；"
          "P35 ⑧ 实装在 kind!=node 分支之后只查节点页，标题却写「每页有图」⇒ 兼犯 R-23（判据作用域≠声明作用域）。"
          "② R-21：gate_prototype.py:1004/3075/3300 与 gen-interactive.py:120 仍留「本会话浏览器不可用」并据以只用代理判据。"
          "另：SCHEMA「内容列 868px」与 R-08/P34 的 804px 是同一元素两种口径（868=804+2×32 padding）。\n"
          "★ 审核另给出两条反例：P22「内容薄但 8 区块非空」在新判据下全 PASS（旧配额会 FAIL）；"
          "boundary 的 5 种近似篡改全部 PASS（只有整句逐字复制被抓）。",
          src="self-report"),
    claim("★ 主 Agent 对上述三项事实陈述的独立复核（R-24：子 Agent 的「完成」有保质期，须按收口时刻复核）",
          "=== 主 Agent 独立复跑（3 项全部成立）===\n"
          "① 图件缺口：自写脚本逐页统计 ⇒\n"
          "   HTML 页总数 24；含 figure 的 9 页；无 figure 的 15 页\n"
          "   无 figure 的页：12-groups/g00…g09.html、12-groups/gd-n.html、12-groups/index.html、"
          "13-interactive/index.html、14-views/01-learning-path.html、index.html\n"
          "② 陈旧散文：grep 命中 gate_prototype.py:1004 / :3082 / :3307 与 gen-interactive.py:120（4 处）\n"
          "③ 口径：grep 得 gen-common.py:834 `.layout>main{padding:0 var(--space-5)}`、:391 `*{box-sizing:border-box}`、"
          "tokens.generated.css:50 `--space-5: 2rem` ⇒ 868 − 2×32 = **804** ✓ 与 gen-figs.CONTENT_COL_PX 同值\n"
          "⇒ 三项均成立；处置见 g_list_updates 的 G19（图件缺口）/ G20（散文能力声明无判据）/ G21（868 命名）与两份登记件的追记"),
    claim("★ 本轮审核的处置（⛔ 未放宽任何判据；以产物为准并登记为契约缺陷）",
          "=== 审核 → 处置（逐条）===\n"
          "① P35 ⑧ 的**声明与对象对齐**：docstring / 代码注释 / CHECKS 标题三处由「每页 ≥1 图」改为「**节点页** ≥1 图」"
          "（判据行为未变，只把声明对齐到对象）⇒ 这是 R-23 的正确处置；R-07 的「每页」缺口登记为 G19。\n"
          "② 陈旧散文 4 处改为「理由回到代理判据自身的局限」：gate P11 note / P35 ⑫ 说明（两处）/ gen-interactive advance 注释。\n"
          "③ SCHEMA §3 与 _probe_thresholds.py 的「内容列宽 868px」更正为「main border-box 868px ⇒ 内容列内宽 804px」。\n"
          "④ CRITERIA-CHANGE-P22.md：C3 的「更严」改为「仅在一致性维度更严」（并加 §5 第 0 条反例）。\n"
          "⑤ CRITERIA-CHANGE-P05-R5.md：加 §6 第 6 条（5 种近似篡改全 PASS 的实测）。\n"
          "⑥ CRITERIA-CHANGE-P35-G4.md：**追加**追记（⛔ 不改上文，含读者须知与 G20 登记）。\n"
          "★ P38 的能力复核只扫 manifest 的两个 found 布尔（⛔ 不扫散文）⇒ 该面登记为 G20，本轮**未**升级为判据。",
          ),
    claim("★ 视觉核查（第 5 轮补做；主 Agent 亲自看图 `read_image`，⛔ 非机检、⛔ 非采信他人）",
          "=== 视觉核查：站点样式 + 单张图的最小核对台（_probe/fig2-*.html → fig2-*.png，1100px；另以真实页面截图对照）===\n"
          "① pe-f-02 分层与缓存面：三层纵排 + 右侧「稳定前缀 / 易变后缀」双列，`特权递减` 与 `失配` 标注清楚 ⇒ ✅\n"
          "② pe-f-03 标签边界：左列四个 <标签> 盒汇聚到「模型」，右侧 `对照` 指向「裸文本」note，`<user_input>` 红色标「不可信」⇒ ✅\n"
          "③ pe-f-04 示例边际收益：左链（零样本→3→10）+ 右反转支（条件反转→推理模型降准→改写为要点可重新获益），两列层级对齐 ⇒ ✅\n"
          "④ pe-f-05 具体性 vs 可验证性：上下两维 + 双向箭头「不矛盾」+ 右侧米色 note ⇒ ✅\n"
          "⑤ pe-f-06 位置偏差：**可读但偏弱** —— 首/中/尾只是并排三个盒子（未画出「窗口条」），到三个工程动作的虚线箭头过淡 ⇒ ⚠ 登记为 D6 的 T-5（建议并入第 6 轮 T1，⛔ 不重开本轮）\n"
          "★ 一处**核对手法**的踩坑（⛔ 不是图件缺陷）：首版核对页未内联站点令牌块 ⇒ 图件里的 var(--…) 全部落到默认值 ⇒ 盒子纯黑、盒内文字黑底黑字 ⇒ 一度误判「图坏了」。图件**按设计**依赖页面令牌（P36 ③ 要求令牌化、随主题）⇒ 看图必须在站点样式内看。\n"
          "★ 清理：已删 11 个**误导性**核对台文件（figcheck.html / fig-pe-f-0*.html / figcheck-pe-f-0*.png）；保留带站点样式的 _probe/fig2-*.html 与 fig2-*.png（8 + 5 件）作为可复用核对台。\n"
          "★ 本 claim 的价值：给出**机器判据给不出的证据**（P36 只断言内联/尺寸/色值/a11y/字形覆盖/规格，⛔ 看不见「一眼能不能读懂」），并更正留档里一条关于**本 Agent 自身能力**的错误陈述（「无视觉」）——它与「某能力不可用」同属**会过期、必须当场复算**的一类（R-21 的形态）。",
          ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    raw = open(LEDGER, encoding="utf-8").read()
    doc = json.loads(raw)

    # ---- 守卫①：语义守卫（对 round 3 / round 4 取规范形做前后比对）----
    # ★ 为什么不用「格式守卫」：本台账**不是**纯 dump —— 它的短数组（`rs_touched` 等）是**紧凑单行**写的，
    #   而 json.dumps(indent=1) 会把它们展开成多行 ⇒ 整文件重排会**churn 掉 round 3/4 的字节**
    #   （守卫首版正是这样拒绝写入的，见运行记录）。⇒ 改为**定点拼接**：只替换 round 5 对象的文本跨度。
    old_r34 = json.dumps([r for r in doc["rounds"] if r.get("round") in (3, 4)],
                         ensure_ascii=False, sort_keys=True)

    rounds = doc["rounds"]
    r5 = [r for r in rounds if r.get("round") == 5]
    if len(r5) != 1:
        print("[FAIL] 期望恰好 1 个 round=5 对象，实为 %d 个" % len(r5))
        return 1
    r5 = r5[0]
    before = json.dumps({k: v for k, v in r5.items()}, ensure_ascii=False, sort_keys=True)

    r5["artifacts"] = ARTIFACTS
    r5["claims"] = CLAIMS
    r5["ended_at"] = "2026-10-16T04:25:00+08:00"
    r5["g_list_updates"] = G_LIST
    r5["note"] = NOTE

    print("[OK] round 5 对象：claims %d 条 / artifacts %d 条 / g_list_updates %d 键"
          % (len(r5["claims"]), len(r5["artifacts"]), len(r5["g_list_updates"])))
    print("     旧对象字符数 %d → 新 %d" % (len(before), len(json.dumps(r5, ensure_ascii=False))))

    # ---- 守卫②：锚点必须唯一（定点拼接的前提）----
    ANCHOR = '   "started_at": "2026-10-15T18:41:00+08:00"\n  },\n'
    if raw.count(ANCHOR) != 1:
        print("[FAIL] 锚点出现 %d 次（应为 1）⇒ ⛔ 不写" % raw.count(ANCHOR))
        return 1
    head = raw[:raw.index(ANCHOR) + len(ANCHOR)]

    # 新 round 5 对象：indent=1 的规范形，再整体缩进 2 空格（它是数组的第 3 个元素）
    body = "\n".join("  " + ln for ln in json.dumps(r5, ensure_ascii=False, indent=1).splitlines())
    text = head + body + "\n ]\n}\n"

    if not a.write:
        print("[dry-run] ⛔ 未写盘；拼接后 %d 字节（原 %d）" % (len(text.encode()), len(raw.encode())))
        return 0

    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    raw2 = open(LEDGER, encoding="utf-8").read()
    back = json.loads(raw2)
    # ---- 守卫③：round 3 / round 4 **语义与字节**均未变 ----
    new_r34 = json.dumps([r for r in back["rounds"] if r.get("round") in (3, 4)],
                         ensure_ascii=False, sort_keys=True)
    if new_r34 != old_r34:
        print("[FAIL] round 3/4 语义被改动 ⇒ ⛔ 视为失败，请人工复核")
        return 1
    if raw2[:len(head)] != head:
        print("[FAIL] 锚点前文本被改动 ⇒ ⛔ 视为失败")
        return 1
    r5b = [r for r in back["rounds"] if r.get("round") == 5][0]
    assert len(back["rounds"]) == 3, "轮次数变了：%d" % len(back["rounds"])
    assert len(r5b["claims"]) == len(CLAIMS) and len(r5b["artifacts"]) == len(ARTIFACTS)
    assert all("===" in c["raw_output"] for c in r5b["claims"]
               if c["source"] == "main-agent-rerun"), "main-agent-rerun 必须带原始输出标记"
    assert all(c["source"] in ("self-report", "main-agent-rerun") for c in r5b["claims"])
    print("[write] ROUND-LEDGER.json 已落盘（%d 字节）；回读：轮次 %s / round5 claims %d / artifacts %d"
          % (len(raw2.encode()), [r["round"] for r in back["rounds"]],
             len(r5b["claims"]), len(r5b["artifacts"])))
    print("        round 3/4 语义与字节均未变 ✅（锚点前文本逐字相同）")
    return 0


G_LIST = {
    "G1": "✅ 已消（第 1 轮；★ 本轮复跑仍 PASS）：R-10 的判据 = P35 ⑨。本轮新增 5 个节点页后，命中枚举模式的页由 3 → **4**，`.enum-list` 4 个；判据仍可判假（2 条夹具）。",
    "G2": "✅ 已消（第 1 轮；★ 本轮复跑仍 PASS）：R-11 的判据 = P35 ⑩。本轮 P35 实检竖表区块 16 个、区内 `<table>` 0；新增的 5 个节点页证据/术语区同为竖表。",
    "G3": "✅ 已消（第 1 轮；★ 本轮复跑仍 PASS）：R-16 的判据 = P37；`_geom_interactive.py` 亦 PASS（11 组 0 超区 / 0 重叠）。★ 本轮发布 5 个节点改变了交互图 DATA（兄弟 chip 由徽标变真链接）⇒ 已重跑 `gen-interactive.py` 与几何复算，**不是**只在旧产物上复跑。",
    "G4": "✅ 已消（第 1 轮；★ 本轮复跑仍 PASS）：P35 ⑪–⑭ + 阈值边界探针。`_selfcheck_p35_fixtures.py`：29 条夹具全触发、阈值边界 0 处不符。",
    "G5": "✅ 已消（第 1 轮；★ 本轮**刷新证据**）：真实渲染通道本轮重跑 —— `_probe_channel.py` 8 张（38.6s，含窄视口 768 与深色）+ 新增节点页 2 张实拍，读数全部非退化；`_probe/env.json` 亦为收口复跑所得。",
    "G6": "✅ 已消（第 4 轮修 `pre` 的 `white-space:pre-wrap`；★ 本轮 24 页复测仍 0）：新增 5 个节点页的 `lab` 代码块经全站 24 页横向溢出普查 = **0 处**（⛔ 未放宽 P38）。",
    "G7": "✅ 已消（第 4 轮补登记件；★ 本轮 P39 复跑仍 PASS）：引用点 3 处 ⟺ 磁盘登记件 **7 个**，断链 0 / 孤儿 0。★ 本轮新增 **2 个**登记件（`CRITERIA-CHANGE-P22.md` / `CRITERIA-CHANGE-P05-R5.md`）已**同批**接入三处引用点（gate docstring / gen-state 的 CHANGE_DECL_4·5 / PUBLISH-STATE.gates）。",
    "G8": "**仍在**（★ 原样保留）：长文可扫性**不可机检** ⇒ 仍为 P35 报告项（逐条打印，⛔ 不判 FAIL）。★ 本轮**未**重跑 `_probe_metrics.py`（它是取证件、非判据）⇒ ⛔ 本行不引用其旧读数；该面由本轮真实渲染（`_probe/` 的 8 张 PNG + 2 张实拍）+ 人看兜。",
    "G9": "**仍在**（★ 原样保留）：窄视口交互图 zoom < 1 —— 本轮 `_probe/channel.json` 仍记 `canvas_1440`（cyW 802）/ `canvas_768`（cyW 718），P37 的 `zoom=1` 仍只在**声明画布**口径下成立；⛔ 未把 P37 口径推广到任意视口。",
    "G10": "✅ 已消（第 4 轮：`PUBLISH-STATE.gates.prototype` 已为 P01–P40）。★ 本轮又改该出口四处：新增 `criteria_change_P22` / `criteria_change_P05_R5` 两个键、`counts.html` 改为由 `complete` 派生、`round` 1 → 5、`pending_note` 去掉写死的轮次 ⇒ 仍与判据一致（判据数未变，仍 40）。",
    "G11": "★ 本轮新增登记项（开工期）：本会话 `_probe_env.py` 读到 `CapBnd = 0000000000000000`。"
           "⚠ **2026-10-16 更正（审核当场指出，主 Agent 复核成立）**：原行据此推断「snap 通道的不可用比第 4 轮更彻底」"
           "——**该推断撤回**。审核子 Agent 在本会话复跑同一探针读到 `CapBnd = 000001ffffffffff`，与第 4 轮一致。"
           "事实是：**能力集是逐进程/逐会话读数，不可跨会话沿用**；`CapEff = 0` 才是 snap 通道不可用的稳定原因（负对照 rc=1 亦稳定复现）。"
           "★ 这一条恰好复现了 R-21 的形态（把一个会过期的读数当已确立的事实）——只不过这次过期的是**机器读数**而非散文结论。"
           "⛔ 无判据能发现它过期（P38 只复算 manifest 的两个 found 布尔）⇒ 登记为 G20 的一部分。",
    "G12": "★ 本轮新增（**bug 已修 / 判据面未落实**）：`gen-state.py` 的 `html_count = 3 + …` 把节点页数**写死** ⇒ 一翻态就与产物数不符；已改为由 `complete` 派生。但「`counts` 与产物实数一致」**仍无判据**（P13 只断言 `counts` 是 dict）⇒ **登记为未落实**。"
           "★ **2026-10-16 用户裁决（写入留档）**：四条「已实现但无判据」的面**全部升级为判据** ⇒ 第 6 轮须把本条落成机检断言（建议挂在 P13 上：`counts.html == len(ctx.html)`、`counts.md == len(ctx.md)`、`counts.node_pages == len(complete)`、`counts.group_pages == len(groups)+1`）+ 负例夹具。执行见 `CONTINUE-PROMPT-D6.md` 任务包 T2。",
    "G13": "★ 本轮新增（**缺陷已修 / 判据面未落实**）：`gen-md.node_md` 原本只印 `why`，而边界原先寄生在 `why` 里 ⇒ 字段化后 MD 镜像会**静默丢失**「适用边界」；已同批补独立块。但「MD 镜像与 HTML 页内容一致」**无判据** ⇒ **登记为未落实**。"
           "★ **2026-10-16 用户裁决**：升级为判据 ⇒ 第 6 轮须断言「每条已发布节点的 MD 镜像包含其 `boundary` 原文、每条 `pitfalls` 的可辨识前缀、每条 `evidence` 的 `source_id`、每条 `terms` 的术语头」+ 负例夹具（把镜像里的边界行删掉 ⇒ 判 FAIL）。执行见 D6 任务包 T2。",
    "G14": "★ 本轮新增（**机制已建 / 未升级为判据**）：引文回源校验目前只存在于**作者期助手** `_wave1_apply.py`（按省略号拆片段，在 `01-research/evidence/A*.json` 的 126 条已回源引文里逐字定位），本轮 14 条引文全部通过。⛔ 它不是判据（构建链与门控都不跑）。★ 诚实边界：它挡「凭空写一句」，⛔ **不挡**「引文库本身被改错」。"
           "★ **2026-10-16 用户裁决**：升级为判据 ⇒ 第 6 轮须把它搬进数据侧自检（建议 `C58`：节点的每条 evidence quote 片段须能在 `01-research/evidence/A*.json` 里逐字定位）+ 负例夹具。执行见 D6 任务包 T2。",
    "G15": "★ 本轮按 `CONTINUE-PROMPT-D4.md` §E 判为**不做**（留行，⛔ 不删）：第 4 项**发布级强化**（SH0–SH5 / CI / `.nojekyll` / 建仓 push / 启用 Pages / hub 自动收录）与第 5 项**跨仓议题**（向 `fe-starter-kit` 提 `non-text` 档补 WCAG 1.4.11 式 3:1 下限）。⇒ **H-2 第 10–11 条不适用**（本轮**不声明**「可发布」）。★ 现状约束仍在：本站 `--border` 对底色仅 1.0:1（浅）/ 1.06:1（深），边框色可任意不可见而**没有任何门控会失败**。★ **2026-10-16 用户裁决（第 6 轮优先序）**：先收口 G19 与四条判据升级，**发布级强化排在其后** ⇒ 本项继续留行。",
    "G16": "★ 本轮新增（**内容侧待办**）：`PE-C-03`（图检索 / GraphRAG）与 `PE-C-06`（提示缓存）在 115 条源池内**无源可依**（本轮 G00 波次不含这两个节点）。⇒ 后续波次须先补**已回源**条目（`sources.json` 有 C37–C40 约束），⛔ 不得编造引文凑数。",
    "G17": "★ 本轮新增（**契约自身计数不一致，已修**）：`DESIGN-CONTRACT.md` §4③ 标题写「收口必做（**五步**）」而其下代码块为**六条**命令 ⇒ 本轮改标题为「六步」（⛔ 报告类历史段落不改，只改契约正文的计数）。",
    "G19": "★★ 本轮新增（**审核当场报出的真实契约缺口，⛔ 未修产品、已修声明**）：`DESIGN-CONTRACT.md` §1 R-07 与 "
           "`CONTENT-V2.md` 的措辞是「**每页** ≥1 自制图」，而产物的实际情况是 **24 页里只有 9 页有图**（8 个节点页 + "
           "`14-views/02-frontier.html`），**15 页无图**（11 个组页 + 分组索引 + 根入口 + 交互页 + 学习路径页）。"
           "判据侧 P35 ⑧ 的实装位于 `if kind != \"node\": … continue` 之后 ⇒ **只对节点页生效**，而它的标题与 docstring 却写「每页有图」"
           "⇒ 同时构成 **R-23 违反**（判据声明的作用域 ≠ 实现的作用域）。"
           "【处置】① **把声明对齐到对象**：P35 ⑧ 的 docstring / 代码注释 / CHECKS 标题三处改为「**节点页** ≥1 图」"
           "（判据行为一字未改，⛔ 不是放宽）；② **缺口如实登记为本行**：R-07 的「每页」这一半**未落实**，"
           "且 `CONTENT-V2.md` 的组页/视图页骨架表里本就没有图件项 ⇒ 契约正文与骨架表**自相矛盾**。"
           "③ 建议下一轮二选一：**(a) 改契约**（把 R-07 的措辞限定为节点页，与骨架表一致）或 **(b) 补图**"
           "（为 15 页各出一张自制图 —— 成本是 15 张 DOT，且会改变这些页的版式，须同批重跑 P28/P35/P36 与渲染证据）。"
           "⛔ 本轮**不擅自选**，因为这决定了「契约要不要改」，属用户裁决面。"
           "★★ **2026-10-16 用户裁决（写入留档）= 走 B″**：① **11 个组页补「本组诱导子图 + 对外依赖」的 mini-DAG**"
           "（由 `10-dag-data/dag.json` **数据派生**，⛔ 不用手绘 11 张）；② 契约措辞改为「**内容承载页（节点页 / 组页）"
           "≥1 图；导航·索引·交互·路径页不强制**」；③ 其余 4 页（分组索引 / 根入口 / 交互页 / 学习路径页）**写明不强制及其理由**"
           "（交互页本身就是图；索引页已有 11 组一览表；入口页职责是开门；路径页的全局拓扑由交互图承载）。"
           "⇒ 执行交第 6 轮（`CONTINUE-PROMPT-D6.md` 任务包 **T1**），且须同批落 `CRITERIA-CHANGE-R07.md`（六段范式）"
           "并把 P35 ⑧ 的作用域由「节点页」扩为「**节点页 + 组页**」+ 新增负例夹具（组页去图 ⇒ FAIL）。",
    "G22": "★ **2026-10-16 用户裁决（第 6 轮主线优先序，写入留档）**：**先**按裁决①（B″）收口 `G19` 与四条判据升级（裁决②），"
           "**再**推波次 2 = **G01 的 5 个节点**（`PE-S-01…PE-S-05`）；**发布级强化**（`G15`）排在其后。"
           "⇒ 第 6 轮的任务包顺序 = **T1（G19 收口）→ T2（四条判据升级）→ T3（波次 2）**，见 `CONTINUE-PROMPT-D6.md` §B。"
           "★ 三者同属一批：T1/T2 动判据与契约、T3 动产物 ⇒ 每完成一个任务包都要跑一遍五步循环"
           "（build → probe → gate + 两侧自检 → 幂等 → 渲染证据），⛔ 不得攒到最后。",
    "G20": "★★ 本轮新增（**审核当场报出；已修散文，判据面仍缺**）：判据/生成器文件里残留 4 处「**本会话浏览器不可用**」的陈旧散文"
           "（`gate_prototype.py` 的 P11 note、P35 ⑫ 说明两处、`gen-interactive.py` 的 advance 上界注释），"
           "并被用作「只能用代理判据」的理由 ⇒ **R-21 违反**（该结论早已被推翻：非 snap 内核一直可用，"
           "本轮复跑 `_probe_env.py` 再次证伪，且 `_probe_thresholds.py` 用同一内核取得了真实渲染读数）。"
           "【处置】① 4 处散文改为「理由回到**代理判据自身的局限**」（⛔ 不再以「浏览器不可用」为由），"
           "存量留痕件 `CRITERIA-CHANGE-P35-G4.md` 以**追加追记**方式更正（⛔ 不改上文）；"
           "② ★ **缺口**：`P38` 的能力复核**只扫 `_probe/channel.json` 的两个 `found` 布尔，⛔ 不扫源文件里的散文能力声明** "
           "⇒ 「文档声称某能力不可用」这一面**无判据**；同理，**能力集这类逐进程读数过期也无人能发现**（见 G11 更正）。"
           "建议下一轮升级为判据（扫源文件的能力声明并与探针读数比对）。"
           "★ **2026-10-16 用户裁决**：升级为判据 ⇒ 第 6 轮须设计一条「**源文件里的能力声明 vs 探针读数**」的机检断言"
           "（⚠ 易假阳：仓内多处**正当引用**该结论以记述教训，如 `gate_prototype.py` 的 P38 docstring 与教训段 ⇒ "
           "措辞规则必须先定「哪些是正当引用」再加负例夹具；建议先只做**已知 4 条历史句的复活守卫**（窄但无假阳），"
           "并把「新措辞的扫描」登记为设计待办）。执行见 `CONTINUE-PROMPT-D6.md` 任务包 T2。",
    "G21": "★ 本轮新增（**审核当场报出，已修**）：同一名词两个口径 —— `SCHEMA.md` §3 的 B-2 实测行与 `_probe_thresholds.py` 的输出标签"
           "都把 main 的 **border-box 宽 868px** 写成「内容列宽」，而 R-08 / P34 / `gen-figs.CONTENT_COL_PX` 的内容列是 **804px**。"
           "复算：`*{box-sizing:border-box}` + `.layout>main{padding:0 var(--space-5)}`（2×32px）⇒ 868 − 64 = 804 ✓。"
           "【处置】两处标签改为「main border-box 868px ⇒ 内容列内宽 804px」；★ 阈值推导本身不受影响（一屏可读量只用 `blockH / caliber`）。",
    "G18": "★ D4 §F 第 6–14 项的逐条处置（本轮）：⑥ G8 长文可扫性 = 报告项（见 G8 行）；⑦ G9 窄视口 zoom（见 G9 行）；⑧ **P35 ⑫ 代理判据可退役但须以更严判据替代** —— 本轮**未退役**（P38 D 段的溢出直接量已在跑，退役动作未做，留行）；⑨ **分组索引 6 列短值表仍未被判据覆盖** —— 本轮 P35 ⑫ 实检到该表 1 张（列数 6 > 3），但它在 `#sec-nodes`/`#sec-rel` 切片**之外**故未触发 FAIL ⇒ 留行；⑩ **组页 `intro` 无枚举模式** ⇒ ⑨ 在组页上前件不成立 —— 本轮未改写组页导读，留行（内容波次是解法）；⑪ **P40 只断言结构**、如实性不可机检（明文登记）；⑫ **P38 不判 PNG 新鲜度** —— 见本轮 claim ⑭（台账写明路径 + mtime，靠人核）；⑬ `report.html` 的 `<title>` 仍写「第 1 轮」—— **刻意不改**（front matter 属历史原文）；⑭ **动效预算**：本轮 P28 读数 = 单页最大 `[data-reveal]` **9**（≤32）、进场 **1330ms**（≤1800）、`--dur-*` 和 1.79s（≤3.6）、`infinite` **0**（≤12）⇒ **未逼近上界**，⛔ 无需砍内容。",
}

NOTE = ("★ 本对象是**第 5 轮（两态契约解锁 + 三项收口 + 内容波次 1）的轮次对象**：按契约 §4① 第 3 条在"
        "**开工期先落盘**（先声明 `rs_touched`），收口时**追加补全** claims / artifacts / g_list_updates / ended_at"
        "（⛔ 未回改 round 3 / round 4 对象，其字节未动）。"
        "★ 本轮全部读数由**主 Agent 亲跑**（`main-agent-rerun`，逐条附原始输出）；⛔ 无一条采信他人自报 —— "
        "本轮确实派了 3 个只读探索子 Agent（判据清单 / 源池可行性 / 两态契约考古），但其产出**只用于规划**，"
        "任何数字都在动手前由主 Agent 独立复算过（如「门控最多只能再翻 4 个」与「数据侧 C24 一个都不能翻」）。"
        "★ 时点关系（⛔ 未改任何历史件）：`report.md` §7.x 与 round 3/4 对象里的旧读数（40 判据 / 152·154 夹具 / "
        "P01–P37 / registered≥60 配额）都是**各自收口时刻的快照**；本对象的现态是 **40 判据 / 159 夹具 / "
        "P01–P40 / 配额已换判据**。"
        "★ 收口完成判据逐条对照：`_probe_env.py` 退出码 0 ✅ · `_probe_channel.py` 产物退化 0 处 ✅ · "
        "`--selftest` 退出码 0 ✅ · `build-all.py --write` 二次比对干净 ✅ · §2 G 清单每行都有处置 ✅（G1–G10 + 新增 G11–G18）· "
        "台账落盘且 P40 PASS ✅（见 claim ① 的门控结论）。")

if __name__ == "__main__":
    sys.exit(main())
