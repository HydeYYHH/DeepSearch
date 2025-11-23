import logging
from typing import Iterator

from lib.search.engines.base import Schema, Selector, Parser, Engine
from lib.search.request import RequestClient


class BraveSchema(Schema):
    container = "div.snippet"
    url = Selector(selector="a", attribute="href")
    title = Selector(selector="div.title", text_content=True)
    abstract = Selector(selector="div.snippet-description", text_content=True)
    source = Selector(selector="div.sitename", text_content=True)


class BraveParser(Parser):
    def __init__(self, html: str, markdown: str):
        super().__init__(html, markdown, schema=BraveSchema)


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

    def __init__(self, client: RequestClient):
        super().__init__(parser=BraveParser, client=client)
        self.logger = logging.getLogger(__name__)
