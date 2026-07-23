# cli/

放命令行入口和本地调试入口。

适合放：

- `python -m ...` 或 `node ...` 的入口封装
- 交互式 CLI
- demo runner
- 本地调试命令

不要在这里放核心业务逻辑。CLI 应该只负责解析参数、加载配置、调用 `agent/` 中的能力。

## 当前入口

当前入口：

```bash
python -m cli.main --input "请解释 Agent 和普通聊天机器人的区别。"
```

带 trace：

```bash
python -m cli.main --input "请读取 README.md，并总结这个项目的学习目标。" --trace
```
