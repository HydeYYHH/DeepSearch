import logging
import os
import random
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

ENABLE_PROXY = os.getenv("ENABLE_PROXY", "False").lower() == "true"


class ProxyForbiddenException(Exception):
    pass


class ProxyPool(object):
    def __init__(self):
        self.pools = []
        self.logger = logging.getLogger(__name__)
        if ENABLE_PROXY:
            # Load proxies from file
            with open(Path(Path(__file__).parents[2], "proxies.txt"), "r") as f:
                self.pools = [line.strip() for line in f.readlines()]
            self.pools = list(set(self.pools))
        else:
            self.logger.info("Proxy is disabled")

    @contextmanager
    def get(self) -> Generator["str | None", None, None]:
        proxy = random.choice(self.pools) if self.pools else None
        try:
            yield proxy
        except ProxyForbiddenException as e:
            self.logger.error(f"Proxy {proxy} failed: {e}")
        else:
            self.pools.append(proxy)

    def add(self, proxy: str):
        self.pools.append(proxy)

    def delete(self, proxy: str):
        self.pools.remove(proxy)
