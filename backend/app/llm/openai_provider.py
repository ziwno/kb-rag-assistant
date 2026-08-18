"""OpenAI 供应商实现 (对话 / 流式 / Embedding / 视觉 / Whisper)。"""
import base64

from openai import AsyncOpenAI, OpenAI

from ..config import settings
from .base import LLMProvider

_MIME_BY_EXT = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
}


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 未配置，请检查 .env")
        self._client = OpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None
        )
        self._async_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None
        )

    # ---------- 向量 ----------
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL, input=texts
        )
        return [item.embedding for item in resp.data]

    # ---------- 对话 ----------
    def complete(self, messages: list[dict], temperature: float = 0.7) -> str:
        resp = self._client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""

    async def astream(self, messages: list[dict], temperature: float = 0.7):
        stream = await self._async_client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # ---------- 视觉 ----------
    def describe_image(self, image_path: str, prompt: str | None = None) -> str:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = image_path.rsplit(".", 1)[-1].lower() if "." in image_path else "png"
        mime = _MIME_BY_EXT.get(ext, "image/png")
        text_prompt = prompt or (
            "请详细描述这张图片的内容，包括画面主体、背景、图中文字信息、"
            "图表数据以及整体主题。请用结构化中文回答。"
        )
        resp = self._client.chat.completions.create(
            model=settings.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content or ""
