"""用户注册 / 登录业务逻辑。"""
import bcrypt
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.auth import UserCreate
from ..utils.auth import create_access_token


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def register_user(db: Session, payload: UserCreate) -> User:
    """注册新用户；用户名或邮箱已存在时抛出 400。"""
    existing = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.email))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已被注册"
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """校验用户名密码，失败抛 401。"""
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def login(db: Session, username: str, password: str) -> str:
    """登录并返回 JWT 字符串。"""
    user = authenticate_user(db, username, password)
    return create_access_token(user.id)
