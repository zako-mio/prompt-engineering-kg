# 当前共识与争议（Current Consensus and Disputes）

- 节点标识：PE-N-02
- 英文名：Current Consensus and Disputes
- 所属分组：GD-N 新一代模块
- 依赖深度：第 27 层
- 内容状态：内容已写满
- 标签：新一代模块、共识、争议

## 为什么需要它

把「已达成共识」与「仍有争议」分开写，是为了避免读者把争议项当结论使用。本节点是本站内容纪律最集中的地方：每条争议都要写出各方证据与适用边界，并明确区分「未被厂商文档收录」与「已被反证推翻」两种判定。

**适用边界**

争议的裁定需要证据积累与时间，本节点只登记现状而不做裁定；读者应按自己的任务域做小规模实测后再决策。

## 机制说明

当前共识有两条：其一，模型越强，越应减少手写步骤与堆砌示例，把工程重心移到上下文与信息的组织治理；其二，指令层级作为权限关系已被底座部分内化，但仍不足以让应用层放弃自身防御。争议集中在三处：范式反转的适用范围（任务域反例证明思维链的符号随串行深度与模型规模变化）。另两处是自动编译与微调的性价比临界点（唯一直接对照实验的结论是二者互补而非替代，未给出成本临界点）、以及原生推理与外部编排的分工（分层自治是倾向性判断，缺少权威裁定）。三条争议的共同处理方式是按任务域与模型类别分别表述，并在自己环境里实测。

## 何时该用 / 何时不该用

- 引用某条技术结论前：先确认它属于共识还是争议项。
- 做技术选型时：对争议项按自己的任务域做小规模实测再决策。
- 不适用于把争议项当结论使用：会重复社区清单「把未证实当已证伪」的错误。
- 不适用于要求本模块给出裁定：裁定需要证据积累与时间，本模块只登记现状。

## 实验台

### prompt（markdown）

```markdown
# 两版提示（同一批样本各跑多次，只改推理指引这一处）

## 变体 A：显式思维链
你是一个逐步骤推理的解题器。先写出推理步骤，再给出最终答案。只输出 JSON，不要输出其他文字：
{"answer": "<最终答案>", "step_count": <你写出的步骤数>}

## 变体 B：一般性指令
你是一个解题器。直接给出最终答案。只输出 JSON，不要输出其他文字：
{"answer": "<最终答案>", "step_count": <你的输出中包含的步骤数>}

## 两版共用的输入封装
{"task_id": "<样本编号>", "depth": "high | shallow", "question": "<题面>"}

统计口径：按 depth 分组，各组分别报准确率、输出 token 中位数与延迟中位数。
```

预期观察：变体 A 与变体 B 对同一条输入都只返回一个 JSON 对象，且都含 answer 与 step_count 两个键；任一版返回非 JSON 或键缺失即判该样本失败，按 depth 分组后两组样本数之和等于输入总数。

### file（python）

```python
# compare.py —— 只优化提示 vs 交替优化权重与提示
a = {"accuracy": 0.71}
b = {"accuracy": 0.78}
# 换成自己跑出的两份报告：json.load(open("joint-probe/prompt_only.json"))
#                     json.load(open("joint-probe/joint.json"))
delta = round(b["accuracy"] - a["accuracy"], 4)
print({"prompt_only": a["accuracy"], "joint": b["accuracy"], "delta": delta})
```

预期观察：输出一行字典，键恰为 prompt_only、joint、delta 三个，且 delta 等于 joint 减 prompt_only（保留 4 位小数）；delta 为正说明联合优化在该任务域更优，接近 0 或为负说明互补性未在该域体现。

## 证据

- **对具备显式推理能力的模型，思维链提示往往只带来边际甚至零准确率增益。**（S-0035，paper）
  - 出处：https://arxiv.org/abs/2506.07142
  - 原文关键句：For models designed with explicit reasoning capabilities, CoT prompting often results in only marginal, if any, gains in answer accuracy.
- **思维链的增益随任务串行深度变化：深任务增益大，浅任务上属于结构性冗余。**（S-0039，paper）
  - 出处：https://arxiv.org/abs/2608.09942
  - 原文关键句：On high-depth P-complete tasks (GSM8K, MATH), CoT gives a +54 to +68 pp recovery gap across all models. ... On shallow TC^0 tasks (MMLU, ARC), CoT is structurally redundant
- **把权重与提示一起优化优于只优化任一侧，二者的关系是互补而非替代。**（S-0048，paper）
  - 出处：https://arxiv.org/abs/2407.10930
  - 原文关键句：these BetterTogether strategies optimizing the weights and prompts of a pipeline together outperform directly optimizing weights alone and prompts alone by up to 60% and 6%, respectively

## 术语

- **未证实与已证伪之别（Unevidenced vs. Falsified）**：「未被现行厂商实践或权威来源收录」只是证据缺席，「已被反证推翻」才有反证；两者判定不同，混用会让读者把未证实当成已证伪。
- **范式反转（Paradigm Reversal）**：同一技巧在新一代模型上由增益转为无增益或负增益的现象；判定须限定任务域与模型类别，不可外推为普遍规律。

## 失效模式

- 把争议项当结论使用：社区清单常把尚未被厂商文档收录写成已被推翻，据此删掉仍然有效的技巧会直接损失准确率。
- 拿单作者预印本或厂商自述当中立证据：跨任务域外推后方向可能相反，据此做的选型会在自己的域上失效。
- 只报平均分而不按任务串行深度分层：思维链的增益被平均掉，看起来没用，深任务上的实际增益被掩盖。
- 把自动编译当成微调的替代：唯一的直接对照实验结论是二者互补，按替代做会同时丢掉两侧收益，并且成本更高。

## 一句话小结

共识与争议分开登记，争议项按任务域实测，且不混淆未证实与已证伪。

## 在本站知识结构中的位置

- 前置：PE-N-01
- 后继：PE-N-03
