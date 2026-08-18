"""LLM 供应商抽象基类。

OpenAI 与智谱 (GLM) 共享同一套接口，
上层业务 (RAG / 文件处理) 只依赖本抽象，便于切换供应商。
"""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成文本向量。"""

    @abstractmethod
    def complete(self, messages: list[dict], temperature: float = 0.7) -> str:
        """同步补全，返回完整文本。"""

    @abstractmethod
    async def astream(self, messages: list[dict], temperature: float = 0.7):
        """异步流式补全，逐段 yield 文本片段 (str)。"""

    @abstractmethod
    def describe_image(self, image_path: str, prompt: str | None = None) -> str:
        """多模态: 为图片生成文字描述。"""
