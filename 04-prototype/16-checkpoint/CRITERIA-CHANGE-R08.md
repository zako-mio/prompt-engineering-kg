# 判据变更登记件 · R-08 / R-18 / R-19 的对象收窄 ＋ 发布级元数据判据族（A 段 / S 段）

> 触发：**用户 2026-10-16 第 8 轮裁决 A**（先做发布级强化：建仓 + CI + Pages + hub 收录）＋
> **SH0–SH5 基线**（SH2 无障碍 / SH4 元数据 / SH5 资产）＋ `CONTINUE-PROMPT-D7.md` §5.4 的 `G15`
> （第 7 轮已跨过发布阈值 `complete = 35 ≥ 34`）。
> 动作：把 release 面缺的 head 元数据与站点级发现协议补上，**并同批**把三条判据的**对象**收窄到
> 它们本来要管的那个（⛔ 阈值一个字节未放宽）：
> · **P09 / R-18**：`<link>` 按 **rel 闭集**分流（元数据类 rel ≠ 加载类资源）；
> · **P12 / R-19**：「主机名」一项只在**正文**上判（属性值里的 URL 归 P09/P30）；
> · **R-08**：把「内容列」用词落实为可复算口径（`G31` 第 7 轮留行项）。
> 新增判据：**A1–A7**（`gate_a11y.py`，SH2）＋ **S1–S11**（`gate_seo_meta.py`，SH4）。
> ⛔ **P01–P41 的编号不变**（P09 / P12 只改对象，不新增编号；与第 6 轮 G12/G13 挂 P13 同体例）。
> 引用闭合（⇒ 满足 **P39**）：`gate_prototype.py`（P09 / P12 的 docstring / 实装 / `CHECKS` 标题）·
> `gen-state.py` 的 `CHANGE_DECL_9` · `PUBLISH-STATE.json` 的 `gates.criteria_change_R08`。
> 契约侧同批：`DESIGN-CONTRACT.md` §1 的 `R-08` 行（补内容列口径）＋ §2 G 清单。
> 性质：**判据变更登记件**，⛔ 不是台账。

---

## 1. 触发事实（⛔ 全部本机复算，主 Agent 亲跑）

