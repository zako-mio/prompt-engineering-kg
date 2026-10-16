# 接续件 · D4：内容波次（64 个 `registered` 节点）+ 三项契约收口

> 上游：`HANDOFF-R3.md`（七节，含 16 条验收定义）· `DESIGN-CONTRACT.md`（R-01…R-24 + §2 G1–G9 + §4 §轮次执行协议）· `report.md` §七（第 4 轮：把教训固化成机制）· `CRITERIA-CHANGE-P05.md`（`boundary` 与阈值两项原始待办）· `CRITERIA-CHANGE-P23.md`（**补登记件**，见 §8 禁忌 7）· `ARCHIVE-HANDOFF-R4.md`（第 4 轮留档增量）
> 性质：**用户已裁决 G7 走 A（补写），并已确认 G6 修掉** ⇒ 本轮**不开新战线**：把内容填进去，并把三件与内容同批的契约收口做掉。
> ★ 本件是**工作令**（粘进新会话即可开工），⛔ 不是又一份 handoff 台账。凡本件出现的数字都给了源件 + 节号；源件里查不到的，本件不写。

---

## 0. 已就绪的前置（⛔ 不要重写）

| 件 | 现态 | 用法 |
|---|---|---|
| `gate_prototype.py` | **P01–P40（40 条判据）/ 154 条负例夹具** | `python3 gate_prototype.py`（0 = 全 PASS）；`--selftest`；`--only P38,P39` |
| `DESIGN-CONTRACT.md` | **R-01…R-24** + §2 G1–G9 + **§3 审核子 Agent 模板** + **§4 §轮次执行协议**（六项） | 纪律源；§4① 开工三步骤照做 |
| `_probe_env.py` / `_probe_channel.py` / `_probe_metrics.py` | 三个探针（开工必跑 / 通道 + 溢出普查 / 阈值取证） | `_probe/` 下的 JSON 是它们的落盘 |
| 真实渲染通道 | `_render.py` / `_render.sh`（playwright + 非 snap Chrome for Testing） | `--html … --width 1440 --height 900 --out …` |
| `_geom_interactive.py` | 交互图**产物侧几何复算** | `python3 _geom_interactive.py` |
| `_selfcheck_switches.mjs` / `_selfcheck_p35_fixtures.py` | 开关行为（37/37 PASS）· P35 夹具对应 + ⑫ 阈值边界探针 | 见 §7 |
| `ROUND-LEDGER.json` | 轮次台账（`schema: pekg/round-ledger/1`），**当前只含 `round: 3`** | 每轮追加一个 round 对象（P40 逐条机检 `rounds[]`） |
| `_run.sh` | 无 bash 会话下的调用包装（`cd 16-checkpoint && exec "$@"`） | `run_gate(path="04-prototype/16-checkpoint/_run.sh", args=["python3","gate_prototype.py"])` |
| `PUBLISH-STATE.json` | `content_status = {complete: 3, registered: 64}`；`pending_nodes` **64 条** | 内容波次的进度真相源；★ 其余字段是第 1 轮快照，见 §5③ |

★ **⛔ 不要重写任何"已消"的东西**：G1–G7 已消（`report.md` §7.8），渲染通道已建立并 10/10 可复跑（`RENDER-CHANNEL.md` §七）。本轮的活是**内容 + 三项收口**。

### 文件基线（开工时可复算，防"读到过期版本"）

| 件 | 字节 | sha256(前16) |
|---|---:|---|
| `CONTINUE-PROMPT-D3.md` | 13027 | `48cc208f4b46131f` |
| `HANDOFF-R3.md` | 24367 | `1bd2c710595c1145` |
| `HANDOFF-R2.md` | 7823 | `da983f5c067e0ac4` |
| `DESIGN-CONTRACT.md` | 22352 | `ee630e71c23db84e` |
| `CRITERIA-CHANGE-P05.md` | 6836 | `b0191999c9b82498` |
| `CRITERIA-CHANGE-P23.md` | 8412 | `b50560569851761e` |
| `ARCHIVE-HANDOFF-R4.md` | 6297 | `8bc8fa14812db635` |
| `report.md` | 75794 | `719644d6e905fa93` |
| `ROUND-LEDGER.json` | 4442 | `93d5d893d658e234` |

---

## A. 任务身份与读者锚点（一句话）

**这是什么站**：`prompt-engineering-kg` 原型站——「新一代提示词工程」知识全景图的可发布静态站（19 个 HTML 页、8 件自制图、11 组 DAG、1 个交互图；零构建自包含，`04-prototype/` 即文档根）。
**给谁看**：要按 DAG 顺序学这套知识的读者（站内入口是「速览→交互图 / 深学→学习路径」双轨）。
**当前处于哪一阶段**：**内容填充期**。架构、版式、交互、判据都已定稿（`report.md` §7.8 的 G1–G7 全消、40 条判据全 PASS），**67 个节点里只有 3 个 `complete` 有节点页**，其余 **64 个 `registered` 节点按 `pending_nodes` 逐条登记但不可点入**（`PUBLISH-STATE.json` 的 `content_status` / `pending_nodes` / `pending_note`；`HANDOFF-R3.md` §四 R5）。
⇒ 本轮唯一的产出方向：**把 64 个 `registered` 节点按组波次填满 8 区块**，并守住「任何时刻都是无断链可发布状态」。

---

## B. 本轮目标（唯一主线）＝内容波次 ＋ 三件同批契约收口

### B-0 主线：64 个 `registered` 节点按组波次填满 8 区块

1. **进度真相源**：`PUBLISH-STATE.json` 的 `pending_nodes`（64 条）与 `content_status.registered = 64`（**本件起草时现读**）。
2. **8 区块**：`why` / `intro` / `when` / `lab` / `evidence` / `terms` / `pitfalls` / `summary`（`CONTINUE-PROMPT-D2.md` §2 的节点页结构；P22 判据断言 `complete ≥3` 且 8 区块全非空）。
3. **按组**：11 组（`counts.groups = 11`），每次推进**一个组**的量级，⛔ 不一次全铺。
4. **每波次必做**（`HANDOFF-R2.md` §二 T2.5 与 `HANDOFF-R3.md` §二 T1.3 的同一条要求，逐字承接）：
   > 「每波次跑门控 + 全量重生成；保持"任何时刻站点都是无断链可发布状态"」
   ⇒ **一波 = 改数据 → `build-all.py --write` → 门控 → 自检 → 幂等二次比对 → 渲染**，⛔ 不得攒到最后一起跑（`HANDOFF-R3.md` §六.6.2 第 12 条：至少推进一波，且**每波次后门控全绿**）。
