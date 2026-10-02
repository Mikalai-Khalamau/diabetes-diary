from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(
    prefix="/api/meal-events",
    tags=["meal-events"],
    redirect_slashes=False,
)


@router.post(
    "/",
    response_model=schemas.MealEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать приём пищи",
)
def create_meal_event(event: schemas.MealEventCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_meal_event(db=db, event=event)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=list[schemas.MealEventRead],
    summary="Получить список приёмов пищи",
)
def get_meal_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_meal_events(db, skip=skip, limit=limit)


@router.get(
    "/{event_id}",
    response_model=schemas.MealEventRead,
    summary="Получить приём пищи",
)
def get_meal_event(event_id: int, db: Session = Depends(get_db)):
    db_event = crud.get_meal_event(db, event_id=event_id)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Приём пищи с ID {event_id} не найден"
        )
    return db_event


@router.patch(
    "/{event_id}",
    response_model=schemas.MealEventRead,
    summary="Обновить приём пищи",
)
def update_meal_event(
    event_id: int,
    event: schemas.MealEventUpdate,
    db: Session = Depends(get_db)
):
    try:
        db_event = crud.update_meal_event(db, event_id=event_id, event=event)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Приём пищи с ID {event_id} не найден"
            )
        return db_event
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить приём пищи",
)
def delete_meal_event(event_id: int, db: Session = Depends(get_db)):
    success = crud.delete_meal_event(db, event_id=event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Приём пищи с ID {event_id} не найден"
        )
    return None