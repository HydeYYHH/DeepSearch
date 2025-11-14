from lib.search.engines import DuckDuckGoEngine, BingEngine, So360Engine, SougouEngine
from lib.search.engines.base import Result
from lib.search.presets.base import Preset, Preference
from lib.search.searcher import EngineConfig


class DefaultPreset(Preset):
    DESCRIPTION = "Suitable for most of the cases."

    async def search(self, query: str, preference: Preference) -> Result:
        num = 20
        latest = False
        if preference == Preference.MORE_RESULTS:
            num = 30
        if preference == Preference.LATEST:
            latest = True
        return await self.searcher.aggregate_search(query=query,
                                                    engines=[EngineConfig(DuckDuckGoEngine(), 1),
                                                             EngineConfig(BingEngine(), 1),
                                                             EngineConfig(So360Engine(), 1),
                                                             EngineConfig(SougouEngine(), 1)],
                                                    num=num,
                                                    latest=latest)
