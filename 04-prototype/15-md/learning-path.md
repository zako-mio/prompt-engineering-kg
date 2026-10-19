# 学习路径

按依赖深度（拓扑层）逐层展开全站 67 个节点。层序由边方向推导：A→B 表示先学 A 再学 B。同一层内的节点彼此没有先后约束。

## 第 0 层 · 1 个节点

- PE-F-01 G00 概率采样与确定性边界（Probabilistic Sampling and the Determinism Boundary）

- 为什么在这层：PE-F-01 为起点层，无前置依赖。

## 第 1 层 · 1 个节点

- PE-F-02 G00 系统 / 开发者 / 用户提示词分层（System, Developer, and User Prompt Layering）

- 为什么在这层：PE-F-02 ← PE-F-01（PREREQ）先理解采样与确定性边界，才能理解为什么提示词要按稳定性与权威性分层

## 第 2 层 · 2 个节点

- PE-A-01 G06 指令层级（Instruction Hierarchy）
- PE-F-03 G00 分隔符与上下文隔离（Delimiters and Context Isolation）

- 为什么在这层：PE-A-01 ← PE-F-01（PREREQ）采样器不区分指令与数据这一事实，是指令层级存在的根本原因
- 为什么在这层：PE-A-01 ← PE-F-02（PREREQ）提示词分层是层级在工程上的落点，先学分层再学层级规则
- 为什么在这层：PE-F-03 ← PE-F-02（PREREQ）先有分层心智，才知道需要在文本上划出哪些边界

## 第 3 层 · 2 个节点

- PE-A-02 G06 直接与间接提示词注入（Direct and Indirect Prompt Injection）
- PE-F-04 G00 零样本与少样本（Zero-shot and Few-shot Prompting）

- 为什么在这层：PE-A-02 ← PE-A-01（PREREQ）先有层级概念，才能理解注入为何是「低特权覆盖高特权」
- 为什么在这层：PE-F-04 ← PE-F-03（PREREQ）示例必须包在显式边界内才能与指令区分，故先学分隔符

## 第 4 层 · 1 个节点

- PE-F-05 G00 指令的具体性与可验证性（Instruction Specificity and Verifiability）

- 为什么在这层：PE-F-05 ← PE-F-04（PREREQ）先掌握示例的用法，才能判断哪些内容该写成指令、哪些该用示例表达

## 第 5 层 · 1 个节点

- PE-F-06 G00 注意力预算与上下文衰减（Attention Budget and Context Rot）

- 为什么在这层：PE-F-06 ← PE-F-05（PREREQ）指令写到可判定之后，剩下的约束来自上下文资源本身

## 第 6 层 · 3 个节点

- PE-C-01 G03 上下文即工作内存与四策略（Context as Working Memory and Four Strategies）（架构在册）
- PE-R-01 G02 思维链与零样本思维链（Chain-of-Thought and Zero-shot CoT）
- PE-S-01 G01 结构模式与约束解码（JSON Schema and Constrained Decoding）

- 为什么在这层：PE-C-01 ← PE-F-01（PREREQ）先理解模型如何消费 token，才能理解上下文为何是有限资源
- 为什么在这层：PE-C-01 ← PE-F-06（UPGRADE）从「提示词要精简」升级为「上下文是工作内存，需要主动治理」
- 为什么在这层：PE-R-01 ← PE-F-06（PREREQ）推理增强本质是花更多 token 换质量，须先理解注意力与成本约束
- 为什么在这层：PE-S-01 ← PE-F-06（PREREQ）理解了注意力预算，才会把结构约束下沉到解码层而不是靠指令堆叠

## 第 7 层 · 4 个节点

- PE-C-02 G03 RAG 提示模式（RAG Prompting Patterns）（架构在册）
- PE-M-01 G07 模型分层选型（Model Tiering）
- PE-R-02 G02 范式反转：推理模型上经典技巧掉分（Paradigm Reversal: Classic Techniques Lose Ground on Reasoning Models）
- PE-S-02 G01 三档严格度（Three Tiers of Strictness）

