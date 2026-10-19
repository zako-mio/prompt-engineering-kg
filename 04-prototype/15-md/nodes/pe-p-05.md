# 记忆与反思（Memory and Reflection）

- 节点标识：PE-P-05
- 英文名：Memory and Reflection
- 所属分组：G09 落地实践
- 依赖深度：第 23 层
- 内容状态：内容已写满
- 标签：落地实践、记忆、反思

## 为什么需要它

长时程任务装不进一个上下文窗口，必须把中间结论写到外部、需要时再取回来，否则每次执行都从零开始。反思把一次执行的经验固化成下次可用的准则，因此写进记忆的东西会长期影响后续判断，写错一条的代价远高于写慢一条。两者共用一条纪律：结论能不能信，取决于裁决信号从哪里来。实践中按信号来源区分复核强度——自评生成的候选最需要外部复核，独立评估次之，外部信号最直接；本次未取得逐档对比三类信号强度的引文，此处按工程经验陈述，不作为已证结论。

**适用边界**

本节点的机制在可取得外部信号的场景下成立；若任务没有可判定的成败信号，反思只能停留在候选层，不能当作已确立的结论写入长期记忆。外部记忆文件这一层是工程延伸做法，官方长时程三分法只列压缩、结构化笔记与多智能体架构三项，引用时应注明来源层级。

## 机制说明

记忆的写入、检索、复核与退役构成一个回路：写入时条目必须带来源、适用边界与证据强度，否则日后无法判断它是否过期；写入要有预算上限并采用零和替换，让新条目挤掉旧条目，避免无限膨胀；退役不等于删除，应保留归档以便解释历史决策。把上下文写出去有三种常见形态：压缩，把已完成的对话压成摘要以维持流程，压缩强度需要显式设定并实测，否则摘要要么丢信息、要么没省下窗口；结构化笔记，适合有明确里程碑的迭代开发；以及多智能体架构，把上下文分给各自持有独立窗口的执行者，让并行探索各写各的。在这三种之外，工程上常再补一层外部记忆文件：条目按需检索后注入。这一层属于工程实践的延伸做法，官方三分法并未单列，其依据是官方把跨步骤持久化列为上下文工程的既定策略。反思把一次执行的经验固化成准则，其可靠性取决于裁决信号从哪里来：自评只是用自己的判断把同一批证据重排一遍，缺少独立于自身输出的真值来源，对事实性错误的判别力因此有限；独立评估引入第二个判断者，能纠正一部分自评盲区，但两者仍可能共享同一类错误；外部信号不依赖模型的看法，实践中是对事实性错误最直接的一种否证来源，本次未取得逐档对比的引文，此处同样按工程经验陈述。工程做法是：自评只用于生成候选，候选经独立评估或外部信号裁决后才进入长期记忆。

## 何时该用 / 何时不该用

- 跨会话复用的结论：写入记忆并标注来源、适用边界与证据强度，未标注的条目不得进入长期记忆。
- 长时程任务中途需要释放窗口时：先压缩对话再落结构化笔记，把里程碑与未决问题写进外部文件；并行分支之间不需要共享上下文时，改用多智能体架构让各自持有独立窗口。
- 不适用于把未复核的自评结论直接写入：自评缺少独立真值来源，会把未经检验的判断固化下来。
- 不适用于只写不退役：过期条目会持续影响新决策，且无法被质疑。

## 实验台

### file（markdown）

```markdown
# 记忆条目（每条都必须能回答：它在什么条件下不成立）
- 结论：<一句话，可判定>
- 来源：<外部信号 / 独立评估 / 模型自评>
- 证据强度：<已由外部信号验证 / 仅独立评估通过 / 仅自评生成>
- 适用边界：<什么条件下成立，什么条件下不成立>
- 复核触发：<再次被引用时 / 超过复核周期 / 上游事实变更时>
- 退役标记：<失效后改标为已退役并保留归档>

# 写入预算（零和替换）
- 条目数上限：<上限值>
- 替换规则：新条目挤掉最弱的一条，按证据强度与最近一次复核结果排序
```

预期观察：产出的记忆文件里每条都能追溯到裁决信号来源与适用边界，且条目总数不超过上限；新条目入库时必有旧条目被替换或退役，文件不会无限增长。

### shell（bash）

