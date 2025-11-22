import inspect
import logging
from dataclasses import dataclass
from typing import Optional, Iterator, Callable
from urllib.parse import urlencode

from lxml.html import HtmlElement

from lib.search.request import Response, RequestClient
from lxml.html import fromstring

from lib.search.proxy import ProxyForbiddenException
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
    preprocess: Optional[Callable[[HtmlElement], HtmlElement]] = None
    url: Optional[Selector] = None
    content: Optional[Selector] = None

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


class Engine(object):
    NAME = "base"
    BASE_URL = None
    DESCRIPTION = None

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

    def __init__(self, parser: Parser.__class__ = Parser):
        self.parser = parser
        self.logger = logging.getLogger('BaseSearchEngine')

    async def search(self, target: list[str], num: int = -1, latest: bool = False, **kwargs) -> list[Result]:
            kwargs['headers'] = {**self.__class__._headers(), **kwargs.get('headers', {})}
            kwargs['cookies'] = {**self.__class__._cookies(), **kwargs.get('cookies', {})}
            targets = list(target or [])

            urls: list[str] = []
            if self.__class__.BASE_URL:
                for t in targets:
                    _params = (kwargs.get('params') or {}).copy()
                    if latest:
                        _params.update(self.__class__._latest() or {})
                    _params.update(self.__class__._query(t))
                    urls.append(f"{self.__class__.BASE_URL}?{urlencode(_params)}")
                kwargs.pop('params', None)
            else:
                urls = targets

            _responses = await RequestClient.get(urls, **kwargs)
            results: list[Result] = []
            for _resp in _responses or []:
                self.logger.info(f"Get response from {_resp.url}")
                parser = self.parser(_resp.html, _resp.markdown)
                res = Result(title=parser.title(), content=parser.parse())
                if self.__class__._detect_sorry(_resp):
                    self.logger.error(f"Sorry, some verification is required for {_resp.url}")
                    raise ProxyForbiddenException(f"Sorry, some verification is required for {_resp.url}")
                if num > 0 and not self.__class__.BASE_URL:
                    res = Result(title=res.title, content=res.content[:num])
                results.append(res)

            if num > 0 and self.__class__.BASE_URL and len(targets) > 0:
                for idx, t in enumerate(targets):
                    base_params = (kwargs.get('params') or {}).copy()
                    if latest:
                        base_params.update(self.__class__._latest() or {})
                    base_params.update(self.__class__._query(t))
                    pager = self.__class__._pager()
                    next(pager, None)
                    content = results[idx].content
                    count = len(content)
                    while count < num and (page := next(pager, None)):
                        _params = {**base_params, **page}
                        page_url = f"{self.__class__.BASE_URL}?{urlencode(_params)}"
                        more = await RequestClient.get([page_url], **kwargs)
                        if not more:
                            break
                        more_resp = more[0]
                        more_resp.raise_for_status()
                        parser = self.parser(more_resp.html, more_resp.markdown)
                        parsed = parser.parse()
                        if not parsed:
                            break
                        count += len(parsed)
                        content.extend(parsed)
                    results[idx] = Result(title=results[idx].title, content=results[idx].content[:num])

            return results
