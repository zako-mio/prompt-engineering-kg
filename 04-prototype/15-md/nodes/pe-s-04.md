# 格式选型与词元效率（Format Choice and Token Efficiency）

- 节点标识：PE-S-04
- 英文名：Format Choice and Token Efficiency
- 所属分组：G01 确定性输出
- 依赖深度：第 9 层
- 内容状态：内容已写满
- 标签：确定性输出、token 效率、格式选型

## 为什么需要它

同一份信息换一种承载格式，输出 token 数可以相差两三成：JSON 的引号、括号与逐条重复的字段名最贵，CSV 与 TSV 最省却要处理转义，YAML 靠缩进表达层级而模型对缩进的容错并不好。输出 token 的单价通常高于输入，长列表与批量任务会把这层差异放大成真实账单。所以格式选型首先是成本与稳定性的工程决策，不是排版偏好。

**适用边界**

本节点只处理同一份信息在多种承载格式之间的取舍，不覆盖约束解码、API 侧 schema 保证与修复回路本身；当下游解析器固定、该格式已通过回归评测时，继续更换格式的收益通常小于重测与回归的成本。

## 机制说明

格式选型的机制可以拆成三件事。其一是冗余度：JSON 用引号、括号与逐条重复的字段名换取自描述，Markdown 表与 CSV 用一行表头，TSV 只用一个制表符，同一批数据从 JSON 换到 TSV 常常省下两三成 token，代价是值里出现分隔符时必须有转义约定。其二是模型熟悉度：格式在训练分布里的常见程度决定模型一次写对的概率，越冷僻的格式越容易在长输出里漂移。其三是解析路径与缓存：下游要机器解析时，结构合法性应交给 schema 而不是自然语言描述；而格式一旦改动，缓存前缀随即失效，输入侧成本会反向上升。选型因此按三条判据落地——下游是否机器解析、模型对该格式是否熟悉、以及该格式能否与缓存前缀长期共存；三个判据都过之后再比 token 数，顺序颠倒会把省下的 token 换成解析失败。

## 何时该用 / 何时不该用

- 下游要机器解析时：先用 schema 或严格结构化输出把结构合法性固定下来，再在同一契约内比较各候选格式的 token 开销。
- 长列表与批量任务：优先逐行一条记录的形态或表头加分隔符的表格，让字段名只出现一次，避免逐条重复字段名。
- 不适用于只盯着 token 数选型：省下的 token 若变成解析失败率与重试次数，总成本反而更高。
- 不适用于把格式一次定死：换模型、换解析器或调整缓存前缀后，模型熟悉度与解析容错都会变，必须重测。

## 实验台

### shell（bash）

```bash
# 同一批 50 条记录，分别序列化成紧凑 JSON / 逐行 JSON / TSV，逐一量 token
python3 - <<'PY'
import json
try:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    n = lambda s: len(enc.encode(s))
except ImportError:
    n = len  # 未装 tiktoken 时退化为字符数，只看相对差距
rows = [{"id": i, "name": f"item-{i}", "qty": i % 7, "note": "n/a"} for i in range(50)]
compact = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
lines = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows)
tsv = "id\tname\tqty\tnote\n" + "\n".join(f"{r['id']}\t{r['name']}\t{r['qty']}\t{r['note']}" for r in rows)
for k, v in [("compact-json", compact), ("lines-json", lines), ("tsv", tsv)]:
    print(k, n(v))
PY
```

预期观察：紧凑 JSON 与 TSV 的 token 数差距通常落在两成到五成的区间；逐行 JSON 因每行重复字段名而比紧凑 JSON 贵，换来的是可逐条流式解析与部分成功。换一批自己的真实数据重跑，差距会随字段名长度与值的分布变化。

### file（markdown）

```markdown
选型记录表：每个候选格式一行，逐列填实测值
  格式 | 实测 token（同一批数据） | 下游解析器 | 解析失败率 | 长输出的格式走样率 | 是否破坏缓存前缀
判据：token 最省的一行只有在该格式的失败率与走样率都可接受时才可选用；
若最省格式的失败率明显更高，就退回次省格式，并把差额记进成本预算。
```

预期观察：读者能拿出「token 数 × 解析失败率」并排的记录再下结论，而不是只报一个更小的 token 数；结论可被他人按同一张表复核。

## 证据

- **删掉重复指令与示例、简化工具描述能同时改善任务表现与 token 效率（官方内部编码 agent 评测：分数升约 10–15%，token 降 41–66%，成本降 33–67%），一般化规则是每条指令只写一次——这说明冗余标记是真实且可量化的成本。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Removing repeated instructions and examples and simplifying tool descriptions can improve task performance and token efficiency. ... State each instruction once.
- **XML 标签被官方点名为「让模型在多部分提示下无歧义解析」的手段，说明格式取舍要按模型能否稳定解析来定，而不是只按字符数多少来定。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs.
- **下游要机器解析时，结构合法性由 json_schema 加 strict 的模式契约承担（additionalProperties 显式置 false），而不是靠自然语言叮嘱模型「请输出合法 JSON」。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }
- **格式与约束本身要付性能代价：格式限制会显著降低推理能力，且约束越严退化越大 ⇒ 更省 token 的强格式并不自动等于更好，选型必须把质量一起计入。**（S-0053，paper）
  - 出处：https://arxiv.org/abs/2408.02442
  - 原文关键句：we observe a significant decline in LLMs reasoning abilities under format restrictions. ... stricter format constraints generally lead to greater performance degradation in reasoning tasks.

## 术语

- **约束解码（Constrained Decoding）**：在采样阶段按文法或 schema 屏蔽不合法的 token 路径，使输出在结构上必然合法；可由推理引擎或库实现，也可由 API 侧保证。
- **结构化输出（Structured Output）**：以 JSON Schema 等模式约束模型输出结构的机制；API 侧的严格模式通常要求全部字段必填且禁止额外属性。
- **三档严格度（Three Tiers of Strictness）**：按约束强度区分的三档做法：自然语言格式要求、模式提示（仅提示结构）、约束解码或 API 级 schema 保证。

## 失效模式

- 把 JSON 当默认输出格式：引号、括号与逐条重复的字段名在长列表里最贵，账单上涨而信息量不变。
- 为省 token 手搓短标记格式：下游解析器跟不上或值里带分隔符，省下的 token 变成解析失败与重试。
- 用 YAML 缩进承载层级：模型在长输出里容易缩进错位，解析器直接报错，输出越长越容易崩。
- 改格式时顺手动了缓存前缀：前缀里任何字符变化都会让它失效，输入侧成本上升把输出侧的节省吃掉。

## 一句话小结

格式选型按三条判据落地：下游是否机器解析、模型对该格式是否熟悉、以及格式变更会不会毁掉缓存前缀；省下的 token 一旦变成解析失败，就应退回次省的那种格式。

## 在本站知识结构中的位置

- 前置：PE-S-03
- 后继：PE-S-05
