import logging
from time import time
from typing import Iterator

from lib.search.engines.base import Engine, Parser, Schema, Selector
from lib.search.request import Response, RequestClient


class BaiduSchema(Schema):
    container = "div.result"
    url = Selector(selector=None, attribute="mu")
    title = Selector(selector="a", text_content=True)
    abstract = Selector(selector='[data-module="abstract"]', text_content=True)
    source = Selector(selector="span.cosc-source-text", text_content=True)


class BaiduParser(Parser):
    def __init__(self, html: str, markdown: str):
        super().__init__(html, markdown, schema=BaiduSchema)


class BaiduEngine(Engine):
    NAME = "baidu"
    BASE_URL = "https://www.baidu.com/s"
    DESCRIPTION = "Chinese search engine with median-quality results and unreliable sources."

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"wd": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        """
        Return the iterator to get the paging parameter.
        """
        pn = 0
        while True:
            yield {"pn": pn}
            pn += 10

    @classmethod
    def _latest(cls) -> dict | None:
        """
        Return the parameter of the time filter specified by the time range.
        """
        now = int(time())
        start = now - 86400
        return {"gpc": f"stf={start},{now}|stftype=1"}

    @classmethod
    def _detect_sorry(cls, result: Response) -> bool:
        return result.url.startswith("https://wappass.baidu.com/static/captcha")

    def __init__(self, client: RequestClient):
        super().__init__(client=client, parser=BaiduParser)
        self.logger = logging.getLogger('BaiduSearchEngine')