- 为什么在这层：PE-C-02 ← PE-C-01（PREREQ）四策略中「选择」这一支的具体实现就是检索，故先学工作内存框架
- 为什么在这层：PE-M-01 ← PE-C-01（PREREQ）先有上下文与成本的全局观，才谈得上按档位分派模型
- 为什么在这层：PE-R-02 ← PE-F-04（PREREQ）少样本用法的现行变化是范式反转的一部分，须先掌握其基本用法
- 为什么在这层：PE-R-02 ← PE-R-01（PREREQ）先掌握思维链的机制，才能理解它在推理模型上为何掉分
- 为什么在这层：PE-S-02 ← PE-S-01（PREREQ）先掌握约束解码，才能理解三档严格度的差别与代价

## 第 8 层 · 4 个节点

- PE-C-03 G03 图检索与全局观（Graph Retrieval and Global View）（架构在册）
- PE-M-02 G07 标记敏感度的迁移性（Transferability of Markup Sensitivity）
- PE-O-01 G04 提示词链（Prompt Chaining）（架构在册）
- PE-S-03 G01 推理与格式的冲突（Reasoning–Format Conflict）

- 为什么在这层：PE-C-03 ← PE-C-02（PREREQ）先掌握片段级检索的提示模式，再引入需要全局观的图检索
- 为什么在这层：PE-M-02 ← PE-M-01（PREREQ）分层后必然跨模型，标记敏感度的迁移性随之成为问题
- 为什么在这层：PE-O-01 ← PE-R-02（PREREQ）先知道模型内部已能处理多步推理，才能理解链条为何收窄
- 为什么在这层：PE-S-03 ← PE-S-02（PREREQ）先有档位概念，才能讨论强约束与推理能力之间的冲突

## 第 9 层 · 4 个节点

- PE-C-04 G03 检索质量与垃圾进垃圾出（Retrieval Quality and GIGO）（架构在册）
- PE-O-02 G04 路由（Routing）（架构在册）
- PE-S-04 G01 格式选型与词元效率（Format Choice and Token Efficiency）
- PE-V-01 G08 交错输入（Interleaved Input）

- 为什么在这层：PE-C-04 ← PE-C-03（PREREQ）无论哪种检索通道，质量都决定上限，故先建通道再谈质量
- 为什么在这层：PE-O-02 ← PE-O-01（PREREQ）链是单一路径的流程，路由是在多条路径之间选择
- 为什么在这层：PE-S-04 ← PE-S-03（PREREQ）先解决推理与格式的冲突，再在可选格式之间做成本权衡
- 为什么在这层：PE-V-01 ← PE-M-02（PREREQ）多模态交错顺序同样受模型特性影响，先学迁移性再学多模态输入

## 第 10 层 · 5 个节点

- PE-C-05 G03 长上下文位置偏差（Long-context Positional Bias）（架构在册）
- PE-E-01 G05 为什么必须先建评测集（Why Build an Eval Set First）
- PE-O-03 G04 并行化与投票（Parallelization and Voting）（架构在册）
- PE-S-05 G01 校验与修复回路（Validation and Repair Loop）
- PE-V-02 G08 视觉推理链（Visual Reasoning Chain）

- 为什么在这层：PE-C-05 ← PE-C-04（PREREQ）检索质量解决「取到没取到」，位置偏差解决「取到了是否用上」
- 为什么在这层：PE-E-01 ← PE-C-04（PREREQ）检索质量的教训是「先度量再优化」，这正是评测集的作用
- 为什么在这层：PE-O-03 ← PE-O-02（PREREQ）路由决定走哪条路，并行化决定每条路上是否同时跑多份
- 为什么在这层：PE-S-05 ← PE-S-04（PREREQ）格式选定后才谈校验与修复回路的设计
- 为什么在这层：PE-V-02 ← PE-A-01（PREREQ）跨模态指令冲突是层级问题在多模态上的表现
- 为什么在这层：PE-V-02 ← PE-V-01（PREREQ）先构造好交错输入，再引导模型先定位再推断

## 第 11 层 · 5 个节点

- PE-C-06 G03 提示缓存（Prompt Caching）（架构在册）
- PE-E-02 G05 测试集构造（Test Set Construction）
- PE-O-04 G04 编排者—工作者（Orchestrator–Workers）（架构在册）
- PE-R-03 G02 自一致性与多数投票（Self-Consistency and Majority Voting）
- PE-V-03 G08 位置敏感与注意力耗散（Positional Sensitivity and Attention Dissipation）

