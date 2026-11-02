# 工具定义与滥用治理（Tool Definition and Abuse Governance）

- 节点标识：PE-O-08
- 英文名：Tool Definition and Abuse Governance
- 所属分组：G04 编排
- 依赖深度：第 15 层
- 内容状态：内容已写满
- 标签：编排、工具定义、治理

## 为什么需要它

工具的名称、描述与参数模式本身就是提示词面的一部分，模型靠它们决定调不调、调哪个、怎么调。工具集膨胀会直接诱发误选与滥用，因此工具设计需要治理而不只是实现。治理的最小动作，是让每个工具都能回答「什么时候不该用它」。

**适用边界**

治理的核心是在「能力覆盖」与「选择歧义」之间权衡；在工具数量少、语义清晰时，治理动作的收益有限，应把精力放在描述质量上。

## 机制说明

工具治理包含四个动作：合并（把语义相近的工具合并，减少选择歧义）、命名（用一致且描述性的名称，避免缩写）、描述（写清何时用与何时不用，而不是重复参数说明）、以及权限（把高风险工具与低风险工具分离，并对其调用加确认或校验）。现行官方口径主张精简工具描述：重复的指令与冗长的说明可以删减，且精简后任务表现与 token 效率同时改善。监控侧应记录工具调用分布与误选情况：某个工具几乎不被调用说明描述或场景不匹配，某个工具被高频误用说明与其他工具语义重叠。这些信号是迭代工具定义的主要依据。规范层面给工具定义了两条硬口径：工具由服务端声明并被设计为由模型控制，模型依据上下文与用户提示自行发现并调用，而每个工具必须由唯一名称与描述入参模式的元数据标识；因此工具描述就是模型的选择依据。选择权一旦下放到模型，过度代理的风险随即成立，代理面的大小取决于工具清单与确认点，而非提示词里的劝阻措辞。

## 何时该用 / 何时不该用

- 工具数量增长、模型开始误选时：先做合并与描述澄清，再考虑增加路由。
- 高风险工具（写操作、外部副作用）：加确认或校验，并与其他工具隔离权限。
- 不适用于工具少且语义清晰时的过度治理：收益有限，应先提升描述质量。
- 不适用于只靠描述解决安全问题：工具权限须在系统层收窄，不能只写在提示里。

## 实验台

### prompt（markdown）

```markdown
- name: refund_order
  use_when: 用户给出订单号并明确要求退款
  avoid_when: 用户只询问退款政策，或订单未支付、已退款
  risk: high
  requires_confirm: true
  input_schema: {order_id: string, reason: enum[质量问题, 重复下单, 其他]}
```

预期观察：工具清单中任一工具缺 avoid_when 栏，或 risk 为 high 却缺 requires_confirm: true，即判为工具定义不完整。

### shell（python）

```python
import collections

TOOLS = [
    {"name": "search_docs", "risk": "low"},
    {"name": "read_file", "risk": "low"},
    {"name": "refund_order", "risk": "high", "confirm": True},
    {"name": "search_docs", "risk": "low"},
]
names = [t["name"] for t in TOOLS]
dup = [n for n, c in collections.Counter(names).items() if c > 1]
bare = [t["name"] for t in TOOLS if t["risk"] == "high" and not t.get("confirm")]
print("count=%d dup=%s high_without_confirm=%s" % (len(names), dup, bare))
```

预期观察：输出 dup=['search_docs'] 与 high_without_confirm=[]，据此判定重名工具必须先合并、高风险工具必须带确认点。

## 证据

- **规范明确把工具设计为模型控制：模型依据上下文理解与用户提示自行发现并调用工具，工具定义因此直接成为决策面。**（S-0118，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/server/tools
  - 原文关键句：Tools in MCP are designed to be model-controlled, meaning that the language model can discover and invoke tools automatically based on its contextual understanding and the user’s prompts.
- **规范要求每个工具由唯一名称标识并附上描述其入参模式的元数据，名称与模式构成工具定义可被判读的最小集。**（S-0118，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/server/tools
  - 原文关键句：Each tool is uniquely identified by a name and includes metadata describing its schema.
- **OWASP 指出调用哪个扩展可能被委托给 LLM 代理自行判断，工具选择权下放即扩大代理面。**（S-0119，official）
  - 出处：https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
  - 原文关键句：The decision over which extension to invoke may also be delegated to an LLM ‘agent’ to dynamically determine based on input prompt or LLM output.

## 术语

- **工具定义与滥用治理（Tool Definition and Abuse Governance）**：工具的名称、描述与参数模式构成提示词面的一部分；描述含糊会诱发误用，工具过多会诱发滥用与误选。
- **ReAct（推理—行动交织）**：交替生成思考、动作与观察，使模型在外部工具反馈驱动下推进任务的单 Agent 控制流范式。

## 失效模式

- 工具描述只重复参数说明而不写何时调用：模型靠字面相似度选择工具，误选率随工具数量上升。
- 高风险写操作与只读查询混在同一权限层：一次误选就把本应只读的调用变成不可回滚的副作用。
- 把权限约束只写进提示词：模型可被输入内容诱导而忽略措辞，限制必须落在系统层的确认与白名单上。

## 一句话小结

工具定义就是提示词面：合并语义、写清使用时机、按风险分离权限。

## 在本站知识结构中的位置

- 前置：PE-O-07
- 后继：PE-P-01
