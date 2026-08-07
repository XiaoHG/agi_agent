# v01 练习：最小 CLI Agent

对应版本：v01  
主题：Minimal CLI Agent  
用途：理解一个最小 Agent 闭环如何从输入走到工具调用与回答

## 练习

1. 这个阶段的核心目标是什么？
2. `route_intent()` 在最小 Agent 里承担什么职责？
3. 为什么 `agent/core.py` 不能直接把所有逻辑写在一个函数里？
4. `tests/test_agent.py` 为什么是这个阶段最关键的回归入口？

## 答案

1. 先打通 `用户输入 -> 路由 -> 工具 -> 回答` 的最小闭环。
2. 它负责把自然语言转换成 `use_tool` / `direct_answer` 这类可执行路由。
3. 因为路由、工具执行、错误处理、回答渲染需要分层，否则后续无法扩展和测试。
4. 它直接验证最小 Agent 的行为是否稳定，是后续所有阶段的基础。

## 验证

```bash
python -m unittest tests.test_agent -v
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```
