# 校验与修复回路（Validation and Repair Loop）

- 节点标识：PE-S-05
- 英文名：Validation and Repair Loop
- 所属分组：G01 确定性输出
- 依赖深度：第 10 层
- 内容状态：内容已写满
- 标签：确定性输出、校验、重试

## 为什么需要它

模型给出坏结构不是偶发故障，而是当前生成方式下的固有概率：字段类型写错、枚举值越界、必填项留空、引用不存在的 id。校验与修复回路把这类失败当作常规分支处理，即生成、用 schema 与业务规则校验、把具体错误回喂、重新生成，直到通过或触顶。没有这条回路，每一次坏输出都要靠人工发现与人工重跑，成本随调用量线性增长，而失败样本也无法被计数与归类。

**适用边界**

修复回路的成本模型划定了它的适用范围：每次重试都要重跑一次生成，因此它只适用于单次生成成本可控、且失败可被校验器表达的场景。若一次生成代价极高，例如长上下文的大模型整段重跑，事后修复会成倍放大成本，此时应优先在生成期约束（约束解码或 API 侧严格 schema），把结构层面的失败直接消除；若失败根因是指令歧义或资料缺失，错误回灌只会重复同一次失败，应回到提示词或检索侧解决。合规与安全类要求也不适合放进这条回路，它们需要确定性判定而不是概率重试。

## 机制说明

一条可用的修复回路由四个部件构成。其一是校验器，既做结构校验（JSON 是否合法、字段类型与必填项、是否出现额外属性），也做业务规则校验（枚举取值、引用是否存在、数值区间）。其二是错误回灌，把校验器的错误信息重新作为输入的一部分送回去，并且必须具体到位置与期望值：只回一句「JSON 非法」几乎不改变下一次采样的结果，而「第 3 个字段 type 应为 integer，实际是 string」把待修正的自由度收窄到一个点上。其三是重试策略，包括次数上限、是否更换提示变体、以及触顶后的兜底动作；上限必须显式设定，否则预算会在无收敛的循环里被烧掉，故障也被延迟暴露。其四是可观测指标，至少要区分首次通过率与最终通过率：前者反映提示词与 schema 的质量，后者反映回路的效率，两者混在一起看会掩盖真正的瓶颈。工程上还有两条经验：校验器写成与模型无关的纯函数，换模型时不必重写；错误信息按结构化的字段路径组织，回灌时逐条列出而不是拼成散文。外部工具链已经把这条回路产品化：promptfoo 把 is-json 这类结构断言做成可声明、可取反的评测项，instructor 在 API 侧提供 schema 校验与重试层，outlines 与 xgrammar 则把结构层面的同类问题前移到生成期解决。

## 何时该用 / 何时不该用

- 输出要进入下游系统且失败可被机器判定时：为解析与校验失败建显式回路，并把失败样本计数留档。
- 校验规则稳定且与模型无关时：把校验器写成纯函数，错误信息带字段路径与期望值，便于换模型复用。
- 不适用于单次生成代价极高的场景：长上下文整段重跑时，应优先用约束解码或严格 schema 在生成期消除结构失败。
- 不适用于把重试当万能药：失败根因在指令歧义或资料缺失时，应先修提示词或检索，而不是加大重试次数。

## 实验台

### file（python）

```python
import json, jsonschema

MAX_TRIES = 3

def validate(raw, schema):
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"JSON 非法：第 {e.lineno} 行第 {e.colno} 列，{e.msg}"
    errs = [f"{'/'.join(map(str, p.absolute_path)) or '<root>'}：{p.message}"
            for p in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
    return (obj, "") if not errs else (None, "\n".join(errs))

def repair_loop(call_model, prompt, schema, max_tries=MAX_TRIES):
    errs = ""
    for attempt in range(1, max_tries + 1):
        ask = prompt if not errs else (
            f"{prompt}\n\n上次输出被校验器拒绝，错误如下：\n{errs}\n"
            "请只修正这些问题后重新输出完整 JSON。")
        obj, errs = validate(call_model(ask), schema)
        if obj is not None:
            return obj, attempt          # attempt = 重试次数 + 1
    raise RuntimeError(f"修复回路触顶：{max_tries} 次仍未通过；最后一次错误：{errs}")
```

