import inspect
import logging
import os
from dataclasses import dataclass
from typing import Optional, Iterator, Callable
from urllib.parse import urlencode

from lib.search.limiter import StandardRateLimitStrategy
from lib.search.request import Response, RequestClient
from dotenv import load_dotenv
from lxml import html
from trafilatura import extract

from lib.search.proxy import ProxyForbiddenException
from lib.search.utils import clean_text

load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))


@dataclass
class Selector(object):
    """
    - selector: css selector to select the element
    - attribute: attribute of the element to extract
    - text: whether to extract text inside the element
    - tail: whether to extract text after the element
    - text_content: whether to extract all text (including child elements) in the element
    - postprocess: function to postprocess the value after extraction
    """
    selector: str
    attribute: Optional[str] = None
    text: Optional[bool] = None
    tail: Optional[bool] = None
    text_content: Optional[bool] = None
    description: Optional[str] = None
    postprocess: Optional[Callable[[str], str]] = None


class Schema(object):
    """
    Content Schema And Model
    - content: optional, markdown content of the page
    - container: css selector to select the container of the search result
    """
    container: str = "html"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self.__dict__.items()])})"

    def __repr__(self):
        return self.__str__()


@dataclass
class Result(object):
    title: str
    content: list[Schema]


class Parser(object):
    def __init__(self, doc: str, schema: Schema.__class__ = Schema):
        self.doc = doc
        self.tree = html.fromstring(doc)
        self.schema = schema

    def title(self) -> str:
        titles = self.tree.cssselect("title")
        return titles[0].text_content() if titles else ""

    def parse(self) -> list[Schema]:
        selectors = {
            name: value for name, value in inspect.getmembers(self.schema)
            if isinstance(value, Selector)
        }
        if not selectors:
            content = extract(self.doc, output_format="markdown", deduplicate=True, with_metadata=True,
                              include_images=True, include_links=True)
            return [self.schema(content=content)]
        res = []
        elements = self.tree.cssselect(self.schema.container)
        for element in elements:
            model = None
            for k, v in selectors.items():
                if not isinstance(v, Selector):
                    continue
                outer = element.cssselect(v.selector)
                if not outer:
                    continue
                if model is None:
                    model = self.schema()
                value = None
                if v.text_content:
                    value = clean_text(outer[0].text_content())
                elif v.text:
                    value = clean_text(outer[0].text)
                elif v.tail:
                    value = clean_text(outer[0].tail)
                elif v.attribute:
                    value = outer[0].get(v.attribute)
                if callable(v.postprocess) and value is not None:
                    value = v.postprocess(value)

                setattr(model, k, value)
            if model is not None:
                res.append(model)
        return res


class Engine(object):
    NAME = "base"
    BASE_URL = None
    DESCRIPTION = None
    LIMIT_STRATEGY = StandardRateLimitStrategy

    @classmethod
    def _query(cls, target: str) -> dict:
        return {}

    @classmethod
    def _cookies(cls) -> dict:
        return {}

    @classmethod
    def _headers(cls) -> dict:
        return {}

    @classmethod
    def _latest(cls) -> dict | None:
        """
        Return the parameter of the time filter specified by the time range.
        """
        return None

    @classmethod
    def _pager(cls) -> Iterator[dict | None]:
        """
        Return the iterator to get the paging parameter.
        """
        yield

    @classmethod
    def _detect_sorry(cls, result: Response) -> bool:
        return False

    def __init__(self, parser: Parser.__class__ = Parser, client: RequestClient.__class__ = RequestClient):
        self.client = client()
        self.parser = parser
        self.logger = logging.getLogger('BaseSearchEngine')

    async def search(self, target: str, num: int = -1, latest: bool = False, site: str = None, **kwargs) -> Result:
        kwargs['headers'] = {**self.__class__._headers(), **kwargs.get('headers', {})}
        kwargs['cookies'] = {**self.__class__._cookies(), **kwargs.get('cookies', {})}
        # Apply time filter if specified
        params = kwargs.get('params', {})
        if latest:
            params.update(self.__class__._latest() or {})
        params.update(self.__class__._query(f"{target} site:{site}")) if site else params.update(
            self.__class__._query(target))
        kwargs['params'] = params

        url = self.__class__.BASE_URL if self.__class__.BASE_URL else target

        # Request
        async def _search():
            _resp = await self.client.get(url, **kwargs)
            _resp.raise_for_status()
            self.logger.info(f"Successfully get response from {url}?{urlencode(kwargs.get('params', {}))}")
            parser = self.parser(_resp.text)
            res = Result(title=parser.title(), content=parser.parse())
            if self.__class__._detect_sorry(_resp):
                self.logger.error(f"Sorry, some verification is required for {_resp.url}")
                raise ProxyForbiddenException(f"Sorry, some verification is required for {_resp.url}")
            return res

        # Return first page results when num <= 0
        if num <= 0:
            return await _search()

        resp = await _search()
        content = resp.content
        count = len(content)
        pager = self.__class__._pager()
        next(pager, None)
        while count < num and (page := next(pager, None)):
            params.update(page)
            kwargs['params'] = params
            resp = await _search()
            if not resp.content:
                break
            count += len(resp.content)
            content.extend(resp.content)

        return Result(title=resp.title, content=content[:num])

    async def aclose(self):
        if hasattr(self.client, 'aclose'):
            await self.client.aclose()
