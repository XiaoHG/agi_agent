# agent/

放 Agent 主链路实验。

适合放：

- 最小 Agent loop
- tool calling
- 多步 workflow
- 状态管理
- memory 机制
- observability 和错误处理

建议按周拆分，例如：

```text
agent/
  week1-basic-agent/
  week2-workflow-agent/
  week5-observability/
```

## 当前实现

Week 1 的实际 Python 包使用下划线命名：

```text
agent/week1_basic_agent/
```

原因：Python import 不支持带连字符的包名。`agent/week1-basic-agent/` 保留为学习说明目录。

核心文件：

- `core.py`：Agent 主流程。
- `router.py`：判断是否调用工具。
- `tools.py`：本地工具实现。
- `prompts.py`：加载 prompt 文件。