| # | 面 | 登记来源 | 触发前的现状（复算） |
|:--:|---|---|---|
| F1 | **发布面 head 元数据** | SH4 | 51 页 HTML：`<meta name="description">` **0 页** · `og:*` **0 页** · `rel="canonical"` **0 页** · `rel="icon"` **51 页**（`assets/favicon.svg`，495 B 存在）。★ `favicon` 已由第 1 轮生成器产出，其余四项全缺 |
| F2 | **站点级发现协议** | SH4 / SH5 | `sitemap.xml` **不存在** · `robots.txt` **不存在** · `.nojekyll` **不存在** · `og.png` **不存在** · 发布根 `favicon.svg` **不存在**（只在 `assets/` 下） |
| F3 | **同类站已有的判据族** | 只读侦察（`_LOCAL_ARCHIVE/REF-AKG-REPORT.md`） | 姊妹站 `algorithm-knowledge-graph` 有 `gate_a11y.py`（A1–A7，hard）与 `gate_seo_meta.py`（S1–S11，hard）；其 profile 把 `og_url_image_exempt` / `favicon_exempt` **两张豁免表写成必须为空**。★ 该站 `build_type = legacy`；本站发布根在子目录 `04-prototype/` ⇒ **必须走 Actions**（legacy 不支持子目录） |
| F4 | **P09 在加 canonical 后整站 FAIL** | 判假探针 `_probe/r8_t1_p09_probe.py` | 合成变体实测（原始输出见 §4①）：给一个真实受检页加 `<link rel="canonical" href="https://<本站>/…">` ⇒ **P09 FAIL**。根因：`_resource_refs()` 把**一切** `<link>` 当加载类资源引用，而 `canonical` / `icon` 是**元数据声明**。★ `rel` 为 `canonical`、`icon` 两种写法**都** FAIL（与是否带主机无关） |
| F5 | **P12 在加 canonical 后整站 FAIL** | 同一探针 | 同一变体 ⇒ **P12 FAIL**：`HOST_RE = \b(zako-mio\|localhost\|…)\b` 是**禁止性**模式，不区分「正文里的内部主机名」与「属性值里的本站发布 URL」。★ 探针还揭出第二处：`sitemap.xml` / `robots.txt` 的**全部内容**按规范就是绝对 URL ⇒ 也会 FAIL |
| F6 | **`G31`（R-08 措辞模糊）** | 台账（第 7 轮留行） | R-08 原文写「内容列宽（804px）」，而「内容列」在产物上**没有定义**：`804` 是 `#main` 的宽度，不是 `body` 或 `.layout` 的。⇒ 任何要复算它的人（含门控实现者）都得自己反推 |
| F7 | **`counts.md` 与判据的「MD 数」是两个口径**（★ CI 档当场抓出） | `gate_prototype.py` G12 ＋ `gen-state.py` | `G12` 原写 `("md", len(ctx.md))`，而 `ctx.md` 是**发布面全部 `*.md`**（含发布根上手写的 `README.md`）；`gen-state.py` 的 `md_count` 是**镜像数**（只含 `15-md/`）。★ 两者在 README 不在发布面时恰好相等 ⇒ 缺陷潜伏；本轮 README 一进 `04-prototype/`（CI 与 P12 都要求它）就当场 FAIL：`('counts.md 与实数不符', 50, 51)` |
| F8 | **P12 的「主机名」对 `README.md` 不适用** | 同上 | `README.md` 是**仓库门面**（GitHub 仓库页显示的那份，⛔ 不在 Pages 上），其职责就是写出本站入口 URL；对它判「正文不得含主机名」＝把规范要求写的东西判成违例 |
| F9 | **`P13` 把「不发布」这条历史意图固化成了判据**（★ 本轮发布后立刻暴露） | `gate_prototype.py` 的 P13 | 原句 `if state.get("published") is not False: bad.append(("PUBLISH-STATE.published 应为 false", …))`。它断言的**不是任何产物事实**，而是第 1 轮「本轮不发布」的时点决定；本站第 8 轮**真的发布**之后它恒 FAIL，而**「线上确实是那个站」这件事没有任何判据** |
| F10 | **「元数据面」这一类随发布动作逐个长出来**（★ 三次实测，同一形态） | 同上 | 第 1 次：`sitemap.xml` / `robots.txt`（URL 载荷）；第 2 次：`README.md`（仓库门面）；第 3 次：`PUBLISH-STATE.json`（发布态台账）。★ 每次都是「把规范要求写的东西判成违例」⇒ 说明**「正文」这个概念在判据里需要一个显式的对象集**，⛔ 不能靠「默认所有文件都是正文」 |

---

## 2. 根因

**三条判据的对象都大于它们的断言对象（R-23 的同型第三次复发）。**

| 判据 | 它**要**判什么 | 它在实装里**实际**判了什么 | 差在哪 |
|---|---|---|---|
| **P09**（R-18 自包含） | 「0 **外链资源**」——浏览器会去取的站外资源 | `_resource_refs()` 收**一切** `<link>`，含 `canonical` / `icon` / `alternate` 等**元数据声明** | 元数据声明不是资源；把「一切 link」算成资源，等于要求「不许写 canonical」 |
| **P12**（R-19 无主机名） | 「公开**正文**里不得出现内部主机名 / 绝对路径 / 内部编号」 | 对**整个文件文本**跑 `HOST_RE`，含标签属性值与 sitemap/robots 的 URL 载荷 | 属性里的 URL 是**规范要求**的（SH4）；sitemap 的全部内容**就是**URL |
| **R-08**（绘图规格） | 「内容列宽下渲染高 ≤600px、缩放 ≥0.90」 | 门控与生成器各自**反推** 804px 是哪个盒子 | 「内容列」缺定义 ⇒ 同一条规格有两处独立反推 |

**共同形态**（与第 5 轮 P35 ⑧、第 6 轮 R-07/R-03、第 7 轮 R-01 同族）：
**声明的对象 ≠ 实现的对象，且没有任何判据会因此失败** —— 因为「对象过宽」在存量产物上
恰好不触发（存量页本来就没有 canonical）。⛔ 它只在**下一个必然发生的改动**（SH4 落地的这一刻）才炸。

