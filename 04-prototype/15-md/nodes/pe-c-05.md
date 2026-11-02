# 长上下文位置偏差（Long-context Positional Bias）

- 节点标识：PE-C-05
- 英文名：Long-context Positional Bias
- 所属分组：G03 上下文工程
- 依赖深度：第 10 层
- 内容状态：内容已写满
- 标签：上下文工程、位置偏差、长上下文

## 为什么需要它

同一份资料放在输入的不同位置，模型能否用上它差别很大。这条偏差直接决定了长资料该放哪里、关键结论该重复几次，以及为什么「检索到就塞进去」不可靠。位置偏差与上下文长度是两个问题：窗口变长不会自动消除首尾偏好。

**适用边界**

偏差的形态随输入占窗口比例变化：在占比不高时表现为中部被忽略，接近窗口上限时首因偏差减弱、转为距离型偏差；因此位置策略必须与实际的窗口占用比例一起考虑。

## 机制说明

位置偏差的经典表现是：相关信息位于输入开头或结尾时表现最好，落在中部时明显退化，显式长上下文模型也不例外。2025 年的一项更新给出更细的条件：该效应在输入占上下文窗口不超过一半时最强，越过这条线后首因偏差减弱、近因偏差相对稳定，中部忽略被距离型偏差取代。复现研究还提出方法学提醒：主题抽样是方差的主要来源，小的主题集会掩盖或放大排序效应，理想化设定下的结论不总能迁移到真实流水线。工程上可落地的动作是三条：把长资料放在最前，把问题与指令放在其后，要求模型先引用原文再给结论。此外还要记录本次输入的窗口占用比例，用真实占比而不是字数去校验位置策略。

## 何时该用 / 何时不该用

- 长资料进入上下文时：资料置前、问题与指令置后，并要求先引用后作答。
- 窗口占用比例很高时：优先压缩，避免落入距离型偏差区间。
- 不适用于照搬论文设定：主题抽样与窗口占比不同会改变结论。
- 不适用于把位置策略当唯一手段：检索精度与压缩仍是主要杠杆。

## 实验台

### shell（bash）

```bash
# 同一份关键资料，分头部 / 中部 / 尾部三种位置各跑 20 次，统计答对次数
# 输入要先撑到接近模型窗口的一半，否则三档差异会被稀释
for pos in top middle bottom; do
  echo "== pos=$pos =="
  for i in $(seq 1 20); do
    curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
      -d @"payload-pos-$pos.json" | grep -o 'ANSWER=[0-9]*' || echo ANSWER=none
  done | sort | uniq -c
done
```

预期观察：top 与 bottom 两档里 ANSWER=42 的出现次数应明显多于 middle 档；若三档计数持平，先核对资料确实占了窗口的一半以上，再决定是否相信这次实验。

### file（markdown）

```markdown
装配检查单（每次请求都要能逐条核对）：
  - 长资料放在最前，问题与指令放在其后
  - 要求模型先逐字引用相关段落，再给结论
  - 记录本次输入的 token 数与模型窗口上限，算出占用比例
判据：抽查 20 次请求，资料起始位置落在消息序列前 10%、问题落在最后 10%，且占用比例有记录；缺任一项即不算做完。
```

预期观察：20 次请求逐条打勾通过，且能说出本次实验落在窗口占用的哪一档（不超过 50% 或超过 50%），而不是只凭观感说「已经放前面了」。

## 证据

- **相关信息位于输入开头或结尾时表现最好，落在长上下文中部时显著退化。**（S-0063，official）
  - 出处：https://aclanthology.org/2024.tacl-1.9/
  - 原文关键句：performance is often highest when relevant information occurs at the beginning or end ... and significantly degrades when models must access relevant information in the middle of long contexts
- **位置偏差在输入占上下文窗口不超过一半时最强，越过之后首因偏差减弱而近因偏差保持相对稳定。**（S-0064，paper）
  - 出处：https://arxiv.org/abs/2508.07479
  - 原文关键句：the LiM effect is strongest when inputs occupy up to 50% of a model's context window. Beyond that, the primacy bias weakens, while recency bias remains relatively stable.
- **官方工程口径把「长文档与数据置于提示最前、问题与指令放在其后」写成了明确动作。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Put longform data at the top: Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples.

## 术语

- **迷失在中间（Lost in the Middle）**：相关信息位于长上下文首尾时表现最好、位于中间时显著退化的位置偏差；该效应在输入接近上下文窗口上限时会被距离型偏差取代。
- **注意力预算（Attention Budget）**：模型在单个上下文窗口内可分配的有效注意力总量有限；token 越多，单位 token 可分得的注意力越少，这一约束构成上下文衰减的机制基础。

## 失效模式

- 把关键资料放在中部：单片段可答的问题也会答错，而且不报错，只给一个泛泛的答案。
- 照搬论文设定下结论：主题抽样与窗口占比一换，排序效应就被掩盖或放大，换一批资料结论就变。
- 只调顺序不改检索与压缩：噪声没降下来，位置带来的收益很快被淹没。
- 用字数估算窗口占用：占用比例要按 token 与模型窗口算，估出来的档位会错，那条 50% 的线就无从判断。

## 一句话小结

资料置前、问题置后，并要求先引用后作答；位置策略须在真实窗口占比上验证。

## 在本站知识结构中的位置

- 前置：PE-C-04
- 后继：PE-C-06
