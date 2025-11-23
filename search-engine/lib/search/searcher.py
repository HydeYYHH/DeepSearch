import asyncio
import logging
import math
from tenacity import retry, stop_after_attempt, wait_exponential

from lib.search.engines.base import Engine, Result, Schema
from dataclasses import dataclass

from lib.search.request import RequestClient
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


@dataclass
class EngineConfig(object):
    engine: Engine
    weight: int = 1


def _build_index(documents):
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return VectorStoreIndex.from_documents(documents, embed_model=embed_model)


class Searcher(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=5, max=30))
    async def search(self, target: str, engine: Engine, abstract: str = None, **kwargs) -> Result:
        try:
            return await engine.search(target, **kwargs)
        except Exception as e:
            self.logger.error(f"Error occurred while searching: {e}")
            if abstract:
                return Result(title=target, content=[Schema(content=abstract, url=target)])
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
        tasks = [
            self.search(target=content.url, engine=Engine(client=client), abstract=content.abstract, **kwargs)
            for content in contents
        ]
        previews = await asyncio.gather(*tasks, return_exceptions=True)
        documents = []
        for i, res in enumerate(previews):
            if isinstance(res, Exception):
                continue
            text = f"{res.title}\n{res.content[0].content if res.content else ''}"
            doc = Document(text=text, metadata={"url": contents[i].url})
            doc.excluded_embed_metadata_keys = ["url"]
            doc.excluded_llm_metadata_keys = ["url"]
            documents.append(doc)
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        nodes = splitter.get_nodes_from_documents(documents)
        documents = [Document(text=n.text, metadata={"url": n.metadata.get("url")}) for n in nodes]
        index = _build_index(documents)
        retriever = index.as_retriever(similarity_top_k=min(num, len(documents)))
        nodes = retriever.retrieve(query)
        return Result(title=query,
                      content=[Schema(content=n.text, url=n.metadata.get("url")) for n in nodes])
