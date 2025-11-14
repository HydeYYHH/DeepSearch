import logging
from typing import Iterator

from lib.search.engines.base import Schema, Selector, Parser, Engine


class So360Schema(Schema):
    container: str = "li.res-list"
    url: str = Selector(selector=".res-title a", attribute="data-mdurl")
    title: str = Selector(selector=".res-title a", text_content=True)
    abstract: str = Selector(selector="p.res-desc", text_content=True)
    source: str = Selector(selector="cite", text_content=True)


class So360Parser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=So360Schema)


class So360Engine(Engine):
    NAME = "so360"
    BASE_URL = "https://www.so.com/s"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"q": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        """
        Return the iterator to get the paging parameter.
        """
        pn = 0
        while True:
            yield {"pn": pn}
            pn += 1

    @classmethod
    def _latest(cls) -> dict | None:
        return {"adv_t": "d"}

    def __init__(self):
        super().__init__(So360Parser)
        self.logger = logging.getLogger('So360SearchEngine')
