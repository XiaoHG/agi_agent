# MCP 本地协议骨架阶段复盘

## MCP 和普通本地函数调用有什么区别？

- 普通本地函数调用是代码内部直接调用函数，调用方需要知道具体函数位置、参数结构和返回结构。
- MCP 更强调协议边界：server 声明工具，client 按协议发起请求，response 用统一结构返回。
- MCP 可以让不同工具以统一方式暴露给 Agent；未来 server 可以在本进程内，也可以通过真实 transport 暴露给多个客户端。
- 当前项目里的 MCP 仍是本地模拟，但已经把“直接函数调用”拆成了 server、client、request、response 和 adapter 几层。

## server、client、adapter 分别负责什么？

- server：声明可用工具，并真正执行工具逻辑，例如 `workspace_summary` 和 `read_project_file`。
- client：面向调用方封装请求过程，把工具名和参数组装成 `MCPRequest`，再交给 server。
- adapter：把 MCP client/server 的能力转换成当前 Agent 可以调用的本地工具接口，例如 `list_mcp_tools()` 和 `call_mcp_tool()`。

## 当前本地 MCP 模拟和真实 MCP 接入有什么差异？

- 当前实现是进程内调用，没有真实网络、stdio、HTTP 或 SDK transport。
- 当前 schema 是简化版，只表达工具名、参数和返回内容。
- 真实 MCP 会涉及更完整的 capabilities、tools/resources/prompts、连接生命周期、错误协议和权限边界。
- 当前重点是学习工程分层，不是实现完整 MCP 标准。

## 为什么工具声明需要 `input_schema`？

- `input_schema` 用来描述工具需要什么参数、参数类型是什么、哪些参数必填。
- 对 Agent 来说，schema 是选择和调用工具的依据。
- 对 server 来说，schema 是校验输入和暴露能力边界的契约。
- 没有 schema，工具调用会退化成不稳定的自由文本约定。

## 当前实现的最大限制是什么？

- 最大限制是它还不是完整 MCP 接入，只是本地模拟协议边界。
- 没有真实 transport，因此不能验证跨进程、跨服务或远程 server 调用。
- 没有完整权限模型，当前只做了路径越界保护。
- 暴露的工具数量很少，还没有和 workflow、RAG 形成组合任务。

## 下一阶段是否可以进入 Skills 与 Subagent？理由是什么？

可以进入下一阶段，但进入前应先提交当前 MCP 阶段，并保留一个明确限制：当前 MCP 是学习版本地模拟。

理由：

- Week 3 的两个核心闭环已经具备：RAG 能检索本地文档，MCP 能通过 server/client/adapter 暴露工具。
- 当前测试覆盖了 MCP 工具声明、正常调用、错误返回、路径越界和 Agent 路由。
- 继续深挖真实 MCP SDK 会明显扩大范围，容易偏离当前课程主线。
- 下一阶段 Skills 与 Subagent 正好可以复用已有工具、RAG 和 MCP 能力，学习如何把能力模块化和角色化。
