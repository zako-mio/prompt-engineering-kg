# 接续件 · D5：内容波次 2 起（还剩 59 个 `registered` 节点）+ 本轮新开的判据面收口

> 上游：`CONTINUE-PROMPT-D4.md`（上一份工作令，已完成）· `ROUND-LEDGER.json` 的 **round 5**（本轮收口台账：15 条 claim / 23 条 artifacts / G1–G18 处置）· `CRITERIA-CHANGE-P22.md` · `CRITERIA-CHANGE-P05-R5.md` · `DESIGN-CONTRACT.md`（R-01…R-24 / §2 G 清单 / §3 审核模板 / §4 六项协议）
> 性质：**工作令**（粘进新会话即可开工），⛔ 不是台账。
> ★ 本件所有数字都给了**源件 + 节号或命令**；源件里查不到的，本件不写。

---

## 0. 已就绪的前置（⛔ 不要重写）

| 件 | 现态（第 5 轮收口实测） | 用法 |
|---|---|---|
| `gate_prototype.py` | **P01–P40 / 159 条负例夹具**，退出码 0 | `python3 gate_prototype.py`；`--selftest`；`--only P05,P22` |
| `10-dag-data/_selfcheck.py` | **数据侧自检**，`PASS（FAIL 0 / WARN 3）` | ★ **第 5 轮起并入收口协议**（见 §D）：`python3 10-dag-data/_selfcheck.py` |
| `DESIGN-CONTRACT.md` | R-01…R-24 + §2 G 清单（G1–G9）+ §3 模板 + §4 六项协议 | 纪律源；§4① 开工三步骤照做 |
| `CRITERIA-CHANGE-P22.md`（新） | 两态配额 → **状态↔内容一致性**（`complete ≥3` 保留；`registered` 的 lab/evidence/pitfalls 必须为空） | 判据为何长这样 |
| `CRITERIA-CHANGE-P05-R5.md`（新） | `boundary` **字段化执行** + `why` 上限 / `intro` 下限按真实渲染重导 | 同上 |
| `SCHEMA.md` | §3 两态表与字段表已同步（`boundary` **必填**、上限 693 / 777） | 字段契约 |
| 探针三件 | `_probe_env.py`（开工必跑）· `_probe_channel.py`（通道 + 全站溢出普查）· `_probe_metrics.py`（静态取证件） | 见 §D |
| `_probe_thresholds.py`（新） | **真实渲染**下的阈值取证（只打印、⛔ 不落产物） | 版式一变就重跑它 |
| 波次工具四件（新） | `_b1_prefill_boundary.py`（boundary 预填，dry-run 默认）· `_b1_emit_review.py`（出改判表）· `_wave1_content.json`（内容草稿载体）· `_wave1_apply.py`（合并 + **引文回源校验**） | 见 §H：下一波照抄这套 |
| `ROUND-LEDGER.json` | 三轮（round 3 / 4 / 5），**round 5 完整** | 每轮**追加**一个 round 对象（P40 机检 `rounds[]`） |
| `PUBLISH-STATE.json` | `round = 5` · `content_status = {complete: 8, registered: 59}` · `pending_nodes` **59 条** · `counts.html` 已改为**由 `complete` 派生** | 进度真相源；★ 由生成器产出，⛔ **不手改** |

### 文件基线（开工时可复算，防"读到过期版本"）

| 件 | 字节 | 说明 |
|---|---:|---|
| `ROUND-LEDGER.json` | 39275 | 三轮；round 5 = 第 5 轮收口 |
| `gate_prototype.py` | 约 250000 | 40 条判据 |
| `10-dag-data/dag.json` | 约 120000 | 67 节点；**67/67 已有 `boundary`** |
| `_b1_boundary_review.md` | 5716 | 67 行改判表 |
| `_wave1_content.json` | — | 波次 1 的内容载体（可作波次 2 的模板） |

---

## A. 任务身份与当前阶段

