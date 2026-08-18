"""JWT 令牌的创建与校验。"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from ..config import settings


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """为指定用户 (subject=user_id) 签发 JWT。"""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """解码并校验 JWT，非法/过期返回 None。"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
