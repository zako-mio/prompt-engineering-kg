# 数据与目录契约 · prompt-engineering-kg（v1 草案）

> 本文件是**生成前的契约**：所有生成器、所有页面、所有委派子 Agent 都以本文件为准。
> ⛔ 本文件只定义**形态**（字段、枚举、路径、阈值）；**内容**在 `10-dag-data/*.json` 里。
> ⛔ 契约不写进产物页面；公开产物中内部编号（`§`、「门控级」等）命中须为 **0**。

---

## 1. 目录契约（★ 断链的头号根因，先约定再生成）

| 目录 | 相对路径基准 | 可引用什么 |
|---|---|---|
| `11-node-pages/` | 同目录 | `../12-groups/…` `../13-interactive/…` `../14-views/…` `../index.html`；**⛔ 0 个外链资源、0 个 `<script>`、0 个 `@import`** |
| `12-groups/` | 同目录 | 同上；**⛔ 自包含同上** |
| `14-views/` | 同目录 | 同上；**⛔ 自包含同上** |
| `13-interactive/` | 同目录 | **允许** `vendor/cytoscape.min.js`、`vendor/cytoscape-dagre.min.js`（同目录外链）；**⛔ 不得引用 CDN** |
| 任意页 | **站点根相对** | **允许**引用 `assets/` 下的**图片资产**（第二类白名单，见下）；⛔ 不得引用站外 |
| `15-md/` | 同目录 | 纯 Markdown，不引用 HTML |
| 根 `index.html` | 同目录 | `11-node-pages/…` `12-groups/…` `13-interactive/…` `14-views/…`；**⛔ 自包含同上** |

**★ 第二类白名单：站点级只读图片资产（2026-10-15 按 ADR-002 新增）**

| 项 | 内容 |
|---|---|
| 目录 | `assets/backdrop/`（背景摄影素材）· `assets/favicon.svg` |
| 允许的引用面 | ① CSS `background-image: url(...)`；② `<img>`；③ `<source>` |
| 扩展名闭集 | `{.webp, .jpg, .jpeg, .png, .avif, .svg}` |
| 路径形态 | **站点根相对**（`assets/…`），⛔ 不得指向站外 |
| ⛔ 禁止 | 白名单前缀下出现 `script` / `link[rel=stylesheet]` / `@import` / 任何非图片资源 |
| 门控断言 | 命中 `assets/` 前缀的引用**全部**为图片扩展名；受检页 `script` 数 = 0、`link[rel=stylesheet]` 数 = 0、站外 `url()` 数 = 0、**未命中任一白名单前缀的引用数 = 0** |

★ **两类白名单分开声明、互不包含**：第一类是**脚本**（交互层第三方库，同目录）；第二类是**图片**（站点级资产）。⛔ 不得用一类去涵盖另一类。

**规则**：每个页面在其 `<head>` 之后立即写一行注释声明本页的相对路径基准，例如
`<!-- base: ../ (相对本站根) -->`。门控按此逐页复核。

**禁止**：⛔ 任何 CDN / 外域链接作为**资源**（`<link>` / `<script src>` / `@import` / `url(http…)`）。
对外**超链接**（`<a href="https://…">`）不受此限——那是引用，不是资源。

---

## 2. 主题与令牌契约（★ 2026-10-15 按 ADR-002 整体重写）

**角色词表真相源**：`fe-starter-kit/tokens/contract.json`（`contract_version` 1.1.1，快照 `10-dag-data/_contract.snapshot.json`，sha256 `f9962171…`）。
**令牌值真相源**：`10-dag-data/site-palette.json`（**56 令牌**：契约 11 角色 + 站点追加 45）。
**消费形态**：由 `16-checkpoint/gen-tokens.py`（v2）读取上述两件派生 `16-checkpoint/tokens.generated.css`；⛔ 不得手改派生结果。

★ **对齐口径（须写清，否则会被误读为「色值也来自契约」）**：与契约对齐的是**角色词表**（11 个 role id），**⛔ 不是色值**。依据：① 契约**没有任何单一调色板含全 11 角色**（content 7 / app 9 / app-oklch 6）；② hub 的 `globals.css` 自述同为「角色令牌集（11 角色）与契约的 roles 对齐」，而其色值与契约三族均不同。⇒ 本站与 hub 同构：**词表取自契约、色值站点自有**。

**契约 11 角色 → 本站令牌名（覆盖 11/11，门控硬判）**