- 为什么在这层：PE-C-06 ← PE-C-05（PREREQ）位置安排决定了提示的稳定结构，正是缓存可命中的前提
- 为什么在这层：PE-E-02 ← PE-E-01（PREREQ）先建立评测集必要性，再谈如何构造才有区分度
- 为什么在这层：PE-O-04 ← PE-O-03（PREREQ）先掌握并行与聚合，再引入需要拆解与汇总的多工作者结构
- 为什么在这层：PE-R-03 ← PE-O-03（PREREQ）投票在编排层是并行模式，在推理层是自一致性，先学编排侧的一般形态
- 为什么在这层：PE-R-03 ← PE-R-02（PREREQ）先接受单路径推理的边界，再看多路径采样能否补上
- 为什么在这层：PE-V-03 ← PE-C-05（PREREQ）纯文本的位置偏差是理解多模态位置敏感的基础
- 为什么在这层：PE-V-03 ← PE-V-01（PREREQ）交错输入的另一面是位置敏感与注意力耗散，须一并掌握

## 第 12 层 · 3 个节点

- PE-C-07 G03 模型上下文协议（Model Context Protocol）（架构在册）
- PE-O-05 G04 生成者—评估者（Generator–Evaluator）（架构在册）
- PE-R-04 G02 思维树与思维图（Tree of Thoughts and Graph of Thoughts）

- 为什么在这层：PE-C-07 ← PE-A-02（PREREQ）外部数据源接入后，间接注入成为主要攻击面
- 为什么在这层：PE-C-07 ← PE-C-06（PREREQ）先理解稳定前缀与上下文组织，再学把外部数据源标准化接入
- 为什么在这层：PE-O-05 ← PE-O-04（PREREQ）编排者—工作者解决拆分，生成者—评估者解决质量把关
- 为什么在这层：PE-R-04 ← PE-R-03（PREREQ）投票是结构最简单的聚合，思维树是它的结构化升级

## 第 13 层 · 4 个节点

- PE-A-03 G06 大模型应用十大风险（Top 10 Risks for LLM Applications）
- PE-E-03 G05 模型即裁判及其偏差（LLM-as-a-Judge and Its Biases）
- PE-O-06 G04 状态机与持久化（State Machine and Persistence）（架构在册）
- PE-R-05 G02 步骤回溯与改写变体（Step Backtracking and Rewrite Variants）

- 为什么在这层：PE-A-03 ← PE-A-02（PREREQ）理解注入的结构后，再看它在风险清单中的位置与相关条目
- 为什么在这层：PE-A-03 ← PE-C-07（PREREQ）接入外部能力会扩大风险面，须回到风险清单核对
- 为什么在这层：PE-E-03 ← PE-E-02（PREREQ）确定性判据不够用时，才引入模型裁判并处理其偏差
- 为什么在这层：PE-E-03 ← PE-O-05（PREREQ）评估者的可靠性问题正是模型裁判的偏差问题
- 为什么在这层：PE-O-06 ← PE-O-05（PREREQ）先有评估与迭代，才需要把迭代过程固化为可恢复的状态
- 为什么在这层：PE-R-05 ← PE-R-04（PREREQ）先理解完整搜索的代价，再学轻量回溯与改写变体

## 第 14 层 · 2 个节点

- PE-O-07 G04 子 Agent 上下文隔离（Sub-agent Context Isolation）（架构在册）
- PE-R-06 G02 极简推理草稿（Chain of Draft）

- 为什么在这层：PE-O-07 ← PE-O-06（PREREQ）状态是跨调用的事实，子 Agent 隔离是跨上下文的边界，两者配套
- 为什么在这层：PE-R-06 ← PE-R-05（PREREQ）在降低成本的方向上，极简草稿是回溯与变体之外的第三条路

## 第 15 层 · 2 个节点

- PE-O-08 G04 工具定义与滥用治理（Tool Definition and Abuse Governance）（架构在册）
- PE-R-07 G02 ReAct 推理—行动交织（ReAct: Interleaved Reasoning and Acting）

- 为什么在这层：PE-O-08 ← PE-O-07（PREREQ）子 Agent 能做什么由工具定义决定，故先学隔离再学工具治理
- 为什么在这层：PE-R-07 ← PE-R-01（PREREQ）ReAct 的思考环节就是推理，须先掌握推理提示的基本形态
- 为什么在这层：PE-R-07 ← PE-R-06（PREREQ）先掌握把推理压短的技巧，再引入外部反馈驱动的循环

