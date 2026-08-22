# v55：Externalized Registry and Runtime Governance

## 本阶段目标

把 `v54` 的长任务生命周期能力，继续推进到外部化 registry 和统一运行治理。

`v54` 已经解决了：

- task lifecycle
- milestone
- watchdog
- pause / resume / expire / abandon

但工业级 Agent 继续往前走时，还需要解决：

- Skills 和 MCP 的来源如何外部化
- registry / catalog 如何统一加载
- policy 如何按环境切换
- governance audit 如何记录解析过程

`v55` 的目标就是把这些治理边界补齐。

## 本阶段在工业 Agent 中的位置

当能力层越来越多以后，系统不能只靠本地静态定义。

必须进一步回答：

- 这个 skill / tool 从哪里来
- 当前环境允许哪些能力
- 谁决定 policy profile
- 执行前如何留下审计证据

所以 `v55` 不是再加一个新能力，而是把能力接入统一 registry 和治理层。

## 本阶段解决的问题

- 为 skill registry 增加外部 JSON 来源
- 为 MCP catalog 增加外部 JSON 来源
- 为 Skills 和 MCP 增加环境驱动的 policy 加载
- 为 registry / policy 解析过程增加 audit trail
- 把 builtin / project / external 统一进可追踪 catalog

## 本阶段新增能力

### 1. External skill registry

新增：

- `skills/registry.py`

它负责：

- 读取外部 skill registry
- 解析 registry source
- 汇总 builtin / external registry 来源

### 2. External MCP catalog

新增：

- `mcp/catalog.py`

它负责：

- 读取外部 MCP catalog
- 解析外部 tool spec
- 与本地 server tool 集合合并

### 3. Environment-aware policy

Skills 与 MCP 都增加了：

- `AGI_AGENT_*_POLICY_PROFILE`
- `AGI_AGENT_*_REGISTRY_PATH`
- `AGI_AGENT_*_CATALOG_PATH`

这样可以让不同运行环境使用不同治理配置。

### 4. Registry governance audit

`execute_skill()` 和 `call_mcp_tool_exchange()` 现在都会记录：

- registry resolution
- policy resolution
- validation
- permission
- execution

这使得能力来源和治理过程可回放、可检查。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `skills/registry.py` | 外部 skill registry 加载 |
| `skills/catalog.py` | 合并 builtin / external / project skills |
| `skills/execution.py` | 增加 registry resolution / audit 轨迹 |
| `skills/policy.py` | 增加环境驱动的 skill policy |
| `mcp/catalog.py` | 外部 MCP catalog 加载 |
| `mcp/servers/local_server.py` | 合并外部 catalog tools |
| `mcp/adapter.py` | 增加 registry / policy / validation 审计 |
| `mcp/policy.py` | 增加环境驱动的 MCP policy |
| `cli/collaboration_demo.py` | 读取环境 policy 配置 |
| `cli/mcp_demo.py` | 读取环境 policy 配置 |
| `configs/skill-registry.json` | 外部 skill registry 示例 |
| `configs/mcp-catalog.json` | 外部 MCP catalog 示例 |
| `tests/test_collaboration.py` | 外部 registry 与审计测试 |
| `tests/test_mcp.py` | 外部 catalog 与审计测试 |

## 核心实现说明

### 1. 为什么要外部化 registry

因为学习版如果一直只靠代码内置定义，就无法逼近真实工业环境中的能力治理方式。

### 2. 为什么要保留 builtin / project / external 三层

因为工业系统通常不是单一来源，必须能同时支持：

- 代码内置默认能力
- 项目定制能力
- 外部注册表能力

### 3. 为什么 policy 要支持环境切换

因为同一套能力在不同环境里，允许范围可能不同。

### 4. 为什么 audit 不能省

因为 registry / policy / validation 的结果本身就是工业可观测性的一部分。

## 运行示例

查看外部 registry 技能：

```bash
python -m cli.collaboration_demo --task "Review current changes before commit." --list-skills
```

查看外部 MCP catalog：

```bash
python -m cli.mcp_demo --list-tools
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_mcp -v
python -m cli.collaboration_demo --task "Review current changes before commit." --list-skills
python -m cli.mcp_demo --list-tools
```

## 当前边界

- 当前 registry / catalog 仍是文件型外部化，不是真实远程服务
- 当前 policy 仍是本地环境驱动，不是企业统一权限中心
- 当前 audit 仍是学习型结构化记录，不是完整审计平台

## 下一步建议

`v55` 之后最自然的下一步是 `v56: Continuous Release Audit and Delivery Control`。

因为现在已经有了：

- runtime events
- replay / recovery
- release gate
- registry governance

接下来可以继续把交付判断推进到持续发布与审计闭环。
