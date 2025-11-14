import logging
from typing import Iterator

from lib.search.engines.base import Schema, Parser, Engine, Selector


class SougouSchema(Schema):
    container = ".vrwrap"
    url = Selector(selector="a", attribute="href")
    title = Selector(selector="a", text_content=True)
    abstract = Selector(selector=".text-layout.space-txt", text_content=True)
    source = Selector(selector=".text-layout.citeurl", text_content=True)


class SougouParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=SougouSchema)


class SougouEngine(Engine):
    NAME = "sougou"
    BASE_URL = "https://www.sogou.com/web"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"query": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        page = 0
        while True:
            page += 1
            yield {"page": page}

    @classmethod
    def _latest(cls) -> dict | None:
        return {"s_from": "inttime_day"}

    def __init__(self):
        super().__init__(parser=SougouParser)
        self.logger = logging.getLogger(__name__)
