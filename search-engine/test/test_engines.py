import pytest

from lib.search.engines import Engine, SougouEngine, BraveEngine, YandexEngine
from lib.search.engines.baidu import BaiduEngine
from lib.search.engines.google import GoogleEngine
from lib.search.engines.so360 import So360Engine
from lib.search.request import RequestClient


@pytest.mark.asyncio
async def test_fetch():
    client = RequestClient()
    engine = Engine(client=client)
    print(await engine.search("https://www.zhihu.com/question/22713470"))
    await client.aclose()


@pytest.mark.asyncio
async def test_so360():
    client = RequestClient()
    engine = So360Engine(client=client)
    print(await engine.search("hello"))
    await client.aclose()


@pytest.mark.asyncio
async def test_sougou():
    client = RequestClient()
    engine = SougouEngine(client=client)
    print(await engine.search("hello"))
    await client.aclose()


@pytest.mark.asyncio
async def test_baidu():
    client = RequestClient()
    engine = BaiduEngine(client=client)
    print(await engine.search("hello", num=10))
    await client.aclose()


@pytest.mark.asyncio
async def test_brave():
    client = RequestClient()
    engine = BraveEngine(client=client)
    print(await engine.search("hello"))
    await client.aclose()


@pytest.mark.asyncio
async def test_yandex():
    client = RequestClient()
    engine = YandexEngine(client=client)
    print(await engine.search("hello"))
    await client.aclose()


@pytest.mark.asyncio
async def test_google():
    client = RequestClient()
    engine = GoogleEngine(client=client)
    print(await engine.search("hello"))
    await client.aclose()
