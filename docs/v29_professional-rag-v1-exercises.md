# v29 练习：Professional RAG v1

## 练习 1：为什么专业 RAG 需要 vector index？

回答：

1. 关键词检索和 vector retrieval 的核心区别是什么？

   关键词检索主要看 query 和文档 chunk 之间是否出现相同词项，适合精确词匹配、简单稳定、容易调试，但对同义表达和问题改写不敏感。

   vector retrieval 会先把 query 和 chunk 都转换成向量，再用相似度分数排序。它的目标是让系统可以按“语义接近程度”找上下文，而不是只依赖字面词重合。本阶段的实现仍然加了 token overlap guard，因为当前 hashing embedding 不是高质量语义模型，需要避免 hash collision 造成无关命中。

2. 为什么本阶段先使用 deterministic local embedding？

   因为本阶段目标是先建立专业 RAG 工程闭环，而不是追求 embedding 质量。deterministic local embedding 有几个好处：

   - 不依赖网络和外部 API key。
   - 测试和 eval 结果稳定。
   - 接口形态接近真实 embedding provider，后续可以替换成外部 embedding 服务或本地模型。
   - 便于先验证 chunk metadata、index rebuild、citation、Agent tool、tests 和 eval 是否接通。

3. 当前实现离真正 production RAG 还差什么？

   当前实现还不是生产级 RAG。主要差距包括：

   - embedding 只是本地 hashing，不是真实语义 embedding。
   - vector index 是 JSON 文件，不是 FAISS、Chroma、LanceDB 或其他专业 vector store。
   - 没有 reranker，也没有 query rewrite。
   - chunk 策略仍然简单，缺少按标题、语义段落、文档类型优化的切分。
   - 没有增量索引、索引版本管理和大规模数据加载策略。
   - citation 已经具备基础能力，但还没有完整的 grounded answer 质量评估和人工审阅流程。

## 练习 2：理解 chunk metadata

回答：

1. `VectorRecord` 为什么不只保存 embedding？

   只保存 embedding 只能完成相似度计算，不能支撑完整 RAG 工作流。RAG 检索命中后，还需要知道命中的是哪段文本、来自哪个文件、具体行号范围是什么，以及如何把来源展示给用户或传给 LLM。

   所以 `VectorRecord` 同时保存：

   - `chunk`：原始文本片段和来源位置。
   - `embedding`：用于相似度检索。
   - `metadata`：用于 citation、调试、导出和未来扩展。

2. `source`、`start_line`、`end_line` 对 RAG 有什么价值？

   它们把检索结果从“一段看起来相关的文本”升级成“可定位、可验证的证据”。用户、测试和后续 LLM 都可以通过这些字段知道上下文来自哪里。

   具体价值：

   - `source` 说明命中文档。
   - `start_line` 和 `end_line` 说明命中的行号范围。
   - 调试错误检索时，可以直接回到原文件定位。
   - eval 可以断言是否命中了合理来源，而不只看生成文本是否像答案。

3. citation 为什么应该从 chunk metadata 生成？

   citation 应该是检索数据模型的一部分，而不是回答阶段临时拼出来的字符串。这样可以保证同一个 chunk 在 vector search、grounded prompt、Agent tool output、trace 和 eval 中使用一致的来源标签。

   当前 citation 格式是：

   ```text
   source:start_line-end_line
   ```

   例如：

   ```text
   README.md:1-40
   ```

## 练习 3：理解 index rebuild

回答：

1. 为什么专业 RAG 需要单独的 rebuild CLI？

   因为索引构建是 RAG 系统里的独立工程步骤，不应该隐藏在每次问答内部。单独的 rebuild CLI 可以让开发者明确执行：

   ```text
   load documents -> chunk -> embed -> build index -> save index
   ```

   它的价值是：

   - 方便手动验证索引数量和检索结果。
   - 方便在文档变化后重建索引。
   - 方便未来接入定时任务、CI 或部署流程。
   - 把“索引构建失败”和“问答生成失败”拆开排查。

2. `data/rag-index.json` 属于什么类型的文件？

   它是本地实验生成产物，不是核心源码文件。它保存当前文档集合构建出的 vector index，包括 schema version、dimensions、records、chunk 文本、embedding 和 metadata。

   这类文件更接近缓存或本地数据产物。是否提交要看项目策略；当前快照说明里把它视为本地实验产物，不要求作为源码提交。

3. 什么时候需要重新 rebuild index？

   以下情况需要重新 rebuild：

   - README、docs、versions 等被索引文档发生变化。
   - chunk 参数变化，例如 `max_lines` 或 `overlap` 调整。
   - embedding 模型或维度变化。
   - metadata schema 变化。
   - 新增或删除了需要进入 RAG 的文档路径。
   - 怀疑检索结果和当前文档内容不一致。

