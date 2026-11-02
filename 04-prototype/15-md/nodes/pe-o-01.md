# 提示词链（Prompt Chaining）

- 节点标识：PE-O-01
- 英文名：Prompt Chaining
- 所属分组：G04 编排
- 依赖深度：第 8 层
- 内容状态：内容已写满
- 标签：编排、提示词链、流程

## 为什么需要它

提示词链把任务拆成步骤、前一步输出作为后一步输入，好处是每步可检查、可记录、可单独评测。它的定位已经收窄：现行口径只在需要检查中间产物或强制执行特定流程结构时才显式编排，其余场景交给模型内部处理或上层编排。

**适用边界**

硬编码链条对业务数据的轻微波动很敏感，一旦某环输出偏离预期整条链失效，因此需要与校验和兜底分支配套。

## 机制说明

链条的实现要点有三处：步骤边界要按可验证的产出划分（而不是按思考阶段划分）、步骤之间要有契约（输出结构固定）、以及每一步都要有失败处理（校验加分支）。链条的价值主要来自可观测性：中间产物落盘后可被检查、可被回归测试、可被人工介入；代价是延迟与调用次数上升，且错误会沿链传播。现行厂商口径在「默认做法」这一点上已经改变：模型内部能处理的多步推理不再需要外部链条，链条退回到需要固化中间产物的场景。因此判断是否该用链条的判据不是任务是否复杂，而是中间产物是否需要被检查或固化。

## 何时该用 / 何时不该用

- 中间产物需要被检查、记录或人工介入时：显式链条仍有价值。
- 流程需要强制合规顺序时（如先审后发）：链条可固化顺序并留下审计痕迹。
- 不适用于把链条当复杂任务的默认做法：模型内部已能处理多数多步推理。
- 不适用于链条环节无契约：无输出契约的链条在数据波动时整条失效。

## 实验台

### file（python）

```python
import json
import sys

CONTRACT = {
    "extract": {"entities", "source_span"},
    "classify": {"label", "confidence", "rationale"},
}


def check(step, payload):
    need = CONTRACT[step]
    missing = need - set(payload)
    if missing:
        raise ValueError("%s 缺字段 %s" % (step, sorted(missing)))
    if step == "classify" and not 0 <= payload["confidence"] <= 1:
        raise ValueError("%s 的 confidence 越界：%r" % (step, payload["confidence"]))
    return payload


for step in ("extract", "classify"):
    line = sys.stdin.readline()
    if not line.strip():
        sys.exit("%s 收到空输入，链条中止" % step)
    try:
        print(json.dumps(check(step, json.loads(line)), ensure_ascii=False))
    except (ValueError, json.JSONDecodeError) as e:
        sys.exit("%s 契约失败：%s" % (step, e))

```

预期观察：标准输入逐行喂入一条 JSON 时逐行回显通过校验的对象；缺字段、confidence 越界或空行时以非 0 退出码结束并打印出错步骤名。

### prompt（markdown）

```markdown
你是链条第 2 步「分类」，只消费上一步 JSON 的 entities 与 source_span，不重读原文。

输入：{{step1_json}}

输出规则：
只输出一个 JSON 对象，键固定为 label、confidence、rationale。
label 必须是 违规、正常、存疑 三者之一。
confidence 是 0 到 1 之间的浮点数。
rationale 不超过 60 字，且必须引用 source_span 里的一段原文。

输入缺 entities 时，只输出 {"label": "存疑", "confidence": 0, "rationale": "缺少 entities"} 并停止。
```

预期观察：输入缺 entities 时输出恰为 label 等于存疑且 confidence 等于 0 的 JSON 对象；正常输入时输出只含 label、confidence、rationale 三个键，不附带任何解释段落。

## 证据

- **官方把工作流定义为由预定义代码路径编排，并把 agent 与之对立，因此链条的步骤顺序由代码固定，而不是由模型临场决定。**（S-0005，official）
  - 出处：https://www.anthropic.com/engineering/building-effective-agents
  - 原文关键句：Workflows are systems where LLMs and tools are orchestrated through predefined code paths. Agents ... are systems where LLMs dynamically direct their own processes
- **厂商现行口径认为自适应思考与子 Agent 编排已接管多数多步推理，显式提示词链只在需要检查中间输出时才保留价值。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：With adaptive thinking and subagent orchestration, Claude handles most multistep reasoning internally. Explicit prompt chaining ... is still useful when you need to inspect intermediate outputs.
- **步骤之间的输出契约可以直接落实为 strict 的 json_schema 响应格式，使中间产物被机器校验而不是靠人眼读。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }

## 术语

- **提示词链（Prompt Chaining）**：把任务拆为若干步骤、前一步输出作为后一步输入的固定流程编排；现行定位收窄为「需要检查或固化中间产物时」的选项。

## 失效模式

- 按思考阶段而不是按可验证产出切步骤：每一步都无法单独断言成败，链条失败时只能整条重跑，排障与调用成本一起翻倍。
- 步骤之间没有输出契约：上游少一个字段就一路传到底，到末步才暴露，返工要把整条链的费用再付一次。
- 校验只放在链尾而不放在每步之后：错误在第 2 步引入、第 5 步才暴露，定位只能靠人工回放整段上下文。
- 链条环节数超过实际需要：延迟与调用次数线性上升，而中间产物无人阅读，等于花钱买了一份不会被翻开的日志。

## 一句话小结

判断是否用链条的判据是中间产物是否需要固化，而不是任务是否复杂。

## 在本站知识结构中的位置

- 前置：PE-R-02
- 后继：PE-O-02
