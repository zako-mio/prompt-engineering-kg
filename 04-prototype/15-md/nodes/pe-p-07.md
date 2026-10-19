# 跨运行时迁移教训（Lessons from Cross-runtime Migration）

- 节点标识：PE-P-07
- 英文名：Lessons from Cross-runtime Migration
- 所属分组：G09 落地实践
- 依赖深度：第 25 层
- 内容状态：内容已写满
- 标签：落地实践、迁移、运行时

## 为什么需要它

同一套提示词与技能从运行时 A 搬到运行时 B 时，能搬走的是结构与判据，搬不走的是效力：工具声明方式、上下文注入方式、思考块回传要求与提示词承载对象都会随运行时与模型代际改变，旧写法可能从有效变成中性甚至有害。若把迁移当成复制粘贴，这类差异往往不以报错形式出现，而是以难以解释的行为漂移出现，排查成本远高于迁移本身。

**适用边界**

本节点的教训来自具体运行时与模型代际的实测形态，换运行时或换代际后必须在新环境重新验证；同一运行时内的小版本升级差异通常较小，但仍以重测结果为准。

## 机制说明

跨运行时迁移的差异集中在四处。能力面：prefill 是否仍被接受、思考块是否必须原样回传、工具声明由谁生成；上下文注入：运行时自动加入的环境说明、工具清单与时间戳会与提示词自身的指令竞争；承载方式：提示词放在自己的代码仓库里，还是寄存在运行时的远端对象上；校验入口：判据与确认在何处触发。因此迁移的动作不是复制粘贴，而是三步：先在新运行时上跑最小复现（同一任务、同一模型、只换运行时），把两侧的完整输入与输出都留下来对比；再把差异逐条归类为能力缺失、隐式注入或写法失效；最后按新能力面重编译提示词与配置，并保留一份可直接切回的旧版本。

## 何时该用 / 何时不该用

- 把提示词或技能迁到新运行时之前：先跑最小复现，确认差异来自运行时而不是任务本身。
- 升级模型代际时：把旧写法逐条重测，判定它仍然有效、已经中性化，还是已经变成有害。
- 不适用于直接套用旧运行时的调优结论：能力面与隐式注入都不同，结论必须在新环境重建。
- 不适用于把迁移当成一次性动作：运行时与模型会持续升级，迁移清单要随版本复跑。

## 实验台

### file（markdown）

```markdown
# 跨运行时迁移重测清单

- 能力面核对：prefill 是否仍被接受、思考块是否必须原样回传、工具声明由谁生成。
- 最小复现：同一任务、同一模型、只换运行时，两侧的完整输入与输出都要留存。
- 差异归类：逐条标为能力缺失、运行时隐式注入或写法失效，不留下未归类的差异。
- 重编译：按新能力面改写参数与字段，而不是保留旧字段反复重试。
- 回滚点：保留一份可直接切回的旧配置，并写明切换方式。
```

预期观察：五节全部填写完成，且每条差异都有归类与处置结论；存在未归类差异时视为未完成。

### shell（bash）

```bash
# 同一任务、同一模型、只换运行时：两侧各跑一次并落盘原始输出
mkdir -p migration/runtime-a migration/runtime-b
python3 run_task.py --runtime a --prompt prompt.md --out migration/runtime-a/out.json
python3 run_task.py --runtime b --prompt prompt.md --out migration/runtime-b/out.json
diff -u migration/runtime-a/out.json migration/runtime-b/out.json | tee migration/diff.txt
cp -r config config.rollback
```

预期观察：diff 有输出即说明两侧存在可观测差异，须逐条归类；config.rollback 已生成，可随时切回旧配置。

## 证据

- **同一段提示词在新一代模型上可能从有效变成反效果，效力不能随写法一起搬运。**（S-0015，official）
  - 出处：https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt-5/gpt-5_prompting_guide.ipynb
  - 原文关键句：Cursor found that sections of their prompt that had been effective with earlier models needed tuning ... they found it counterproductive with GPT-5
- **prefill 这项能力在新一代模型上被移除，旧写法在新运行时上直接以请求错误告终。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：prefilled responses ... on the last assistant turn are no longer supported. Requests with prefilled assistant messages to these models return a 400 error.
- **迁移的处置动作是按新能力面重编译参数，而不是保留旧参数继续调用。**（S-0003，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/extended-thinking
  - 原文关键句：You need to migrate off `type: "enabled"` if: ... where `type: "enabled"` returns a 400 error. ... remove `budget_tokens`, set `thinking: {type: "adaptive"}`

## 术语

- **换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）**：提示词中的多数经验与具体模型绑定；更换模型后必须重跑评测并重做优化，而不是沿用旧结论。
- **标记敏感度的迁移性（Transferability of Markup Sensitivity）**：对某种标记（如 XML 标签）的响应强度取决于该模型是否针对此类标记做过指令对齐训练，因此同一标记在不同模型上的效果不可假定一致。
- **自适应思考（Adaptive Thinking）**：由模型自行决定思考深度的现行机制，取代手动指定思考 token 预算的旧做法；后者在新一代模型上已返回错误。

## 失效模式

- 把迁移当复制粘贴：旧写法在新运行时上静默失效，输出照旧生成，但原有的判据已不再成立。
- 只对比最终答案、不对比两侧输入：运行时隐式注入带来的差异被漏掉，问题被误判成模型能力不足。
- 沿用旧代际的调优结论：已经变成有害的写法被继续保留，质量下降却找不到原因。
- 迁移后不留回滚点：新写法一旦不达标，只能凭记忆重写旧配置，恢复成本高于迁移本身。

## 一句话小结

跨运行时迁移的正确动作是重测、重编译并保留回滚点，而不是复制粘贴。

## 在本站知识结构中的位置

- 前置：PE-P-06
- 后继：PE-N-01
