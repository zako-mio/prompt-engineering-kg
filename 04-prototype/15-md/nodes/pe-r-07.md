# ReAct 推理—行动交织（ReAct: Interleaved Reasoning and Acting）

- 节点标识：PE-R-07
- 英文名：ReAct: Interleaved Reasoning and Acting
- 所属分组：G02 推理增强
- 依赖深度：第 15 层
- 内容状态：内容已写满
- 标签：推理增强、ReAct、工具调用

## 为什么需要它

ReAct 是把推理与工具调用交织成单一循环的控制流范式：模型先想、再调工具、再读回真实反馈，如此往复推进任务。它解释了为什么 agent 能边想边查、边查边改，也是几乎所有 agent 框架的默认骨架。手写 ReAct 格式的职责已被模型原生工具调用接管，但循环本身从未消失——线上 agent 出问题时要排查的，仍然是这个循环的轮数、终止与工具面。

**适用边界**

手写格式这一条路径只在两类场合还站得住：模型不具备原生工具调用能力，或者出于教学与调试目的需要把中间步骤显式打印出来。其余场合应当直接使用原生调用，省下的格式约束工作不会转化为任何能力。而循环层面的治理责任无法被托管：无论走哪条路径，轮数上限、终止条件、工具描述质量与失败重试策略都必须由工程侧显式设定，厂商的格式原生化并没有替你把这些一并解决。

## 机制说明

ReAct 的循环由三步交替构成。第一步是思考：模型依据当前上下文分析状态，判断下一步需要哪个工具。第二步是行动：按工具的参数模式发起一次调用。第三步是观察：读取工具返回的真实结果，把它写回上下文，再进入下一轮思考。它相对纯推理的优势，是把外部世界的真实反馈引入推理链，用检索或执行结果压住凭记忆作答带来的幻觉；它相对纯行动的劣势，是推理与行动会互相干扰——一次失败的调用可能把后续推理带偏。当前实现这个循环有三条路径：直接用模型的原生工具调用、用框架封装的现成循环、或手写格式约束模型输出思考与动作。三条路径共用同一套循环结构，区别只在格式由谁保证。

## 何时该用 / 何时不该用

- 任务需要与外部系统交互、必须依赖真实反馈才能推进时：ReAct 循环是基础范式。
- 模型具备原生工具调用能力时：直接走原生调用，不必手写 Thought/Action/Observation 格式。
- 工具数量多或描述含糊时：先治理工具的名称、描述与参数模式，再谈循环优化。
- 不适用于无需外部反馈的任务：纯推理任务上套循环只增加调用次数与延迟。
- 不适用于不设轮数上限的循环：没有终止条件会让死循环与工具滥用直接变成账单。

## 实验台

### prompt（markdown）

```markdown
为一次 ReAct 循环写清三层约束，逐条填空后再接工具：

【可用工具】只列本次任务真正需要的一到三个，每个写清名称、用途、参数模式与返回形态。
【单轮格式】每轮必须依次输出三行，缺一即判为格式失败：
Thought: 当前状态与下一步要调用的工具及理由（不超过两句）
Action: 工具名与参数（必须是合法 JSON）
Observation: 由系统填入工具返回原文，模型不得自行编造
【终止与兜底】最多轮数 N（例如 8）；达到 N 仍未得到结论时，必须停止调用工具并输出目前掌握的最优答案与未解问题；同一工具同一参数连续两次失败后必须更换参数或更换工具，不得原样重试。
```

预期观察：模型按 Thought/Action/Observation 三行交替输出，Action 为可解析的合法 JSON；轮数不超过设定上限；达到上限或连续失败时按兜底规则停止并给出带未解项的答案，而不是继续调用工具。

### shell（bash）

```bash
# 循环上线前的最小体检：轮数与工具面各看一眼
# 1) 本次运行实际发生了几轮工具调用（trajectory 里数 Action / tool_use 条目）
grep -c '"type": *"tool_use"' run-trajectory.jsonl
# 2) 有没有同一工具同一参数被反复原样重试（死循环前兆）
python3 - <<'PY'
import json, collections
c = collections.Counter()
for line in open("run-trajectory.jsonl", encoding="utf-8"):
    ev = json.loads(line)
    if ev.get("type") == "tool_use":
        c[(ev.get("name"), json.dumps(ev.get("input"), sort_keys=True))] += 1
for (name, args), n in c.most_common(5):
    print(n, name, args[:80])
print("重复调用总次数 =", sum(n for n in c.values() if n > 1))
PY
```

预期观察：第 1 条打印出本次运行的轮数，与设定上限对照即可判断是否触顶；第 2 条按「工具名 + 规范化参数」聚合，重复项次数大于 1 即说明存在原样重试，需要检查参数反馈是否被真正读入上下文。

## 证据

- **ReAct 至今仍被主流教程站列为标准提示技术，与零样本、少样本、CoT、RAG 等并列，同时该站把 Function Calling 单列为 AI Agents 分组条目——说明它既是提示技术，也是 agent 循环的入口。**（S-0066，community）
  - 出处：https://www.promptingguide.ai/
  - 原文关键句：Prompting Techniques → Zero-shot / Few-shot / CoT … / PAL / ReAct … AI Agents → Context Engineering / Function Calling
- **ReAct agent 的提示词仍是一个活跃的优化对象：在 DSPy 三个优化器的对比中，SIMBA 对 ReAct agent 的收益最大，且这一收益随模型规模增大而更明显。**（S-0052，official）
  - 出处：https://aclanthology.org/2026.findings-eacl.161/
  - 原文关键句：We study three optimizers from the DSPy framework -- COPRO, MiPROv2, and SIMBA … SIMBA providing the largest benefits for ReAct agents, particularly at larger model scales.
- **工具描述属于提示词面的一部分：精简重复指令与示例、简化工具描述，可以同时提升任务表现与 token 效率，官方内部评测给出的量级是分数 10–15%、token 41–66%、成本 33–67%。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Removing repeated instructions and examples … configurations with leaner system prompts improved evaluation scores by roughly 10–15% … reducing total tokens by 41–66% and cost by 33–67%

## 术语

- **ReAct（推理—行动交织）**：交替生成思考、动作与观察，使模型在外部工具反馈驱动下推进任务的单 Agent 控制流范式。
- **工具定义与滥用治理（Tool Definition and Abuse Governance）**：工具的名称、描述与参数模式构成提示词面的一部分；描述含糊会诱发误用，工具过多会诱发滥用与误选。

## 失效模式

- 格式塌陷：模型不再按 Thought/Action/Observation 输出，解析器取不到动作，循环要么空转要么直接崩在第一步。
- 工具滥用与误选：工具清单过长、描述含糊或彼此重叠时，模型会挑错工具或用错参数，错误在后续轮次被当成事实继续推理。
- 死循环与成本失控：不设轮数上限、又允许原样重试时，同一次调用会被反复发起，token 与外部 API 账单同步放大。
- 被观察结果带偏：工具返回的内容被当成可信指令而非数据，间接注入可篡改后续推理，循环越深污染面越大。

## 一句话小结

用原生工具调用替掉手写格式，但思考、行动、观察这个循环仍然要逐轮设防。

## 在本站知识结构中的位置

- 前置：PE-R-01
- 后继：PE-R-08
