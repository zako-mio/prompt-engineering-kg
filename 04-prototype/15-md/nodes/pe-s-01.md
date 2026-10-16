# 结构模式与约束解码（JSON Schema and Constrained Decoding）

- 节点标识：PE-S-01
- 英文名：JSON Schema and Constrained Decoding
- 所属分组：G01 确定性输出
- 依赖深度：第 6 层
- 内容状态：内容已写满
- 标签：确定性输出、JSON Schema、约束解码

## 为什么需要它

只要输出要被程序解析，格式失败就是可用性问题而不是体验问题：下游解析器一抛异常，整条链路就停在错误处理上。把结构合法性从「在提示里请求模型照做」下沉到「解码时由 schema 保证」，是提示词工程里少数能拿到确定性收益的手段。掌握它才分得清哪些格式约束该放进解码层、哪些只能留在提示层，也才知道为什么一个被放宽的 schema 会让严格模式形同虚设。

**适用边界**

它保证的只是结构合法：字段填错值、枚举选错项、数量级离谱都会被结构校验放过，schema 只能圈定形状，值域与业务正确性仍要由评测集和下游校验兜住。

## 机制说明

约束解码在采样的每一步先算出哪些 token 还落在合法路径上，把不合法的候选直接屏蔽掉再采样，所以结构合法性是生成过程中被保证的，而不是生成出来以后再校验。实现位置有三处：本地推理引擎或库把 schema 编译成文法后逐 token 过滤；托管 API 的严格模式由服务端完成同一件事；前两者都不可用时才退回到生成后校验并重试。API 侧的现行契约要求把模式收敛到可判定的子集：显式声明禁止额外属性、把必填字段全部列出——这与解码期屏蔽的实现方式直接相关，只有模式变成确定的有限状态约束，才可能逐 token 判定候选是否合法。工程上有两点后果：结构约束会收窄生成空间，推理密集的任务应拆成先自由推理、再格式化输出的两阶段；schema 本身要按接口契约评审，字段增删都算破坏性变更。

## 何时该用 / 何时不该用

- 输出要直接进下游程序时：用 API 侧严格模式或本地约束解码把结构合法性交给解码层，schema 随接口一起版本化。
- 任务既要复杂推理又要结构化结果时：拆成先自由推理、再格式化输出的两阶段，别指望单次带 schema 的调用同时做好两件事。
- 不适用于把结构合法当语义正确的验收依据：字段值是否可信仍要由评测集与下游业务校验判定。
- 不适用于在自由创作类任务上强加 schema：生成空间被收窄会直接压掉表达质量。

## 实验台

### shell（bash）

```bash
# 严格模式：schema 内禁止额外属性、必填字段全部列出（漏掉 required 或 additionalProperties 会退化成普通模式）
cat > schema.json <<'JSON'
{"type":"json_schema","json_schema":{"name":"invoice","strict":true,"schema":{
  "type":"object","additionalProperties":false,
  "required":["vendor","total","currency"],
  "properties":{"vendor":{"type":"string"},"total":{"type":"number"},"currency":{"type":"string"}}}}}
JSON
curl -s "$API_ENDPOINT" -H 'content-type: application/json' -d @payload.json > raw.json

python3 - <<'PY'
import json
r = json.load(open('raw.json'))
out = json.loads(r['choices'][0]['message']['content'])
json.dump(out, open('out.json', 'w'), ensure_ascii=False, indent=2)
d = json.load(open('out.json'))
print('字段齐全:', sorted(d))                       # 结构这一关
print('值抽查:', d.get('total'), d.get('currency'))  # 语义这一关
PY

# 连跑 10 次：结构关应当每次都过，值关只能靠与邮件原文比对
for i in $(seq 1 10); do python3 -c 'import json,sys; json.load(open(sys.argv[1]))' out.json && echo ok; done
```

预期观察：十次输出都能被解析器直接读入且三个字段齐全，说明结构失败在本节点上已被消除；但值抽查会把「结构合法不等于语义正确」当场暴露——金额与币种仍可能与邮件原文不符。

### prompt（markdown）

```markdown
第一段（不带 schema，自由推理）：
  阅读工单与日志，推导可能的根因。先写推理过程，再写结论；不要考虑输出格式。

第二段（带 schema 的严格模式，只做格式化）：
  把上一步的结论填入给定对象：root_cause / evidence / confidence / next_action。
  只输出该对象；不要重写推理过程；证据不足的字段留空字符串，不要编造。
```

预期观察：推理质量不再被 schema 压缩，而格式化这一步结构必然合法；对照实验里把两段合并成一次带 schema 的调用，同一批工单上的结论错误率会明显上升。

## 证据

- **现行官方严格模式以 strict: true 与 additionalProperties: false 的组合声明 schema，说明「禁止额外属性」是严格模式契约的组成部分，而不是可选的写法偏好。**（S-0014，official）
  - 出处：https://developers.openai.com/api/docs/guides/structured-outputs
  - 原文关键句：response_format: { type: "json_schema", json_schema: { name: "math_reasoning", strict: true, schema: { ... "additionalProperties": false } } }
- **约束解码被工具链自述为保证结构正确的手段，且已是主流推理引擎的默认结构化生成后端——证明这条路线的实现在解码层，而不是生成后的校验层。**（S-0093，official）
  - 出处：https://pypi.org/pypi/xgrammar/0.1.33/json
  - 原文关键句：It leverages constrained decoding to ensure 100% structural correctness ... It is the default structured generation backend for most LLM inference engines
- **论文一手结论：格式限制下模型的推理能力明显下降，且约束越严、推理任务的性能退化越大——这是「强结构约束有代价」的量化依据。**（S-0053，paper）
  - 出处：https://arxiv.org/abs/2408.02442
  - 原文关键句：we observe a significant decline in LLMs reasoning abilities under format restrictions. ... stricter format constraints generally lead to greater performance degradation in reasoning tasks

## 术语

- **约束解码（Constrained Decoding）**：在采样阶段按文法或 schema 屏蔽不合法的 token 路径，使输出在结构上必然合法；实现位置可以是本地推理引擎或库，也可以是托管 API 的严格模式。
- **结构化输出（Structured Output）**：以 JSON Schema 等模式约束模型输出结构的机制；API 侧的严格模式通常要求全部字段必填且禁止额外属性。
- **推理与格式的冲突（Reasoning–Format Conflict）**：在生成空间受限的格式约束下，模型的推理表现会下降，且约束越严退化越大；用先自由推理再格式化的两阶段可规避。

## 失效模式

- 把结构合法当语义正确：schema 一过就上线，字段值错、枚举选错、单位混用会直接流进下游，发现时已经写进库或发给客户。
- schema 放宽到解码期无法判定：用 anyOf、递归引用或条件必填等表达力过剩的写法，严格模式要么被拒、要么退化成不保证，结构失败又回来了。
- 在单次调用里同时要求深推理与强格式：约束越严推理退化越大，答案结构完美而结论错误，且这种错误不容易被结构校验发现。
- 把 schema 当写死的配置：字段增删不做版本化评审，上游提示与下游解析器同时改动，故障定位成本翻倍。

## 一句话小结

把结构合法性下沉到解码层去保证，语义正确性仍必须由评测集与业务校验承担。

## 在本站知识结构中的位置

- 前置：PE-F-06
- 后继：PE-S-02
