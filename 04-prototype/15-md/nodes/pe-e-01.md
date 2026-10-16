# 为什么必须先建评测集（Why Build an Eval Set First）

- 节点标识：PE-E-01
- 英文名：Why Build an Eval Set First
- 所属分组：G05 评测与自动优化
- 依赖深度：第 10 层
- 内容状态：内容已写满
- 标签：评测、评测集、判据

## 为什么需要它

没有评测集，任何「提示词变好了」的判断都不可复现，而不可复现的判断无法在换模型、换数据、换同事之后继续成立；日常提示词工作里最常见的内耗，正是几个人各自凭印象争论哪版更好。有了带判据的样本，改动好坏才变成一个可以复跑出数字的问题。先建评测集是把提示词工作从个人经验变成工程实践的那条分界线。

**适用边界**

评测集只覆盖被采样到的失败模式，未被覆盖的失败仍会漏过；因此它需要随真实故障持续增补，而不是一次建好长期使用。

## 机制说明

评测集的最小形态是一组输入、期望输出与判据三件套，其中判据决定评测集的价值上限。判据分两类：确定性判据（字段是否合法、是否包含指定内容、是否命中正则）与模型辅助判据（相似度、评分准则、事实一致性）。确定性判据可复现、成本低，应优先使用；模型辅助判据用于覆盖无法机械判定的质量标准，但须注意其自身偏差。组织方式建议按失败模式分层，而不是随机抽样：每层对应一类已知问题，层内样本量服从该问题的实际发生率。工程上还应把评测集与提示词一起版本化，使每次改动都有可比基线。

## 何时该用 / 何时不该用

- 开始优化提示词之前：先建最小评测集，否则改动不可比较，只能靠印象判断好坏。
- 多人或多轮改动之后：把评测集当基线复跑，用通过率变化代替口头结论。
- 不适用于把它当一次性交付：不随真实故障增补样本的评测集会逐渐失真。
- 不适用于把「提示词更好」当成未证前提：若成功标准未定义、任务定义还在反复变动，先固化成套样本与判据会把早期的错误形态一起冻结。

## 实验台

### shell（bash）

```bash
# 最小评测集：同一批输入上比较「基线提示词」与「候选提示词」
npx promptfoo@latest eval -c promptfooconfig.yaml --no-cache
# promptfooconfig.yaml 骨架：
#   prompts: [prompt-baseline.txt, prompt-candidate.txt]
#   providers: [<你的模型>]
#   tests:
#     - vars: { input: "<一条代表性输入>" }
#       assert:
#         - type: is-json
#         - type: contains
#           value: "<必须出现的字段名>"
```

预期观察：两条提示词在同一批样本上各得一个通过率；先记录基线，再改提示词重跑，差值才是改动效果。若两边都 100%，说明判据太松或样本太易，应先加负例与边界例。

### file（markdown）

```markdown
维护 `eval-set.md` 三张表：
1. 样本表：样本 id / 输入 / 期望输出或判据 / 来源（真实故障、构造、对抗）
2. 失败模式表：模式名 / 对应样本 id / 当前通过率 / 上次变化时间
3. 基线表：提示词版本号 / 评测集版本 / 通过率 / 结论
规则：每次线上故障都必须落到某个失败模式层并新增样本；没有新增样本的故障复盘不算完成。
```

预期观察：读者能凭三张表回答「这次改动是否真的变好」与「当前最薄弱的失败模式是哪一层」，而不是凭记忆回答。

## 证据

- **官方把「成功标准」与「失败的评测」放在提示工程之前：先界定判据，再决定该改提示词还是该换模型。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.
- **一次提示词瘦身的收益是在内部评测集上量出来的：评测分数提升 10–15%，同时 token 与成本大幅下降——没有评测集这类改动无法被证实。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：In a sample of internal coding-agent eval runs, configurations with leaner system prompts improved evaluation scores by roughly 10–15% while reducing total tokens by 41–66% and cost by 33–67%.
- **先建评测集必然要先给判据分类：确定性判据（equals / contains / regex / is-json 等）与模型辅助判据（llm-rubric / factuality 等）是两条不同的实现路径。**（S-0077，official）
  - 出处：https://www.promptfoo.dev/docs/configuration/expected-outputs/
  - 原文关键句：Deterministic eval metrics: equals / contains / icontains / regex / is-json / javascript ... Model-assisted: similar / classifier / moderation / llm-rubric / g-eval

## 术语

- **评测集（Eval Set）**：带判据的一组代表性输入输出样本，是判断提示词改动是否真的变好的唯一依据；先建评测集再做优化。
- **门控即判据（Gate as Executable Criterion）**：把「这次改动是否可接受」写成可执行的检查脚本并以其退出码作结论，使质量判断可复现、可回归。

## 失效模式

- 跳过评测集直接调提示词：改动效果无法与基线比较，改好改坏都说不清。
- 只用模型辅助判据：判据自身的偏差被当成被测对象的偏差，且每次复跑成本更高。
- 评测集一次建好长期不动：它固化了旧失败模式，新故障没有样本承接，整体分数好看而线上继续坏。
- 只收典型正例：误拒与过度保守这类失败永远不会被这批样本暴露。

## 一句话小结

先把判据与样本落成可复跑的评测集，再让每次提示词改动同基线相比，并随故障增补。

## 在本站知识结构中的位置

- 前置：PE-C-04
- 后继：PE-E-02
