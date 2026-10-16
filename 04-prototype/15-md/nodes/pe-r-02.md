# 范式反转：推理模型上经典技巧掉分（Paradigm Reversal: Classic Techniques Lose Ground on Reasoning Models）

- 节点标识：PE-R-02
- 英文名：Paradigm Reversal: Classic Techniques Lose Ground on Reasoning Models
- 所属分组：G02 推理增强
- 依赖深度：第 7 层
- 内容状态：内容已写满
- 标签：推理增强、范式反转、思维链、适用边界

## 为什么需要它

这是本教程要讲清的第一条被证伪的技巧形态：在具备原生思考的推理模型上，手写「一步一步思考」式思维链与堆砌示例不仅收益趋零，还可能降低指令遵循能力并显著推高延迟与 token。它值得单独立节点，是因为教程生态普遍仍按 2023 年口径正面呈现 CoT，读者按目录学习就会学到过期结论。

**适用边界**

该判定只在推理模型加高串行深度已被底座内化的任务上成立，不能外推到非推理模型，也不能外推到数学与代码这类高串行深度任务。

## 机制说明

反转的机制来自分工变化：推理模型把多步推导内化进底座，思考深度由模型按需分配，外部再写一遍步骤既重复又可能与内部策略冲突，表现为指令遵循下降、延迟与 token 上升。三源独立同向：两家厂商官方建议推理模型上避免思维链提示；学术侧测得推理模型上 CoT 增益仅 2.9% 至 3.1%，Gemini Flash 2.5 为负 3.3%，耗时增加 20% 至 80%。工程上的推论是把判据落在任务属性而非写法上：先量该任务在目标模型上的串行深度是否已被底座内化，再决定提示里要不要保留步骤；模型换代后内化范围会扩大，同一份提示需要重新量一次。

## 何时该用 / 何时不该用

- 使用具备原生思考的推理模型时：不要再手写思维链步骤，改用一般性指令并让模型自行分配思考深度。
- 任务是浅层分类、抽取或格式化时：显式推理步骤纯属浪费，延迟与 token 都会上升。
- 不适用于非推理模型：这类模型上显式思维链仍有明确收益，属另一条路径。
- 不适用于高串行深度任务：GSM8K 与 MATH 这类任务上 CoT 仍有大幅增益，须按任务域判断。
- 不适用于把「未被厂商文档收录」当成「已被证伪」：缺席证据与反证是两种判定，不得混用。

## 实验台

### prompt（markdown）

```markdown
【对照 A（经典形态）】
你是一个严谨的逻辑学家。请一步一步思考，把每一步推导列出来，最后给出结论。
问题：{q}

【对照 B（现行形态）】
给出结论，并说明你依据的关键事实。
问题：{q}
```

预期观察：在推理模型上，B 的准确率不应低于 A，而 A 的输出 token 与延迟应显著更高；在非推理模型上，A 通常优于 B。若结果与上述方向相反，说明该模型或该任务不属于本节点所限定的边界。

### file（markdown）

```markdown
记录表：模型名 / 模型类别（推理或非推理）/ 任务串行深度（浅层或高深度）/ 形态（A 或 B）/ 准确率 / 输出 token / 延迟
判据：本节点的判定只在「推理模型 + 高串行深度已被底座内化」的格子里成立；其余格子应分别记录，不得合并成一个平均值。
```

预期观察：读者得到一张按模型类别与串行深度分格的对照表，能自己复述适用边界，而不是记住一句结论。

## 证据

- **推理模型上思维链提示的增益仅边际（o3-mini 2.9%、o4-mini 3.1%），而 Gemini Flash 2.5 上为负 3.3%，同时耗时增加 20% 至 80%；边界是 GPQA Diamond 198 题、每条件 25 次重复，非推理模型上 CoT 仍有小增益。**（S-0035，paper）
  - 出处：https://arxiv.org/abs/2506.07142
  - 原文关键句：For models designed with explicit reasoning capabilities, CoT prompting often results in only marginal, if any, gains in answer accuracy. However, it significantly increases the time and tokens …