## 练习 4：理解 Agent tool 接入

回答：

1. `search_vector_docs` 和 `search_docs` 的职责有什么区别？

   `search_docs` 是原有本地关键词检索工具，适合验证基础 RAG、精确词命中和简单文档搜索。

   `search_vector_docs` 是 v29 新增的专业 RAG 检索入口，它走 vector index，输出 citation 和 vector score，用于学习 chunk metadata、embedding、vector search 和 source evidence。

2. 为什么普通 `search_docs` 不应该被直接替换掉？

   因为这是学习项目里的渐进式演进。直接替换会带来几个问题：

   - 破坏之前阶段已经通过的测试和 eval。
   - 让关键词检索和 vector 检索的行为差异无法对比。
   - 当前 vector retrieval 还只是本地 hashing 原型，不适合作为唯一检索策略。
   - 保留旧工具可以作为 fallback，也便于定位新检索链路的问题。

3. 为什么 `search_vector_docs` 也要进入 tool schema？

   因为 tool schema 是 LLM tool calling 能看到的工具目录。只有进入 schema，模型才有机会在工具选择阶段主动选择 `search_vector_docs`。

   如果只在规则 router 中接入，那么它只能被固定关键词触发；进入 tool schema 后，它也能参与 LLM-assisted tool selection 和未来 LangGraph/Planner 的工具规划。

## 练习 5：理解 eval

回答：

1. `rag-vector-search` eval 验证了哪些行为？

   它验证至少三类行为：

   - 路由行为：请求 `Use professional RAG to search docs for MCP.` 应该进入 `use_tool`。
   - 工具选择：tool name 应该是 `search_vector_docs`。
   - 输出行为：答案中应该包含 vector context、citation 和相关上下文，而不是走普通 `search_docs` 或 direct answer。

2. 为什么 eval 不应该依赖真实 embedding 网络请求？

   eval 的核心要求是可重复、可比较、低成本。如果依赖真实 embedding 网络请求，会引入：

   - 网络不稳定。
   - API key 依赖。
   - 调用成本。
   - 模型版本变化导致结果波动。
   - CI 或离线环境无法运行。

   所以本阶段用 deterministic local embedding 保证 eval 稳定。真正接入外部 embedding provider 后，也应该保留 deterministic eval 或 mock/stub 方案。

3. citation 和 vector score 对评估有什么帮助？

   citation 让 eval 能检查检索是否命中了可定位来源，而不是只判断答案文本是否看起来合理。

   vector score 让开发者能观察排序和相关性变化。它不一定直接作为严格断言，因为模型和索引策略变化会影响分数，但它对调试和回归分析很重要。

## 练习 6：手动验证

完成下面命令，并记录关键输出：

```bash
python -m unittest tests.test_rag -v
python -m cli.eval_runner
python -m cli.rag_index_demo --question "agent workflow"
python -m cli.main --input "Use professional RAG to search docs for MCP." --trace
```

回答：

已执行验证命令。

### 1. `python -m unittest tests.test_rag -v`

关键输出：

```text
Ran 18 tests in 0.060s

OK
```

说明：本地 RAG、vector index、Agent tool、router 和 CLI 相关单测通过。

### 2. `python -m cli.eval_runner`

关键输出：

```json
{
  "total": 19,
  "passed": 19,
  "failed": 0
}
```

说明：当前 regression eval 全部通过，其中 `rag-vector-search` 已验证 `search_vector_docs` 路径。

### 3. `python -m cli.rag_index_demo --question "agent workflow"`

关键输出：

```text
Vector index saved: data/rag-index.json
Records: 562
Dimensions: 64

Query: agent workflow
- README.md:316-355 score=0.679
- docs/plans/v1_learning-master-plan.md:1-40 score=0.668
- docs/plans/v2_week1-task-plan.md:71-110 score=0.667
```

回答：`rag_index_demo` 当前生成了 562 条 records。

### 4. `python -m cli.main --input "Use professional RAG to search docs for MCP." --trace`

关键输出：

```text
Route request: use_tool / search_vector_docs

[Tool] search_vector_docs
Result: found 3 vector context chunk(s) for 'Use professional RAG to search docs for MCP.'.

Citation 1: docs/v09_deepseek-rag-exercises.md:771-797
Citation 2: docs/v09_deepseek-rag-exercises.md:1-40
Citation 3: versions/v04_mcp-local-protocol.md:176-205
```

回答：

1. `search_vector_docs` 输出中的 citation 是：

   - `docs/v09_deepseek-rag-exercises.md:771-797`
   - `docs/v09_deepseek-rag-exercises.md:1-40`
   - `versions/v04_mcp-local-protocol.md:176-205`

2. trace 中 route 是：

   ```text
   use_tool
   ```

3. trace 中 tool name 是：

   ```text
   search_vector_docs
   ```
