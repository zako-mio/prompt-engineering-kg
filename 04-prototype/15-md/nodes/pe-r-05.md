# 步骤回溯与改写变体（Step Backtracking and Rewrite Variants）

- 节点标识：PE-R-05
- 英文名：Step Backtracking and Rewrite Variants
- 所属分组：G02 推理增强
- 依赖深度：第 13 层
- 内容状态：内容已写满
- 标签：推理增强、回溯、改写变体

## 为什么需要它

完整树搜索的代价来自对所有分支都展开并评估，而多数任务只需要其中一小部分收益。步骤回溯把「回到上一步之前的状态重来」这一动作单独拿出来，改写变体则用同一判据筛掉多数不合适的表述，两者都保留了搜索式推理最容易兑现的那部分好处，却不必付出全树评估的成本。它们因此适合放在思维树之前：先用最便宜的方式确认「判据是否可用」，判据不可用时提前止损。

**适用边界**

回溯要求能保存并恢复中间状态、能判断哪一步失败、且有最大回溯次数；改写择优要求能比较候选优劣。三项缺一，回溯就退化为把同一请求重发多次，择优就退化为随机抽取一个候选。

## 机制说明

步骤回溯的机制是保存某一步之前的中间状态，判定该步失败后回到该状态重新展开，而不是从头重算；改写变体是对同一输入生成多个不同表述或不同视角的候选，再按判据择优或合并结果。两类做法共用一个前提：存在可判定的判据。回溯要能回答「这一步是否失败」，择优要能回答「哪个候选更好」。判据可来自外部校验器（测试是否通过、字段是否合法、约束是否满足），也可来自模型自评；外部信号可复现且可写进门控，自评信号便宜但带有系统性偏差，因此优先用外部信号，自评只当补充。工程上还必须把这两类做法与成本上限绑定：设定最大回溯次数与最大候选数，超限即返回当前最优解并记录未收敛样本，否则循环会一直消耗预算而没有任何停止条件。

## 何时该用 / 何时不该用

- 存在外部可验证的中间判据（测试、校验器、模式检查）时：回溯与择优选都能稳定获益，判据越强收益越确定。
- 任务对表述敏感、同一意图有多种合理表达且输出需批量重复时：多候选择优可用投票或判据提高一致性。
- 需要显式控制成本时：把最大回溯次数、最大候选数与 token 预算一并设定，并记录未收敛样本供后续分析。
- 不适用于无判据的场景：没有「失败」与「更好」的判定，两类做法都退化为随机重试，只是把成本乘上倍数。
- 不适用于延迟敏感或高并发的在线请求路径：多候选与回溯串行叠加会成倍放大延迟与 token 成本。

## 实验台

### prompt（markdown）

```markdown
任务：把下面的句子改写为不超过 40 个字的标题，保持原意。
输入：{{text}}
要求：给出 3 个不同表述的候选，每个候选单独成行，行首标注 候选1/候选2/候选3；
不要解释，不要合并候选；若某候选无法满足字数限制，仍要给出并注明「超限」。
输出格式（严格 JSON，无多余文字）：
{"candidates":[{"id":1,"text":"...","over_limit":false}]}
```

预期观察：得到含 3 个候选的 JSON，作为「改写变体」的原料；每个候选可被独立判据检查：汉字数是否超过 40、是否保持原意。判据全过的第一个候选即被择优选中（见下一条 lab 的循环）。

### file（python）

