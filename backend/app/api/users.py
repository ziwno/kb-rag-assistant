"""用户信息接口。"""
from fastapi import APIRouter, Depends

from ..api.deps import get_current_user
from ..models.user import User
from ..schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user
