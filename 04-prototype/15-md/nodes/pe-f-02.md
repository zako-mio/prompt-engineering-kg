# 系统 / 开发者 / 用户提示词分层（System, Developer, and User Prompt Layering）

- 节点标识：PE-F-02
- 英文名：System, Developer, and User Prompt Layering
- 所属分组：G00 地基：模型是概率采样器
- 依赖深度：第 1 层
- 内容状态：内容已写满
- 标签：地基、提示词分层、缓存

## 为什么需要它

提示词不是一段越写越长的文本，而是按特权与生命周期分层的一组指令。分层之所以必要，是因为不同内容的变更频率与权威性不同：产品级约束几乎不变，任务级指令每次调用都变，用户输入则完全不可信。混在一层会导致每次改一处就要重测全部内容，也无法在安全侧表达「谁说了算」。

**适用边界**

层数由运行时决定，若所用运行时只暴露单层提示，则应至少用分隔符在文本上模拟出分层，而不能因此放弃分层心智。

## 机制说明

系统层承载产品身份、长期约束与安全策略，其特点是稳定、由开发者掌控、可被缓存；开发者层承载任务级指令与输出契约，随调用点变化；用户层承载本次输入，内容不可信。三者之外通常还有工具返回、检索资料与记忆条目，它们与用户输入同属不可信内容，需要显式标注而非与指令混排。分层的两个直接收益是：其一，把稳定前缀与易变后缀分开，使提示缓存可以命中；其二，为指令层级提供工程落点，使「低特权来源不得覆盖高特权来源」这条规则有地方可写。

## 何时该用 / 何时不该用

- 提示中包含长期不变的产品约束时：放进系统层，使缓存可命中且改动面最小。
- 需要表达指令优先级时：用分层承载特权关系，而不是在正文里用大写强调。
- 不适用于把系统层当垃圾桶：把每次调用都变的内容写进系统层会破坏前缀稳定性并推高成本。
- 不适用于假设分层本身即安全：层级只是工程落点，真正的防御还需要权限收窄与输出校验。

## 实验台

### shell（bash）

```bash
# 同一段长前缀，分别用「系统层内容完全不变」与「系统层改一个字」的两种方式调用
# 记录每档的时间与计费字段（缓存命中通常在响应里以 cached_tokens 之类的字段体现）
for variant in stable mutated; do
  echo "== variant=$variant =="
  for i in 1 2 3; do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"payload-$variant.json" | grep -o '"[a-z_]*cached[a-z_]*":[0-9]*'
  done
done
```

预期观察：stable 档从第二次起出现缓存命中字段、延迟明显下降；mutated 档每次都当作全新前缀，命中归零。这一步让读者亲眼看到「系统层的稳定性 = 可缓存性 = 成本」。

### file（markdown）

```markdown
分层记录表：把现有提示逐段剪开，每段填四列
  段内容 | 放在哪一层（系统 / 开发者 / 用户） | 变更频率（几乎不变 / 每次调用 / 完全不可信） | 若放错层的代价
判据：凡是「几乎不变」的内容都应落在系统层且位于前缀；凡是「每次调用都变」的内容都不得进系统层。
不得用「反正模型看得懂」替代分层判断——分层要管的是缓存与权限，不是模型理解力。
```

预期观察：读者能把自己的提示切成三层，并说出每一段为什么在那层，而不是凭感觉排列顺序。

## 证据

- **精简系统层（删掉重复指令与示例、简化工具描述）在内部编码 agent 评测中把分数提高约 10–15%，同时把 token 降 41–66%、成本降 33–67%；其一般化规则是「每条指令只写一次」。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Removing repeated instructions and examples and simplifying tool descriptions can improve task performance and token efficiency. ... State each instruction once.
- **官方口径要求用标签把示例与指令分开，理由是 XML 风格标签能让模型在多部分提示里无歧义解析——这正是「分层要有文本落点」的一手依据。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs.
- **上下文工程的目标被表述为「找到最小的高信噪比 token 集」——支持「系统层不是垃圾桶」这一工程推论。**（S-0004，official）
  - 出处：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：good context engineering means finding the smallest possible set of high-signal tokens

## 术语

- **提示词分层（系统 / 开发者 / 用户）（Prompt Layering）**：把提示词按特权与生命周期拆为系统、开发者、用户三层，各层承担不同的稳定性与权威性职责。
- **提示缓存（Prompt Caching）**：把稳定的提示前缀在服务端缓存复用，以降低重复前缀的延迟与计费成本；要求前缀稳定且顺序固定。

## 失效模式

- 把系统层当垃圾桶：每次调用都变的内容写进系统层会破坏前缀稳定性，缓存全失效，延迟与成本同时上升。
- 只用大写与强调表达优先级：特权关系没有工程落点，安全侧无法表达「谁说了算」，模型只看到更响的语气。
- 把分层当成安全机制：层级只是工程落点，防注入仍须权限收窄与输出校验，分层本身不拦任何东西。
- 三层之外的可信度混同：工具返回、检索资料与记忆条目与用户输入同属不可信内容，不加标注就与指令混排等于放弃边界。

## 一句话小结

按变更频率与权威性把提示词分层，稳定前缀放前、易变内容放后。

## 在本站知识结构中的位置

- 前置：PE-F-01
- 后继：PE-F-03
