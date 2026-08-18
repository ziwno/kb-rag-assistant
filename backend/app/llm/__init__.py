"""LLM 供应商工厂。根据 config.LLM_PROVIDER 返回对应实现。"""
from ..config import settings
from .base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """按环境变量 LLM_PROVIDER (openai|zhipu) 返回供应商实例。"""
    if settings.is_provider_openai:
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    from .zhipu_provider import ZhipuProvider

    return ZhipuProvider()


__all__ = ["LLMProvider", "get_llm_provider"]
