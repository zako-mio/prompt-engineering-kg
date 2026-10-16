# 声明式编译与签名（Declarative Compilation and Signatures）

- 节点标识：PE-E-06
- 英文名：Declarative Compilation and Signatures
- 所属分组：G05 评测与自动优化
- 依赖深度：第 18 层
- 内容状态：内容已写满
- 标签：声明式编译、DSPy、评测

## 为什么需要它

声明式编译把「写提示词」换成「声明输入输出签名加指标」，由编译器在指令与示例空间中搜索配置。它解决的是提示词无法版本化、换模型即失效这两个工程痛点，代价是引入学习曲线与编译成本。把提示词从手写文本变成可编译的声明，改动的评审对象就从措辞变成了签名与指标，团队才能在换模型或扩任务时复用同一套编译流程，而不是重新手写一遍提示词。

**适用边界**

编译产物与指标、训练集、具体模型三者绑定，任一改动都要重编译，不能把某次编译出的指令集当作可跨模型搬运的固定资产；签名只声明输入输出字段的形状，字段语义与业务正确性仍由指标与评测集承担；此外它不适合无评测集的探索阶段，缺乏可自动计算的指标时搜索没有方向。

## 机制说明

基本构件有三个：签名（声明输入与输出字段）、模块（把调用组织成流水线）、优化器（在指令与示例空间中搜索）。编译器按指标在训练集上搜索，产出可直接使用的指令与少量示例。官方文档给出的选型判据是两轴：瓶颈在指令、示例还是权重，以及可用的算力预算；并给出起步建议与在两者都弱且预算充足时的推荐。现行主推路径把某个基于反思的优化器作为入门教程，并在最近版本中把其结构化指令提议器设为默认；另一个优化器的官方定位是「指令与示例需要一起调时最先进」。工程上还有两点必须同时立起来：编译方向由指标定义，指标写错则搜索会把错误的目标优化得更彻底；编译产物与具体模型绑定，换模型后须重跑评测与编译，而不是沿用旧产物。

## 何时该用 / 何时不该用

- 多阶段流水线、人工调优成本高时：先写签名与模块骨架，再交给优化器搜索指令与示例，人工只审签名与指标。
- 需要换模型后快速重建配置时：保留签名、模块与指标不动，只对新模型重跑一次编译，用同一批评测集对比前后得分。
- 不适用于把某个优化器当唯一最优：官方明确否认存在单一最优且不提供自动选择，选型要按瓶颈位置与预算自己判断。
- 不适用于跳过小规模验证直接上量：签名设计错误会被编译过程放大，先用小样本跑通编译与评测闭环再扩数据。

## 实验台

### shell（bash）

```bash
# 声明式编译的最小闭环：签名 + 模块 + 指标，先跑通再谈调优
python3 - <<'PY'
import dspy

class QA(dspy.Signature):
    """回答用户问题，事实不足时明说。"""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

prog = dspy.Predict(QA)

def metric(example, pred, trace=None):
    return example.answer.strip() == pred.answer.strip()

trainset = [dspy.Example(question=q, answer=a).with_inputs('question')
            for q, a in [('2+2?', '4'), ('3+4?', '7')]]
print('编译前:', sum(metric(e, prog(question=e.question)) for e in trainset), '/', len(trainset))

opt = dspy.MIPROv2(metric=metric, auto='light')
compiled = opt.compile(prog, trainset=trainset)
print('编译后:', sum(metric(e, compiled(question=e.question)) for e in trainset), '/', len(trainset))
print(compiled.dump_state()['traces'] if hasattr(compiled, 'dump_state') else compiled)
PY
```

预期观察：脚本先打印编译前的命中数，再打印编译后的命中数，且不报错——说明签名、模块、指标三者已构成可跑的编译闭环；指标换成随机标签后编译不再提升，暴露指标决定编译方向这一点。

### prompt（markdown）

```markdown
任务：把「工单分类」从手写提示词迁到声明式编译。
第 1 步（只做声明，不写措辞）：写出签名——输入字段为 ticket_text，输出字段为 category 与 confidence；再写出模块的调用顺序。
第 2 步（定义指标）：给出可自动计算的判据（例如 category 与标注一致记 1 分，confidence 与正确性不匹配扣 0.2）。
第 3 步（编译）：在训练集上搜索指令与少量示例，产出可用的编译产物。
第 4 步（留出验证）：在未参与编译的留出集上对比编译前后的得分，并记录换模型后需要重跑编译这一事实。
```

预期观察：四个步骤把「声明—指标—编译—验证」摆成可评审的顺序；若第 2 步的指标不可自动计算，第 3 步就会失去方向，这一失败会当场暴露在留出集的得分上。

## 证据

- **论文一手报告：DSPy 只需几行代码与数分钟编译，就让 GPT-3.5 与 llama2-13b-chat 自举出的流水线超过标准少样本提示与专家手写示例，量化了声明式编译的收益与成本量级。**（S-0045，paper）
  - 出处：https://arxiv.org/abs/2310.03714
  - 原文关键句：Within minutes of compiling, a few lines of DSPy allow GPT-3.5 and llama2-13b-chat to self-bootstrap pipelines that outperform standard few-shot prompting … expert-created demonstrations
- **官方文档明确否认存在单一最优优化器，也不做自动选择：auto 旋钮只控制单个优化器内部预算，不负责选型——这直接把「照抄推荐值」定为误用。**（S-0080，official）
  - 出处：https://dspy.ai/current/diving-deeper/choosing-an-optimizer/
  - 原文关键句：DSPy doesn't introspect your task or LM to pick an optimizer. The `auto` knobs on MIPROv2 and GEPA only control budget within an optimizer, not which optimizer to use.
- **发布说明显示编译器的默认指令提议器随版本变化（3.4.1 把 GEPA 的结构化 InstructionProposer 设为默认），说明编译产物的行为与版本绑定，升级时需重编译与重评测。**（S-0083，official）
  - 出处：https://api.github.com/repos/stanfordnlp/dspy/releases/latest
  - 原文关键句："tag_name":"3.4.1" … "DSPy 3.4.1 makes GEPA's structured InstructionProposer the default instruction proposer"

## 术语

- **声明式编译与签名（Declarative Compilation and Signatures）**：把 LLM 调用声明为带输入输出字段的签名，再由编译器在指令与示例空间中搜索最优配置；代表实现为 DSPy。
- **换模型即失效与重编译（Model Swap Invalidates and Requires Recompilation）**：提示词中的多数经验与具体模型绑定；更换模型后必须重跑评测并重做优化，而不是沿用旧结论。

## 失效模式

- 把签名当注释随手写：输入输出字段命名含糊、必填与可选不分，编译过程会把这种含糊放大成流水线级错误，且错误定位不到具体字段。
- 指标不可自动计算就开始编译：评分只能靠人读，搜索失去方向，编译只是把随机改动包装成「已优化」，留出集上不会出现真实提升。
- 照抄某个优化器当固定答案：官方否认存在单一最优且不提供自动选择，选错方向会白烧预算，正确做法是按瓶颈在指令、示例还是权重来选。
- 把一次编译产物当固定资产搬到别的模型上：编译产物与模型、指标、训练集三者绑定，换模型不重编译会把旧结论带进新环境，失效点难以归因。

## 一句话小结

签名、模块与优化器构成可编译的声明式流程，产物随指标、训练集与模型绑定；选型按瓶颈与预算决定，没有单一最优。

## 在本站知识结构中的位置

- 前置：PE-E-05
- 后继：PE-E-07
