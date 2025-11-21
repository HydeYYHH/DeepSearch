import operator
from datetime import datetime
from typing import Annotated, Literal, Any, Optional
import os

from dotenv import load_dotenv
from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from agent.rpc_client import RpcClient, zero_client, Result
from agent.tools import tools_by_name, tools_signatures
from agent.prompts import SEARCH_PROMPT_TEMPLATE, SUMMARIZE_PROMPT, SAFETY_CHECK_PROMPT
from model.history import History
from model.session import Session

rpc_client = RpcClient(zero_client)


class AgentState(BaseModel):
    # User input
    user_input: str = ""
    # Search Engine Metadata
    available_engines: dict[str, str] | None = None
    # Search results
    search_results: Annotated[list, operator.add] = []
    # Generated content
    messages: Annotated[list, operator.add] = []
    answer: str | None = None
    # History for recent interactions
    history: Annotated[list[tuple[str, str]], operator.add] = []


class Summary(BaseModel):
    content: str = Field(description="Summary content")


class Safety(BaseModel):
    safe_or_not: Literal["safe", "unsafe"] = Field(description="Whether the query is safe")
    reason: Optional[str] = Field(description="Briefly explain the reason")


load_dotenv()
_google_api_key = os.environ.get("GOOGLE_API_KEY") or "dummy"
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_retries=3,
    google_api_key=_google_api_key,
)
llm_with_tools = llm.bind_tools(
    [StructuredTool(name=tool.__name__, description=tool.__doc__, args_schema=tool) for tool in tools_signatures]
)
summarizer = llm.with_structured_output(Summary)
checker = llm.with_structured_output(Safety)


async def trim_history(state: AgentState) -> dict:
    """Trim history to the last 3 interactions."""
    if len(state.history) > 3:
        state.history = state.history[-3:]
    return {"history": state.history}


async def list_available_engines(state: AgentState) -> dict:
    return {"available_engines": await rpc_client.list_available_engines()}


async def search_call(state: AgentState) -> dict:
    # Include history in the prompt if available
    history = ""
    if state.history:
        history = "\n### Previous Interactions:\n" + "\n".join(
            [f"User: {q}\nAI: {a}" for q, a in state.history]
        )

    msg = await llm_with_tools.ainvoke([
        SystemMessage(
            content=SEARCH_PROMPT_TEMPLATE + f"**Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + history),
        HumanMessage(content=f"""User input: {state.user_input}
        Available engines: {state.available_engines}"""),
        HumanMessage(
            content=(
                    "### Search results before"
                    + "\n".join(
                [
                    f"**{i + 1}. {res['title']}**\n"
                    f"> {res['content']}\n"
                    for i, res in enumerate(state.search_results)
                ]
            )
            )
        )
    ])
    return {"messages": [msg]}


async def tool_node(state: AgentState) -> dict:
    result = []
    for tool_call in state.messages[-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation: Result = await tool(**tool_call["args"])
        result.append(observation)
    return {"search_results": result}


async def should_continue(state: AgentState) -> Literal["tool_node", "summarize"]:
    if state.messages[-1].tool_calls:
        return "tool_node"
    return "summarize"


async def summarize(state: AgentState) -> dict[str, Any]:
    # Include history in the summarize prompt if available
    history_content = ""
    if state.history:
        history_content = "\n### Previous Interactions:\n" + "\n".join(
            [f"User: {q}\nAI: {a}" for q, a in state.history]
        )
    prompt = [
        SystemMessage(content=SUMMARIZE_PROMPT ),
        HumanMessage(content=f"""User input: {state.user_input}"""),
        HumanMessage(
            content=(
                    "### Search Results"
                    + "\n".join([
                f"**{i + 1}. {res['title']}**\n"
                f"> {res['content']}\n"
                for i, res in enumerate(state.search_results)
            ])
            )
        ),
        HumanMessage(content=history_content),
    ]
    summary_result = await summarizer.ainvoke(prompt)
    return {"answer": summary_result.content, "messages": [AIMessage(content=summary_result.content)]}


async def update_history(state: AgentState) -> dict:
    if state.answer:
        return {"history": [(state.user_input, state.answer)]}
    return {}


async def safety_check(state: AgentState) -> dict:
    safety = await checker.ainvoke([
        SystemMessage(content=SAFETY_CHECK_PROMPT),
        HumanMessage(content=f"{state.answer}")
    ])
    if safety.safe_or_not == "unsafe":
        return {"answer": safety.reason, "messages": [AIMessage(content=safety.reason)]}
    return {}


builder = StateGraph(AgentState)
builder.add_node("trim_history", trim_history)
builder.add_node("list_available_engines", list_available_engines)
builder.add_node("search_call", search_call)
builder.add_node("tool_node", tool_node)
builder.add_node("summarize", summarize)
builder.add_node("safety_check", safety_check)
builder.add_node("update_history", update_history)

builder.add_edge(START, "trim_history")
builder.add_edge("trim_history", "list_available_engines")
builder.add_edge("list_available_engines", "search_call")
builder.add_conditional_edges("search_call", should_continue, {
    "tool_node": "tool_node",
    "summarize": "summarize",
})
builder.add_edge("tool_node", "search_call")
_safety_enabled = str(os.environ.get("SAFETY_CHECK", os.environ.get("ENABLE_SAFETY_CHECK", "true"))).lower() == "true"
if _safety_enabled:
    builder.add_edge("summarize", "safety_check")
    builder.add_edge("safety_check", "update_history")
else:
    builder.add_edge("summarize", "update_history")
builder.add_edge("update_history", END)

agent = builder.compile()


async def run(user_input: str, session_id: int):
    history = History.create(session_id, user_input)
    # Update session abstract
    Session.update_abstract(session_id, user_input)
    # Read history from DB
    histories = History.get_histories(session_id)
    histories = [(h.user_input, h.answer or "") for h in histories if h.answer is not None]
    state = await agent.ainvoke(AgentState(user_input=user_input, history=histories))
    History.update_answer(history.id, state.get("answer"))
    return {
        "answer": state.get('answer'),
        "history_id": history.id,
    }
