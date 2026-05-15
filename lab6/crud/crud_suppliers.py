"""
Модуль CRUD-операций для поставщиков (Supplier).
Содержит функции для получения, создания, обновления и удаления поставщиков,
а также эндпоинты FastAPI с группировкой через APIRouter.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
import models, schemas
from database import get_db

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


# ---------- CRUD functions ----------
def get_supplier(db: Session, supplier_id: int):
    """
    Получить поставщика по ID.

    Args:
        db (Session): Сессия базы данных.
        supplier_id (int): Идентификатор поставщика.

    Returns:
        models.Supplier | None: Объект поставщика или None.
    """
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()


def get_suppliers(db: Session, skip: int = 0, limit: int = 100, sort: str = "id", order: str = "asc"):
    """
    Получить список поставщиков с пагинацией и сортировкой.

    Args:
        db (Session): Сессия базы данных.
        skip (int): Количество записей для пропуска.
        limit (int): Максимальное количество записей.
        sort (str): Поле сортировки ('id' или 'name').
        order (str): Направление ('asc' или 'desc').

    Returns:
        List[models.Supplier]: Список поставщиков.
    """
    query = db.query(models.Supplier)
    sort_column = models.Supplier.name if sort == "name" else models.Supplier.id
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    return query.offset(skip).limit(limit).all()


def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    """
    Создать нового поставщика.

    Args:
        db (Session): Сессия базы данных.
        supplier (schemas.SupplierCreate): Данные для создания.

    Returns:
        models.Supplier: Созданный поставщик.

    Raises:
        HTTPException: 400, если не заполнено ни одно из contact_person/phone/email,
                       или нарушен формат телефона/email;
                       409, если телефон или email уже существуют.
    """
    if supplier.contact_person is None and supplier.phone is None and supplier.email is None:
        raise HTTPException(status_code=400, detail="At least one of contact_person, phone, email must be provided")
    try:
        db_supplier = models.Supplier(**supplier.model_dump())
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "phone" in err_msg:
            raise HTTPException(status_code=409, detail="Phone number already exists")
        if "email" in err_msg:
            raise HTTPException(status_code=409, detail="Email already exists")
        if "check constraint" in err_msg:
            raise HTTPException(status_code=400, detail="Invalid phone or email format")
        raise HTTPException(status_code=400, detail="Supplier creation failed")


def update_supplier(db: Session, supplier_id: int, supplier_update: schemas.SupplierUpdate):
    """
    Обновить данные поставщика.

    Args:
        db (Session): Сессия базы данных.
        supplier_id (int): ID поставщика.
        supplier_update (schemas.SupplierUpdate): Данные для обновления.

    Returns:
        models.Supplier: Обновлённый поставщик.

    Raises:
        HTTPException: 404, если поставщик не найден;
                       400, если после обновления все три контактных поля стали None
                       или нарушен формат;
                       409, если телефон/email уже используются.
    """
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_data = supplier_update.model_dump(exclude_unset=True)
    new_contact = update_data.get("contact_person", db_supplier.contact_person)
    new_phone = update_data.get("phone", db_supplier.phone)
    new_email = update_data.get("email", db_supplier.email)
    if new_contact is None and new_phone is None and new_email is None:
        raise HTTPException(status_code=400, detail="At least one of contact_person, phone, email must be non-null")
    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    try:
        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "phone" in err_msg:
            raise HTTPException(status_code=409, detail="Phone number already used")
        if "email" in err_msg:
            raise HTTPException(status_code=409, detail="Email already used")
        if "check constraint" in err_msg:
            raise HTTPException(status_code=400, detail="Invalid phone or email format")
        raise HTTPException(status_code=400, detail="Supplier update failed")


def delete_supplier(db: Session, supplier_id: int):
    """
    Удалить поставщика.

    Args:
        db (Session): Сессия базы данных.
        supplier_id (int): ID поставщика.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: 404, если поставщик не найден;
                       409, если на поставщика ссылаются товары или приходы.
    """
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    try:
        db.delete(db_supplier)
        db.commit()
        return {"message": "Supplier deleted"}
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e.orig).lower()
        if "foreign key constraint" in err_msg or "references" in err_msg:
            raise HTTPException(status_code=409, detail="Cannot delete supplier: it is referenced in products or receipts")
        raise HTTPException(status_code=400, detail=f"Deletion failed: {e.orig}")


# ---------- Endpoints ----------
@router.get("/", response_model=List[schemas.SupplierResponse])
def read_suppliers(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        sort: str = "id",
        order: str = "asc",
        db: Session = Depends(get_db)
):
    """
    GET /suppliers
    Получить список поставщиков с пагинацией и сортировкой.
    """
    return get_suppliers(db, skip=skip, limit=limit, sort=sort, order=order)


@router.get("/{supplier_id}", response_model=schemas.SupplierResponse)
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """
    GET /suppliers/{supplier_id}
    Получить поставщика по ID.
    """
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db_supplier


@router.post("/", response_model=schemas.SupplierResponse, status_code=201)
def create_supplier_endpoint(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    """
    POST /suppliers
    Создать нового поставщика.
    """
    return create_supplier(db, supplier)


@router.patch("/{supplier_id}", response_model=schemas.SupplierResponse)
def update_supplier_endpoint(
        supplier_id: int,
        supplier_update: schemas.SupplierUpdate,
        db: Session = Depends(get_db)
):
    """
    PATCH /suppliers/{supplier_id}
    Частично обновить данные поставщика.
    """
    return update_supplier(db, supplier_id, supplier_update)


@router.delete("/{supplier_id}")
def delete_supplier_endpoint(supplier_id: int, db: Session = Depends(get_db)):
    """
    DELETE /suppliers/{supplier_id}
    Удалить поставщика.
    """
    return delete_supplier(db, supplier_id)