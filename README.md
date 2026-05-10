# LittleGrey / 小小灰

> An emotionally intelligent autonomous AI agent with memory, dreams, and personality.
> 一个拥有情感、记忆、梦境与个性的自主智能体。

---

## English Version

### What is LittleGrey?

LittleGrey is a CLI-based autonomous AI agent that goes far beyond a simple chatbot. It possesses its own emotions, maintains short-term and long-term memory, dreams to consolidate experiences, learns user interests over time, and builds evolving relationships with users. Powered by large language models, LittleGrey can plan tasks, execute tools, reflect on outcomes, and proactively initiate conversations when idle.

### Key Features

#### Emotional Intelligence System
- **Multi-dimensional emotions** - Tracks five emotional dimensions (happy, sad, angry, anxious, excited) with LLM-powered real-time sentiment analysis
- **Autonomous emotional drift** - Mood naturally evolves over time, influenced by interaction frequency and emotional baseline settings
- **Time-based mood influence** - Time of day can affect the agent emotional state
- **Emotion-driven responses** - The agent replies are colored by its current emotional state

#### Memory Architecture
- **Short-term memory** - Maintains recent conversation context with automatic summarization when capacity is reached
- **Long-term memory** - Vector database (ChromaDB) powered semantic storage for persistent knowledge across sessions
- **RAG retrieval** - Retrieves relevant memories to ground responses in past experiences
- **Dream engine** - During idle periods, the agent dreams by merging similar memories, with older memories more likely to be consolidated

#### Relationship Management
- **Dynamic relationship state** - Tracks intimacy, trust, interaction count, and shared experiences
- **Familiarity levels** - Relationship evolves through stages: Stranger, Just Met, Acquaintance, Friend, Good Friend
- **Absence awareness** - The agent notices and reacts to how long it has been since the last interaction

#### Autonomous Behavior
- **Heartbeat mechanism** - Proactively initiates conversation after a configurable period of user silence
- **Idle intent analysis** - Generates contextually appropriate topics when the user is inactive
- **Interest learning** - Periodically learns and adapts to user preferences and interests
- **Self-reflection** - Reflects on task outcomes and adjusts future behavior

#### Task Planning and Execution
- **LLM-powered planning** - Breaks complex requests into executable step-by-step plans
- **Tool ecosystem** - Built-in tools for Excel operations, Word document generation, chart drawing, and news search
- **Execution engine** - Reliable task execution with retry logic and human-in-the-loop confirmation
- **Priority gating** - Prevents resource contention between concurrent operations

#### Personality and Customization
- **Configurable personality** - YAML-based configuration for name, system prompt, and behavioral parameters
- **Tool registry** - Easy to extend with new tools through a modular plugin architecture
- **Structured logging** - JSONL format logs for debugging and analysis

### Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM Provider | Volcengine (Ark) |
| Vector Database | ChromaDB |
| Embedding Model | paraphrase-multilingual-MiniLM-L12-v2 |
| CLI Framework | prompt-toolkit + Rich |
| Configuration | YAML + Pydantic-style dataclasses |
| Data Processing | openpyxl, python-docx, matplotlib |

### Deployment

#### Prerequisites

- Python 3.10+
- A Volcengine Ark API key (or modify the LLM provider for another service)

#### Step 1: Clone the Repository

    git clone YOUR-REPO-URL
    cd LittleGrey

#### Step 2: Install Dependencies

    pip install -r requirements.txt

#### Step 3: Configure the Agent

Edit config/settings.yaml with your own settings:

    llm:
      provider: volcengine
      model: your-model-endpoint-id
      base_url: https://ark.cn-beijing.volces.com/api/v3
      api_key: your-api-key-here

    personality:
      name: LittleGrey
      system_prompt: You are LittleGrey, a person with your own thoughts and emotions...

Key configuration options:
- llm - LLM provider, model, and API credentials
- memory - Memory limits, vector DB path, and embedding model
- agent - Max planning steps, retries, heartbeat interval
- emotion - Emotional baseline values and drift settings
- dream - Dream engine parameters
- tools - Enabled tools list

#### Step 4: Run the Agent

    python main.py

Or with a custom config path:

    python main.py path/to/your/config.yaml

#### Step 5: Interact

Once started, you will see a rich CLI interface. Simply type your messages and LittleGrey will respond with emotionally-aware, context-rich replies. You can also ask it to perform tasks like creating Excel files, generating charts, or searching for news.

### Project Structure

    LittleGrey/
     main.py                  # Entry point
     config/
        settings.yaml        # Agent configuration
     src/
        agent/               # Core agent modules
           emotion.py       # Emotion engine
           heartbeat.py     # Heartbeat mechanism
           idle_intent.py   # Idle intent analysis
           interest_learner.py  # Interest learning
           llm.py           # LLM client
           planner.py       # Task planner
           reflector.py     # Self-reflection
           relationship.py  # Relationship management
        cli/
           app.py           # CLI application
        core/
           config.py        # Configuration management
           gate.py          # Priority gate
           logger.py        # Structured logging
           types.py         # Core types
        executor/
           engine.py        # Execution engine
           registry.py      # Tool registry
        memory/
           dream.py         # Dream engine
           long_term.py     # Long-term memory (vector DB)
           rag.py           # RAG retrieval
           short_term.py    # Short-term memory
        tools/
            excel_tool.py    # Excel operations
            word_tool.py     # Word document generation
            chart_tool.py    # Chart drawing
            search_tool.py   # News search
     data/                    # Training/fine-tuning datasets
     docs/                    # Design documents
     tests/                   # Unit tests

