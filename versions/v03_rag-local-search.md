# 本地 RAG 最小闭环 v3

版本：v3

日期：2026-07-24

## 本次目标

在 Week 2 状态与工作流基础上，加入 Week 3 的第一个能力：本地 RAG 最小闭环。

本次不引入 embedding、向量库或外部服务，而是先用可解释、可测试的本地关键词检索打通完整链路：

文档加载 -> 切分 -> 检索 -> 上下文组装 -> Agent 调用 -> CLI 输出

## 新增文件

### `rag/__init__.py`

行号范围：`1-15`

职责：

- 导出 RAG 相关基础能力
- 让 `rag` 成为可直接复用的包

### `rag/documents.py`

行号范围：`1-67`

职责：

- 定义 `Document`
- 从 `README.md`、`docs/`、`versions/` 加载本地文本
- 只接受 `.md` 和 `.txt`
- 防止路径越界

### `rag/chunking.py`

行号范围：`1-71`

职责：

- 定义 `TextChunk`
- 按行切分文档
- 支持 overlap
- 为后续检索和 trace 提供稳定 chunk 标识

### `rag/retrieval.py`

行号范围：`1-67`

职责：

- 定义 `SearchResult`
- 进行关键词检索
- 输出排序后的相关 chunk

### `rag/qa.py`

行号范围：`1-62`

职责：

- 组合加载、切分和检索
- 生成可读的 RAG 答案
- 输出来源引用和上下文预览

### `cli/rag_demo.py`

行号范围：`1-32`

职责：

- 提供独立的 RAG 命令行入口
- 便于直接测试检索链路

### `tests/test_rag.py`

行号范围：`1-67`

职责：

- 测试文档加载
- 测试 chunk 切分
- 测试检索排序
- 测试 Agent 路由到 `search_docs`
- 测试 CLI 级 RAG 闭环

## 修改文件

### `agent/tools.py`

变更行号范围：`1-92`

本次改动：

- 新增 `search_docs`
- 调用本地 RAG 结果并包装成 `ToolResult`

### `agent/router.py`

变更行号范围：`99-176`

本次改动：

- 新增 `_looks_like_knowledge_search()`
- 新增 `search_docs` 路由
- 调整路由优先级，避免 `workflow` 抢走“Search docs ...”这类请求

### `agent/core.py`

变更行号范围：`7-141`

本次改动：

- 接入 `search_docs` 工具分支
- 保持主流程不变，只增加新的工具能力

### `agent/__init__.py`

变更行号范围：`1-21`

本次改动：

- 导出 `search_docs`

### `pyproject.toml`

变更行号范围：`1-10`

本次改动：

- 将 `rag` 包纳入项目包列表

### `README.md`

变更行号范围：`126-164`

本次改动：

- 更新当前已完成阶段说明
- 新增 RAG CLI 示例

### `docs/current-learning-state.md`

变更行号范围：`1-113`

本次改动：

- 将当前阶段更新为 Week 3
- 增加 RAG 学习重点
- 更新恢复指令

## 新增功能

1. 可以通过 `search_docs` 搜索本地文档。
2. Agent 可以把“搜索文档”请求路由到本地知识检索工具。
3. 可以单独运行 `python -m cli.rag_demo` 查看检索结果。
4. 检索结果会输出来源、匹配词和上下文预览。

## 交互流程

### Agent 内部流程

```text
用户输入
  -> route_intent()
  -> search_docs / workflow / 其他工具
  -> tool execution
  -> answer synthesis
```

### RAG demo 流程

```text
question
  -> load local documents
  -> chunk documents
  -> retrieve relevant chunks
  -> render answer with sources
```

## 验证结果

- `python -m unittest discover -s tests -v`
- `python -m cli.main --input "Search docs for workflow." --trace`
- `python -m cli.rag_demo --question "What does workflow mean in this project?"`

结果：

- 所有测试通过。
- 主 Agent 能正确路由到 `search_docs`。
- RAG demo 能返回本地文档引用。

## 学习点评

这次迭代的重点不是“模型更聪明”，而是“链路更完整”。

做对的地方：

- 先做最小闭环，再考虑 embedding 和向量库。
- 检索结果带来源，便于复盘和评估。
- 把 RAG 作为工具接入主 Agent，避免知识模块和主流程脱节。

需要继续补的地方：

- RAG 评估 case 还不够。
- 检索仍然是关键词级别，还没到真正的向量检索。
- MCP 还没开始。