| 契约角色 | 本站令牌名 | 用途档 |
|---|---|---|
| `surface.page` | `--surface-page` | non-text（作参考底） |
| `surface.raised` | `--surface-raised` | non-text（作参考底） |
| `surface.subtle` | `--surface-subtle` | non-text（作参考底） |
| `surface.stripe` | `--surface-stripe` | non-text（装饰性条带，不检） |
| `text.primary` | `--text-primary` | body（硬 4.5） |
| `text.secondary` | `--text-secondary` | body（硬 4.5） |
| `text.tertiary` | `--text-tertiary` | **non-body（硬 3.0）**，⛔ 仅限非正文 |
| `link` | `--link` | body（硬 4.5） |
| `brand.primary` | `--brand-primary` | non-text（作 `--on-brand` 的底） |
| `border.line` | `--border-line` | **non-text（硬 3.0）**，WCAG 2.2 SC 1.4.11 |
| `border.subtle` | `--border-subtle` | non-text（装饰性弱分隔，不检） |

**站点追加令牌（45 个）**：表面阶梯第 5 级 `--surface-sunken` · 描边追加 `--border-card`（装饰性柔边，**report-only**）与 `--edge-highlight` · 品牌族衍生 5（`--brand-bright/deep/soft/tint`、`--on-brand`）· 语义色 4（`--success/warning/danger`、`--focus-ring`）· 阴影 2（`--shadow-1/2`）· 动效 7 · 字体 2 · 字号 6 · 间距 7 · 形状与栅格 6 · 背景 scrim 3。

**⛔ 明令不得引入（hub 自身零 `var()` 消费的 5 个）**：`--surface-inset` · `--shadow-3` · `--shadow-card` · `--shadow-card-hover` · `--glass-brd`。
理由：它们在 hub 自身零消费，与 hub 自己的铁律「⛔ 不留无人消费的令牌」相抵 ⇒ 属 hub 未修的既有缺陷，⛔ 不是范例。`gen-tokens.py` 内置守门：引入即 FAIL。

**用途档与阈值（★ 采 hub 的收紧值，⛔ 不采契约的 report-only）**

| 档 | 阈值 | 契约口径 | 本站口径 | 理由 |
|---|---|---|---|---|
| `body` | 4.5:1 | hard | **hard** | 一致 |
| `non-body` | 3.0:1 | report-only | **hard 3.0** | 契约把它定为 report-only 的处置是「限定用途」；hub 实测收紧为机检硬 3.0 ⇒ 对齐 hub 即采收紧值 |
| `non-text` | 3.0:1 | report-only | **hard 3.0** | 同上（WCAG 2.2 SC 1.4.11） |
| 装饰性柔边（`border.subtle` / `border.card`） | — | — | **report-only** | 它们按定义不在 3:1 判据面内（3:1 判的是「必须被看见才能用」的**控件边界**）；实测 `border.card` 仅 1.34:1 / 1.47:1 |

**主题契约（★ 结构性变更，撤掉 `light-dark()`）**
- **三块结构**：`:root`（浅色值在此）· `@media (prefers-color-scheme: dark) { :root:not([data-theme='light']) }`（跟随系统）· `:root[data-theme='dark']`（强制深色）。
- ⛔ **无 `:root[data-theme='light']` 块** —— 强制浅色是「**不覆盖 ＋ 守卫**」实现的。
- **pre-paint 内联脚本**在 `<head>`、先于首帧；读 `localStorage['ui-theme']`，`system` 档 `removeAttribute`。⛔ 不得放 body 末尾。
- **切换只改属性，⛔ 不接管 `color-scheme`**（避免双真相源）。
- ⛔ 不得用 `light-dark()`。★ 理由须写准：hub 的「被 CSS 管线降级」结论出自**其构建管线**，本站零构建无管线；本站的独立证据是 `getComputedStyle` 读带 `light-dark()` 的自定义属性得到**未求值 token 流**。⇒ 换机制的理由是「与生态一致 ＋ 消除语义陷阱 ＋ 不依赖实现差异」，⛔ **不是「在本站已证实失效」**。
- **门控断言**：三块齐备 ＋ 令牌声明块全站 `sha256` 唯一 ＋ ⛔ 无第二处令牌声明。

