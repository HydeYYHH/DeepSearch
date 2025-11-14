import logging
from typing import Iterator

from lib.search.engines.base import Schema, Selector, Parser, Engine
from lib.search.request import Response


# Due to Yandex's anti-scraping policies,
# avoid making consecutive requests or fetching multiple pages in quick succession.


class YandexSchema(Schema):
    container = "li.serp-item"
    url = Selector(selector="a", attribute="href")
    title = Selector(selector=".OrganicTitle-LinkText", text_content=True)
    abstract = Selector(selector="div.TextContainer", text_content=True)
    source = Selector(selector="div.OrganicHost-Title", text_content=True)


class YandexParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=YandexSchema)


class YandexEngine(Engine):
    NAME = "yandex"
    BASE_URL = "https://yandex.com/search"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"text": target}

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        p = 0
        while True:
            p += 1
            yield {"p": p}

    @classmethod
    def _latest(cls) -> dict | None:
        return {"within": "77"}

    @classmethod
    def _detect_sorry(cls, result: Response) -> bool:
        return "Are you not a robot?" in result.text

    def __init__(self):
        super().__init__(parser=YandexParser)
        self.logger = logging.getLogger(__name__)
