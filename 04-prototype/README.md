# 新一代提示词工程 · 知识全景图与教程

> 面向**有工程基础、提示词工程尚未系统化**的工程师：把提示词工程按**依赖分层**整理成一张知识图谱，
> 每个知识点给出**可回源证据**、**适用边界**与**失效模式**，并显式标出哪些社区经验在**新一代推理模型**上已经失效。

站点入口：<https://zako-mio.github.io/prompt-engineering-kg/> ｜ 仓库：`prompt-engineering-kg`

---

## 一、这是什么

一套**数据驱动、幂等生成**的静态知识站：`10-dag-data/` 是唯一真相源，一组生成器把
它派生成可直接阅读的页面与机器可读镜像；「新一代模块」是一个只含数据的独立分区，
刷新它只需改该分区的一个台账文件并重跑生成器与门控。

**双轨交付**：一张可点、可下钻的**交互全景图**（速览）；一组**分层节点页**（深学）。

## 二、当前进度（诚实标注）

| 项 | 数 | 说明 |
|---|---:|---|
| 知识节点 | 67 | 已写满 **35** / 架构在册待写 **32** |
| 知识分组 | 11 | `g00`–`g09` ＋ `gd-n`（新一代模块） |
| 依赖边 | 96 | 全部为有向依赖，DAG 无环 |
| 页面 | 51 | 节点页 35 ＋ 组页 12 ＋ 视图页 2 ＋ 交互 1 ＋ 根入口 1 |
| 图件 | 47 | 全部本站自制、内联、随主题 |

★ **「架构在册待写」不是留白**：这 32 个节点在组页、学习路径与交互图上以**徽标显式标注**
（虚线边框），并逐条登记在 `PUBLISH-STATE.json` 的 `pending_nodes`。⛔ 本站不静默留白。

## 三、目录结构

```
04-prototype/                 # ← 发布根（Pages 部署的就是这一层）
├── index.html                # 根入口
├── favicon.svg  og.png       # 站点图标 / 社交卡（静态资产）
├── sitemap.xml  robots.txt   # 站点级发现协议（由 gen-meta.py 生成）
├── .nojekyll                 # 关闭 Jekyll
├── 10-dag-data/              # ★ 唯一真相源（dag / glossary / sources / frontier / 令牌 / 调色板）
│   └── figures/              #   图件源（.dot）与产物（.svg），94 件
├── 11-node-pages/            # 节点页 35 个
├── 12-groups/                # 组页 11 个 ＋ 分组索引
├── 13-interactive/           # 交互全景图（唯一允许引用同目录 vendor/ 本地脚本的页面）
│   └── vendor/               #   cytoscape / cytoscape-dagre（脚本白名单，⛔ 不扩散）
├── 14-views/                 # 学习路径页 / 新一代模块页
├── 15-md/                    # 机器可读 MD 镜像（与 HTML 同源派生）
├── 16-checkpoint/            # 生成器 ＋ 门控 ＋ 设计契约 ＋ 判据变更登记件
└── PUBLISH-STATE.json        # 发布态台账（生成物）
```

## 四、本地复跑（零构建、零外链依赖）

```bash
cd 04-prototype/16-checkpoint
python3 build-all.py --dry-run        # 只输出新增/修改/删除清单
python3 build-all.py --write          # 幂等落盘（二次比对必须干净）
python3 gate_prototype.py             # 判据 P01–P41（退出码 0 = 全 PASS）
python3 gate_prototype.py --selftest  # 逐条触发负例（证明判据可判假）
python3 gate_a11y.py                  # 无障碍判据 A1–A7
python3 gate_seo_meta.py              # head 元数据判据 S1–S11
```

依赖：`python3`（3.12）＋ `graphviz`（出图）。⛔ 无第三方 Python 包依赖。

## 五、门控体系（三层，各自独立）

