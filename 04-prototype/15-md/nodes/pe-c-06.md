# 提示缓存（Prompt Caching）

- 节点标识：PE-C-06
- 英文名：Prompt Caching
- 所属分组：G03 上下文工程
- 依赖深度：第 11 层
- 内容状态：内容已写满
- 标签：上下文工程、提示缓存、成本

## 为什么需要它

提示缓存把稳定前缀的重复计算省掉，是少见的「不改内容就能降本降延迟」的手段。它的前提是前缀逐字稳定、顺序固定，因此缓存友好性其实是一条提示词组织约束。缓存命中的判定单位是前缀而不是整段文本，因此任何前置改动都会让后面的缓存全部失效。

**适用边界**

缓存命中的收益只覆盖稳定前缀部分，若前缀本身很短或每次都变，缓存不会带来收益；此外缓存通常有存活时间，长时间不调用后首次请求仍需全量计算。

## 机制说明

缓存的实现方式是把请求前缀与服务端已计算的中间状态做匹配，命中则复用。因此影响命中的因素包括：前缀的逐字一致性、消息顺序、以及前缀的长度占比。实践中常见的破坏方式有四种：在前缀里插入时间戳或随机标识、把随会话变化的内容写进系统提示、动态拼接工具定义、以及在不同调用点使用措辞略有差异的同一段指令。改进办法是把提示按稳定性排序：最稳定的产品级约束放最前，其次任务级指令与工具定义，最后才是本次输入与检索资料；同时把易变内容集中到末尾，避免打断前缀。厂商文档把这条约束写得更具体：Azure 侧在最先的 1,024 个 token 内，只要有一个字符不同就算缓存未命中，可用 cached_tokens 是否为 0 判定；Bedrock 侧把缓存分为隐含与显式两型，各型的支持情况随模型与 API 变化，启用前要先查支持矩阵。

## 何时该用 / 何时不该用

- 存在重复出现的稳定前缀（系统提示、工具定义、长资料）时：按稳定性排序可提高命中率。
- 需要降本降延迟且提示结构稳定时：把缓存命中率纳入监控指标。
- 不适用于前缀每次都变的场景：缓存不会带来收益，反而可能增加复杂度。
- 不适用于把易变内容放前缀：时间戳与随机标识会破坏全部命中。

## 实验台

### file（python）

```python
# cache_prefix.py —— 稳定前缀前置、动态内容后置，并断言前缀指纹不随请求变化
import hashlib, json

STABLE = [
    "你是一名代码审查员，只按下面的检查单逐条给出结论。",
    "检查单：1 空指针 2 资源泄漏 3 边界条件 4 日志中的敏感字段。",
    "输出格式：每行一个 结论|条目编号|证据位置。",
]
TOOLS = [{"name": "read_file", "inputSchema": {"type": "object"}}]

def order(dynamic):
    """正确顺序：稳定段在前，动态内容作为最后一块"""
    blocks = STABLE + [json.dumps(TOOLS, sort_keys=True, ensure_ascii=False), dynamic]
    return "\n".join(blocks[:-1]), blocks[-1]

def order_bad(dynamic):
    """反例：把本次输入放到最前"""
    return "\n".join([dynamic] + STABLE + [json.dumps(TOOLS, sort_keys=True, ensure_ascii=False)])

def fp(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

a_prefix, a_tail = order("本次待审文件：a.py")
b_prefix, b_tail = order("本次待审文件：b.py")
stable = fp(a_prefix) == fp(b_prefix)
tail_only = a_tail != b_tail
bad_breaks = fp(order_bad("本次待审文件：a.py")) != fp(order_bad("本次待审文件：b.py"))

assert stable, "稳定段没被隔离：换一次输入前缀指纹就变了"
assert tail_only, "动态内容没有落在末尾：两次请求的尾部完全相同"
assert bad_breaks, "反例不成立：动态内容前置后前缀指纹仍然相同"
print(json.dumps({"prefix_sha": fp(a_prefix), "stable_prefix_unchanged": stable,
                  "dynamic_at_tail_only": tail_only, "dynamic_first_breaks_prefix": bad_breaks},
                 ensure_ascii=False))
```

预期观察：脚本退出码 0 并打印一行 JSON，其中 prefix_sha 为 12 位十六进制串，stable_prefix_unchanged、dynamic_at_tail_only、dynamic_first_breaks_prefix 三个键均为 true。若把 dynamic 拼进前缀而不放到末尾，前两条断言之一失败，脚本以 AssertionError 与非零退出码结束。

## 证据

- **Azure 侧缓存命中的判定落在缓存前缀的最先 1,024 个 token 内，一个字符不同即未命中，可用 cached_tokens 是否为 0 识别。**（S-0116，official）
  - 出处：https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/prompt-caching
  - 原文关键句：A single character difference in the first 1,024 tokens results in a cache miss, which is characterized by a cached_tokens value of 0.
- **提高命中率的工程动作是把稳定或重复内容放在提示开头、动态内容放在结尾，并保持会话上下文只追加。**（S-0116，official）
  - 出处：https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/prompt-caching
  - 原文关键句：Place stable or repeated content at the beginning of the prompt and dynamic content at the end. Keep conversation context append-only.
- **Bedrock 侧提示缓存分为隐含与显式两型，且每一型的支持情况随模型与 API 而不同。**（S-0117，official）
  - 出处：https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
  - 原文关键句：Amazon Bedrock supports two types of prompt caching: Implicit Prompt Caching and Explicit Prompt Caching. Support for each type varies by model and API.

## 术语

- **提示缓存（Prompt Caching）**：把稳定的提示前缀在服务端缓存复用，以降低重复前缀的延迟与计费成本；要求前缀稳定且顺序固定。

## 失效模式

- 症状：在前缀里插入时间戳、请求编号或当天日期。后果：最先 1,024 个 token 内任一字符不同就判为未命中，命中率归零，计费回到全量输入。
- 症状：把每轮都变的检索结果或用户档案写进系统提示。后果：缓存前缀被持续改写，排在它后面的稳定段也无法复用，稳定内容的复用价值被前排的变动吃光。
- 症状：以为缓存默认生效，不做 cached_tokens 观测。后果：厂商把缓存定义为可选特性且支持范围随模型与 API 变化，未启用时既无节省也无告警，成本评估建立在并不存在的收益上。
- 症状：每轮重排或重写历史消息来整理上下文。后果：只追加的约定被打破，前缀指纹变化使已缓存段落失效，长会话后段的延迟反而最高。

## 一句话小结

按稳定性排序提示内容，把易变内容压到末尾，并用命中率监控组织方式。

## 在本站知识结构中的位置

- 前置：PE-C-05
- 后继：PE-C-07
