"""FastAPI 应用入口: CORS 配置、路由注册、启动建表。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, chat, files, summarize, users
from .config import settings
from .database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("数据库初始化完成 (provider=%s)", settings.LLM_PROVIDER)
    yield


app = FastAPI(
    title="AI 个人知识库助手 API",
    description="上传 PDF/图片/音频，基于 RAG 的智能问答与摘要",
    version="1.0.0",
    lifespan=lifespan,
)

# 跨域: 公网部署放开所有来源 (认证走 Bearer token，不依赖 cookie 凭证)。
# 若需收紧，可改为具体的 cpolar 域名白名单。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(summarize.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "provider": settings.LLM_PROVIDER}
