#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_r8_ledger_update.py —— 把**第 8 轮**对象追加进 `ROUND-LEDGER.json`（⛔ 不回改 round 3–7 的字节）。

## 为什么用**文本手术**而不是 `json.load → json.dump`
第 5/6/7 轮的写入器对本文件立了「历史轮次对象字节不得变动」的守卫，且本文件的缩进
（根键 1 空格 / 轮次对象 2 空格 / 其下键 3 空格）**不是**任何单次 `json.dumps` 的产物
—— 它是历轮**逐次文本追加**的结果。⇒ 本轮沿用同一手法：只在本文件**末尾的 `]` 之前**插入
第 8 轮对象，其余字节**一个都不动**（脚本自带守卫，见 `guards()`）。

## 契约依据（`DESIGN-CONTRACT.md` §轮次执行协议 ③④）
- 每条 claim 必须标 `source`（`self-report` / `main-agent-rerun`）并附 `raw_output` **原文**；
- `main-agent-rerun` 的 `raw_output` 必须带原始输出标记（`===`）；
- `rs_touched` 必须逐条声明本轮触碰的 R-xx（⛔ 不得为空、不得写契约规则表外的 id）。
机检判据 = **P40**（只断言结构与自洽，⛔ 不验证自述是否如实）。

## 用法
    python3 _r8_ledger_update.py            # dry-run：打印校验结果，⛔ 不落盘
    python3 _r8_ledger_update.py --write    # 落盘
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

# ---------------------------------------------------------------- 第 8 轮对象

STARTED = "2026-10-16T13:40:00+08:00"
ENDED = "2026-10-16T14:35:00+08:00"

RS_TOUCHED = ["R-07", "R-08", "R-09", "R-19", "R-20", "R-21", "R-22", "R-23", "R-24", "R-25"]