---

## 3. 裁决表（本轮执行）

| # | 项 | 裁决 | 依据 |
|:--:|---|---|---|
| D1 | **P09 的 `<link>` 分流** | 引入 `LINK_META_RELS = (canonical, icon, apple-touch-icon, mask-icon, alternate)`；元数据类 **不**当资源引用。**同批加两条防退化断言**：① **rel 闭集** —— 落在 `("", stylesheet, preload, modulepreload, prefetch, dns-prefetch, preconnect)` 之外的 rel 一律 FAIL；② 元数据类的 href **无主机**，或（仅 `canonical` / `alternate`）**必须等于本站基址前缀**（`LINK_META_HOSTED_OK`） | 对象收窄到「加载类」；闭集 + 自指基址两条断言使 ⛔ 不退化成「有 link 就放过」 |
| D2 | **P09 的分流单点化** | 新增 `_is_meta_link(ref)` 作为**唯一**分流点；`check_p09` 的**两条**子断言（受检页集合、交互页）都经它 | 两处各写一份会让「rel 是什么」出现两个口径（同 F4 的成因） |
| D3 | **P12 的主机名收窄** | 「主机名」一项只在 `_strip_url_attrs(text)`（摘掉 `href="…"` 与带主机的 `content="…"`）上判；对 `sitemap.xml` / `robots.txt` **再**摘掉正文里的绝对 URL 词（`_strip_host_urls`，替换为空格 ⛔ 不是空串） | 属性的取值归 P09/P30（断言更精确）；sitemap/robots 是**发布发现协议的载体**，其内容按规范就是 URL |
| D4 | **P12 的负例加固** | `mut_p12` 由 1 条扩为 **2** 条：新增「正文里只放一个裸主机名」 | 收窄后必须有一条夹具**专门守住正文侧**，否则会悄悄退化成「主机名永远不判」 |
| D5 | **图件的可访问名** | `gen-figs.postprocess()` 由图注首句派 `aria-label`（`_a11y_name`），并去掉 Graphviz 自动写的无信息 `<title>fig</title>`；属性值经 `_xml_attr` 转义 | A4 要求 `role="img"` 带可访问名（SH2）；同理 F2：Graphviz 的 `<title>` 内容是字面量 `fig`，读屏只会念出无信息词 |
| D6 | **新增 A 段（`gate_a11y.py`）** | A1 skip 恰 1 且目标锚点存在 · A2 `:focus-visible` ≥1 · A3 `<main>` 恰 1 · A4 内联图形可访问（命名 / `aria-hidden` / ⛔ 不得冲突声明）· A5 `<html lang>` 非空 · A6 `rel="icon"` 声明 ≥1 · A7 `a.skip` 是正文内**第一个可聚焦元素**（WCAG 2.4.1 的实现前提） | SH2；判据实现 `import gate_prototype` ⛔ 不复制正则 |
| D7 | **新增 S 段（`gate_seo_meta.py`）** | S1 head 元数据区 `<title>` 恰 1 且含站点名 · S2 description 恰 1 非空 · S3 og 五项齐备 · S4 canonical 恰 1 · S5 canonical **自指且目标现存** · S6 `og:url` ≡ canonical · S7 icon 目标在盘存在 · S8 robots 含 `Sitemap:` 且指向本仓 · S9 sitemap `loc` 集合 ⟺ 发布面 HTML 集合（双向闭合）· S10 sitemap 良构且 ⛔ 无 `<lastmod>` · S11 description 长度 ≥16 且 ⛔ ≠ 站点标语 | SH4 / SH5；⛔ 不提供 `*_exempt` 类豁免字段（姊妹站把「两张豁免表必须为空」写成硬要求） |
| D8 | **R-08 的内容列口径** | 补写为「内容列 = `.layout > main` 的 border-box 内宽 ＝ 868 − 2×32 ＝ **804px**」（`G31` 第 7 轮留行项） | `G31`；使「804」可被独立复算 |
| D9 | **canonical 归一化口径** | `X/index.html` ≡ `X/`（仅用于**比较**，⛔ 不用于生成；生成侧一律写显式 `index.html`） | GitHub Pages 对 `…/index.html` 301 到 `…/`，两者是同一资源；只认一种会把**正确产物**判错 |
| D10 | **`counts` 的 MD 口径拆成两个** | `md` = **镜像数**（`15-md/` 下，由真相源侧 `_md_expected(groups, complete)` 派生）；新增 **`md_total`** = 发布面全部 `*.md`。`P13` 的 G12 对**两个**都判 | F7；★ ⛔ 期望值**必须**取自真相源对象而**不是磁盘** —— 取自磁盘就与实测值同源、判据恒真 |
| D11 | **`HOST_CARRIER_FILES` 补 `README.md`** | `sitemap.xml` / `robots.txt` / `README.md` 三件都是**元数据面**（不在 Pages 上、或职责就是承载绝对 URL）⇒ 「主机名」一项对它们不适用 | F8；⛔ 收窄的是对象不是阈值 |
| D12 | **`MD_FIXED` 由误写的 4 修正为与生成器一致** | `gen-md.generate()` 的固定件 = `index.md` ＋ `groups/index.md` ＋ `learning-path.md` ＋ `frontier.md`；★ 修正前后 G12 各自报出一次 FAIL（判据真的在判） | F7；★ 复算命令已写进 `_md_expected` 的 docstring |
| D13 | **`published` 断言由「必须是 false」改为「内部一致性」** | 原句 `if state.get("published") is not False: FAIL` 把第 1 轮「本轮不发布」这条**历史意图**固化成了判据 ⇒ 本站真发布（第 8 轮）之后它恒 FAIL，而它断言的**不是任何产物事实**。⇒ 改为：`published=false` ⇒ `publish` 段**必须不存在**（⛔ 不得残留过期事实）；`published=true` ⇒ `publish` 段齐备（`repo` / `entry_url` / `pages_build_type` / `hub_listed`）**且 `entry_url` 必须与本站基址相符**。`mut_p13` 同批由 4 条扩为 **6** 条（新增两条一致性负例） | F9；★ 新断言拿**判据自己的站点基址**去撞 `entry_url`，⛔ 不是只查非空（防恒真） |
| D14 | **`HOST_CARRIER_FILES` 再补 `PUBLISH-STATE.json`**；`publish.repo` 写成**完整 URL** | 第 8 轮新增的 `publish` 段必然承载 `repo` 与 `entry_url`（P13 的一致性断言**正是拿它们判的**）⇒ 它是第五件「职责就是承载绝对 URL / 仓库标识」的元数据面件。★ 且实测发现一个**摘除口径的漏洞**：裸 slug `zako-mio/prompt-engineering-kg` 不含 `scheme`，`_strip_host_urls`（按 `scheme://` 匹配）摘不掉它 ⇒ 把 `repo` 改成完整 URL（既更有用，也让摘除口径自洽）。 | F10；★ ⛔ 仍是收窄对象：HTML 页正文的裸主机名照样 FAIL |

