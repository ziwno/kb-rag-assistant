"""RAG 问答服务: 检索 → 构建 Prompt → LLM 生成。

支持普通问答与 SSE 流式问答，并持久化聊天记录。
"""
import logging

from sqlalchemy.orm import Session

from ..config import settings
from ..llm import get_llm_provider
from ..models.conversation import Conversation
from . import embedding_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个基于用户个人知识库的智能问答助手。"
    "请严格基于提供的文档片段回答问题；如果文档中没有相关信息，"
    "请明确回答'文档中没有找到相关信息'，不要编造内容。"
    "回答请使用与问题相同的语言，做到简洁、准确、有条理。"
)


def build_context(chunks: list[dict]) -> str:
    parts = [f"[片段 {i + 1}] {c['text']}" for i, c in enumerate(chunks)]
    return "\n\n".join(parts)


def build_messages(question: str, context: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"以下是知识库中检索到的相关文档片段：\n\n{context}\n\n"
                f"请回答用户问题：{question}"
            ),
        },
    ]


def retrieve_context(
    question: str,
    file_ids: list[str],
    user_id: str,
    top_k: int | None = None,
) -> list[dict]:
    """将问题向量化后在 ChromaDB 中检索相关切片。"""
    provider = get_llm_provider()
    query_embedding = provider.embed_texts([question])[0]
    return embedding_service.search_chunks(
        query_embedding,
        file_ids,
        user_id,
        top_k or settings.RETRIEVAL_TOP_K,
    )


# 检索结果为空时的兜底提示 (避免把空上下文交给 LLM 产生误导性回答)
EMPTY_RETRIEVAL_MSG = (
    "所选文档中没有找到可用的内容。请确认文件已处理完成（状态为“已就绪”），"
    "或重新选择文档范围后重试。"
)


def rag_query(question: str, file_ids: list[str], user_id: str) -> dict:
    """非流式 RAG，返回 {"answer", "sources"}。"""
    chunks = retrieve_context(question, file_ids, user_id)
    if not chunks:
        return {"answer": EMPTY_RETRIEVAL_MSG, "sources": []}
    context = build_context(chunks)
    provider = get_llm_provider()
    answer = provider.complete(build_messages(question, context))
    sources = sorted({c["metadata"]["filename"] for c in chunks})
    return {"answer": answer, "sources": sources}


async def rag_query_stream(question: str, file_ids: list[str], user_id: str):
    """流式 RAG，逐条 yield 事件: {"type": start|content|end}。"""
    chunks = retrieve_context(question, file_ids, user_id)
    if not chunks:
        yield {"type": "start", "chunk": ""}
        yield {"type": "content", "chunk": EMPTY_RETRIEVAL_MSG}
        yield {"type": "end", "sources": []}
        return
    context = build_context(chunks)
    provider = get_llm_provider()
    sources = sorted({c["metadata"]["filename"] for c in chunks})

    yield {"type": "start", "chunk": ""}
    async for chunk in provider.astream(build_messages(question, context)):
        yield {"type": "content", "chunk": chunk}
    yield {"type": "end", "sources": sources}


def save_conversation(
    db: Session, user_id: str, question: str, answer: str, file_ids: list[str]
) -> None:
    conv = Conversation(
        user_id=user_id, question=question, answer=answer, file_ids=list(file_ids)
    )
    db.add(conv)
    db.commit()
