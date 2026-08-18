"""文件处理 Celery 任务。

流程:
1. 从数据库读取文件信息
2. 按类型解析: PDF → 文本, 图片 → 多模态 LLM 描述, 音频 → Whisper 转写, 文本 → 原文
3. 文本切片 (chunk_size=500, overlap=50)
4. 生成向量并写入 ChromaDB
5. 更新数据库状态为 completed
"""
import logging

from celery import Celery

from ..config import settings
from ..database import SessionLocal
from ..llm import get_llm_provider
from ..models.file import File
from ..parsers import audio_parser, image_parser, pdf_parser
from ..services import embedding_service
from ..services.chunking_service import split_text

logger = logging.getLogger(__name__)

celery_app = Celery(
    "knowledge_base",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="process_file", bind=True, max_retries=2, default_retry_delay=10)
def process_file(self, file_id: str) -> None:
    """处理单个文件: 解析 → 切片 → 向量化 → 更新状态。"""
    db = SessionLocal()
    try:
        record = db.get(File, file_id)
        if record is None:
            logger.warning("文件 %s 不存在，任务退出", file_id)
            return

        record.status = "processing"
        record.error_message = None
        db.commit()

        text = _extract_text_by_type(record)
        chunks = split_text(text)
        if not chunks:
            raise ValueError("未能从文件中提取到有效文本，请检查文件内容")

        provider = get_llm_provider()
        payload = [
            {
                "text": chunk_text,
                "metadata": {
                    "file_id": record.id,
                    "user_id": record.user_id,
                    "chunk_index": idx,
                    "source_type": record.file_type,
                    "filename": record.filename,
                },
            }
            for idx, chunk_text in enumerate(chunks)
        ]
        embedding_service.add_chunks(provider, payload)

        record.status = "completed"
        record.chunk_count = len(chunks)
        record.error_message = None
        db.commit()
        logger.info("文件 %s 处理完成，共 %d 个切片", record.filename, len(chunks))

    except Exception as exc:  # noqa: BLE001
        logger.exception("文件 %s 处理失败", file_id)
        # 网络抖动等瞬时错误自动重试。注意: self.retry(exc=exc) 在重试耗尽时
        # 会把原始异常重新抛出 (而非 MaxRetriesExceededError)，因此用
        # self.request.retries >= max_retries 判断是否耗尽，再标记失败。
        if self.request.retries >= self.max_retries:
            db.rollback()
            record = db.get(File, file_id)
            if record:
                record.status = "failed"
                record.error_message = str(exc)[:1000]
                db.commit()
        else:
            raise self.retry(exc=exc)
    finally:
        db.close()


def _extract_text_by_type(record: File) -> str:
    """按文件类型分派到对应解析器。"""
    if record.file_type == "pdf":
        return pdf_parser.extract_text(record.file_path)
    if record.file_type == "image":
        return image_parser.generate_description(record.file_path)
    if record.file_type == "audio":
        return audio_parser.transcribe(record.file_path)
    if record.file_type == "text":
        with open(record.file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"不支持的文件类型: {record.file_type}")
