from dotenv import load_dotenv
from zero import ZeroServer
from msgspec import Struct
import os
import sys
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from lib import Searcher
from lib.search.engines import *
from lib.search.presets.base import Preference
from lib.search.presets.default import DefaultPreset

app = ZeroServer(port=5559)


class SearchConfig(Struct):
    target: str
    preset: str = "default"
    preference: str = "balance"
    kwargs: dict = {}


class Result(Struct):
    title: str
    content: list[dict[str, str]]


@app.register_rpc
async def echo(msg: str) -> str:
    return msg


available_presets = {
    "default": DefaultPreset,
}

searcher = Searcher()


@app.register_rpc
async def fetch(url: str) -> Result:
    res = await searcher.search(target=url, engine=Engine())
    return Result(title=res.title, content=[item.__dict__ for item in res.content])


@app.register_rpc
async def search(config: SearchConfig) -> Result:
    res = await (available_presets[config.preset.lower()](searcher)
                 .search(config.target, Preference(config.preference.lower())))
    return Result(title=res.title, content=[item.__dict__ for item in res.content])

@app.register_rpc
async def list_available_engines() -> dict[str, str]:
    return {preset: available_presets[preset].DESCRIPTION for preset in available_presets.keys()}


if __name__ == '__main__':
    load_dotenv()
    app.run(workers=4)