## 第 16 层 · 3 个节点

- PE-A-04 G06 过拒与安全—可用性权衡（Over-refusal and the Safety–Usability Tradeoff）
- PE-P-01 G09 我的 agent 的提示词面（My Agent's Prompt Surface）
- PE-R-08 G02 反思与自评回路（Reflection and Self-Critique Loop）

- 为什么在这层：PE-A-04 ← PE-A-03（PREREQ）清单给出风险面，过拒讨论防御强度与可用性的取舍
- 为什么在这层：PE-A-04 ← PE-E-01（PREREQ）过拒率要被度量才有意义，评测集是它的载体
- 为什么在这层：PE-A-04 ← PE-O-08（PREREQ）工具治理与安全策略共同决定过拒率的高低
- 为什么在这层：PE-P-01 ← PE-O-08（FLOW）工具定义是提示词面的一部分，从编排原理直接落到自身 agent 的盘点
- 为什么在这层：PE-R-08 ← PE-R-07（PREREQ）先有行动与观察的循环，才能理解反思回路在何处插入

## 第 17 层 · 3 个节点

- PE-A-05 G06 负向提示的失效（Failure of Negative Prompting）
- PE-E-05 G05 自动提示词工程（Automatic Prompt Engineering）
- PE-P-02 G09 技能文件编写（Authoring Skill Files）

- 为什么在这层：PE-A-05 ← PE-A-04（PREREQ）安全约束的具体写法决定它是否真的生效，故接着学负向提示的失效
- 为什么在这层：PE-E-05 ← PE-E-02（PREREQ）自动优化依赖评测集与可自动计算的判据
- 为什么在这层：PE-E-05 ← PE-R-08（PREREQ）反思给出候选改进，自动提示词工程把候选筛选机制化
- 为什么在这层：PE-P-02 ← PE-P-01（PREREQ）先盘点提示词面，才知道技能文件在其中的位置与常驻策略

## 第 18 层 · 3 个节点

- PE-A-06 G06 不可信内容的标注与隔离（Tagging and Isolating Untrusted Content）
- PE-E-06 G05 声明式编译与签名（Declarative Compilation and Signatures）
- PE-P-03 G09 子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）

- 为什么在这层：PE-A-06 ← PE-A-05（PREREQ）先掌握指令该怎么写，再学不可信内容该如何标注与隔离
- 为什么在这层：PE-A-06 ← PE-C-02（PREREQ）检索资料是不可信内容的主要来源，提示模式须与标注配套
- 为什么在这层：PE-A-06 ← PE-F-03（PREREQ）分隔符是标注不可信内容的技术前提
- 为什么在这层：PE-E-06 ← PE-E-05（UPGRADE）从「让模型改指令」升级为「声明签名并由编译器搜索配置」
- 为什么在这层：PE-P-03 ← PE-P-02（PREREQ）技能文件之后是委派契约，两者共同构成按需层的提示资产

## 第 19 层 · 3 个节点

- PE-E-04 G05 评测工具链与红蓝对抗（Evaluation Toolchain and Red Teaming）
- PE-E-07 G05 文本梯度与反思式进化（Textual Gradient and Reflective Evolution）
- PE-M-03 G07 换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）

- 为什么在这层：PE-E-04 ← PE-A-06（FLOW）隔离措施是否有效只能靠对抗评测度量，故接评测工具链
- 为什么在这层：PE-E-04 ← PE-E-03（PREREQ）先理解裁判偏差，才能正确使用工具链中的模型辅助断言
- 为什么在这层：PE-E-04 ← PE-S-05（FLOW）校验器的判据与评测工具链的断言共用同一套表达方式
- 为什么在这层：PE-E-07 ← PE-E-06（PREREQ）先有编译流程与指标，再引入以反馈为梯度的优化方式
- 为什么在这层：PE-M-03 ← PE-E-06（PREREQ）声明式编译是换模型后重编译这条纪律的技术依托
- 为什么在这层：PE-M-03 ← PE-M-02（PREREQ）先理解标记按模型重测，再推广到整体提示词的重编译流程

## 第 20 层 · 2 个节点

- PE-E-08 G05 元提示（Meta-prompting）
- PE-M-04 G07 成本—质量—延迟三角（Cost–Quality–Latency Triangle）