**这是什么站**：`prompt-engineering-kg` 原型站——「新一代提示词工程」知识全景图的可发布静态站（零构建自包含，`04-prototype/` 即文档根）。
**给谁看**：要按 DAG 顺序学这套知识的读者（站内入口是「速览→交互图 / 深学→学习路径」双轨）。
**当前阶段**：**内容填充期**，且**第 5 轮已解锁**。现态 **8 个 `complete` / 59 个 `registered`**；59 个 `registered` 已在 `pending_nodes` 逐条登记但**不可点入**。
⇒ 本轮及后续唯一的产出方向：**按组继续把 `registered` 填满 8 区块**，并守住「任何时刻都是无断链可发布状态」。

---

## B. 本轮目标（唯一主线）＝内容波次 2 起

1. **进度真相源**：`PUBLISH-STATE.json` 的 `pending_nodes`（现 59 条）与 `content_status.registered = 59`。
2. **按组推进**：11 组，**每次一个组**的量级（⛔ 不一次全铺）。**建议下一波 = G01（PE-S-01…PE-S-05，5 个节点）**，其后 G02 的 7 个、G03 的 7 个 …
   ★ 已完成：G00 的 6 个节点（`PE-F-01` 本就 complete，其余 5 个为第 5 轮波次 1 所填）。
3. **每节点必填四样**（缺一样该节点不能翻 `complete`）：`lab`（≥1，建议 2）、`evidence`（≥1，建议 2–3）、`pitfalls`（≥1，建议 3–4）、**1 张自制内联 SVG 图**（P35 ⑧ 对一个节点页而言是硬要求）。
4. **每波次必做**（逐字承接 D4 §B-0 第 4 条）：
   > 「每波次跑门控 + 全量重生成；保持"任何时刻站点都是无断链可发布状态"」
   ⇒ **一波 = 改数据 → 出图 → `build-all.py --write` → 重跑 `_probe_channel.py` → 门控 → 自检（门控 + 数据侧）→ 幂等二次比对 → 渲染**，⛔ 不得攒到最后一起跑。
5. ★ **渲染不是可选项**：凡触碰页面/生成器，必须有本轮真实渲染产物（`_probe_channel.py` 的 PNG + 像素读数），并对**新增节点页**各留 1 张实拍（`_render.py`）。

---

## C. 开工必做（照 `DESIGN-CONTRACT.md` §4① 三步）

| 步 | 动作 | 跑不动的后果 |
|:--:|---|---|
| 1 | **读契约**：§1 规则表（R-01…R-24）、§2 G 清单、§4 本协议；并读 `CRITERIA-CHANGE-P22.md` 与 `CRITERIA-CHANGE-P05-R5.md`（第 5 轮改过的两条判据） | 触碰了 R-xx 却没声明 ⇒ 收口时 §2 G 清单必然漏项 |
| 2 | **复跑环境探测**：`cd 04-prototype/16-checkpoint && python3 _probe_env.py` | ⛔ **不得开工**：能力可用性未知时，任何「做不到」的结论都是待验证假设（R-21） |
| 3 | **声明 `rs_touched`**：写进 `ROUND-LEDGER.json` 的 `rounds[].rs_touched`（**新增一个 round 对象**，`round: 6`） | `rs_touched` 为空 ⇒ **P40 FAIL** |

★ **建议声明的 `rs_touched`（按实际改动增删）**：`R-01`（每页一图）、`R-05`（散文切分）、`R-07`/`R-08`/`R-09`（图件：每页一图 / 规格 ≤600px / 字形覆盖）、`R-10`（枚举位置化）、`R-11`（长文竖表）、`R-20`（同批）、`R-21`、`R-22`、`R-23`、`R-24`。

---

## D. 收口必做（逐条贴**原始输出**）

