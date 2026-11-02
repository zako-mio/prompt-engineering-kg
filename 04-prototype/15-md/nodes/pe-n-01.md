# 三代范式脉络（Three-Generation Paradigm Arc）

- 节点标识：PE-N-01
- 英文名：Three-Generation Paradigm Arc
- 所属分组：GD-N 新一代模块
- 依赖深度：第 26 层
- 内容状态：内容已写满
- 标签：新一代模块、范式脉络、框架

## 为什么需要它

把 2020 到 2026 分成三代，不是为了记年份，而是为了判断当前的主要矛盾在哪一层：写指令、组织上下文、还是编排与编译。有了这条脉络，读者才能理解为什么「提示词工程是否已死」是个错误问题——它没有被替代，而是被叠加了上下两层。

**适用边界**

三代划分是分析框架而非历史事实的精确分期，各代的时间边界在文献中并不一致，且三代在不同组织与不同任务上的推进速度差别很大。

## 机制说明

第一代是提示词工程时代，焦点是单次调用的指令写法与手工推理技巧；第二代是上下文工程时代，焦点是把正确的动态知识放进窗口，手段包括检索、图检索、长文本压缩与位置优化；第三代是编排与编译时代，焦点是把模型当作组件去编排、用协议标准化外部接入、用编译器自动生成配置。三代之间是叠加关系：第三代仍然需要前两代的全部能力，只是主要矛盾上移。

## 何时该用 / 何时不该用

- 判断学习与工程投入方向时：先定位当前瓶颈属于哪一代的问题。
- 向他人解释提示词工程现状时：用三代脉络说明它是叠加而非替代。
- 不适用于把三代当精确分期：文献中的时间边界并不一致。
- 不适用于跳过前两代直接做第三代：瓶颈在检索时，编排不解决问题。

## 实验台

### file（python）

```python
# gen_probe.py —— 三代对照：同一任务的三版实现各测一次，判定瓶颈落在哪一代
import csv, json, pathlib

ROWS = pathlib.Path("gen-probe") / "measure.csv"
COLS = ["variant", "accuracy", "in_tokens", "out_tokens", "latency_s"]
ORDER = ["g1_prompt", "g2_context", "g3_orchestration"]

rows = list(csv.DictReader(open(ROWS, encoding="utf-8")))
assert list(rows[0].keys()) == COLS, list(rows[0].keys())
assert [r["variant"] for r in rows] == ORDER, [r["variant"] for r in rows]
acc = {r["variant"]: float(r["accuracy"]) for r in rows}
gain = {v: round(acc[v] - acc[ORDER[0]], 4) for v in ORDER}
bottleneck = max(gain, key=gain.get)
monotonic = acc[ORDER[0]] <= acc[ORDER[1]] <= acc[ORDER[2]]
print(json.dumps({"gain": gain, "bottleneck": bottleneck, "monotonic": monotonic},
                 ensure_ascii=False))
```

预期观察：脚本正常退出并打印一行 JSON，其中包含 gain（三键齐全）、bottleneck（取值必为 g1_prompt / g2_context / g3_orchestration 之一）与 monotonic（true 或 false）三个键；measure.csv 缺行或列名不符时脚本以 AssertionError 退出。

### shell（bash）

```bash
set -eu
mkdir -p gen-probe && cd gen-probe
printf 'variant,accuracy,in_tokens,out_tokens,latency_s\n' > measure.csv
for v in g1_prompt g2_context g3_orchestration; do
  python3 run_eval.py --variant "$v" --model fixed-model --seed 7 --repeat 5 --csv >> measure.csv
done
wc -l measure.csv
```

预期观察：measure.csv 恰为 4 行（1 行表头加 3 行），wc -l 打印 4；三行 variant 依次为 g1_prompt、g2_context、g3_orchestration，且任一版本评测失败时脚本以非零退出码中止。

## 证据

- **厂商侧把上下文工程定义为提示工程的自然演进，二者是继承关系而非替代关系。**（S-0004，official）
  - 出处：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：we view context engineering as the natural progression of prompt engineering. Prompt engineering refers to methods for writing and organizing LLM instructions
- **第二代的工程手段可归为三类具体动作：为单个 agent 隔离上下文、跨多步持久化信息、压缩大数据量。**（S-0019，official）
  - 出处：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- **第三代把外部接入收敛为协议层规范：MCP 改为无状态，每个请求自带协议版本与客户端能力。**（S-0022，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - 原文关键句：Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request now carries its protocol version and client capabilities in `_meta`

## 术语

- **三代范式脉络（Three-Generation Paradigm Arc）**：2020-2023 提示词工程、2023-2025 上下文工程、2025-2026 编排与编译三个相继阶段；三者是叠加而非替代关系。
- **上下文工程（Context Engineering）**：在推理时点管理与筛选进入上下文窗口的全部 token（含工具定义、MCP、外部数据、消息历史、记忆），目标是维持一组最小的、高信噪比的 token 集。

## 失效模式

- 把三代当成精确分期：文献里的时间边界并不一致，按年份切分会让某个技巧属于哪一代无法定论，进而误判当前瓶颈在写指令还是在组织上下文。
- 跳过前两代直接上编排：瓶颈仍在检索或压缩时，改编排不会改变准确率，投入被花在不产生增益的那一层上。
- 只比较工具是否流行而不测指标：会得到升级了却没变好的结论，却无法定位瓶颈落在哪一代，下一轮投入仍然靠猜。
- 把叠加读成替代：删掉提示词层与上下文层的基础功之后改编排，准确率通常反而下降，因为上层依赖下层提供的输入质量。

## 一句话小结

三代是叠加而非替代关系；先定位当前瓶颈落在哪一代，再决定投入方向。

## 在本站知识结构中的位置

- 前置：无
- 后继：PE-N-02
