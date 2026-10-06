from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(
    prefix="/api/glucose-events",
    tags=["glucose-events"],
redirect_slashes=False,
)


@router.post(
    "/",
    response_model=schemas.GlucoseEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать измерение сахара",
)
def create_glucose_event(event: schemas.GlucoseEventCreate, db: Session = Depends(get_db)):
    """Создаёт новое измерение сахара"""
    return crud.create_glucose_event(db=db, event=event)


@router.get(
    "/",
    response_model=list[schemas.GlucoseEventRead],
    summary="Получить список измерений сахара",
)
def get_glucose_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получает список измерений сахара с пагинацией"""
    return crud.get_glucose_events(db, skip=skip, limit=limit)


@router.get(
    "/{event_id}",
    response_model=schemas.GlucoseEventRead,
    summary="Получить измерение сахара",
)
def get_glucose_event(event_id: int, db: Session = Depends(get_db)):
    """Получает измерение сахара по ID"""
    db_event = crud.get_glucose_event(db, event_id=event_id)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Измерение сахара с ID {event_id} не найдено"
        )
    return db_event


@router.patch(
    "/{event_id}",
    response_model=schemas.GlucoseEventRead,
    summary="Обновить измерение сахара",
)
def update_glucose_event(
    event_id: int,
    event: schemas.GlucoseEventUpdate,
    db: Session = Depends(get_db)
):
    """Обновляет измерение сахара по ID"""
    db_event = crud.update_glucose_event(db, event_id=event_id, event=event)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Измерение сахара с ID {event_id} не найдено"
        )
    return db_event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить измерение сахара",
)
def delete_glucose_event(event_id: int, db: Session = Depends(get_db)):
    """Удаляет измерение сахара по ID"""
    success = crud.delete_glucose_event(db, event_id=event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Измерение сахара с ID {event_id} не найдено"
        )
    return None