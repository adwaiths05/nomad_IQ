from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuthSession
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(str(user.id))
    refresh_token, refresh_expires = create_refresh_token(str(user.id))

    session = AuthSession(user_id=user.id, refresh_token=refresh_token, expires_at=refresh_expires)
    db.add(session)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    session = await db.scalar(select(AuthSession).where(AuthSession.refresh_token == refresh_token))
    if session is None or session.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user_id = payload["sub"]
    access_token = create_access_token(user_id)
    new_refresh_token, refresh_expires = create_refresh_token(user_id)

    session.refresh_token = new_refresh_token
    session.expires_at = refresh_expires
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


async def logout_user(db: AsyncSession, refresh_token: str) -> None:
    await db.execute(delete(AuthSession).where(AuthSession.refresh_token == refresh_token))
    await db.commit()
