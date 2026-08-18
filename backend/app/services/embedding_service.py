"""向量存储服务 (ChromaDB)。

向量写入 / 删除 / 检索全部集中在这里。
collection 按供应商隔离 (见 config.collection_name)，
因为不同供应商的 embedding 维度不一致。
"""
import logging

import chromadb

from ..config import settings
from ..llm import LLMProvider

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    """惰性初始化 ChromaDB PersistentClient (进程内单例)。"""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        logger.info("ChromaDB 初始化完成，持久化目录: %s", settings.CHROMA_PERSIST_DIR)
    return _client


def get_collection():
    client = get_client()
    return client.get_or_create_collection(
        name=settings.collection_name, metadata={"hnsw:space": "cosine"}
    )


def add_chunks(provider: LLMProvider, chunks: list[dict]) -> int:
    """批量写入切片。

    chunks: [{"text": str, "metadata": {...}}]
    每个切片的 metadata 包含 file_id / user_id / chunk_index / source_type / filename。
    """
    if not chunks:
        return 0

    collection = get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = provider.embed_texts(texts)
    ids = [f"{c['metadata']['file_id']}_{c['metadata']['chunk_index']}" for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    logger.info("已写入 %d 个切片到 collection %s", len(chunks), settings.collection_name)
    return len(chunks)


def delete_file_chunks(file_id: str) -> None:
    """删除某个文件的全部向量切片。"""
    collection = get_collection()
    collection.delete(where={"file_id": file_id})


def search_chunks(
    query_embedding: list[float],
    file_ids: list[str],
    user_id: str,
    top_k: int = 5,
) -> list[dict]:
    """按相似度检索切片。

    file_ids 为空时检索该用户的全部文档 (跨文档检索)。
    """
    collection = get_collection()
    # chromadb 的 where 顶层若含多个条件，必须用 $and 运算符组合
    if file_ids:
        where = {
            "$and": [{"user_id": user_id}, {"file_id": {"$in": file_ids}}]
        }
    else:
        where = {"user_id": user_id}

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    results: list[dict] = []
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]
    for i, text in enumerate(docs):
        results.append(
            {
                "text": text,
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else None,
            }
        )
    return results
