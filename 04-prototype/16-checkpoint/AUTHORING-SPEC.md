# 内容生产的**部件契约**（AUTHORING-SPEC）—— 子 Agent 的执行说明书

> 性质：**可执行说明书**（R-25 的部件契约）。⛔ 不是判据、⛔ 不是台账。
> 用法：派内容子 Agent 时**只给一句**「照 `04-prototype/16-checkpoint/AUTHORING-SPEC.md` 为 `<节点 id>` 产出部件文件」
> ＋ 目标节点 id ＋ 部件输出路径。★ 目的：**压缩主 Agent 的非必要上下文占用**（正文永不进主 Agent 上下文）。
> 依据（正文的每一条都有来源，⛔ 不凭印象）：`DESIGN-CONTRACT.md` §1 R-25 · `SCHEMA.md` §3 · `gate_prototype.check_p05/p06/p13/p22/p35` ·
> `10-dag-data/_selfcheck.py` 的 C28–C33/C58 · `CONTINUE-PROMPT-D5.md` §H。

---

## 0. 你是谁、你能碰什么

* 你是**执行者**：只产出**一个** JSON 部件文件，⛔ 不落任何站点产物、⛔ 不改判据/契约/生成器、⛔ 不委派。
* 你**只读**：`01-research/evidence/A*.json`（引文库）、`10-dag-data/dag.json`（节点现状）、
  `10-dag-data/glossary.json`（术语台账）、`SCHEMA.md`（契约）、本文件。
* 你**只写**：`04-prototype/16-checkpoint/<目标目录>/<NODE-ID>.json`（一个文件）。
* ⛔ **不要**把你的正文回贴给主 Agent：返回体只写 `status` / `summary`（≤200 字）/ `files_created` / `warnings` / `errors`。

## 1. 部件文件形状（★ 严格照抄，字段名一字不差）

```json
{
  "node_id": "PE-S-01",
  "spec": {
    "why": "……",
    "intro": "……",
    "boundary": "……",
    "when": ["……", "不适用于……"],
    "lab": [{"kind": "shell", "lang": "bash", "text": "……", "expect": "……"}],
    "evidence": [{"claim": "……", "source_id": "S-0014", "quote": "……"}],
    "terms": ["约束解码（Constrained Decoding）：……"],
    "pitfalls": ["……", "……", "……"],
    "summary": "……",
    "tags": ["……"]
  }
}
```

★ `node_id` **必须写在部件里**（⛔ 不靠文件名推断 —— 合并器以它为准，文件名写错但内容对是静默错配）。
★ `evidence` 里**只写** `claim` / `source_id` / `quote` 三项：`url` 与 `tier` 由 `_wave1_apply.py`
  从 `sources.json` **按 source_id 注入**（⛔ 手抄 URL 会被判为不一致而 FAIL）。

★★ **合并器到底收哪些字段（2026-10-16 波次 2 当场修正，务必读）**：
`_wave1_apply.py` 会把上表**全部区块**写进 `dag.json`。其中两类的处理不同：

| 字段 | 合并时的额外校验 |
|---|---|
| `lab` / `evidence` / `pitfalls` | ★ 逐项校验：`lab` 四字段齐全；`evidence` 回源＋台账注入＋`quote ≤200`；`pitfalls` 非空 |
| `why` / `intro` / `boundary` / `when` / `terms` / `summary` / `tags` | 只在部件**确有该字段且非空**时覆盖（⛔ 空值不覆盖）；**内容级硬约束由数据侧 `C28`–`C33` 与门控 `P05`/`P22` 裁决**，⛔ 合并器不做散文判断 |

★ **历史坑（⛔ 不得重犯）**：波次 1 时合并器**只写** `lab`/`evidence`/`pitfalls`/`content_status`，
  部件的散文被**静默丢弃**（作者写了、产物一字未用）。该缺口的形态是「契约说要 8 区块、合并器只收 3 个」
  —— 与 R-23 同族。⇒ 现在**全部区块都合并**；若你只想改某几个字段，只写那几个字段即可（其余保持盘上值）。
