from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from database import get_db
import schemas

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales-by-category", response_model=List[schemas.SalesByCategoryResponse])
def sales_by_category(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Агрегированные продажи по категориям: выручка, прибыль, маржинальность.
    """
    sql = text("""
        SELECT 
            c.id as category_id,
            c.name as category_name,
            COALESCE(SUM(di.quantity), 0) as total_sold_quantity,
            COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as total_sales_revenue,
            COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_purchase_cost,
            (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
             COALESCE(SUM(ri.quantity * ri.purchase_price), 0))::numeric(15,2) as gross_profit,
            CASE 
                WHEN COALESCE(SUM(ri.quantity * ri.purchase_price), 0) > 0 
                THEN ROUND(100.0 * (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
                                    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)) / 
                           COALESCE(SUM(ri.quantity * ri.purchase_price), 0), 2)
                ELSE 0 
            END as profit_margin_percent,
            COUNT(DISTINCT p.id) as number_of_products_sold
        FROM category c
        LEFT JOIN product p ON c.id = p.category_id
        LEFT JOIN receipt_item ri ON p.id = ri.product_id
        LEFT JOIN dispatch_item di ON p.id = di.product_id
        GROUP BY c.id, c.name
        HAVING COALESCE(SUM(di.quantity * di.write_off_price), 0) >= :min_revenue
        ORDER BY gross_profit DESC
    """)
    result = db.execute(sql, {"min_revenue": min_revenue})
    rows = result.mappings().all()
    return rows


@router.get("/sales-by-supplier", response_model=List[schemas.SalesBySupplierResponse])
def sales_by_supplier(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Продажи по поставщикам: выручка, прибыль от товаров каждого поставщика.
    """
    sql = text("""
        SELECT 
            s.id as supplier_id,
            s.name as supplier_name,
            COALESCE(SUM(di.quantity), 0) as total_sold_quantity,
            COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as total_sales_revenue,
            COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_purchase_cost,
            (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
             COALESCE(SUM(ri.quantity * ri.purchase_price), 0))::numeric(15,2) as gross_profit,
            COUNT(DISTINCT p.id) as product_count
        FROM supplier s
        LEFT JOIN product p ON s.id = p.supplier_id
        LEFT JOIN receipt_item ri ON p.id = ri.product_id
        LEFT JOIN dispatch_item di ON p.id = di.product_id
        GROUP BY s.id, s.name
        HAVING COALESCE(SUM(di.quantity * di.write_off_price), 0) >= :min_revenue
        ORDER BY gross_profit DESC
    """)
    result = db.execute(sql, {"min_revenue": min_revenue})
    rows = result.mappings().all()
    return rows


@router.get("/top-destinations", response_model=List[schemas.TopDestinationResponse])
def top_destinations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Топ клиентов (пунктов назначения) по сумме закупок из расходных накладных.
    """
    sql = text("""
        SELECT 
            di.destination,
            COALESCE(SUM(di2.quantity), 0) as total_sold_quantity,
            COALESCE(SUM(di2.quantity * di2.write_off_price), 0)::numeric(15,2) as total_sales_revenue,
            COUNT(DISTINCT di.id) as number_of_invoices,
            COUNT(DISTINCT di2.product_id) as unique_products_count
        FROM dispatch_invoice di
        JOIN dispatch_item di2 ON di.id = di2.dispatch_invoice_id
        GROUP BY di.destination
        ORDER BY total_sales_revenue DESC
        LIMIT :limit
    """)
    result = db.execute(sql, {"limit": limit})
    rows = result.mappings().all()
    return rows


@router.get("/inventory-summary", response_model=List[schemas.InventorySummaryResponse])
def inventory_summary(
    low_stock_threshold: float = Query(10, ge=0),
    sort_by: str = Query("current_balance", pattern="^(current_balance|total_sold|turnover_percentage)$"),
    db: Session = Depends(get_db)
):
    """
    Сводка по товарам: текущий остаток, оборачиваемость, дней с последней продажи.
    """
    sql = text("""
        WITH product_stats AS (
            SELECT
                p.id,
                p.name,
                COALESCE(SUM(ri.quantity), 0) as total_received,
                COALESCE(SUM(di.quantity), 0) as total_sold,
                COALESCE(SUM(ri.quantity), 0) - COALESCE(SUM(di.quantity), 0) as current_balance,
                MAX(di2.date) as last_sale_date,
                COALESCE(SUM(di.quantity * di.write_off_price), 0) as estimated_value
            FROM product p
            LEFT JOIN receipt_item ri ON p.id = ri.product_id
            LEFT JOIN dispatch_item di ON p.id = di.product_id
            LEFT JOIN dispatch_invoice di2 ON di.dispatch_invoice_id = di2.id
            GROUP BY p.id, p.name
        )
        SELECT
            id as product_id,
            name as product_name,
            current_balance,
            total_received,
            total_sold,
            CASE
                WHEN total_received > 0
                THEN ROUND(100.0 * total_sold / total_received, 1)
                ELSE 0
            END as turnover_percentage,
            CASE
                WHEN last_sale_date IS NOT NULL
                THEN (CURRENT_DATE - last_sale_date)::int
                ELSE NULL
            END as days_since_last_sale,
            estimated_value
        FROM product_stats
        WHERE current_balance < :threshold OR total_sold > 0
        ORDER BY
            CASE :sort_by
                WHEN 'current_balance' THEN current_balance
                WHEN 'total_sold' THEN total_sold
                ELSE ROUND(100.0 * total_sold / NULLIF(total_received, 0), 1)
            END DESC
    """)
    result = db.execute(sql, {"threshold": low_stock_threshold, "sort_by": sort_by})
    rows = result.mappings().all()
    return rows