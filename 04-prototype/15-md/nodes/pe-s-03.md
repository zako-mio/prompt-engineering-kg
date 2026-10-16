# 推理与格式的冲突（Reasoning–Format Conflict）

- 节点标识：PE-S-03
- 英文名：Reasoning–Format Conflict
- 所属分组：G01 确定性输出
- 依赖深度：第 8 层
- 内容状态：内容已写满
- 标签：确定性输出、推理、格式约束

## 为什么需要它

强格式约束与推理能力之间存在真实冲突：同一条需要多步推导的任务，在「先自由推理再格式化」与「边推理边遵守 schema」两种形态下质量可以差一截，且约束越严退化越大。看清这条冲突才能定下实现顺序——需要推理的任务先自由推理再格式化，不需要推理的任务才直接强约束。

**适用边界**

这条冲突的前提是任务本身需要推导：抽取、分类、改写这类不需要推理的任务，强结构几乎没有代价，直接一次强约束即可。冲突的实证对象是生成空间受限的约束解码与强格式指令，不含两阶段模式——两阶段之所以有效，正是因为它把推理与格式化在时间上分开了。

## 机制说明

冲突的机制有三个候选层面。一是解码期受限：约束解码在每一步都屏蔽了大部分候选 token，模型无法在中间状态上自由试探，推理所需的「先走错再修正」被结构合法性掐掉。二是注意力被格式占位：schema 的字段名、括号与转义在本可用于题目本身的注意力预算里占去一块。三是训练分布里的格式—长度耦合：模型见到的结构化输出往往很短，于是被要求遵守 schema 时倾向直接给答案，而不是先展开推导。缓解手段因此有三条：两段式，先用一次不加强格式约束的调用完成推理，再用一次带 schema 的调用把结论整理成目标结构；把 schema 压扁成下游真正消费的最少字段，减少必填项与嵌套；必要时把约束档位从最严放宽到较弱的 A 档，再用校验与修复回路补回结构可靠性。代价是调用次数与延迟上升，收益是推理质量与结构可靠性同时成立。

## 何时该用 / 何时不该用

- 需要多步推导且输出要结构化：拆成推理与格式化两次调用，中间结果以自然语言或无约束草稿传递。
- 抽取、分类、改写这类不需要推导的任务：直接上最严约束，一次调用完成，不为两阶段付延迟。
- 不适用于把两阶段当默认：简单任务上多一次调用只增加成本与延迟，不带来质量收益。
- 不适用于只测结构通过率：格式合法而语义错误的输出会通过结构校验，须同时统计语义正确率。

## 实验台

### shell（bash）

```bash
# 同一批需要多步推导的题，两种形态各跑一遍，分别统计语义正确率、结构合法率与平均输出 token
# schema_only：一次调用，直接要求输出符合 schema 的 JSON
# two_stage：第一次自由推理，第二次只把结论整理进 schema
for shape in schema_only two_stage; do
  echo "== shape=$shape =="
  for i in $(seq 1 30); do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"req-$shape-$i.json" > "out-$shape-$i.json"
  done
  python3 score.py --shape "$shape"   # 打印 语义正确率 / 结构合法率 / 平均输出 token
done
```

预期观察：schema_only 档的结构合法率通常接近满分、语义正确率明显更低；two_stage 档把语义正确率补回来，代价是调用次数与总 token 上升。两次读数的差值就是这个冲突在本模型与本题集上的量级，也是判断是否值得拆调用的依据。

### file（markdown）

```markdown
schema 压扁清单：对着现有 schema 逐字段问四句
  下游真的会读这个字段吗 | 能否由其它字段推导出来 | 是否只是文档性说明 | 能否从嵌套对象提升为平铺标量
判据：四句里有一句答「否」就删掉该字段；删完重跑上一步的两形态对照，看语义正确率的差距是否缩小。
注意：压扁只降低格式约束的占用，替代不了两段式——需要长推导时仍要拆调用。
```

预期观察：读者能把自己的 schema 砍到只留下游真正消费的字段，并能量出压扁之后两形态之间的差距收窄了多少。

## 证据

- **格式约束下模型的推理能力出现显著下降，且约束越严退化越大——这是本节点核心结论的一手实证。**（S-0053，paper）
  - 出处：https://arxiv.org/abs/2408.02442
  - 原文关键句：we observe a significant decline in LLMs reasoning abilities under format restrictions. ... stricter format constraints generally lead to greater performance degradation
- **推理过程本身在 token 上是有长度的，且推理预算的取值直接决定效果——支持「格式占用与推理展开相互挤占」这一解释路径。**（S-0056，paper）
  - 出处：https://arxiv.org/abs/2412.18547
  - 原文关键句：the reasoning process of current LLMs is unnecessarily lengthy ... the choice of token budget plays a crucial role in the actual compression effectiveness
- **推理增益取决于任务深度：深任务上 CoT 带来 +54 至 +68 个百分点的回升，浅任务上 CoT 在结构上是冗余的——支持「不需要推理的抽取类任务几乎不承受格式代价」这一适用边界。**（S-0039，paper）
  - 出处：https://arxiv.org/abs/2608.09942
  - 原文关键句：On high-depth P-complete tasks (GSM8K, MATH), CoT gives a +54 to +68 pp recovery gap across all models. On shallow TC^0 tasks (MMLU, ARC), CoT is structurally redundant (Delta in [0.0, +4.6] pp).

## 术语

- **推理与格式的冲突（Reasoning–Format Conflict）**：在生成空间受限的格式约束下，模型的推理表现会下降，且约束越严退化越大；本节点给出的处置是把推理与格式化在时间上拆开，而不是在两者之间二选一。
- **约束解码（Constrained Decoding）**：在采样阶段按文法或 schema 屏蔽不合法的 token 路径，使输出在结构上必然合法；本节点关注的正是这种逐 token 屏蔽对中间推理步骤的挤压。
- **结构化输出（Structured Output）**：以 JSON Schema 等模式约束模型输出结构的机制；严格模式通常要求全部字段必填且禁止额外属性，字段与嵌套越多，被压缩的自由生成空间越大。

## 失效模式

- 把 schema 写全当严谨：字段越全、必填越多、嵌套越深，被挤占的自由生成空间越大，推理任务上的语义正确率反而下降。
- 只看结构合法率：约束一严结构通过率必然变高，若不同时测语义正确率，会把推理退化读成质量提升。
- 把两阶段当默认：不需要推导的抽取类任务上多一次调用只增加延迟与成本，收益为零。
- 两阶段的中间结果也传成结构体：第一段输出若同样要符合 schema，等于把约束提前搬回推理阶段，冲突并未被规避。

## 一句话小结

需要推理的任务应把自由推理与结构化整理拆成两次调用，只有不需要推导的抽取类任务才适合直接上最严约束。

## 在本站知识结构中的位置

- 前置：PE-S-02
- 后继：PE-S-04
