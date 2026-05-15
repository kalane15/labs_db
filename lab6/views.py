from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from database import get_db
import schemas

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/top-products", response_model=List[schemas.TopProductResponse])
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    min_sold: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Возвращает топ товаров по обороту из представления top_products_by_turnover.
    По умолчанию только товары с total_sold_quantity > 0, сортировка по turnover_rank.
    """
    sql = text("""
        SELECT *
        FROM top_products_by_turnover
        WHERE total_sold_quantity > :min_sold
        ORDER BY turnover_rank
        LIMIT :limit
    """)
    result = db.execute(sql, {"min_sold": min_sold, "limit": limit})
    rows = result.mappings().all()
    return rows


@router.get("/category-summary", response_model=List[schemas.CategorySummaryResponse])
def get_category_summary(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Возвращает сводку по категориям из представления category_summary.
    Фильтр по total_sales_revenue >= min_revenue.
    """
    sql = text("""
        SELECT *
        FROM category_summary
        WHERE total_sales_revenue >= :min_revenue
        ORDER BY gross_profit DESC
    """)
    result = db.execute(sql, {"min_revenue": min_revenue})
    rows = result.mappings().all()
    return rows