- **官方明确建议避免思维链提示：推理模型内部已执行推理，因此要求「一步一步思考」或「解释你的推理」既不必要，且可能不但无益反而有害。**（S-0010，official）
  - 出处：https://developers.openai.com/api/docs/guides/reasoning-best-practices
  - 原文关键句：These models perform best with straightforward prompts. Some prompt engineering techniques, like instructing the model to "think step by step," may not enhance performance (and can sometimes hinder …
- **官方现行口径把偏好一般性指令而非规定性步骤写成原则，并把手写思维链降级为思考关闭时的兜底；在部分新模型上要求模型写出推理内容可能被拒绝。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Prefer general instructions over prescriptive steps. A prompt like "think thoroughly" often produces better reasoning than a hand-written step-by-step plan. ... Manual chain-of-thought (CoT) …
- **任务域反例：在高串行深度任务（GSM8K、MATH）上 CoT 相对无 CoT 有 54 至 68 个百分点的恢复差，浅层任务上结构性冗余，代码任务上随模型规模符号翻转；该结论来自单作者预印本，样本为三个 7B 至 32B instruct 模型。**（S-0039，paper）
  - 出处：https://arxiv.org/abs/2608.09942
  - 原文关键句：On high-depth P-complete tasks (GSM8K, MATH), CoT gives a +54 to +68 pp recovery gap across all models. On shallow TC^0 tasks (MMLU, ARC), CoT is structurally redundant (Delta in [0.0, +4.6] pp). …
- **可恢复性反例：经验证器强化学习训练的推理模型上少样本思维链常劣于直接作答且增加示例持续降准，但把示例转成显式要点后可重新获益（AIME'25 上 GPT-4.1 提升 14.0 个百分点）——故「有害」是默认用法的结果，不是示例本身无用。**（S-0038，paper）
  - 出处：https://arxiv.org/abs/2509.23196
  - 原文关键句：Recent reasoning LLMs (RLMs), especially those trained with verifier-based reinforcement learning, often perform worse with few-shot CoT than with direct answering. ... adding more exemplars …
- **第三家厂商交叉验证：新一代模型自动生成内部思考文本，通常不需要让模型在返回内容里再概述、规划或详述推理步骤；并建议避免不必要的说服性语言。**（S-0018，official）
  - 出处：https://ai.google.dev/gemini-api/docs/prompting-strategies
  - 原文关键句：Gemini 2.5 and 3 series models automatically generate internal "thinking" text ... it's generally not necessary to have the model outline, plan, or detail reasoning steps in the returned response …

## 术语

- **思维链（Chain-of-Thought, CoT）**：引导模型先写出中间推理步骤再给答案的技巧；在具备原生思考的推理模型上其边际收益趋零甚至为负，在非推理模型与高串行深度任务上仍有效。
- **范式反转（Paradigm Reversal）**：同一技巧在新一代模型上由增益转为无增益或负增益的现象；判定须限定任务域与模型类别，不可外推为普遍规律。
- **串行深度（Serial Depth）**：任务解题所需的串行推理步数；它是判断 CoT 是否有用的可证伪变量——高串行深度任务上 CoT 仍有大幅增益，浅层任务上则结构性冗余。
- **少样本提示（Few-shot Prompting）**：在提示中给出若干输入输出示例以约束格式、语气与歧义消解；现行口径为少量、多样、结构化，并反对穷举边界案例。
- **未证实与已证伪之别（Unevidenced vs. Falsified）**：「未被现行厂商实践或权威来源收录」只是证据缺席，「已被反证推翻」才有反证；两者判定不同，混用会让读者把未证实当成已证伪。

## 失效模式

- 把经典技巧整条搬到推理模型上：思维链与示例堆砌会同时推高成本与延迟，并可能降低指令遵循能力。
- 把「未被厂商文档收录」写成「已被证伪」：缺席证据与反证是两种判定，混用会让读者把未证实当成已证伪。
- 把单一任务域的结论外推为普遍规律：反例已证明 CoT 的符号随任务串行深度与模型规模变化。
- 在多轮对话中改写含思考内容的历史：现行模型要求原样追加，编辑会导致报错或思考块被丢弃。

## 一句话小结

在推理模型加高串行深度已被内化的任务上，手写思维链与堆砌示例边际收益趋零或为负。

## 在本站知识结构中的位置

- 前置：PE-R-01
- 后继：PE-R-03