```bash
cd 04-prototype/16-checkpoint
python3 _probe_env.py                 # ① 环境探测（R-21）
python3 _probe_channel.py             # ② 通道 + 产物非退化 + 全站横向溢出（R-22）★ 必在改完产物之后
python3 gate_prototype.py             # ③ 门控（记退出码 + 结论行 + FAIL 项）
python3 gate_prototype.py --selftest  # ④ 自检（记「N 条判据 / M 条负例夹具」）
python3 build-all.py --write          # ⑤ 幂等（记 written / removed / 二次比对干净）
python3 _geom_interactive.py          # ⑥ 几何复算（交互图）
python3 ../10-dag-data/_selfcheck.py  # ⑦ ★ 数据侧自检（第 5 轮起并入本清单；★ 路径相对 16-checkpoint）
```

| 要求 | 细节 |
|---|---|
| **贴原始输出** | ⛔ 不得只写「全绿」；结论行**逐字**贴（含退出码） |
| **逐条处置 G 清单** | `DESIGN-CONTRACT.md` §2 的 G1–G9 + 台账里的 G10–G18：**消掉**（给出消它的判据）**或更新一行说明为什么仍在**（⛔ 不得删除）。★ 第 5 轮的做法：§2 只**追加**新行，逐条处置写进本台账的 `g_list_updates`（⛔ 不改历史行） |
| **落台账** | ①–⑦ 的读数与 `source` 写进本轮对象（R-24）；`main-agent-rerun` 的 `raw_output` 必须含 `===` |
| **渲染** | 触碰页面/样式/生成器 ⇒ **必须**有本轮真实渲染产物 |

### ★ 三类陈旧读数（每轮都要处置，⛔ 不得当现态引用）

| # | 类别 | 本仓实例 |
|:--:|---|---|
| ① | 陈旧**散文结论** | 第 1 轮的「浏览器不可用」是**误诊**（可用内核一直在盘上）⇒ 每轮复跑 `_probe_env.py`（R-21） |
| ② | 陈旧**机器读数** | **P38 不自己渲染**，它读预生成的 `_probe/channel.json` ⇒ **改产物必须先重跑 `_probe_channel.py`**（R-22）；踩过：修完 `pre` 后 P38 仍报 637px |
| ③ | 陈旧**台账 / 报告** | 台账是**时点快照**（`report.md` §7.x 写「152/154 夹具 / P01–P37 / registered ≥60 配额」都是**各自收口时刻**的读数；现态为 **159 夹具 / P01–P40 / 配额已换判据**）⇒ 台账**追加**，⛔ 不回改旧对象；报告只**追加 + 显式对齐** |

---

## E. 残留（⛔ 不得静默消失；逐条给处置）

