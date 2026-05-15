from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import schemas

router = APIRouter(prefix="/functions", tags=["functions"])


@router.get("/product-balance/{product_id}", response_model=schemas.ProductBalanceResponse)
def get_product_balance(product_id: int, db: Session = Depends(get_db)):
    """
    Вызов функции get_product_balance для расчёта остатка товара.
    """
    sql = text("SELECT get_product_balance(:pid) AS balance")
    result = db.execute(sql, {"pid": product_id}).scalar()
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found or function error")
    return schemas.ProductBalanceResponse(product_id=product_id, balance=float(result))


@router.get("/supplier-active/{supplier_id}", response_model=schemas.SupplierActiveResponse)
def check_supplier_active(
        supplier_id: int,
        days: int = Query(90, ge=1, le=365),
        db: Session = Depends(get_db)
):
    """
    Вызов функции is_supplier_active для проверки активности поставщика за N дней.
    """
    sql = text("SELECT is_supplier_active(:sid, :days) AS is_active")
    result = db.execute(sql, {"sid": supplier_id, "days": days}).scalar()
    if result is None:
        raise HTTPException(status_code=404, detail="Supplier not found or function error")
    return schemas.SupplierActiveResponse(
        supplier_id=supplier_id,
        is_active=result,
        checked_days=days
    )


@router.post("/add-receipt-item", response_model=schemas.ProcedureResponse, status_code=201)
def call_add_receipt_item(req: schemas.AddReceiptItemRequest, db: Session = Depends(get_db)):
    """
    Вызов процедуры add_receipt_item для добавления позиции в приходную накладную.
    """
    try:
        sql = text("CALL add_receipt_item(:inv_id, :prod_id, :qty, :price)")
        db.execute(sql, {
            "inv_id": req.invoice_id,
            "prod_id": req.product_id,
            "qty": req.quantity,
            "price": req.price
        })
        db.commit()
        return schemas.ProcedureResponse(message="Receipt item added successfully", success=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/add-dispatch-item", response_model=schemas.ProcedureResponse, status_code=201)
def call_add_dispatch_item(req: schemas.AddDispatchItemRequest, db: Session = Depends(get_db)):
    """
    Вызов процедуры add_dispatch_item для добавления позиции в расходную накладную.
    Контроль остатка выполняется внутри процедуры.
    """
    try:
        sql = text("CALL add_dispatch_item(:inv_id, :prod_id, :qty, :price)")
        db.execute(sql, {
            "inv_id": req.invoice_id,
            "prod_id": req.product_id,
            "qty": req.quantity,
            "price": req.price
        })
        db.commit()
        return schemas.ProcedureResponse(message="Dispatch item added successfully", success=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
