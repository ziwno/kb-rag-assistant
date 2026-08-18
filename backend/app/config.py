"""集中式配置管理。

所有配置通过环境变量 / .env 注入，由 pydantic-settings 读取。
Docker Compose 会覆盖 DATABASE_URL / REDIS_URL 等基础设施地址。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---------- 基础设施 ----------
    DATABASE_URL: str = "sqlite:///./knowledge_db.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---------- 安全 / JWT ----------
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ---------- LLM 供应商 ----------
    # 可选值: "openai" | "zhipu"
    LLM_PROVIDER: str = "openai"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_WHISPER_MODEL: str = "whisper-1"

    ZHIPU_API_KEY: str = ""
    ZHIPU_CHAT_MODEL: str = "glm-4"
    ZHIPU_VISION_MODEL: str = "glm-4v"
    ZHIPU_EMBEDDING_MODEL: str = "embedding-2"

    # ---------- 向量库 ----------
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "file_chunks"

    # ---------- 文件存储 ----------
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 104857600  # 100MB

    # ---------- RAG ----------
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 5

    # ---------- 异步任务 ----------
    # true: 使用 Celery (生产)；false: 使用 FastAPI BackgroundTasks 内联处理 (本地调试)
    USE_CELERY: bool = True

    @property
    def is_provider_openai(self) -> bool:
        return self.LLM_PROVIDER.lower() == "openai"

    @property
    def collection_name(self) -> str:
        # 不同供应商的 embedding 维度不同 (OpenAI 1536 / 智谱 1024)，
        # 因此按供应商隔离 collection，避免混用导致检索结果异常。
        return f"{self.CHROMA_COLLECTION}_{self.LLM_PROVIDER.lower()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
