"""对话接口: 非流式问答 + SSE 流式问答。"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..database import get_db
from ..models.user import User
from ..schemas.chat import ChatQueryIn, ChatQueryOut
from ..services import rag_service
from ..services.file_service import get_owned_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# SSE 心跳间隔 (秒)，防止代理 / 客户端判定连接超时
HEARTBEAT_SECONDS = 15


def _validate_files(db: Session, user_id: str, file_ids: list[str]) -> None:
    """校验所有 file_id 都属于当前用户，防止越权检索他人文件。"""
    for fid in file_ids:
        get_owned_file(db, fid, user_id)


@router.post("/query", response_model=ChatQueryOut)
def query(
    payload: ChatQueryIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """普通问答 (非流式)。"""
    _validate_files(db, current_user.id, payload.file_ids)
    result = rag_service.rag_query(payload.question, payload.file_ids, current_user.id)
    rag_service.save_conversation(
        db, current_user.id, payload.question, result["answer"], payload.file_ids
    )
    return ChatQueryOut(**result)


@router.get("/stream")
async def stream_chat(
    question: str = Query(..., min_length=1, description="用户问题"),
    file_ids: str = Query(
        "", description="逗号分隔的文件ID列表；为空则跨当前用户全部文档检索"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """流式问答 (SSE)。

    事件格式:
      data: {"type":"start","chunk":""}
      data: {"type":"content","chunk":"..."}
      data: {"type":"end","sources":["a.pdf"]}
      data: [DONE]
    空行注释 `: ping` 为心跳。
    """
    ids = [fid.strip() for fid in file_ids.split(",") if fid.strip()]
    if ids:
        _validate_files(db, current_user.id, ids)

    async def event_generator():
        queue: asyncio.Queue[tuple[str, object | None]] = asyncio.Queue()

        async def _retrieve_and_stream() -> None:
            try:
                async for event in rag_service.rag_query_stream(
                    question, ids, current_user.id
                ):
                    await queue.put(("event", event))
            except Exception as exc:  # noqa: BLE001
                logger.exception("流式问答生成失败")
                await queue.put(
                    ("event", {"type": "error", "chunk": f"生成失败: {exc}"})
                )
            finally:
                await queue.put(("end", None))

        async def _heartbeat() -> None:
            while True:
                await asyncio.sleep(HEARTBEAT_SECONDS)
                await queue.put(("ping", None))

        retrieve_task = asyncio.create_task(_retrieve_and_stream())
        ping_task = asyncio.create_task(_heartbeat())
        try:
            while True:
                kind, payload = await queue.get()
                if kind == "event":
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                elif kind == "ping":
                    yield ": ping\n\n"
                else:  # end
                    yield "data: [DONE]\n\n"
                    break
        finally:
            retrieve_task.cancel()
            ping_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