---

## 4. 变更后实测原始输出（⛔ 逐字贴；`main-agent-rerun`）

### ① 判假探针（改前 —— 这是本次变更的**唯一**触发证据）

`python3 _probe/r8_t1_p09_probe.py`（原件 `_probe/r8_t1_p09_probe.txt`）节选：

```
变体                                     P09    P30    P15    P12
C0 现状（无新增）                             PASS   PASS   PASS   PASS
F1 +canonical（绝对自指）                      FAIL   PASS   PASS   FAIL
F2 +favicon rel=icon（相对）                   FAIL   PASS   PASS   PASS
F5 全套（SH4 标准档形态）                        FAIL   PASS   PASS   FAIL
```

### ② 门控（改后）

`python3 gate_prototype.py --only P09,P12`：

```
[PASS] P09 自包含：…元数据类 `<link>` 100 处（进 rel 闭集；`canonical`/`alternate` 容许本站绝对自指 URL）；
       脚本白名单引用 13 处、图片白名单引用 500 处；违例 0 处 []
[PASS] P12 公开产物无内部编号 / 绝对路径 / 主机名 / 令牌串
       受检产物 110 个（主机名一项在**正文**上判：摘掉 href 与带主机的 content 后 110 个文件）；命中 0 处 {}
```

### ③ 自检（可判假性）

