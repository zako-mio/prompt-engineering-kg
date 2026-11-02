# 路由（Routing）

- 节点标识：PE-O-02
- 英文名：Routing
- 所属分组：G04 编排
- 依赖深度：第 9 层
- 内容状态：内容已写满
- 标签：编排、路由、成本

## 为什么需要它

路由按输入类型或难度把请求分派给不同处理路径与不同模型档位，是成本与质量之间最直接的调节手段。它的风险同样直接：分派错误的代价是把请求送进不适合的路径，效果可能比不做路由更差。

**适用边界**

路由的前提是分类判据可被评测；在分类准确率不足时，路由只是把不确定性从一处搬到另一处，并额外增加了复杂度。

## 机制说明

路由的常见分派维度有四种：任务类型（抽取、分类、生成、推理）、难度（是否需要多步推导）、数据敏感度（是否可外发）、以及成本档位（快模型与强模型）。实现上可以先用轻量模型或规则做分类，再按类别选择路径与模型。工程要点有三条：其一，分类判据必须建评测集并度量准确率与混淆情况；其二，必须保留兜底路径，分类不确定时走安全的一侧而不是强行分派；其三，路由本身会增加一次调用或一段判断逻辑，因此只有当档位间的成本或质量差异足够大时才划算。

## 何时该用 / 何时不该用

- 不同请求的成本敏感度或能力需求差异很大时：路由能显著改善整体性价比。
- 需要对敏感数据做本地处理、其余外发时：按数据敏感度分流是合规手段。
- 不适用于分类判据不可评测的场景：误分派会让效果劣于不路由。
- 不适用于档位差异很小的场景：路由开销可能超过节省。

## 实验台

### file（python）

```python
import json

RULES = [
    ("sensitive", lambda q: any(k in q for k in ("身份证", "手机号", "病历")), "local"),
    ("long_context", lambda q: len(q) > 8000, "strong"),
    ("yes_no", lambda q: q.strip().endswith("是或否？"), "cheap"),
]


def route(q):
    for name, pred, path in RULES:
        if pred(q):
            return path, name
    return "fallback", "no_rule"


CASES = [
    ("请判断这条评论是否违规，是或否？", "cheap"),
    ("病历摘要：患者主诉头痛三天", "local"),
    ("长文档：" + "内容" * 5000, "strong"),
    ("帮我写一首关于秋天的诗", "fallback"),
]

hits = 0
for q, want in CASES:
    got, why = route(q)
    hits += got == want
    print(json.dumps({"want": want, "got": got, "by": why}, ensure_ascii=False))
print("分派准确率 %d/%d" % (hits, len(CASES)))
assert hits == len(CASES), "分派判据与评测集不一致"

```

预期观察：运行后打印四条分派记录与一行「分派准确率 4/4」；把任一用例的期望路径改错时 assert 失败并以非 0 退出码结束。

## 证据

- **官方把路由与提示词链、并行化（分段与投票）并列写成预定义代码路径下的工作流模式，说明路由是代码层的分派而不是模型自发行为。**（S-0005，official）
  - 出处：https://www.anthropic.com/engineering/building-effective-agents
  - 原文关键句：Workflows are systems where LLMs and tools are orchestrated through predefined code paths. ... Prompt chaining ... Routing ... Parallelization (Sectioning / Voting)
- **官方明确指出延迟与成本问题有时换一个模型就能改善，因此档位分派应排在继续打磨提示词之前。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.
- **高推理档模型只需高层指导而普通档模型需要精确指令，所以分派路径时必须连同提示形态一起切换。**（S-0011，official）
  - 出处：https://developers.openai.com/api/docs/guides/prompt-engineering
  - 原文关键句：Generally speaking, reasoning models will provide better results on tasks with only high-level guidance. This differs from GPT models, which benefit from very precise instructions.

## 术语

- **路由（Routing）**：先对输入分类再分派给不同处理路径或不同模型的编排模式，用于在成本与质量之间做按需分配。
- **模型分层选型（Model Tiering）**：按任务难度把请求分派给不同能力档与价位的模型，用路由在成本与质量之间取得平衡。

## 失效模式

- 分派判据只在样例上试过就上线：分类准确率与混淆情况无人度量，误分派把难题送进弱档，整体效果比不路由更差。
- 没有兜底路径：分类器拿不准时仍强行选一条分支，不确定性被固化成确定的结果，而不是留在待人工处理的入口。
- 分派后不换提示形态：强档与弱档沿用同一份提示词，弱档被长指令压垮、强档被细步骤钉死，两档都拿不到应有水平。
- 路由省下的钱没有记账：只统计平均单价下降，不统计误分派带来的重试与人工复核，账面省了而实际更贵。

## 一句话小结

路由要建分类评测集并保留兜底路径，否则误分派比不做路由更差。

## 在本站知识结构中的位置

- 前置：PE-O-01
- 后继：PE-O-03