| # | 项 | 源件指针 | 建议动作 |
|:--:|---|---|---|
| 1 | **还剩 59 个 `registered` 节点**（G01 起） | `PUBLISH-STATE.json` 的 `pending_nodes` | 按 §B 的每波次循环推进；**建议一波一组** |
| 2 | **`counts` 与产物实数一致 → 仍无判据** | 台账 round 5 的 `G12`（`counts.html` 的写死 bug 第 5 轮已修） | 建议挂到 **P13** 上（⛔ 不新增判据编号），并补负例夹具 |
| 3 | **MD 镜像与 HTML 页内容一致 → 无判据** | 台账 `G13`（`gen-md` 丢边界第 5 轮已修） | 同上，建议挂到 P13 并补夹具 |
| 4 | **引文回源校验只在作者期助手里** | 台账 `G14`；工具 = `_wave1_apply.py` | 建议升级为数据侧判据（如 `C58`）：节点 evidence 的每条 quote 片段须能在 `01-research/evidence/A*.json` 里逐字定位 |
| 5 | **`PE-C-03`（图检索/GraphRAG）与 `PE-C-06`（提示缓存）在 115 条源池内无源** | 台账 `G16` | 属 G03（不在 G01 波次）；动到它们之前**先补已回源条目**（`sources.json` 有 C37–C40 约束），⛔ 不得编造引文 |
| 6 | **P35 ⑫ 代理判据可退役但须以更严判据替代** | 台账 `G18` 第⑧项 | 退役动作未做；⛔ 不得只删不加 |
| 7 | **分组索引 6 列短值表未被判据覆盖** | 台账 `G18` 第⑨项 | 若加断言，按 `_probe/channel.json` 的实测列宽/行数取阈值（⛔ 不凭直觉） |
| 8 | **组页 `intro` 无枚举模式 ⇒ P35 ⑨ 前件不成立** | 台账 `G18` 第⑩项 | 「内容波次正好是解法」：写组页导读时该出现枚举模式才写 |
| 9 | **`intro` 下限没能被渲染重导** | `CRITERIA-CHANGE-P05-R5.md` §5.6 第 2 条 | 渲染**给不出**因果下限（只给上界）⇒ 如实登记为未达成；后续波次用真实内容复核（现 corpus 最紧 129 vs 下限 120） |
| 10 | **G8 长文可扫性 / G9 窄视口 zoom / P38 不判 PNG 新鲜度 / P40 只断言结构** | `DESIGN-CONTRACT.md` §2 G8·G9；台账 `G18` 第⑪⑫项 | 均为**明文不可机检或仍在**，⛔ 不得假装机检 |
| 11 | **发布级强化（CI / `.nojekyll` / 建仓 push / Pages / hub 收录）与跨仓 3:1 议题** | `CONTINUE-PROMPT-D4.md` §E 第 4–5 项；台账 `G15` | 第 5 轮判为**不做**；若本轮仍不做，须继续留行并明写「H-2 第 10–11 条不适用」 |
| 12 | **`DESIGN-CONTRACT.md` §4③ 的「五步/六步」计数** | 台账 `G17`（第 5 轮已把标题改「六步」） | 已完成，无需再动 |
| 13 | **R-07 的「每页 ≥1 自制图」在组页/视图页/入口页未落实**（24 页仅 9 页有图） | 台账 `G19`（★ 第 5 轮审核当场报出；P35 ⑧ 的**声明**已对齐为「节点页」） | **须二选一**（属用户裁决面）：**(a) 改契约**——把 R-07 的措辞限定为节点页，与 `CONTENT-V2.md` 的组页/视图页骨架表一致；**(b) 补图**——为 15 页各出一张自制图（成本 15 张 DOT，且会改这些页的版式 ⇒ 须同批重跑 P28/P35/P36 与渲染证据） |
| 14 | **`_probe_thresholds.py` 的取样集硬编码为 3 个节点页**，而 `complete` 已达 8 页 | 台账 `G20` 邻面；审核 warning | 报告项（⛔ 不判 FAIL）。建议把 `PAGES` 改为「扫描 `11-node-pages/*.html` 全部节点页」，使 693/777 随内容波次自动重取 |
| 15 | **`_b1_boundary_review.md` 的「状态」列是波次 1 之前的快照**（PE-F-02…06 仍写 `registered`） | 审核 warning | 读该表时按收口时刻复核（R-24 同型）；或下一轮用 `_b1_emit_review.py` 重新生成 |
| 16 | **`_probe/channel.json` 的 `node_driver_hint.found=false` 命名误导**（本会话 node v24.19.0 在盘且跑通 37 例开关自检） | 审核 warning | 该字段只探 `.npm-global` 路径且**无判据复算**；建议改名或在探针里改成「PATH 可达性」多路探测 |

---

## F. 环境事实（★ 可直接照抄的硬事实；逐条给来源）

