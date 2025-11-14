import asyncio
import logging
import math
import re
from functools import lru_cache
from urllib.parse import urlparse

import hnswlib
import numpy as np
from curl_cffi import ProxySpec
from tenacity import retry, stop_after_attempt, wait_exponential
from tldextract import tldextract

from lib.search.engines.base import Engine, Result
from dataclasses import dataclass

from lib.search.limiter import RateLimiter
from lib.search.proxy import ProxyPool
from lib.search.utils import auto_aclose


def _extract_domain(url: str) -> str:
    extracted = tldextract.extract(url)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}".lower()
    return extracted.fqdn or urlparse(url).netloc


@dataclass
class EngineConfig(object):
    engine: Engine
    weight: int = 1


class Searcher(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxies = ProxyPool()
        self.limiter = RateLimiter()

    @staticmethod
    @lru_cache(maxsize=1)
    def _emb_model():
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("moka-ai/m3e-small")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, max=10))
    async def search(self, query: str) -> Result:
        """Local knowledge search"""
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, max=10))
    @auto_aclose
    async def search(self, target: str, engine: Engine, **kwargs) -> Result:
        with self.proxies.get() as proxy:
            if engine.__class__.NAME == 'base':
                self.limiter.allow(f"{proxy}:{_extract_domain(target)}", strategy=engine.__class__.LIMIT_STRATEGY)
            else:
                self.limiter.allow(f"{proxy}:{engine.__class__.NAME}", strategy=engine.__class__.LIMIT_STRATEGY)
            if proxy:
                kwargs.update({"proxies": ProxySpec(
                    http=f"http://{proxy}",
                    https=f"https://{proxy}",
                )})
            return await engine.search(target, **kwargs)

    async def aggregate_search(self, query: str, engines: list[EngineConfig], num: int = 10, **kwargs) -> Result:
        total = sum(engine.weight for engine in engines)
        nums = [max(1, math.ceil(cfg.weight / total * num * 1.5)) for cfg in engines]
        tasks = [
            self.search(query, cfg.engine, num=nums[i], **kwargs)
            for i, cfg in enumerate(engines)
        ]
        results = await asyncio.gather(*tasks)
        # Extract contents
        contents = []
        texts = []
        pattern = re.compile(
            r"title|description|abstract|summary|content|snippet",
            re.I)
        for res in results:
            if not res:
                continue
            for item in res.content:
                contents.append(item)
                texts.append(f"passage: {"\n".join(
                    str(v) for k, v in vars(item).items() if v and pattern.search(k)
                )}")
        if not texts:
            return Result(title=query, content=[])
        # Embed contents
        embeddings = self._emb_model().encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        query_embedding = self._emb_model().encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
        query_similarities = np.dot(embeddings, query_embedding)

        # Build index
        dim = embeddings.shape[1]
        index = hnswlib.Index(space='ip', dim=dim)
        index.init_index(max_elements=len(embeddings), ef_construction=kwargs.pop("ef", 200), M=kwargs.pop("m", 16))
        index.add_items(embeddings, np.arange(len(embeddings)))
        index.set_ef(kwargs.pop("ef", 100))
        # Dedup
        threshold = kwargs.pop("threshold", 0.9)
        sorted_indices = np.argsort(-query_similarities)
        groups = {}
        group_id = 0
        for idx in sorted_indices:
            assigned = False
            for gid, group_items in groups.items():
                max_similarity = max(np.dot(embeddings[idx], embeddings[item]) for item in group_items)
                if max_similarity > threshold:
                    groups[gid].append(idx)
                    assigned = True
                    break

            if not assigned:
                groups[group_id] = [idx]
                group_id += 1
        keep = []
        for group_items in groups.values():
            group_items.sort(key=lambda x: -query_similarities[x])
            keep.append(group_items[0])
        keep.sort(key=lambda x: -query_similarities[x])
        if len(keep) < num:
            candidate_scores = {}
            for gid, group_items in groups.items():
                if len(group_items) <= 1:
                    continue
                for candidate in group_items[1:]:
                    min_similarity = min(np.dot(embeddings[candidate], embeddings[k]) for k in keep)
                    score = (1 - min_similarity) * query_similarities[candidate]
                    candidate_scores[candidate] = score
            sorted_candidates = sorted(candidate_scores.keys(), key=lambda x: -candidate_scores[x])
            needed = num - len(keep)
            for i in range(min(needed, len(sorted_candidates))):
                if sorted_candidates[i] not in keep:
                    keep.append(sorted_candidates[i])
        if len(keep) < num:
            all_indices = set(range(len(contents)))
            remaining = list(all_indices - set(keep))
            remaining.sort(key=lambda x: -query_similarities[x])
            needed = num - len(keep)
            for i in range(min(needed, len(remaining))):
                keep.append(remaining[i])
        keep.sort(key=lambda x: -query_similarities[x])
        return Result(title=query, content=[contents[i] for i in keep[:num]])
