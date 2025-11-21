# DeepSearch
[English](https://github.com/HydeYYHH/DeepSearch/blob/master/README.md)     [中文](https://github.com/HydeYYHH/DeepSearch/blob/master/README_zh.md)

DeepSearch is an LLM-powered web search engine focused on deep web information retrieval.

## Screenshot
![example1](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/weather_example.gif)
![example2](https://github.com/HydeYYHH/DeepSearch/blob/master/assets/compare_example.gif)


## Installation
### Manual Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/HydeYYHH/DeepSearch
    cd DeepSearch
    ```
2. Setup Search engine
    ```bash
    cd search-engine
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3. Setup LLM agent
    ```bash
    cd llm-agent
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
4. Setup Frontend
    ```bash
    cd frontend
    npm install
    ```
5. Export environment variables
    ```bash
    export GOOGLE_API_KEY=Your Google API Key
    export HUGGING_FACE_HUB_TOKEN=Your Hugging Face Hub Token
    export USE_ONLINE_EMBEDDING=False # Set to True if you want to use gemini online embedding else use local embedding pretrained model downloading from huggingface
    ```
6. Run the application
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
### Docker Deployment
```bash
docker compose up
```