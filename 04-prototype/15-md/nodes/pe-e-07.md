# 文本梯度与反思式进化（Textual Gradient and Reflective Evolution）

- 节点标识：PE-E-07
- 英文名：Textual Gradient and Reflective Evolution
- 所属分组：G05 评测与自动优化
- 依赖深度：第 19 层
- 内容状态：内容已写满
- 标签：文本梯度、反思进化、优化回路

## 为什么需要它

手工调提示词的瓶颈是反馈留不下来：改一句、跑一遍、凭印象判断，下一次改动无法与前一次严格比较。文本梯度把自然语言评价当作「梯度」逐层回传到系统的每个可变组件上，反思式进化则让模型读自己的执行轨迹、生成可复用的改进规则并写回提示。两者把「靠人猜方向」换成「靠轨迹与评分驱动的搜索」，也正因如此，它们的前提是硬的：拿不到轨迹，反思就没有依据；没有可自动计算的评分函数，就无法判断一次改动是改进还是退化。

**适用边界**

这套方法不能被当成「无脑自动调优」：当任务无法自动评分、执行轨迹被截断或读不到、或者改动效果只能靠主观感受判断时，反思与搜索都会退化成随机改写——它们自动化的只是候选生成，判定权始终在使用者手里。另一条限制来自成本与收益结构：每次反思与每轮搜索都要额外调用模型，若任务本身调用量极小、或提示词很少改动，优化开销会超过收益；此外部分实现的增益依赖任务类型与底座模型规模，换个任务或换小模型未必复现。

## 机制说明

文本梯度的做法是：把系统的每个可变部分（提示、代码片段、输出）表示为变量，用模型对结果给出自然语言评价，再把评价作为「梯度」回传到变量上做更新；这条路线在问答与代码优化任务上给出了可测的改进，并已发表于同行评议期刊。反思式进化则让模型看到自己的推理轨迹与评分，生成改进规则并更新提示；报告显示其在多个任务上优于强化学习基线，且所需采样次数大幅减少。两者的工程前提相同：必须能拿到完整执行轨迹（否则反思没有依据）与可用评分函数（否则无法判断改进方向）。落地时有三条关键设计：其一，把评分函数当成产品的一部分来维护，因为它定义了优化器真正在追什么；其二，把每次候选与得分留档，否则无法区分真实增益与采样噪声；其三，控制搜索预算，采样次数与并行度都要有上限，避免优化成本超过提示词本身的价值。

## 何时该用 / 何时不该用

- 已能自动计算评分函数时：候选之间有了可判定的比较口径，优化回路才谈得上收敛。
- 能取到完整执行轨迹时：模型读得到失败过程，生成的改进规则才指向真正的原因。
- 系统由多个可分别评价的组件构成时：文本梯度可逐组件回传评价，而不必整体重写提示。
- 候选需求远大于人工审阅能力时：让模型批量提出候选、由评分函数筛选，比逐条手改更划算。
- 不适用于没有评分函数的任务：没有判据就没有改进方向，搜索无法收敛，往往只把提示词越改越长。
- 不适用于轨迹缺失或调用预算极小的场景：反思失去依据，额外调用还会推高成本。

## 实验台

### shell（python）

```python
# 最小反思式优化回路：轨迹 → 评分 → 反思规则 → 新候选 → 留档
TRACE, CAND, K, MIN_GAIN = [], [], 3, 0.05

def metric(output, expect):          # 前提 1：可自动计算的评分函数（没有它就没有改进方向）
    return 1.0 if expect.strip() in output else 0.0

def run(prompt, batch, call_lm):     # call_lm(prompt, x) 返回 (output, steps)
    rows = []
    for x in batch:
        output, steps = call_lm(prompt, x['input'])
        rows.append({'input': x['input'], 'output': output, 'steps': steps,   # 前提 2：完整轨迹
                     'score': metric(output, x['expect'])})
    TRACE.extend(rows)               # 轨迹必须先落盘，再谈反思
    return rows

def reflect(rows, call_reflect):     # 反思只产出「改进规则」，不直接重写答案
    bad = [r for r in rows if r['score'] == 0]
    return call_reflect(bad)         # 输入里要含中间步骤，否则模型只能对着结果猜原因

def step(prompt, batch, call_lm, call_reflect):
    rows = run(prompt, batch, call_lm)               # 基线：同一评测窗口上的得分
    rule = reflect(rows, call_reflect)               # 读失败轨迹 → 改进规则
    cand = call_lm.rewrite(prompt, rule)             # 只按规则改，其余原文不动
    base = sum(r['score'] for r in rows) / len(batch)
    scores = [sum(r['score'] for r in run(cand, batch, call_lm)) / len(batch) for _ in range(K)]
    mean = sum(scores) / K
    CAND.append({'rule': rule, 'base': base, 'mean': mean,
                 'spread': max(scores) - min(scores),
                 'adopted': mean - base >= MIN_GAIN})
    return cand if CAND[-1]['adopted'] else prompt    # 未过阈值 ⇒ 保留原提示词，候选只留档
```

