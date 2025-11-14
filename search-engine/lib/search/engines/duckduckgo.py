import logging
import re
from typing import Iterator
from urllib.parse import unquote

from lib.search.engines.base import Schema, Selector, Parser, Engine


def extract_url(url: str) -> str:
    if 'duckduckgo.com/l/?uddg=' in url:
        match = re.search(r'uddg=([^&]+)', url)
        if match:
            url = unquote(match.group(1))
    if not url.startswith(('http://', 'https://')):
        return 'https:' + url
    return url


class DuckDuckGoSchema(Schema):
    container = ".result"
    url = Selector(
        selector="a.result__a",
        attribute="href",
        postprocess=extract_url
    )
    title = Selector(selector="a.result__a", text_content=True)
    abstract = Selector(selector="a.result__snippet", text_content=True)


class DuckDuckGoParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=DuckDuckGoSchema)


class DuckDuckGoEngine(Engine):
    NAME = "duckduckgo"
    BASE_URL = "https://html.duckduckgo.com/html"

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
            yield {"s": pn}
            pn += 10

    def __init__(self):
        super().__init__(DuckDuckGoParser)
        self.logger = logging.getLogger(__name__)
