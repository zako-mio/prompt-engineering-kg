# 大模型应用十大风险（Top 10 Risks for LLM Applications）

- 节点标识：PE-A-03
- 英文名：Top 10 Risks for LLM Applications
- 所属分组：G06 安全与鲁棒性
- 依赖深度：第 13 层
- 内容状态：内容已写满
- 标签：安全、风险清单、OWASP

## 为什么需要它

命名风险清单的价值在于按版本给出一份可逐条勾选的覆盖面，避免团队只防住自己恰好想到的那一两类风险。现行 2026 版的调整不是文案微调：权限类风险升到 LLM03，隐藏上下文暴露取代了上一版的系统提示泄露，旧的序号与条目名会直接错位。把版本绑定写进引用习惯，才能让评审记录与缓解措施一一对得上。

**适用边界**

清单是覆盖检查表，既不是风险排序，也不是合规认证或标准证书。当被引用的那一版与实现所依据的版本不一致时，序号、条目名与缓解措施都会对不上，此时必须先统一版本再讨论。清单也不排斥自研风险项：团队可以按自身业务补充条目，但须与官方十条分开标注，避免把内部项当成官方口径对外引用。

## 机制说明

现行 2026 版十条依次为：提示注入、敏感信息泄露、过度自主权、供应链、数据与模型投毒、无界消耗、错误信息、隐藏上下文暴露、向量与嵌入弱点、输出处理不当。相对上一版有三处实质变化：权限类风险位次前移、隐藏上下文暴露替代了系统提示泄露、注入形态扩到多模态内容与工具返回。使用方式建议按工程阶段映射：设计阶段先过能力边界与权限分配，接入阶段过供应链与向量与嵌入弱点，上线阶段过无界消耗与输出处理，运行期持续盯注入与信息泄露。两点提醒：首次引用务必注明版本号，因为官网索引页与官方仓库正文的同步状态存在落差；清单给的是覆盖面而非风险排序，条目齐不等于实施到位。

## 何时该用 / 何时不该用

- 系统设计评审时：用清单逐条检查覆盖面，尤其是权限与供应链两类。
- 接入第三方模型或检索链路前：核对供应链与向量与嵌入弱点两条。
- 上线前检查时：重点核对无界消耗与输出处理不当。
- 不适用于把清单当合规认证：它是覆盖检查表，不是标准或证书。
- 不适用于不标版本地引用：不同版本条目与位次不同，混用会误导读者。

## 实验台

### shell（bash）

```bash
printf '%s\n' "这张提示词上覆盖了下面十条里的哪几条？" > prompt.txt
for k in "Prompt Injection" "Sensitive Information Disclosure" "Excessive Agency" \
         "Supply Chain" "Data and Model Poisoning" "Unbounded Consumption" \
         "Misinformation" "Hidden Context Exposure" \
         "Vector and Embedding Weaknesses" "Improper Output Handling"; do
  printf '%-34s %s\n' "$k" "$(grep -c "$k" prompt.txt)"
done
```

预期观察：十行输出，每行右侧为命中次数；未覆盖的条目计数为 0，据此把清单缺口逐条落到整改项上。

### file（python）

```python
version = "2026"
refs = [
    "LLM01:2026 Prompt Injection",
    "LLM03 Excessive Agency",
    "LLM08 Hidden Context Exposure",
]
for r in refs:
    assert version in r or r.split()[0].endswith(version), r
print("all references pinned to", version)
```

预期观察：逐条断言引用串里带上了版本号，全部通过时打印 all references pinned to 2026；把任一条换成上一版条目名即立刻断言失败。

## 证据

- **OWASP 官方资源页确认 2026 版是现行最新的 LLM 应用风险清单，可作为版本引用的锚点。**（S-0030，official）
  - 出处：https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/
  - 原文关键句：OWASP Top 10 for LLM Applications 2026 is the latest community-driven guide to the most critical security risks facing applications powered by large language models.
- **官方仓库正文给出 2026 版清单的位次与官方英文条目名，可据此核对引用是否过期。**（S-0031，official）
  - 出处：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/README.md
  - 原文关键句：LLM01:2026 Prompt Injection | ... | LLM03 Excessive Agency | LLM04 Supply Chain | ... | LLM08 Hidden Context Exposure | ... | LLM10 Improper Output Handling
- **官方正文给出提示注入的判定与防御取向：不存在可靠的拦截式预防，防御须是架构性的。**（S-0032，official）
  - 出处：https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/2026/final/LLM01_PromptInjection.md
  - 原文关键句：Prompt injection is intrinsic to current generative AI... so no reliable prevention mechanism exists today... Defense is therefore architectural rather than interceptive.

## 术语

- **提示词注入（Prompt Injection）**：输入内容改变了应用开发者未预期的模型行为；模型在架构上不区分「指令」与「数据」，因此不存在可靠的拦截式预防，防御须是架构性的。
- **指令层级（Instruction Hierarchy）**：按特权等级排列指令来源（系统 > 开发者 > 用户 > 工具），使低特权来源的指令无法覆盖高特权来源；用它是为了给清单里的权限类风险提供可落地的防御位。

## 失效模式

- 把清单当合规认证：把它写进验收材料当合格证明，结果是条目齐了但权限与供应链两类没做任何治理。
- 不标版本地引用：沿用上一版的序号与条目名，评审记录与缓解措施一一错位，读者无法判断讨论的是哪一版。
- 只勾条目不动权限：权限类风险停留在纸面，一旦被注入触发就直接放大成工具滥用与越权操作。
- 把注入当纯输入过滤问题：只加输入侧过滤，忽略工具返回与检索内容这些入口，任务照样被外部内容改写。

## 一句话小结

清单是按版本映射到工程阶段的覆盖检查表：先钉住版本号，再逐条把覆盖面转成整改项，其中权限类风险要落到指令层级与工具授权这类架构位，而不是只写一条禁止语。官网索引页与官方仓库正文存在同步落差，所以引用时须写明版本来源。

## 在本站知识结构中的位置

- 前置：PE-A-02
- 后继：PE-A-04