**对比度契约**
- 按 `site-palette.json` 的 `contrast_triples`（18 个三元组 × 2 主题）**逐对硬判**；门控须带**空集守卫**（三元组为 0 即 FAIL）与**负向夹具**（坏三元组必须被抓、令牌缺失必须判假、`report_only` 不得进 FAIL）。
- **★ 色相不承载身份**（硬规则 5）：⛔ 组配色令牌数 = 0；组身份由「中性色序号标记（与 `dag.json` 的 group id 同源）＋ 文字标题 ＋ 组页内位置顺序」三项共同承载。

---

## 3. `10-dag-data/dag.json`（唯一真相源）

```jsonc
{
  "meta": {
    "mission": "新一代提示词工程知识全景图与教程",
    "as_of": "2026-10",
    "edition": "v1",
    "node_count": 0, "edge_count": 0, "group_count": 0, "layer_count": 0,
    "acyclic": true,
    "edge_semantics": ["PREREQ前置依赖", "CONTAINS包含从属", "UPGRADE概念升级", "FLOW流程承接"],
    "audience": "有工程基础、提示词工程未系统化的工程师",
    "direction_rule": "A→B 表示先学 A 再学 B（学习顺序）；层序由本方向推导，写反会使分层颠倒",
    "sources": "见 10-dag-data/sources.json"
  },
  "groups": [
    { "id": "G00", "name": "…", "en": "…", "order": 0, "intro": "…", "node_count": 0 }
  ],
  "nodes": [
    {
      "id": "PE-F-01",
      "name": "中文名（English Name）",
      "en": "English Name",
      "group": "G00",
      "layer": 0,
      "content_status": "complete | registered",
      "why": "为什么需要它 / 解决什么问题（口径与阈值见下文「判据分档原则」；⛔ 不再内联边界陈述——见下一行）",
      "boundary": "适用边界（★ 必填且非空；一句完整表述，⛔ 不得与 why/intro 的任一整句逐字重复；why/intro 中⛔ 不得残留引导串「适用边界是」）",
      "intro": "机制（口径与阈值见下文「判据分档原则」）",
      "when": ["何时该用（≥1 条）", "何时不该用（≥1 条）"],
      "lab": [ { "kind": "shell|file|prompt", "lang": "bash|python|markdown", "text": "…", "expect": "…" } ],
      "evidence": [ { "claim": "…", "source_id": "S-0001", "url": "https://…", "quote": "≤200 字原文关键句", "tier": "official|paper|vendor|community" } ],
      "terms": ["术语（Term）：一句话界定"],
      "pitfalls": ["失效模式（≥1 条）"],
      "summary": "一句话小结（须为完整句、非空洞、不与 why/intro 整句重复；长度仅作报告项）",
      "prereq": ["PE-F-00"],
      "successors": ["PE-F-02"],
      "tags": ["…"]
    }
  ],
  "edges": [
    { "source": "PE-F-01", "target": "PE-F-02", "rel": "PREREQ", "note": "为什么先学前者" }
  ],
  "layers": { "0": ["PE-F-01"], "1": ["PE-F-02"] }
}
```

**`rel` 枚举（闭集，⛔ 不得新增）**：`PREREQ` 前置依赖 · `CONTAINS` 包含从属 · `UPGRADE` 概念升级 · `FLOW` 流程承接。

**节点 id 约定**：`PE-<域码>-<两位序号>`。域码闭集：
`F` 地基 · `S` 确定性输出 · `R` 推理增强 · `C` 上下文工程 · `O` 编排 · `E` 评测与自动优化 · `A` 安全与鲁棒性 · `M` 模型差异与迁移 · `V` 多模态 · `P` 落地实践 · `N` 新一代模块。
文件名为 `11-node-pages/<小写 id>.html`，例如 `PE-R-02` → `11-node-pages/pe-r-02.html`。

**★ `content_status` 两态（⛔ 不得含糊）**：

| 态 | 含义 | 门控要求 |
|---|---|---|
| `complete` | 内容已写满（**且必有节点页**——`gen-nodes.py:151` 只对 `complete` 落页） | **8 区块全部非空**（why / intro / when / lab / evidence / terms / pitfalls / summary） |
| `registered` | 架构已在册、内容待后续波次填充 | ① `why` / `intro` / `summary` **三段必须非空且非空洞占位**（口径与阈值见下「判据分档原则」：`why` caliber ≥60、`intro` caliber ≥120、`summary` 按结构性三条）<br>② ★ **`lab` / `evidence` / `pitfalls` 必须为空**——内容已填却仍标 `registered` ⇒ **状态说谎**，判 FAIL；半填（只填其中一块）同样 FAIL |

