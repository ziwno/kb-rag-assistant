"""文件记录的业务逻辑 (增删查)。"""
import logging
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.file import File
from ..utils.file_utils import save_upload
from . import embedding_service

logger = logging.getLogger(__name__)


def create_file_record(
    db: Session,
    user_id: str,
    filename: str,
    file_type: str,
    file_path: str,
    file_size: int | None,
) -> File:
    record = File(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size or 0,
        status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_user_files(db: Session, user_id: str) -> list[File]:
    return (
        db.query(File)
        .filter(File.user_id == user_id)
        .order_by(File.created_at.desc())
        .all()
    )


def get_owned_file(db: Session, file_id: str, user_id: str) -> File:
    """获取属于当前用户的文件，防止越权访问他人文件。"""
    record = (
        db.query(File)
        .filter(File.id == file_id, File.user_id == user_id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )
    return record


def delete_file(db: Session, record: File) -> None:
    """删除文件: 先清向量，再删磁盘文件，最后删数据库记录。"""
    try:
        embedding_service.delete_file_chunks(record.id)
    except Exception:  # noqa: BLE001
        logger.exception("删除文件 %s 的向量切片失败", record.id)

    if record.file_path:
        path = Path(record.file_path)
        try:
            if path.exists():
                path.unlink()
        except OSError:
            logger.warning("删除磁盘文件失败: %s", record.file_path)

    db.delete(record)
    db.commit()