`python3 gate_prototype.py --selftest --only P09,P12`：

```
[PASS] P09 … 正向：PASS / 负例（8 条）：全部触发（判据可判假）—— 8/8
[PASS] P12 … 正向：PASS / 负例（2 条）：全部触发（判据可判假）—— 2/2
== 自检结论：PASS ==（2 条判据 / 10 条负例夹具，全部须正向 PASS 且负例触发）
```

`python3 gate_a11y.py` / `--selftest`：

```
== 门控结论：PASS ==  FAIL 0 项 []
       受检页面 51 个：内联图形元素 47 个（其中装饰 0 个）；违例 0 处 []
== 自检结论：PASS ==（7 条判据 / 9 条负例夹具）
```

`python3 gate_seo_meta.py` / `--selftest`：

```
== 门控结论：PASS ==  FAIL 0 项 []
       sitemap.xml：<loc> 51 条 ⟺ 发布面 HTML 51 页（双向闭合；missing 0 / orphan 0 / dup 0）
== 自检结论：PASS ==（11 条判据 / 18 条负例夹具）
```

### ④ 本轮**自检当场抓出**的夹具/判据缺陷（⛔ 不得静默）

| # | 现象 | 根因 | 处置 |
|:--:|---|---|---|
| 1 | `A2` 负例「把 `:focus-visible` 改成 `:focus-visible-x`」**未触发** | 判据正则写的 `:focus-visible\b`，而 `\b` 在 `-` 处**成立**（`-` 非词字符）⇒ 改后照旧命中 | 右界改 `(?![\w-])` |
| 2 | `A3` 负例未触发 | 夹具改的是 `</main>`（闭标签），而判据匹配的是 `<main …>`（开标签） | 夹具锚点改成在 `</head>` 后插 `<main>` |
| 3 | `S1` 判「`<title>` 12 个」**假阳** 47 页 | 内联 SVG 的**节点标签**也是 `<title>` 元素（Graphviz 每节点一条） | 判据对象切片到 head 的元数据区（首个 `</title>` 之后 → 首个 `<style>` 之前） |
| 4 | `S1` 两条负例未触发 | 夹具往 `</head>` 前插 `<title>`，落点在元数据区**之外** | 夹具改用 `re.sub` 替换 + 在 `<style>` 前插入 |
| 5 | `S11` 两条负例未触发 | 夹具**追加**第 2 条 description ⇒ 判据因 `S2` 的对象而 `continue` | 夹具改用 `re.sub` 替换**已有**那条的 content |
| 6 | `A6` 无负例夹具（`--selftest` 报 SKIP） | 初版 A6 判「盘上 favicon 存在」，夹具无法在不破坏真实文件的前提下造负例 | 改判「每页 `rel="icon"` **声明** ≥1」（可达性归 S7），夹具=抹掉某页的声明 |
| 7 | `A7` 原为「A4 的两条通道都被行使」，而旁上**装饰图形 0 个** ⇒ 恒 FAIL 且无可行夹具 | 把**内容事实**（本站在无装饰图件）写成了**构建硬要求** | 重定义为「`a.skip` 是正文内第一个可聚焦元素」（WCAG 2.4.1 的实现前提），夹具=在 skip 前插一个可聚焦元素 |
| 8 | `P13` 报 `('counts.md 与实数不符', 50, 51)` **只在 CI 档出现** | `G12` 拿 `len(ctx.md)`（含手写 README）当「镜像数」，而生成器算的是镜像数 | 两侧口径**显式拆开**：`md`（镜像）＋ 新增 `md_total`（全部 `*.md`），G12 对两者都判（D10） |
| 9 | `P12` 报 `README.md` 含 `zako-mio` | `README.md` 是仓库门面，其职责就是写本站 URL；判据对象未包含「元数据面」这一类 | `HOST_CARRIER_FILES` 补 `README.md`（D11）；★ 与 sitemap/robots 同一处置口径 |