5. ★ **渲染不是可选项**：本轮必然触碰页面/生成器 ⇒ 按 `DESIGN-CONTRACT.md` §4③「渲染」一行，**必须**有真实渲染产物（`_probe_channel.py` 的 PNG + 像素读数）。

### B-1 契约收口①：`boundary` 由可选转**必填** —— 67 个节点**逐条人工改判**

| 项 | 内容 |
|---|---|
| 源件 | `HANDOFF-R2.md` §二.T1 第 1 条（「`boundary` 为可选；"适用边界"靠 `why`/`intro` 内联 + 显式标记 `适用边界是` 切出 ⇒ 67 个节点**逐条人工改判**拆分」）＋ `HANDOFF-R2.md` §一 第 3 条（`boundary` 升为一等受检对象，写入 P05）＋ `CRITERIA-CHANGE-P05.md` §3 的 C3 条 |
| 数量 | **67**（`PUBLISH-STATE.json` 的 `counts.nodes = 67`；`CRITERIA-CHANGE-P05.md` §1 实测「边界从句内联于 `why` 的节点数 **67 / 67**」） |
| ★ 红线 | ⛔ **不得正则机械拆分**。实测反例（`CRITERIA-CHANGE-P05.md` §3，逐字）：**`PE-F-03` 的「…而是边界：」是主题词而非适用性限定，被正则误捕**；而 **`PE-P-02` 真正的边界句（「在能力较弱的模型或需要严格流程合规的场景下…」）反而未被捕获**。⇒ 机械拆分会**降低内容质量**（同件 §3 原话）。 |
| 完成标准 | ① 每个节点 `boundary` 非空且与 `why` 主体**不重复**（整句归一化比对，`HANDOFF-R2.md` §一 第 3 条）；② `boundary` 转必填并**写入 P05**；③ `why` 主体压回其目标带（带值见 §B-2）。 |
| 纪律 | 这是**内容工作**，不是脚本工作。判据同批（R-20）：字段转必填 ⇒ 同一次改动内改 P05，⛔ 不允许「已实现但无判据」这第三种状态。 |

### B-2 契约收口②：`why` 上限与 `intro` 下限**按真实渲染重导**（⛔ 不得再凭直觉给数）

| 项 | 内容 |
|---|---|
| 源件 | `HANDOFF-R2.md` §五.T6 第 2 条（「旧的 120/150 数值是在**旧版式**下推的 ⇒ 必须在**新版式**下重新推导」）＋ `HANDOFF-R3.md` §二.T1 第 2 条（「★ 本轮已有真实渲染通道（`_render.py` / `_probe_channel.py`）⇒ **可以真渲染取样了**：在一屏可读量（视口 900px）下取『首屏能读完多少 caliber』的实测值，据此反解上限」） |
| 现态 | `why` 上限 120 **已撤销**、降为报告项（`CRITERIA-CHANGE-P05.md` §3 的 C2、§6 的字段分档表）；`intro` 保留硬下限 **120（`registered`）**、上限 >250 打印；`summary` 无硬数值下限、改三条结构性硬判据（同件 §5） |
| 通道 | `_probe_metrics.py`（文字度量 / 长文游程 / 横表宽度 / 窄视口 zoom）+ `_render.py`（真实渲染取样）。★ 现成读数：汉字 advance **1.0000em**、最长无标点游程 **151**（p90 130 / 中位 78）（`report.md` §7.2） |
| ★ 分档原则（沿用，⛔ 不得绕过） | `CRITERIA-CHANGE-P05.md` §6 判别句：*若把数据改成符合该阈值会**降低**内容质量，则问题在阈值不在数据*。上限**只影响版式首屏** ⇒ 硬判据只留给「改成符合它会改善内容」的下限 |
| 变更纪律 | 先取证（真渲染读数）→ 再落 `CRITERIA-CHANGE-*.md`（触发事实 / 根因 / 裁决表 / **变更后实测原始输出** / 局限登记 / 纪律自陈）→ **同批**改门控与 `SCHEMA.md`（`CRITERIA-CHANGE-P05.md` §7 第 3 条） |
| ⛔ | 不得先改产物后补判据（`DESIGN-CONTRACT.md` §4② 第 2 条：那会让判据从「约束」退化为「描述」） |

### B-3 契约收口③：每波次跑门控 + 自检 + 幂等 + 渲染

见 B-0 第 4 条。★ **四样缺一样，这一波不算做完**（对应 `HANDOFF-R3.md` §六.6.1 的第 1–6、9 条）。

---

## C. 开工必做（照 `DESIGN-CONTRACT.md` §4① 三步，逐条落地）

| 步 | 动作（可执行） | 跑不动的后果（契约原文） |
|:--:|---|---|
| 1 | **读 `DESIGN-CONTRACT.md`**：§1 规则表（R-01…R-24）、§2 G 清单、§4 本协议 | 「触碰了 R-xx 却没声明 ⇒ 收口时 §2 G 清单必然漏项」 |
| 2 | **复跑环境探测**：`cd 04-prototype/16-checkpoint && python3 _probe_env.py` | 「⛔ **不得开工**：能力可用性未知时，任何『做不到』的结论都是待验证假设」 |
| 3 | **声明本轮触碰的 R-xx**：写进 `ROUND-LEDGER.json` 的 `rounds[].rs_touched`（新增一个 round 对象） | 「`rs_touched` 为空 ⇒ **P40 FAIL**」 |

### ★ 为什么第 2 步是「开工必跑」而⛔ 不是抄上一轮的结论