预期观察：每次迭代都留下「基线分 / 候选分 / 波动幅度 / 是否采纳」四列；只有均值增益跨过阈值且波动没有恶化才采纳候选，否则保留原提示词进入下一轮。去掉重复次数 K 与 spread 就会把一次幸运运行当成真实增益（把 call_lm / call_reflect 换成你所用的框架调用即可，例如 DSPy 程序加 LM）。

### file（markdown）

```markdown
# 反思式优化台账（三个文件，缺一不可）
1. `trace.jsonl` —— 每次运行一行：run_id / prompt_version / input / 中间步骤（工具调用、检索结果）/ output / score / failure_mode
   规则：只存最终答案的轨迹撑不起反思——模型看不到「为什么错」，改进规则就会指错原因。
2. `candidates.md` —— 候选表：候选号 / 改动摘要 / 反思规则原文 / 评测窗口 / 重复次数 K / 均值 / 波动 / 采纳或拒绝
   规则：被拒绝的候选也要留档，否则同一改动会被下一轮反复提出。
3. `baseline.md` —— 基线表：prompt_version / eval_set_version / 均值 / 结论 / 回滚条件
   回滚条件示例：线上指标连续 3 次低于基线即回滚，并把该失败模式补进评测集再重跑。
```

预期观察：打开台账即可回答三件事：这次候选相对基线涨了多少、涨得稳不稳、上次被拒绝的改动是什么；三个文件缺任何一个，优化回路都会退化成「凭印象换提示词」。

## 证据

- **文本梯度路线在问答与代码优化任务上都拿到了可测的准确率提升，说明「把自然语言反馈当梯度逐层回传」是可评测的工程方法而非修辞。**（S-0049，official）
  - 出处：https://api.crossref.org/works/10.1038/s41586-025-08661-4
  - 原文关键句：TextGrad improves the zero-shot accuracy of GPT-4o in Google-Proof Question Answering from 51% to 55%, yields 20% relative performance gain in optimizing LeetCode-Hard coding problem solutions
- **反思式进化在六个任务上平均超过强化学习基线 6 个百分点、最高 19pp，同时采样（rollout）最多减少 35 倍——轨迹反思的样本效率是其核心论点。**（S-0047，official）
  - 出处：https://proceedings.iclr.cc/paper_files/paper/2026/hash/0e9e708b6f48e14fd0ac29e167413f76-Abstract-Conference.html
  - 原文关键句：Across six tasks, GEPA outperforms GRPO by 6 percentage points on average and by up to 19pp, while using up to 35x fewer rollouts.
- **DSPy 的 SIMBA 把「让模型分析自身表现并生成改进规则」写成明确的优化器行为，说明反思式进化已有可直接调用的工程形态。**（S-0082，official）
  - 出处：https://raw.githubusercontent.com/stanfordnlp/dspy/refs/heads/main/docs/docs/api/optimizers/SIMBA.md
  - 原文关键句：SIMBA ... uses the LLM to analyze its own performance and generate improvement rules. It samples mini-batches, identifies challenging examples with high output variability
- **同一族优化器的收益依赖任务类型与模型规模（MiPROv2 对 CoT 更稳、SIMBA 对 ReAct 与更大模型更有利），因此不能假设换任务后增益照搬。**（S-0052，official）
  - 出处：https://aclanthology.org/2026.findings-eacl.161/
  - 原文关键句：MiPROv2 yielding the most stable gains for CoT, and SIMBA providing the largest benefits for ReAct agents, particularly at larger model scales.

## 术语

- **文本梯度与反思式进化（Textual Gradient and Reflective Evolution）**：以自然语言反馈作为「梯度」逐层改进系统组件（TextGrad），或让模型基于自身执行轨迹反思并生成改进规则（GEPA、SIMBA）。
- **反思与自评回路（Reflection and Self-Critique Loop）**：让模型对自己的输出给出评价并据此改写，形成闭环改进；本节点的反思式进化把它从「改这一次的输出」扩展到「改产生输出的提示与规则」。
- **自动提示词工程（APE）**：由模型自动生成候选指令并按评测指标筛选的优化路线；其候选生成与筛选都需要评测集支撑，是文本梯度与反思式进化的共同祖先。

## 失效模式

- 把反思当成万能改进：在没有评分函数的情况下，模型只会把提示词改得更长更花哨，改动方向无法判定，也无法回滚。
- 轨迹只留最终答案：反思拿不到失败过程，只能对结果猜测原因，生成的改进规则经常指向错误的那一步。
- 评分函数与真实目标脱节：优化器会高效地刷高指标，产出一个在评测集上漂亮、在真实任务上退化的提示词。
- 不留候选与对照记录：无法区分真实增益与采样噪声，容易把一次幸运的运行当成方法有效，后续反复重提同一改动。

## 一句话小结

先建执行轨迹记录与可自动计算的评分函数，再引入文本梯度或反思式的优化回路；候选必须留档并跨过增益阈值才采纳，判定权始终在评分函数与人工复核手里。

## 在本站知识结构中的位置

- 前置：PE-E-06
- 后继：PE-E-08
