"""图片解析: 调用多模态 LLM 生成结构化文字描述。"""
from ..config import settings
from ..llm import get_llm_provider

_DESCRIBE_PROMPT = (
    "你是一个多模态知识库助手。请详细描述这张图片的内容："
    "包括画面主体、背景、图中文字信息（若是PPT/截图请逐条转写）、"
    "图表数据以及整体主题。请用结构化的中文回答。"
)


def generate_description(file_path: str) -> str:
    """将图片转为可检索的文字描述。"""
    provider = get_llm_provider()
    return provider.describe_image(file_path, prompt=_DESCRIBE_PROMPT)
