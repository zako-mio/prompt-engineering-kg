# 并行化与投票（Parallelization and Voting）

- 节点标识：PE-O-03
- 英文名：Parallelization and Voting
- 所属分组：G04 编排
- 依赖深度：第 10 层
- 内容状态：内容已写满
- 标签：编排、并行化、投票

## 为什么需要它

并行化有两种形态：把任务切成互不依赖的子任务同时处理（分段），或对同一任务多次采样再聚合（投票）。前者主要买延迟，后者主要买鲁棒性。两者都要求先确认任务结构支持并行，否则只是把成本翻倍。

**适用边界**

分段要求子任务之间无顺序依赖且可独立验证；投票要求答案唯一且错误发散，否则聚合无效。

## 机制说明

分段式并行把大任务拆成若干独立子任务，同时处理后合并结果，典型收益是延迟下降，质量取决于切分是否均匀与合并是否无损。投票式并行对同一输入多次采样，再按多数或按判据聚合，收益取决于错误是否发散。工程要点有三条：其一，切分必须按可独立验证的边界，否则合并阶段会成为新的瓶颈；其二，投票的采样数应按边际收益曲线设定，而不是越多越好；其三，聚合环节本身需要判据，无判据的聚合只是把选择权交给了随机。监控侧应分别记录并行带来的延迟收益与质量变化，避免用延迟改善掩盖质量退化。

## 何时该用 / 何时不该用

- 子任务互不依赖且可独立验证时：分段并行能有效降低延迟。
- 答案唯一、错误发散的封闭任务：投票式并行可提升鲁棒性。
- 不适用于子任务有顺序依赖的场景：强行并行会产生错误结果。
- 不适用于无判据的聚合：聚合判据缺失时投票退化为随机选择。

## 实验台

### file（python）

```python
SAMPLES = ["B", "B", "A", "B", "C"]


def vote(xs):
    top = max(set(xs), key=xs.count)
    return top, xs.count(top) / len(xs)


for n in range(1, len(SAMPLES) + 1):
    label, share = vote(SAMPLES[:n])
    print("N=%d 答案=%s 得票占比=%.2f 成本倍数=%d" % (n, label, share, n))

label, share = vote(SAMPLES)
print("最终答案=%s 得票占比=%.2f" % (label, share))
assert share >= 0.6, "得票占比低于 0.6，聚合不可判，应改用外部判据而不是多数裁决"

```

预期观察：输出 N=1 到 N=5 共五行加一行最终答案，末行得票占比为 0.60；把 SAMPLES 改成五条互不相同的答案时 assert 失败并以非 0 退出码结束。

### shell（bash）

```bash
#!/usr/bin/env bash
set -euo pipefail
TASKS='[{"id":"a","needs":[]},{"id":"b","needs":[]},{"id":"c","needs":["a"]}]'
python3 - "$TASKS" <<'PY'
import json
import sys

tasks = json.loads(sys.argv[1])
blocked = [t["id"] for t in tasks if t["needs"]]
if blocked:
    sys.exit("拒绝并行：以下子任务有上游依赖 %s" % blocked)
print("可并行：%d 个子任务互不依赖" % len(tasks))
PY

```

预期观察：直接粘贴运行会打印「拒绝并行：以下子任务有上游依赖 ['c']」并以非 0 退出码结束；把 c 的 needs 改成空数组后打印「可并行：3 个子任务互不依赖」并以 0 退出码结束。

## 证据

- **采样数增加带来的准确率增益早期即见顶，部分配置下高采样数反而下降，而 token 成本随采样数近似线性增长。**（S-0058，paper）
  - 出处：https://arxiv.org/abs/2511.00751
  - 原文关键句：while token costs scale nearly linearly with sample count. Critically, performance plateaued early and in some configurations declined at high sample counts
- **同样 N=5 的投票设置在部分模型上准确率从 78% 降到 74.3%，所以采样数必须逐模型实测，不能按跨模型惯例设定。**（S-0059，paper）
  - 出处：https://arxiv.org/abs/2601.06423
  - 原文关键句：Claude Opus 4.5 tells a completely different story. Its accuracy actually drops from 78% to 74.3% while faithfulness jumps dramatically from 0.270 to 0.891 at N=5.
- **自一致性在部分封闭答案基准上的提升达两位数，而在较容易的基准上只有个位数，投票收益随任务难度下降而收缩。**（S-0057，paper）
  - 出处：https://arxiv.org/abs/2203.11171
  - 原文关键句：self-consistency boosts ... GSM8K (+17.9%), SVAMP (+11.0%), AQuA (+12.2%), StrategyQA (+6.4%) and ARC-challenge (+3.9%)

## 术语

- **自一致性（Self-Consistency）**：以高温并行采样多条推理路径并对最终答案做多数投票的集成方法；其收益在现代模型上趋于饱和，且在部分模型上符号可能翻转。

## 失效模式

- 按任务阶段而不是按可独立验证的边界切分并行：合并阶段成为新瓶颈，省下的延迟被合并与返工抵消。
- 投票采样数按惯例固定：成本随采样数近似线性增长，而准确率早已见顶，多出的调用换不到可测的收益。
- 聚合没有判据只做多数裁决：答案不唯一或错误同向时，多数会把同一个错误放大成共识。

## 一句话小结

分段买延迟、投票买鲁棒性，两者都要先确认任务结构与聚合判据。

## 在本站知识结构中的位置

- 前置：PE-O-02
- 后继：PE-O-04
