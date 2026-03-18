from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import AuthMeResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import login_user, logout_user, refresh_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthMeResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthMeResponse:
    user = await register_user(db, payload)
    return AuthMeResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await login_user(db, payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await refresh_tokens(db, payload.refresh_token)


@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await logout_user(db, payload.refresh_token)
    return {"status": "ok"}


@router.get("/me", response_model=AuthMeResponse)
async def me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    return AuthMeResponse.model_validate(current_user)
