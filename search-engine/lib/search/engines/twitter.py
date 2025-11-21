import logging

from lib.search.engines.base import Schema, Selector, Parser, Engine


def splice_url(url: str) -> str:
    if url and not url.startswith(('http://', 'https://')):
        return 'https://nitter.net' + url
    return url


class TwitterSchema(Schema):
    container = ".timeline-item"
    url = Selector(
        selector="a.tweet-link",
        attribute="href",
        postprocess=splice_url
    )
    abstract = Selector(selector=".tweet-content", text_content=True)
    author = Selector(selector="div.fullname-and-username", text_content=True)
    time = Selector(selector="span.tweet-date a", attribute="title")


class TwitterParser(Parser):
    def __init__(self, doc: str):
        super().__init__(doc, schema=TwitterSchema)


class TwitterEngine(Engine):
    NAME = "twitter"
    BASE_URL = "https://nitter.net/search"

    @classmethod
    def _query(cls, target: str) -> dict:
        return {"q": target}

    def __init__(self):
        super().__init__(parser=TwitterParser)
        self.logger = logging.getLogger(__name__)
