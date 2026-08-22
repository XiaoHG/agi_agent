# Externalized Registry and Runtime Governance v55 练习

对应版本：v55  
主题：Externalized Registry and Runtime Governance  
用途：理解为什么能力层必须从本地静态定义继续走向外部化治理

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v54` 之后还不能说项目已经具备工业级能力治理？
2. `skills/registry.py` 主要解决什么问题？
3. `mcp/catalog.py` 主要解决什么问题？
4. 为什么 builtin / project / external 三层要同时保留？
5. 为什么 governance audit 必须记录 registry resolution？

## 练习 2：读外部治理链路

阅读：

- `skills/registry.py`
- `skills/catalog.py`
- `skills/execution.py`
- `skills/policy.py`
- `mcp/catalog.py`
- `mcp/servers/local_server.py`
- `mcp/adapter.py`
- `tests/test_collaboration.py`
- `tests/test_mcp.py`

请回答：

1. `get_available_skills()` 为什么要先合并 builtin，再合并 external，最后合并 project？
2. `call_mcp_tool_exchange()` 的审计链路新增了哪些阶段？
3. 为什么 external registry 不能直接覆盖所有 builtin 能力？
4. 为什么 policy profile 需要支持环境切换？
5. 为什么 validation 失败时也要保留 audit 记录？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_mcp -v
python -m cli.collaboration_demo --task "Review current changes before commit." --list-skills
python -m cli.mcp_demo --list-tools
```

请记录：

1. 是否能看到 external skill source？
2. 是否能看到 external MCP catalog tool？
3. 审计信息里是否出现 registry resolution？
4. 失败请求是否仍保留 governance audit？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么外部化 registry 是工业化治理的必要一步？
2. 为什么 environment-aware policy 比硬编码 policy 更适合后续扩展？
3. 为什么 `v55` 仍然是学习版，但已经更接近生产治理？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `v54` 主要解决的是长任务生命周期，还没有解决能力来源外部化和统一治理。
2. `skills/registry.py` 解决的是外部 skill registry 的读取、解析和来源汇总。
3. `mcp/catalog.py` 解决的是外部 MCP catalog 的读取和工具合并。
4. 因为工业系统通常同时存在默认能力、项目能力和外部能力，不能只保留一种来源。
5. 因为 registry resolution 本身就是治理事实，后续审计、回放和问题排查都需要它。

### 练习 2：读外部治理链路

1. 因为需要保留默认能力，再叠加外部能力，最后让项目定制能力拥有最高优先级。
2. 新增了 registry resolution、policy resolution、validation、permission 和 execution 等阶段。
3. 因为外部 registry 只是补充治理来源，不应该破坏系统最基本的默认能力。
4. 因为不同环境可能需要不同的 registry / catalog / policy 组合。
5. 因为失败本身也是治理事实，不能只保留成功路径。

### 练习 3：动手验证

1. 是，应能看到 external skill source。
2. 是，应能看到 external MCP catalog tool。
3. 是，应能看到 registry resolution。
4. 是，失败请求仍应保留 governance audit。

### 练习 4：工程取舍题

1. 因为工业治理必须可配置、可审计、可切换，而不是写死在代码里。
2. 因为环境驱动策略更容易适配不同部署场景。
3. 因为它已经把外部 registry、catalog、policy 和 audit 串起来了，但还没有真实远程治理中心。
