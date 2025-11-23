from lib.search.engines import DuckDuckGoEngine, BingEngine, So360Engine, SougouEngine
from lib.search.engines.base import Result
from lib.search.presets.base import Preset, Preference
from lib.search.request import RequestClient
from lib.search.searcher import EngineConfig


class DefaultPreset(Preset):
    DESCRIPTION = "Suitable for most of the cases."

    async def search(self, query: str, preference: Preference, client: RequestClient) -> Result:
        num = 20
        latest = False
        if preference == Preference.MORE_RESULTS:
            num = 30
        if preference == Preference.LATEST:
            latest = True
        return await self.searcher.aggregate_search(query=query,
                                                    client=client,
                                                    engines=[EngineConfig(DuckDuckGoEngine(client=client), 1),
                                                             EngineConfig(BingEngine(client=client), 1),
                                                             EngineConfig(So360Engine(client=client), 1),
                                                             EngineConfig(SougouEngine(client=client), 1)],
                                                    num=num,
                                                    latest=latest)
