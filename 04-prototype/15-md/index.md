# 新一代提示词工程知识全景图与教程（Markdown 镜像）

本目录是站点的纯文本镜像，供检索与引用；人类阅读入口是 HTML 页面。

- 读者锚点：有工程基础、提示词工程未系统化的工程师
- 数据时点：2026-10
- 版次：v1
- 节点 67 / 边 96 / 分组 11 / 依赖深度层 30
- 边语义：PREREQ前置依赖、CONTAINS包含从属、UPGRADE概念升级、FLOW流程承接
- 依赖方向：A→B 表示先学 A 再学 B；层序由该方向推导
- 无环：是
- 内容状态：已写满 67 个（架构已全部落页，无待填充项）

## 目录

- [知识分组](groups/index.md)
- [学习路径](learning-path.md)
- [新一代模块](frontier.md)
- [已写满的节点](nodes/)

## 已写满的节点

- [PE-F-01 概率采样与确定性边界（Probabilistic Sampling and the Determinism Boundary）](nodes/pe-f-01.md)
- [PE-F-02 系统 / 开发者 / 用户提示词分层（System, Developer, and User Prompt Layering）](nodes/pe-f-02.md)
- [PE-F-03 分隔符与上下文隔离（Delimiters and Context Isolation）](nodes/pe-f-03.md)
- [PE-A-01 指令层级（Instruction Hierarchy）](nodes/pe-a-01.md)
- [PE-F-04 零样本与少样本（Zero-shot and Few-shot Prompting）](nodes/pe-f-04.md)
- [PE-A-02 直接与间接提示词注入（Direct and Indirect Prompt Injection）](nodes/pe-a-02.md)
- [PE-F-05 指令的具体性与可验证性（Instruction Specificity and Verifiability）](nodes/pe-f-05.md)
- [PE-F-06 注意力预算与上下文衰减（Attention Budget and Context Rot）](nodes/pe-f-06.md)
- [PE-S-01 结构模式与约束解码（JSON Schema and Constrained Decoding）](nodes/pe-s-01.md)
- [PE-R-01 思维链与零样本思维链（Chain-of-Thought and Zero-shot CoT）](nodes/pe-r-01.md)
- [PE-C-01 上下文即工作内存与四策略（Context as Working Memory and Four Strategies）](nodes/pe-c-01.md)
- [PE-S-02 三档严格度（Three Tiers of Strictness）](nodes/pe-s-02.md)
- [PE-R-02 范式反转：推理模型上经典技巧掉分（Paradigm Reversal: Classic Techniques Lose Ground on Reasoning Models）](nodes/pe-r-02.md)
- [PE-C-02 RAG 提示模式（RAG Prompting Patterns）](nodes/pe-c-02.md)
- [PE-M-01 模型分层选型（Model Tiering）](nodes/pe-m-01.md)
- [PE-S-03 推理与格式的冲突（Reasoning–Format Conflict）](nodes/pe-s-03.md)
- [PE-C-03 图检索与全局观（Graph Retrieval and Global View）](nodes/pe-c-03.md)
- [PE-O-01 提示词链（Prompt Chaining）](nodes/pe-o-01.md)
- [PE-M-02 标记敏感度的迁移性（Transferability of Markup Sensitivity）](nodes/pe-m-02.md)
- [PE-S-04 格式选型与词元效率（Format Choice and Token Efficiency）](nodes/pe-s-04.md)
- [PE-C-04 检索质量与垃圾进垃圾出（Retrieval Quality and GIGO）](nodes/pe-c-04.md)
- [PE-O-02 路由（Routing）](nodes/pe-o-02.md)
- [PE-V-01 交错输入（Interleaved Input）](nodes/pe-v-01.md)
- [PE-S-05 校验与修复回路（Validation and Repair Loop）](nodes/pe-s-05.md)
- [PE-C-05 长上下文位置偏差（Long-context Positional Bias）](nodes/pe-c-05.md)
- [PE-O-03 并行化与投票（Parallelization and Voting）](nodes/pe-o-03.md)
- [PE-E-01 为什么必须先建评测集（Why Build an Eval Set First）](nodes/pe-e-01.md)
- [PE-V-02 视觉推理链（Visual Reasoning Chain）](nodes/pe-v-02.md)
- [PE-R-03 自一致性与多数投票（Self-Consistency and Majority Voting）](nodes/pe-r-03.md)
- [PE-C-06 提示缓存（Prompt Caching）](nodes/pe-c-06.md)
- [PE-O-04 编排者—工作者（Orchestrator–Workers）](nodes/pe-o-04.md)
- [PE-E-02 测试集构造（Test Set Construction）](nodes/pe-e-02.md)
- [PE-V-03 位置敏感与注意力耗散（Positional Sensitivity and Attention Dissipation）](nodes/pe-v-03.md)
- [PE-R-04 思维树与思维图（Tree of Thoughts and Graph of Thoughts）](nodes/pe-r-04.md)
- [PE-C-07 模型上下文协议（Model Context Protocol）](nodes/pe-c-07.md)
- [PE-O-05 生成者—评估者（Generator–Evaluator）](nodes/pe-o-05.md)
- [PE-R-05 步骤回溯与改写变体（Step Backtracking and Rewrite Variants）](nodes/pe-r-05.md)
- [PE-O-06 状态机与持久化（State Machine and Persistence）](nodes/pe-o-06.md)
- [PE-E-03 模型即裁判及其偏差（LLM-as-a-Judge and Its Biases）](nodes/pe-e-03.md)
- [PE-A-03 大模型应用十大风险（Top 10 Risks for LLM Applications）](nodes/pe-a-03.md)
- [PE-R-06 极简推理草稿（Chain of Draft）](nodes/pe-r-06.md)
- [PE-O-07 子 Agent 上下文隔离（Sub-agent Context Isolation）](nodes/pe-o-07.md)
- [PE-R-07 ReAct 推理—行动交织（ReAct: Interleaved Reasoning and Acting）](nodes/pe-r-07.md)
- [PE-O-08 工具定义与滥用治理（Tool Definition and Abuse Governance）](nodes/pe-o-08.md)
- [PE-R-08 反思与自评回路（Reflection and Self-Critique Loop）](nodes/pe-r-08.md)
- [PE-A-04 过拒与安全—可用性权衡（Over-refusal and the Safety–Usability Tradeoff）](nodes/pe-a-04.md)
- [PE-P-01 我的 agent 的提示词面（My Agent's Prompt Surface）](nodes/pe-p-01.md)
- [PE-E-05 自动提示词工程（Automatic Prompt Engineering）](nodes/pe-e-05.md)
- [PE-A-05 负向提示的失效（Failure of Negative Prompting）](nodes/pe-a-05.md)
- [PE-P-02 技能文件编写（Authoring Skill Files）](nodes/pe-p-02.md)
- [PE-E-06 声明式编译与签名（Declarative Compilation and Signatures）](nodes/pe-e-06.md)
- [PE-A-06 不可信内容的标注与隔离（Tagging and Isolating Untrusted Content）](nodes/pe-a-06.md)
- [PE-P-03 子 Agent 委派与返回契约（Sub-agent Delegation and Return Contract）](nodes/pe-p-03.md)
- [PE-E-04 评测工具链与红蓝对抗（Evaluation Toolchain and Red Teaming）](nodes/pe-e-04.md)
- [PE-E-07 文本梯度与反思式进化（Textual Gradient and Reflective Evolution）](nodes/pe-e-07.md)
- [PE-M-03 换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）](nodes/pe-m-03.md)
- [PE-E-08 元提示（Meta-prompting）](nodes/pe-e-08.md)
- [PE-M-04 成本—质量—延迟三角（Cost–Quality–Latency Triangle）](nodes/pe-m-04.md)
- [PE-E-09 提示词版本化与回归（Prompt Versioning and Regression）](nodes/pe-e-09.md)
- [PE-P-04 门控即判据（Gate as Executable Criterion）](nodes/pe-p-04.md)
- [PE-P-05 记忆与反思（Memory and Reflection）](nodes/pe-p-05.md)
- [PE-P-06 模型上下文协议接入实况（MCP in Practice）](nodes/pe-p-06.md)
- [PE-P-07 跨运行时迁移教训（Lessons from Cross-runtime Migration）](nodes/pe-p-07.md)
- [PE-N-01 三代范式脉络（Three-Generation Paradigm Arc）](nodes/pe-n-01.md)
- [PE-N-02 当前共识与争议（Current Consensus and Disputes）](nodes/pe-n-02.md)
- [PE-N-03 模块维护机制（Module Maintenance Mechanism）](nodes/pe-n-03.md)
- [PE-N-04 跟踪渠道（Tracking Channels）](nodes/pe-n-04.md)

## 知识分组一览

- [G00 地基：模型是概率采样器](groups/g00.md)：6 个节点
- [G01 确定性输出](groups/g01.md)：5 个节点
- [G02 推理增强](groups/g02.md)：8 个节点
- [G03 上下文工程](groups/g03.md)：7 个节点
- [G04 编排](groups/g04.md)：8 个节点
- [G05 评测与自动优化](groups/g05.md)：9 个节点
- [G06 安全与鲁棒性](groups/g06.md)：6 个节点
- [G07 模型差异与迁移](groups/g07.md)：4 个节点
- [G08 多模态](groups/g08.md)：3 个节点
- [G09 落地实践](groups/g09.md)：7 个节点
- [GD-N 新一代模块](groups/gd-n.md)：4 个节点

## 新一代模块

- [新一代模块条目镜像](frontier.md)：只含数据、不含教程正文；条目带时间锚、版次、状态与取代关系，大更新时只刷新该处。
