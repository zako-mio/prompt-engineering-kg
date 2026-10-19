# 成本—质量—延迟三角（Cost–Quality–Latency Triangle）

- 节点标识：PE-M-04
- 英文名：Cost–Quality–Latency Triangle
- 所属分组：G07 模型差异与迁移
- 依赖深度：第 20 层
- 内容状态：内容已写满
- 标签：成本、延迟、模型分层

## 为什么需要它

成本、质量与延迟三项指标互相牵制：提高质量通常以 token 成本与首字延迟为代价，压低成本又常以通过率下降为代价，因此三者必须放进同一张目标表里设定，否则会出现「质量达标但成本失控」或「成本达标但不可用」的结果。更关键的是，降本必须落到可测量的量上——每任务 token 数、每任务时延、每任务通过率——而不是停在「优化一下提示词」这类口号；否则一次改动究竟是省了钱，还是只是把开销挪到了重试与人工兜底上，无从判断。

**适用边界**

三角没有普适最优点，可行组合由业务目标决定：交互路径通常以延迟为硬约束，离线批处理通常以成本为硬约束，高风险环节则以质量为硬约束；它是一条约束关系而不是一条公式，具体取舍必须用评测集与成本数据共同验证，不能靠单价表推算。

## 机制说明

三角的机制是三组典型权衡。其一，推理深度与延迟成本：让模型思考更久通常更准，但思考 token 计入输出计费并直接拉长时延；其二，上下文规模与成本延迟：塞入更多资料能提高召回，却推高输入 token 与首字延迟；其三，采样次数与鲁棒性：多路径投票能提升鲁棒性，但成本随样本数近似线性增长，而准确率收益往往很早就饱和。工程做法分三步：先声明哪一维是硬约束、哪一维可以让（面向用户的问答通常以延迟为硬约束，离线批处理通常以成本为硬约束，合规审核则以质量为硬约束）；再在满足约束的候选里选最便宜的那个；最后用同一批评测样本测量三项指标并逐任务上报。可用的杠杆有四个：模型分层与路由（廉价模型做分类、抽取与格式化，贵模型只接真正难的请求）、推理档位（如 reasoning.effort 由低到高的档位）、输出长度与采样数（限制草稿长度、按收益曲线砍样本数）、以及提示缓存与批处理（稳定前缀复用、把非实时任务攒批）。

## 何时该用 / 何时不该用

- 设定系统目标时：先写清哪一维是硬约束、哪一维可以让，再在剩余空间里压成本。
- 做模型分层与路由时：用廉价模型承担分类、抽取与格式化，把贵模型留给真正难的请求。
- 不适用于只优化单一维度：压力会转移到另外两维，并制造出新的瓶颈。
- 不适用于把三角当精确公式：具体取舍必须用评测与成本数据验证，而不是靠单价推算。

## 实验台

### shell（bash）

```bash
# 三角标定：同一批评测样本，跑两套配置，逐任务记录三项指标
# A 组 = 廉价模型 + 低推理档（承担路由与抽取）；B 组 = 强模型 + 高推理档（只接难题）
for cfg in "cheap:low" "strong:high"; do
  model="${cfg%%:*}"; effort="${cfg##*:}"
  t0=$(date +%s%3N)
  curl -s "$API_ENDPOINT" -H 'content-type: application/json' \
    -d "{\"model\":\"$model\",\"reasoning\":{\"effort\":\"$effort\"},\"input\":\"<task>\"}" \
    -o "out-$model.json"
  t1=$(date +%s%3N)
  echo "$model effort=$effort latency_ms=$((t1-t0)) tokens=$(jq -r '.usage.total_tokens' out-$model.json)"
done
# 把两行的 latency_ms 与 tokens 同同一批样本的通过率并列，再判断哪一维是瓶颈
```

