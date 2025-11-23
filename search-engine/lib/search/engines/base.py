import inspect
import logging
from dataclasses import dataclass
from typing import Optional, Iterator, Callable
from urllib.parse import urlencode

from lxml.html import HtmlElement, fromstring

from lib.search.request import Response, RequestClient

from lib.search.utils import clean_text


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
    selector: Optional[str] = None
    attribute: Optional[str] = None
    text: Optional[bool] = None
    tail: Optional[bool] = None
    text_content: Optional[bool] = None
    description: Optional[str] = None
    postprocess: Optional[Callable[[str], str]] = None


class Schema(object):
    """
    - container: css selector to select the container of the search result
    - preprocess: function to preprocess the element before extraction
    """
    container: str = "html"
    url: Optional[Selector] = None
    abstract: Optional[Selector] = None
    preprocess: Optional[Callable[[HtmlElement], HtmlElement]] = None

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
    def __init__(self, html: str, markdown: str, schema: Schema.__class__ = Schema):
        self.html = html
        self.markdown = markdown
        self.schema = schema
        self.selectors = {
            name: value for name, value in inspect.getmembers(self.schema)
            if isinstance(value, Selector)
        }
        self.tree = fromstring(html)

    def title(self) -> str:
        titles = self.tree.cssselect("title")
        return titles[0].text_content() if titles else ""

    def parse(self) -> list[Schema]:
        if not self.selectors:
            return [self.schema(content=self.markdown)]
        results = []
        elements = self.tree.cssselect(self.schema.container)
        for element in elements:
            if self.schema.preprocess:
                element = self.schema.preprocess(element)
                if not element:
                    continue
            model = self.schema()
            for key, selector in self.selectors.items():
                if not isinstance(selector, Selector):
                    continue
                outer = (
                    element.cssselect(selector.selector)
                    if selector.selector
                    else [element]
                )
                if not outer:
                    setattr(model, key, None)
                    continue
                value = None
                if selector.text_content:
                    value = clean_text(outer[0].text_content())
                elif selector.text:
                    value = clean_text(outer[0].text)
                elif selector.tail:
                    value = clean_text(outer[0].tail)
                elif selector.attribute:
                    value = outer[0].get(selector.attribute)
                if callable(selector.postprocess) and value is not None:
                    value = selector.postprocess(value)
                setattr(model, key, value)
            results.append(model)
        return results


from lib.search.exception import ProxyForbiddenException


class Engine(object):
    NAME = "base"
    BASE_URL = None
    DESCRIPTION = None

    @classmethod
    def _query(cls, target: str) -> dict:
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

    def __init__(self, client: RequestClient, parser: Parser.__class__ = Parser):
        self.client = client
        self.parser = parser
        self.logger = logging.getLogger('BaseSearchEngine')

    async def search(self, target: str, num: int = -1, latest: bool = False, **kwargs) -> Result:
        params = kwargs.get('params', {})
        if latest:
            params.update(self.__class__._latest() or {})
        params.update(self.__class__._query(target))
        kwargs['params'] = params

        url = self.__class__.BASE_URL if self.__class__.BASE_URL else target

        # Request
        async def _search():
            _resp = await self.client.get(url, **kwargs)
            _resp.raise_for_status()
            self.logger.info(f"Successfully get response from {url}?{urlencode(kwargs.get('params', {}))}")
            parser = self.parser(html=_resp.html, markdown=_resp.markdown)
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
