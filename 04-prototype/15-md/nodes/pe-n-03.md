# 模块维护机制（Module Maintenance Mechanism）

- 节点标识：PE-N-03
- 英文名：Module Maintenance Mechanism
- 所属分组：GD-N 新一代模块
- 依赖深度：第 28 层
- 内容状态：内容已写满
- 标签：新一代模块、维护机制、刷新

## 为什么需要它

本领域知识时效性衰减很快，如果把「最新一代」的内容散落到各个知识节点，每次刷新都要改动大量文件并重新验证。把它收敛为一个只含数据的分区，刷新动作就变成改一处、重跑生成与门控，这是本站能长期维护的结构性前提。

**适用边界**

该机制只覆盖「最新一代」这一类时效性内容；稳定的机制型知识仍按普通节点维护，两者不应混用同一刷新流程。

## 机制说明

机制包含四个约定：载体（条目集合以数据文件承载，不含教程正文）、字段（每条带时间锚、版次、状态与取代关系）、状态取值（限定为已确认、有争议、未证实三值，不得新增）、以及刷新动作（改条目集合与时间锚、重跑生成器与门控，不改任何页面模板）。字段中「取代关系」是维持历史可解释性的关键：一条结论被后续条目取代时，旧条目应被标记而非删除，使读者能理解某个建议为何曾经成立。

## 何时该用 / 何时不该用

- 刷新最新一代内容时：只改条目集合与时间锚，重跑生成与门控。
- 条目被新结论取代时：标记取代关系而非删除旧条目，保留历史可解释性。
- 不适用于把稳定机制型知识也放进本分区：两者刷新流程不同，混用会导致频繁改动。
- 不适用于跳过版次与时间锚的一致性断言：会出现假刷新。

## 实验台

### file（python）

```python
# refresh_probe.py —— 改一条条目并重跑生成器，断言改动没有泄漏到该模块之外
import json, pathlib, shutil, subprocess, sys, tempfile

SITE = pathlib.Path(__file__).resolve().parent.parent      # 04-prototype/
OWN = {"14-views/02-frontier.html", "15-md/frontier.md"}    # 由条目集合驱动的两页
TARGET = "PE-N-03"


def build(root):
    p = subprocess.run([sys.executable, str(root / "16-checkpoint/build-all.py"),
                        "--dry-run", "--json", "--root", str(root)],
                       check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


work = pathlib.Path(tempfile.mkdtemp()) / "site"
shutil.copytree(SITE, work, ignore=shutil.ignore_patterns(
    "__pycache__", "_LOCAL_ARCHIVE", "_r*_backup"))
base = build(work)
assert not (base["added"] or base["modified"] or base["deleted"]), "基线不干净：先落盘一次再复现"

doc = json.loads((work / "10-dag-data/frontier.json").read_text(encoding="utf-8"))
item = [i for i in doc["items"] if i["id"] == TARGET][0]
item["supersedes"] = sorted(set(item.get("supersedes") or [])
                           | {"%s@%s" % (TARGET, doc["edition"])})
doc["previous_edition"] = doc["edition"]
doc["edition"] = doc["as_of"] = "2026-11"
(work / "10-dag-data/frontier.json").write_text(
    json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

now = build(work)
leak = sorted(set(now["modified"]) - OWN)
print("modified=%d own=%d leak=%d added=%d deleted=%d"
      % (len(now["modified"]), len(set(now["modified"]) & OWN), len(leak),
         len(now["added"]), len(now["deleted"])))
print("leak_files=%s" % leak[:3])
assert not leak, "刷新泄漏到别的产物"
assert now["modified"] and set(now["modified"]) <= OWN, "该模块的产物必须变化，否则是假刷新"
assert doc["as_of"] == doc["edition"], "时间锚与版次不一致，判为假刷新"
print("refresh_ok=1")
```

预期观察：在整站的临时副本上运行，脚本先打印一行 modified=、own=、leak=、added=、deleted= 的计数，再打印 leak_files=[]（空列表），最后打印 refresh_ok=1；一旦基线不干净、改动泄漏到这两个产物之外、该模块的两页没有变化，或时间锚与版次不一致，脚本以 AssertionError 退出。

### file（python）

