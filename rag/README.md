# rag/

放 RAG 相关实验。

适合放：

- 文档加载
- 文档切分
- embedding
- 向量检索
- rerank
- 检索结果拼接
- RAG 问答评估

建议不要把原始私密文档提交到仓库。原始数据可放 `data/raw/`，该目录默认被 `.gitignore` 忽略。

当前专业 RAG v1/v49 已增加本地 deterministic embedding、JSON vector index、后端元数据、增量更新计划和 citation 校验：

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

默认 index 输出到 `data/rag-index.json`，用于学习 vector index rebuild、chunk metadata 和 source citation 的基本流程。

当前后端硬化能力：

- embedding backend descriptor
- index backend descriptor
- document fingerprints
- incremental index update plan
- grounded answer citation validation
