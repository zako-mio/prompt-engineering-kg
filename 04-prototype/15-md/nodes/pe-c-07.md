# 模型上下文协议（Model Context Protocol）

- 节点标识：PE-C-07
- 英文名：Model Context Protocol
- 所属分组：G03 上下文工程
- 依赖深度：第 12 层
- 内容状态：内容已写满
- 标签：上下文工程、MCP、协议

## 为什么需要它

工具与数据源各自为战、无法复用，是 2024 年之前上下文接入的主要工程痛点；模型上下文协议用一套标准接口把这件事收敛掉，并把治理问题一并标准化。掌握它是为了能判断接入方案该复用协议还是自建，以及协议能覆盖与不能覆盖什么。

**适用边界**

协议只定义接口与治理边界，不提供编排、状态机维护或提示词优化能力；官方也明确其标准输入输出传输不是沙箱，安全责任仍在使用方。

## 机制说明

协议以 JSON-RPC 为底层，标准化客户端与服务端之间的双向通信，并定义三类原语及其控制权归属：提示模板由用户控制、资源由应用控制、工具由模型控制。传输侧现行规范支持标准输入输出与可流式 HTTP，旧的 HTTP 加 SSE 传输已列为弃用。治理侧已经中立化：协议现由 Linux Foundation 下的基金托管，规范采用宽松开源许可。现行规范版本相对上一版有破坏性变更——转为无状态并移除了初始化握手与会话，旧实现需要相应改造；同时部分早期特性进入弃用。

## 何时该用 / 何时不该用

- 需要接入多种外部数据源或工具、且希望复用既有实现时：优先采用协议而非自建接口。
- 需要供应商中立的接入层时：协议的中立治理与开源许可是选型依据。
- 不适用于把协议当编排方案：编排、状态机与提示词优化须由上层承担。
- 不适用于假设传输层提供隔离：官方明确标准输入输出传输不是沙箱。

## 实验台

### file（python）

```python
# mcp_tools_audit.py —— 用一条 tools/list 响应校验协议侧可审计形状，并跑一个反例
import copy, json

RESP = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [
    {"name": "read_file", "description": "读取工作区内的文本文件",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "list_dir", "description": "列出目录条目",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}}},
]}}

def audit(resp):
    problems = []
    if resp.get("jsonrpc") != "2.0":
        problems.append("非 JSON-RPC 2.0")
    tools = resp.get("result", {}).get("tools") or []
    if not tools:
        problems.append("tools 为空")
    names = [t.get("name") for t in tools]
    if len(names) != len(set(names)):
        problems.append("工具名重复")
    for t in tools:
        if not t.get("description"):
            problems.append("缺 description：%s" % t.get("name"))
        if (t.get("inputSchema") or {}).get("type") != "object":
            problems.append("inputSchema 非 object：%s" % t.get("name"))
    return problems

ok = audit(RESP)
bad = copy.deepcopy(RESP)
bad["result"]["tools"][1]["name"] = "read_file"
bad["result"]["tools"][0].pop("inputSchema")
bad_problems = audit(bad)

assert ok == [], "合法响应被判有问题：%s" % ok
assert len(bad_problems) == 2, "反例命中数不符：%s" % bad_problems
print(json.dumps({"tools": len(RESP["result"]["tools"]), "ok_problems": ok,
                  "bad_problems": len(bad_problems)}, ensure_ascii=False))
```

预期观察：脚本退出码 0 并打印一行 JSON，其中 tools 为 2，ok_problems 为空数组，bad_problems 为 2（重名一条加重名后缺 inputSchema 一条）。改动 RESP 使合法响应被判出问题时，第一条断言失败并以 AssertionError 退出。

## 证据

- **协议把三类原语的控制权分别划给用户、应用与模型，工具一栏归模型控制。**（S-0020，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/server
  - 原文关键句：Tools: Executable functions ... | Prompts | User-controlled | Resources | Application-controlled | Tools | Model-controlled |
- **现行规范的传输只列标准输入输出与可流式 HTTP 两种，前者是客户端启动子进程上的换行分隔消息。**（S-0021，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
  - 原文关键句：1. stdio: newline-delimited messages over the standard streams of a client-launched subprocess. 2. Streamable HTTP: each message is an HTTP POST to a single MCP endpoint
- **官方安全声明明确 SDK 不为标准输入输出通道的两端提供防护，且该传输不是沙箱。**（S-0025，official）
  - 出处：https://modelcontextprotocol.io/community/security
  - 原文关键句：The SDK does not defend either peer against a malicious counterpart across the stdio channel... The SDK's stdio transport is not a sandbox.

## 术语

- **模型上下文协议（MCP）**：以 JSON-RPC 为底层、标准化 AI 客户端与外部数据/工具源之间双向通信的开放协议；现行规范为 2026-07-28 版，治理归属 Linux Foundation 下的 AAIF。
- **MCP 三大原语（Prompts / Resources / Tools）**：MCP 服务端暴露的三类能力：提示模板（用户控制）、资源（应用控制）、工具（模型控制）。
- **间接提示词注入（Indirect Prompt Injection）**：恶意指令藏在模型会读取的外部内容（网页、邮件、文档、工具返回、记忆）中，而非由用户直接输入。

## 失效模式

- 症状：把协议当成编排方案，指望它管状态机、重试与分支。后果：编排与提示词优化都不在协议定义范围内，接入之后仍要自建上层，工期与集成风险被系统性低估。
- 症状：假设标准输入输出传输自带隔离，直接挂载不可信的服务端。后果：官方安全声明写明该传输不是沙箱且两端可能持有等价的环境权限，一次恶意服务端即可越界到宿主。
- 症状：照旧版规范实现，保留初始化握手与会话状态。后果：现行规范已转为无状态并移除握手，旧实现在新客户端下无法完成连接，升级时才暴露成套改造工作量。
- 症状：把工具返回当可信输入，不设调用权限与审计。后果：工具由模型控制并可被自动发现与调用，外部内容里的指令能直接转成实际动作，越权操作事后难以归因。

## 一句话小结

协议统一了接口与治理，但不含编排与沙箱；安全责任仍然在使用方。

## 在本站知识结构中的位置

- 前置：PE-C-06
- 后继：PE-P-06
