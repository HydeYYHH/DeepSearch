FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* ./
RUN [ -f pnpm-lock.yaml ] && npm i -g pnpm || true
RUN if [ -f pnpm-lock.yaml ]; then pnpm install; else npm install; fi
COPY frontend ./frontend
RUN cd frontend && npm run build

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake && rm -rf /var/lib/apt/lists/*
COPY search-engine/requirements.txt /app/search-engine/requirements.txt
COPY llm-agent/requirements.txt /app/llm-agent/requirements.txt
RUN pip install --no-cache-dir -r /app/search-engine/requirements.txt && pip install --no-cache-dir -r /app/llm-agent/requirements.txt
COPY search-engine /app/search-engine
COPY llm-agent /app/llm-agent
COPY --from=frontend-build /app/frontend/dist /app/llm-agent/static
ENV PORT=8000
EXPOSE 8000 5559
CMD ["sh","-c","python search-engine/server/server.py & python llm-agent/main.py"]