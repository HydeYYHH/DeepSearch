from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.staticfiles import StaticFiles
import asyncio
import uuid
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.agent import run
from model import db
from model.history import History
from model.session import Session

app = FastAPI(
    title="DeepSearch",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def root():
    return JSONResponse({"status": "ok"})

tasks: dict[str, dict] = {}
tasks_lock = asyncio.Lock()

@app.post("/api/tasks")
async def create_task(request: Request):
    data = await request.json()
    query = data["query"]
    session_id = int(data["session_id"])
    tid = uuid.uuid4().hex
    async with tasks_lock:
        tasks[tid] = {"status": "queued", "result": None, "error": None, "task": None}
    async def worker():
        async with tasks_lock:
            tasks[tid]["status"] = "running"
        try:
            res = await run(query, session_id)
            async with tasks_lock:
                tasks[tid]["result"] = res
                tasks[tid]["status"] = "done"
        except asyncio.CancelledError:
            async with tasks_lock:
                tasks[tid]["status"] = "canceled"
        except Exception as e:
            async with tasks_lock:
                tasks[tid]["error"] = str(e)
                tasks[tid]["status"] = "error"
    t = asyncio.create_task(worker())
    async with tasks_lock:
        tasks[tid]["task"] = t
    return {"task_id": tid, "status": tasks[tid]["status"]}

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    async with tasks_lock:
        info = tasks.get(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")
    data = {"task_id": task_id, "status": info.get("status")}
    if info.get("result"):
        data.update({
            "history_id": info["result"].get("history_id"),
            "answer": info["result"].get("answer")
        })
    if info.get("error"):
        data["error"] = info.get("error")
    return data

@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    async with tasks_lock:
        info = tasks.get(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")
    t = info.get("task")
    if t and not t.done():
        t.cancel()
        async with tasks_lock:
            tasks[task_id]["status"] = "canceled"
        return {"task_id": task_id, "status": "canceled"}
    return {"task_id": task_id, "status": info.get("status")}

@app.post("/api/search")
async def search(request: Request, query: str | None = Form(None), session_id: int | None = Form(None)):
    if query is None or session_id is None:
        data = await request.json()
        query = data.get("query")
        session_id = data.get("session_id")
    res = await run(query, int(session_id))
    return {
        "query": query,
        "history_id": res["history_id"],
        "answer": res["answer"],
    }


@app.post("/api/sessions")
async def create_session():
    obj = Session.create()
    return {
        "id": obj.id,
        "created_at": obj.created_at,
        "abstract": obj.abstract
    }

@app.get("/api/sessions")
async def get_all_sessions():
    sessions = Session.get_sessions()
    return [
        {
            "id": session.id,
            "created_at": session.created_at,
            "abstract": session.abstract
        }
        for session in sessions
    ]


@app.get("/api/sessions/{session_id}/histories")
async def get_session_histories(session_id: int):
    histories = History.get_histories(session_id)
    return [
        {
            "id": history.id,
            "timestamp": history.timestamp,
            "user_input": history.user_input,
            "answer": history.answer,
            "session_id": history.session_id
        }
        for history in histories
    ]

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    success = Session.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}

@app.delete("/api/histories/{history_id}")
async def delete_history(history_id: int):
    success = History.delete_history(history_id)
    if not success:
        raise HTTPException(status_code=404, detail="History not found")
    return {"message": "History deleted successfully"}

@app.on_event("startup")
async def startup():
    with db:
        db.create_tables([Session, History])

def main():
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
