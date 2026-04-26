from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.ambient_ai import AmbientAssistRequest, AmbientAssistResponse, QueryExpansionResponse
from app.services.ambient_ai_service import assist_with_ambient_context, expand_ambient_query

router = APIRouter(prefix="/ai", tags=["ambient-ai"])


@router.post("/assist", response_model=AmbientAssistResponse)
async def ambient_assist(payload: AmbientAssistRequest, db: AsyncSession = Depends(get_db)) -> AmbientAssistResponse:
    return await assist_with_ambient_context(db, payload)


@router.post("/expand", response_model=QueryExpansionResponse)
async def ambient_expand(payload: AmbientAssistRequest, db: AsyncSession = Depends(get_db)) -> QueryExpansionResponse:
    return await expand_ambient_query(db, payload)