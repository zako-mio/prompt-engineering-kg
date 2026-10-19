# 模型上下文协议接入实况（MCP in Practice）

- 节点标识：PE-P-06
- 英文名：MCP in Practice
- 所属分组：G09 落地实践
- 依赖深度：第 24 层
- 内容状态：内容已写满
- 标签：落地实践、MCP、接入

## 为什么需要它

接入 MCP 的真实工作量集中在选型与治理，而不是协议解析：用本地子进程还是远程端点、协议版本怎么钉、服务端从哪里来、哪些声明会进入上下文，每一项都有现行一手口径可查，也都有各自典型的失效方式。把这些当成配置细节随手决定，代价通常在上线后才显形：本地传输被误当成隔离边界，或者旧实现按有状态假设继续运行。

**适用边界**

本节点的口径以 2026-07-28 版规范、官方注册中心说明与官方安全策略为准；换到更早的协议版本时，握手、会话与传输的结论都要重新核对。这些结论覆盖的是协议层与官方分发层，具体某个服务端的实现质量、权限配置与数据处理方式仍须单独审计，不能由协议合规替代。

## 机制说明

MCP 的接入面可以按五件事逐条落定。第一是传输：现行规范给出两种，标准输入输出面向由客户端拉起的本地子进程、消息按行分隔，可流式 HTTP 则把每条消息作为一次 HTTP POST 发到单一端点、回复以 JSON 对象或请求级事件流返回。第二是信任边界：官方安全策略明确，标准输入输出下客户端与服务端可能拥有同等的环境级权限，并且该传输不是沙箱，因此选它并不等于获得隔离。第三是版本：现行协议版本为 2026-07-28，修订分草稿、现行、终稿三态，接入时应把版本号写进配置与回归用例，而不是跟随最新。第四是来源：官方注册中心是面向公开服务端的集中元数据仓库，且明确不支持私有服务端，私有服务需要自建分发与核验路径。第五是能力面：服务端以提示模板、资源与工具三类声明暴露能力，控制权分别归用户、应用与模型，接入评审要逐类确认哪些声明会进入上下文。2026-07-28 版把会话做成无状态，移除了初始化握手，改由每个请求自带协议版本与客户端能力，按有状态假设写的旧实现需要改造。

## 何时该用 / 何时不该用

- 接入第三方服务端前：核验来源是否在官方注册中心、把协议版本钉进配置，并逐类审查它暴露的提示模板、资源与工具。
- 选择传输方式时：本地受控环境用标准输入输出，跨主机或需要共享服务时用可流式 HTTP，两者信任边界不同。
- 从旧版协议迁移时：按无状态前提改造，处理初始化握手移除与会话取消带来的改造点。
- 不适用于把标准输入输出传输当成隔离边界：官方明确它不是沙箱，客户端与服务端可能拥有同等环境级权限。
- 不适用于把官方注册中心当成私有服务的分发渠道：它只收录公开服务端，不支持私有服务端。

## 实验台

### shell（bash）

```bash
# 1) 列出 MCP 客户端配置里挂了哪些服务端，以及各自用的传输
for f in "$HOME/.config/mcp/servers.json" ./.mcp.json; do
  [ -f "$f" ] || continue
  echo "== $f =="
  python3 - "$f" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
servers = d.get("mcpServers", d)
for name, cfg in servers.items():
    transport = "stdio" if "command" in cfg else cfg.get("type", "http")
    print("%-24s %-10s %s" % (name, transport, cfg.get("command") or cfg.get("url")))
PY
done

# 2) 协议版本是否被钉住：配置里应当出现现行版本号
grep -RIn "2026-07-28" "$HOME/.config/mcp" ./.mcp.json 2>/dev/null || echo "未钉版本：配置里没有出现协议版本号"
```

预期观察：第一段逐行输出服务端名、传输方式（stdio 或 http）与启动命令或端点地址；第二段在配置里找到现行版本号时逐条打印命中行，找不到则打印未钉版本，提示把版本号写进配置与回归用例。

