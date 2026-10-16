# 评测工具链与红蓝对抗（Evaluation Toolchain and Red Teaming）

- 节点标识：PE-E-04
- 英文名：Evaluation Toolchain and Red Teaming
- 所属分组：G05 评测与自动优化
- 依赖深度：第 19 层
- 内容状态：内容已写满
- 标签：评测、工具链、红蓝对抗

## 为什么需要它

评测若只靠一次性人工抽查，就无法回答「这次改动是否变好」，也无法回答「这次改动是否打破了既有行为」。工具链把这两问变成可重复执行的命令：本地批量评测在改动时跑，持续集成回归在提交时跑固定子集，对抗评测在安全改动或定期巡检时跑。红蓝对抗是其中的安全侧，它同时度量拦截率与过拒率——缺任何一侧，防御调优都会朝「多拦一点总没错」的方向漂移。

**适用边界**

只测拦截率会奖励过度保守的防御，必须把过拒率纳入同一份报告，否则「把正常请求也拦下」会被当成成绩；同理，工具方自述的「被谁使用」不能当作选型依据，选型必须先在自己的评测集上端到端跑通一条回归。

## 机制说明

评测工具链的能力面可以按断言类型划分：确定性断言覆盖相等、包含、正则、JSON 合法性、脚本、延迟、成本与工具调用相关指标；模型辅助断言覆盖相似度、分类器、评分准则、答案相关性与上下文忠实度。任意断言通常都可加 not- 前缀取反，于是「必须不出现」这类负向要求也能被机械表达。工程落地分三层：本地批量评测在改动时跑，持续集成回归在提交时跑固定子集，对抗评测在安全改动或定期跑。红蓝对抗的产出应包含两列——攻击成功率与正常请求拒绝率，两者共同构成防御质量画像。生态现状是：没有一手来源给出「默认选择」的排他口径，工具方自述只能当能力面参考，选型要回到自己的评测集与断言需求上。

## 何时该用 / 何时不该用

- 需要把评测纳入日常流程时：按本地批量评测、持续集成回归、对抗评测三层组织，各层跑不同的样本子集与运行频率。
- 执行安全改动或定期巡检时：跑对抗评测，并同时记录攻击成功率与正常请求拒绝率两个指标。
- 不适用于只测拦截率：单一指标会奖励过度保守的防御，把可用性损失误读成安全收益。
- 不适用于把工具选型当结论：生态无一手「默认选择」依据，应先定义自己的断言集合再选工具。

## 实验台

### shell（bash）

```bash
npx promptfoo@latest eval -c promptfooconfig.yaml --output results.json
# 断言里同时放正向与负向，负向用 not- 前缀：
#   assert:
#     - {type: contains, value: OK}
#     - {type: not-contains, value: 内部编号}
python3 - <<'PY'
import json
s = json.load(open('results.json'))['results']['stats']
print('successes=%s failures=%s' % (s['successes'], s['failures']))
PY
```

预期观察：命令退出码为 0，并打印出断言通过数与失败数两项计数；把同一命令放进持续集成后，任一断言失败即以非 0 退出，回归在提交时被自动拦下。

### file（markdown）

```markdown
# 对抗评测报告（两列缺一不可）

| 指标 | 数值 | 口径 |
|---|---|---|
| 攻击样本数 | 200 | 攻击方构造的注入、越狱等恶意输入 |
| 拦截率 | __% | 恶意输入被正确拒绝的比例 |
| 过拒率 | __% | 正常请求被误拒的比例 |
| 误拒样例 | top-5 | 逐条人工复核后回写判据 |
```

预期观察：报告同时给出拦截率与过拒率两行；只填拦截率的版本在评审时不予通过，因为无法排除用「把正常请求也拦下」换来的高拦截率。

## 证据

- **断言在工具链里是可机械判定的检查项，且可加 not- 前缀取反，使「必须不出现」这类负向要求也能自动判定。**（S-0077，official）
  - 出处：https://www.promptfoo.dev/docs/configuration/expected-outputs/
  - 原文关键句：Deterministic eval metrics: equals / contains / icontains / regex / is-json / javascript / python / webhook ... Every test type can be negated by prepending `not-`
- **该评测工具自述同时覆盖提示词/Agent/RAG 测试与红队渗透扫描，并声称被 OpenAI 与 Anthropic 使用；这是厂商自述，只能作为能力面参考。**（S-0087，official）
  - 出处：https://api.github.com/repos/promptfoo/promptfoo
  - 原文关键句："stargazers_count":25996 ... "license":{"spdx_id":"MIT"} ... "Test your prompts, agents, and RAGs. Red teaming/pentesting/vulnerability scanning for AI. ... Used by OpenAI and Anthropic."
- **同类评测框架按单元测试形态组织（pytest 风格），说明工具链侧已把断言、判定与回归当作软件测试原语来复用。**（S-0096，official）
  - 出处：https://pypi.org/pypi/deepeval/4.0.0/json
  - 原文关键句："license":"Apache-2.0" ... "similar to Pytest but specialized for unit testing LLM apps" ... MCP Metrics: MCP Task Completion / MCP Use / Multi-Turn MCP Use

## 术语

- **红蓝对抗（Red Teaming）**：由攻击方构造注入、越狱等恶意输入，检验防御方实际拦截率与过拒率的对抗式评测。
- **过拒（Over-refusal）**：安全策略过严导致正常请求被拒绝的现象；它与拦截率构成安全—可用性权衡，须双向度量而非只优化一侧。

## 失效模式

- 只报拦截率：防御被调成宁枉勿纵，正常请求大面积被拒，可用性损失被计成安全收益。
- 断言只用模型裁判：位置偏差与冗长偏好进入回归曲线，改动方向被系统性带偏而无人察觉。
- 评测脚本只在本地手动跑：评测不进持续集成，回归在提交时无人执行，无声退化要等用户发现才暴露。
- 把工具方自述当选型依据：把「被某厂商使用」读成事实上的默认选择，跳过在自己评测集上的端到端验证。

## 一句话小结

评测按本地批量、集成回归、对抗评测三层落地，对抗层必须同时报告攻击成功率与过拒率，选型回到自己的断言需求。

## 在本站知识结构中的位置

- 前置：PE-E-03
- 后继：PE-E-09
