# 新一代模块

- 时间锚：2026-10
- 版次：2026-10
- 上一般次：无
- 条目数：4

状态三值口径：已确认 = 多源同向且可复核；有争议 = 存在反向证据或未获权威裁定；未证实 = 尚未取得足以支撑的独立证据。未实测标注指该条未在本机跑通，只给出可执行的复现步骤。

## PE-N-01 三代范式脉络：提示词工程 → 上下文工程 → 编排与编译

- 状态：已确认
- 时间锚：2026-10
- 版次：2026-10
- 取代：无

2020 至 2023 年以单次调用的指令写法与手工推理技巧为主；2023 至 2025 年重心移到把正确的动态知识放进窗口（检索、图检索、长文本压缩、位置优化）；2025 至 2026 年重心再上移到编排、协议标准化与自动编译。三代是叠加而非替代关系，判断投入方向的依据是当前瓶颈落在哪一代。多源证据同向：厂商侧把上下文工程明确定义为提示工程的自然演进，并给出隔离、持久化、压缩三类工程内容；协议侧则用标准化接口把外部数据与工具的接入从各家自建收敛为统一规范。

- 证据（S-0004，official）：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - 原文关键句：we view context engineering as the natural progression of prompt engineering. Prompt engineering refers to methods for writing and organizing LLM instructions ... Context engineering refers to the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference, including all the other information that may land there outside of the prompts.
- 证据（S-0019，official）：https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
  - 原文关键句：The process of managing this information flow is called context engineering. Context engineering includes strategies such as isolating context for a specific agent, persisting information across multiple steps, or compressing large amounts of data to improve efficiency.
- 证据（S-0022，official）：https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - 原文关键句：Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request now carries its protocol version and client capabilities in `_meta`... 1. Deprecate the Roots, Sampling, and Logging features (SEP-2577).

离线复现：步骤：① 取同一任务的三个版本实现——纯提示词版本、加检索的上下文版本、加编排或编译的版本；② 在固定模型与固定评测集上分别测准确率、输入 token、输出 token 与延迟；③ 检查三代之间的增量是否单调，以及瓶颈是否随版本前移而改变。注意：本条为脉络性判断，未在本机实测三代实现的完整对照，复现结论以读者自身数据为准。

## PE-N-02 当前共识与争议：范式反转的边界、编译与微调的临界点、原生推理与外部编排的分工

- 状态：有争议
- 时间锚：2026-10
- 版次：2026-10
- 取代：PE-R-03

共识两条：模型越强越应减少手写步骤与堆砌示例，把重心移到上下文与信息的组织治理；指令层级作为权限关系已被底座部分内化，但不足以让应用层放弃自身防御。争议三处：其一，范式反转的适用范围——多源证据显示推理模型上思维链与示例堆砌的边际收益趋零或为负，但任务域反例证明该符号随任务串行深度与模型规模变化；其二，自动编译与微调的性价比临界点——唯一直接的学术对照实验结论是二者互补而非替代，未给出成本临界点；其三，原生推理与外部编排的分工——分层自治是倾向性判断，缺权威裁定。因此本模块对这三处一律登记为有争议，不代读者裁定。

- 证据（S-0035，paper）：https://arxiv.org/abs/2506.07142
  - 原文关键句：For models designed with explicit reasoning capabilities, CoT prompting often results in only marginal, if any, gains in answer accuracy. However, it significantly increases the time and tokens needed to generate a response. ... o3-mini (2.9%) and o4-mini (3.1%); Performance decrease for Gemini Flash 2.5 (-3.3%).
- 证据（S-0039，paper）：https://arxiv.org/abs/2608.09942
  - 原文关键句：On high-depth P-complete tasks (GSM8K, MATH), CoT gives a +54 to +68 pp recovery gap across all models. On shallow TC^0 tasks (MMLU, ARC), CoT is structurally redundant (Delta in [0.0, +4.6] pp).
- 证据（S-0037，paper）：https://arxiv.org/abs/2507.13525
  - 原文关键句：For high-performance LLMs, simple prompts often outperform more complex ones while reducing cost. In contrast, commonly used prompting styles in natural language processing, such as step-by-step reasoning, or the use of reasoning models often lead to lower accuracy.