- 为什么在这层：PE-E-08 ← PE-E-07（PREREQ）先能改进组件，再让模型生成或改写提示词本身
- 为什么在这层：PE-M-04 ← PE-M-03（PREREQ）重编译涉及预算，必须与成本、质量、延迟三项指标一起决策
- 为什么在这层：PE-M-04 ← PE-R-04（PREREQ）显式搜索的成本量级决定了它只在预算充足时适用
- 为什么在这层：PE-M-04 ← PE-R-06（PREREQ）压缩推理长度的收益必须在成本—质量—延迟三角里衡量

## 第 21 层 · 1 个节点

- PE-E-09 G05 提示词版本化与回归（Prompt Versioning and Regression）

- 为什么在这层：PE-E-09 ← PE-E-04（PREREQ）工具链就位后，回归才有可执行的载体
- 为什么在这层：PE-E-09 ← PE-E-08（PREREQ）批量改写产生大量候选，必须有版本化与回归来筛选

## 第 22 层 · 1 个节点

- PE-P-04 G09 门控即判据（Gate as Executable Criterion）

- 为什么在这层：PE-P-04 ← PE-E-09（FLOW）版本化与回归的判据形态，就是可执行的门控脚本
- 为什么在这层：PE-P-04 ← PE-P-03（PREREQ）委派需要可验证的返回契约，门控即判据是它的机械形态
- 为什么在这层：PE-P-04 ← PE-S-01（PREREQ）约束解码是门控中「结构合法」类断言的实现基础

## 第 23 层 · 1 个节点

- PE-P-05 G09 记忆与反思（Memory and Reflection）

- 为什么在这层：PE-P-05 ← PE-E-07（PREREQ）反思式进化与记忆机制共用同一套「候选—复核—落库」流程
- 为什么在这层：PE-P-05 ← PE-O-06（PREREQ）持久化状态与长期记忆是同一类「跨调用事实」的两种载体
- 为什么在这层：PE-P-05 ← PE-P-04（PREREQ）判据就位后，才谈得上用记忆沉淀并复核跨会话结论
- 为什么在这层：PE-P-05 ← PE-V-03（FLOW）长序列治理的结论落到实践层就是记忆的写入与退役

## 第 24 层 · 1 个节点

- PE-P-06 G09 模型上下文协议接入实况（MCP in Practice）

- 为什么在这层：PE-P-06 ← PE-C-07（FLOW）协议原理落到自己的运行时上就是接入实况
- 为什么在这层：PE-P-06 ← PE-P-05（PREREQ）记忆与上下文管理就绪后，再接入外部数据源与工具
- 为什么在这层：PE-P-06 ← PE-V-02（FLOW）多模态能力往往通过外部服务接入，须与接入治理一并考虑

## 第 25 层 · 1 个节点

- PE-P-07 G09 跨运行时迁移教训（Lessons from Cross-runtime Migration）

- 为什么在这层：PE-P-07 ← PE-P-06（PREREQ）接入实况之后是跨运行时迁移，后者会重新暴露接入差异

## 第 26 层 · 1 个节点

- PE-N-01 GD-N 三代范式脉络（Three-Generation Paradigm Arc）（架构在册）

- 为什么在这层：PE-N-01 ← PE-P-07（FLOW）迁移教训引出对三代范式脉络的整体回看

## 第 27 层 · 1 个节点

- PE-N-02 GD-N 当前共识与争议（Current Consensus and Disputes）（架构在册）

- 为什么在这层：PE-N-02 ← PE-N-01（PREREQ）先有三代脉络，才能把各条结论归入共识或争议

## 第 28 层 · 1 个节点

- PE-N-03 GD-N 模块维护机制（Module Maintenance Mechanism）（架构在册）

- 为什么在这层：PE-N-03 ← PE-M-04（PREREQ）刷新是有成本的动作，须先有成本与收益的取舍框架
- 为什么在这层：PE-N-03 ← PE-N-02（PREREQ）先区分共识与争议，再定义这个分区如何被维护与刷新

## 第 29 层 · 1 个节点

- PE-N-04 GD-N 跟踪渠道（Tracking Channels）（架构在册）

- 为什么在这层：PE-N-04 ← PE-N-03（PREREQ）维护机制确定后，才谈得上用哪些渠道定期核验
- 为什么在这层：PE-N-04 ← PE-P-01（FLOW）自身 agent 的提示词面盘点，决定需要跟踪哪些渠道的变化