```python
import json, sys

criteria = {"c1": lambda c: len(c.get("text", "")) <= 40,
            "c2": lambda c: c.get("text", "").strip().endswith(("\u3002", "\uff01", "?", "!"))}

def rewrite_variants(question, n=3):
    """\u751f\u6210 n \u4e2a\u6539\u5199\u5019\u9009\uff08\u6a21\u62df\uff1a\u5b9e\u9645\u7528\u6a21\u578b\u591a\u6b21\u91c7\u6837\uff09"""
    return [{"id": i, "text": f"\u5019\u9009{i}\uff1a{question}"} for i in range(n)]

def pick_best(cands, criteria):
    """\u6309\u5224\u636e\u9010\u6761\u7b5b\uff0c\u8fd4\u56de\u7b2c\u4e00\u4e2a\u5168\u90e8\u901a\u8fc7\u7684\u5019\u9009\uff08\u65e0\u5219 None\uff09"""
    for c in cands:
        if all(f(c) for f in criteria.values()):
            return c
    return None

def run(question, max_candidates=3):
    """\u7ed1\u5b9a\u4e0a\u9650\uff1a\u8d85\u9650\u8fd4\u56de\u5f53\u524d\u6700\u4f18 + \u672a\u6536\u655b\u6807\u8bb0"""
    cands = rewrite_variants(question, max_candidates)
    best = pick_best(cands, criteria)
    return {"selected": None if best is None else best["id"],
            "text": None if best is None else best["text"],
            "passed": best is not None,
            "candidates_tried": len(cands),
            "unconverged": best is None}

if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "\u628a\u8fd9\u6bb5\u8bdd\u6539\u5199\u6210\u4e00\u4e2a\u6807\u9898"), ensure_ascii=False))

```

预期观察：运行 python3 rewrite_loop.py <句子> 输出一行 JSON 且 candidates_tried=max_candidates（上限生效）；存在通过判据的候选时返回第一个通过者（如 python3 rewrite_loop.py 把这句话改写成标题。 ⇒ {"selected": 0, "passed": true, "unconverged": false}）；全部候选都不通过时 passed=false、unconverged=true、selected=null，即超限即停止而不是无限重试。

## 证据

- **官方工作流模式清单把「并行化（分节 / 投票）」与提示词链、路由等并列为独立模式，说明多候选加投票择优是官方承认的一等做法，而非临时技巧。**（S-0005，official）
  - 出处：https://www.anthropic.com/engineering/building-effective-agents
  - 原文关键句：Workflows are systems where LLMs and tools are orchestrated through predefined code paths. ... Parallelization (Sectioning / Voting)
- **多候选采样的历史收益有具体数字，说明「生成多个候选再择优」不是零收益的仪式。**（S-0057，paper）
  - 出处：https://arxiv.org/abs/2203.11171
  - 原文关键句：self-consistency boosts ... GSM8K (+17.9%), SVAMP (+11.0%), AQuA (+12.2%), StrategyQA (+6.4%) and ARC-challenge (+3.9%)
- **在 2026 前沿模型的一个多模型实测里，把候选数提到 N=5 时准确率反而从 78% 降到 74.3%，说明候选数与判据必须按模型实测，不能照搬常数。**（S-0059，paper）
  - 出处：https://arxiv.org/abs/2601.06423
  - 原文关键句：Claude Opus 4.5 tells a completely different story. Its accuracy actually drops from 78% to 74.3% while faithfulness jumps dramatically from 0.270 to 0.891 at N=5.

## 术语

- **校验与修复回路（Validation and Repair Loop）**：把输出交给校验器判定，失败即把校验错误回灌重试，并在达到最大重试次数时停止；它是步骤回溯在输出层的对应物，代价上限由重试次数显式给定。
- **自一致性（Self-Consistency）**：对同一输入做多次采样再对结果做多数投票的集成做法，属于「改写变体 + 择优」在答案层的特例；其收益依赖任务是否存在多条合理路径，因此须按任务与模型实测再定候选数。

## 失效模式

- 无判据的回溯：没有「失败」的判定，代码只是在重发同一请求，成本翻倍而质量不变，最终还得靠人工挑。
- 回溯点选得过早：把状态恢复到太靠前的位置，等于丢掉已经正确的中间结论重新推理，成本高于从头做一遍。
- 候选数不设上限：候选与重试数量线性推高 token 成本与延迟，而收益在少数候选之后通常不再增长。
- 只靠模型自评择优：自评存在冗长偏好与自我偏好，会优先选中「看起来完整」而非「真的正确」的候选。
- 超限静默放弃：达到最大次数后直接返回失败而不记录未收敛样本，问题被隐藏，后续无法区分「难」与「判据坏了」。

## 一句话小结

步骤回溯与改写择优是思维树的轻量替代：前者依赖可恢复的中间状态与失败判据，后者依赖能比较候选优劣的判据。两类做法都须绑定重试与候选上限并记录未收敛样本；无判据或延迟敏感时退回单路生成。

## 在本站知识结构中的位置

- 前置：PE-R-04
- 后继：PE-R-06
