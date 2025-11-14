import logging
from typing import Iterator

from lib.search.engines.base import Schema, Selector, Parser, Engine


import base64

def extrac_url(url: str) -> str:
    encoded_url = url.split('&u=a1')[1].split('&ntb=1')[0]
    encoded_url = encoded_url.replace('-', '+').replace('_', '/')
    padding = '=' * ((4 - len(encoded_url) % 4) % 4)
    encoded_url += padding
    return base64.b64decode(encoded_url).decode('utf-8')


class BingSchema(Schema):
    container = "li.b_algo"
    url = Selector(selector="h2 a", attribute="href", postprocess=extrac_url)
    title = Selector(selector="h2 a", text_content=True)
    abstract = Selector(selector="p.b_lineclamp2", text_content=True)
    source = Selector(selector="div.tptt", text_content=True)


class BingParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=BingSchema)


class BingEngine(Engine):
    NAME = "bing"
    BASE_URL = "https://www.bing.com/search"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"q": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        first = 1
        while True:
            yield {"first": first}
            first += 10

    @classmethod
    def _latest(cls) -> dict | None:
        return {"filters": 'ex1%3a"ez1"'}

    def __init__(self):
        super().__init__(parser=BingParser)
        self.logger = logging.getLogger(__name__)
