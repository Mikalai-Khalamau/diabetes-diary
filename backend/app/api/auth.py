from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.deps import get_current_user
from app.security import create_access_token

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    redirect_slashes=False,
)


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, email=payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )
    user = crud.create_user(db=db, user=payload)
    crud.create_default_foods(db, user_id=user.id)
    return user

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Вход (получение JWT-токена)",
)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    token = create_access_token(subject=user.email)
    return schemas.Token(access_token=token)


@router.get(
    "/me",
    response_model=schemas.UserRead,
    summary="Текущий пользователь",
)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user