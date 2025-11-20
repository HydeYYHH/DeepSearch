# DeepSearch
[English](https://github.com/HydeYYHH/DeepSearch/blob/master/README.md)     [中文](https://github.com/HydeYYHH/DeepSearch/blob/master/README_zh.md)

DeepSearch 是一个由 LLM 驱动的网络搜索引擎，专注于深度网络信息检索。

## 截图
![example1](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/weather_example.gif)
![example2](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/compare_example.gif)

## 技术架构

DeepSearch 采用模块化架构，以实现高效的网络搜索和 LLM 驱动的处理：

- **前端**：使用 React 和 Vite 开发响应式用户界面，处理搜索输入、会话管理和结果显示。
- **后端 (LLM Agent)**：基于 FastAPI 的 API 端点，集成 LLM 模型（如 Gemini）用于查询处理、总结和安全检查。
- **搜索引擎**：自定义引擎，使用 Sentence Transformers 进行本地嵌入或 Google Gemini 进行在线嵌入，支持代理管理、速率限制和通过 HNSWlib 的语义搜索。
- **数据库**：通过 Peewee ORM 管理的 SQLite，用于存储会话和搜索历史。
- **其他组件**：代理池用于网络抓取、速率限制器用于 API 调用，以及使用 asyncio 的异步处理。

此设置确保了可扩展性，通过环境变量提供本地或云端嵌入选项。

## 安装
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
5. 导出环境变量
    ```bash
    export GOOGLE_API_KEY=Your Google API Key
    export HUGGING_FACE_HUB_TOKEN=Your Hugging Face Hub Token
    export USE_ONLINE_EMBEDDING=False # 如果想使用 gemini 在线嵌入设置为 True，否则使用从 huggingface 下载的本地嵌入预训练模型
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