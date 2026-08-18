"""智谱 (GLM) 供应商实现 (对话 / 流式 / Embedding / 视觉)。

官方 zhipuai SDK 为同步实现，流式输出通过线程池包装，
避免阻塞 FastAPI 事件循环。
"""
import asyncio
import base64
import logging

from zhipuai import ZhipuAI

from ..config import settings
from .base import LLMProvider

logger = logging.getLogger(__name__)

_MIME_BY_EXT = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
}

# 用于标记线程流结束 / 异常
_END = object()
_ERR = object()


class ZhipuProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.ZHIPU_API_KEY:
            raise RuntimeError("ZHIPU_API_KEY 未配置，请检查 .env")
        self._client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)

    # ---------- 向量 ----------
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # embedding-2 每次只接受单个字符串，逐条调用
        return [
            self._client.embeddings.create(
                model=settings.ZHIPU_EMBEDDING_MODEL, input=t
            )
            .data[0]
            .embedding
            for t in texts
        ]

    # ---------- 对话 ----------
    def complete(self, messages: list[dict], temperature: float = 0.7) -> str:
        resp = self._client.chat.completions.create(
            model=settings.ZHIPU_CHAT_MODEL, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""

    async def astream(self, messages: list[dict], temperature: float = 0.7):
        # zhipuai SDK 是同步实现，放到线程池执行；
        # 通过 call_soon_threadsafe 把结果切回事件循环，保证 Queue 线程安全。
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _put(item) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, item)

        def _run() -> None:
            try:
                stream = self._client.chat.completions.create(
                    model=settings.ZHIPU_CHAT_MODEL,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    content = (
                        chunk.choices[0].delta.content if chunk.choices else None
                    )
                    if content:
                        _put(content)
            except Exception:  # noqa: BLE001
                logger.exception("Zhipu stream failed")
                _put(_ERR)
            finally:
                _put(_END)

        task = loop.run_in_executor(None, _run)
        try:
            while True:
                item = await queue.get()
                if item is _END:
                    break
                if item is _ERR:
                    raise RuntimeError("智谱流式输出失败，请检查 API Key 与网络")
                yield item
        finally:
            await task

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
            model=settings.ZHIPU_VISION_MODEL,
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
