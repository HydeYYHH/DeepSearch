import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode


@dataclass
class Response:
    url: str
    status_code: int
    html: str
    markdown: Optional[str] = None

    def raise_for_status(self):
        status_code = int(self.status_code)
        if 400 <= status_code:
            raise RuntimeError(f"HTTP {status_code} for {self.url}")


class RequestClient:

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.crawler = AsyncWebCrawler()

    async def get(self, url: str, **kwargs):
        if not self.crawler.ready:
            await self.crawler.start()
        scripts = []
        config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            js_code=scripts,
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_links=True,
            remove_overlay_elements=True,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            wait_for_timeout=5000,
        )
        resp = await self.crawler.arun(
            url=url if not kwargs.get("params") else f"{url}?{urlencode(kwargs.get('params', {}))}",
            config=config,
        )
        wrapped = Response(
            url=resp.url,
            status_code=resp.status_code if resp.status_code else 200 if resp.success else 400,
            html=resp.html,
            markdown=resp.markdown.raw_markdown if resp.markdown else None
        )
        wrapped.raise_for_status()
        return wrapped

    async def aclose(self):
        await self.crawler.close()
