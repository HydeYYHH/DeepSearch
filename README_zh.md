# DeepSearch
[English](https://github.com/HydeYYHH/DeepSearch/blob/master/README.md)     [中文](https://github.com/HydeYYHH/DeepSearch/blob/master/README_zh.md)

DeepSearch 是一个由 LLM 驱动的网络搜索引擎，专注于深度网络信息检索。

## 截图
![example1](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/weather_example.gif)
![example2](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/compare_example.gif)

## 技术架构

DeepSearch 采用模块化架构，以实现高效的网络搜索和 LLM 驱动的处理：

- **前端**：使用 React 和 Vite 开发响应式用户界面，处理搜索输入、会话管理和结果显示。
- **后端 (LLM Agent)**：基于 FastAPI 的 API 端点，集成 gemini-2.5-flash 模型和 langgraph 框架构建深度搜索工作流。![workflow](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/agent_workflow.svg)
- **搜索引擎**：采用基于网络爬虫的高度可定制化搜索引擎，使用 LlamaIndex 进行离线分块与向量检索；通过 SentenceSplitter 进行 512 token 分块并设置 128 token 重叠，使用 HuggingFace Embedding 进行本地嵌入，基于 VectorStoreIndex 完成相似度检索，从而减少搜索结果的 token 量并优化检索质量。![architecture](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/web_architecture.svg)
- **数据库**：通过 Peewee ORM 管理的 SQLite，用于存储会话和搜索历史。
- **其他组件**：代理池用于网络抓取、速率限制器用于 API 调用。

## 安装
### 手动安装
1. 克隆仓库：
    ```bash
    git clone https://github.com/HydeYYHH/DeepSearch
    cd DeepSearch
    ```
2. 设置搜索引擎
    ```bash
    cd search-engine
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3. 设置 LLM 代理
    ```bash
    cd llm-agent
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
4. 设置前端
    ```bash
    cd frontend
    npm install
    ```
5. 导入环境变量
    ```bash
    export GOOGLE_API_KEY=Your Google API Key
    ```
6. 运行应用
    ```bash
    cd search-engine
    source .venv/bin/activate
    python server/server.py
    ```
    ```bash
    cd llm-agent
    source .venv/bin/activate
    python main.py
    ```
    ```bash
    cd frontend
    npm run dev
    ```
### Docker部署
```bash
docker compose up
```