- 证据（S-0052，official）：https://aclanthology.org/2026.findings-eacl.161/
  - 原文关键句：We study three optimizers from the DSPy framework -- COPRO, MiPROv2, and SIMBA ... MiPROv2 yielding the most stable gains for CoT, and SIMBA providing the largest benefits for ReAct agents, particularly at larger model scales. ... CoT remains effective for tabular fact checking, especially with smaller models.
- 证据（S-0048，paper）：https://arxiv.org/abs/2407.10930
  - 原文关键句：these BetterTogether strategies optimizing the weights and prompts of a pipeline together outperform directly optimizing weights alone and prompts alone by up to 60% and 6%, respectively
- 证据（S-0017，vendor）：https://openai.com/index/instruction-hierarchy-challenge/
  - 原文关键句：OpenAI's models are trained to follow a clear instruction hierarchy: System > developer > user > tool ... TensorTrust (dev-user) 0.76 → 0.91 (+0.15); System<>User Conflict 0.84 → 0.95 (+0.11); GPQA Diamond 0.83 → 0.83; Chat WinRate vs o1 0.71 → 0.66 (-0.05); Preference Score 0.46 → 0.40 (-0.06).

离线复现：步骤：① 在自己的任务域内取一个推理模型与一个非推理模型；② 对同一批样本分别用「显式思维链」与「一般性指令」两版提示，各跑多次；③ 记录准确率、输出 token 与延迟，并按任务串行深度分层统计；④ 再对同一流水线跑一次「仅优化提示」与「交替优化权重与提示」的对照。注意：本条未在本机实测，且第三方证据来自单作者预印本与厂商自述；结论须以读者自身任务的实测为准，不得直接外推。

## PE-N-03 模块维护机制：以数据为载体的增量刷新与取代关系

- 状态：已确认
- 时间锚：2026-10
- 版次：2026-10
- 取代：无

本模块的载体是条目集合而非教程正文，刷新动作被定义为「改条目集合与时间锚、重跑生成器与门控」，不触碰任何页面模板。维持这一机制的三条依据来自协议与厂商侧的现行实践：规范文档以版本页声明当前版本与修订状态；厂商对 API 能力给出显式弃用时间线；风险清单则用条目更替表达结论的演进。同时必须承认一处真实的同步落差——风险清单的官方索引页与官方仓库正文在版本上并不同步，这正是需要「时间锚 + 取代关系」而不是「就地覆盖」的理由：旧条目被标记取代而非删除，读者才能理解某条建议为何曾经成立。

- 证据（S-0023，official）：https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning
  - 原文关键句：The current protocol version is 2026-07-28. ... Revisions may be marked as: Draft / Current / Final.
- 证据（S-0011，official）：https://developers.openai.com/api/docs/guides/prompt-engineering
  - 原文关键句：Store production prompts in your application code instead of creating reusable prompt objects. ... OpenAI is deprecating reusable prompt objects in the API. Prompt creation will be de-emphasized beginning June 3, 2026, and `v1/prompts` is scheduled to shut down on November 30, 2026.
- 证据（S-0031，official）：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/README.md
  - 原文关键句：Status: Published | Release date: August 4, 2026 ... LLM01:2026 Prompt Injection | LLM02 Sensitive Information Disclosure | LLM03 Excessive Agency | LLM04 Supply Chain | LLM05 Data and Model Poisoning | LLM06 Unbounded Consumption | LLM07 Misinformation | LLM08 Hidden Context Exposure | LLM09 Vector and Embedding Weaknesses | LLM10 Improper Output Handling
- 证据（S-0034，official）：https://genai.owasp.org/llm-top-10/
  - 原文关键句：（同步落差证据：官网索引页在 2026-10-14 抓取时仍以 2025 版十条为展示主体，与官方仓库 2026/README.md 标注的 2026 版并存）

离线复现：步骤：① 在本地复制条目集合文件；② 只修改其中一条条目的状态与取代关系，并把时间锚更新为新版次；③ 重跑生成器并记录除该模块外其余产物文件的摘要变化数（应为 0）；④ 断言版次与时间锚一致，否则判为假刷新。注意：本条机制的描述取自协议与厂商文档的现行实践，未在本机跑通完整生成器，故只给出可执行的复现步骤而非实测结论。

## PE-N-04 跟踪渠道：学术、厂商、协议标准与包仓库四类最小集

