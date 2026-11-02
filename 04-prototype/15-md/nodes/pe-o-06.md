# 状态机与持久化（State Machine and Persistence）

- 节点标识：PE-O-06
- 英文名：State Machine and Persistence
- 所属分组：G04 编排
- 依赖深度：第 13 层
- 内容状态：内容已写满
- 标签：编排、状态机、持久化

## 为什么需要它

长时程任务的进度必须显式建模并落盘，否则一次中断就意味着从头开始，而长任务恰恰最容易中断。状态机与持久化把「做到哪一步了」变成可查询、可恢复、可审计的事实。代价是每一步都要定义落点与幂等边界，否则恢复会把已经发生的副作用再执行一次。

**适用边界**

状态粒度需要权衡：过粗会丢失进度，过细会推高写入与恢复成本；对短任务引入状态机只会增加复杂度而无收益。

## 机制说明

状态机的设计包含四个决定：状态集合（有哪些阶段）、转移条件（什么情况进入下一状态）、持久化介质与频率（多久落一次盘）、以及恢复语义（重启后从哪继续、已完成步骤是否重放）。工程实践中最常见的缺陷是恢复语义不明确：重启后重放已产生副作用的步骤，造成重复写入或重复调用。解决办法是给每个有副作用的步骤加幂等标识，使重放安全。此外，状态记录本身也是可观测性资产：它能回答「卡在哪一步、失败几次、哪一步最慢」，这些信息是优化链条与编排的直接依据。现行框架把持久化拆成两层：检查点按线程保存图状态并在每个超步落盘，使会话延续、人工介入、回溯与容错都建立在同一份状态记录上；应用级数据（偏好、事实、共享知识）则放在图状态之外的存储里，两层混用会让恢复读到过期数据。

## 何时该用 / 何时不该用

- 任务需要跨多次调用或跨越人类审批节点时：必须显式建模状态并持久化。
- 有副作用步骤时：为每步加幂等标识，使恢复可安全重放。
- 不适用于短任务：状态机只会增加复杂度而无收益。
- 不适用于恢复语义未定义就上线：重放副作用会造成重复写入。

## 实验台

### shell（python）

```python
# state_machine.py
import json, pathlib

CKPT = pathlib.Path("ckpt.json")


def load():
    if CKPT.exists():
        return json.loads(CKPT.read_text(encoding="utf-8"))
    return {"step": 0, "done": []}


def run(steps):
    st = load()
    for i, (key, fn) in enumerate(steps, 1):
        if key in st["done"]:
            continue
        fn()
        st["done"].append(key)
        st["step"] = i
        CKPT.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return st


steps = [("step1", lambda: print("extract")), ("step2", lambda: print("load"))]
run(steps)
run(steps)
print(load())
```

预期观察：连续两次 run 只打印一次 extract 与 load，ckpt.json 的 done 仍为 step1 与 step2 两项且无重复。

### shell（bash）

```bash
rm -f ckpt.json; python3 state_machine.py; python3 state_machine.py; cat ckpt.json
```

预期观察：第二次运行没有任何步骤输出，ckpt.json 的 done 数组长度仍为 2，证明重跑未追加重复步骤。

## 证据

- **该框架把检查点的作用界定为按线程持久化图状态，并让会话延续、人工介入与容错共用同一份状态记录。**（S-0123，vendor）
  - 出处：https://docs.langchain.com/oss/python/langgraph/persistence
  - 原文关键句：Checkpointers persist a thread’s graph state as checkpoints. ... including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
- **同一文档把应用定义的数据（偏好、事实、共享知识）排除在图状态之外，说明检查点与存储是两层独立的持久化。**（S-0123，vendor）
  - 出处：https://docs.langchain.com/oss/python/langgraph/persistence
  - 原文关键句：Stores persist application-defined data outside the graph state. ... including user preferences, facts, and shared knowledge.

## 术语

- **状态机与持久化（State Machine and Persistence）**：把长时程任务的进度显式建模为状态并落盘保存，使流程可中断、可恢复、可审计。
- **校验与修复回路（Validation and Repair Loop）**：对模型输出做结构或语义校验，失败则把校验错误回灌给模型重试，直至通过或达到重试上限。

## 失效模式

- 恢复时重放已产生副作用的步骤：重复下单或重复扣款，外部系统的账目与本地的进度对不上。
- 检查点只在任务结束时落盘一次：中断等于零进度，长任务被迫从头重跑，持久化形同虚设。
- 把会话状态与用户偏好数据混在同一份存储：恢复时读到过期偏好，去重与续跑判断同时失真。
- 状态机只保留成功与失败两态：重试与人工介入无法区分，流程卡住时判断不出该继续还是该终止。

## 一句话小结

长任务必须显式建模状态并定义恢复语义，副作用步骤要可安全重放。

## 在本站知识结构中的位置

- 前置：PE-O-05
- 后继：PE-O-07
