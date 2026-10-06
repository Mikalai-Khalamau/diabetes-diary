from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(
    prefix="/api/insulin-events",
    tags=["insulin-events"],
    redirect_slashes=False,
)


@router.post("/", response_model=schemas.InsulinEventRead, status_code=status.HTTP_201_CREATED, summary="Создать инъекцию инсулина")
def create_insulin_event(
    event: schemas.InsulinEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_insulin_event(db=db, event=event, user_id=current_user.id)


@router.get("/", response_model=list[schemas.InsulinEventRead], summary="Получить список инъекций инсулина")
def get_insulin_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_insulin_events(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=schemas.InsulinEventRead, summary="Получить инъекцию инсулина")
def get_insulin_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = crud.get_insulin_event(db, event_id=event_id, user_id=current_user.id)
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Инъекция инсулина с ID {event_id} не найдена")
    return db_event


@router.patch("/{event_id}", response_model=schemas.InsulinEventRead, summary="Обновить инъекцию инсулина")
def update_insulin_event(
    event_id: int,
    event: schemas.InsulinEventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_event = crud.update_insulin_event(db, event_id=event_id, user_id=current_user.id, event=event)
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Инъекция инсулина с ID {event_id} не найдена")
    return db_event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить инъекцию инсулина")
def delete_insulin_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    success = crud.delete_insulin_event(db, event_id=event_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Инъекция инсулина с ID {event_id} не найдена")
    return None