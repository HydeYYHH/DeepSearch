import re


def clean_text(text: str) -> str:
    return re.sub(r'[\r\n]+', '', text).strip()


import asyncio
from functools import wraps
from collections.abc import Iterable


def auto_aclose(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        _res = await func(*args, **kwargs)
        res_list = _res if isinstance(_res, Iterable) and not isinstance(_res, (str, bytes)) else [_res]

        async def _close_one(obj):
            if hasattr(obj, "aclose") and callable(obj.aclose):
                await obj.aclose()
            elif hasattr(obj, "close") and callable(obj.close):
                maybe_coro = obj.close()
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro

        await asyncio.gather(*[_close_one(r) for r in res_list])
        return _res

    return wrapper