```bash
# 容量与复核到期检查：把预算和复核日期写成可执行判据
MEM=./memory/entries.jsonl
CAP=40
n=$(wc -l < "$MEM")
echo "entries=$n cap=$CAP"
[ "$n" -le "$CAP" ] || echo "over budget: retire the weakest entry before writing"
python3 - "$MEM" <<'PY'
import datetime, json, sys
today = datetime.date.today()
for line in open(sys.argv[1], encoding='utf-8'):
    entry = json.loads(line)
    due = datetime.date.fromisoformat(entry['review_by'])
    if due <= today:
        print('due:', entry['id'], entry['signal'], entry['review_by'])
PY
```

预期观察：脚本先打印条目数与上限，超出上限时提示先替换或退役最弱的一条；随后逐条列出复核到期的条目及其裁决信号来源，据此决定复核、降级还是退役。

## 证据

- **官方给出的长时程任务三分法把压缩、结构化笔记与多智能体架构并列，并指出结构化笔记适合有明确里程碑的迭代开发——这正是把上下文写出去、需要时再取回来的工程形态。**（S-0004，official）
  - 出处：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：compaction, structured note-taking, and multi-agent architectures. ... Compaction maintains conversational flow...; Note-taking excels for iterative development with clear milestones
- **官方把跨步骤持久化信息与压缩大数据量并列为上下文工程的正式策略，因此外部记忆文件这一工程延伸做法有官方策略层面的依据，但它本身不是长时程三分法里的一项。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **一手研究把「检索成功」写成推理的前提条件——外部记忆的价值不在写入动作本身，而在需要时能否被检索到并进入上下文，因此检索路径与条目组织必须当作工程对象来设计。**（S-0064，paper）
  - 出处：https://arxiv.org/abs/2508.07479
  - 原文关键句：successful retrieval is a prerequisite for reasoning
- **压缩不是随手截断：研究显示冗长的推理过程可以靠提示里的 token 预算压下来，但预算取值直接决定压缩效果——压缩强度必须显式设定并实测。**（S-0056，paper）
  - 出处：https://arxiv.org/abs/2412.18547
  - 原文关键句：the reasoning process of current LLMs is unnecessarily lengthy ... but the choice of token budget plays a crucial role in the actual compression effectiveness
- **以可计算的指标作为裁决信号时，反思式进化在六项任务上平均超过强化学习基线 6 个百分点、最高 19 个百分点，且所需 rollout 最多少 35 倍——外部信号带来的收益是可测的。**（S-0047，official）
  - 出处：https://proceedings.iclr.cc/paper_files/paper/2026/hash/0e9e708b6f48e14fd0ac29e167413f76-Abstract-Conference.html
  - 原文关键句：Across six tasks, GEPA outperforms GRPO by 6 percentage points on average and by up to 19pp, while using up to 35x fewer rollouts.

## 术语

- **记忆与反思（Memory and Reflection）**：把跨会话的结论沉淀为可复用的记忆条目，写入时标注来源、适用边界与证据强度，并在被引用时按实际效果复核与退役，避免记忆成为过期经验的放大器。
- **反思与自评回路（Reflection and Self-Critique Loop）**：让模型对自己的输出给出评价并据此改写，形成闭环改进；在记忆场景中它只负责生成候选准则，候选须经独立评估或外部信号裁决后才能入库。
- **文本梯度与反思式进化（Textual Gradient and Reflective Evolution）**：以自然语言反馈作为改进信号逐层优化组件，或让模型基于自身执行轨迹反思并生成改进规则；后者的可靠性取决于裁决信号来自模型自身还是外部。

## 失效模式

- 把自评当裁决：自评用的是生成该结论时的同一套依据，复核往往只是重排原有判断，错误容易被原样固化进长期记忆。
- 记忆只写不退役：过期条目持续参与决策且无法被质疑，形成越用越偏的经验放大器。
- 条目缺来源与适用边界：日后无法判断它是否过期，也无法在被引用时触发复核。
- 写入没有预算上限：记忆无限膨胀，检索命中率下降，真正有用的结论被淹没。

## 一句话小结

记忆条目带来源与适用边界，写入设预算、退役留归档；反思只产候选，候选经独立评估或外部信号裁决后才写入长期记忆。

## 在本站知识结构中的位置

- 前置：PE-P-04
- 后继：PE-P-06
