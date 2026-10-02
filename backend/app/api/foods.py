from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(
    prefix="/api/foods",
    tags=["foods"],
    redirect_slashes=False,
)


@router.post("/", response_model=schemas.FoodRead, status_code=status.HTTP_201_CREATED)
def create_food(food: schemas.FoodCreate, db: Session = Depends(get_db)):
    existing_food = crud.get_food_by_name(db, name=food.name)
    if existing_food:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Продукт с названием '{food.name}' уже существует"
        )
    return crud.create_food(db=db, food=food)


@router.get("/", response_model=list[schemas.FoodRead])
def get_foods(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_foods(db, skip=skip, limit=limit)


@router.get("/{food_id}", response_model=schemas.FoodRead)
def get_food(food_id: int, db: Session = Depends(get_db)):
    db_food = crud.get_food(db, food_id=food_id)
    if not db_food:
        raise HTTPException(status_code=404, detail=f"Продукт с ID {food_id} не найден")
    return db_food


@router.patch("/{food_id}", response_model=schemas.FoodRead)
def update_food(food_id: int, food: schemas.FoodUpdate, db: Session = Depends(get_db)):
    db_food = crud.update_food(db, food_id=food_id, food=food)
    if not db_food:
        raise HTTPException(status_code=404, detail=f"Продукт с ID {food_id} не найден")
    return db_food


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, db: Session = Depends(get_db)):
    try:
        success = crud.delete_food(db, food_id=food_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Продукт с ID {food_id} не найден")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))