**★ 状态↔内容一致性（门控硬判；2026-10-16 判据变更 P22）**：`complete` 节点 **≥3 个**（须覆盖三种内容形态：一条被证伪的技巧、一条机制型原理、一条落地实践）；两态合计 = 全量注册数；`registered` 的三块必须为空。
⛔ 原「`registered` 节点 **≥60 个**」数量配额已**撤销**：它无因果依据（全仓无推导），且其适用阶段（注册期）在内容填充期结束——照它改数据意味着 64 个节点**永远不可点入**，会**降低**内容质量 ⇒ 按判据分档原则换判据而非改数字。
变更登记全文见 `CRITERIA-CHANGE-P22.md`（与门控 `P22`、`10-dag-data/_selfcheck.py` 的 C23–C27 **同批同源同值**）。
⛔ 不得把 `registered` 当"内容缺失"隐藏——组页 / 学习路径 / 交互图须在页内**显式标注该节点的内容状态**（"架构在册 · 内容待填充"），并在 `PUBLISH-STATE.json` 的 `pending_nodes` 处逐条登记，⛔ 不得静默留白。

**字段长度约束（门控可判）**：

> ★ **2026-10-15 判据变更（P05）**：原写「`why` 80–120 字（`registered` 放宽为 ≥60）」——该**上限 120 无因果依据**，是本契约初稿凭直觉定的；而本契约又强制要求每个节点写出「适用边界」，却没给边界独立字段，于是边界从句被写进 `why`，**67/67 个节点全部越限**。裁决：**改契约，不改数据**。
> - **下限保留为硬判据**（防一句话打发，因果直接）：`complete` ≥80、`registered` ≥60，口径＝**汉字数 + 拉丁词数（不计标点与空白）**。
> - **上限改为报告项，⛔ 不判 FAIL**（理由：导语过长只影响版式首屏，与正确性无关，无因果依据可定硬阈值；实测值须在门控输出里逐条可见）。
> - **新增 `boundary` 字段**：**本轮（P05 变更轮）可选**，内容波次起**必填** —— ★ **已于 2026-10-16 执行**：67 个节点逐条人工改判完成，`boundary` 转**必填且非空**，`why`/`intro` 主体收回、⛔ 不再内联边界陈述、⛔ 正文不得残留引导串（否则会渲染出第二个「适用边界」块）。
>   ★ 执行纪律：切分一律走 `gen-common.split_boundary` 的**显式标记**查找（⛔ 不新写关键词正则——实测会把「…而是边界：」这类**主题词**误判为适用性限定）；`PE-R-02` 用的是变体标记「适用边界必须写清：」，属逐条人工改判的对象。执行登记见 `CRITERIA-CHANGE-P05-R5.md`。
> - 变更登记全文见 `CRITERIA-CHANGE-P05.md`。

**口径定义（唯一，全站一致）**：`汉字数 = len(re.findall(r'[\u4e00-\u9fff]', s))`；`拉丁词数 = len(re.findall(r"[A-Za-z][A-Za-z0-9\-'.]*", s))`；`caliber = 汉字数 + 拉丁词数`。⛔ 不得用 `len(s)`（字节/字符数）作判据口径。

**★ 判据分档原则（2026-10-15 定，第 2 轮起沿用，防同型缺陷重犯）**：

> 数值阈值只在**能说清"把数据改成符合它会改善内容"**时才作硬判据；否则降为**报告项**（逐条打印，⛔ 不判 FAIL）。
> 判别句：*若把数据改成符合该阈值会降低内容质量，则问题在阈值不在数据。*

| 字段 | **硬判据**（因果直接） | **报告项**（⛔ 不判 FAIL） |
|---|---|---|
| `why` | `complete` caliber ≥80；`registered` caliber ≥60（理由：防"一句话打发"）· 非空洞占位 | caliber 实测值逐条打印；★ **上限报告阈值 = 693**（2026-10-16 按**真实渲染**重导：一屏可读量实测下界，取证装置 `_probe_thresholds.py`；⛔ 不得升为硬判据） |
| `intro` | `registered` caliber ≥120（理由：机制叙述需要展开空间）· `complete` caliber ≥150 | 超过 **777** 打印（＝一屏可读量实测下界）。★ **诚实登记**：`intro` 的**下限**无法由渲染导出——渲染只能给"一屏容量"这一**上界**，下限的因果在**内容侧**；本行保留其内容侧理由，⛔ 不硬凑数字 |
| `summary` | ① 以句末标点（。！？）结尾的**完整句**；② 不含空洞占位词；③ **不与 `why` / `intro` 的任一整句逐字相同**（防"复制粘贴当小结"） | caliber 实测值逐条打印（⛔ **数值下限已撤销**）；上限 80（★ 本轮未重导） |
| `boundary` | ★ **必填且非空**（2026-10-16 起）：且**不与 `why`/`intro` 的任一整句逐字相同**、正文**不残留**引导串（三条均为硬判据） | — |
| `pitfalls` / `evidence` | `complete` 节点各 ≥1 条 | — |

