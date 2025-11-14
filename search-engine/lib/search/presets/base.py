from abc import ABC, abstractmethod
from enum import Enum

from lib import Searcher


class Preference(Enum):
    BALANCE = "balance"
    LATEST = "latest"
    MORE_RESULTS = "more_results"


class Preset(ABC):

    DESCRIPTION = None

    def __init__(self, searcher: Searcher):
        self.searcher = searcher

    @abstractmethod
    async def search(self, query: str, preference: Preference):
        pass