因为它踩过坑：**「某能力不可用」这个结论本身会过期**。

- 第 1 轮的结论是「浏览器在本会话不可用」（`CONTINUE-PROMPT-D2.md` §0 的浏览器行、`CONTINUE-PROMPT-D3.md` §10、`VERIFY-CONSTRAINT.md` §开头）。
- 第 2 轮实测**推翻**：真因是 `CapEff=0000000000000000` + `NoNewPrivs=1`，失败在**启动层**（`DESIGN-CONTRACT.md` G5 行）；而**可用的非 snap 内核一直在盘上**（`~/.cache/ms-playwright/chromium-1243/`）。⇒ 这是**误诊**，不是真实约束。
- 代价：「该结论在本任务里被当作既定约束**跑了 3 轮**」（`_reflection-candidates/candidate_20261015T1021Z_r1014_01.md` 第 8 行）。
- ⇒ 机制化为 **R-21**（`DESIGN-CONTRACT.md` §1）：**⛔ 不得把「某能力不可用」当成已确立的事实沿用上一轮的散文结论**；声明不可用而候选实际存在 ⇒ 判 FAIL。机检落点是 **P38 B 段**。

### ★ 本轮开工必须声明的 `rs_touched`（下表是**模板**，逐条按本轮实际改动增删）

| R-id | 为什么本轮会碰它 | 收口时要给的东西 |
|---|---|---|
| **R-20** | 三项契约收口里两项要**新增/修改判据**（P05、阈值） | 「同批」的证据：判据变更与产物的改动时序 + `CRITERIA-CHANGE-*.md` |
| **R-21** | 开工第 2 步 | `_probe_env.py` 的原始输出（⛔ 不得转述） |
| **R-22** | 触碰页面/样式/生成器 ⇒ 渲染证据；改完产物要重跑探针 | 本轮 PNG + 像素读数 + **重跑 `_probe_channel.py` 之后的** P38 读数 |
| **R-23** | P35 ⑫ 是代理判据、分组索引 6 列表未被覆盖（§D 有登记要求） | ⑫ 的登记是否更新（代理对象 / 直接量 / 失效面） |
| **R-24** | 若委派了内容波次或审核 | `ROUND-LEDGER.json` 每条 claim 的 `source` + `raw_output`；主 Agent 独立复跑 |
| **R-11 / R-10 / R-02 / R-05** | **每写一条新内容都可能碰到**（长文字段竖表 / 枚举位置化 / 一行一事 / 散文切分） | P35 ⑩⑪⑫、P35 ⑨、P35 ③⑬、P35 ⑦ 的逐页复算表 |

---

## D. 收口必做（照 `DESIGN-CONTRACT.md` §4③，逐条贴**原始输出**）

```bash
cd 04-prototype/16-checkpoint
python3 _probe_env.py                 # ① 环境探测（R-21）
python3 _probe_channel.py             # ② 验证通道 + 产物非退化 + 全站横向溢出（R-22）★ 必在改完产物之后跑
python3 gate_prototype.py             # ③ 门控（记退出码 + 结论行 + FAIL 项）
python3 gate_prototype.py --selftest  # ④ 自检（记「N 条判据 / M 条负例夹具」结论行）
python3 build-all.py --write          # ⑤ 幂等（记 written / removed / 二次比对干净）
python3 _geom_interactive.py          # ⑥ 几何复算（交互图）
```

| 要求 | 细节 |
|---|---|
| **贴原始输出** | ⛔ 不得只写「全绿」；结论行**逐字**贴（含退出码）。★ 子 Agent 报的读数由**主 Agent 复跑后**再贴 |
| **逐条更新 G 清单** | `DESIGN-CONTRACT.md` §2 的**每一行**：**消掉**（给出消它的判据）**或更新一行说明为什么仍在**（⛔ 不得删除） |
| **落台账** | ①–⑥ 的读数与 `source` 写进 `ROUND-LEDGER.json` 本轮对象（R-24） |
| **渲染** | 触碰页面/样式/生成器 ⇒ **必须**有真实渲染产物（`_probe_channel.py` 的 PNG + 像素读数） |

### ★ 三类**陈旧读数**（本轮收口时必须逐条处置，⛔ 不得当现态引用）

| # | 类别 | 具体件与实测事实 | 处置 |
|:--:|---|---|---|
| ① | 陈旧**散文结论** | 第 1 轮的「浏览器不可用」（`CONTINUE-PROMPT-D2.md` §0 / `CONTINUE-PROMPT-D3.md` §10）**是误诊**，可用内核一直在盘上 | 见 §C：每轮复跑 `_probe_env.py`（R-21）；凡「环境能力不可用」的陈述**必须**附本轮探针原始输出（`HANDOFF-R3.md` §六.6.3 第 15 条） |
| ② | 陈旧**机器读数** | **P38 不自己渲染**，它读**预生成的 manifest** `16-checkpoint/_probe/channel.json`（`gate_prototype.py:1886` 定义 `PROBE_MANIFEST_REL`、`:3857 _load_probe_manifest()` 只读磁盘文本；`report.md` §7.4）⇒ **改了产物必须先重跑 `_probe_channel.py`**，否则拿到**陈旧 FAIL**（实测踩过：`pre` 修完后 P38 仍报 637px） | 纪律：`改产物 ⇒ 重跑探针 ⇒ 再看判据`（R-22）。★ ①与②合起来是完整的一句：**既不看陈旧的散文结论，也不看陈旧的机器读数** |
| ③ | 陈旧**台账 / 报告** | · `ROUND-LEDGER.json` 的 round 3 对象记「40 条判据 / **152** 条负例夹具」，而现态实测 **154**（`report.md` §7.9 第 4 条①）——台账是**时点快照**，其后又加了夹具；★ 同件现读：`rounds` 只有 `round: 3` 一个对象<br>· `PUBLISH-STATE.json` 的 `gates.prototype` 已改为「判据 **P01–P40**」（本件起草时现读），但 `round: 1`、`content_status` 3/64 等仍是第 1 轮快照，⛔ 该文件由生成器产出、⛔ 不手改（`HANDOFF-R3.md` §六.6.3 对应的 §一.6 同源登记） | 台账**追加**本轮对象，⛔ 不回改旧对象；报告类快照**只追加 + 显式对齐**（`report.md` §7.0 的范式：给旧读数标时点，⛔ 不改写历史段落） |