★ 合并器对**已 complete** 的节点默认**拒绝重放**（防把波次 N 的件打到上一波已发布的节点上）；
  需要重放修内容时，由主 Agent 显式加 `--reapply` 并留痕。⇒ 你**不需要**关心这一点（你只 dry-run）。

## 2. 逐字段硬约束（⛔ 全部是**机检**；违反即不接受）

| 字段 | 硬约束 | 判据来源 |
|---|---|---|
| `why` | caliber（**汉字数 + 拉丁词数**）**≥ 80**；⛔ 不得含空洞占位词（`待填充`/`TBD`/`TODO`/`待补`/`占位`/`待定`） | P05 / C28 / C30 |
| `intro` | caliber **≥ 150** | P05 / C28 |
| `boundary` | **必填、非空**；⛔ 不得与 `why`/`intro` 中任一**整句逐字相同**；⛔ `why`/`intro` 里**不得**残留引导串 `适用边界是` / `适用边界必须写清` | P05 / C32 |
| `when` | **≥1 条**（建议 2–4）；以 `不适用于` 开头的条目 = 「不该用」，其余 = 「该用」；建议每条用**全角冒号**切成「总结：细节」两段 | P05 / P35 ⑥ |
| `lab` | **≥1 条**（建议 1–2）；每条**四字段齐全且非空**：`kind` / `lang` / `text` / `expect`。★ **闭集**（`SCHEMA.md` 第 124 行的示例值即契约）：`kind ∈ {shell, file, prompt}`、`lang ∈ {bash, python, markdown}` —— ⛔ 不要自造 `kind`（如「命令行」），盘上既有 complete 节点只用这三种组合 | `_wave1_apply` 第 3 项 + `SCHEMA.md` |
| `evidence` | **≥1 条**（建议 2–3）；每条含 `claim` / `source_id` / `quote`；`quote` **≤200 字**；★ **逐字回源**（见 §3） | P06 / C31 / **C58** |
| `terms` | **≥1 条**（建议 2–3）；形状 `术语头：界定`；★ `术语头`（**全角冒号前**）必须**逐字等于** `glossary.json` 里某条的 `term` 字段（含全角括号与英文） | C33 |
| `pitfalls` | **≥1 条**（建议 3–4）；建议每条用全角冒号切成「症状：后果」 | P06 |
| `summary` | 结构性三条：① **完整句**；② 非空洞；③ ⛔ **不得与 `why`/`intro` 整句逐字相同** | P05 |
| `tags` | 建议 ≤3 个短标签 | 形态约定 |
| 8 区块 | `why` / `intro` / `when` / `lab` / `evidence` / `terms` / `pitfalls` / `summary` **全非空** | C29 / P22 |

★ **caliber 怎么算**：`len(汉字) + len(拉丁词)`；汉字 = `[\u4e00-\u9fff]` 的字符数，
拉丁词 = `[A-Za-z][A-Za-z0-9\-'.]*` 的匹配数。**标点与空白都不计**。
⇒ 自查：`python3 - <<'PY'` 里用同一对正则算一遍（⛔ 不要用 `len(s)`）。

## 3. ★ 引文怎么找、怎么用（**本件最重要的一节**）

**你⛔ 不得自己写一句「看起来像原文」的话。** 每一步都照做：

1. **选料**：用选料器按你的知识点关键词列出候选（一次给多个关键词，OR 关系）：
   ```bash
   cd 04-prototype/16-checkpoint
   python3 _wave_pick_quotes.py "结构化输出" json_schema strict
   ```
   它会一并打印 **S-id**（由 URL 映射）、`tier`、`date`、来源名与**引文原文**。
   ⛔ **`S-id = ——` 的行不可用**（该 URL 不在 `sources.json` 台账内 ⇒ 无 `source_id` 可注入）。
