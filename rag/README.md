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

当前专业 RAG v1 增加了本地 deterministic embedding 和 JSON vector index：

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

默认 index 输出到 `data/rag-index.json`，用于学习 vector index rebuild、chunk metadata 和 source citation 的基本流程。
