"""音频转文字 (Whisper)。

智谱暂无 Whisper 等价接口，因此音频转写统一走 OpenAI Whisper API；
即使 LLM 供应商选择 zhipu，只要配置了 OPENAI_API_KEY 即可转写音频。
"""
import logging

from ..config import settings

logger = logging.getLogger(__name__)


def transcribe(file_path: str) -> str:
    """将音频文件转为文字 (本地文件路径 → 文本)。"""
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("音频转写需要配置 OPENAI_API_KEY (Whisper API)")

    from openai import OpenAI

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None
    )
    with open(file_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=settings.OPENAI_WHISPER_MODEL, file=f
        )
    return result.text or ""
