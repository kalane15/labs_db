"""
Модуль CRUD-операций для категорий товаров (Category).
Содержит функции для получения, создания, обновления и удаления категорий,
а также эндпоинты FastAPI с группировкой через APIRouter.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, APIRouter, Query, Depends
import models, schemas
from database import get_db

router = APIRouter(prefix="/categories", tags=["categories"])


# ---------- CRUD functions ----------
def get_category(db: Session, category_id: int):
    """
    Получить категорию по ID.

    Args:
        db (Session): Сессия базы данных.
        category_id (int): Идентификатор категории.

    Returns:
        models.Category | None: Объект категории или None.
    """
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100, sort: str = "id", order: str = "asc"):
    """
    Получить список категорий с пагинацией и сортировкой.

    Args:
        db (Session): Сессия базы данных.
        skip (int): Количество записей для пропуска.
        limit (int): Максимальное количество записей.
        sort (str): Поле сортировки ('id' или 'name').
        order (str): Направление ('asc' или 'desc').

    Returns:
        List[models.Category]: Список категорий.
    """
    query = db.query(models.Category)
    if sort == "name":
        order_col = models.Category.name
    else:
        order_col = models.Category.id
    if order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    return query.offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate):
    """
    Создать новую категорию.

    Args:
        db (Session): Сессия базы данных.
        category (schemas.CategoryCreate): Данные для создания.

    Returns:
        models.Category: Созданная категория.

    Raises:
        HTTPException: 409, если имя категории уже существует.
    """
    try:
        db_category = models.Category(**category.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "duplicate key" in err_msg or "unique constraint" in err_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Database error: {e.orig}")


def update_category(db: Session, category_id: int, category_update: schemas.CategoryUpdate):
    """
    Обновить категорию.

    Args:
        db (Session): Сессия базы данных.
        category_id (int): ID категории.
        category_update (schemas.CategoryUpdate): Данные для обновления.

    Returns:
        models.Category: Обновлённая категория.

    Raises:
        HTTPException: 404, если категория не найдена;
                       409, если новое имя уже существует.
    """
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    try:
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "duplicate key" in err_msg or "unique constraint" in err_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Update error: {e.orig}")


def delete_category(db: Session, category_id: int):
    """
    Удалить категорию.

    Args:
        db (Session): Сессия базы данных.
        category_id (int): ID категории.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: 404, если категория не найдена;
                       409, если на категорию ссылаются товары.
    """
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        db.delete(db_category)
        db.commit()
        return {"message": "Category deleted"}
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "foreign key constraint" in err_msg or "references" in err_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Cannot delete category: products reference it")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Deletion error: {e.orig}")


# ---------- Endpoints ----------
@router.get("/", response_model=List[schemas.CategoryResponse])
def read_categories(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        sort: str = "id",
        order: str = "asc",
        db: Session = Depends(get_db)
):
    """
    GET /categories
    Получить список категорий с пагинацией и сортировкой.
    """
    return get_categories(db, skip=skip, limit=limit, sort=sort, order=order)


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def read_category(category_id: int, db: Session = Depends(get_db)):
    """
    GET /categories/{category_id}
    Получить категорию по ID.
    """
    db_category = get_category(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.post("/", response_model=schemas.CategoryResponse, status_code=201)
def create_category_endpoint(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    POST /categories
    Создать новую категорию.
    """
    return create_category(db, category)


@router.patch("/{category_id}", response_model=schemas.CategoryResponse)
def update_category_endpoint(
        category_id: int,
        category_update: schemas.CategoryUpdate,
        db: Session = Depends(get_db)
):
    """
    PATCH /categories/{category_id}
    Частично обновить категорию.
    """
    return update_category(db, category_id, category_update)


@router.delete("/{category_id}")
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """
    DELETE /categories/{category_id}
    Удалить категорию.
    """
    return delete_category(db, category_id)