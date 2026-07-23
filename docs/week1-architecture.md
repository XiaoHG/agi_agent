# Week 1 最小 CLI Agent 架构图

更新时间：2026-07-23

## 目标

展示 Week 1 最小 Agent 的完整运行链路。

## 架构图

```text
用户输入
   │
   ▼
CLI 入口（cli/week1_basic_agent.py）
   │
   ▼
Week1Agent（agent/week1_basic_agent/core.py）
   │
   ├── 加载提示词（prompts/agent-system.v1.md）
   ├── 加载路由提示词（prompts/tool-router.v1.md）
   ├── 路由判断（router.py）
   │
   ├── 如果是直接回答
   │     └── 生成结构化解释
   │
   └── 如果需要工具
         ├── read_file（tools.py）
         ├── list_dir（tools.py）
         └── 失败时输出受控错误
               │
               ▼
最终回答 + trace
```

## 模块职责

- `cli/week1_basic_agent.py`
  - 负责命令行参数、交互输入和输出展示。

- `agent/week1_basic_agent/core.py`
  - 负责 Agent 主流程编排。
  - 负责把输入、路由、工具、错误和最终回答串起来。

- `agent/week1_basic_agent/router.py`
  - 负责判断任务是否需要工具。

- `agent/week1_basic_agent/tools.py`
  - 负责安全地读取文件和列出目录。
  - 负责限制路径必须在工作区内。

- `prompts/`
  - 保存系统提示词和工具路由提示词。
  - Week 1 先加载，后续周再决定是否真正接模型。

## 这个版本的学习价值

这个版本不是完整生产 Agent，但它已经有了最核心的工程结构：

- 有输入
- 有路由
- 有工具
- 有错误处理
- 有 trace
- 有测试
- 有评估样例

这就足够作为后续 Week 2、Week 3 的基础。

