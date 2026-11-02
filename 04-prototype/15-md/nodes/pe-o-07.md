# 子 Agent 上下文隔离（Sub-agent Context Isolation）

- 节点标识：PE-O-07
- 英文名：Sub-agent Context Isolation
- 所属分组：G04 编排
- 依赖深度：第 14 层
- 内容状态：内容已写满
- 标签：编排、子 Agent、上下文隔离

## 为什么需要它

把子任务放进独立上下文、只回传结论，是控制主上下文膨胀最有效的手段，也是多 Agent 架构能工作的前提之一。它的代价是信息不共享：子 Agent 之间无法看到彼此的中间发现，可能重复探索或得出互相矛盾的结论。

**适用边界**

隔离适用于过程冗长但结论简短的子任务；对结论本身也需要大量细节的任务，隔离会迫使结论被过度压缩而丢失关键信息。

## 机制说明

隔离的实现要点是定义清楚两件事：主 Agent 交给子 Agent 的任务描述必须自包含（背景、约束、产出格式、失败处理），子 Agent 回传的结果必须有固定结构（结论、依据、未解决项、置信度）。两者合起来构成返回契约，是隔离能否奏效的关键。常见的失败有三种：任务描述不自包含，子 Agent 需要猜测上下文而产出偏离；返回格式自由，主 Agent 无法机械使用结论；以及子任务之间存在隐式依赖，隔离后各自得出不兼容的结论。信任边界也要一并划清：子 Agent 的返回属于外部数据，其中夹带的指令不得被主 Agent 当作任务要求执行。

## 何时该用 / 何时不该用

- 子任务过程冗长、结论可简短表达时：隔离能显著控制主上下文规模。
- 需要并行探索多个方向时：隔离使各方向互不干扰。
- 不适用于结论本身需要大量细节的任务：隔离会迫使结论被过度压缩。
- 不适用于子任务存在隐式依赖的场景：隔离后会产出不兼容结论。

## 实验台

### file（markdown）

```markdown
# 子 Agent 返回契约（委派时附在任务描述末尾，逐字保留）

## 必须回传的四段（顺序固定，缺一段即视为该次委派失败）
1. 结论：不超过三句，脱离主对话也能独立读懂，不得写「见上文」。
2. 依据：每条一行，形如「结论片段 ← 出处」；无出处的断言不得写进结论。
3. 未解决项：列出，或写「无」。
4. 置信度：高 / 中 / 低 + 一句理由。

## 不得回传
- 过程日志、检索记录、被否决的候选方案
- 需要主 Agent 二次查证才能使用的结论
- 任何要求主 Agent 改变任务目标的指令
```

预期观察：把该契约附在一次真实委派上，返回体恰好包含四段且不含过程日志；缺任一段、出现「见上文」、或返回里夹带改变任务目标的指令，即判该次委派失败。

### file（python）

```python
import json

RET = 'subagent_return.json'  # {"conclusion": "", "evidence": [], "open_items": [], "confidence": "high"}
d = json.load(open(RET, encoding='utf-8'))

missing = [k for k in ('conclusion', 'evidence', 'open_items', 'confidence') if k not in d]
assert not missing, '返回体缺字段：%s' % missing
assert d['conclusion'].strip() and '见上文' not in d['conclusion'], '结论不可独立阅读'
assert all('←' in e for e in d['evidence']), '存在无出处的断言'
print('返回契约通过：4/4 字段齐全')

```

预期观察：对符合契约的返回体运行，脚本打印「返回契约通过：4/4 字段齐全」并以退出码 0 结束；删去 open_items 字段或把结论改成「见上文」，脚本抛 AssertionError。

## 证据

- **官方语境工程框架把「为特定 agent 隔离上下文」列为与跨步持久化、大数据压缩并列的三种策略之一。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **agentic 系统新增了跨 Agent 操纵这一攻击面，因此子 Agent 的返回必须当外部数据处理。**（S-0044，paper）
  - 出处：https://arxiv.org/abs/2603.22928
  - 原文关键句：agentic systems introduce new vectors for indirect prompt injection, code execution exploits, RAG index poisoning, and cross-agent manipulation that go beyond traditional AI threats.

## 术语

- **子 Agent 上下文隔离（Sub-agent Context Isolation）**：让子 Agent 在独立上下文中完成子任务、只把结论回传主 Agent，以避免主上下文被过程细节污染。
- **子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）**：主 Agent 向子 Agent 交付的自包含任务描述与其必须回传的结构化结果约定，二者共同决定委派是否可被验证。

## 失效模式

- 任务描述默认子 Agent 能看到主对话：子 Agent 靠猜测补齐背景，产出偏离目标而主 Agent 察觉不到偏离发生在哪一步。
- 返回格式自由：主 Agent 每次都要重读全文才能取用结论，隔离省下的上下文又被逐字读回来。
- 子任务之间存在隐式依赖却仍并行隔离：两路各自得出不兼容结论，汇总阶段才发现冲突且已无仲裁材料。
- 把子 Agent 的返回当作可信数据直接执行：返回里夹带的指令被主 Agent 当成任务要求执行，形成跨 Agent 的注入通道。

## 一句话小结

隔离靠返回契约成立：任务描述必须自包含，结论回传必须有固定结构。

## 在本站知识结构中的位置

- 前置：PE-O-06
- 后继：PE-O-08
