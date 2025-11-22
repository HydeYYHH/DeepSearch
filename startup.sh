#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "DeepSearch setup"

if [ -z "$GOOGLE_API_KEY" ]; then
  read -p "Enter GOOGLE_API_KEY: " GOOGLE_API_KEY
fi
if [ -z "$USE_ONLINE_EMBEDDING" ]; then
  USE_ONLINE_EMBEDDING="False"
fi
export GOOGLE_API_KEY
export USE_ONLINE_EMBEDDING

cd "$ROOT_DIR/search-engine"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate

cd "$ROOT_DIR/llm-agent"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate

cd "$ROOT_DIR/frontend"
npm install

cd "$ROOT_DIR/search-engine"
./.venv/bin/python server/server.py &

cd "$ROOT_DIR/llm-agent"
./.venv/bin/python main.py &

cd "$ROOT_DIR/frontend"
npm run dev