### ★ 收口完成的判据（逐条核，`DESIGN-CONTRACT.md` §4③ 末）

`_probe_env.py` 退出码 0 · `_probe_channel.py` 的产物退化 **0 处** · `gate_prototype.py --selftest` 退出码 0 · `build-all.py --write` 二次比对干净 · §2 G 清单每行都有处置 · 台账已落盘且 **P40 PASS**。

---

## E. 第 1 轮遗留（★ **原样承接，⛔ 一条不得丢**）

> 逐条给源件指针。★ 表里第 1、2、3 项就是 §B 的三项收口；第 4、5 项本轮**可以完全不做**，但必须**逐条给处置**（做 / 或更新一行说明为什么仍在）——⛔ 不得静默消失。

| # | 项 | 源件指针 | 本轮动作 |
|:--:|---|---|---|
| 1 | **`boundary` 字段拆分**（转必填 + 67 节点逐条人工改判 + 写入 P05） | `HANDOFF-R2.md` §二.T1.1 · §一 第 3 条 · `CRITERIA-CHANGE-P05.md` §3 C3 / §7.1 | 见 §B-1 |
| 2 | **`why` 上限 / `intro` 下限按真实渲染重导** | `HANDOFF-R2.md` §二.T1.2 · §五.T6.2 · `HANDOFF-R3.md` §二.T1.2 · `CRITERIA-CHANGE-P05.md` §7.2 | 见 §B-2 |
| 3 | **64 个 `registered` 节点按组波次填满 8 区块**（+ 每波次门控 + 全量重生成 + 无断链可发布） | `HANDOFF-R2.md` §二.T2.4–5 · `HANDOFF-R3.md` §二.T1.3 · §四 R5 | 见 §B-0 |
| 4 | **发布级强化**：SH0–SH5 基线（a11y / 响应式 / SEO 元数据 / 门控）· **CI** · **`.nojekyll`** · 在 `~/opencode/projects/prompt-engineering-kg` 建仓并 push · 启用 **Pages** · 验证 **hub 自动收录**（消费点 `scripts/domain/catalog.py`） | `HANDOFF-R2.md` §二.T3.6–8 · `HANDOFF-R3.md` §二.T1.4 · §六.6.2 第 10–11 条 | 本轮**可判为不做**，但必须在 G 清单/残留里**留一行**（⛔ 不得删）。★ 它是 16 条验收里第 10–11 条的对象 ⇒ 本轮若**不**声明「可发布」，须明写「故第 10–11 条不适用」 |
| 5 | **跨仓议题**：向 `fe-starter-kit` 提「`non-text` 档（`border` 类角色，`min_contrast: null`）应补 **WCAG 1.4.11 式 3:1 下限**，并同步 10 个既有站」 | `HANDOFF-R2.md` §一 第 2 条 · §二.T4.9 · `HANDOFF-R3.md` §二.T1.5（⛔ 不在本仓修） | 同第 4 项：可不动，但留行。★ 现状约束（同源）：本站 `--border` 对底色仅 **1.0:1（浅）/ 1.06:1（深）** ⇒ 边框色可以任意不可见而**没有任何门控会失败** |

---

## F. 本轮（第 1–4 轮）新增遗留（逐条给指针）

> ★ 与本件主线的关系：**第 14 行（动效预算）会直接卡住内容波次**（每新增一个区块都可能多一个 `[data-reveal]`），其余各行是诚实性边界。⛔ 不得因为「不是本轮主线」就漏登。