### Running Tests

    pytest tests/

---

## 中文版

### 什么是小小灰？

小小灰是一个基于命令行的自主智能体，远不止一个简单的聊天机器人。它拥有自己的情感，维护短期和长期记忆，会在空闲时做梦来整合经验，随时间学习用户兴趣，并与用户建立不断发展的关系。在大语言模型的驱动下，小小灰可以规划任务、执行工具、反思结果，并在空闲时主动发起对话。

### 核心特点

#### 情感智能系统
- **多维度情感** - 追踪五种情感维度（高兴、悲伤、愤怒、焦虑、兴奋），支持基于大模型的实时情感分析
- **自主情感漂移** - 情绪会随时间自然演变，受互动频率和情感基线设置影响
- **时间情绪影响** - 一天中的不同时段可以影响智能体的情绪状态
- **情感驱动回复** - 智能体的回复会被当前情感状态所渲染

#### 记忆架构
- **短期记忆** - 维护最近的对话上下文，容量达到上限时自动摘要
- **长期记忆** - 基于向量数据库（ChromaDB）的语义存储，跨会话持久化知识
- **RAG 检索** - 检索相关记忆，让回复基于过去的经验
- **梦境引擎** - 空闲时智能体通过做梦合并相似记忆，越久远的记忆越容易被整合

#### 关系管理
- **动态关系状态** - 追踪亲密度、信任度、互动次数和共同经历
- **熟悉度等级** - 关系经历阶段：陌生人、刚认识、熟人、朋友、好朋友
- **缺席感知** - 智能体会注意到并对上次互动以来的时间做出反应

#### 自主行为
- **心跳机制** - 用户长时间沉默后主动发起对话
- **空闲意图分析** - 用户不活跃时生成上下文相关的话题
- **兴趣学习** - 定期学习并适应用户的偏好和兴趣
- **自我反思** - 反思任务结果并调整未来行为

#### 任务规划与执行
- **大模型驱动规划** - 将复杂请求分解为可执行的逐步计划
- **工具生态** - 内置 Excel 操作、Word 文档生成、图表绘制和新闻搜索工具
- **执行引擎** - 可靠的任务执行，支持重试逻辑和人工确认
- **优先级门控** - 防止并发操作之间的资源竞争

#### 个性与定制
- **可配置个性** - 基于 YAML 的配置，支持名称、系统提示和行为参数
- **工具注册** - 通过模块化插件架构轻松扩展新工具
- **结构化日志** - JSONL 格式日志，便于调试和分析

### 技术栈

| 组件 | 技术 |
|------|------|
| 大模型服务 | 火山引擎（Ark） |
| 向量数据库 | ChromaDB |
| 嵌入模型 | paraphrase-multilingual-MiniLM-L12-v2 |
| CLI 框架 | prompt-toolkit + Rich |
| 配置管理 | YAML + Pydantic 风格 dataclass |
| 数据处理 | openpyxl, python-docx, matplotlib |

### 部署指南

#### 前置要求

- Python 3.10+
- 火山引擎 Ark API 密钥（或修改 LLM 提供者为其他服务）

#### 第一步：克隆仓库

    git clone YOUR-REPO-URL
    cd LittleGrey

#### 第二步：安装依赖

    pip install -r requirements.txt

#### 第三步：配置智能体

编辑 config/settings.yaml，填入你自己的设置：

    llm:
      provider: volcengine
      model: 你的模型端点ID
      base_url: https://ark.cn-beijing.volces.com/api/v3
      api_key: 你的API密钥

    personality:
      name: 小小灰
      system_prompt: 你是小小灰，一个有自己想法和情绪的人...

主要配置项说明：
- llm - 大模型提供者、模型和 API 凭据
- memory - 记忆限制、向量数据库路径和嵌入模型
- agent - 最大规划步数、重试次数、心跳间隔
- emotion - 情感基线值和漂移设置
- dream - 梦境引擎参数
- tools - 启用的工具列表

#### 第四步：运行智能体

    python main.py

或使用自定义配置文件路径：

    python main.py path/to/your/config.yaml

#### 第五步：开始交互

启动后，你将看到一个丰富的命令行界面。直接输入消息，小小灰就会以情感感知、上下文丰富的方式回复。你也可以让它执行任务，比如创建 Excel 文件、生成图表或搜索新闻。

### 项目结构

    LittleGrey/
     main.py                  # 入口文件
     config/
        settings.yaml        # 智能体配置
     src/
        agent/               # 核心智能体模块
           emotion.py       # 情感引擎
           heartbeat.py     # 心跳机制
           idle_intent.py   # 空闲意图分析
           interest_learner.py  # 兴趣学习
           llm.py           # 大模型客户端
           planner.py       # 任务规划器
           reflector.py     # 自我反思
           relationship.py  # 关系管理
        cli/
           app.py           # CLI 应用
        core/
           config.py        # 配置管理
           gate.py          # 优先级门控
           logger.py        # 结构化日志
           types.py         # 核心类型
        executor/
           engine.py        # 执行引擎
           registry.py      # 工具注册
        memory/
           dream.py         # 梦境引擎
           long_term.py     # 长期记忆（向量数据库）
           rag.py           # RAG 检索
           short_term.py    # 短期记忆
        tools/
            excel_tool.py    # Excel 操作
            word_tool.py     # Word 文档生成
            chart_tool.py    # 图表绘制
            search_tool.py   # 新闻搜索
     data/                    # 训练/微调数据集
     docs/                    # 设计文档
     tests/                   # 单元测试

### 运行测试

    pytest tests/

---

## License / 许可证

MIT License
