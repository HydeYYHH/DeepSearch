import logging
from typing import Iterator, Optional

from lxml.html import HtmlElement

from lib.search.engines.base import Engine, Parser, Schema, Selector


def preprocess(doc: HtmlElement) -> Optional[HtmlElement]:
    return doc if doc.cssselect("a")[0].get("href").startswith("http") else None

class GoogleSchema(Schema):
    container = "div[data-rpos]"
    url = Selector(selector="a", attribute="href")
    title = Selector(selector="a", text_content=True)
    abstract = Selector(selector='[data-sncf="1"]', text_content=True)
    source = Selector(selector='div.notranslate', text_content=True)
    preprocess = preprocess

class GoogleParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=GoogleSchema)


class GoogleEngine(Engine):
    NAME = "google"
    BASE_URL = "https://www.google.com/search"
    DESCRIPTION = "Popular search engine with high-quality results and reliable sources."

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
            yield {"start": pn}
            pn += 10

    @classmethod
    def _latest(cls) -> dict | None:
        """
        Return the parameter of the time filter specified by the time range.
        """
        return {"tbs": "qdr:d"}

    def __init__(self):
        super().__init__(GoogleParser)
        self.logger = logging.getLogger('GoogleSearchEngine')