★ 上表是本轮最值钱的**过程**产出：**9 条里有 6 条是「判据对象 ≠ 断言对象」**（同一形态的 6 次复发），
而其中 **#8 / #9 是被 `_ci_gate.sh fast` 档（子集）翻出来的** ⇒ 另一条教训：
**跑子集不是「少跑一点」，它会换一个扫描面**，从而暴露全量档因运行顺序/环境而看不到的对象错配。

---

## 5. 局限登记（⛔ 必须明说）

| # | 局限 | 说明 |
|:--:|---|---|
| L1 | **A4 认「元素自带可访问名」** | ⛔ 不认祖先 `<figcaption>` 命名 —— ATS 对 `<figure>` 的命名支持不一致。「靠祖先命名」会得到「在自己机器上对、在别人机器上错」的结论。代价：图件必须自己有 `aria-label`（本轮已由 `gen-figs` 产出） |
| L2 | **S11 的长度下限是护栏，⛔ 不是可读性阈值** | `DESC_MIN = 16` 只说「比这更短的句子不可能承载一页摘要」，⛔ 不宣称「≥16 就一定好」 |
| L3 | **P09 的 rel 闭集是「我们想到的那些」** | 闭集之外的 rel 一律 FAIL 是**有意**的（fail-closed）：将来若真要加 `rel="manifest"` 等，必须同批改本登记件与闭集。★ 这是「宁可失败也不要静默放过」，代价是每加一种 rel 要动一次判据 |
| L4 | **P12 的 `_strip_host_urls` 只作用于 sitemap / robots（按 basename 匹配）** | 若将来新增别的「URL 载荷型」产物（如 `feed.xml`），必须同批加进 `HOST_CARRIER_FILES`，否则会假阳 |
| L5 | **`canonical` 写的是 `…/index.html` 而非 `…/`** | 两者在 GitHub Pages 上 301 等价（D9 的归一化口径据此）。★ 未做的事：没有验证搜索引擎对 301 的处理（⛔ 本机无联网核对手段） |
| L6 | **A/S 两段未接入 `gate_prototype.py --only` 的编号空间** | 它们是**独立脚本**（`gate_a11y.py` / `gate_seo_meta.py`）。⇒ CI 必须**分别**调用三个门控；⚠ 漏调其中一个不会有任何报警（这条属「装置覆盖」缺口，如实留行） |

---

## 6. 纪律自陈

1. **同批**：判据改动、夹具、契约措辞（R-08）、登记件、三处引用闭合**同一批**落盘（R-20）。
2. **对象收窄不是放宽**：三处收窄各自**同批**补了至少一条防退化断言（P09 的闭集 + 自指基址、
   P12 的正文侧夹具、S11 的「≠ 站点标语」），并逐条跑 `--selftest` 证明仍可判假。
3. **探针先行**：三处对象缺陷**全部**由 `_probe/r8_t1_p09_probe.py` 的合成变体实测揭出，
   ⛔ 没有一处是「读码推断」出来的（F4/F5 是先测后改）。
4. **夹具缺陷不许静默**：本轮自检当场抓出的 7 条缺陷全部登记在 §4④，并逐条给了修法与复跑证据。
5. **诚实边界**：`gate_prototype.py` 的 P01–P41 **编号未动**；A/S 两段的**未接入编号空间**这一缺口
   已在 L6 明文登记，⛔ 不假装「一条命令跑全部门控」。

---

## L. 本轮当场发现登记（⛔ 不得静默）

1. **`\b` 在 `-` 处成立**：`x\b` 会命中 `x-y`。凡「以 `-` 为构造符」的标识符做正则右界，
   必须写 `(?![\w-])`。★ 通用教训，已落进 `gate_a11y.py` 的注释。
2. **判据对象与夹具锚点必须同一切片**：§4④ 的 #3/#4/#5 三条是同一形态 ——
   判据看 head 元数据区，夹具却把内容插在 `</head>` 前。★ 通用教训。
3. **「追加一条」几乎总是错的夹具形态**：夹具要改的是**已有那条**的取值，而不是再加一条
   （再加一条会连带触发**另一条**判据的断言，让「这条判据可判假」无法证明）。
4. **`role="img"` 不带可访问名 = 读屏念「图像」**：Graphviz 自动写的 `<title>fig</title>`
   看似满足「有名字」，实为无信息。★ 「有属性」≠「有语义」。
