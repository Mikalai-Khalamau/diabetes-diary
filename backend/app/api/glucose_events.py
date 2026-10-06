from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(
    prefix="/api/glucose-events",
    tags=["glucose-events"],
    redirect_slashes=False,
)


@router.post("/", response_model=schemas.GlucoseEventRead, status_code=status.HTTP_201_CREATED, summary="Создать измерение сахара")
def create_glucose_event(
    event: schemas.GlucoseEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_glucose_event(db=db, event=event, user_id=current_user.id)


@router.get("/", response_model=list[schemas.GlucoseEventRead], summary="Получить список измерений сахара")
def get_glucose_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_glucose_events(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=schemas.GlucoseEventRead, summary="Получить измерение сахара")
def get_glucose_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = crud.get_glucose_event(db, event_id=event_id, user_id=current_user.id)
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Измерение сахара с ID {event_id} не найдено")
    return db_event


@router.patch("/{event_id}", response_model=schemas.GlucoseEventRead, summary="Обновить измерение сахара")
def update_glucose_event(
    event_id: int,
    event: schemas.GlucoseEventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = crud.update_glucose_event(db, event_id=event_id, user_id=current_user.id, event=event)
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Измерение сахара с ID {event_id} не найдено")
    return db_event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить измерение сахара")
def delete_glucose_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    success = crud.delete_glucose_event(db, event_id=event_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Измерение сахара с ID {event_id} не найдено")
    return None