2. **逐字复制**：从输出里复制 `quote` 的**原文片段**。★ 允许用 `...` 或 `…` **省略中间**，但**每个片段**
   必须与库里的原文**逐字相同**（大小写、空格、标点都不许动）。⇒ 这一条会被 `_wave1_apply.py` 与数据侧
   `C58` **逐片段**校验；改一个词就 FAIL。
3. **`claim`**：用**你自己的话**写这条引文支持什么（≤ 一句，可判定）。
4. **同一条引文可被多个节点引用**，但⛔ 不得把同一条引文在**同一个节点的 2 条 evidence**里重复使用。

★ 诚实边界：本流程挡的是「凭空写一句」，⛔ **挡不住**「引文库本身被改错」。若某知识点在库里
**确实找不到**可用引文 ⇒ **如实上报 `errors`**，⛔ **不得编造**、⛔ 不得用无关引文凑数。

## 4. 图件（若你的任务含出图）

* 出图**不由内容子 Agent 做**：它由**单独一路**子 Agent 改 `gen-figs.py`（单写者，⛔ 避免并发写同一文件）。
* 图件源形状：`FIGS["<fid>"] = dict(caption="…", dot="""digraph fig { … }""")`；节点页与图必须**成对**新增
  （`gen-figs.FIGS` 一条 + `gen-nodes.NODE_FIG` 一条）。
* 硬约束：① 色值只用 `HEX2VAR` 里的 16 个（⛔ 越界 `SystemExit`）；② `rankdir` 用 **LR 或 TB 都可**，
  但**宽高比必须满足两条界**（内容列 804px 下：渲染高 ≤ 600px、缩放比 ≥ 0.90 ⇒ `viewBox 宽 ≤ 893`）；
  ③ 字形只用 fontconfig 覆盖的（CJK / ASCII / `·` / `…` / `→` / `—` 安全；⛔ 别用 `₁₂` 这类下标）；
  ④ 图内**无裸 hex / 无固定 width·height / 无 `<?xml`·DOCTYPE·clip-path / 无外链**（P36）。
* 验收：`python3 gen-figs.py --write && python3 gen-figs.py --check && python3 _selfcheck_figs_spec.py` 全 PASS。

## 5. 交件前的**自查命令**（★ 必跑，把输出贴进你的返回体 `warnings`）

```bash
cd 04-prototype/16-checkpoint
python3 _wave1_apply.py --parts-dir <你的部件目录>            # dry-run：回源 / 注入 / 长度 / 结构 四项
python3 _wave_pick_quotes.py <你的关键词> >/dev/null          # 引文可选性的粗核对
sha256sum <你的部件目录>/<NID>.json _wave3_parts/<NID>.json    # ★ 两处必须逐字节相同（禁忌 #10）
```
* dry-run 的每一行 `[NODE] lab N 条 / evidence N 条 / pitfalls N 条` 与 `片段 k/k 回源` 就是你的成绩单；
  ⛔ **全绿才算交件**；红了就改，⛔ 不要交「差一点」的件。
* ★ **顺手也要扫一遍内部记号**（禁忌 #9）：`grep -c '[⛔★⚠]' <你的部件文件>` 必须是 0。
* ★ **⛔ 不要**跑 `build-all.py` / `gate_prototype.py` / `_probe_channel.py`（那是主 Agent 的活，且会改产物）。
* ★ **⛔ 不要**跑 `_wave1_apply.py --write`（**只有主 Agent 落盘**）。

## 6. 返回体（★ 严格 JSON，⛔ 不回贴正文）

