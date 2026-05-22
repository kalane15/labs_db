"""
Модуль CRUD-операций для товаров (Product).
Содержит функции для получения, создания, обновления и удаления товаров,
а также эндпоинты FastAPI с группировкой через APIRouter.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy.exc import IntegrityError
import models, schemas
from database import get_db

router = APIRouter(prefix="/products", tags=["products"])


# ---------- CRUD functions ----------
def get_product(db: Session, product_id: int):
    """
    Получить товар по его ID.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        product_id (int): Идентификатор товара.

    Returns:
        models.Product | None: Объект товара или None, если не найден.
    """
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100, sort: str = "id", order: str = "asc",
                 category_id: int = None, supplier_id: int = None):
    """
    Получить список товаров с поддержкой пагинации, сортировки и фильтрации.

    Args:
        db (Session): Сессия базы данных.
        skip (int): Количество записей для пропуска (пагинация).
        limit (int): Максимальное количество записей.
        sort (str): Поле для сортировки ('id', 'name', 'category_id', 'supplier_id').
        order (str): Направление сортировки ('asc' или 'desc').
        category_id (int, optional): Фильтр по ID категории.
        supplier_id (int, optional): Фильтр по ID поставщика.

    Returns:
        List[models.Product]: Список товаров, удовлетворяющих условиям.
    """
    query = db.query(models.Product)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if supplier_id:
        query = query.filter(models.Product.supplier_id == supplier_id)

    if not hasattr(models.Product, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort column: '{sort}'")
    attr = getattr(models.Product, sort)
    if not isinstance(attr, InstrumentedAttribute):
        raise HTTPException(status_code=400, detail=f"Cannot sort by '{sort}': not a column")
    sort_col = attr

    if order == "desc":
        query = query.order_by(sort_col.desc())
    elif order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown order")

    return query.offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    """
    Создать новый товар.

    Args:
        db (Session): Сессия базы данных.
        product (schemas.ProductCreate): Данные для создания товара.

    Returns:
        models.Product: Созданный объект товара.

    Raises:
        HTTPException: 400, если категория или поставщик не существуют,
                       или нарушено ограничение unit.
    """
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail=f"Category with id {product.category_id} does not exist")
    supplier = db.query(models.Supplier).filter(models.Supplier.id == product.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=400, detail=f"Supplier with id {product.supplier_id} does not exist")

    db_product = models.Product(**product.model_dump())
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "chk_product_unit" in str(e.orig):
            raise HTTPException(status_code=400, detail="Invalid unit value. Allowed: шт, кг, л, м, уп")
        raise HTTPException(status_code=400, detail=f"Database integrity error: {e.orig}")


def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate):
    """
    Обновить существующий товар.

    Args:
        db (Session): Сессия базы данных.
        product_id (int): ID товара для обновления.
        product_update (schemas.ProductUpdate): Данные для обновления.

    Returns:
        models.Product: Обновлённый объект товара.

    Raises:
        HTTPException: 404, если товар не найден;
                       400, если новые категория/поставщик не существуют
                       или нарушено ограничение unit.
    """
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        cat = db.query(models.Category).filter(models.Category.id == update_data["category_id"]).first()
        if not cat:
            raise HTTPException(status_code=400, detail=f"Category id {update_data['category_id']} not found")

    if "supplier_id" in update_data:
        sup = db.query(models.Supplier).filter(models.Supplier.id == update_data["supplier_id"]).first()
        if not sup:
            raise HTTPException(status_code=400, detail=f"Supplier id {update_data['supplier_id']} not found")

    for key, value in update_data.items():
        setattr(db_product, key, value)

    try:
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "chk_product_unit" in str(e.orig):
            raise HTTPException(status_code=400, detail="Invalid unit value. Allowed: шт, кг, л, м, уп")
        raise HTTPException(status_code=400, detail=f"Update error: {e.orig}")


def delete_product(db: Session, product_id: int):
    """
    Удалить товар.

    Args:
        db (Session): Сессия базы данных.
        product_id (int): ID товара для удаления.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: 404, если товар не найден;
                       409, если товар используется в приходных/расходных позициях.
    """
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db.delete(db_product)
        db.commit()
        return {"message": "Product deleted"}
    except IntegrityError as e:
        db.rollback()
        if "foreign key constraint" in str(e.orig).lower() or "fk_receipt_item_product" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete product: it is referenced in receipt or dispatch items"
            )
        raise HTTPException(status_code=400, detail=f"Deletion error: {e.orig}")


# ---------- Endpoints ----------
@router.get("/", response_model=List[schemas.ProductResponse])
def read_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        sort: str = "id",
        order: str = "asc",
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """
    GET /products
    Получить список товаров с пагинацией, сортировкой и фильтрацией.
    """
    return get_products(db, skip=skip, limit=limit, sort=sort, order=order,
                        category_id=category_id, supplier_id=supplier_id)


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    GET /products/{product_id}
    Получить товар по ID.
    """
    db_product = get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@router.post("/", response_model=schemas.ProductResponse, status_code=201)
def create_product_endpoint(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    POST /products
    Создать новый товар.
    """
    return create_product(db, product)


@router.patch("/{product_id}", response_model=schemas.ProductResponse)
def update_product_endpoint(
        product_id: int,
        product_update: schemas.ProductUpdate,
        db: Session = Depends(get_db)
):
    """
    PATCH /products/{product_id}
    Частично обновить товар.
    """
    return update_product(db, product_id, product_update)


@router.delete("/{product_id}")
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """
    DELETE /products/{product_id}
    Удалить товар.
    """
    return delete_product(db, product_id)
