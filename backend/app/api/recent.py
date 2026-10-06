from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(
    prefix="/api",
    tags=["recent"],
    redirect_slashes=False,
)


@router.get("/events/recent", response_model=schemas.RecentEventsResponse, summary="Получить события за сегодня и вчера")
def get_recent_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_recent_events(db, user_id=current_user.id, timezone_str=settings.app_timezone)


@router.get("/stats/recent", response_model=schemas.RecentStatsResponse, summary="Получить статистику за сегодня и вчера")
def get_recent_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_recent_stats(db, user_id=current_user.id, timezone_str=settings.app_timezone)