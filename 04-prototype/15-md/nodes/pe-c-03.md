# 图检索与全局观（Graph Retrieval and Global View）

- 节点标识：PE-C-03
- 英文名：Graph Retrieval and Global View
- 所属分组：G03 上下文工程
- 依赖深度：第 8 层
- 内容状态：内容已写满
- 标签：上下文工程、图检索、全局观

## 为什么需要它

向量检索擅长定位片段，却不擅长回答需要跨文档综合的问题，因为答案不在任何单个片段里。图检索通过实体与关系索引补上这一层全局观，让「这批资料整体说了什么」这类问题可被回答。它的代价是索引构建与更新的成本更高，且更新链路更长。

**适用边界**

图谱的构建与维护成本显著高于向量索引，且对需要精确定位的问题不如向量检索直接；因此它适合作为按问题类型分流的第二通道，而不是替代向量检索的默认通道。

## 机制说明

图检索的基本流程是：抽取实体与关系构建索引，检索时沿关系遍历并聚合相关子图，再对聚合结果生成摘要或全局视图，最后把摘要作为上下文交给模型。它相对向量检索的优势在于关系可达性与跨文档聚合；劣势在于索引构建成本、更新成本以及查询路径的调参复杂度。工程上常见的务实做法是混合：用向量检索处理定位型问题，用图检索处理全局型问题，并用一个轻量分类器或规则在两者之间分流。判据可以写成：如果问题的答案需要在多个文档之间做归纳或比较，就走图检索通道；如果答案可以在单个片段内找到，就走向量通道。

## 何时该用 / 何时不该用

- 需要跨文档归纳、比较或脉络发现的问题：图检索通道更有优势。
- 资料集合相对稳定、索引维护成本可摊销时：图谱索引的经济性成立。
- 不适用于定位型问题：单片段可答的问题上图检索只会增加成本。
- 不适用于索引频繁变更的场景：图谱更新成本会压过收益。

## 实验台

### shell（bash）

```bash
# 同一条全局型问题（例：这批资料整体在争论什么），换两种上下文形态各跑 3 次
#   segments      = 向量检索 top-k 片段直接拼接
#   entity-digest = 先抽实体与关系、再压成社区摘要
for shape in segments entity-digest; do
  echo "== shape=$shape =="
  for i in 1 2 3; do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"payload-graph-$shape.json" \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
  done
done
```

预期观察：segments 档在被追问「这批资料分几派、各派主张是什么」时往往答不全，entity-digest 档能一次给出分派与出处。判据是数每次回答里被点名的文档编号个数：segments 档常为 1 到 2 个，entity-digest 档应不少于 3 个且跨不同文档。

### file（markdown）

```markdown
问题分流登记表（拿手上 10 条真实问题，每条填一行）：
  问题 | 能否在单个片段内答出 | 需要几个文档 | 走哪个通道
判据：答案要跨两个以上文档归纳或比较的问题走图通道，其余走向量通道；同一行只许标一个通道。
补充：图通道的索引是一次性重活，登记表要同时记下建索引的模型调用次数与耗时，否则判断不了这条路是否划算。
```

预期观察：10 行问题每行只有一个通道，被分到图通道的问题都在向量通道上试过且确实答不好；登记表里有索引调用次数与耗时两列。

## 证据

- **针对整个语料库的全局问题，纯向量检索会失效，因为这类问题本质是查询聚焦的摘要任务而不是检索任务。**（S-0121，paper）
  - 出处：https://arxiv.org/abs/2404.16130
  - 原文关键句：RAG fails on global questions directed at an entire text corpus ... since this is inherently a query-focused summarization (QFS) task, rather than an explicit retrieval task.
- **该方法的图索引分两阶段完成：先从源文档抽取实体知识图谱，再为紧密关联的实体群预生成社区摘要。**（S-0121，paper）
  - 出处：https://arxiv.org/abs/2404.16130
  - 原文关键句：Our approach uses an LLM to build a graph index in two stages: first, to derive an entity knowledge graph from the source documents, then to pregenerate community summaries ...
- **上游实现仓自述处于维护模式、不再接受新 PR 与新功能，因此它只能当研究原型用，不能当有支持的依赖。**（S-0122，community）
  - 出处：https://raw.githubusercontent.com/microsoft/graphrag/main/README.md
  - 原文关键句：This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features.

## 术语

- **图检索（GraphRAG）**：结合知识图谱的实体关系索引与传统向量检索，用于回答需要全局脉络或跨文档聚合的问题。

## 失效模式

- 把图检索当默认通道：定位型问题要多付一次建索引与遍历的代价，答案还未必比向量检索准。
- 在上游已自述维护模式的仓上建生产依赖：代码是演示级、不再接受新特性，出问题没有上游兜底。
- 开工前没算索引成本：实体抽取与社区摘要要对全量语料跑一遍模型调用，语料一改就得重算。
- 把社区摘要当事实来源：摘要是模型压缩出来的，数字与细节可能被抹掉，拿它答数值问题会得到像样的错答案。

## 一句话小结

图检索补的是跨文档综合能力，应作为按问题类型分流的第二通道。

## 在本站知识结构中的位置

- 前置：PE-C-02
- 后继：PE-C-04
