"""文件上传相关的工具函数。"""
import uuid
from pathlib import Path

from fastapi import UploadFile

from ..config import settings

ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "pdf": {".pdf"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"},
    "text": {".txt", ".md"},
}


def infer_file_type(filename: str) -> str | None:
    """根据扩展名推断文件类型，未知返回 None。"""
    ext = Path(filename).suffix.lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


def save_upload(file: UploadFile, filename: str, user_id: str) -> Path:
    """将上传文件流式写入磁盘，返回存储路径 (带随机文件名防冲突)。"""
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix or ""
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = user_dir / stored_name

    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):  # 1MB 分块，避免大文件占内存
            out.write(chunk)

    return dest
