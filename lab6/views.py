from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/top-products", response_model=List[schemas.TopProductResponse])
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    min_sold: float = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Топ товаров по обороту из представления top_products_by_turnover.
    Фильтр total_sold_quantity > min_sold, сортировка по turnover_rank.
    """
    rows = (
        db.query(models.TopProductByTurnover)
        .filter(models.TopProductByTurnover.total_sold_quantity > min_sold)
        .order_by(models.TopProductByTurnover.turnover_rank)
        .limit(limit)
        .all()
    )
    return [schemas.TopProductResponse.model_validate(row) for row in rows]


@router.get("/category-summary", response_model=List[schemas.CategorySummaryResponse])
def get_category_summary(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Сводка по категориям из представления category_summary.
    Фильтр total_sales_revenue >= min_revenue, сортировка по gross_profit.
    """
    rows = (
        db.query(models.CategorySummary)
        .filter(models.CategorySummary.total_sales_revenue >= min_revenue)
        .order_by(desc(models.CategorySummary.gross_profit))
        .all()
    )
    return [schemas.CategorySummaryResponse.model_validate(row) for row in rows]