| 层 | 脚本 | 判据 | 判什么 |
|---|---|---|---|
| 站点自建 | `16-checkpoint/gate_prototype.py` | **P01–P41** | 真相源结构 / 自包含 / 主题与令牌 / 对比度 / 内容呈现 / 图件规格 / 交互几何 / 验证通道 / 留档闭合 |
| 无障碍 | `16-checkpoint/gate_a11y.py` | **A1–A7** | skip 链 / 焦点可见 / 地标 / 内联图形可访问 / `lang` / 图标声明 / skip 的首停点 |
| 元数据 | `16-checkpoint/gate_seo_meta.py` | **S1–S11** | head 六件 / canonical 自指 / og 一致 / 图标可达 / robots+sitemap 双向闭合 |

三条硬纪律：

1. **每条判据都必须可判假** —— `--selftest` 逐条注入负例，任一条未触发即判该判据本身不合格。
2. **计数型判据一律带空集守卫** —— 集合为空即 FAIL，防判据恒真。
3. **⛔ 不为通过而放宽阈值、⛔ 不设豁免白名单** —— 判据改动必须与产物改动**同批**，并落
   `CRITERIA-CHANGE-*.md` 登记件（`P39` 会双向闭合校验这件登记）。

## 六、★ 本仓与既有卫星站的**有意偏离**（⛔ 不得读作遗漏）

同类知识图谱站（本账号下 7 个）一律走 **GitHub Pages 的 legacy 分支发布**（`main /` 为发布根）。
**本仓例外**，原因与代价如下：

| # | 偏离 | 原因 | 代价 |
|:--:|---|---|---|
| 1 | **发布根在子目录 `04-prototype/`**，经 `.github/workflows/pages.yml` 发布 | 本仓是**双面仓**：仓根是过程归档面（生成器、门控、设计契约、轮次台账），发布面是其下的一个子目录 | legacy 分支发布**不支持子目录** ⇒ 必须走 Actions ⇒ 每次发布都真跑一遍生成器 + 门控 |
| 2 | **`.nojekyll` 既入库、又由 CI 的 build job 再 `touch` 一次** | 仓内一份保证 `04-prototype/` 直接可用；CI 一份满足「谁产出发布目录、谁负责 `.nojekyll`」 | 两处都要维护（⛔ 但两者必须一致，且都为空文件） |
| 3 | **CI 分两档**：push 跑「CI 档」子集；全量 P01–P41 + 渲染探针走 `workflow_dispatch` ＋ 每周一次 | 全量档含渲染与几何复算，单次数分钟；push 档要快 | ⚠ **不是所有判据每次 push 都跑** —— 见 `16-checkpoint/_ci_gate.sh` 的 `--only` 清单，那是**有意**的分级 |
| 4 | **⛔ 不 vendor `vendor/pipeline/` 令牌管线** | 那套件服务的是「一站两形态（内联 ＋ 外链样式表）」；本站是**全站内联**（R-18 零外链）⇒ 无外链样式面 | 与同类站的值件/schema 形状**不对齐**（如实声明，⛔ 不假装已对齐） |

## 七、许可与素材

- 站点代码与内容：本站自制。
- 背景摄影素材：见页脚逐素材署名（夜间帧 CC BY 4.0、日间帧 CC0 1.0）。
- 交互图脚本：`13-interactive/vendor/` 下的 cytoscape / cytoscape-dagre（MIT）。
- 引用纪律：⛔ 不转载书籍、标准或论文正文；只登记题录、链接与不超过 200 字的原文关键句。

## 八、数据口径

- 全部主张的 `evidence[].quote` 与来源库（`10-dag-data/sources.json`）**逐片段回源**校验
  （`_wave1_apply.py` 的合并校验 ＋ 数据侧 `C58`）。
- `terms` 的术语头必须**逐字命中** `10-dag-data/glossary.json` 的 `term`（数据侧 `C33`）。
- 「未证实」与「已证伪」是两种判定，⛔ 不混用。