预期观察：首次即通过时返回 attempt=1；把某个字段的值改成字符串后，errs 应给出该字段的路径与期望类型，而不是笼统的「格式错误」；连续失败达到上限时抛出异常并计数，不得无限重试。

### file（markdown）

```markdown
回路指标记录表（每次请求一行）
列：请求 id / 首次是否通过 / 重试次数 / 最后一次错误类型（结构 / 语义）/ 最终是否通过
派生指标：首次通过率 = 首次通过数 ÷ 请求数；修复成功率 = 重试后通过数 ÷ 首次失败数；平均重试次数 = 重试次数总和 ÷ 请求数
纪律：触顶样本逐条留档并归类到具体错误类型，不得只统计最终通过率。
```

预期观察：能区分首次通过率与最终通过率，并据此判断瓶颈在提示词与 schema 侧还是在回路效率侧；触顶样本可被归因到具体错误类型。

## 证据

- **外部工具链把「输出是否合法」做成了声明式断言：promptfoo 的确定性评测项里直接含 is-json 这类结构断言，且断言可用 not- 取反，使校验步骤能在评测与 CI 里机械执行。**（S-0077，official）
  - 出处：https://www.promptfoo.dev/docs/configuration/expected-outputs/
  - 原文关键句：Deterministic eval metrics: equals / contains / icontains / regex / is-json / javascript / python / webhook ... Every test type can be negated by prepending `not-`
- **结构正确性可以在生成期由约束解码保证（XGrammar 自述约束解码可保证 100% 结构正确，且已是多数推理引擎的默认结构化生成后端），说明结构层面的失败并非只能靠事后修复。**（S-0093，official）
  - 出处：https://pypi.org/pypi/xgrammar/0.1.33/json
  - 原文关键句：It leverages constrained decoding to ensure 100% structural correctness ... It is the default structured generation backend for most LLM inference engines
- **「生成→反馈→再生成」这条自我修正路线已被主流教程目录收为独立技术条目（Reflexion），说明在生态里它是被承认的标准做法而非异常处理。**（S-0066，community）
  - 出处：https://www.promptingguide.ai/
  - 原文关键句：Prompting Techniques → Zero-shot / Few-shot / CoT / Meta Prompting / Self-Consistency / Prompt Chaining / ToT / RAG / ... / ReAct / Reflexion / Multimodal CoT / Graph Prompting

## 术语

- **校验与修复回路（Validation and Repair Loop）**：对模型输出做结构或语义校验，失败则把校验错误回灌给模型重试，直至通过或达到重试上限；工程上必须显式设定重试上限，并区分首次通过率与最终通过率。
- **结构化输出（Structured Output）**：以 JSON Schema 等模式约束模型输出结构的机制；API 侧的严格模式通常要求全部字段必填且禁止额外属性，因此它能消除结构失败，但不判断字段取值是否正确。
- **三档严格度（Three Tiers of Strictness）**：按约束强度区分的三档做法：自然语言格式要求、模式提示（仅提示结构）、约束解码或 API 级 schema 保证；档位越高，留给修复回路的结构失败越少，回路主要面向语义失败。

## 失效模式

- 错误回灌过于笼统：只把「JSON 非法」贴回去，模型只能在同一个自由空间里重新采样，修复成功率接近单次通过率。
- 重试没有上限：失败样本反复消耗预算，故障被延迟到账单或下游系统才暴露。
- 只统计最终通过率：提示词与 schema 的退化被回路的重试掩盖，直到平均重试次数与延迟一起上升才被察觉。
- 把无法被校验器表达的失败也塞进回路：指令歧义或资料缺失导致的错误不会被错误信息修正，重试只是把同一次失败重复一遍。

## 一句话小结

修复回路的价值不在于多试几次，而在于把「坏结构」从异常降级为可计数、可收敛的常规分支。

## 在本站知识结构中的位置

- 前置：PE-S-04
- 后继：无
