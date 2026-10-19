# 子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）

- 节点标识：PE-P-03
- 英文名：Sub-agent Delegation and Return Contract
- 所属分组：G09 落地实践
- 依赖深度：第 18 层
- 内容状态：内容已写满
- 标签：落地实践、委派、返回契约

## 为什么需要它

把子任务交出去并不等于把责任交出去。子 Agent 看不到主 Agent 的上下文，也没有向用户追问的通道，它只能按拿到的任务描述独立作业。于是委派的质量由两件可检查的事决定：任务描述是否自包含，以及回传的结果是否有固定形状。缺前者，子 Agent 会在信息不足处自行补全并产出错位结论；缺后者，主 Agent 拿回一段自然语言，既无法机械使用，也看不出这份结果是否已经做完。把这两件事写成契约，委派才从一次口头请求变成可复核的工序。

**适用边界**

返回契约的收益在子任务过程冗长而结论简短时最大；若子任务结论本身就需要大量细节，过度压缩的返回契约会丢掉关键信息，此时应允许结构化地回传证据片段，而不是把篇幅上限当成铁律。

## 机制说明

自包含的任务描述应写清五项：目标、背景与约束、可用资源与工具、产出格式、以及失败时的处理方式。返回契约应规定四项：结论、依据（可追溯到具体来源或步骤）、未解决项、以及置信度或不确定性说明。工程要点有三条：其一，委派提示词应模板化并版本化，使契约变更可被评审；其二，返回结果应可被机械解析（固定字段），而不是自然语言段落；其三，应保留子 Agent 的原始输出以便复核，避免只保留摘要后无法追溯。之所以强调「只回什么」，是因为子 Agent 没有向用户发问的通道：任务里没写清的部分，它只能在正文里自行补全，而正文一旦回贴进主上下文，主上下文就会被过程细节占满，委派省下的上下文成本又被吃回去。成本事实必须提前讲明：多 Agent 系统的 token 消耗远高于普通对话，官方自述的量级是普通对话的四倍、多 Agent 约十五倍，因此委派应留给可并行的独立子任务，而不是把一个线性任务拆成多份。最后一条纪律是不要采信子 Agent 的自报：实测出现过自报准确但不完整的形态，报出的数字都对，却漏掉了没被问到的部分，所以完成度必须由委派方按自己的收口时刻复核。

## 何时该用 / 何时不该用

- 把可独立完成的子任务交给子 Agent 时：任务描述必须自包含，并把产出格式与失败时的处理方式一并写进去。
- 子任务的结论要被主 Agent 机械使用时：要求返回固定字段，而不是一段自然语言段落。
- 子任务过程冗长而结论简短时：只要求回结论、依据、未解决项与置信度，原始输出留在子 Agent 侧备查。
- 不适用于把线性任务拆成多路委派：多 Agent 系统的 token 消耗远高于普通对话，只有可并行的独立子任务才值得拆。
- 不适用于只保留摘要：主 Agent 应保留原始输出以便复核，否则结论无法追溯。

## 实验台

### file（markdown）

```markdown
# 委派单（任务描述：五项必须写全）

- 目标：<一句话说清要交付什么>
- 背景与约束：<相关事实、不可触碰的边界、口径>
- 可用资源与工具：<能读哪些文件、能跑哪些命令、不能做什么>
- 产出格式：<返回体的字段与顺序，见下>
- 失败处理：<拿不到关键信息时报 partial，并写清缺什么>

# 返回契约（子 Agent 只回这四项，不回贴正文）

| 字段 | 含义 | 上限 |
|---|---|---|
| status | success / partial / failed | 三选一 |
| summary | 结论摘要 | 不超过 200 字 |
| evidence | 依据列表，每条带来源标识 | 不超过 5 条 |
| open_items | 未解决项与不确定说明 | 逐条列出 |

# 三条纪律

1. 子 Agent 没有向用户发问的通道：任务里没写清的部分，要么按约定报 partial，要么在 open_items 里列出，不要自行补全。
2. 不回贴正文：过程细节留在子 Agent 侧，主 Agent 只接收上面四个字段。
3. 原始输出保留可查：主 Agent 需要复核时能取到子 Agent 的原始记录，而不是只有一份摘要。
```

