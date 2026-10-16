# 技能文件编写（Authoring Skill Files）

- 节点标识：PE-P-02
- 英文名：Authoring Skill Files
- 所属分组：G09 落地实践
- 依赖深度：第 17 层
- 内容状态：内容已写满
- 标签：落地实践、技能文件、渐进式披露

## 为什么需要它

技能文件是把自己的工作方法固化成可复用资产的载体，它决定了 agent 在什么情况下会用到某套方法、以及用到多少。写法上有一条被现行官方口径直接推翻的经验：过去有效的「详尽操作手册式技能」在新一代模型上反而会降低效果，因此技能文件必须改成短触发加按需展开。

**适用边界**

这条反转针对的是具备较强指令理解能力的模型；在能力较弱的模型或需要严格流程合规的场景下，显式步骤仍有必要，此时应把步骤写成可检查的产出条件。

## 机制说明

技能文件的写法包含四个决定：触发描述（什么时候用，应尽可能短且可判定）、要点集合（做什么、不做什么、判据是什么）、展开结构（哪些细节放在主文件、哪些放到按需加载的引用文件）、以及边界声明（适用范围与不适用场景）。现行官方口径给出的两条原则值得直接采用：触发描述要尽可能短，因为它是常驻成本；有用的技能的关键标志之一是渐进式披露。两条原则是一组对冲：主文件越短，常驻占用越低，代价是运行时展开的次数变多；触发描述的判定性比它的信息量更重要。

## 何时该用 / 何时不该用

- 把自己反复使用的做法固化为可复用资产时：用短触发加按需展开的结构。
- 上下文占用需要控制时：把细节移到按需加载的引用文件，主文件只留索引。
- 不适用于照搬旧模型的写法：详尽手册式技能在新模型上可能降低效果。
- 不适用于需要严格流程合规的场景直接删步骤：应把步骤改写为可检查的产出条件。

## 实验台

### file（markdown）

```markdown
---
name: <skill-name>
description: <一句话触发条件：什么时候用这个技能。不超过一到两句，不写操作步骤>
---

# <技能标题>

## 什么时候用
- <可判定的触发条件，逐条列出>

## 要点
- <做什么：3 到 7 条，每条一句话>
- <不做什么：只写必要的少数几条，优先改写成正向描述>

## 判据
- <怎么算做完：可判定的条件>

## 边界
- <适用：……>
- <不适用：……>

## 按需展开
- 细节见 `references/<topic>.md`（仅在需要时读取）
```

预期观察：读者能产出一个主文件只有触发条件、要点、判据、边界与索引的技能；细节全部下沉到引用文件，常驻占用显著下降。

### shell（bash）

```bash
# 对照实验：同一任务，分别用「详尽手册式技能」与「短触发 + 按需展开技能」
# 记录三项指标：任务成功率、技能文件常驻 token、完成任务所需交互轮数
for variant in verbose concise; do
  echo "== variant=$variant =="
  # 用同一批任务跑评测集，输出成功率与 token 占用
  run_skill_eval --skill "$variant" --eval-set ./evals/skill-tasks.jsonl
done
```

预期观察：在具备较强指令理解能力的模型上，concise 变体的成功率不低于 verbose，且常驻 token 与交互轮数应下降；若结果相反，说明目标模型或任务不属于本节点限定的边界，应记录该反例。

## 证据

- **官方现行立场：许多技能曾被写成详尽的操作路线或配方，而模型对细微差别与模糊性的理解已经提高，因此过去有效的过度具体指导如今反而可能损害结果；技能描述应尽可能短，渐进式披露是有用技能的关键标志之一。**（S-0013，official）
  - 出处：https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  - 原文关键句：many skills were written as elaborate itineraries or recipes. Models have gotten much better at understanding nuance and ambiguity, so overly specific guidance can now hinder results where it …
- **生产案例：某工具厂商发现其提示中过去对更早模型有效的若干段落需要重新调优，其中「要彻底」这类强化表述在新模型上被证明适得其反；且构造不良、含矛盾或含糊指令的提示对新模型的伤害比其他模型更大。**（S-0015，official）
  - 出处：https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt-5/gpt-5_prompting_guide.ipynb
  - 原文关键句：Cursor found that sections of their prompt that had been effective with earlier models needed tuning ... <maximize_context_understanding> Be THOROUGH ... they found it counterproductive with GPT-5 …
- **现行官方口径要求把同一指令只写一次，并明确重复指令与示例堆砌属于应删减的内容：在内部编码 agent 评测样本中，更精简的系统提示改善了评分并同时降低 token 与成本（厂商自述内部评测，官方自称方向性）。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Removing repeated instructions and examples and simplifying tool descriptions can improve task performance and token efficiency. In a sample of internal coding-agent eval runs, configurations with …
- **官方对提示工程的边界表述：并非所有成功标准或失败的评测都最适合用提示工程解决——有时换模型能更省力地改善延迟与成本；这条边界同样适用于技能文件的维护决策。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：Not every success criteria or failing eval is best solved by prompt engineering. For example, you can sometimes improve latency and cost more easily by selecting a different model.

## 术语

- **技能文件（Skill File）**：以文件形式固化某类任务的触发条件与操作要点的提示资产；现行口径要求触发描述尽可能短并按需展开细节。
- **渐进式披露（Progressive Disclosure）**：提示资产只在前端暴露最短的触发描述与索引，把细节留到确实需要时再加载，以压低常驻上下文占用。
- **指令的具体性与可验证性（Instruction Specificity and Verifiability）**：指令应写到可被判定的程度：明确输出形态、判定标准与失败条件，使结果可被自动化校验而非靠人工观感。

## 失效模式

- 把技能写成详尽操作手册：在新一代模型上过度具体的指导反而损害结果，并推高常驻 token。
- 用大写与强制语气保证关键指令被执行：现行口径主张回调攻击性语言，生产案例显示强化表述在新模型上适得其反。
- 触发描述写成操作步骤：触发描述是常驻成本，写长会挤占上下文且降低匹配准确度。
- 把细节全部堆在主文件：缺少渐进式披露会让技能无法按需加载，常驻占用居高不下。

## 一句话小结

技能文件走短触发加按需展开：主文件只放触发条件、要点、判据与索引。

## 在本站知识结构中的位置

- 前置：PE-P-01
- 后继：PE-P-03
