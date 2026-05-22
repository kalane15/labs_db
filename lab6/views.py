from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from database import get_db
import schemas

router = APIRouter(prefix="/views", tags=["views"])


def _raise_view_db_error(exc: SQLAlchemyError) -> None:
    orig = getattr(exc, "orig", None)
    msg = str(orig or exc)
    lower = msg.lower()
    if "does not exist" in lower or "undefinedtable" in lower or "relation" in lower:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database view is missing. Apply init/6DML-view.sql to the database.",
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Database query failed: {msg}",
    )


@router.get("/top-products", response_model=List[schemas.TopProductResponse])
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    min_sold: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Возвращает топ товаров по обороту из представления top_products_by_turnover.
    Возвращает товары с total_sold_quantity > min_sold, сортировка по turnover_rank.
    """
    try:
        sql = text("""
            SELECT *
            FROM top_products_by_turnover
            WHERE total_sold_quantity > :min_sold
            ORDER BY turnover_rank
            LIMIT :limit
        """)
        result = db.execute(sql, {"min_sold": min_sold, "limit": limit})
        return result.mappings().all()
    except SQLAlchemyError as e:
        _raise_view_db_error(e)


@router.get("/category-summary", response_model=List[schemas.CategorySummaryResponse])
def get_category_summary(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Возвращает сводку по категориям из представления category_summary.
    Фильтр по total_sales_revenue >= min_revenue.
    """
    try:
        sql = text("""
            SELECT *
            FROM category_summary
            WHERE total_sales_revenue >= :min_revenue
            ORDER BY gross_profit DESC
        """)
        result = db.execute(sql, {"min_revenue": min_revenue})
        return result.mappings().all()
    except SQLAlchemyError as e:
        _raise_view_db_error(e)