CLAIMS = [
    {
        "id": "C-R8-01",
        "claim": "发布仓建立且私密边界成立：仓根 = 任务根，入库面只含 `04-prototype/`（286 件 / 11M），"
                 "调研 / 需求 / 架构三层与过程证据（53M / 1742 文件）整层排除并归档到 `_LOCAL_ARCHIVE/`。",
        "source": "main-agent-rerun",
        "raw_output": "=== git ls-files | awk -F/ '{print $1}' | sort | uniq -c ===\n"
                      "      1 .gitignore\n    285 04-prototype\n"
                      "=== 私密性负向自检（`git ls-files` 对私密模式的命中数，须为 0）===\n"
                      "grep -E 'source-manual|A5-report-audit|_r6_backup|_r7_backup|_probe/|"
                      "_render-proof|_LOCAL_ARCHIVE|__pycache__|01-research|02-requirements|03-architecture' "
                      "⇒ 命中 0 行\n"
                      "=== git check-ignore -v 逐条复核 ===\n"
                      "01-research/source-manual.md → IGNORED\n"
                      "02-requirements/handoff.json → IGNORED\n"
                      "03-architecture/ADR-001-site-architecture.json → IGNORED\n"
                      "04-prototype/16-checkpoint/_LOCAL_ARCHIVE/REF-AKG-REPORT.md → IGNORED\n"
    },
    {
        "id": "C-R8-02",
        "claim": "判假探针实测出 **4 处判据对象缺陷**（⛔ 无一处是读码推断）：P09 把一切 `<link>` 当加载类资源、"
                 "P12 对属性值与 sitemap/robots 的 URL 载荷判「主机名」、P13 的 `counts.md` 与判据的「MD 数」"
                 "是两个口径、P12 对 `README.md` 这类元数据面不适用。",
        "source": "main-agent-rerun",
        "raw_output": "=== python3 _probe/r8_t1_p09_probe.py（节选，改前）===\n"
                      "变体                                     P09    P30    P15    P12\n"
                      "C0 现状（无新增）                             PASS   PASS   PASS   PASS\n"
                      "F1 +canonical（绝对自指）                      FAIL   PASS   PASS   FAIL\n"
                      "F2 +favicon rel=icon（相对）                   FAIL   PASS   PASS   PASS\n"
                      "F5 全套（SH4 标准档形态）                        FAIL   PASS   PASS   FAIL\n"
                      "=== 原子事实 ===\n"
                      "  canonical 绝对             -> [('link', 'https://…', '<link rel=\"canonical\" …>')]\n"
                      "  URL_HTTP_RE 对 canonical 绝对 URL 的判定：False（它只匹配 CSS url()）\n"
                      "=== CI 档当场抓出（改后）===\n"
                      "  [FAIL] P12 … 命中 1 处 {'主机名': [('README.md', 'zako-mio')]}\n"
                      "  [FAIL] P13 … 违例 1 处 [('counts.md 与实数不符', 50, 51)]\n"
    },
    {
        "id": "C-R8-03",
        "claim": "三条判据的对象收窄**全部带防退化断言**且逐条可判假：P09 负例 3→8 条、P12 1→2 条；"
                 "新增 A1–A7（7 条 / 9 夹具）与 S1–S11（11 条 / 18 夹具）；三条门控全 PASS。",
        "source": "main-agent-rerun",
        "raw_output": "=== python3 gate_prototype.py（全量）===\n"
                      "== 门控结论：PASS ==  FAIL 0 项 []\n"
                      "=== python3 gate_prototype.py --selftest ===\n"
                      "== 自检结论：PASS ==（41 条判据 / 176 条负例夹具，全部须正向 PASS 且负例触发）\n"
                      "=== python3 gate_a11y.py ===\n"
                      "== 门控结论：PASS ==  FAIL 0 项 []\n"
                      "=== python3 gate_a11y.py --selftest ===\n"
                      "== 自检结论：PASS ==（7 条判据 / 9 条负例夹具）\n"
                      "=== python3 gate_seo_meta.py ===\n"
                      "== 门控结论：PASS ==  FAIL 0 项 []\n"
                      "=== python3 gate_seo_meta.py --selftest ===\n"
                      "== 自检结论：PASS ==（11 条判据 / 18 条负例夹具）\n"
    },
    {
        "id": "C-R8-04",
        "claim": "幂等与既有判据面无回归：`build-all --dry-run` 差集 0；`gen-figs --check` 94 件一致；"
                 "`_selfcheck_figs_spec` 47 张真实图件全合规；`10-dag-data/_selfcheck.py` 退出码 0。",
        "source": "main-agent-rerun",
        "raw_output": "=== python3 build-all.py --dry-run ===\n"
                      "  added      0\n  modified   0\n  deleted    0\n  unchanged  104\n"
                      "=== python3 gen-figs.py --check ===\n[PASS] 图件 94 件与派生结果一致\n"
                      "=== python3 _selfcheck_figs_spec.py ===\n"
                      "[OK  ] 盘上真实图件 47 张全部合规（逐一复算，⛔ 不抽样）\n"
                      "== 结论：PASS ==（四发合成探针 + 盘上 47 张真实图件；不符 0 处）\n"
                      "=== python3 10-dag-data/_selfcheck.py ===\nDATA_EXIT=0\n"
    },
    {
        "id": "C-R8-05",
        "claim": "CI 三 job 契约在真实 GitHub Actions 上跑通（build → gate → deploy 全绿，本仓**首次**真 CI），"
                 "`_ci_gate.sh fast` 本地实跑亦 PASS。",
        "source": "main-agent-rerun",
        "raw_output": "=== gh run view 38861097316 --repo zako-mio/prompt-engineering-kg ===\n"
                      "✓ build in 18s\n✓ gate\n✓ deploy\nWATCH_EXIT=0\n"
                      "=== bash _ci_gate.sh fast（本地）===\n"
                      "== _ci_gate.sh [fast] 结论：PASS ==\nCI_FAST_EXIT=0\n"
    },
    {
        "id": "C-R8-06",
        "claim": "线上站点 9 个路径全部 200；两个页面**真实渲染 + 像素读数 + 逐张看图**均非退化；"
                 "hub 自动收录成立（`has_pages: true`，条目数 11）。",
        "source": "main-agent-rerun",
        "raw_output": "=== curl 状态码 ===\n"
                      "/                                      200\n"
                      "/11-node-pages/pe-a-01.html            200\n"
                      "/12-groups/g02.html                    200\n"
                      "/13-interactive/index.html             200\n"
                      "/sitemap.xml                           200\n"
                      "/robots.txt                            200\n"
                      "/og.png                                200\n"
                      "/favicon.svg                           200\n"
                      "/14-views/01-learning-path.html        200\n"
                      "=== PIL 读数（线上截图）===\n"
                      "r8_t4_live_root.png   1440x4811  唯一色 5258   956543 B  亮度  8.9.. 45.7  OK(非空)\n"
                      "r8_t4_live_node.png   1440x5235  唯一色 11116 1493057 B  亮度  8.1.. 52.9  OK(非空)\n"
                      "=== hub catalog（scripts/cli.py）===\n"
                      "catalog 含 prompt-engineering-kg: True\n条目数: 11\n"
                      "HIT: {\"name\": \"prompt-engineering-kg\", \"summary\": \"提示词工程知识全景图：67 节点 × 11 组"
                      " × 96 条依赖边…\", \"entry_url\": \"https://zako-mio.github.io/prompt-engineering-kg/\","
                      " \"has_pages\": true}\n"
    },
]