预期观察：两套配置各自打印每任务 token 与时延；把它们与同一批评测样本的通过率并列后，才能看出哪一维真正越界。只看单价表得不出这个结论，因为重试与采样会改变实际用量。

### file（markdown）

```markdown
# 三角目标表（每个任务族一行）
硬约束维：质量 / 延迟 / 成本（三选一，必须写清）
可让维：三选一，并注明可让到什么程度
质量下限：通过率 >= __%
延迟上限：p95 <= __ ms
成本上限：每任务 <= __ token（或每千任务 <= __ 元）
测量口径：每任务 token 数 / 每任务时延 / 每任务通过率，三项取自同一批样本
判据：任何一项越界即判该方案不可用，而不是「平均下来还行」
```

预期观察：读者能产出一张可判定的目标表：先声明硬约束与可让维，再用同一批样本测三项指标，任一项越界即判不可用。

## 证据

- **官方对适用范围的边界表述：并非所有成功标准或失败的评测都最适合用提示工程解决，换一个模型有时能更省力地改善延迟与成本，因此三角里降本降延迟的第一杠杆是选型而不是改提示词。**（S-0002，official）
  - 出处：https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
  - 原文关键句：For example, you can sometimes improve latency and cost more easily by selecting a different model.
- **现行官方口径给出推理努力档的取值闭集，并要求非 none 档位时移除温度与 top-p 等采样参数，说明推理档位是三角里可以直接调节的一维。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：Set `reasoning.effort` to `low`, `medium` (default), `high`, `xhigh`, or `max`. ... When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`.
- **量化证据：更精简的系统提示在内部编码 agent 评测样本中同时提高了评分并大幅降低 token 与成本，说明降本可以落到可测量的量上，而不必以质量为代价（厂商自述内部评测，官方自称方向性）。**（S-0012，official）
  - 出处：https://developers.openai.com/api/docs/guides/latest-model
  - 原文关键句：configurations with leaner system prompts improved evaluation scores by roughly 10–15% while reducing total tokens by 41–66% and cost by 33–67%.
- **采样路径数增加带来的准确率收益极小（20 样本下 HotpotQA 仅 0.4%、MATH-500 仅 1.6%），而 token 成本随样本数近乎线性增长，因此采样数是三角里最先饱和的一维。**（S-0058，paper）
  - 出处：https://arxiv.org/abs/2511.00751
  - 原文关键句：0.4% on HotpotQA across 20 samples, and 1.6% on MATH-500 -- while token costs scale nearly linearly with sample count

## 术语

- **成本—质量—延迟三角（Cost–Quality–Latency Triangle）**：三项工程指标互相牵制：提升质量常以 token 成本与延迟为代价，故三者须共同设定目标而非单独优化其一。
- **模型分层选型（Model Tiering）**：按任务难度把请求分派给不同能力档与价位的模型，用路由在成本与质量之间取得平衡。
- **推理努力档（Reasoning Effort）**：推理模型上控制思考深度的参数档位；启用非 none 档位时通常须移除温度与 top-p 等采样参数。
- **提示缓存（Prompt Caching）**：把稳定的提示前缀在服务端缓存复用，以降低重复前缀的延迟与计费成本；要求前缀稳定且顺序固定。

## 失效模式

- 把三角当口号：只说「要又快又准又便宜」，不写硬约束与可让维，选型时没人能判定哪个方案胜出。
- 用单价代替每任务成本：忽略重试、采样数与缓存命中率，账单与实际用量脱节，优化方向随之跑偏。
- 只压输出长度不看通过率：截断回答让 token 下降，但失败重试把总成本与尾延迟推得更高。
- 频繁改动系统提示以省 token：前缀不再稳定，缓存命中率归零，成本不降反升。

## 一句话小结

三角的正确用法是先声明硬约束与可让维，再用同一批样本测每任务 token、时延与通过率，任一项越界即判该方案不可用。

## 在本站知识结构中的位置

- 前置：PE-M-03
- 后继：PE-N-03