| # | 遗留 | 源件指针 | 性质 / 处置 |
|:--:|---|---|---|
| 6 | **G8 长文可扫性**：「一段长散文读起来是不是一堵墙」——实测最长无标点游程 **151** caliber / p90 130 / 中位 78 | `DESIGN-CONTRACT.md` §2 G8 · `HANDOFF-R3.md` §四 R3 · `report.md` §7.8 | **明文不可机检**（无因果阈值可定）⇒ 降为 **P35 报告项**（逐条打印，⛔ 不判 FAIL）；★ 由真实渲染 + 人看兜；⛔ **不得假装机检** |
| 7 | **G9 窄视口交互图 zoom < 1**：视口 **768 → 0.8755**、**640 → 0.7077**；`<1180px` 档（1024 / 900）**仍 1.0000** | `DESIGN-CONTRACT.md` §2 G9 · `HANDOFF-R3.md` §一.5 · §四 R4 · `report.md` §7.8 | **仍在**。按 `_probe/channel.json` 的 `canvas_1440`（cyW 802）/ `canvas_768`（cyW 718）真实读数定判据；⛔ 不得把 P37 的默认视口口径推广到任意视口 |
| 8 | **`P35 ⑫` 是代理判据**：列数 ≤3 **代理**「无横向滚动」这一直接量 | `DESIGN-CONTRACT.md` §1 R-23（⚠ 部分）· §2 G4 行 · `HANDOFF-R3.md` §一.2 · §四 R15 · `CRITERIA-CHANGE-P35-G4.md` §5 | 登记已写明「代理对象 / 直接量 / 失效面」。★ 现态：直接量（P38 D 段的 `scrollWidth − clientWidth`）**已在跑** ⇒ 处置是「⑫ 可退役，但**退役须以更严新判据替代**，⛔ 不得只删不加」（`HANDOFF-R3.md` §一.2） |
| 9 | **分组索引 6 列短值表未被判据覆盖** | `DESIGN-CONTRACT.md` §2 G4 行 · `HANDOFF-R3.md` §一.3 · §四 R16 · `CRITERIA-CHANGE-P35-G4.md` §5 失效面 / §7 L2 | 保留理由（实测行宽 ≈620px < 804px）**未被判据覆盖**。★ 真渲染补充读数：该表 `tableW` 804px、横向溢出 **0**、最多 1 行（`HANDOFF-R3.md` §一.3）⇒ 若加断言，**按 `_probe/channel.json` 的实测列宽/行数取阈值**（⛔ 不凭直觉） |
| 10 | **组页 `intro` 无枚举模式** ⇒ P35 ⑨ 在组页上**前件不成立** | `DESIGN-CONTRACT.md` §2 G4 行 · `HANDOFF-R3.md` §一.4 · §四 R17 · `CRITERIA-CHANGE-P35-G4.md` §7 L3 | ⛔ 不得改 `10-dag-data/` 去造前件。**内容波次正好是解法**：写 `intro` 时该出现枚举模式才写（「该形态本就该出现时才写」，同源原文） |
| 11 | **`P40` 只能断言台账结构**，⛔ 如实性不可机检 | `DESIGN-CONTRACT.md` §1 R-24（⚠ 部分）· §2 G4 行 · `HANDOFF-R3.md` §四 R15 · `gate_prototype.py:4084-4087` 的机检边界自陈 | 明文登记「不可机检」。★ 可机检的部分（本件起草时现读源码）：`rounds[]` 每条须有合法 `round` / `started_at` / `ended_at` / 非空 `rs_touched`（R-id 必须**存在于契约规则表**）/ 非空 `artifacts` / 非空 `claims`，且 `main-agent-rerun` 的 `raw_output` 必须含 `===` |
| 12 | **`P38` 不断言 PNG 新鲜度**（陈旧 manifest 拦不住） | `DESIGN-CONTRACT.md` §1 R-22 · `report.md` §7.4 / §7.9 · `HANDOFF-R3.md` §四 R22 | P38 断言的是「非退化 + sha256 自洽」，⛔ 不问「这些 PNG 是不是本轮生成的」。★ 且它是**自洽地陈旧**（manifest 与磁盘 PNG 逐条对得上，只是对的是上一版产物）⇒ 重跑探针 ✅，但**"这是不是本轮的图"仍无人判**：收口时请**人核 + 在台账写明本轮 PNG 的路径与 mtime** |
| 13 | **`report.html` 的 `<title>` 仍写「第 1 轮」** | `report.md` §7.9 第 6 条① | **刻意不改**（front matter `title` 属历史原文，按「⛔ 不改一–六段」的同一纪律保留）⇒ 读者以 `report.md` §7.0 的时点对齐为准 |
| 14 | **动效预算四项上界**（单页 `[data-reveal]` ≤ **32** / 进场 ≤1800ms / `--dur-*` 和 ≤3.6s / `infinite` ≤12），但**上界取自 hub 基线 × 余量**，本站实测基线不同（单页最大 9、错峰 60ms） | `HANDOFF-R3.md` §四 R12 · `gate_prototype.py:72-75`（`MOTION_*` 常量，现读）· `gen-common.py:787`（注释写「单页最大 16 个」） | ★ **与内容波次直接冲突**：每新增一个 `[data-reveal]` 都吃这个预算 ⇒ 每波次后**必看 P28 的逐页读数**；若逼近 32，处置顺序是「按本站基线重导阈值（同批落登记件）」**先于**「砍内容」。⚠ 三处数字不一致（契约 §5 写 32，`gen-common.py:787` 注释写 16，`gate_prototype.py:72` 是 32）⇒ **以 `gate_prototype.py` 的常量与 P28 实读为准** |

---

## G. 新能力清单（下一轮**直接可用**，逐条给命令）

| 能力 | 命令 | 它保证什么 / ⛔ 不保证什么 |
|---|---|---|
| 真实渲染（通道本体） | `python3 _render.py --html ../12-groups/g00.html --width 1440 --height 900 --out /tmp/x.png` | 证明「CSS 生效、素材加载、字形正常」；⛔ **不证明版式符合设计意图**（`RENDER-CHANNEL.md` §六.1） |
| 真实渲染（便捷入口） | `_render.sh <html> [width] [height] [out.png]`（四位置参数，默认 1440/900；自动带 `--json` manifest） | 同上 |
| 环境探测 | `python3 _probe_env.py`（写 `_probe/env.json`） | **开工第一步必跑**（R-21） |
| 通道 + 溢出普查 | `python3 _probe_channel.py`（写 `_probe/channel.json`；8 个渲染对象含窄视口 + 深色；全站 19 页横向溢出普查 + 像素读数 + 宽度标定） | ★ **改完产物必须先重跑它**，否则 P38 读陈旧 manifest（§D②） |
| 阈值推导取证 | `python3 _probe_metrics.py`（只打印，⛔ 不落产物） | 文字度量 / 长文游程 / 横表宽度 / 窄视口 zoom。★ 它的横表宽度是**静态模型**：不折行 ⇒ 给的是「单行不折时的下界」，**⛔ 不能当判据**（`report.md` §7.2 交叉印证：模型判 4 张表 OVER，真实渲染溢出 0） |
| 门控 | `python3 gate_prototype.py` / `--selftest` / `--only P38,P39` | **40 判据 / 154 负例夹具** |
| 几何复算 | `python3 _geom_interactive.py` | 交互图**产物侧几何**（渲染证不了的那部分） |
| 开关行为自检 | `PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$HOME/.local/bin:$PATH" node _selfcheck_switches.mjs` | ★ **必须带 PATH 引导**（node 不在会话 PATH，见 §J） |
| P35 夹具对应 + ⑫ 阈值边界 | `python3 _selfcheck_p35_fixtures.py` | 3 列仍 PASS / 4 列 FAIL（防 ⑫ 退化为「有表即 FAIL」或「永不 FAIL」） |
| 通道证据一键复跑 | `python3 _render-proof/_verify_all.py` | 10/10 PASS |
| 令牌 / 图件一致性 | `python3 gen-tokens.py --check` · `python3 gen-figs.py --check` | 令牌块与图件是否与派生结果一致 |
| 全量重生成 | `python3 build-all.py --dry-run` → `--write` → 再 `--write`（验幂等） | 幂等 + 孤儿产物清理 |
| 轮次台账 | `ROUND-LEDGER.json`（`schema: pekg/round-ledger/1`） | 每轮**追加**一个 round 对象（P40 机检结构） |
| 审核子 Agent | `DESIGN-CONTRACT.md` **§3 模板**（六项动作，含**复核能力声明**与**区分自报/读数**） | 派审核时**只给一句**「照 `DESIGN-CONTRACT.md` §3 的模板执行审核」+ 本轮改动范围 |
| 无 bash 会话的调用包装 | `_run.sh` | `run_gate(path="04-prototype/16-checkpoint/_run.sh", args=["python3","gate_prototype.py"])` |

