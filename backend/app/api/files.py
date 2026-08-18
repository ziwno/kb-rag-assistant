"""文件管理接口: 上传 / 列表 / 状态 / 删除。"""
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.file import FileOut, FileStatusOut, FileUploadResponse
from ..services import file_service
from ..tasks.file_processor import process_file
from ..utils.file_utils import infer_file_type

router = APIRouter(prefix="/files", tags=["files"])

_ALLOWED_TYPES = ("pdf", "image", "audio", "text")


@router.post("/upload", response_model=FileUploadResponse, status_code=202)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str | None = Form(None, description="可选: pdf|image|audio|text，缺省按扩展名推断"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传文件。返回 202，文件在后台异步解析并向量化。"""
    ftype = file_type or infer_file_type(file.filename or "")
    if ftype not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件类型，请上传 PDF / 图片 / 音频 / 文本",
        )
    if file.size is not None and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件超过大小限制 (100MB)")

    # 流式落盘，避免大文件占用内存
    dest = file_service.save_upload(file, file.filename or "unnamed", current_user.id)

    record = file_service.create_file_record(
        db,
        current_user.id,
        file.filename or "unnamed",
        ftype,
        str(dest),
        file.size or dest.stat().st_size,
    )

    if settings.USE_CELERY:
        # 生产: 交给 Celery Worker 异步处理
        process_file.delay(record.id)
    else:
        # 本地调试: 用 FastAPI BackgroundTasks 内联处理
        background_tasks.add_task(process_file.run, record.id)

    return FileUploadResponse(file_id=record.id)


@router.get("", response_model=list[FileOut])
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的文件列表。"""
    return file_service.list_user_files(db, current_user.id)


@router.get("/{file_id}/status", response_model=FileStatusOut)
def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询文件处理状态。"""
    record = file_service.get_owned_file(db, file_id, current_user.id)
    return FileStatusOut(
        file_id=record.id,
        status=record.status,
        chunk_count=record.chunk_count,
        error_message=record.error_message,
    )


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文件 (同时删除向量与本地文件)。"""
    record = file_service.get_owned_file(db, file_id, current_user.id)
    file_service.delete_file(db, record)
