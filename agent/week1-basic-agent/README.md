# Week 1 Basic Agent

这个目录是 Week 1 的实验说明目录。

实际可运行代码在：

- `agent/week1_basic_agent/`
- `cli/week1_basic_agent.py`

## 目标

实现一个最小 CLI Agent，理解以下链路：

```text
用户输入 -> 路由判断 -> 工具调用或直接回答 -> trace -> 最终输出
```

## 本周工具

- `read_file`
- `list_dir`

## 运行方式

```bash
python -m cli.week1_basic_agent --input "请读取 README.md，并总结这个项目的学习目标。" --trace
```