ARTIFACTS = [
    ".gitignore",
    ".github/workflows/pages.yml",
    "04-prototype/README.md", "04-prototype/.nojekyll", "04-prototype/favicon.svg", "04-prototype/og.png",
    "04-prototype/sitemap.xml", "04-prototype/robots.txt",
    "04-prototype/16-checkpoint/gate_a11y.py", "04-prototype/16-checkpoint/gate_seo_meta.py",
    "04-prototype/16-checkpoint/gen-meta.py", "04-prototype/16-checkpoint/_ci_gate.sh",
    "04-prototype/16-checkpoint/gate-manifest.json",
    "04-prototype/16-checkpoint/CRITERIA-CHANGE-R08.md",
    "04-prototype/16-checkpoint/_r8_ledger_update.py",
    "04-prototype/16-checkpoint/_LOCAL_ARCHIVE/REF-AKG-REPORT.md",
    "04-prototype/16-checkpoint/_probe/r8_t1_p09_probe.py",
    "04-prototype/16-checkpoint/_probe/r8_t1_p09_probe.txt",
    "04-prototype/16-checkpoint/_probe/r8_t3_ci_gate_fast.txt",
    "04-prototype/16-checkpoint/_probe/r8_t4_run_watch.txt",
    "04-prototype/16-checkpoint/_probe/r8_t4_live_root.png",
    "04-prototype/16-checkpoint/_probe/r8_t4_live_node.png",
    "04-prototype/16-checkpoint/_probe/r8_t4_hub_catalog.json",
    "04-prototype/10-dag-data/dag.json", "04-prototype/10-dag-data/figures/",
    "04-prototype/PUBLISH-STATE.json",
]

