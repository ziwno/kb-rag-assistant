"""文件相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size: int | None
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime


class FileUploadResponse(BaseModel):
    file_id: str
    status: str = "processing"
    message: str = "文件已上传，后台处理中..."


class FileStatusOut(BaseModel):
    file_id: str
    status: str
    chunk_count: int = 0
    error_message: str | None = None
