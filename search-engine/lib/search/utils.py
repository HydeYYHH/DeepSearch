import re
import asyncio


def clean_text(text: str) -> str:
    return re.sub(r'[\r\n]+', '', text).strip()

def close_async(obj) -> None:
    if hasattr(obj, 'aclose'):
        asyncio.run(obj.aclose())
