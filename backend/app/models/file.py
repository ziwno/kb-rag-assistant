"""文件表模型。"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # pdf | image | audio | text
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 本地/对象存储路径
    file_path: Mapped[str] = mapped_column(String(500), default="")
    file_size: Mapped[int | None] = mapped_column(BigInteger, default=0)
    # pending -> processing -> completed | failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="files")

    def __repr__(self) -> str:
        return f"<File {self.filename} ({self.status})>"
