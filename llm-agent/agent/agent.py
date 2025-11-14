import asyncio
import operator
from datetime import datetime
from typing import Annotated, Literal, Any

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from rpc_client import RpcClient, zero_client, Result
from tools import tools_by_name, tools_signatures

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
    # Safety check result
    unsafe_reason: str | None = None


class Summary(BaseModel):
    content: str = Field(description="Summary content")


class Safety(BaseModel):
    safe_or_not: Literal["safe", "unsafe"] = Field(description="Whether the query is safe")
    reason: str = Field(description="Briefly explain the reason")


load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_retries=3,
)
llm_with_tools = llm.bind_tools(
    [StructuredTool(name=tool.__name__, description=tool.__doc__, args_schema=tool) for tool in tools_signatures]
)
summarizer = llm.with_structured_output(Summary)
checker = llm.with_structured_output(Safety)


async def list_available_engines(state: AgentState) -> dict:
    return {"available_engines": await rpc_client.list_available_engines()}


async def search_call(state: AgentState) -> dict:
    msg = await llm_with_tools.ainvoke([
        SystemMessage(content=f"""
You are an AI search expert simulating human researcher behavior. Your sole task is tool selection (search/fetch/none) through iterative exploration until conclusive evidence is found. Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
### Core Directives
1. **Intent-Driven Reliability**
   - Factual/health/financial/legal queries: Require ≥2 authoritative sources (.gov/.edu/official sites)
   - Subjective/opinion/entertainment queries: Accept single credible source
2. **Termination Protocol**
   - Evidence explicitly answers all core query units
   - Source reliability matches query intent per Directive 1
   - All conflicting data is resolved or discarded
3. **Exploration Rules**
   - Verify quantitative claims with primary sources
   - Fetch content when snippets hide critical context
   - Treat timestamps as evidence decay indicators (e.g., 2024 data invalid for "current 2025")
### Examples
**Example 1: Factual Query**
User: "Current minimum wage in California"
Analysis:
Intent: Legal/factual → requires .gov source
Atomic facts: [location=CA, metric=min wage, timeframe=current]
Action: `search: "California minimum wage 2025 official site:.gov"`
Results: "dir.ca.gov: $16.50/hour effective Jan 2025"
Triage:
- All facts covered: Yes
- Authoritative source: Yes (.gov)
- No hidden qualifiers: Yes
Action: `none`
**Example 2: Entertainment Query**
User: "Most liked Taylor Swift music video on YouTube"
Analysis:
Intent: Entertainment → established media acceptable
Atomic facts: [artist, metric=likes, platform=YouTube]
Action: `search: "Taylor Swift most liked YouTube video Billboard"`
Results: "Billboard: 'Blank Space' has 3.2B views (Oct 2025)"
Triage:
- All facts covered: No ("views" ≠ "likes")
Action: `fetch: "https://www.billboard.com/music/pop/taylor-swift-youtube-records-1235789234/"`
Fetched content: "Most-liked: 'ME!' with 28M likes (source: YouTube API)"
Triage:
- All facts covered: Yes
- Reliable source: Yes (established media for entertainment context)
- No conflicts: Yes
Action: `none`
**Example 3: Conflict Resolution**
User: "Did iPhone 16 launch in September 2025?"
Action: `search: "iPhone 16 release date September 2025"`
Results:
- "Apple.com: Available September 20, 2025"
- "TechCrunch: Delayed to October"
Triage:
- Atomic facts present: Yes
- Contradiction exists: Yes → requires primary source fetch
Action: `fetch: "https://www.apple.com/newsroom/2025/09/apple-unveils-iphone-16/"`
Verification: Official press release confirms September 20 launch
Action: `none`
Tips:
- Use search operators like `site`:, quotes `...`, `-exclude`, `OR` to refine your queries and retrieve more relevant results.
        """),
        HumanMessage(content=f"""User input: {state.user_input}
        Available engines: {state.available_engines}
        Search results before: {"\n".join(
            [f"- {res['title']}: {res['content']}" for res in state.search_results]
        )}""")
    ])
    return {"messages": [msg]}


async def tool_node(state: AgentState) -> dict:
    result = []
    for tool_call in state.messages[-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation: Result = await tool(**tool_call["args"])
        result.append(observation)
    return {"search_results": result}


def should_continue(state: AgentState) -> Literal["tool_node", "summarize"]:
    if state.messages[-1].tool_calls:
        return "tool_node"
    return "summarize"


async def summarize(state: AgentState) -> dict[str, Any]:
    prompt = [
        SystemMessage(content="""
        You are a content summarization assistant. Your task is to synthesize all provided information into a clear, comprehensive, and well-structured final answer.
        **Crucially, you MUST cite your sources.** For every piece of information taken from a search result, you must append a citation marker in the format `[cite: URL]` at the end of the sentence.
        Example of expected output format:
        The sky appears blue because of a phenomenon known as Rayleigh scattering [cite: https://mocksite.com/science].
        """),
        HumanMessage(
            content=f"""User input: {state.user_input}\nSearch results:{"\n".join(
                [f"- {res['title']}: {res['content']}" for res in state.search_results]
            )}""")
    ]
    summary_result = await summarizer.ainvoke(prompt)
    return {"answer": summary_result.content, "messages": [AIMessage(content=summary_result.content)]}


async def safety_check(state: AgentState) -> dict:
    safety = await checker.ainvoke([
        SystemMessage(content="""Determine whether the following text contains any of the following prohibited categories:
        1. Sexual or pornographic content
        2. Violence, abuse, or self-harm
        3. Hate speech or discrimination
        4. Political extremism or ideology incitement
        5. Illegal or criminal behavior (drugs, terrorism, scams, gambling, etc.)
        6. Privacy violations (e.g., ID number, phone number, address)
        7. Any other content that may violate laws or social ethics"""),
        HumanMessage(content=f"{state.answer}")
    ])
    updates = {"messages": [AIMessage(content=safety.model_dump_json())]}
    if safety.safe_or_not == "unsafe":
        updates["unsafe_reason"] = safety.reason
    return updates


builder = StateGraph(AgentState)

builder.add_node("list_available_engines", list_available_engines)
builder.add_node("search_call", search_call)
builder.add_node("tool_node", tool_node)
builder.add_node("summarize", summarize)
builder.add_node("safety_check", safety_check)

builder.add_edge(START, "list_available_engines")
builder.add_edge("list_available_engines", "search_call")
builder.add_conditional_edges("search_call", should_continue, {
    "tool_node": "tool_node",
    "summarize": "summarize",
})
builder.add_edge("tool_node", "search_call")
builder.add_edge("summarize", "safety_check")
builder.add_edge("safety_check", END)

agent = builder.compile()


async def main():
    state = await agent.ainvoke(AgentState(user_input="今年发生的最大的地震"))
    messages = state['messages'] if isinstance(state, dict) else state.messages
    for m in messages:
        m.pretty_print()
    print(state)
    print(state['answer'])


if __name__ == "__main__":
    asyncio.run(main())