### file（python）

```python
# 接入评审：把服务端声明的能力面逐类列出，并标出需要人工确认的写操作
declared = {
    "prompts": ["review_checklist"],
    "resources": ["repo://README.md"],
    "tools": ["search_issues", "create_issue", "delete_branch"],
}
WRITE_HINTS = ("create", "delete", "update", "write", "push", "merge")
for kind, names in declared.items():
    for name in names:
        risky = kind == "tools" and any(h in name for h in WRITE_HINTS)
        print("%-9s %-16s %s" % (kind, name, "需确认" if risky else "只读"))
```

预期观察：逐行列出提示模板、资源与工具三类声明，命中写操作关键词的工具被标为需确认、其余标为只读；据此把接入评审落成一张可逐条勾选的能力面清单，而不是只看服务端名字就放行。

## 证据

- **现行规范给出两种传输：标准输入输出用于客户端拉起的本地子进程，可流式 HTTP 用于单一端点的远程接入，选型即决定接入形态。**（S-0021，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
  - 原文关键句：1. stdio: newline-delimited messages over the standard streams of a client-launched subprocess. ... 2. Streamable HTTP: each message is an HTTP POST to a single MCP endpoint
- **官方安全策略明确标准输入输出传输下客户端与服务端可能拥有同等的环境级权限，且该传输不是沙箱。**（S-0025，official）
  - 出处：https://modelcontextprotocol.io/community/security
  - 原文关键句：When using the stdio transport, the client spawns the server as a local subprocess and both might run with equivalent environment-level privilege. ... The SDK's stdio transport is not a sandbox.
- **2026-07-28 版把 MCP 转为无状态并移除初始化握手，改由每个请求自带协议版本与客户端能力，旧实现须按此改造。**（S-0022，official）
  - 出处：https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - 原文关键句：Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request now carries its protocol version and client capabilities in `_meta`...
- **官方版本页给出当前协议版本号与修订三态，接入时应据此钉住版本而不是跟随最新。**（S-0023，official）
  - 出处：https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning
  - 原文关键句：The current protocol version is 2026-07-28. ... Revisions may be marked as: Draft / Current / Final.
- **官方注册中心是公开 MCP 服务端的集中元数据仓库，并明确不支持私有服务端。**（S-0026，official）
  - 出处：https://modelcontextprotocol.io/registry/about
  - 原文关键句：The MCP Registry is the official centralized metadata repository for publicly accessible MCP servers ... The MCP Registry does not support private servers.

## 术语

- **模型上下文协议（MCP）**：以 JSON-RPC 为底层、标准化 AI 客户端与外部数据/工具源之间双向通信的开放协议；现行规范为 2026-07-28 版，治理归属 Linux Foundation 下的 AAIF。
- **MCP 三大原语（Prompts / Resources / Tools）**：MCP 服务端暴露的三类能力：提示模板（用户控制）、资源（应用控制）、工具（模型控制）。

## 失效模式

- 把标准输入输出传输当成沙箱：客户端与服务端可能拥有同等的环境级权限，被污染的服务端可以直接读写本机资源。
- 不钉协议版本：配置里没有版本号，服务端或规范一变就无法判断是哪一侧变了，回归用例定位不到原因。
- 只看服务端名字就接入：没有逐类审查提示模板、资源与工具声明，写操作类工具会在无人确认的情况下进入可用能力面。
- 沿用有状态假设的旧实现：握手与会话被移除后初始化流程空转，请求缺少协议版本与客户端能力而失败。

## 一句话小结

MCP 接入要逐条落定五件事：传输选型与信任边界、协议版本钉法、服务端来源核验、能力面逐类审查，以及无状态化带来的迁移改造。

## 在本站知识结构中的位置

- 前置：PE-C-07
- 后继：PE-P-07