```json
{"status":"success|partial|failed","summary":"≤200 字：写了哪个节点、各字段条数与 caliber、哪些引文用了哪条 S-id、dry-run 是否全绿",
 "data":{"node_id":"PE-S-01","calibers":{"why":0,"intro":0},"evidence":[{"source_id":"S-0014"}],"dry_run":"PASS|FAIL"},
 "files_created":["/abs/path/to/parts/PE-S-01.json"],"files_modified":[],"decisions":[],"warnings":[],"errors":[]}
```
* `status=partial`：某字段拿不到合格材料（如**库里无可用引文**）⇒ 在 `errors` 里写清**缺什么**，
  ⛔ **不要**用低质量材料填充；主 Agent 会把该节点**不发布**并登记（与 `PE-C-03`/`PE-C-06` 同一处置口径）。
* `status=failed`：读不到输入 / 环境坏了 ⇒ 写清现象，⛔ 不重试超过 2 次。

## 7. ⛔ 禁忌清单（违反即整件作废）

| # | ⛔ 禁止 | 为什么 |
|:--:|---|---|
| 1 | 编造或改写引文（哪怕只改一个词） | `_wave1_apply.py` 与 `C58` 逐片段比对，必 FAIL；且这是「不可检 → 可拦」的唯一价值 |
| 2 | 手抄 `url` / `tier` | 一律由台账**注入**；手抄会与 `sources.json` 不一致 ⇒ P06 FAIL |
| 3 | 用 `len(s)` 估 caliber | 口径是「汉字数 + 拉丁词数」，标点空白不计 |
| 4 | 把 `boundary` 写成 `why`/`intro` 里的某句 | P05/C32 直接判 FAIL（整句重复） |
| 5 | 在 `why`/`intro` 里写「适用边界是…」 | 渲染器会切出**第二个**边界块 ⇒ C32 FAIL |
| 6 | 自造术语头 | `terms` 的头必须逐字来自 `glossary.json`；库里没有的术语**不要写**（⛔ 也不要顺手加术语） |
| 7 | 落盘 / 改判据 / 改契约 / 改生成器 | R-25：子 Agent 只产出部件；落盘与复跑是主 Agent 的事 |
| 8 | 把正文回贴进返回体 | 会挤占主 Agent 上下文 —— 这正是本契约要消除的成本 |
| **9** | ★ **公开文案里写内部标注记号**（`⛔` / `★` / `⚠`） | 2026-10-16 第 7 轮**当场抓到 9 处（5 个部件）**：门控 **P33** 扫全站可见文案，命中即 FAIL。想强调就换中文表述（「注意」「必须」）。★ 注意 `lab[].expect` / `lab[].text` **也是公开文案**，不是给你的备注 |
| **10** | ★ **跑完 dry-run 又改部件文件、却不重跑** | 2026-10-16 第 7 轮**至少 3 次**（`PE-E-08` / `PE-A-03` / 图件侧各一例）：`PE-E-08` 自报 quote 长 136/162/175，盘上实为 **227/241/132** —— **三条全不吻合** ⇒ 主 Agent 落盘时被合并器拦下、**整批中止**（`_wave1_apply.py` 是 fail-closed 的）。⇒ **先定稿、再 dry-run**；dry-run 之后一个字符都别改；交件时报出 `_wave3_parts/<NID>` 与 solo 副本的 **sha256 必须相同** |
| **11** | ★ **在 `16-checkpoint/` 顶层新建文件** | 顶层 `*.py` 是门控 **P41** 的**显式扫描面**（基线上限 34 个）；2026-10-16 第 7 轮有子 Agent 在此留下 7 个临时脚本，把扫描面抬到 44 个 ⇒ 主 Agent 必须逐个核实后清理。临时脚本一律放 `_wave3_solo/` 下，**交件前自行删除** |
| **12** | ★ **删改「别的」子 Agent 的文件** | 2026-10-16 第 7 轮实测一次：某子 Agent 的清理脚本**规则过宽**，误删了同层两个**他人**临时脚本（`_pick_quote_len.py` / `_selfcheck_pe_e_06.py`）。⇒ 清理脚本只许匹配**自己**的前缀；本波有 8 路并发，⛔ 不要写 `rm _tmp_*` 这类全局通配 |
