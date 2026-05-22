"""
Модуль CRUD-операций для поставщиков (Supplier).
Содержит функции для получения, создания, обновления и удаления поставщиков,
а также эндпоинты FastAPI с группировкой через APIRouter.
"""
from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy import Column

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


def get_suppliers(
    db: Session,
    page: int = 1,
    limit: int = 100,
    sort: str = "id",
    order: str = "asc",
    name: Optional[str] = None,
    contact_person: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None
):
    """
    Получить список поставщиков с пагинацией, сортировкой и фильтрацией.

    Args:
        db (Session): Сессия базы данных.
        page (int): Номер страницы (начиная с 1).
        limit (int): Количество записей на странице.
        sort (str): Поле сортировки ('id' или 'name').
        order (str): Направление ('asc' или 'desc').
        name (str, optional): Фильтр по имени (частичное совпадение, без учёта регистра).
        contact_person (str, optional): Фильтр по контактному лицу.
        phone (str, optional): Фильтр по телефону (точное совпадение).
        email (str, optional): Фильтр по email (точное совпадение).

    Returns:
        List[models.Supplier]: Список поставщиков, удовлетворяющих условиям.
    """
    query = db.query(models.Supplier)

    if name:
        query = query.filter(models.Supplier.name.ilike(f"%{name}%"))
    if contact_person:
        query = query.filter(models.Supplier.contact_person.ilike(f"%{contact_person}%"))
    if phone:
        query = query.filter(models.Supplier.phone == phone)
    if email:
        query = query.filter(models.Supplier.email == email)

    if not hasattr(models.Supplier, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort column: '{sort}'")
    attr = getattr(models.Supplier, sort)
    if not isinstance(attr, InstrumentedAttribute):
        raise HTTPException(status_code=400, detail=f"Cannot sort by '{sort}': not a column")
    sort_column = attr

    if order == "desc":
        query = query.order_by(sort_column.desc())
    elif order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown order")

    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


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
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(100, ge=1, le=200, description="Items per page"),
    sort: str = "id",
    order: str = "asc",
    name: Optional[str] = Query(None, description="Filter by name (partial match, case-insensitive)"),
    contact_person: Optional[str] = Query(None, description="Filter by contact person (partial match)"),
    phone: Optional[str] = Query(None, description="Filter by phone (exact match)"),
    email: Optional[str] = Query(None, description="Filter by email (exact match)"),
    db: Session = Depends(get_db)
):
    """
    GET /suppliers
    Получить список поставщиков с пагинацией, сортировкой и фильтрацией.
    """
    return get_suppliers(
        db,
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email
    )


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