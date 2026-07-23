# Week 1 Sample Runs

Status: first runnable examples recorded.

## Run 1: direct answer

Command:

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot."
```

Input:

```text
Explain the difference between an agent and a chatbot.
```

Output summary:

```text
An agent makes task-oriented decisions, can call tools, can keep state, and can complete work through multiple steps.
```

## Run 2: read README

Command:

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals."
```

Input:

```text
Read README.md and summarize the project learning goals.
```

Output summary:

```text
The agent reads README.md and returns a concise summary of the beginning of the document.
```

## Run 3: directory overview

Command:

```bash
python -m cli.main --input "List the main project directories and explain what they are responsible for."
```

Input:

```text
List the main project directories and explain what they are responsible for.
```

Output summary:

```text
The agent lists the project directories and explains the responsibilities of agent/, cli/, prompts/, evals/, tests/, docs/, and related directories.
```

## Run 4: error handling

Command:

```bash
python -m cli.main --input "Read not-exist.md."
```

Input:

```text
Read not-exist.md.
```

Output summary:

```text
The tool call fails safely because not-exist.md does not exist.
```

