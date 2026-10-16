# 注意力预算与上下文衰减（Attention Budget and Context Rot）

- 节点标识：PE-F-06
- 英文名：Attention Budget and Context Rot
- 所属分组：G00 地基：模型是概率采样器
- 依赖深度：第 5 层
- 内容状态：内容已写满
- 标签：地基、注意力、上下文衰减

## 为什么需要它

上下文窗口变大不等于可以随便塞：窗口内的有效注意力是有限资源，token 越多，每个 token 分到的注意力越少，关键信息被忽略的概率随之上升。这条约束解释了为什么「检索到就塞进去」的策略会失效，也解释了长资料置顶与压缩策略为何有效。

**适用边界**

注意力预算是机制解释而非精确可计算量，工程上只能通过位置安排、压缩与检索精度来间接管理，不能把它当公式使用。

## 机制说明

上下文衰减描述的是随上下文增长，模型对其中信息的实际可用性下降。机制侧的解释是注意力预算有限：窗口内 token 越多，单位 token 可分得的注意力越少，因此正确的目标不是「塞满窗口」，而是维持一组最小的、高信噪比的 token 集。工程推论有三条：其一，位置安排有实际收益——相关信息放在输入首尾比放在中部更容易被使用；其二，压缩与摘要不是省成本的附属手段，而是维持信噪比的必要动作；其三，检索精度比检索数量更重要，多召回的相关度低的片段会稀释注意力。

## 何时该用 / 何时不该用

- 上下文接近窗口上限时：优先压缩与筛选，而不是继续追加资料。
- 资料很多时：把最相关的片段置于首尾并显式引用，避免关键信息落在中部。
- 不适用于把预算当精确公式：它只提供方向性判据，具体取舍须用评测集验证。
- 不适用于以「窗口很大」为由放弃筛选：窗口容量与有效注意力是两件事。

## 实验台

### shell（bash）

```bash
# 位置实验：同一句关键信息分别放在资料的首部 / 中部 / 尾部
# 三档各跑 20 次，统计「答案用到了该关键信息」的比例
for pos in head middle tail; do
  echo "== pos=$pos =="
  for i in $(seq 1 20); do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"needle-$pos.json" | grep -o 'NEEDLE[_-]OK' | wc -l
  done | awk '{s+=$1} END {print "命中率", s/NR}'
done
```

预期观察：首部与尾部的命中率通常高于中部，且资料越长差距越明显——这一步把「位置偏差」从说法变成自己量出来的读数。

### file（markdown）

```markdown
上下文预算表：把当前上下文逐块登记
  块（资料 / 示例 / 历史 / 工具定义 / 记忆） | token | 标注（必要 / 可压缩 / 可删） | 删或压之后的评测读数
判据：任何标为「可删」的块都必须真的删掉并重跑评测，用读数说话。
不得用「窗口还没满」当作保留理由——窗口容量与有效注意力是两件事。
```

预期观察：读者能对上下文做有依据的取舍，而不是把「检索到的东西」全部留在窗口里。

## 证据

- **相关信息出现在输入的首部或尾部时表现最好，必须从长上下文中部取用时显著下降——且这一点对「显式长上下文模型」同样成立。**（S-0063，official）
  - 出处：https://aclanthology.org/2024.tacl-1.9/
  - 原文关键句：relevant information occurs at the beginning or end of the input context, and significantly degrades when models must access relevant information in the middle of long contexts
- **官方给出的长上下文技巧之一是「把长资料放在前部、query 与指令放在其后」——支持「位置安排是工程动作」这一推论。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Put longform data at the top: Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples.
- **推理过程本身冗长且可通过在提示中给定合理的 token 预算来压缩，而预算取值的选取显著影响压缩效果——支持「压缩是维持信噪比的必要动作」。**（S-0056，paper）
  - 出处：https://arxiv.org/abs/2412.18547
  - 原文关键句：the reasoning process of current LLMs is unnecessarily lengthy and it can be compressed by including a reasonable token budget in the prompt

## 术语

- **注意力预算（Attention Budget）**：模型在单个上下文窗口内可分配的有效注意力总量有限；token 越多，单位 token 可分得的注意力越少，这一约束构成上下文衰减的机制基础。
- **上下文衰减（Context Rot）**：随上下文长度增长，模型对其中信息的实际可用性下降的现象；表现为长上下文中关键信息被忽略或利用不充分。

## 失效模式

- 以「窗口很大」为由放弃筛选：窗口容量与有效注意力是两件事，塞满窗口只会稀释关键信息。
- 把注意力预算当精确公式：它提供的是方向性判据，据此反推「还剩多少注意力」是伪精确。
- 检索到就塞：多召回的低相关片段会稀释注意力，反而降低关键信息被真正使用的概率。
- 关键信息落在中部：位置偏差使中部内容最易被忽略，资料总量再小也可能踩到这一点。

## 一句话小结

窗口容量不等于有效注意力，目标是维持最小的高信噪比 token 集。

## 在本站知识结构中的位置

- 前置：PE-F-05
- 后继：PE-S-01
