from typing import Literal

from pydantic import BaseModel, Field

from agent.rpc_client import RpcClient, zero_client, SearchConfig, Result


class list_available_engines(BaseModel):
    """List all available search engines."""


class fetch_content(BaseModel):
    """Fetch detailed content from a web page with the given URL."""
    url: str = Field(..., description="URL to fetch content from")


class search(BaseModel):
    """
    Search the web with the given query using specific search engines and preferences.
    Search operators like `site:`, `"..."`, `-`, `OR` supported but not guaranteed to work.
    """
    query: str = Field(..., description="Search query text")
    engine: str = Field(default="default", description="Search engine name to use, default is 'default' engine")
    preference: Literal["balance", "latest", "more_results"] = Field(
        default="balance",
        description="Search preference: 'balance' (balanced, default choice), 'latest' (most recent), 'more_results' (more total results)", )


tools_signatures = [
    fetch_content,
    search,
]

rpc_client = RpcClient(zero_client)


async def _fetch_content(url: str) -> Result:
    return await rpc_client.fetch(url)


async def _search(query: str, engine: str = "default", preference: str = "balance") -> Result:
    return await rpc_client.search(SearchConfig(target=query, preset=engine, preference=preference))


tools_by_name = {
    "fetch_content": _fetch_content,
    "search": _search,
}
