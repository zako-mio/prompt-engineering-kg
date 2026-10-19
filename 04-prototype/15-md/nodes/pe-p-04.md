# 门控即判据（Gate as Executable Criterion）

- 节点标识：PE-P-04
- 英文名：Gate as Executable Criterion
- 所属分组：G09 落地实践
- 依赖深度：第 22 层
- 内容状态：内容已写满
- 标签：落地实践、门控、判据

## 为什么需要它

质量判断若停在人的观感上就不可复现：同一次改动，换一个人或换一天会得出不同结论，讨论只能靠印象与记忆。把「这次改动是否可接受」写成一条会失败的脚本、用退出码作结论，判断才成为可重复执行的事实；阈值也随之内化在脚本里，想放宽就必须改脚本本身并留下痕迹，而不是在评审时说一句「这次先放过」。

**适用边界**

门控只能判定它被写出来的那些性质，没有被写成判据的性质不会被检查，因此全绿只说明已写下的约束未被违反，不说明质量已经达标；判据面需要随故障复盘与负向自检持续增补，否则它会稳定地漏掉新出现的问题类型。

## 机制说明

一条可用的判据由四件事构成：断言（检查什么）、级别（失败是否阻断）、证据（失败时打印什么才够定位）、负向自检（一个必须让它失败的负例）。判据最常见的三种失效形态都出在这四件事上：其一，恒真：断言的对象是空集，检查从未真正发生，脚本却返回通过，缺的是空集守卫；其二，假绿：判据覆盖的对象少于结论所断言的对象，存量数据恰好落在判据面之外，于是「全绿」被读成「已达标」，判据面必须与结论面同宽；其三，代理判据：目标性质难以直接检查，就退而检查一个容易测的替代物，再把替代物的结果当成结论，而替代物与结论之间那一步从未被验证。数值阈值另有一条纪律：只有当把数据改成符合该阈值会改善内容时，阈值才配当硬判据，否则它只配作报告项逐条打印，因为此时问题在阈值而不在数据。失败输出须给出对象标识、期望与实测三元组，否则失败不可定位；判据也不得为已识别的死代码或死令牌设置豁免，豁免会成为新的漏洞面。门控与评测集互补：评测集回答质量是否变好，门控回答约束是否被违反。

## 何时该用 / 何时不该用

- 把质量要求固化为可复现过程时：每条要求写成一个带负例的判据，并用退出码表达结论。
- 判据失败时：先打印对象标识、期望与实测三元组，再确认被断言的对象是否就是该动的对象。
- 不适用于只写正向断言的门控：没有负例的判据分不清「检查通过」与「检查从未发生」。
- 不适用于为通过而放宽阈值或加豁免：阈值只在改动数据能改善内容时才配当硬判据，否则降为报告项。

## 实验台

### file（python）

```python
def gate(items, limit):
    return all(x["score"] <= limit for x in items)      # 空集时循环体不执行，函数照样返回 True

def gate_guarded(items, limit):
    assert items, "empty set: nothing was checked"      # 空集守卫：没有对象可检时必须失败
    return all(x["score"] <= limit for x in items)

print("unguarded on empty set:", gate([], 5))
try:
    gate_guarded([], 5)
    print("guarded on empty set: PASS (unexpected)")
except AssertionError as e:
    print("guarded on empty set: FAIL:", e)
print("guarded on real data:", gate_guarded([{"score": 3}], 5))
```

预期观察：第一行打印 unguarded on empty set: True，说明没有守卫的判据在空集上恒真；第二行打印 guarded on empty set: FAIL: empty set: nothing was checked，说明守卫把「没有对象可检」变成可见失败；最后一行打印 guarded on real data: True，说明判据在真实数据上仍按预期工作。

### file（python）

```python
rows = [{"id": "a", "ok": True}, {"id": "b", "ok": False}]

scope = rows[:1]                                       # 判据只覆盖第一个对象
print("gate over scope:", all(r["ok"] for r in scope))
print("claim over all rows:", all(r["ok"] for r in rows))
```

预期观察：第一行打印 gate over scope: True：判据只覆盖一个对象且存量数据恰好不触发，于是显示全绿；第二行打印 claim over all rows: False，说明结论所断言的范围大于判据覆盖的范围时，全绿不构成达标结论。

## 证据

- **现行评测工具把判据分为确定性判据与模型辅助判据两档，并把取反做成每个判据类型的一等能力，因此负向自检可以直接复用框架的取反前缀。**（S-0077，official）
  - 出处：https://www.promptfoo.dev/docs/configuration/expected-outputs/
  - 原文关键句：Deterministic eval metrics: equals / ... Model-assisted: similar / classifier / moderation / llm-rubric / g-eval / ... Every test type can be negated by prepending `not-`
- **官方明确并非每条成功判据或失败评测都该由提示工程解决，有时换模型比改提示词更能改善延迟与成本，所以判据失败时要先确认被断言的对象是否就是该动的对象。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.
- **社区级清单把「没有测量结果」明确列为一种真实答案，并指出它与「已判定失效」不是一回事：缺测既不能当通过，也不能当否决。**（S-0112，community）
  - 出处：https://raw.githubusercontent.com/xobotyi/cc-foundry/633188bb7286246bfc7cba3ec2eb2fbf153d4409/plugins/ai-helpers/skills/prompt-engineering/references/superseded-techniques.md
  - 原文关键句："Nothing measured" is a real answer and it is not the same as "dead."

## 术语

- **门控即判据（Gate as Executable Criterion）**：把「这次改动是否可接受」写成可执行的检查脚本并以其退出码作结论，使质量判断可复现、可回归。
- **评测集（Eval Set）**：带判据的一组代表性输入输出样本，是判断提示词改动是否真的变好的唯一依据；先建评测集再做优化。
- **未证实与已证伪之别（Unevidenced vs. Falsified）**：「未被现行厂商实践或权威来源收录」只是证据缺席，「已被反证推翻」才有反证；两者判定不同，混用会让读者把未证实当成已证伪。

## 失效模式

- 恒真判据：断言对象为空集时检查一次都没执行，脚本照样返回通过，问题从未被检查。
- 假绿：判据覆盖的对象少于结论所断言的对象，存量数据恰好不触发，全绿被读成已达标。
- 代理判据：用容易测的替代物代替难以直测的目标性质，替代物与结论之间那一步从未被验证。
- 阈值误升为硬判据：把只影响版式的数值写成阻断条件，为过门控去改数据，反而降低内容质量。

## 一句话小结

把「达标」写成一条会失败的脚本，并为每条判据配一个必须失败的负例，才挡得住恒真、假绿与代理判据这三种退化。

## 在本站知识结构中的位置

- 前置：PE-E-09
- 后继：PE-P-05
