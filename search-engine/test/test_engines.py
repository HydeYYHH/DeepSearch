import pytest

from lib.search.engines.so360 import So360Engine
from lib.search.utils import auto_aclose


@pytest.mark.asyncio
@auto_aclose
async def test_so360():
    engine = So360Engine()
    print(await engine.search("hello"))