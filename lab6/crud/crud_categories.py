"""
Модуль CRUD-операций для категорий товаров (Category).
Содержит функции для получения, создания, обновления и удаления категорий,
а также эндпоинты FastAPI с группировкой через APIRouter.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, InstrumentedAttribute
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


def get_categories(
        db: Session,
        page: int = 1,
        limit: int = 100,
        sort: str = "id",
        order: str = "asc",
        name: Optional[str] = None,
        description: Optional[str] = None
):
    """
    Получить список категорий с пагинацией, сортировкой и фильтрацией.

    Args:
        db (Session): Сессия базы данных.
        page (int): Номер страницы (начиная с 1).
        limit (int): Количество записей на странице.
        sort (str): Поле сортировки ('id' или 'name').
        order (str): Направление ('asc' или 'desc').
        name (str, optional): Фильтр по имени (частичное совпадение, без учёта регистра).
        description (str, optional): Фильтр по описанию (частичное совпадение).

    Returns:
        List[models.Category]: Список категорий, удовлетворяющих условиям.
    """
    query = db.query(models.Category)

    if name:
        query = query.filter(models.Category.name.ilike(f"%{name}%"))
    if description:
        query = query.filter(models.Category.description.ilike(f"%{description}%"))

    if not hasattr(models.Category, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort column: '{sort}'")
    attr = getattr(models.Category, sort)
    if not isinstance(attr, InstrumentedAttribute):
        raise HTTPException(status_code=400, detail=f"Cannot sort by '{sort}': not a column")
    sort_col = attr

    if order == "desc":
        query = query.order_by(sort_col.desc())
    elif order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown order")

    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


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
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        limit: int = Query(100, ge=1, le=200, description="Items per page"),
        sort: str = "id",
        order: str = "asc",
        name: Optional[str] = Query(None, description="Filter by name (partial match, case-insensitive)"),
        description: Optional[str] = Query(None, description="Filter by description (partial match)"),
        db: Session = Depends(get_db)
):
    """
    GET /categories
    Получить список категорий с пагинацией, сортировкой и фильтрацией.
    """
    return get_categories(
        db,
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        name=name,
        description=description
    )


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
