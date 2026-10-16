# 概率采样与确定性边界（Probabilistic Sampling and the Determinism Boundary）

- 节点标识：PE-F-01
- 英文名：Probabilistic Sampling and the Determinism Boundary
- 所属分组：G00 地基：模型是概率采样器
- 依赖深度：第 0 层
- 内容状态：内容已写满
- 标签：地基、采样、确定性、约束解码

## 为什么需要它

如果不先接受「模型是概率采样器」这个事实，后面所有关于格式、评测与迁移的经验都会退化成口诀。工程师最常见的失败是把偶发的好结果当成方法有效，于是把一次演示的成功写法固化成流程。本节点要建立的是判据意识：先问结论在什么条件下可复现，再问怎么写得更好。

**适用边界**

采样随机性只是不确定性的来源之一，模型换代与上下文变化带来的不确定性更大，因此把随机性压到零并不等于结果稳定。

## 机制说明

自回归语言模型在每一步对下一个 token 输出一个概率分布，再从该分布中取样；解码策略（贪心、温度、top-p）只改变取样规则，不改变「输出是分布的一个样本」这一事实。工程上可用的确定性手段有三类：一是约束解码，按文法或 schema 屏蔽非法 token 路径，使结构必然合法；二是结构校验与重试，把失败当作可处理的常规分支；三是固定可固定的一切，包括提示文本、消息顺序、工具定义与采样参数。需要区分两种不同的不确定性：一是采样噪声，可通过降低温度与固定参数压缩；

## 何时该用 / 何时不该用

- 输出要被程序直接消费时：必须叠加约束解码或结构校验，不能只依赖提示词里的格式说明。
- 评测提示词改动时：用多次运行的通过率而非单次结果做判断，并固定除被测变量以外的一切。
- 不适用于把确定性当作唯一目标：需要多样性探索（如候选生成、投票采样）时必须主动引入随机性。
- 不适用于把随机性当作失败借口：结构性错误（字段缺失、格式违规）应通过约束解码消除，而不是归因于随机。

## 实验台

### shell（bash）

```bash
for i in 1 2 3 4 5; do
  curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
    -d '{"model":"<your-model>","messages":[{"role":"user","content":"把这句话的情感标为 POSITIVE 或 NEGATIVE，只输出标签：这个产品完全超出预期"}],"temperature":0}'
  echo
done
```

预期观察：五次输出逐字相同的概率很高但不必定为 100%；把其中一次输出改成要求返回 JSON 后，差异出现频率应上升。这一步的目的是让读者亲眼看到「同一输入、多次运行」的分布。

### file（markdown）

```markdown
记录表：字段 = 运行序号 / 原始输出 / 是否可被解析 / 失败类型（结构失败 / 语义失败）
判据：结构失败率应通过约束解码压到 0；语义失败率只能通过评测集与提示词改动降低。
不得用「这次看起来对了」替代失败率统计。
```

预期观察：读者能区分结构失败与语义失败两类，并知道前者应被机制消除、后者应被度量。

## 证据

- **格式限制会显著降低模型的推理能力，且格式越严格退化越大；结论限于生成空间受限的约束解码与强格式指令，不适用于「先自由推理再格式化」的两阶段模式。**（S-0053，paper）
  - 出处：https://arxiv.org/abs/2408.02442
  - 原文关键句：we observe a significant decline in LLMs reasoning abilities under format restrictions. Furthermore, we find that stricter format constraints generally lead to greater performance degradation in …
- **严格结构化输出的现行契约要求 schema 内显式声明 additionalProperties: false 并列出必填字段，这是把结构合法性从提示层移到解码层的手段。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }
- **官方对提示工程适用范围的边界表述：并非所有成功标准或失败的评测都最适合用提示工程解决，换模型有时能更省力地改善延迟与成本。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.

## 术语

- **概率采样与确定性边界（Probabilistic Sampling and the Determinism Boundary）**：模型逐 token 从概率分布中采样，因此同一输入不保证同一输出；确定性只能在约束解码、结构校验与固定参数等工程手段划出的边界内近似获得。
- **约束解码（Constrained Decoding）**：在采样阶段按文法或 schema 屏蔽不合法的 token 路径，使输出在结构上必然合法；可由推理引擎或库实现，也可由 API 侧保证。
- **结构化输出（Structured Output）**：以 JSON Schema 等模式约束模型输出结构的机制；API 侧的严格模式通常要求全部字段必填且禁止额外属性。

## 失效模式

- 把单次成功当成方法有效：不建评测集就固化写法，换模型或换数据后无声失效。
- 把结构性错误归因于「模型随机」：字段缺失与格式违规本可由约束解码消除，却被当成不可控因素。
- 为追求确定性而把温度压到 0 并以为万事大吉：模型与上下文带来的不确定性不受温度影响。

## 一句话小结

先接受输出是分布的一个样本，再用约束解码与评测集把不确定性拆成可处理的两类。

## 在本站知识结构中的位置

- 前置：无
- 后继：PE-F-02