```python
# check_entries.py —— 条目集合的四个不变量，任一条不成立即判本次刷新不可发布
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
doc = json.loads((ROOT / "10-dag-data/frontier.json").read_text(encoding="utf-8"))
items = doc["items"]
ALLOWED = {"confirmed", "disputed", "unverified"}     # 状态闭集，不得新增第四值
ids = {i["id"] for i in items}


def ref_ok(s):
    return s.split("@")[0] in ids                      # 允许 id@版次 形式指向旧版次


assert doc["as_of"] == doc["edition"], "时间锚必须与版次一致"
assert not [i["id"] for i in items if i.get("status") not in ALLOWED], "状态越出闭集"
assert not [(i["id"], s) for i in items for s in (i.get("supersedes") or [])
            if not ref_ok(s)], "取代关系指向不存在的条目"
assert not [i["id"] for i in items if not i.get("evidence")], "条目必须带 evidence"

print("entries=%d status_ok=1 supersedes_ok=1 anchor=%s/%s"
      % (len(items), doc["as_of"], doc["edition"]))
```

预期观察：脚本打印一行 entries=N status_ok=1 supersedes_ok=1 anchor=版次/时间锚，其中两个日期字段必须逐字相同；状态出现第四种取值、取代关系指向不存在的条目、任一条目缺 evidence，或时间锚与版次不一致时，脚本以 AssertionError 退出。

## 证据

- **协议规范页用「当前协议版本号 + 修订状态标记」两个字段表达版次，这正是条目集合所需的时间锚与状态字段的现行形态。**（S-0023，official）
  - 出处：https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning
  - 原文关键句：The current protocol version is 2026-07-28. ... Revisions may be marked as: Draft / Current / Final.
- **厂商对将被移除的能力给出显式弃用时间线：弃用起点与关停日期都写明，旧用法被标记弃用而非立刻删除。**（S-0011，official）
  - 出处：https://developers.openai.com/api/docs/guides/prompt-engineering
  - 原文关键句：OpenAI is deprecating reusable prompt objects in the API. Prompt creation will be de-emphasized beginning June 3, 2026 ... `v1/prompts` is scheduled to shut down on November 30, 2026.
- **风险清单以状态行与发布日期作版次锚，条目编号带年份前缀，说明整代结论是用新条目更替表达的，而不是就地改写旧条目标题。**（S-0031，official）
  - 出处：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/README.md
  - 原文关键句：Status: Published | Release date: August 4, 2026 ... LLM01:2026 Prompt Injection | LLM02 Sensitive Information Disclosure | LLM03 Excessive Agency
- **同一项目方的官方索引页仍停在 2025 版，与仓库正文的 2026 版并存，构成一处真实的同步落差。**（S-0034，official）
  - 出处：https://genai.owasp.org/llm-top-10/
  - 原文关键句：TOP 10 FOR GEN AI 2025 Top 10 Risk & Mitigations for LLMs and Gen AI Apps

## 术语

- **三代范式脉络（Three-Generation Paradigm Arc）**：2020-2023 提示词工程、2023-2025 上下文工程、2025-2026 编排与编译三个相继阶段；三者是叠加而非替代关系。
- **门控即判据（Gate as Executable Criterion）**：把「这次改动是否可接受」写成可执行的检查脚本并以其退出码作结论，使质量判断可复现、可回归。

## 失效模式

- 症状：刷新时直接改写旧条目的结论并把原条目删掉；后果：读者看不出某条建议为何曾经成立，历史解释链断掉。
- 症状：改了条目集合却没有同步更新版次与时间锚；后果：生成器无法区分真刷新与假刷新，旧口径被当成新口径发布。
- 症状：把稳定的机制型知识也塞进这个只含数据的模块；后果：两类内容的刷新周期不同，一次小改动就要连带重验大量页面。
- 症状：只看官方索引页上的版本号，不核对仓库正文；后果：索引页与正文的版次并不同步，会取到上一代条目当作现行口径。

## 一句话小结

最新一代只含数据，刷新只改一处，并断言版次与时间锚保持一致。

## 在本站知识结构中的位置

- 前置：PE-N-02、PE-M-04
- 后继：PE-N-04
