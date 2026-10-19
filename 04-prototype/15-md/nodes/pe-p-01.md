# 我的 agent 的提示词面（My Agent's Prompt Surface）

- 节点标识：PE-P-01
- 英文名：My Agent's Prompt Surface
- 所属分组：G09 落地实践
- 依赖深度：第 16 层
- 内容状态：内容已写满
- 标签：落地实践、提示词面、盘点

## 为什么需要它

一个 agent 的行为不只由系统提示决定：工具定义、技能的触发描述、子 Agent 的委派模板、记忆与检索注入、门控判据都在同一时刻影响它。把这些部件合起来称作提示词面，是为了能统一回答三个问题——哪些内容必须常驻、哪些可以按需加载、改动之后要在哪里验证。只盯着系统提示做优化，会漏掉大部分实际在起作用的文本，也会把回归验证做在错误的对象上。

**适用边界**

提示词面的构成随运行时不同而不同，本节点的四层划分与清单来自使用者自己的 agent 运行环境，换一个运行时需要重新盘点，不能直接照搬。

## 机制说明

盘点提示词面按四层进行。常驻层是每一轮都进入上下文的部分，包括系统提示、工具的名称与描述、安全规则；它改动的影响面最大，必须跑全量回归。按需层是技能正文、检索资料与外部文档，只有在触发描述被匹配中之后才展开，因此触发描述本身是常驻成本，必须短且可判定；这也解释了为什么把技能写成详尽行程单的做法已经过时——模型对细微差别与模糊性的理解变好之后，过度具体的分步指导反而会限制它的判断，把技能写成判断准则（做什么、不做什么、怎么算做完）比写成步骤表更稳，细节则交给引用文件承载。传递层是委派给子 Agent 的任务描述与返回契约，要求契约稳定且可被机器检查。判据层是门控脚本、校验器与评测集判据，它们不是给模型看的文本，而是给这次改动下结论的装置。同一处改动会在多处显形：改工具描述会影响工具选择，改技能触发描述会影响技能是否被选中，改系统提示则会影响下游的全部判据。盘点的产出是一张清单，逐部件标注所在位置、注入条件、更新频率与验证方式，这张清单本身就是后续优化的依据。

## 何时该用 / 何时不该用

- 优化 agent 行为前：先盘点提示词面，确认问题出在常驻层、按需层、传递层还是判据层。
- 上下文占用过高时：检查技能正文与检索资料是否被误设为常驻，改用短触发描述加按需展开。
- 不适用于把系统提示当成唯一的优化对象：工具描述、委派模板与记忆注入同样决定行为。
- 不适用于照搬本清单到其他运行时：提示词面的构成随运行时而异，换环境须重新盘点。

## 实验台

### file（markdown）

```markdown
# 提示词面盘点清单（逐部件一行，填完即可看出这面有多大）

| 部件 | 所在位置 | 注入条件 | 更新频率 | 验证方式 |
|---|---|---|---|---|
| 系统提示 | <路径> | 常驻 | 低 | 全量回归 |
| 工具描述 | <路径> | 常驻 | 中 | 工具选择评测 |
| 技能触发描述 | <路径> | 常驻 | 中 | 触发命中率 |
| 技能正文 | <路径> | 按需（被选中后展开） | 高 | 单技能评测 |
| 检索资料 | <路径> | 按需注入 | 高 | 引用正确性抽查 |
| 委派模板 | <路径> | 委派时 | 中 | 返回契约校验 |
| 记忆条目 | <路径> | 按需注入 | 高 | 过期复核 |
| 门控判据 | <路径> | 不注入模型 | 中 | 负向自检 |

## 填完要回答的三个问题
1. 常驻部件的合计占用是多少？
2. 哪些部件本该按需却被设成了常驻？
3. 每个部件改动之后，用哪一条判据证明它变好了？
```

预期观察：读者得到一张覆盖常驻、按需、传递、判据四层的清单，每个部件都写明了注入条件与验证方式；清单里标记为常驻却更新频繁的部件，就是下一步该改成按需加载的对象。

### shell（bash）

```bash
# 量一遍常驻占用：逐个列出常驻层部件，看谁最贵
for f in prompt/system.md prompt/tools/*.json prompt/skills/*/SKILL.md; do
  [ -f "$f" ] || continue
  wc -m "$f"
done

# 按需层只应在被选中后展开：技能正文与引用文件不应出现在常驻清单里
for f in prompt/skills/*/references/*.md; do
  [ -f "$f" ] || continue
  echo "按需：$f"
  wc -m "$f"
done
```

预期观察：输出是一张常驻占用清单：系统提示、工具描述与技能触发描述各占多少字一目了然；若某个技能的正文出现在常驻清单里，就说明它没有被拆成短触发描述加按需引用文件。

## 证据

- **官方把上下文工程定义为推理时点对全部进入上下文窗口的 token 的管理，并明确包含落在提示词之外的信息，因此提示词面不能等同于提示词文本本身。**（S-0004，official）
  - 出处：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference ... including all the other information that may land there outside of the prompts.
- **工具描述被官方明确列为可精简对象，且精简后任务表现与 token 效率同时改善，说明工具描述属于提示词面且值得单独审计。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Removing repeated instructions and examples and simplifying tool descriptions can improve task performance and token efficiency.
- **官方把注入的入口列为直接输入、检索内容、工具输出、中间推理与持久记忆，这些正是提示词面里会被写入的部件，因此记忆与上下文注入必须按不可信内容对待。**（S-0032，official）
  - 出处：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/final/LLM01_PromptInjection.md
  - 原文关键句：whether direct user input, retrieved content, tool output ... persistent memory, alters the model's behavior in ways the application developer did not intend.
- **官方现行立场：技能曾被写成详尽行程单与配方，而过度具体的指导如今反而可能损害结果，因此技能描述应尽可能短。**（S-0013，official）
  - 出处：https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  - 原文关键句：many skills were written as elaborate itineraries or recipes. ... overly specific guidance can now hinder results where it previously helped. ... skill descriptions should be as short as possible

## 术语

- **渐进式披露（Progressive Disclosure）**：提示资产只在前端暴露最短的触发描述与索引，把细节留到确实需要时再加载，以压低常驻上下文占用。
- **工具定义与滥用治理（Tool Definition and Abuse Governance）**：工具的名称、描述与参数模式构成提示词面的一部分；描述含糊会诱发误用，工具过多会诱发滥用与误选。
- **子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）**：主 Agent 向子 Agent 交付的自包含任务描述与其必须回传的结构化结果约定，二者共同决定委派是否可被验证。

## 失效模式

- 把系统提示当成唯一的提示词面：工具描述、技能触发描述、委派模板与记忆条目都没进盘点，改动只在看不见的地方生效。
- 把技能写成详尽行程单：过度具体的分步指导在新一代模型上反而限制判断，同时推高常驻占用。
- 把本该按需的资产设成常驻：技能正文与检索资料挤占每一轮的上下文，成本上升而效果不升。
- 盘点完不写验证方式：清单只剩部件名，改动之后无法判断是否真的变好，盘点退化成目录。

## 一句话小结

提示词面要按常驻、按需、传递、判据四层盘点，每个部件都标出注入条件与验证方式。

## 在本站知识结构中的位置

- 前置：PE-O-08
- 后继：PE-P-02