**★ 2026-10-16：上限按**真实渲染**重导 + 口径统一（P05-R5 的 B-2，登记件 `CRITERIA-CHANGE-P05-R5.md` §5）**：

> 取证装置 = `16-checkpoint/_probe_thresholds.py`（**只打印、⛔ 不落产物**，走与 `_render.py` 同一条真实渲染通道）。
> 实测（1440×900，非 snap Chrome for Testing）：★ **口径按 2026-10-16 审核更正** —— `_probe_thresholds.py` 量到的是 main 的 **border-box 宽 868px**；因 `box-sizing:border-box` 且 `.layout>main{padding:0 var(--space-5)}`（2×32px）⇒ **内容列内宽 = 868 − 64 = 804px**，与 R-08 / P34 / `gen-figs.CONTENT_COL_PX` 的 804px **同一口径**（此前把 868 写成「内容列宽」是同名两口径，⛔ 不得再这样写）。行高 **28px**；逐页反解「**一屏可读量**」（caliber 口径）：
> `why` = 693 / 698 / 855（取 **min 693**）、`intro` = 777 / 813 / 835（取 **min 777**）。
> ★ **阈值推导本身不受该命名影响**：一屏可读量只用 `blockH / caliber`，⛔ 不用列宽。
> ★ 两者**只能作报告项**：上限只影响版式首屏，与正确性无因果关联（本 § 的分档原则）。
> ★ **⛔ 静态模型不得当判据**：`_probe_metrics.py` 的横表宽度是「不折行」模型，实测会与真实渲染相反（`report.md §7.2`）。
> ★ **口径统一**：数据侧自检的 `len()` 口径（旧 `C28` 的 `why≥60 / intro≥120 / summary≥30`）本轮**废除**，
> 与门控同源同值改为 `caliber`。触发事实：补写 `PE-R-02` 的机制句后，`len` 口径下 intro = 270 报越限，
> 而 `caliber` 口径下 = 204 ⇒ **同一字段两条阈值两种单位**必然漂移。

**★ `summary` 数值下限撤销的理由（判据变更 P05 的第二例，同型缺陷）**：原 `summary ≥30` 是在**旧单位（字符数）**下标定的（旧单位下实测最低正好 30、全绿）；本契约改用 `caliber` 单位后该数字**未重新标定**即沿用 ⇒ 新单位下 49 个节点跌破（最低 23）。同 `why` 上限一样，属"阈值在新单位下无因果依据"。处置：**换判据而非改数字**——`summary` 真正要保证的是"它是一句完整、独立、非复制的结论"，这与长度无关。⇒ 改为上表的结构性三条。

---

## 4. `10-dag-data/frontier.json`（「新一代模块」的载体）

```jsonc
{
  "as_of": "2026-10",
  "edition": "2026-10",
  "previous_edition": null,
  "tracking_sources": [ { "name": "arXiv cs.CL", "url": "…", "kind": "preprint|official|conference" } ],
  "items": [
    {
      "id": "PE-N-01",
      "title": "…",
      "summary": "…",
      "status": "confirmed|disputed|unverified",
      "supersedes": ["PE-R-01"],
      "evidence": [ { "source_id": "S-0001", "url": "…", "quote": "…", "tier": "…" } ],
      "offline_repro": "可选：离线复现步骤（未实测者须显式标注）"
    }
  ]
}
```

**更新流程（幂等）**：只改 `frontier.json` 的 `edition` / `as_of` / `items` ⇒ 重跑生成器 ⇒ 门控。
⛔ 不得直接改 `11-node-pages/pe-n-*.html`（会被重生成回退）。

---

## 5. `10-dag-data/sources.json`（引用台账）

```jsonc
{ "sources": [ { "id": "S-0001", "title": "…", "url": "…", "tier": "official|paper|vendor|community", "date": "YYYY-MM-DD", "note": "…" } ] }
```

