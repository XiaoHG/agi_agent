# AI Agent（智能体）正式出版书籍推荐（市面可购，区分**中文实战书 / 英文经典工程书 / 理论学术经典**）
按学习路径分层：入门实战 → 架构进阶 → 多智能体系统 → 底层理论。
> 说明：只收录**正规出版社纸质图书**，不包含网络讲义、预印本、在线专栏。

## 一、中文实战书籍（国内已出版，适合Python开发者优先入手）

### 1. 《动手做AI Agent：大模型应用开发》｜蔺佳 人民邮电出版社
- **定位：入门首选**
- 内容：Agent基础循环（感知-规划-行动-记忆）、ReAct、工具调用；基于 LangChain、LangGraph、AutoGen 从零搭建单智能体；配套完整代码。
- 适合：有Python基础，第一次动手写Agent，从Demo起步。

### 2. 《LangGraph智能体设计模式与多智能体开发》｜王晓华 清华大学出版社
- **定位：LangGraph专项进阶**
- 内容：LangGraph 状态图、分支、循环、9种经典Agent架构模式； Supervisor主从多智能体、业务落地案例。
- 适合：想要掌握**生产级状态型智能体**，摆脱简单链式Agent开发者。

### 3. 《智能体工程驱动AI Agent开发》｜王晓华 清华大学出版社
- **定位：工程化视角，从原型走向上线**
- 内容：智能体需求分析、架构选型、记忆体系、评估、监控、错误处理；打通“原型→产品”鸿沟。

### 4. 《多智能体协同：基于大语言模型的工程实践与系统构建》｜周佺喜 电子工业出版社（2026新书）
- **定位：多Agent系统中文稀缺好书**
- 内容：AutoGen / LangGraph / CrewAI 对比；A2A、MCP协议、智能体通信、任务协商、分工调度。
- 适合：想要搭建智能体团队、数字员工集群。

### 5. 《构建Agentic AI系统：打造能推理、可规划、自适应的AI智能体》
原著：*Building Agentic AI Systems*，清华大学出版社（茹炳晟 译，2025.12）

- **定位：架构必读书（强烈推荐）**
- 核心：智能体自主循环、规划、反思、记忆、容错设计；不只讲框架，讲**智能体系统设计思想**。
- 适合：开发者、架构师，理解为什么很多Agent原型无法落地。

### 6. 《AI Agent开发全书》｜博文视点
覆盖单/多智能体、LangGraph、CrewAI、Swarm、MCP；附带金融、物流真实行业案例，偏企业落地。

## 二、英文原版经典工程书籍（适合进阶、架构、想阅读第一手资料）

1. **Agent Design Patterns（Peter Belcak，Manning）**
    当前Agent领域公认**设计模式圣经**。系统归纳规划、反思、路由、记忆、工具调用、多智能体协作通用范式。
2. **AI Agents in Action (2nd Edition)（Manning）**
    实战导向，LangChain生态，单智能体→多智能体，大量可运行代码。
3. **Building Agentic AI Systems（Packt）**
    中文版已引进，英文原版更新更快；聚焦自治智能体控制循环、自适应系统。
4. **Designing Multi-Agent Systems**
    多智能体架构、冲突协商、通信机制，适合做智能体集群、数字组织。
5. **Building Generative AI Agents: Using LangGraph, AutoGen, and CrewAI**
    三大主流多智能体框架横向对比，快速选型参考。

## 三、经典理论书籍（传统智能体基础，建立底层认知，适合科研/算法）
> 大模型LLM-Agent是新兴方向，传统多智能体理论仍是根基
1. **Artificial Intelligence: Foundations of Computational Agents（Poole & Mackworth）**
    智能体经典教材，自主智能、规划、博弈、不确定性推理；很多高校AI课程教材。
2. **Reinforcement Learning: An Introduction（Sutton & Barto）**
    强化学习圣经；理解**学习型智能体、序列决策**必备，LLM+RL智能体的理论基础。
3. **Human-Compatible AI（Stuart Russell）**
    智能体目标对齐、安全性、可控制自治系统；思考Agent伦理与长期风险。

### ✅ 给你两类**合法免费/正版电子版渠道**
## 一、完全开源、作者公开授权免费下载（无版权风险，优先推荐）
《深入理解 AI Agent：设计原理与工程实践》李博杰
GitHub开源书籍（Apache2.0协议，允许自由下载PDF/EPUB）
项目地址：https://github.com/bojieli/ai-agent-book
在线阅读：https://bojieli.github.io/ai-agent-book/
PDF下载：前往项目的 Releases 页面直接获取

这本书内容覆盖Agent基础、工具调用、LangGraph、多智能体、生产实践，非常适合入门学习。

## 二、付费正版电子书购买渠道（前面书单里商业书籍正规电子版）
1. **异步社区（人民邮电）**
《动手做AI Agent》等异步图书官方电子版，支持EPUB/PDF
网址：https://www.epubit.com
2. **京东读书 / 当当读书**
绝大多数清华、电子工业出版社AI Agent新书都有正版电子书
3. **Leanpub / Packt（英文原版）**
Agent Design Patterns、AI Agents in Action 英文原版官方电子书平台

## 三、额外免费学习替代资源（不用买书也能系统学Agent）
1. LangGraph、AutoGen、CrewAI 官方文档（自带大量案例）
2. DeepLearning.AI Agent专项公开课
3. HuggingFace Agent开源教程