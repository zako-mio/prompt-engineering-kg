# 换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）

- 节点标识：PE-M-03
- 英文名：Model Swap Invalidates and Requires Recompilation
- 所属分组：G07 模型差异与迁移
- 依赖深度：第 19 层
- 内容状态：内容已写满
- 标签：模型迁移、重编译、回归

## 为什么需要它

换模型常被当成改一个字符串的轻量操作，实际上提示词中的多数经验都与具体模型绑定：同一段指令在旧模型上稳定通过，换到新模型后可能整段失效，而失败现场往往被误读成提示词写法退化。把换代当成一次重编译而不是一次配置替换，才能在模型迭代、推理参数改型与能力收回发生时守住质量底线：先建立新模型基线，再区分模型差异与提示词问题，最后只改必要部分并跑全量回归。

**适用边界**

需要重建的只限于与模型相关的部分：指令措辞、示例选择、参数档位与格式约束强度；任务定义、输出契约、评测集与校验器这些与模型无关的部分应当复用，这也正是提示词工程值得投入的地方。

## 机制说明

提示词不是可移植资产，原因有四条：其一，模型对指令措辞的敏感度不同，同一句强调在旧模型上有效，在新模型上可能被直接忽略；其二，模型对示例的依赖程度不同，有的模型靠少量示例即可对齐格式，有的需要更完整的示例，有的已经不需要示例；其三，模型对格式约束的耐受度不同，把强约束加在已经内化格式的模型上反而会干扰推理；其四，推理能力的内化程度不同，这决定了显式推理指令是增益还是冗余。厂商侧的变更同样会让旧提示词失效：推理参数改型、旧写法在新模型上直接返回错误、某些能力被收回，都会让原本可用的技巧在换代后不可用。工程上应把换代写成固定动作：冻结模型版本与提示词版本，用同一评测集建立新基线，逐条归因失败项，只对与模型相关的部分重做优化，再跑全量确认无回归；若使用声明式编译框架，换模型后重跑编译即可产出新的指令与示例配置。需要注意，评测集与校验器必须与模型解耦，否则每次换代都要重写评测逻辑，迁移成本会失控。

## 何时该用 / 何时不该用

- 更换底座模型或模型版本时：先冻结模型版本与提示词版本，用同一评测集建立新基线，再决定改动范围。
- 厂商发布弃用通告或收回能力时：逐条核对现有提示词中用到的技巧与参数，先迁移到现行写法，再评估效果。
- 使用声明式编译框架时：换模型后重跑编译产出新配置，而不是手工逐句改写提示词。
- 不适用于沿用旧模型上的基线数字：那会把模型侧的能力差异记成提示词改动的涨跌。

## 实验台

### shell（bash）

```bash
cd prompts/
git rev-parse --short HEAD    # 提示词与评测集的版本标识
python3 evals/run_eval.py --model "$OLD_MODEL" --out reports/old.json
python3 evals/run_eval.py --model "$NEW_MODEL" --out reports/new.json
python3 evals/diff_reports.py reports/old.json reports/new.json --by-case
```

预期观察：两次运行使用同一评测集与同一校验器，只有模型标识不同；输出逐样本对比并按用例分组列出新增失败项，用于区分模型差异与提示词问题。若两份报告缺少同一评测集版本标识，则本次对比判定为不可比，不给出涨跌结论。

### prompt（markdown）

```markdown
你是一名提示词迁移分析员。输入是同一评测集上旧模型与新模型的两份逐样本结果，以及当前提示词的版本标识。请只依据输入作答，不引入外部知识。要求：一，列出新模型上新增的失败用例，并标注它们共同依赖的提示词特征，例如措辞强调、示例数量、格式约束强度、显式推理指令；二，把每个失败项归因为模型差异、提示词问题或能力收回三类之一，并给出依据；三，对需要改写的部分给出最小改动建议，对与模型无关的部分明确写出可以复用；四，若两份结果的评测集版本标识不一致，直接判定为不可比并停止分析。
```

预期观察：输出把新增失败用例逐条归因到模型差异、提示词问题或能力收回三类之一，给出最小改动建议，并显式列出可以复用的与模型无关部分；当两份结果的评测集版本标识不一致时，回答必须判为不可比，而不是继续比较分数。

## 证据

- **厂商在换代时直接收回能力：新模型不再支持末轮助手消息预填充，带预填充的请求返回错误，依赖该技巧的提示词必须重写。**（S-0001，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - 原文关键句：Starting with Claude 4.6 models and Claude Mythos Preview ... on the last assistant turn are no longer supported. Requests with prefilled assistant messages to these models return a 400 error.
- **推理参数在换代时改型：旧的思考开关写法与手动预算参数被弃用，新模型上直接报错，必须迁移到新的参数形态与档位。**（S-0003，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/extended-thinking
  - 原文关键句：You need to migrate off `type: "enabled"` if: You use Claude Opus 4.6 or Sonnet 4.6, where `budget_tokens` is deprecated. ... where `type: "enabled"` returns a 400 error.
- **厂商把可复用的提示对象 API 标记弃用并给出关停时间线，提示词因此必须作为应用代码的一部分被版本化与回滚。**（S-0011，official）
  - 出处：https://developers.openai.com/api/docs/guides/prompt-engineering
  - 原文关键句：OpenAI is deprecating reusable prompt objects in the API. Prompt creation will be de-emphasized beginning June 3, 2026, and `v1/prompts` is scheduled to shut down on November 30, 2026.

## 术语

- **换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）**：提示词中的多数经验与具体模型绑定；更换模型后必须重跑评测并重做优化，而不是沿用旧结论。
- **声明式编译与签名（Declarative Compilation and Signatures）**：把 LLM 调用声明为带输入输出字段的签名，再由编译器在指令与示例空间中搜索最优配置；代表实现为 DSPy。
- **提示词版本化与回归（Prompt Versioning and Regression）**：把提示词当作代码资产纳入版本控制，并在每次改动后跑同一评测集对比基线，防止无声退化。

## 失效模式

- 把换模型当成改一个字符串：旧提示词直接上线，失败现场被误读成提示词写法退化，团队在错误的层面上反复调参。
- 沿用旧模型上的基线数字：模型侧的能力差异被记成提示词改动的涨跌，据此接受一个实际更差的版本。
- 把评测逻辑与模型耦合：校验器里写死某个模型的输出习惯，每次换代都要重写评测，迁移成本失控。
- 没有可回滚的版本：换代失败时只能整体回退模型，无法只回退提示词侧的那一次改动，定位范围被放大。

## 一句话小结

提示词不是可移植资产：换代、参数改型或能力收回发生后，必须重建基线、只重做与模型相关的部分并跑全量回归，同时保留可回滚的版本。

## 在本站知识结构中的位置

- 前置：PE-M-02
- 后继：PE-M-04