| # | 事实 | 来源 |
|:--:|---|---|
| 1 | **`node` / `npm` 不在会话 PATH** ⇒ 跑 `.mjs` 自检须显式引导：`PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$HOME/.local/bin:$PATH" node _selfcheck_switches.mjs` | `_selfcheck_switches.mjs` 用法注释；第 5 轮实测 `node -v` = v24.19.0 |
| 2 | `dot`（graphviz 2.43.0）**在 PATH**；但构建链**不依赖它**（图件预渲染入库，`build-all.py` 不调外部可执行；只有 `gen-figs.py --write` 需要本机 `dot`） | `gen-figs.py` 文件头；第 5 轮实测 `/usr/bin/dot` |
| 3 | 站点须**以 `04-prototype/` 为文档根**起静态服务（⛔ 不用 `file://` 直开，背景素材会 404） | `_render.py` 文件头 |
| 4 | **真实渲染通道** = playwright-python **1.63.0** + **非 snap** Chrome for Testing（`~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`）⇒ ⛔ 不必新装任何东西 | `_probe/env.json`；第 5 轮收口复跑 |
| 5 | **snap 通道结构性不可用**：`CapEff = 0` 且本会话 **`CapBnd` 也是 0**（第 4 轮为 `000001ffffffffff`）⇒ `snap-confine` 取不到 `cap_dac_override`，失败在**启动层** | 台账 round 5 的 `G11` 与 claim ③ |
| 6 | ★ **`/tmp` 在 DSH 的每次 bash 调用之间是私有的**（同一调用内可见，跨调用即消失）⇒ 渲染/探针产物**一律写进工作区**（如 `16-checkpoint/_probe/`），⛔ 不要写 `/tmp` 再跨步读取 | 第 5 轮实测：`_render.py --out /tmp/x.png` 成功，下一步 `cp` 报 No such file |
| 7 | 会话写入权限面 = 工作区；⛔ 写不到 `~/.dsh/`（反思候选只能落项目内 `_reflection-candidates/`） | `_reflection-candidates/README-STAGING.md` §一 |
| 8 | 无 bash 的会话里可用 `run_gate(path="04-prototype/16-checkpoint/_run.sh", args=[...])` 包装 | `_run.sh` 文件头 |

---

## G. 禁忌清单（每条给理由）

| # | ⛔ 禁忌 | 为什么 |
|:--:|---|---|
| 1 | **为变绿而放宽判据 / 开豁免** | 判据纪律：⛔ 不得为通过而放宽阈值；⛔ 不得设豁免；失败即 FAIL 且退出码非 0 |
| 2 | **正则机械拆分边界 / 关键词猜测** | 实测 `…而是边界：` 是**主题词**会被误捕；切分只走 `gen-common.split_boundary` 的**显式标记**查找 |
| 3 | **把委派方自报当读数** | R-24：子 Agent 带**开工时刻**的世界观交付 ⇒ 主 Agent 须按收口时刻复核其**事实陈述** |
| 4 | **用 `agent-browser` 做视觉验证** | 它是**假绿通道**（回显成功却产出纯白 1 色空图） |
| 5 | **只改产物不补判据** | R-20：任一改动必须与判据同批；契约不允许「已实现但无判据」这第三种状态 |
| 6 | **改写历史报告段落 / 回改旧台账对象** | 只允许「追加 + 显式对齐」 |
| 7 | **把 `CRITERIA-CHANGE-P23.md` 说成「原件找回」** | 它是**补登记件**（产物侧事实反推，推断处标〔推断〕） |
| 8 | **改完产物不重跑探针就宣布转绿** | P38 读的是落盘 manifest ⇒ 会拿到「自洽地陈旧」的读数 |
| 9 | **把静态宽度模型当判据** | `_probe_metrics.py` 的横表宽度是**不折行**模型；能当判据的只有渲染期直接量 |
| 10 | **手抄 evidence 的 `url` / `tier`** | 必须按 `source_id` 从 `sources.json` **注入**（`_wave1_apply.py` 已实现），否则一条笔误就是 P06/C31 双 FAIL |
| 11 | **编造引文** | P06/C31 只查「键齐 / ≤200 字 / url·tier 一致」，**伪造可全绿通过** ⇒ 回源是**人的**责任（可用 `_wave1_apply.py` 的回源校验兜一道，它 ⛔ 挡不住引文库本身写错） |

