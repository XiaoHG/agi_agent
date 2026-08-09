# v43：Long-Horizon Memory and Session Continuity

## 本阶段目标

把项目从“能保存单次运行”推进到“能在多个运行之间保持会话和任务连续性”，为后续真实工业 Agent 的长任务工作流打基础。

## 本阶段在工业 Agent 中的位置

工业 Agent 不可能只靠当前上下文长期工作。

它必须具备：

- session memory
- task memory
- 跨运行连续性
- 与 checkpoint / replay / resume 联动

`v43` 解决的是“Agent 如何在多次运行之间记住自己正在做什么”。

## 本阶段解决的问题

- 让 checkpoint 之外再有一层可持续更新的长程记忆
- 让会话和任务拥有稳定 ID
- 让 resume 不只恢复 route，也恢复 session / task 连续性
- 让 CLI 能直接查看 session memory 和 task memory

## 本阶段新增能力

### 1. SessionMemory

新增 `SessionMemory`，记录：

- session_id
- run_ids
- recent_inputs
- active_task_ids
- key_facts
- continuity_notes

它负责描述“这个会话最近发生了什么”。

### 2. TaskMemory

新增 `TaskMemory`，记录：

- task_id
- objective
- latest_route
- related_tools
- related_skills
- related_delegations
- latest_answer_preview
- continuity_notes

它负责描述“这个任务当前进展到了哪里”。

### 3. MemorySnapshot

每次 `WorkspaceAgent.run()` 持久化时，都会同步生成 `MemorySnapshot` 并写入 trace。

这让：

- checkpoint
- replay
- resume
- CLI

都能读取同一份连续性状态。

### 4. CLI memory inspection

`cli.main` 现在支持：

- `--session-id`
- `--task-id`
- `--list-session-memory`
- `--list-task-memory`
- `--show-session-memory`
- `--show-task-memory`

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `agent/memory.py` | 新增长程记忆模型与本地 JSON store |
| `agent/core.py` | `WorkspaceAgent` 接入 session/task memory |
| `agent/persistence.py` | checkpoint 摘要展示 session/task 信息 |
| `agent/replay.py` | replay / resume 接入 memory continuity |
| `agent/__init__.py` | 导出 memory 相关类型 |
| `cli/main.py` | 新增 memory CLI 入口 |
| `tests/test_memory.py` | 新增长程记忆测试 |
| `tests/test_persistence.py` | 增加 CLI / resume / memory 联动测试 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么要区分 session memory 和 task memory

因为“这次会话经历了什么”和“这个具体任务进展到哪里”不是同一层问题。

- session memory 关注跨轮次上下文
- task memory 关注具体任务连续性

### 2. 为什么 memory 不能只放在 checkpoint 里

checkpoint 更像一次运行快照。

memory 要解决的是多次运行的连续累计，因此必须有独立存储模型，而不是每次都只看单条 checkpoint。

### 3. 为什么 resume 要恢复 session / task ID

因为真正的连续性不是“再跑一次同样的 route”，而是“继续同一个会话里的同一个任务”。

## 运行示例

运行并写入指定 session/task：

```bash
python -m cli.main \
  --input "Read README.md and summarize the project learning goals." \
  --session-id learning-session \
  --task-id readme-learning
```

查看 session memory：

```bash
python -m cli.main --session-id learning-session --show-session-memory
```

查看 task memory：

```bash
python -m cli.main --task-id readme-learning --show-task-memory
```

## 验证命令

```bash
python -m unittest tests.test_memory tests.test_persistence -v
python -m unittest discover -s tests -v
```

## 当前边界

- 这是本地 JSON 长程记忆层，不是向量记忆或外部 memory service
- task id 默认仍是规则推断，不是语义任务聚类
- memory 先服务于连续性和调试，不做自动任务规划

## 下一步建议

下一阶段建议进入：

`v44：Industrial Evaluation Matrix and Failure Bench`

重点是把现在已有的 route / tool / skill / replay / recovery / memory 统一纳入更专业的评估矩阵。