---

## H. 16 条验收定义（★ 从 `HANDOFF-R3.md` §六 **逐条搬**，⛔ 不得改写成更松的措辞）

> ★ 编号说明（本件所加，⛔ 未改动任何条件原文）：`HANDOFF-R3.md` §六 的三张表**各自从 1 起编号**，故本件在「#」列同时给出**原节号**，以免歧义。
> ★ 本波次若**不**声明「可发布」，§六.6.2（第 10–12 条）须明写「不适用」并给理由（§E 第 4、5 项）。

### H-1 硬门槛（缺一即**不算做完**）—— 源：`HANDOFF-R3.md` §六.6.1

| # | 条件 | 核法 |
|:--:|---|---|
| 6.1-1 | `python3 _probe_env.py` **退出码 0** | 贴原始输出 |
| 6.1-2 | `python3 _probe_channel.py` 退出码 **0**（⇒ 产物退化 0 处 **且** 全站横向溢出 **0 处**） | 贴 D 段原始输出 |
| 6.1-3 | `python3 gate_prototype.py` 退出码 **0**（⇒ **P38 / P39 都转绿**） | 贴结论行 |
| 6.1-4 | `python3 gate_prototype.py --selftest` 退出码 **0**（判据 40 条 / 夹具 ≥154 条，**全部触发**） | 贴结论行 |
| 6.1-5 | `python3 build-all.py --write` **二次比对干净** | 贴 `written/removed/二次比对` |
| 6.1-6 | `python3 _geom_interactive.py` PASS；`node _selfcheck_switches.mjs` PASS | 贴结论行 |
| 6.1-7 | `DESIGN-CONTRACT.md` §2 的 **G1–G9 每一行**都有处置（消掉 或 更新一行说明为什么仍在，⛔ 不得删除） | 人核 |
| 6.1-8 | `ROUND-LEDGER.json` 本轮对象已落盘，**P40 PASS**，每条 claim 标了 `source` 且带原始输出 | 机检 + 人核 |
| 6.1-9 | 若本轮改了**页面/样式/生成器** ⇒ `_probe/` 有**本轮**的真实渲染 PNG（8 条）+ 像素读数 | 人核（★ 新鲜度暂靠 R22 登记） |

### H-2 交付级条件（本轮若声明「可发布」则必须满足）—— 源：`HANDOFF-R3.md` §六.6.2

| # | 条件 |
|:--:|---|
| 6.2-10 | CI 跑起来且**门控全绿**；`.nojekyll` 存在；Pages 已启用且 URL 可达 |
| 6.2-11 | hub 自动收录已验证（消费点 `scripts/domain/catalog.py`） |
| 6.2-12 | 64 个 `registered` 节点的**内容波次**至少推进一波，且每波次后门控全绿（⛔ 不得攒到最后一起跑） |

### H-3 诚实性条件（★ 与硬门槛同等重要）—— 源：`HANDOFF-R3.md` §六.6.3

| # | 条件 |
|:--:|---|
| 6.3-13 | 凡「做不到 / 未验证」的面，**逐条**写进 §2 G 清单或 §四残留，⛔ 不得含糊（「基本完成」「应该没问题」都算不合格） |
| 6.3-14 | 凡引用他人读数处，标明 `self-report` 还是 `main-agent-rerun`（R-24） |
| 6.3-15 | 凡「环境能力不可用」的陈述，**必须**附本轮 `_probe_env.py` 的原始输出（R-21） |
| 6.3-16 | `report.md` §4.3-1 的冲突必须被**显式对齐**（§一.6），⛔ 不得一句「已推翻」了事 |

★ 关于第 6.3-16 条的现态（据 `report.md` §7.6 与 §7.0）：第 4 轮已完成**时点对齐**的一半；本条要求的是「**部分推翻 + 部分被证实**」的写法（窄视口与横向溢出**已实测**，而 §4.3-1 里的「长表格横向溢出」一项**实测确实存在过** 2 处 `<pre>`）⇒ 本轮若再写报告，⛔ 不得退化成「已推翻」四个字。

---

## I. 禁忌清单（每条都给理由，⛔ 不写空话）

