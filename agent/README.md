# agent/

放 Agent 主链路实验。

适合放：

- 最小 Agent loop
- tool calling
- 多步 workflow
- 状态管理
- memory 机制
- observability 和错误处理

后续按能力模块迭代，不按周创建运行代码目录：

```text
agent/
  core.py
  router.py
  tools.py
  prompts.py
  state.py      # 后续需要状态管理时再添加
  memory.py     # 后续需要记忆能力时再添加
```

## 当前实现

当前 Python 包采用标准模块命名，保持代码层简洁：

```text
agent/core.py
agent/router.py
agent/tools.py
agent/prompts.py
```

核心文件：

- `core.py`：Agent 主流程。
- `router.py`：判断是否调用工具。
- `tools.py`：本地工具实现。
- `prompts.py`：加载 prompt 文件。