**许可纪律（★ 2026-10-15 按 ADR-002 修订；原载「⛔ 图件全部自制；⛔ 不使用外部图片素材」，与引入真实摄影素材直接冲突 ⇒ **同批改正**）**：
- 公开库只承载**消化重组后的知识**与**自研脚本**；⛔ 书籍/标准/论文**正文**不入公开仓，只入引用台账（题录 + 链接 + ≤200 字关键句）。
- **数据图解（图表 / 关系图 / 示意图）一律自制** —— 这类件承载本站的知识结构，自绘是它的正确形态。
- **背景摄影素材**：⛔ **仅允许 CC0 / CC BY 许可**，且须同时满足三件：
  ① 入**许可台账** `assets/backdrop/LICENSES.json`（文件名 / 素材名 / 作者 / 许可 / 来源 URL）；
  ② 在**页脚独占一行署名**（CC BY 类必须署名；CC0 类自愿但本站仍登记）；
  ③ 派生过程须**幂等且可复现**（纯函数、无时钟）。
  ⛔ 不得引入许可不明、需付费、或禁止改作的素材。
- ⛔ **不得自绘渐变 / 点阵 / 噪点充当「视觉」** —— 自绘在放大后没有可分辨细节，是**清晰度上限**而非调参失误（H2 硬规则 1）。背景只能用真实素材。
- ⛔ 不得留下「实现已改、规则仍相反」的死规则：本条的每次修订都须与实现**同批**。

---

## 6. `10-dag-data/glossary.json`（术语单一真相源）

```jsonc
{ "terms": [ { "term": "…", "en": "…", "definition": "…", "node_refs": ["PE-F-02"] } ] }
```

**规则**：同一术语在全站**只允许一种表述**；节点页 `terms` 区块的条目必须能在本文件中解析（门控逐条复核）。

---

## 7. `PUBLISH-STATE.json`

```jsonc
{ "as_of": "…", "edition": "v1", "round": 1, "published": false,
  "counts": { "nodes": 0, "groups": 0, "edges": 0, "layers": 0, "html": 0, "md": 0 },
  "gates": { "prototype": "…" }, "repo": null }
```

---

## 8. 门控判据清单（`16-checkpoint/gate_prototype.py`）

每条判据**必须带负向自检**（`--selftest` 时全部负例须触发，否则判据本身 FAIL）。

| 判据 | 断言 | 级别 |
|---|---|---|
| P01 | `dag.json` / `frontier.json` / `glossary.json` / `sources.json` 均为合法 JSON 且必填字段齐全 | FAIL |
| P02 | 节点 id 唯一、`group` 均在 `groups[].id` 中、`prereq`/`successors` 指向存在节点 | FAIL |
| P03 | `edges[].rel` ∈ 闭集；**无环**；拓扑层序与边方向一致（A→B ⇒ layer(A) < layer(B)） | FAIL |
| P04 | 每个 `groups[]` 至少 1 个节点；**无孤立节点**（每个节点至少 1 条入边或出边，Layer 0 除外） | FAIL |
| P05 | 字段约束逐节点复核：`why`/`intro` 数值下限（硬）＋ `summary` 结构性三条（硬）＋ 全部 caliber 实测值逐条打印（报告项） | FAIL（数值下限与结构性三条）/ REPORT（caliber 实测） |
| P06 | 每个节点 `pitfalls` ≥1、`evidence` ≥1（GD-N `unverified` 例外） | FAIL |
| P07 | `terms` 逐条能在 `glossary.json` 解析（术语统一） | FAIL |
| P08 | 全站 HTML 断链 = 0（含跨目录相对路径） | FAIL |
| P09 | 自包含：`11-node-pages` / `12-groups` / `14-views` / 根 `index.html` 的**外链资源 = 0**、`<script>` = 0、`@import` = 0 | FAIL |
| P10 | 主题：全站令牌声明块 `sha256` 唯一 | FAIL |
| P11 | 对比度：正文类 ≥4.5:1；**所有**节点底色上的标签色达标（含由亮度计算） | FAIL |
| P12 | 公开产物中内部编号（`§` 编号、「门控级/咨询级」）命中 = 0 | FAIL |
| P13 | MD 镜像覆盖：`15-md/` 覆盖全部节点与组 | FAIL |
| P14 | 页面间导航可达：每页至少有到根 index 与所属组页的链接 | FAIL |

**判据纪律**：⛔ 不得为通过而放宽阈值；⛔ 不得设置「已识别的死代码/死令牌」豁免；失败即 FAIL，⛔ 不静默降级。
