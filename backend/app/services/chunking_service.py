"""文本切片服务 (LangChain RecursiveCharacterTextSplitter)。"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import settings


def split_text(text: str) -> list[str]:
    """将长文本切成有重叠窗口的切片。

    分隔符按中文习惯优先 (段落 → 句号 → 分号 → 空格)，减少句子被截断。
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", ". ", " ", ""],
    )
    return splitter.split_text(text)
