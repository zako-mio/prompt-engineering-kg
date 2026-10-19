# 标记敏感度的迁移性（Transferability of Markup Sensitivity）

- 节点标识：PE-M-02
- 英文名：Transferability of Markup Sensitivity
- 所属分组：G07 模型差异与迁移
- 依赖深度：第 8 层
- 内容状态：内容已写满
- 标签：模型迁移、标记、可迁移性

## 为什么需要它

同一套标记写法在不同模型上的收益并不可迁移：某个模型对 XML 标签、分节标题这类结构响应明显，换到另一个模型后同样的标签可能被完全忽略，甚至被当作正文原样打印出来。已有生产案例显示，过去在更早模型上有效的提示段落需要重新调校，其中一处强调式标签写法在新模型上被判定为适得其反。因此标记敏感度必须按模型实测，不能按经验继承。

**适用边界**

本节点限定的是标记与结构写法的可迁移性：它不否定标记在多部分提示中的消歧价值，只说明这种价值的强度必须逐模型实测；同一模型族内不同版本的标记敏感度同样需要重新确认，不能按版本号外推。

## 机制说明

标记敏感度的差异有三个来源：训练数据中该类标记的出现频率、指令微调阶段是否使用过这类标记、以及分词器对标记的切分方式（部分标签会被切成不利于整体识别的片段）。还有一个更直接的来源：模型族对指令具体程度的需求本就不同，推理型模型在只给高层指引时表现更好，另一些模型则需要非常精确的指令，因此把结构写得更细本身没有跨模型一致的收益。工程上的应对是把标记体系当作可替换的配置项：为每个目标模型维护一组已验证的标记写法，在换模型或引入新模型时做一次小规模对照测试（同一任务分别用带标记与不带标记的提示），并把标记是否泄漏到输出作为一项判据——标记出现在输出中，通常意味着模型没有把它当作结构信号。

## 何时该用 / 何时不该用

- 换模型或引入新模型时：对标记写法做一次带标记与不带标记的小规模对照测试，再决定是否沿用。
- 多模型共存的产品中：为每个模型维护一组已验证的标记写法，把标记体系做成可替换的配置。
- 不适用于把标记写法当跨模型通用经验：敏感度取决于该模型是否针对此类标记做过对齐训练。
- 不适用于只看准确率就判定标记有效：还要检查标记是否泄漏到输出中。

## 实验台

### file（python）

```python
# 标记敏感度对照：同一任务、同一评测集，只切换标记写法，逐模型各跑一遍
VARIANTS = {
    "markup": "资料放进 <context> 标签，示例放进 <example> 标签，格式约束单独分节",
    "plain": "资料、示例、格式约束三段平铺，不使用任何标签",
}

def leaked(text):
    # 标记泄漏：标签出现在输出里，通常说明结构信号未被识别
    return any(t in text for t in ("<context>", "</context>", "<example>", "</example>"))

rows = []
for model in MODELS:
    for name, style in VARIANTS.items():
        out = call(model, build(style, task))   # build 只改标记写法，不改内容
        rows.append({"model": model, "style": name,
                     "score": score(out, task), "leaked": leaked(out)})
print_table(rows)
```

预期观察：逐模型得到一张对照表：只有当某个模型上 markup 变体的得分不低于 plain 且未出现标记泄漏时，才把该标记写法登记为该模型的已验证配置；若两个变体差异不显著，说明该模型对这套标记不敏感，不能把别处模型的收益当作它也会受益。

### file（markdown）

```markdown
# 标记写法登记表（按模型维护；换模型新增一行，不覆盖旧行）

| 模型 | 标记写法 | 对照结论 | 标记泄漏 | 登记日期 |
|---|---|---|---|---|
| <model-a> | `<context>` / `<example>` 分节 | 优于平铺 | 无 | <date> |
| <model-b> | 不用标签，改分节标题 | 与平铺持平 | 无 | <date> |
| <model-c> | 尚未对照 | 无结论 | 未测 | <date> |

对照记录须写明：任务、评测集、两个变体的得分、以及是否出现标记泄漏。
```

预期观察：读者能产出一张按模型分行的登记表，同一标记写法在不同模型上可以有不同结论；表中没有任何一行是从别的模型复制而来，换模型时只新增行而不改旧行。

## 证据

- **生产案例：某工具厂商发现其提示中过去对更早模型有效的段落需要重新调校，其中一处强调式标签在新模型上被判定为适得其反，说明同一标记写法跨模型不可沿用。**（S-0015，official）
  - 出处：https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt-5/gpt-5_prompting_guide.ipynb
  - 原文关键句：Cursor found that sections of their prompt that had been effective with earlier models needed tuning ... <maximize_context_understanding> Be THOROUGH ... they found it counterproductive with GPT-5
- **官方口径按模型族区分指令的具体程度：推理型模型在只给高层指引时表现更好，而另一类模型需要非常精确的指令，因此结构与指令写多细的收益随模型族而变。**（S-0011，official）
  - 出处：https://developers.openai.com/api/docs/guides/prompt-engineering
  - 原文关键句：Generally speaking, reasoning models will provide better results on tasks with only high-level guidance. This differs from GPT models, which benefit from very precise instructions.
- **标记用法的官方说明本身以单一模型族为对象表述（帮助该模型解析复杂提示），说明标记收益的结论是按模型族给出的，不能直接外推到其他模型。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Wrap examples in `<example>` tags (multiple examples in `<examples>` tags) so Claude can distinguish them from instructions. ... XML tags help Claude parse complex prompts unambiguously

## 术语

- **标记敏感度的迁移性（Transferability of Markup Sensitivity）**：对某种标记（如 XML 标签）的响应强度取决于该模型是否针对此类标记做过指令对齐训练，因此同一标记在不同模型上的效果不可假定一致。
- **分隔符与上下文隔离（Delimiters and Context Isolation）**：用 XML 标签、专用分节标记等把指令、示例、资料与用户输入在文本上划出边界，使模型能无歧义解析多部分提示。
- **换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）**：提示词中的多数经验与具体模型绑定；更换模型后必须重跑评测并重做优化，而不是沿用旧结论。

## 失效模式

- 照搬别的模型上验证过的标记写法：换模型后收益可能归零甚至转负，而失败会被误判为提示词写得不好，而不是标记不适用。
- 只看准确率就判定标记有效：标记泄漏到输出说明结构信号未被识别，此时的小幅得分提升可能来自任务本身的容错。
- 把标记体系硬编码进产品：多模型共存时无法按模型切换写法，只能整体回退到最保守的一套。
- 用同一套对照结论覆盖同族的所有版本：同族不同版本的标记敏感度仍需重新确认，不能按版本号外推。

## 一句话小结

标记写法是按模型重测的配置项：换模型时用带标记与不带标记的对照测试重新确认，并把标记是否泄漏纳入判据。

## 在本站知识结构中的位置

- 前置：PE-M-01
- 后继：PE-M-03