G_LIST = {
    "G15": "✅ **已消（第 8 轮）**：发布级强化**全部落地并线上验证** —— SH0–SH5 基线里缺的部分（SH4 元数据 / "
           "SH5 资产）补上；SH2 无障碍判据化；CI 三 job 在真实 Actions 上**首次**跑通；仓 "
           "`zako-mio/prompt-engineering-kg` 建成并 push；Pages 启用（`build_type: workflow`，"
           "★ 与同类站的 legacy 有意偏离，理由=legacy 不支持子目录发布）；hub 自动收录成立"
           "（`has_pages: true`，条目数 11）。★ **跨仓议题（P2）仍在**：本站 `--border` 对底色仅 "
           "1.0:1（浅）/ 1.06:1（深），⛔ 不在本仓修，应向共享令牌契约提 WCAG 1.4.11 式 3:1 下限。",
    "G31": "✅ **已消（第 8 轮）**：`R-08` 的「内容列」补上口径 —— 「＝ `.layout > main` 的 border-box 内宽 "
           "＝ 868 − 2×32 ＝ **804px**」（⛔ 不是 `body` 也不是 `.layout` 的宽度）。见 `DESIGN-CONTRACT.md` §1 R-08 行。",
    "G9": "**仍在（第 8 轮未动）**：窄视口交互图 zoom < 1（`canvas_768` cyW 718 ⇒ 视口 768 时 0.8755）。"
          "P37 的 `zoom=1` 只在**声明画布**口径下成立。★ 本轮把它写进 `gate-manifest.json` 的 `not_covered`。",
    "G18": "第 8 轮逐项：⑧ P35 ⑫ 代理判据仍未退役（留行）；⑨ 分组索引 6 列短值表仍未被判据覆盖（留行）；"
           "⑩ 组页 `intro` 无枚举模式（留行）；⑪ P40 只断结构、如实性不可机检（明文登记）；"
           "⑫ P38 不判 PNG 新鲜度（留行）；⑬ `report.html` 的 `<title>` 仍写「第 1 轮」（**刻意不改**，"
           "front matter 属历史原文）。★ 本轮**新增 3 项**：⑭ A/S 两段是两个独立脚本，⛔ 漏调其中一个"
           "**不会有任何报警**（装置覆盖缺口）；⑮ `gate-manifest.json` 自身无判据校验它的编号集合与实现一致；"
           "⑯ `_probe/` 目录无判据管辖。三者均已写进 `gate-manifest.json` 的 `not_covered`。",
    "G33": "**仍在（第 8 轮未动）**：`_wave_pick_quotes.py` 的 URL→id 映射假阴性（`setdefault` 建索引）。"
           "判「引文可用性」应以 `_wave1_apply.py` 的 dry-run 为准。",
    "G38": "**仍在（第 8 轮未动）**：`PE-E-03` / `PE-A-05` 的核心机制句在引文库中无一手可引用原文。"
           "两名子 Agent 如实上报、⛔ 未编造 ⇒ 本轮不改数据。",
    "G39": "**仍在（第 8 轮未扩面）**：任务根的两个探针 `.py` 与 `_probe/` 下的脚本不在 P41 扫描面内。"
           "★ 本轮**把它们排除出本仓**（`.gitignore` 已挡），但 P41 的扫描面本身未扩（避免同轮第三次判据变更）。",
    "G16": "**仍在（第 8 轮未动）**：`PE-C-03`（图检索/GraphRAG）与 `PE-C-06`（提示缓存）在源池**无源可依**"
           "（实测：`_wave_pick_quotes.py \"GraphRAG\"` / `\"提示缓存\"` 均返回空集）⇒ 动 G03 前必须先补"
           "**已回源**条目，⛔ 不得编造引文。",
    "G23": "**未解决（留行）**：`C58` 对象只有节点侧；`frontier.json` 侧 2 片引文无法在 A 池逐字回源。"
           "本轮 C58b 仍以 WARN 常驻，⛔ 未改 `frontier.json`。",
    "G25": "**未解决（第 8 轮未动）**：`P41` 仍是窄版（⛔ 不判「任何措辞」）。",
    "G32": "**已处置（留行以免被读作已消）**：审核委派的工具面须含可执行 shell。★ 第 8 轮**未派审核子 Agent**；"
           "该纪律已写进 `AUTHORING-SPEC.md` 与契约 §3 的既有条目。",
    "G42": "★ **第 8 轮新增（本轮最值钱的一条）**：**判据对象 ≠ 断言对象**同型缺陷**第 4–6 次复发** —— "
           "本轮 6 条实测缺陷里 **4 条**属此型（P09 的「一切 link 皆资源」、P12 的「属性值/URL 载荷算正文」、"
           "P13 的「镜像数 vs 全部 .md」、P12 对元数据面不适用）。★ **它们全部潜伏至今**，因为"
           "「对象过宽」在**存量产物**上恰好不触发（存量页本来没有 canonical、README 本来不在发布面）"
           "⇒ 只在**下一个必然发生的改动**（SH4 落地、README 进发布面）时才炸。"
           "⇒ 可复用认识：**判据的对象边界必须用「下一个会加进来的东西」去撞一次**，"
           "⛔ 不能靠「存量全绿」证明它对。",
    "G43": "★ **第 8 轮新增**：**跑子集不是「少跑一点」，它会换一个扫描面** —— `P13` 的 "
           "`('counts.md 与实数不符', 50, 51)` 与 `P12` 的 `README.md` 命中**只在 `_ci_gate.sh fast` "
           "（`--only` 子集）里被翻出来**。⇒ 分档执行除了「省预算」，还有**第二个作用**："
           "不同的执行顺序/对象组合会让不同的对象错配暴露出来。⛔ 但这也意味着**分档不等于等价**，"
           "两档都必须真跑过（本轮两档都跑了，全绿）。",
    "G44": "★ **第 8 轮新增（已处置）**：**子 Agent 把临时自查件落在 `16-checkpoint/` 顶层**"
           "（`_selfcheck_sh4_head.py`）⇒ 违反 `AUTHORING-SPEC.md` 禁忌 #11（顶层 `*.py` 是 P41 的扫描面）。"
           "★ 与第 7 轮 `G36` 同型**第 2 次复发** ⇒ 主 Agent 已把该件移入 `_probe/`。"
           "★ 该件的产出自查（17 页 canonical/og:url 全部等于 `SITE_BASE_URL + 产物相对路径`）经主 Agent 复跑成立。",
    "G45": "★ **第 8 轮新增（已处置）**：**子 Agent 的交付面与「只读参照物」冲突** —— 本轮为只读侦察克隆了"
           "姊妹站（26M）到 `_probe/_ref_akg/`，而该目录在**同一时间**被另一路内容子 Agent 当作"
           "「可移植的实现参照」读取（它读了 `gate_seo_meta.py` 与 `gate_a11y.py` 并据此实现 A/S 段）。"
           "⇒ 侦察结论已落 `_LOCAL_ARCHIVE/REF-AKG-REPORT.md`（含 12 件 sha256 实测比对），"
           "克隆**已删除**（⛔ 不留第三方全树）。★ 认识：临时只读参照物要**显式告知委派方它何时会被删除**。",
    "G46": "★ **第 8 轮新增（装置欠账）**：`gate_prototype.py` 的 `build_probes()` 会真跑 **4 次**"
           "`build-all` 子进程（幂等 a/b、dry-run、orphan 各一次）⇒ 一次全量门控要跑 5 遍生成链路。"
           "这是「判据依赖真实生成链路」的**必要代价**（⛔ 不能用 mock 替代，否则 P16/P17 恒真），"
           "但它使 push 档必须排除 P38/P41 之外的**生成链路开销**无从削减。★ 如实登记为成本事实。",
}

