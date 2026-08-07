# v07 练习：Project Learning Assistant

对应版本：v07  
主题：Project Learning Assistant  
用途：理解综合项目如何组合前面所有能力

## 练习

1. 这个阶段为什么不再只做单点能力？
2. Project Learning Assistant 组合了哪些能力？
3. 为什么综合项目必须保留 CLI、tests、eval 和 docs？
4. `docs/current-learning-state.md` 在这个阶段的作用是什么？

## 答案

1. 因为项目目标已经转向可演示、可学习、可回归的完整原型。
2. 它组合了文件读取、RAG、MCP、Skills、Subagent 和评估。
3. 因为没有这些支撑层就只能算 demo，不能算可维护项目。
4. 它用于恢复学习进度和记录当前阶段判断。

## 验证

```bash
python -m cli.project_demo
python -m unittest discover -s tests -q
```
