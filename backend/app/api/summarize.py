"""摘要接口: 生成指定文件 (支持跨文档) 的内容摘要。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..database import get_db
from ..models.user import User
from ..schemas.chat import ChatQueryOut, SummarizeIn
from ..services import rag_service
from ..services.file_service import get_owned_file

router = APIRouter(tags=["summarize"])

_SUMMARY_PROMPT = (
    "请总结这些文档的主要内容，要求："
    "1) 提炼核心观点；"
    "2) 列出关键信息与结论；"
    "3) 若包含多个文档，请对比其主题异同；"
    "4) 使用条理清晰的结构化中文输出。"
)


@router.post("/summarize", response_model=ChatQueryOut)
def summarize(
    payload: SummarizeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成指定文件的摘要 (支持一次多个文件)。"""
    if not payload.file_ids:
        raise HTTPException(status_code=400, detail="至少需要选择一个文件来生成摘要")
    for fid in payload.file_ids:
        get_owned_file(db, fid, current_user.id)

    result = rag_service.rag_query(_SUMMARY_PROMPT, payload.file_ids, current_user.id)
    rag_service.save_conversation(
        db, current_user.id, "生成文档摘要", result["answer"], payload.file_ids
    )
    return ChatQueryOut(**result)