NOTE = ("★ 本对象是**第 8 轮（T1：守边界建仓 → T2/T3：发布级元数据基线 + 三条判据对象收窄 + 两个新门控 "
        "+ CI → T4：建仓发布并线上验证）**的轮次对象：采用**收口期一次性落盘**"
        "（与第 7 轮同口径；见下「偏离登记」）。\n"
        "★ 本轮读数全部由**主 Agent 亲跑**（`main-agent-rerun`，逐条附原始输出，原件落 "
        "`16-checkpoint/_probe/r8_*.txt`）；★ 本轮派了 **2 个子 Agent**（1 路只读侦察姊妹站发布约定、"
        "1 路把 head 元数据接进 4 个生成器），两者的产出**均由主 Agent 复跑核验**：\n"
        "  · 侦察子 Agent 的 12 件 sha256 登记经主 Agent **逐件复算**（全部吻合，见 `REF-AKG-REPORT.md`）；\n"
        "  · 生成器子 Agent 自报「四个脚本退出码 0」→ 主 Agent 复跑**成立**；"
        "但另有**两项**其未覆盖：它把临时自查件落在 `16-checkpoint/` 顶层（`G44`，已移入 `_probe/`），"
        "且其交付面与只读参照物同时段被读取（`G45`，已登记）。\n"
        "★ **偏离登记**：契约 §4① 第 3 条要求「开工期先落盘 `rs_touched`」，本轮（与第 7 轮同）"
        "采用**收口期一次性落盘**。理由：开工时确实还不知道会触碰哪些 R-xx —— "
        "本轮开工后的第一个动作（判假探针）就新增了 R-19/R-23 的触碰面，先写只会写成一个随后必然被推翻的猜测。"
        "★ 该项已在第 7 轮登记为待裁决（要么改契约措辞、要么允许写「预计触碰集」），本轮**仍未裁决**，如实续留。\n"
        "★ **本轮的定位**：把「产物」从「只存在于本地归档目录」推到「公开可读且被 hub 收录」；"
        "它顺带把三条判据的**对象边界**收窄到它们本来要管的东西，并首次让**分档 CI** 与**两个新门控族**落地。")


def build_round():
    return {
        "round": 8,
        "started_at": STARTED,
        "ended_at": ENDED,
        "rs_touched": RS_TOUCHED,
        "claims": CLAIMS,
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
    if any(r["round"] == 8 for r in doc["rounds"]):
        raise SystemExit("[FAIL] 已存在 round 8 对象 ⇒ 本脚本只负责**首次**追加（⛔ 不覆盖）")

    rnd = build_round()
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
        print("  回读：JSON 合法 · 轮次 %s · round 8 claims %d 条 · artifacts %d 项"
              % ([r["round"] for r in back["rounds"]], len(back["rounds"][-1]["claims"]),
                 len(back["rounds"][-1]["artifacts"])))
        print("  == 结论：已落盘 ==")
    else:
        print("  == 结论：dry-run，⛔ 未写盘 ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
