# 分隔符与上下文隔离（Delimiters and Context Isolation）

- 节点标识：PE-F-03
- 英文名：Delimiters and Context Isolation
- 所属分组：G00 地基：模型是概率采样器
- 依赖深度：第 2 层
- 内容状态：内容已写满
- 标签：地基、分隔符、上下文隔离

## 为什么需要它

多部分提示里最容易出错的不是内容，而是边界：模型无法区分哪段是指令、哪段是示例、哪段是待处理的资料。分隔符解决的就是这个歧义问题，它让「指令」与「数据」在文本上有了可见边界，也是后续不可信内容标注与注入防御的前提。

**适用边界**

标记的效果取决于模型是否针对此类标记做过对齐训练，换模型必须重测；标记只能降低歧义，不能提供安全保证，因为模型在架构上仍不区分指令与数据。

## 机制说明

现行官方口径推荐用 XML 风格标签包裹示例与资料，理由是这类标签能让模型在多部分提示中无歧义地解析结构；同时要求把长资料放在提示前部、把 query 与指令放在其后，并在资料较多时先让模型引用相关片段再作答。工程上应把标记体系当成一套需要版本化的小规范：标签名固定、嵌套规则固定、同一含义只用一个标签，否则标记体系本身会成为新的歧义源。需要强调的是，标记的收益主要体现在「多部分提示的边界消歧」上，它不是通用性能杠杆；把它当成万能提准手段会在简单任务上白付 token。

## 何时该用 / 何时不该用

- 提示同时包含指令、示例、资料与用户输入时：必须加显式边界标记。
- 资料很长时：把资料置于前部并配合先引用后作答，以对抗位置偏差。
- 不适用于把它当通用性能杠杆：单段指令、单轮问答上引入标签只增加 token 与解析噪声。
- 不适用于假设标记即安全边界：不可信内容即使被标记包裹，仍可能被当作指令执行。

## 实验台

### file（markdown）

```markdown
同一任务写两版提示，只差边界标记：
  A 版：指令、示例、资料、用户输入连成一段，靠空行分隔
  B 版：四类内容各用固定标签包裹（标签名固定、嵌套规则固定、同一含义只用一个标签）
两版各跑 30 次，记录：结构违规率（输出格式不合契约的次数）、以及「资料里的句子被当成指令执行」的次数。
判据：B 版结构违规率应显著低于 A 版；若两者无差异，说明该模型对此类标记不敏感，须换标记或改用其它隔离手段。
```

预期观察：读者能量出标记带来的消歧收益，也知道这个收益会随模型变化（同一标记在另一模型上可能无差异）。

### shell（bash）

```bash
# 注入探测：把「资料」里放一句伪指令，看模型是否把它当指令执行
# 分别测「裸资料」与「已标注为资料」两种形态，各 20 次，统计被执行的次数
for shape in bare tagged; do
  echo "== shape=$shape =="
  for i in $(seq 1 20); do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"inject-$shape.json" | grep -c 'INJECTED'
  done | sort | uniq -c
done
```

预期观察：标注能降低被执行的次数，但通常不为零——这一步是让读者亲眼看到「标记只消歧、不保安全」，不要把标记当成注入防线。

## 证据

- **官方一手要求把示例包在标签里，以便模型能把示例与指令区分开——这是「边界标记」的直接依据。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Wrap examples in `<example>` tags (multiple examples in `<examples>` tags) so Claude can distinguish them from instructions.
- **「上下文隔离」被列为上下文工程的标准手段之一，与持久化、压缩并列——说明隔离是工程动作而非风格偏好。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **一手安全口径指出模型在架构上不区分「指令」与「数据」，且注入是当前生成式 AI 的固有属性、不存在可靠预防机制——因此标记只能消歧，不能作安全边界。**（S-0032，official）
  - 出处：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/final/LLM01_PromptInjection.md
  - 原文关键句：LLMs make no architectural distinction between "instructions" and "data" ... Prompt injection is intrinsic to current generative AI ... so no reliable prevention mechanism exists today.

## 术语

- **分隔符与上下文隔离（Delimiters and Context Isolation）**：用 XML 标签、专用分节标记等把指令、示例、资料与用户输入在文本上划出边界，使模型能无歧义解析多部分提示。
- **标记敏感度的迁移性（Transferability of Markup Sensitivity）**：对某种标记（如 XML 标签）的响应强度取决于该模型是否针对此类标记做过指令对齐训练，因此同一标记在不同模型上的效果不可假定一致。

## 失效模式

- 把标记当通用性能杠杆：单段指令或单轮问答上加标签只增加 token 与解析噪声，收益为零。
- 标记体系自身失控：标签名不固定、同一含义用多个标签、嵌套规则随人而异，标记于是成为新的歧义源。
- 把标记当安全边界：不可信内容被标签包裹后仍可能被当作指令执行，注入在架构层面并未被挡住。
- 关键资料放在中部：位置偏差会让中部信息被忽略，而标记只解决「这段是什么」，不解决「读者还会不会看它」。

## 一句话小结

用固定的标记体系划清指令与数据的边界，并知道它只消歧、不保安全。

## 在本站知识结构中的位置

- 前置：PE-F-02
- 后继：PE-F-04
