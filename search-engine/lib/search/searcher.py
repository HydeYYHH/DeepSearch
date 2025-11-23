import asyncio
import logging
import math
import os
from functools import lru_cache
from itertools import chain
from urllib.parse import urlparse
from google.genai import types

import hnswlib
import numpy as np
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from tldextract import tldextract

from lib.search.engines.base import Engine, Result, Schema
from dataclasses import dataclass

from lib.search.request import RequestClient


def _extract_domain(url: str) -> str:
    extracted = tldextract.extract(url)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}".lower()
    return extracted.fqdn or urlparse(url).netloc


@dataclass
class EngineConfig(object):
    engine: Engine
    weight: int = 1


class EmbeddingModel(object):
    def __init__(self, online: bool = True):
        self.online = online
        if online:
            self.client = genai.Client()
            self.model = self.client.models
        else:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    def encode_documents(self, text: list[str]):
        if self.online:
            _all = []
            BATCH = 100
            for i in range(0, len(text), BATCH):
                batch = text[i:i + BATCH]
                embs = self.model.embed_content(
                    model="gemini-embedding-001", contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                ).embeddings
                _all.extend([e.values for e in embs])
            arr = np.asarray(_all, dtype=np.float32)
            return arr
        else:
            arr = self.model.encode(
                text, normalize_embeddings=True, convert_to_numpy=True,
                batch_size=128
            )
            return arr.astype(np.float32)

    def encode_query(self, text: str):
        if self.online:
            emb = self.model.embed_content(
                model="gemini-embedding-001", contents=text,
                config=types.EmbedContentConfig(task_type="query")
            ).embeddings[0].values
            return np.asarray(emb, dtype=np.float32)
        else:
            arr = self.model.encode(
                [text], normalize_embeddings=True, convert_to_numpy=True,
                batch_size=128,
            )[0]
            return arr.astype(np.float32)


class Searcher(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        online = os.getenv('USE_ONLINE_EMBEDDING', 'false').lower() == 'true'
        self._emb_model = EmbeddingModel(online=online)

    @staticmethod
    @lru_cache(maxsize=1)
    def _chunker():
        from semchunk import chunkerify
        return chunkerify('google-bert/bert-base-multilingual-uncased', 512)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=5, max=30))
    async def search(self, target: str, engine: Engine, abstract: Schema = None, **kwargs) -> Result:
        try:
            return await engine.search(target, **kwargs)
        except Exception as e:
            self.logger.error(f"Error occurred while searching: {e}")
            if abstract:
                return Result(title=target, content=[abstract])
            raise e

    async def aggregate_search(self, query: str, client: RequestClient, engines: list[EngineConfig], num: int = 10,
                               **kwargs) -> Result:
        total = sum(engine.weight for engine in engines)
        nums = [max(1, math.ceil(cfg.weight / total * num * 1.5)) for cfg in engines]
        tasks = [
            self.search(target=query, engine=cfg.engine, abstract=None, num=nums[i], **kwargs)
            for i, cfg in enumerate(engines)
        ]
        results = await asyncio.gather(*tasks)
        # Dedup
        contents = {}
        for res in results or []:
            for item in (res.content if res else []):
                if hasattr(item, "url"):
                    contents[item.url] = item
        if not contents:
            return Result(title=query, content=[])
        contents = list(contents.values())
        # Preview
        tasks = [
            self.search(target=content.url, engine=Engine(client=client), abstract=content.abstract, **kwargs)
            for content in contents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        results = [res for res in results if not isinstance(res, Exception)]
        # Chunking
        chunks, offsets = self._chunker().__call__([f"{res.title}\n{res.content[0].content}" for res in results],
                                                   offsets=True, overlap=0.2)
        chunks = list(chain.from_iterable(chunks))
        doc_offsets = []
        for doc_idx, doc_chunks in enumerate(offsets):
            doc_offsets.extend([doc_idx] * len(doc_chunks))
        # Initialize index
        embeddings = self._emb_model.encode_documents(chunks)
        dim = embeddings.shape[1]
        index = hnswlib.Index(space='cosine', dim=dim)
        index.init_index(max_elements=len(embeddings), ef_construction=200, M=16)
        index.add_items(embeddings, np.arange(len(embeddings)))
        index.set_ef(100)
        # Query
        query_embedding = self._emb_model.encode_query(query).reshape(1, -1)
        labels, _ = index.knn_query(query_embedding, k=min(num, len(chunks)))
        labels = labels[0].astype(int)
        return Result(title=query,
                      content=[Schema(content=chunks[i], url=contents[doc_offsets[i]].url) for i in labels])
