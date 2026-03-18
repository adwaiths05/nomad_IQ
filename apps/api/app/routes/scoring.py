from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.scoring import ScoreBatchRequest, ScorePlaceRequest, ScoreRead
from app.services.scoring_service import score_batch, score_place

router = APIRouter(prefix="/score", tags=["scoring"])


@router.post("/place", response_model=ScoreRead)
async def score_place_endpoint(payload: ScorePlaceRequest, db: AsyncSession = Depends(get_db)) -> ScoreRead:
    row = await score_place(db, str(payload.place_id))
    return ScoreRead.model_validate(row)


@router.post("/batch", response_model=list[ScoreRead])
async def score_batch_endpoint(payload: ScoreBatchRequest, db: AsyncSession = Depends(get_db)) -> list[ScoreRead]:
    rows = await score_batch(db, [str(place_id) for place_id in payload.place_ids])
    return [ScoreRead.model_validate(row) for row in rows]