| # | ⛔ 禁忌 | 为什么（源件 + 节号） |
|:--:|---|---|
| 1 | **为变绿而放宽判据 / 开豁免** | 判据纪律：「⛔ 不得为通过而放宽阈值；⛔ 不得设豁免；失败即 FAIL 且退出码非 0」（`CONTINUE-PROMPT-D2.md` §4 / `CONTINUE-PROMPT-D3.md` §8）。★ G6 的处置是范例：**修的是产物，不是阈值**（`report.md` §7.3） |
| 2 | **正则机械拆分 `boundary`** | 实测会**降低内容质量**：`PE-F-03` 的「…而是边界：」是**主题词**被误捕，而 `PE-P-02` 真正的边界句**反而未被捕获**（`CRITERIA-CHANGE-P05.md` §3） |
| 3 | **把委派方自报当读数** | 「子 Agent 的『完成』按其**开工时刻**的世界观交付 ⇒ 主 Agent 须按**收口时刻**复核其**事实陈述**」（R-24，`DESIGN-CONTRACT.md` §1）；实例：G4 报告仍写「浏览器不可用」 |
| 4 | **用 `agent-browser` 做视觉验证** | 它是**假绿通道**：`agent-browser 0.34.0` 回显 `✓ Screenshot saved to …` 却产出**纯白 1 色空图**（1280×577，`uniq_colors=1`），且把 `--output` 当字面文件名（`DESIGN-CONTRACT.md` G5 行 / `VERIFY-CONSTRAINT.md`）⇒ 此前据它声称「已验证视觉」的结论一律无效 |
| 5 | **只改产物不补判据** | R-20：任一改动必须与判据**同批**（新增规则 ⇒ 同批落判据或登记为未落实）；契约「⛔ 不允许第三种状态」（`DESIGN-CONTRACT.md` §1 R-20 + §4② 第 1 条） |
| 6 | **改写历史报告段落** | 只允许「追加 + 显式对齐」：`report.md` §7.0 的范式是给旧读数**标时点**，「⛔ 不是回头改写历史段落」（`ARCHIVE-HANDOFF-R4.md` §4 同源要求） |
| 7 | **把 `CRITERIA-CHANGE-P23.md` 说成「原件找回」** | 它是**补登记件**：开篇自陈「本件是补登记件，不是原件找回……由**产物侧事实反推**而成，⛔ 不主张复原了原作者的全部论证；凡实现里没有记录的动机，一律标〔推断〕」（`CRITERIA-CHANGE-P23.md` §开头 / §5.1）；`ARCHIVE-HANDOFF-R4.md` §5.4 列为硬要求 |
| 8 | **改完产物不重跑探针就宣布转绿** | P38 读的是落盘 manifest（`report.md` §7.4）⇒ 会拿到「自洽地陈旧」的读数 |
| 9 | **把静态宽度模型当判据** | `_probe_metrics.py` C 段的横表合计宽**不折行**；真实渲染溢出 0 而模型判 4 张 OVER（`report.md` §7.2）⇒ 能作判据的只有渲染期直接量 |

---

## J. 环境事实（★ 可直接照抄的硬事实，逐条给来源）

| # | 事实 | 来源 |
|:--:|---|---|
| 1 | **node / npm 不在会话 PATH** ⇒ 跑 `.mjs` 自检须**显式 PATH 引导**：`PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$HOME/.local/bin:$PATH"` | `_selfcheck_switches.mjs:9` 的用法注释（逐字） |
| 2 | `dot`（graphviz）**在 PATH**；★ 但构建链**不依赖它**：图件是**预渲染入库**，`build-all.py` 不引入外部可执行依赖（仅 `gen-figs.py --write` 需要本机 `dot`） | `gen-figs.py` §文件头（第 8–9、21 行）· `gen-common.py:875`（「⛔ 构建期不调 graphviz」） |
| 3 | 站点必须**以 `04-prototype/` 为文档根**起静态服务器（⛔ 不用 `file://` 直开——背景素材会 404） | `_render.py:44-46`（「root=04-prototype」）· `gen-common.py:1262-1264`（「本形态要求站点以**站点根为文档根**提供……`python3 -m http.server` 即可」） |
| 4 | **真实渲染通道** = playwright-python **1.63.0** + **非 snap** Chrome for Testing **153.0.8010.12**（`~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`）⇒ ⛔ 不必新装任何东西 | `_probe/env.json`（`non_snap_chromium.found = true`、`playwright_python.version = 1.63.0`）· `_render.py:58-59` · `RENDER-CHANNEL.md:12-13` |
| 5 | **snap 通道结构性不可用**：`CapEff=0000000000000000` + `NoNewPrivs=1` ⇒ `snap-confine` 取不到 `cap_dac_override`，失败在**启动层**（⛔ 不是「`/run/user/1000` 只读」——该路径实测存在且可写） | `_probe/env.json` 的 `caps` / `snap_negative_control` · `DESIGN-CONTRACT.md` G5 行 |
| 6 | 会话写入权限面 = **`workspace-write`** ⇒ ⛔ 写不到 `~/.dsh/`；反思候选只能**落项目内暂存**（`04-prototype/16-checkpoint/_reflection-candidates/`），再由**持有记忆侧写权的角色**逐字搬到 `~/.dsh/reflection/candidates/` | `_reflection-candidates/README-STAGING.md` §一（含「按提示做过一次一次性升级 ⇒ **被用户驳回**，此后不再尝试任何越权写入」） |
| 7 | 无 bash 的会话里，用 `run_gate` 包装：`run_gate(path="04-prototype/16-checkpoint/_run.sh", args=[...])` ≡ `cd 16-checkpoint && <...>` | `_run.sh` §文件头 |

---

## K. 交接契约

1. **要委派就照 `DESIGN-CONTRACT.md` §3 的模板**：派审核子 Agent 时**只给一句**「照 `DESIGN-CONTRACT.md` §3 的模板执行审核」+ 本轮改动范围；模板的六项动作含①逐条找落实证据 ②「存在机检判据且 PASS」才算已落实 ③分「被违反」与「从未被判据覆盖」两类 ④★**复核能力声明**（把「某能力不可用」当**待验证假设**，亲自跑 `_probe_env.py`）⑤★**区分自报与读数** ⑥⛔ 不改产物、⛔ 不改判据、⛔ 不提「建议放宽阈值」。
2. **★ 硬条款：子 Agent 的「完成」有保质期。** `DESIGN-CONTRACT.md` §4④ 第 3 条原文：「它带着**开工时刻**的世界观交付（本轮实例：G4 报告仍写『浏览器不可用』）⇒ 主 Agent 须按**收口时刻**复核其**事实陈述**，⛔ 不整段采信」。⇒ 并发运行时，**每一条引用子 Agent 的读数都要主 Agent 独立复跑**（门控 / 自检 / 渲染 / 几何，逐条），并在台账里分别标 `self-report` / `main-agent-rerun`（§4④ 第 1–2 条）。
3. **动同一批文件前先确认子 Agent 已停手**：「报失败」≠「进程已停」（§4④ 第 4 条；处置：落盘前跑静默期侦察，如 `_g4_settle.py`）。
4. **审核结论与门控冲突时以产物为准**，并把冲突**登记为契约缺陷**（§4⑤ 第 3 条）——⛔ 不得「以门控为准」把审核意见压掉。
5. **收口时交回**（照 §4③）：①–⑥ 的**原始输出** + G 清单逐条处置 + `ROUND-LEDGER.json` 本轮对象。★ 若本轮触碰了页面/样式/生成器，还要交本轮真实渲染 PNG 与像素读数。

