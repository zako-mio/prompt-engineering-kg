# 跟踪渠道（Tracking Channels）

- 节点标识：PE-N-04
- 英文名：Tracking Channels
- 所属分组：GD-N 新一代模块
- 依赖深度：第 29 层
- 内容状态：内容已写满
- 标签：新一代模块、跟踪渠道、时效

## 为什么需要它

既然结论会过期，就需要一组稳定的跟踪渠道，使刷新有据可依、且能核验结论的时效。渠道选择的原则是：优先一手来源、覆盖学术与厂商两侧、并保留一份安全侧的权威清单。渠道建好之后，纪律比清单更重要：回源日期与立场偏差都要随条目一起留档。

**适用边界**

渠道只能保证信息可达，不能保证信息正确；部分官方页面无日期戳，引用时须显式标注时效不确定，而不是假定其为最新。

## 机制说明

最小渠道集包含四类：学术侧（预印本平台的自然语言处理与密码安全分类，用于跟踪范式反转与防御机制的研究进展）、厂商侧（三大模型厂商的开发者文档与更新日志，用于跟踪现行口径与弃用时间线）。后两类为协议与标准侧（协议规范页与变更页、风险清单官方仓库，用于跟踪治理与版本变更）、以及包与仓库侧（包注册表与代码托管平台的元数据，用于核验工具版本与维护活跃度）。使用要点有三条：每次刷新记录回源日期；对无日期戳的页面标注时效不确定；对厂商自述的量化数字标注立场偏差，不作中立证据。

## 何时该用 / 何时不该用

- 定期刷新最新一代内容时：按四类渠道逐项核验，并记录回源日期。
- 需要核验某条结论是否仍现行时：优先查厂商文档与规范变更页。
- 不适用于把渠道当正确性保证：渠道只保证可达，正确性仍需交叉验证。
- 不适用于忽略页面时效标注：无日期戳页面不得假定为最新。

## 实验台

### file（markdown）

```markdown
# 刷新表（四类渠道最小集）

每刷新一条结论，就在下表加一行；一行只对应一次回源。

| 渠道类别 | 一手来源 | 页面或仓库 | 页面自身日期 | 回源日期 | 关联条目 | 立场偏差 |
|---|---|---|---|---|---|---|
| 学术 | arXiv cs.CL 新提交 | https://arxiv.org/list/cs.CL/recent | 时效不确定（列表页逐篇不同） | 2026-11-02 | PE-N-01 | 预印本未经同行评审 |
| 厂商 | Claude Docs 提示工程页 | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices | 时效不确定（页面无日期戳） | 2026-11-02 | PE-N-03 | 厂商自述 |
| 协议与标准 | MCP 规范版本页 | https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning | 2026-07-28 | 2026-11-02 | PE-N-03 | 无 |
| 包与仓库 | DSPy 最新发布元数据 | https://api.github.com/repos/stanfordnlp/dspy/releases/latest | 2026-10-12 | 2026-11-02 | PE-N-04 | 无 |

填写规则：「页面自身日期」只填页面或元数据自带的日期，取不到就写「时效不确定」，不要用回源日期顶替；「立场偏差」列对厂商自述的量化数字必须写明，含数字但不表明立场的行视为不合格。
```

预期观察：表格恰好覆盖学术、厂商、协议与标准、包与仓库四类各一行，且每行的回源日期非空；页面自身日期一列只出现页面自带日期或「时效不确定」，凡把回源日期填进该列的行判不合格。

### file（python）

```python
# tracking_check.py —— 刷新表的最小校验：四类齐备、日期不缺、厂商数字标立场
import csv, datetime

KINDS = {"学术", "厂商", "协议与标准", "包与仓库"}
COLS = ["渠道类别", "一手来源", "页面或仓库", "页面自身日期",
        "回源日期", "关联条目", "立场偏差"]


def day(s):
    return datetime.date.fromisoformat(s)          # 非 ISO 日期直接抛错


rows = list(csv.DictReader(open("tracking.csv", encoding="utf-8")))
assert rows and list(rows[0].keys()) == COLS, "表头不符 %s" % list(rows[0].keys() if rows else [])

bad = []
for r in rows:
    if r["渠道类别"] not in KINDS:
        bad.append((r["页面或仓库"], "渠道类别不在四类闭集"))
    if not r["回源日期"]:
        bad.append((r["页面或仓库"], "缺回源日期"))
    else:
        day(r["回源日期"])
    own = r["页面自身日期"]
    if not own:
        bad.append((r["页面或仓库"], "缺页面自身日期"))
    elif own != "时效不确定":
        day(own)                                   # 有日期戳就必须可解析
    if not r["关联条目"]:
        bad.append((r["页面或仓库"], "缺关联条目"))
    if r["渠道类别"] == "厂商" and not r["立场偏差"]:
        bad.append((r["页面或仓库"], "厂商自述数字未标立场偏差"))

missing = sorted(KINDS - {r["渠道类别"] for r in rows})
assert not missing, "四类渠道缺 %s" % missing
assert not bad, bad
print("rows=%d kinds=4 missing=0 bad=0" % len(rows))
```

预期观察：脚本打印一行 rows=N kinds=4 missing=0 bad=0；四类渠道缺任一类、回源日期为空或不是可解析日期、页面自身日期为空或既不是日期也不是「时效不确定」、某行缺关联条目、厂商行未标立场偏差时，脚本以 AssertionError 退出。

## 证据

- **厂商把弃用公告集中在一个固定的 Release notes 页，并把最早关停日期在同一页跟踪，说明厂商侧渠道的时间锚位置是固定可查的。**（S-0120，official）
  - 出处：https://ai.google.dev/gemini-api/docs/deprecations
  - 原文关键句：Deprecation announcements are made on the Release notes page, and the announced earliest shutdown dates are tracked on this page.
- **协议规范页用一张对照表同时给出三类原语与各自的控制方，说明协议侧渠道可用于核验概念归属与版本语义。**（S-0020，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/server
  - 原文关键句：Prompts: Pre-defined templates or instructions ... | Prompts | User-controlled | Resources | Application-controlled | Tools | Model-controlled |
- **代码托管平台的发布元数据同时带 tag 号与 ISO 发布时间戳，说明包与仓库侧渠道可用于核验工具现行版本与维护活跃度。**（S-0083，official）
  - 出处：https://api.github.com/repos/stanfordnlp/dspy/releases/latest
  - 原文关键句："tag_name":"3.4.1" ... "published_at":"2026-10-12T23:12:32Z" ... "DSPy 3.4.1 makes GEPA's structured InstructionProposer the default instruction proposer"

## 术语

- **提示词版本化与回归（Prompt Versioning and Regression）**：把提示词当作代码资产纳入版本控制，并在每次改动后跑同一评测集对比基线，防止无声退化。

## 失效模式

- 症状：刷新时只记结论不记回源日期；后果：下一轮无法判断该结论是否过期，既重复核对又漏掉真正失效的条目。
- 症状：把没有日期戳的页面默认为最新；后果：引用的页面可能早已停更，时效不确定被伪装成确定。
- 症状：把厂商自述的提升百分比当作中立证据；后果：结论带立场偏差，跨厂商比较被系统性拉向对自己有利的一侧。
- 症状：把渠道清单当成正确性保证；后果：渠道只保证页面可达，可达不等于正确，错误结论会被一手来源的外表背书。

## 一句话小结

四类渠道覆盖学术、厂商、协议标准与包仓库，每次刷新记录回源日期。

## 在本站知识结构中的位置

- 前置：PE-N-03
- 后继：无
