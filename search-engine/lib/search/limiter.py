import logging
from typing import Sequence

from limits import storage, strategies, RateLimitItemPerSecond


class RateLimitStrategy:
    sliding_window: Sequence[tuple[int, int]]


class StrictRateLimitStrategy(RateLimitStrategy):
    sliding_window = [(1, 2), (15, 20), (150, 600)]


class StandardRateLimitStrategy(RateLimitStrategy):
    sliding_window = [(15, 20), (150, 600)]


class RateExceededException(Exception):
    pass


class RateLimiter:
    sliding_window = strategies.SlidingWindowCounterRateLimiter(storage.MemoryStorage())
    logger = logging.getLogger(__name__)

    def allow(self, key: str, strategy: RateLimitStrategy.__class__ = StandardRateLimitStrategy):
        if not all(self.sliding_window.hit(RateLimitItemPerSecond(item[0], item[1]), key) for item in
                   strategy.sliding_window):
            self.logger.warning(f"Rate limit exceeded for key {key}")
            raise RateExceededException(f"Rate limit exceeded for key {key}")
