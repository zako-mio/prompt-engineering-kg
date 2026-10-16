# 指令的具体性与可验证性（Instruction Specificity and Verifiability）

- 节点标识：PE-F-05
- 英文名：Instruction Specificity and Verifiability
- 所属分组：G00 地基：模型是概率采样器
- 依赖深度：第 4 层
- 内容状态：内容已写满
- 标签：地基、指令设计、可验证性

## 为什么需要它

指令写得越细不一定越好：在新一代模型上，过度具体的手写步骤反而会降低效果，因为模型对模糊与细微差别的处理能力已经提高。真正需要的是可验证性——把「做到什么算完成」写成可判定的条件，而不是把「怎么做」写成操作手册。

**适用边界**

「偏好一般性指令」针对的是推理能力已被底座内化的任务；在需要严格流程合规的场景（审计、合规流水线）里，显式步骤仍然是必要的，此时应把步骤写成可检查的产出条件而非叙述。

## 机制说明

指令质量可以从两个维度拆开：具体性（说了多少细节）与可验证性（结果能否被判定）。现行厂商口径在具体性上整体向「更一般」移动：偏好一般性指令而非规定性步骤，理由是模型的推理常常超出人类预先规定的步骤；同时把「只写一次、不重复指令」列为反堆砌原则。在可验证性上则相反，要求把输出形态、判定标准与失败条件写清，因为那是自动化校验的前提。二者并不矛盾：一般性针对的是推理路径，可验证性针对的是交付契约。

## 何时该用 / 何时不该用

- 需要自动化校验输出时：把输出形态与判定条件写成可判定的契约。
- 推理类任务上：给目标与约束，少写规定性步骤，避免限制模型的推理路径。
- 不适用于合规与审计流水线：需要流程可追溯时，显式步骤仍是必要产出。
- 不适用于把「具体」等同于「长」：重复同一指令只增加 token，不增加约束力。

## 实验台

### file（markdown）

```markdown
把一条模糊指令改写成可验证契约，逐项填表
  原句 | 输出形态（交付物长什么样） | 判定条件（怎样算通过） | 失败条件（出现什么就是没做到） | 是否可自动校验
判据：三列齐全才算契约成立；只剩「输出形态」的是格式要求，不是契约。
不得把「尽量好」「专业一点」这类词写进判定条件——它们不可判定，等于没有判据。
```

预期观察：读者能写出能被脚本校验的交付契约，并意识到「可验证性」与「具体性」是两个独立维度。

### shell（bash）

```bash
# 同一任务两种写法：A 规定性步骤（先做 1、2、3） / B 目标 + 约束 + 可验证契约
# 用同一个校验脚本对两版输出打分，各跑 20 次
for style in prescriptive layered; do
  echo "== style=$style =="
  for i in $(seq 1 20); do
    run_task "$style" | validate_contract.py -
  done | awk '{p+=$1} END {print "通过率", p/NR}'
done
```

预期观察：在推理型任务上 B 版通过率不低于 A 版、token 更少；若 A 版更好，说明该任务其实需要严格流程（审计类），那就把步骤改写成可检查的产出条件而不是删掉步骤。

## 证据

- **现行官方口径承认：过度具体的指导在新一代模型上会由助力转为阻力——这是「指令具体性整体向更一般移动」的一手依据。**（S-0013，official）
  - 出处：https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  - 原文关键句：Models have gotten much better at understanding nuance and ambiguity, so overly specific guidance can now hinder results where it previously helped.
- **官方明确偏好一般性指令而非规定性步骤，理由是模型的推理常常超出人类预先规定的步骤。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Prefer general instructions over prescriptive steps. A prompt like "think thoroughly" often produces better reasoning than a hand-written step-by-step plan.
- **官方把「可验证性」的边界摆在台面上：并非所有成功标准或失败的评测都最适合用提示工程解决，换模型有时更省力——所以先判断这个失败到底该不该由提示工程承担。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.

## 术语

- **指令的具体性与可验证性（Instruction Specificity and Verifiability）**：指令应写到可被判定的程度：明确输出形态、判定标准与失败条件，使结果可被自动化校验而非靠人工观感。

## 失效模式

- 把「具体」等同于「长」：重复同一指令只增加 token 与注意力消耗，不增加任何约束力。
- 把「一般性」当成「模糊」：一般性针对推理路径，交付契约仍必须可判定；写成「尽量好」就无法自动校验。
- 在合规与审计流水线上照搬「少写步骤」：需要流程可追溯的场景里显式步骤是必要产出，只是要写成可检查的条件。
- 只写成功标准、不写失败条件：出错时无法区分「没做到」与「没测到」，评测集也无法定位回归。

## 一句话小结

目标与约束写到可判定，方法提示尽量克制，并且不重复同一指令。

## 在本站知识结构中的位置

- 前置：PE-F-04
- 后继：PE-F-06
