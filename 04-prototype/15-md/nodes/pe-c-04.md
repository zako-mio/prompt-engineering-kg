# 检索质量与垃圾进垃圾出（Retrieval Quality and GIGO）

- 节点标识：PE-C-04
- 英文名：Retrieval Quality and GIGO
- 所属分组：G03 上下文工程
- 依赖深度：第 9 层
- 内容状态：内容已写满
- 标签：上下文工程、检索质量、评测分层

## 为什么需要它

生成质量的上限由检索质量决定：召回了无关或互相矛盾的资料，模型会被误导，而提示词层面的任何技巧都补不回来。这条约束决定了优化的顺序——先修检索，再调提示。检索质量的两个可控面是召回与排序：先保证相关片段进得来，再保证它们排得前。

**适用边界**

「先修检索」针对的是答案必须以资料为依据的任务；在创作类任务上检索只是参考，此时检索质量对结果的影响权重较低。

## 机制说明

检索链路由四个环节构成：分块策略、向量化模型、相似度与排序、以及最终进入上下文的数量。每个环节都有典型的失败模式：分块过大会引入噪声、过小会切断语义；向量模型与领域不匹配会导致语义漂移；只按相似度排序会引入近义但无关的片段；进入上下文的数量过多会稀释注意力。工程上应把评测分层：先单独评测检索的召回与精确度（例如答案片段是否被召回、召回片段中有多少无关），再评测端到端生成质量。分层的意义在于归因——整体分数下降时，能判断是检索退化还是生成退化。

## 何时该用 / 何时不该用

- 端到端质量不达标时：先分层评测检索，确认瓶颈位置再动手改提示。
- 检索结果进入上下文前：对片段做去重、截断与不可信内容标注。
- 不适用于创作类任务套用该顺序：此类任务检索只是参考，权重较低。
- 不适用于只评测端到端分数：无法归因的分数无法指导修复。

## 实验台

### file（python）

```python
cases = [
    {"q": "退款时限", "gold": {"d7"}, "returned": ["d7", "d2", "d9"]},
    {"q": "发票重开", "gold": {"d11"}, "returned": ["d4", "d5", "d6"]},
]

hit = sum(1 for c in cases if c["gold"] & set(c["returned"]))
noise = sum(len([d for d in c["returned"] if d not in c["gold"]]) for c in cases)
total = sum(len(c["returned"]) for c in cases)

print("recall@3:", f"{hit / len(cases):.0%}")
print("precision@3:", f"{(total - noise) / total:.0%}")
print("diagnosis:", "fix_retrieval_first" if hit / len(cases) < 1 else "review_prompt")
```

预期观察：输出 recall@3: 50%、precision@3: 17%、diagnosis: fix_retrieval_first，说明召回缺失时改提示词救不回答案。

### file（python）

```python
def rrf(ranked_lists, k=60):
    scores = {}
    for lst in ranked_lists:
        for rank, doc in enumerate(lst, start=1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda kv: -kv[1])

keyword = ["d3", "d1", "d8"]
vector = ["d1", "d5", "d3"]
for doc, score in rrf([keyword, vector]):
    print(f"{doc} {score:.5f}")
```

预期观察：输出顺序为 d1、d3、d5、d8，两路都命中的文档被抬到最前，说明混合排序看的是多路一致性而非单路名次。

## 证据

- **相关性的衡量标准是检索结果满足用户信息需求的程度，而不是向量距离的数值大小。**（S-0124，official）
  - 出处：https://learn.microsoft.com/en-us/azure/search/search-relevance-overview
  - 原文关键句：The true measure of relevance is how well a retrieved set of results meets your customer and user information needs.
- **混合检索通过在同一索引上合并关键词查询的精确性与向量查询的语义相似度来提升相关性。**（S-0124，official）
  - 出处：https://learn.microsoft.com/en-us/azure/search/search-relevance-overview
  - 原文关键句：Hybrid search (classic) delivers relevance by combining the precision of keyword queries and the semantic similarity of vector queries in a search request targeting a single index.
- **检索索引投毒已被列为一类独立攻击向量，说明检索侧的污染必须在检索层治理。**（S-0044，paper）
  - 出处：https://arxiv.org/abs/2603.22928
  - 原文关键句：agentic systems introduce new vectors for indirect prompt injection, code execution exploits, RAG index poisoning, and cross-agent manipulation that go beyond traditional AI threats.

## 术语

- **垃圾进垃圾出（GIGO）**：检索阶段召回的内容质量直接决定生成质量：不相关或互相矛盾的资料会误导生成层，提示词层面的技巧无法补偿。
- **评测集（Eval Set）**：带判据的一组代表性输入输出样本，是判断提示词改动是否真的变好的唯一依据；先建评测集再做优化。

## 失效模式

- 只按向量相似度取前 k 条：近义但无关的片段被召回，模型被误导且置信度看不出异常。
- 分块过大且重叠不足：跨段语义被切断，答案片段根本没进候选集，提示写得再好也无从作答。
- 只评测端到端分数：分数下降时无法区分检索退化与生成退化，修复动作只能靠猜。
- 把相关性等同于向量距离：离线指标好看而与用户信息需求脱节，线上满意度不升。

## 一句话小结

先分层评测检索再去调提示，检索结果进入上下文之前须去重与标注。

## 在本站知识结构中的位置

- 前置：PE-C-03
- 后继：PE-C-05