---

## H. 每波次的可复制流程（★ 第 5 轮把工具建好了，照抄即可）

```
# 1) 内容草稿：新建 _waveN_content.json（结构照 _wave1_content.json）
#    evidence 只写 {claim, source_id, quote, quote_truncated?}；★ url/tier 由脚本注入
# 2) 出图：gen-figs.py 的 FIGS 加 N 条 + gen-nodes.py 的 NODE_FIG 加 N 条（★ 成对，否则 P35 ⑧ FAIL）
#      python3 gen-figs.py --write      # 越界色值 / 规格 >600px 会当场 SystemExit（⛔ 不得靠 CSS 缩放掩盖）
#      python3 gen-figs.py --check
# 3) 合并内容：python3 _waveN_apply.py --write   （照 _wave1_apply.py：回源校验 + 注入 + 翻态）
# 4) 全量重生成：python3 build-all.py --write    （再跑一次作幂等二次比对）
# 5) ★ 重跑探针：python3 _probe_channel.py       （否则 P38 读陈旧 manifest）
# 6) 门控 + 自检：gate_prototype.py / --selftest / ../10-dag-data/_selfcheck.py
# 7) 其余对账：_geom_interactive.py · gen-tokens.py --check · gen-figs.py --check
#              _selfcheck_p35_fixtures.py · node _selfcheck_switches.mjs（PATH 引导）
# 8) 渲染证据：_probe/ 的 8 张 + 新增节点页实拍（_render.py，★ 输出写工作区，不写 /tmp）
# 9) 台账：追加 round 6 对象（claims 逐条带 raw_output；main-agent-rerun 必须含 ===）
```

★ 每次都要看的**逐页读数**：`P28`（单页 `[data-reveal]` ≤32；第 5 轮实测最大 9，余量充足）、`P35` 的十四项、`P13`（MD 镜像 + `pending_nodes == registered`）、`P08`（新页发布后兄弟 chip 由徽标变真链接，跨页锚点不得指向未发布页）。

---

## I. 交接契约

1. **要委派就照 `DESIGN-CONTRACT.md` §3 的模板**：派审核子 Agent 时**只给一句**「照 `DESIGN-CONTRACT.md` §3 的模板执行审核」+ 本轮改动范围。
2. **★ 硬条款：子 Agent 的「完成」有保质期**（§4④ 第 3 条）⇒ 并发运行时，**每一条引用子 Agent 的读数都要主 Agent 独立复跑**，并在台账里分别标 `self-report` / `main-agent-rerun`。
3. **动同一批文件前先确认子 Agent 已停手**（「报失败」≠「进程已停」）。
4. **审核结论与门控冲突时以产物为准**，并把冲突**登记为契约缺陷**（§4⑤ 第 3 条）。
5. **收口时交回**：①–⑦ 的原始输出 + G 清单逐条处置 + 台账本轮对象 + 本轮真实渲染 PNG 与像素读数。
6. **留档**：`report.md` **追加**新段（⛔ 一–七段逐字保留）；`report.html` 用 `report-renderer` 重渲染并过四项质量门控。

---

## L. 一句话交接

> 第 5 轮把**两态契约解锁了**（配额 → 状态↔内容一致性）、把 `boundary` **字段化**了、
> 把 `why` 上限按**真实渲染**重导了（693 / 777），并用**波次 1**（G00 的 5 个节点）证明这条流水线能跑通（门控 40 条 / 159 夹具全绿，14 条引文全部回源）。
> 这一轮之后，风险不再在「机制有没有」，而在「**59 个节点 × (内容 + 自制图) 的产能与纪律稳定性**」——
> 于是最要紧的是：**每波一组、每波重跑探针再看判据、每波留原始输出**，以及**不用 `/tmp` 存跨步产物**。
