# 留档交接契约 · **第 4 轮增量**（教训固化 + 判据扩到 P40）

> ★ 本件是 `ARCHIVE-HANDOFF.md` 的**增量**，不是替代：先按原契约执行，**再**叠加本件。
> 触发：原留档（`report.md` §六 / `report.html`）写于 **门控 37 条 / G6 未修 / P23 断链未补**之时；
> 现态已是 **40 条判据 / FAIL 0 / G6 已消 / G7 已消** ⇒ 原留档**已过期**，须刷新。
> 用户裁决：**刷新留档**（并已就 G7 选择「A 补写」、就反思候选产出者形式自行向 Reflection 环反馈）。

## 1. 本轮（第 4 轮）新增事实（真相源）

| 件 | 承载 |
|---|---|
| `16-checkpoint/DESIGN-CONTRACT.md` | 新增 **§4 §轮次执行协议**（开工/执行中/收口/委派/审核/判据变更留档六项）＋ **R-21…R-24** ＋ **G6–G9** |
| `16-checkpoint/CRITERIA-CHANGE-P38-P40.md` | 三条新判据的变更登记（含「教训→机制」六条对照表） |
| `16-checkpoint/HANDOFF-R3.md` | 下一轮接续件（七节，含 16 条验收定义） |
| `16-checkpoint/CRITERIA-CHANGE-P23.md` | **补登记件**（⛔ 非原件找回；由产物侧事实反推，推断处标〔推断〕） |
| `16-checkpoint/ROUND-LEDGER.json` | 轮次台账（每条 claim 标 source；`main-agent-rerun` 必须含原始输出标记） |
| `16-checkpoint/_probe_env.py` / `_probe_channel.py` / `_probe_metrics.py` | 开工必跑的三个探针 |
| `~/.dsh/reflection/candidates/candidate_20261015T1021Z_r1014_0{1..5}.md` | 5 条反思候选（已落盘，sha256 逐件一致） |

## 2. 本轮六条教训 → 机制（必须写进报告第七段）

| 教训 | 机制 | 机检 |
|---|---|---|
| ①「环境能力不可用」这一结论本身要复核 | `_probe_env.py` ＋ **P38 B 段**（判据自己复算内核/驱动是否存在；声明不可用而内核在盘上 ⇒ FAIL） | ✅ |
| ② 假绿通道（工具回显成功 ≠ 产物有效） | `_probe_channel.py` ＋ **P38 C 段**（判据**自己用纯 Python 解码 PNG**：尺寸/唯一色≥64/亮度区间≥32/字节≥4096，sha256 与磁盘重算比对） | ✅ |
| ③ 门控全绿 ≠ 该看的面被覆盖 | **P38 D 段**：全站 19 页横向溢出**直接量**（scrollWidth−clientWidth）；P35 新增**报告项**「逐页最长无标点游程」 | ✅／❌（可扫性**显式标注不可机检**） |
| ④ 判据与夹具的作用域必须与对象对齐 | **P39**：`CRITERIA-CHANGE-*.md` 三处引用点 ⟺ 磁盘存在性**双向闭合** | ✅ |
| ⑤ 委派方自报 ≠ 读数；子 Agent 的「完成」有保质期 | **P40** ＋ `ROUND-LEDGER.json` | ⚠ 结构可机检、**如实性不可机检**（明文标注） |
| ⑥「已实现但无判据」= 未落实 | 契约 §4③ ＋ **P40** 的 `rs_touched`（R-id 必须存在于契约规则表） | ✅ |

★ **必写的一条过程事实**：新判据**当场报出真实缺陷**（此前 37 条全绿）——`<pre>` 横向溢出 2 处
（`pe-f-01` 637px / `pe-r-02` 208px）与 `CRITERIA-CHANGE-P23.md` 断链。两条都**已处置**：
G6 由主 Agent 用 `white-space:pre-wrap` 修掉（**真实渲染实测**：19 页文档级与元素级横向溢出**均为 0**，P38 转绿）；
G7 经用户裁决走 A，补登记件落盘，P39 转绿。

## 3. 必须自己跑的命令（⛔ 数字以你自己的输出为准）

```
cd 04-prototype/16-checkpoint
python3 gate_prototype.py             # 现态应为 exit 0 / 40 条判据 / FAIL 0
python3 gate_prototype.py --selftest   # 现态应为 40 条判据 / 154 条夹具 全触发
python3 _probe_env.py ; python3 _probe_channel.py ; python3 _probe_metrics.py
python3 build-all.py --write          # 幂等（二次比对干净）
python3 gen-tokens.py --check ; python3 gen-figs.py --check
python3 _geom_interactive.py
python3 _render.py --html ../12-groups/g00.html --width 1440 --height 900 --out <png>   # 至少 1 张真实渲染
```
★ **切记**：`P38` 读的是 **`_probe/channel.json`**（预生成 manifest）⇒ **改了产物必须先重跑 `_probe_channel.py`**，
否则会得到**陈旧 FAIL**（本轮实测踩过：修完 `pre` 后 P38 仍报 637px）。这条要写进报告第七段。

## 4. 报告怎么写

- `report.md` **追加 `## 七、第 4 轮：把教训固化成机制（判据扩到 P40）`**；⛔ **一–六段逐字保留**。
- 第七段必须覆盖：六条教训→机制表（§2）、新判据当场报出的两个真实缺陷与处置、**陈旧 manifest 陷阱**、
  `§4 轮次执行协议` 的六项、`HANDOFF-R3.md` 的交接指向、反思候选 5 条已落盘（含**产出者形式**待用户向
  Reflection 环反馈这一 open item）、以及最终读数（40 判据 / 154 夹具 / G1–G9 终态）。
- 另**必须**修正一处**过期表述**：第六段或 §4.3 里凡把门控记作「P01–P37」的地方，
  改为在第七段显式说明「本段写于 P37 时点，第 4 轮后为 P01–P40」，⛔ **不要改写历史段落本身**（契约要求保留原文 + 显式对齐）。
- `report.html` 用 `report-renderer` skill 重渲染并过四项质量门控（UTF-8 无替换字符 / div 开闭平衡 / 五段完整 / 结构齐全）。

## 5. 诚实性硬要求

1. ⛔ 不虚构读数；每条数字标明来源：`主 Agent 复跑` / `委派方自报` / `你自己实测`。
2. ⛔ 不删改 `report.md` 一–六段；新增只走第七段与显式对齐句。
3. ⛔ 不改 `10-dag-data/*.json`、⛔ 不改生成器与站点产物（本轮已定稿）；只写 `report.md` / `report.html`。
4. ⛔ 不把 `CRITERIA-CHANGE-P23.md` 描述成"原件找回"——它是**补登记件**，必须原样说明。
5. ⛔ 不为让报告好看而省略 G 清单里仍开着的项（G8/G9 等）。

## 6. 返回契约

```json
{"status":"success|partial|failed","summary":"200 字以内",
 "data":{"report_md":"…","report_html":"…","sections":["一…七 各段标题"],
   "gate":"exit/判据数/FAIL 数","selftest":"判据数/夹具数","idempotent":"…",
   "probe_env":"…","probe_channel":"…","render_pngs":["…"],
   "g_status":{"G1..G9":"…"},"stale_manifest_trap":"已写入第七段 yes/no",
   "html_quality_gate":"PASS|FAIL（四项）"},
 "files_created":[],"files_modified":[],"decisions":[],"warnings":[],"errors":[]}
```
