# 接续件 · D2：生成器 + 页面 + 门控

> 上游：`10-dag-data/*.json`（D1 产出，**已完成**）· `SCHEMA.md`（数据契约）· `ADR-001`（架构决策）· `BD-001`（模块边界）
> 本件是**委派子 Agent 的任务书**，也是本轮原型的最后一段工程。
> ⛔ 本件不重述契约与架构正文，只写"怎么做"。

## 0. 前置事实（实测，⛔ 不要重新探测）

| 项 | 值 |
|---|---|
| 令牌层 | `16-checkpoint/gen-tokens.py` **已由主 Agent 写好并自检 6/6 PASS**；用法：`--print` / `--write` / `--check` / `--selftest` / `--report` / `--contrast <BG>`。⛔ **不要重写它，也不要另造第二套对比度公式** |
| 契约快照 | `10-dag-data/_contract.snapshot.json`（sha256 `f99621718ee1d879295da42ab05f9e0ac1cae77e878c32e2efcb3a296fc12020`，contract_version 1.1.1） |
| 浏览器 | ⛔ **本会话不可用**（snap chromium 卡在只读 `/run/user/1000`）。见 `VERIFY-CONSTRAINT.md`。⇒ 验证只走机检，⛔ 不要尝试截图 |
| cytoscape | `13-interactive/vendor/cytoscape.min.js` + `cytoscape-dagre.min.js` 已在位（自 0817 站复制） |

## 1. 生成器（`16-checkpoint/`）

**必须共用同一个外壳函数**（ADR 第一条硬性决定）：节点页 / 组页 / 视图页 / 根入口**全部**经同一个 `page_shell(...)` 产出。⛔ 不得出现第二套模板——门控要断言模板标识集合的大小 = 1。

| 脚本 | 职责 |
|---|---|
| `gen-common.py` | `page_shell()`（唯一外壳）· 站内导航（面包屑 + 回到根 + 回到所属组）· 令牌块内联（调 `gen-tokens.py --print` 取内容，⛔ 不自己拼 CSS 令牌）· 对比度工具（**复用 `gen-tokens.py` 的函数，⛔ 不重写公式**）· 站内链接约定 |
| `gen-nodes.py` | 由 `dag.json` 生成 `11-node-pages/<id 小写>.html`（**本轮只落 3 个 `complete` 节点**；其余 `registered` 节点本轮不落页，但必须写进 `PUBLISH-STATE.json` 的 `pending_nodes`） |
| `gen-groups.py` | `12-groups/index.html` + `12-groups/g<NN>.html`（11 组全出） |
| `gen-views.py` | `14-views/01-learning-path.html`（按拓扑层序的学习路径）+ `14-views/02-frontier.html`（新一代模块，由 `frontier.json` 驱动） |
| `gen-root.py` | 根 `index.html`（双轨入口：速览→交互图 / 深学→学习路径） |
| `gen-md.py` | `15-md/` 镜像（index / groups / nodes / learning-path / frontier） |
| `gen-interactive.py` | `13-interactive/index.html`（cytoscape：组级视图 + 点击下钻 + 深链；**同目录 `vendor/` 外链是唯一白名单例外**） |
| `build-all.py` | 主入口：`--dry-run`（先出新增/修改/删除清单）· `--write`（幂等落盘 + **孤儿产物清理**）· 无参数=help |

**幂等硬要求**：连续两次 `--write` 后全部产物的逐文件 sha256 完全一致；`--dry-run` 的差异清单与实际落盘清单差集 = 0；已从真相源删除的对象，其产物文件必须被清理（残留数 = 0）。

## 2. 页面结构

- **节点页 8 区块**：`why` / `intro` / `when` / `lab` / `evidence` / `terms` / `pitfalls` / `summary`。`registered` 节点若落页须**显式标注内容状态**（⛔ 不得静默留白）。
- **组页**：组内节点表（按 `layer` 升序）+ 本组学习路径 + 组间前后继。
- **视图页**：学习路径（拓扑层序，每层列出节点与"为什么在这层"）；新一代模块（`edition` / `as_of` / 每条 `status` 徽标 / `supersedes` 指向 / 未实测标注）。
- **每页页首写一行注释声明相对路径基准**：`<!-- base: ../ -->`。
- ⛔ 公开产物中**不得出现**内部编号（`§` 编号、「门控级/咨询级」）、绝对路径、主机名、令牌串。

## 3. 自包含与目录契约（生成前写成生成器常量）

| 受检集合 | 约束 |
|---|---|
| `11-node-pages/` `12-groups/` `14-views/` 根 `index.html` | 外链 script = 0 · 外链样式/资源 = 0 · `@import` = 0 · 跨目录相对路径资源引用 = 0 |
| `13-interactive/` | 唯一例外：允许引用 `13-interactive/vendor/` 前缀下的本地脚本；⛔ 例外不得扩散 |

## 4. 门控（`16-checkpoint/gate_prototype.py`）

**判据清单以 `SCHEMA.md` §8 的 P01–P14 为基线**，并按 ADR 的 quality_scenarios 补齐以下**新增判据**（编号续接）：

| 判据 | 断言 |
|---|---|
| P15 | 模板标识集合大小 = 1（⛔ 无第二套外壳） |
| P16 | 幂等：连续两次生成后逐文件 sha256 一致；不一致文件数 = 0 |
| P17 | `--dry-run` 差异清单与实际落盘清单差集 = 0 |
| P18 | 孤儿产物残留数 = 0 |
| P19 | 令牌漂移：注入单字段漂移的**负向夹具**必须被判失败；漂移报告须列出漂移字段名与两侧取值 |
| P20 | 契约覆盖：11 个角色中本站消费 7 个、未覆盖 4 个**显式登记**；覆盖数/应覆盖数报告齐全 |
| P21 | 前沿刷新：改动 `frontier.json` 后其余模块产物 sha256 变化数 = 0；每条必含 `as_of`/`edition`，`status` ∈ 三值闭集 |
| P22 | `content_status` 配额：`complete` ≥3 且 8 区块全非空；`registered` ≥60 且 why/intro/summary 达下限且非空洞占位 |

**判据纪律**：⛔ 不得为通过而放宽阈值；⛔ 不得设置豁免；失败即 FAIL 且退出码非 0；`--selftest` 必须**逐条触发负例**（⛔ 恒真判据、空集判据、豁免判据一律算不合格）。

## 5. 交付与自检

1. 跑 `python3 gen-tokens.py --write` 再跑 `build-all.py --dry-run` 与 `--write`（各一次，再跑第二次验幂等）。
2. 跑 `gate_prototype.py`（须 0 FAIL）与 `gate_prototype.py --selftest`（须全部负例触发）。
3. 写 `04-prototype/PUBLISH-STATE.json`（含 `as_of`/`edition`/`round`/`published:false`/`counts`/`gates`/`pending_nodes`）。
4. ⛔ 只写 `04-prototype/` 下的文件；⛔ 不碰 `10-dag-data/*.json` 与 `_contract.*`；⛔ 不碰 `gen-tokens.py`。
5. 返回时把 `gate_prototype.py` 与 `--selftest` 的**真实输出原文**放进 `data`。
