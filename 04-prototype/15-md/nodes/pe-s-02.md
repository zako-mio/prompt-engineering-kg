# 三档严格度（Three Tiers of Strictness）

- 节点标识：PE-S-02
- 英文名：Three Tiers of Strictness
- 所属分组：G01 确定性输出
- 依赖深度：第 7 层
- 内容状态：内容已写满
- 标签：确定性输出、严格度、格式约束

## 为什么需要它

模型不会因为你在提示里写了一句「只输出 JSON」就真的只输出 JSON：自然语言格式要求只是倾向，不是保证。把约束强度分成三档——自然语言格式要求、把结构契约（JSON Schema 或 JSON mode）写进调用、以及在生成期屏蔽非法 token 的约束解码——格式可靠性才从一个靠运气的问题变成一个可选的工程参数。分档的用处是按下游能不能容错来选档：下游是人看、坏了重跑一次没代价，用最松的一档就够；下游是无人值守的流水线、一次结构失败就要人工介入，才值得付最紧一档的代价。

**适用边界**

档位要按后果定、不是按偏好定：约束越强，生成空间越窄，在需要多步自由推理的任务上会压低推理表现，此时最高档往往不是最优解而是两阶段拆分；反过来，在无人值守的下游，最松的一档等于没有约束，必须自己补上校验与重试。

## 机制说明

三档的机制差别在于约束发生在哪一层。第一档是自然语言格式要求：指令留在提示里（如「只输出 JSON，不要解释」），模型只是在概率上倾向于照做，输出仍需后置解析，失败率随任务复杂度上升。第二档是结构契约：把 JSON Schema 放进请求（JSON mode 或 response_format 一类参数），模型按模式生成字段，结构由生成侧的检查兜住，但模式是否被完全遵守仍取决于实现，字段缺失或多余字段依旧可能出现。第三档是约束解码：在采样的每一步按文法或 schema 屏蔽掉不合法的 token 路径，非法结构在生成期就不可达，结构失败率随之趋零，代价是生成空间变窄、并依赖具体 provider 或推理引擎的实现。三档的强度与成本、可移植性大致成反比：越严越可靠，也越贵、越难跨 provider 迁移，越可能压掉推理质量。

## 何时该用 / 何时不该用

- 无人值守的生产流水线：用第三档，并把结构失败从监控项里移除。
- 一次性脚本、人工查看的输出：可用第一档，但必须有人工或后置校验兜底。
- 不适用于一刀切选最高档：推理密集型任务上强约束会压低推理表现，该拆成两阶段。
- 不适用于只升档不配失败处理：档位与重试策略必须成对定义、一起评审。

## 实验台

### prompt（markdown）

```markdown
【第一档：自然语言格式要求】
把下面这句话的情感标为正向或负向，只输出 JSON：{"sentiment": "..."}
句子：{q}

【第二档：结构契约】
按给定的 JSON Schema 输出（sentiment 为必填 string 字段），不要输出任何解释文字。
句子：{q}

【第三档：约束解码或严格模式】
同一请求改用严格结构化输出参数（如 strict: true 与 additionalProperties: false），schema 同上。
句子：{q}
```

预期观察：同一批输入上结构失败率应呈阶梯下降：第一档明显大于零、第二档接近零但仍有字段级偏差、第三档为 0。若第三档仍出现非法 JSON，说明该 provider 的严格模式并未在解码期生效，须换实现，或降档并补上重试。

### file（markdown）

```markdown
记录表：档位 / provider 与模型 / 结构失败率 / 语义正确率 / 输出 token 与延迟 / 是否配了重试兜底
判据：结构失败率只应随档位上升而下降，语义正确率则可能在最高档下降，两列必须同表记录，不得只看结构通过率。
迁移检查：把同一 schema 换到另一家 provider 重跑，失败率回升即说明该档位在那里只是提示而非约束。
```

预期观察：读者得到一张按档位与 provider 分格的对照表，能看出结构与语义两条曲线的方向相反，并据此为下游选出够用而不浪费的档位。

## 证据

- **第三档的现行形态是 API 侧严格模式：schema 内显式声明 strict: true 与 additionalProperties: false，把结构合法性从提示层移到解码层。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }
- **严格档有代价且不是越严越好：格式限制本身会降低推理表现，且格式约束越严格退化越大。**（S-0053，paper）
  - 出处：https://arxiv.org/abs/2408.02442
  - 原文关键句：we observe a significant decline in LLMs reasoning abilities under format restrictions. ... stricter format constraints generally lead to greater performance degradation in reasoning tasks.
- **第三档在实现上落在推理引擎或约束解码库一侧，靠屏蔽非法 token 保证结构正确，因此同一档位的可用性随 provider 而异。**（S-0093，official）
  - 出处：https://pypi.org/pypi/xgrammar/0.1.33/json
  - 原文关键句：It leverages constrained decoding to ensure 100% structural correctness ... It is the default structured generation backend for most LLM inference engines

## 术语

- **三档严格度（Three Tiers of Strictness）**：按约束强度区分的三档做法：自然语言格式要求、模式提示（仅提示结构）、约束解码或 API 级 schema 保证；档位越高结构越可靠，代价与迁移难度也越大。
- **约束解码（Constrained Decoding）**：在采样阶段按文法或 schema 屏蔽不合法的 token 路径，使输出在结构上必然合法；可由推理引擎或库实现，也可由 API 侧保证。
- **校验与修复回路（Validation and Repair Loop）**：对模型输出做结构或语义校验，失败则把校验错误回灌给模型重试，直至通过或达到重试上限；它是松档位必须配的兜底件。

## 失效模式

- 把档位当质量旋钮：一路升到最高档，结果在多步推理任务上准确率反而下降，还把实现锁死在少数几家提供严格模式的厂商上。
- 只升档不配失败处理：第三档下把结构校验从监控里删掉，一旦换模型或换 provider，结构失败重新出现却无人发现。
- 把第一档当生产方案：提示里写一句「只输出 JSON」就直连下游解析器，解析异常被记成业务异常，错误记到了错误的账上。
- 把三档当成同一实现的三挡参数：不同 provider 的「严格」含义并不一致，有的只保证合法 JSON、不保证符合 schema，跨 provider 迁移时契约会静默变化。

## 一句话小结

三档严格度的用法是先看下游能不能容错、再决定约束强度，并让档位与失败处理成对定义。

## 在本站知识结构中的位置

- 前置：PE-S-01
- 后继：PE-S-03