- 状态：已确认
- 时间锚：2026-10
- 版次：2026-10
- 取代：无

四类渠道构成最小跟踪集：学术侧（预印本平台的自然语言处理与密码安全分类）用于跟踪范式反转与防御机制的研究进展；厂商侧（三大模型厂商的开发者文档与更新日志）用于跟踪现行口径与弃用时间线；协议与标准侧（协议规范与变更页、风险清单官方仓库）用于跟踪治理与版本变更；包与仓库侧（包注册表与代码托管平台元数据）用于核验工具版本与维护活跃度。使用纪律有三条：每次刷新记录回源日期；对无日期戳页面标注时效不确定；对厂商自述的量化数字标注立场偏差，不作中立证据。

- 证据（S-0001，official）：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Wrap examples in `<example>` tags (multiple examples in `<examples>` tags) so Claude can distinguish them from instructions. ... XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs.
- 证据（S-0012，official）：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Set `reasoning.effort` to `low`, `medium` (default), `high`, `xhigh`, or `max`. ... When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`.
- 证据（S-0020，official）：https://modelcontextprotocol.io/specification/2026-07-28/server
  - 原文关键句：Prompts: Pre-defined templates or instructions ... Resources: Structured data or content that provides additional context ... Tools: Executable functions ... | Prompts | User-controlled | Resources | Application-controlled | Tools | Model-controlled |
- 证据（S-0083，official）：https://api.github.com/repos/stanfordnlp/dspy/releases/latest
  - 原文关键句："tag_name":"3.4.1" ... "published_at":"2026-10-12T23:12:32Z" ... "DSPy 3.4.1 makes GEPA's structured InstructionProposer the default instruction proposer"
- 证据（S-0105，official）：https://developers.openai.com/api/docs/deprecations
  - 原文关键句：（退役时间线入口；该域直连曾返回 403，精确退役日期未取得一手页面 ⇒ 不得据此断言具体日期）

离线复现：步骤：① 对每条待刷新结论，从四类渠道中各取至少一个一手来源；② 记录回源日期与页面自身日期（无日期戳者标注「时效不确定」）；③ 若结论来自厂商自述数字，标注立场偏差并不作中立证据；④ 与上一版次条目比对，改动即触发条目更新并记录取代关系。注意：渠道清单本身未在本机做端到端自动抓取，只给出人工可执行的最小流程。

## 跟踪渠道

- **arXiv cs.CL（计算与语言）新提交**（preprint）：https://arxiv.org/list/cs.CL/recent —— 跟踪范式反转、上下文工程与自动优化方向的预印本；预印本未经同行评审，引用须标注并优先寻找独立复现。
- **arXiv cs.CR（密码学与安全）新提交**（preprint）：https://arxiv.org/list/cs.CR/recent —— 跟踪指令层级、注入防御与 agent 攻击面方向的预印本。
- **Anthropic — Claude Docs 提示工程与模型迁移文档**（official）：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices —— 厂商侧现行口径的主要来源：思维链降级、prefill 与思考预算弃用、负向提示改写、长上下文位置建议。注意：页面无日期戳，只能按内容所含模型代号推断时效。
- **OpenAI — API 指南与模型更新页**（official）：https://developers.openai.com/api/docs/guides/latest-model —— 厂商侧现行口径：精简系统提示的量化口径、推理努力档位、指令层级与弃用时间线。注意：厂商自述数字不作中立证据。
- **Google — Gemini API 提示设计策略**（official）：https://ai.google.dev/gemini-api/docs/prompting-strategies —— 第三家厂商的交叉验证来源：内部思考文本、避免说服性语言、示例过量的过拟合风险。
- **Model Context Protocol — 规范与变更页**（official）：https://modelcontextprotocol.io/specification/2026-07-28/changelog —— 跟踪协议版本的破坏性变更、原语定义与治理归属；接入实况的权威依据。
- **OWASP GenAI Security Project — LLM Top 10 官方仓库**（official）：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/README.md —— 安全侧权威清单的 canonical 源；注意：官网索引页与仓库正文存在同步落差，引用须注明取自哪一处。
- **PyPI / npm 注册表与代码托管平台元数据**（official）：https://pypi.org/pypi/dspy/json —— 核验工具现行版本、许可证与维护活跃度；用于判断某条工具链结论是否仍然成立。
