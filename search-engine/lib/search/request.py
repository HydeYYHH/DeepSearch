from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, ProxyConfig, SemaphoreDispatcher


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

    @staticmethod
    async def get(urls: list[str], **kwargs) -> list[Response]:
        async with AsyncWebCrawler(
                config=BrowserConfig(headless=True,
                                     proxy_config=ProxyConfig(server=kwargs.get("proxy")) if kwargs.get("proxy") else None,
                                     user_agent=kwargs.get("user_agent",
                                                           "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36"),
                                     verbose=True,
                                     headers=kwargs.get("headers", {}),
                                     cookies=[kwargs.get('cookies')] if kwargs.get('cookies') else [],
                                     enable_stealth=True)
        ) as crawler:
            scripts = []
            config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                js_code=scripts,
                exclude_external_links=True,
                exclude_social_media_links=True,
                exclude_all_images=True,
                remove_overlay_elements=True,
                magic=True,
                simulate_user=True,
                override_navigator=True,
            )
            responses = await crawler.arun_many(
                urls=[u if not kwargs.get("params") else f"{u}?{urlencode(kwargs.get('params', {}))}" for u in (urls or [])],
                config=config,
                dispatcher=SemaphoreDispatcher(
                    semaphore_count=kwargs.get("semaphore_count", 5),
                    max_session_permit=kwargs.get("max_session_permit", 20),
                )
            )
            wrapped = [
                Response(
                    url=resp.url,
                    status_code=200 if resp.success else 400,
                    html=resp.html,
                    markdown=resp.markdown.raw_markdown
                ) for resp in responses
            ]
        return wrapped
