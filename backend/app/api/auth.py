"""认证接口: 注册 / 登录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import Token, UserCreate, UserLogin, UserOut
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """用户注册。"""
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """用户登录，返回 JWT token。"""
    access_token = auth_service.login(db, payload.username, payload.password)
    return Token(access_token=access_token)