预期观察：读者得到一份可直接复用的委派单与返回契约：五项任务描述与四个返回字段一一对应；换第二个子任务时只需替换目标与产出格式，契约本身不动，因此两次委派的返回体可以直接比较。

### shell（bash）

```bash
# 校验子 Agent 返回体的形状：字段齐全、有上限、正文没有被回贴
python3 - <<'PY'
import json, sys
d = json.loads(sys.stdin.read())
need = ("status", "summary", "evidence", "open_items")
missing = [k for k in need if k not in d]
assert not missing, "缺字段：%s" % missing
assert d["status"] in ("success", "partial", "failed"), "status 取值越界"
assert len(d["summary"]) <= 200, "summary 超上限（%d 字）" % len(d["summary"])
assert len(d["evidence"]) <= 5, "evidence 条数超上限（%d）" % len(d["evidence"])
assert all("source_id" in e for e in d["evidence"]), "evidence 缺来源标识"
assert d["status"] == "success" or d["open_items"], "非 success 必须写出未解决项"
print("返回体形状合格：字段齐全 / summary %d 字 / evidence %d 条"
      % (len(d["summary"]), len(d["evidence"])))
PY
```

预期观察：把一份返回体喂进这段校验：字段齐全、条数在上限内、来源标识逐条存在时打印合格行；把 summary 写成整段正文或漏掉 open_items 时断言失败并指出缺哪一项，于是返回契约从口头约定变成可执行的检查。

## 证据

- **官方把多 Agent 的成本量级写了出来：普通对话的四倍、多 Agent 约十五倍，因此委派不能按普通对话的成本预期来用。**（S-0006，official）
  - 出处：https://www.anthropic.com/engineering/multi-agent-research-system
  - 原文关键句：agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats.
- **官方把「为某个 Agent 隔离上下文」列为上下文工程的既定策略，说明子 Agent 的上下文隔离不是实现细节，而是可设计的一层。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **官方把提示词链、路由、并行、编排者—工作者与生成者—评估者列为五种既定编排模式，其中编排者—工作者正是委派与汇总的模式化形态，因此委派与返回可以在事前写成固定路径。**（S-0005，official）
  - 出处：https://www.anthropic.com/engineering/building-effective-agents
  - 原文关键句：Prompt chaining ... Routing ... Parallelization (Sectioning / Voting) ... Orchestrator-workers ... Evaluator-optimizer.
- **官方结构化输出以 schema 加严格模式约束解码，使输出可被机械解析，返回契约的固定字段应走同一条路，而不是靠自然语言约定。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }

## 术语

- **子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）**：主 Agent 向子 Agent 交付的自包含任务描述与其必须回传的结构化结果约定，二者共同决定委派是否可被验证。
- **子 Agent 上下文隔离（Sub-agent Context Isolation）**：让子 Agent 在独立上下文中完成子任务、只把结论回传主 Agent，以避免主上下文被过程细节污染。
- **编排者—工作者（Orchestrator–Workers）**：由编排者拆解任务并把子任务分派给多个工作者，最后汇总结果的编排模式。

## 失效模式

- 把委派写成一句话：任务描述缺背景与产出格式，子 Agent 只能在信息不足处自行补全，回来的结论与主任务错位。
- 返回体回贴正文：子 Agent 把过程细节整段送回，主上下文被过程占满，委派省下的上下文成本又被吃回去。
- 只保留摘要不保留原始输出：事后要复核时取不到依据，结论无法追溯，也判断不出是哪一步出的错。
- 采信子 Agent 的自报完成度：实测出现过自报准确但不完整的形态，报出的数字都对却漏掉了没被问到的部分，完成度必须由委派方复核。
- 把线性任务拆成多路委派：多 Agent 系统的 token 消耗远高于普通对话，并行只在子任务可独立完成时才划算。

## 一句话小结

委派要同时规定任务描述的五项自包含内容与返回结果的四项固定字段，并要求子 Agent 只回结论与依据、不回贴正文。

## 在本站知识结构中的位置

- 前置：PE-P-02
- 后继：PE-P-04