---

## L. 一句话交接

> 前四轮把**规则、判据、通道、台账**都立起来了（40 判据 / 154 夹具 / G1–G7 全消）；这一轮是第一次**大规模往里填内容**——
> 于是风险从「机制有没有」变成「**内容与纪律同步不跑偏**」：67 条 `boundary` 要**逐条人工**判（正则必错）、阈值要**按真渲染重导**（直觉必错）、
> 每写一波都要**重跑探针再看判据**（不重跑必读到陈旧读数）。
> ⛔ 本轮不要开新战线：把 64 个节点填进去，把三项收口做掉，把三条陈旧读数逐条处置掉。

---

## 自检（A–K 十一项检查表，逐项给行号区间）

| 项 | 要求 | 是否命中 | 行号区间 |
|:--:|---|:--:|---|
| A | 任务身份与读者锚点（一句话：这是什么站 / 给谁看 / 当前阶段） | ✅ | §A · 第 **41–46** 行 |
| B | 本轮唯一主线＝内容波次（8 区块 / 按组 / 保持无断链可发布）＋ 三件同批收口（`boundary` 必填 67 条人工改判不得正则 / `why` 上限与 `intro` 下限按真渲染重导 / 每波次门控+自检+幂等+渲染） | ✅ | §B · 第 **50–85** 行（B-0 **52–60**、B-1 **62–70**、B-2 **72–81**、B-3 **83–85**） |
| C | 开工必做（读契约 → 复跑 `_probe_env.py` → 声明 R-xx）＋「环境能力不可用这个结论本身会过期」 | ✅ | §C · 第 **89–115** 行（三步表 **91–95**、★理由 **97–104**、`rs_touched` 模板 **106–115**） |
| D | 收口必做（六条命令原始输出 + 逐条更新 G 清单 + 落台账 + 三类陈旧读数 + 收口完成判据） | ✅ | §D · 第 **119–148** 行（命令块 **121–129**、要求表 **131–136**、三类陈旧读数 **138–144**、完成判据 **146–148**） |
| E | 第 1 轮遗留原样承接（5 条，逐条源件指针） | ✅ | §E · 第 **152–162** 行（表 **156–162**：boundary **158** / 阈值 **159** / 64 波次 **160** / 发布级强化 **161** / 跨仓 3:1 **162**） |
| F | 本轮（第 1–4 轮）新增遗留（9 条，逐条指针） | ✅ | §F · 第 **166–180** 行（表 **170–180**：G8 **172**、G9 **173**、⑫ 代理 **174**、6 列表 **175**、`intro` 枚举 **176**、P40 **177**、P38 新鲜度 **178**、`<title>` **179**、动效预算 **180**） |
| G | 新能力清单（逐条给命令） | ✅ | §G · 第 **184–202** 行（表 **186–202**，16 条） |
| H | 16 条验收定义（逐条搬，9 + 3 + 4，不改松） | ✅ | §H · 第 **206–242** 行（6.1-1…9 **215–223**、6.2-10…12 **229–231**、6.3-13…16 **237–240**） |
| I | 禁忌清单（每条给理由） | ✅ | §I · 第 **246–258** 行（9 条 **250–258**） |
| J | 环境事实（逐条给来源） | ✅ | §J · 第 **262–272** 行（7 条 **266–272**） |
| K | 交接契约（§3 模板 + 子 Agent「完成」有保质期写成硬条款） | ✅ | §K · 第 **276–282** 行（★ 硬条款在 **279**） |
| ★ | 另加：一句话交接（L） | ✅ | §L · 第 **286–291** 行 |

**本件起草期做的实测核对**（用于 §J 与 §0 的现读数字，⛔ 非引用他人自报）：`04-prototype/16-checkpoint/_d4_probe.py`（只读脚本，只打印不落任何产物）——读数：`node`/`npm` 均 `shutil.which → None` 而 `~/.nvm/versions/node/v24.19.0/bin/node` 存在（`v24.19.0`）；`dot → /usr/bin/dot`（graphviz 2.43.0）；`~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome` 存在（293285184 B）；`PUBLISH-STATE.json` 现读 `content_status = {complete:3, registered:64}`、`pending_nodes` 64 条、`round = 1`；`ROUND-LEDGER.json` 现读只含 `round: 3`。

**本件交付前的自检读数**（`04-prototype/16-checkpoint/_d4_verify.py`，只读脚本；四项原始输出）：
① 章节行号表（A–L 全部在列，本件共 **321 行**）；② **H 节 16 条与 `HANDOFF-R3.md` §六 原文逐字比对：16 / 16 命中**（比对口径 = 条件列逐字 `in` 源件表格单元格集合；首次跑出 15/16 是因为本件曾把第 16 条的 `§一.6` 增补了源件没有的限定语 ⇒ **已改回逐字**）；③ 文中反引号里的文件/路径引用 **29 条可解析**，唯一「盘上找不到」的是 `CRITERIA-CHANGE-*.md`——它是**通配写法**（源件即如此写：`DESIGN-CONTRACT.md` §4 写「照 `CRITERIA-CHANGE-*.md` 范式」），⛔ 非虚构路径；④ **A–K 十一节缺项 = 无**。

**⛔ 本件未写的（源件里查不到 ⇒ 删掉或标「待核」）**：
1. **1.14.0 → 1.30.5 这类标注工具版本** —— 本会话无权确认，**删掉**。
2. **`dot -V` 的确切版本号** —— 源件只写「需本机 graphviz `dot`」（`gen-figs.py` 第 21 行），**版本号不写**。
3. **`_selfcheck_switches.mjs` 是否仍 37/37 PASS** —— 源件记的是第 3 轮读数（`HANDOFF-R3.md` §五.5.2），本件**按 `self-report` 引用**，本轮须自行复跑（§H-1 第 6 条）。
4. **发布级强化（CI / Pages / hub 收录）的任何现状** —— 源件均记「未做」（`HANDOFF-R3.md` §二.T1.4），故本件只说「可判为不做但须留行」，⛔ 不猜现状。
