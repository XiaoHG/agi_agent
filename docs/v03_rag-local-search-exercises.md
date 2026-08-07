# v03 练习：本地 RAG 最小闭环

对应版本：v03  
主题：Local RAG  
用途：理解检索、证据和 grounded answer 的最小实现

## 练习

1. 为什么本阶段先做本地检索，而不是直接接向量库？
2. `search_docs()` 和 `answer_docs_with_llm()` 的职责差异是什么？
3. 为什么 grounded answer 必须保留 source evidence？
4. `tests/test_rag.py` 主要在验证什么？

## 答案

1. 先把检索链路、证据拼接和回答结构打通，再升级基础设施更稳。
2. `search_docs()` 偏检索，`answer_docs_with_llm()` 偏基于证据生成答案。
3. 因为没有证据的答案很难判断是否真的来自上下文。
4. 它验证检索、路由、回答和失败路径是否符合预期。

## 验证

```bash
python -m unittest tests.test_rag tests.test_rag_llm -v
python -m cli.rag_demo --question "What does workflow mean in this project?"
```
