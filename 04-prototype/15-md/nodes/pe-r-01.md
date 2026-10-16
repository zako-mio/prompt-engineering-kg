# 思维链与零样本思维链（Chain-of-Thought and Zero-shot CoT）

- 节点标识：PE-R-01
- 英文名：Chain-of-Thought and Zero-shot CoT
- 所属分组：G02 推理增强
- 依赖深度：第 6 层
- 内容状态：内容已写满
- 标签：推理增强、思维链、自适应思考

## 为什么需要它

思维链是提示词工程史上收益最确定的技巧之一，也是当前最容易被误用的一条：它的价值取决于模型是否已具备原生思考能力，以及任务是否需要多步串行推导。把这两点判断清楚，才能避免在推理模型上白付延迟与 token。

**适用边界**

CoT 的效力由一个门控条件决定：模型是否具备原生思考机制，以及任务是否真需要多步串行推导。在这个门控之外强加显式步骤指令，只换来更长的输出与延迟，答案准确率不会改善。多轮对话还有一条独立的工程约束：含思考块的助手轮次必须原样回传、历史只能追加，任何手工编辑或删改都会触发报错或让该块被丢弃。此外，结构化输出类需求不应靠 CoT 解决，应交给模式约束与校验回路。

## 机制说明

思维链的基本做法是引导模型先输出中间推理步骤再给结论，为逻辑推导留出草稿空间。零样本思维链则只加一句触发语即可生效，无需示例。现行官方口径把它整体降级：偏好一般性指令而非规定性步骤，手写思维链只在思考功能关闭时作为兜底；在部分新模型上要求模型把推理写进标签甚至会被拒绝。同时，多轮对话中的思考内容有工程约束——必须原样回传且历史保持追加式，否则会报错或被丢弃。因此本节点要先判断模型类别与任务串行深度，再决定写不写推理指令，而不是无条件加一句「一步一步思考」。

## 何时该用 / 何时不该用

- 非推理模型上处理多步推导任务：显式引导推理步骤仍有明确收益。
- 推理模型的思考功能被关闭时：手写思维链可作为兜底手段。
- 需要模型展示可信中间过程的场合：显式推理步骤可读、可复核。
- 不适用于推理模型默认开启思考的场景：手写步骤边际收益趋零甚至为负。
- 不适用于多轮对话中改写历史：含思考内容的历史必须原样追加，不得编辑。

## 实验台

### shell（bash）

```bash
# 在**非推理模型**上做最小对照：同一道多步题，零样本直答 vs 零样本 CoT
Q='一个仓库周一入库 120 箱，周二入库 85 箱，周三出库 137 箱，周四入库 96 箱。现在库存 164 箱，问周一之前库存多少箱？先只给答案。'
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"gpt-4.1-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"temperature\":0}"

# 只改一句触发语，其余（模型 / 参数 / 题干）逐字不动
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"gpt-4.1-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"$Q 一步一步思考。\"}],\"temperature\":0}"
```

预期观察：两条命令都返回 200；CoT 那条的 completion_tokens 明显更高，且正文里出现中间步骤（120+85-137+96 之类）。把同一题目跑 20 次统计首次正确率：非推理模型上 CoT 一般高于直答，且在库存这种串联减法任务上差距最明显。若换成推理模型（思考默认开启），同一对照的差距会缩到噪声级（T1a 在 GPQA 类任务上量到 2.9%–3.1% 的边际增益，而耗时增加 20–80%），此时这句触发语只买到延迟。

### prompt（markdown）

```markdown
对照两条提示词，第二条是零样本思维链的标准形态：

【A 直答】把下面的题目直接给出最终数值答案，不要写过程。

【B 零样本 CoT】把下面的题目一步一步思考，写出每一步的中间结果后再给最终数值答案。

两条只在「是否要求中间步骤」上不同，模型、题型、温度、最大输出长度都必须一致，否则对照无效。
题目要选**串行深度高**的多步推导题（多步算术、约束满足、单位与汇率换算是典型），不要选单跳事实题。
```

预期观察：在非推理模型上，B 的首次正确率应高于 A，且差额随题目串行步数增加而扩大。若把同一对提示词搬到推理模型上，差额收敛到噪声级，而输出 token 与延迟明显上升——这正是串行深度与模型类别两个门控变量的实测体现。

## 证据

- **对具备显式推理能力的模型，CoT 提示往往只带来边际甚至为零的准确率增益，却显著增加生成所需的时间与 token——这是范式反转的量化依据。**（S-0035，paper）
  - 出处：https://arxiv.org/abs/2506.07142
  - 原文关键句：For models designed with explicit reasoning capabilities, CoT prompting often results in only marginal, if any, gains in answer accuracy. However, it significantly increases the time and tokens needed
- **官方口径已把手工思维链降级为兜底：模型有原生思考时应当依赖思考，而部分新模型可能直接拒绝「写出推理」的要求。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Manual chain-of-thought (CoT) prompting as a fallback. When thinking is off ... rely on thinking instead ... a prompt that asks the model to write out its reasoning
- **对比评测显示，高性能模型上简单提示常优于更复杂的提示且成本更低；逐步推理这类常用风格并不占优。**（S-0037，paper）
  - 出处：https://arxiv.org/abs/2507.13525
  - 原文关键句：For high-performance LLMs, simple prompts often outperform more complex ones while reducing cost. In contrast, commonly used prompting styles in natural language processing

## 术语

- **思维链（Chain-of-Thought, CoT）**：引导模型先写出中间推理步骤再给答案的技巧；在具备原生思考的推理模型上其边际收益趋零甚至为负，在非推理模型与高串行深度任务上仍有效。
- **零样本思维链（Zero-shot CoT）**：仅以一句触发语（如「一步一步思考」）诱发推理步骤的 CoT 变体，不需要示例。
- **自适应思考（Adaptive Thinking）**：由模型自行决定思考深度的现行机制，取代手动指定思考 token 预算的旧做法；后者在新一代模型上已返回错误。

## 失效模式

- 把「一步一步思考」当万能开关：在思考默认开启的模型上它只抬高 token 与延迟，准确率停在噪声级。
- 在显式推理指令里规定死步骤：官方口径偏好一般性指令，规定性步骤会挤掉模型本可自行展开的更优推理路径。
- 手工编辑含思考块的历史：改写后再次请求会报错或让该块被静默丢弃，长程任务的推理上下文由此断裂且难以定位。
- 只用单跳事实题验证 CoT：串行深度不足的题目本身不需要中间草稿，据此得出「CoT 无效」的结论无法外推。

## 一句话小结

CoT 不是通用加速器：先看模型有没有原生思考、任务串行深度够不够，两个门控都通过才写显式推理指令。

## 在本站知识结构中的位置

- 前置：PE-F-06
- 后继：PE-R-02
