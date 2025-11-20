import pytest

from lib.search.engines import Engine, SougouEngine, BraveEngine, YandexEngine
from lib.search.engines.baidu import BaiduEngine
from lib.search.engines.google import GoogleEngine
from lib.search.engines.so360 import So360Engine
from lib.search.utils import auto_aclose

@pytest.mark.asyncio
@auto_aclose
async def test_fetch():
    engine = Engine()
    print(await engine.search("https://www.zhihu.com/question/22713470"))


@pytest.mark.asyncio
@auto_aclose
async def test_fetch_pdf():
    engine = Engine()
    print(await engine.search("https://www.gov.cn/zhengce/zhengceku/202507/P020250711338864590628.pdf"))

@pytest.mark.asyncio
@auto_aclose
async def test_so360():
    engine = So360Engine()
    print(await engine.search("hello"))

@pytest.mark.asyncio
@auto_aclose
async def test_sougou():
    engine = SougouEngine()
    print(await engine.search("hello"))

@pytest.mark.asyncio
@auto_aclose
async def test_baidu():
    engine = BaiduEngine()
    print(await engine.search("hello", num=10))


@pytest.mark.asyncio
@auto_aclose
async def test_brave():
    engine = BraveEngine()
    print(await engine.search("hello"))


@pytest.mark.asyncio
@auto_aclose
async def test_yandex():
    engine = YandexEngine()
    print(await engine.search("hello"))


@pytest.mark.asyncio
@auto_aclose
async def test_google():
    engine = GoogleEngine()
    print(await engine.search("hello"))
