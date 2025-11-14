import logging
from typing import Iterator

from lib.search.engines.base import Schema, Selector, Parser, Engine

# Rate limited by Brave Search

class BraveSchema(Schema):
    container: str = "div.snippet"
    url: str = Selector(selector="a", attribute="href")
    title: str = Selector(selector="div.title", text_content=True)
    abstract: str = Selector(selector="div.snippet-description", text_content=True)
    source: str = Selector(selector="div.sitename", text_content=True)


class BraveParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=BraveSchema)


class BraveEngine(Engine):
    NAME = "brave"
    BASE_URL = "https://search.brave.com/search"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"q": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        """
        Return the iterator to get the paging parameter.
        """
        offset = 0
        while True:
            yield {"offset": offset}
            offset += 1

    @classmethod
    def _latest(cls) -> dict | None:
        return {"tf": "pd"}

    def __init__(self):
        super().__init__(parser=BraveParser)
        self.logger = logging.getLogger(__name__)
