"""对话 / 摘要相关 Pydantic 模型。"""
from pydantic import BaseModel, Field


class ChatQueryIn(BaseModel):
    question: str = Field(min_length=1)
    file_ids: list[str] = Field(default_factory=list)


class ChatQueryOut(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)


class SummarizeIn(BaseModel):
    # 允许为空列表，由端点返回语义化的 400 (而非 Pydantic 的 422)
    file_ids: list[str] = Field(default_factory=list, description="需要摘要的文件ID列表")
