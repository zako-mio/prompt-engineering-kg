# 上下文即工作内存与四策略（Context as Working Memory and Four Strategies）

- 节点标识：PE-C-01
- 英文名：Context as Working Memory and Four Strategies
- 所属分组：G03 上下文工程
- 依赖深度：第 6 层
- 内容状态：内容已写满
- 标签：上下文工程、工作内存、策略

## 为什么需要它

把上下文当作模型的工作内存来管理，是 2025 至 2026 年最上位的一条工程口径：它把提示词、检索、记忆、工具定义与消息历史放进同一个资源池，并给出写入、选择、压缩、隔离四类可操作策略。掌握本节点是为了能在「该常驻、该检索、还是该压缩掉」之间做出有依据的选择。

**适用边界**

四策略是组织框架而非清单，其取舍取决于模型的有效注意力与任务的串行深度，不能脱离评测集直接套用。

## 机制说明

工作内存的隐喻带来三条直接推论：内存容量不等于可用容量（受注意力预算约束）、写入需要成本（token 与延迟）、以及清理与压缩是必要动作而非优化。四类策略因此可以这样分工：写入（把需要长期复用的结论沉淀为记忆或笔记）、选择（按需检索与按需加载）、压缩（对长历史做摘要与结构化提取，保住结论而丢弃过程）、隔离（把子任务放进独立上下文，只回传结论）。四类策略不是并列的技巧清单，而是一组需要权衡的预算分配。

## 何时该用 / 何时不该用

- 长时程任务上下文持续增长时：必须组合压缩与结构化笔记，而不是无限追加。
- 任务可分解为独立子任务时：用隔离把过程留在子上下文里。
- 不适用于把四策略当清单照做：取舍取决于模型有效注意力与任务串行深度。
- 不适用于无评测集的压缩：压缩会丢信息，必须用评测集确认丢失的是非关键信息。

## 实验台

### file（python）

```python
blocks = {
    "system_instructions": 900,
    "tool_schemas": 1400,
    "retrieved_docs": 5200,
    "message_history": 12000,
    "scratchpad_notes": 600,
}

total = sum(blocks.values())
for name, n in sorted(blocks.items(), key=lambda kv: -kv[1]):
    print(f"{name:20s}{n:7d}{n / total:8.1%}")

history_share = blocks["message_history"] / total
print("compress_first:", "message_history" if history_share > 0.5 else "retrieved_docs")
```

预期观察：输出五行按 token 降序的分类占比，末行为 compress_first: message_history；说明长时程任务应先压缩历史并写成结构化笔记，而不是继续追加检索内容。

## 证据

- **官方文档把上下文工程的操作归为隔离上下文、跨步骤持久化与压缩数据三类，可作为本节点四策略框架的对照。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **上下文工程的优化目标是找到最小的高信噪比 token 集合，而不是把可用信息尽量塞满窗口。**（S-0004，official）
  - 出处：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：good context engineering means finding the smallest possible set of high-signal tokens
- **写入策略的工程落点是把用户偏好、事实与共享知识存成图状态之外的持久化存储，使其不必每轮重新进入上下文。**（S-0123，vendor）
  - 出处：https://docs.langchain.com/oss/python/langgraph/persistence
  - 原文关键句：Stores persist application-defined data outside the graph state. ... including user preferences, facts, and shared knowledge.

## 术语

- **上下文工程（Context Engineering）**：在推理时点管理与筛选进入上下文窗口的全部 token（含工具定义、MCP、外部数据、消息历史、记忆），目标是维持一组最小的、高信噪比的 token 集。
- **提示词工程（Prompt Engineering）**：编写与组织指令（尤其 system / developer 指令）以取得最优单次结果的方法集合；关注「如何对模型说话」。

## 失效模式

- 把四策略当清单逐条照做：短任务上也加摘要与子上下文隔离，多出摘要损失与协调开销，端到端质量反而下降。
- 上下文写满才清理：早期约束与已确认结论被一并摘要掉，模型随后反复推翻已定方案。
- 只在主上下文里不断追加检索结果：重复片段占满窗口并抬高单次成本，真正需要的证据被挤出注意力范围。
- 用子上下文隔离却不回传结构化结论：父层拿不到可判定的事实，只能重跑子任务。

## 一句话小结

把上下文当作模型的工作内存，用写入、选择、压缩、隔离四策略来管理它。

## 在本站知识结构中的位置

- 前置：无
- 后继：PE-C-02
