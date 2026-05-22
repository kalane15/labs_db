from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, desc, or_
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_float(value) -> float:
    return float(value) if value is not None else 0.0


def _sales_revenue_expr():
    return func.coalesce(func.sum(models.DispatchItem.quantity * models.DispatchItem.write_off_price), 0)


def _purchase_cost_expr():
    return func.coalesce(func.sum(models.ReceiptItem.quantity * models.ReceiptItem.purchase_price), 0)


@router.get("/sales-by-category", response_model=List[schemas.SalesByCategoryResponse])
def sales_by_category(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Агрегированные продажи по категориям: выручка, прибыль, маржинальность.
    """
    sales_revenue = _sales_revenue_expr()
    purchase_cost = _purchase_cost_expr()
    gross_profit = sales_revenue - purchase_cost

    rows = (
        db.query(
            models.Category.id.label("category_id"),
            models.Category.name.label("category_name"),
            func.coalesce(func.sum(models.DispatchItem.quantity), 0).label("total_sold_quantity"),
            sales_revenue.label("total_sales_revenue"),
            purchase_cost.label("total_purchase_cost"),
            gross_profit.label("gross_profit"),
            case(
                (purchase_cost > 0, func.round(100.0 * gross_profit / purchase_cost, 2)),
                else_=0,
            ).label("profit_margin_percent"),
            func.count(func.distinct(models.Product.id)).label("number_of_products_sold"),
        )
        .outerjoin(models.Product, models.Category.id == models.Product.category_id)
        .outerjoin(models.ReceiptItem, models.Product.id == models.ReceiptItem.product_id)
        .outerjoin(models.DispatchItem, models.Product.id == models.DispatchItem.product_id)
        .group_by(models.Category.id, models.Category.name)
        .having(sales_revenue >= min_revenue)
        .order_by(desc(gross_profit))
        .all()
    )

    return [
        schemas.SalesByCategoryResponse(
            category_id=row.category_id,
            category_name=row.category_name,
            total_sold_quantity=_to_float(row.total_sold_quantity),
            total_sales_revenue=_to_float(row.total_sales_revenue),
            total_purchase_cost=_to_float(row.total_purchase_cost),
            gross_profit=_to_float(row.gross_profit),
            profit_margin_percent=_to_float(row.profit_margin_percent),
            number_of_products_sold=row.number_of_products_sold,
        )
        for row in rows
    ]


@router.get("/sales-by-supplier", response_model=List[schemas.SalesBySupplierResponse])
def sales_by_supplier(
    min_revenue: float = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Продажи по поставщикам: выручка, прибыль от товаров каждого поставщика.
    """
    sales_revenue = _sales_revenue_expr()
    purchase_cost = _purchase_cost_expr()
    gross_profit = sales_revenue - purchase_cost

    rows = (
        db.query(
            models.Supplier.id.label("supplier_id"),
            models.Supplier.name.label("supplier_name"),
            func.coalesce(func.sum(models.DispatchItem.quantity), 0).label("total_sold_quantity"),
            sales_revenue.label("total_sales_revenue"),
            purchase_cost.label("total_purchase_cost"),
            gross_profit.label("gross_profit"),
            func.count(func.distinct(models.Product.id)).label("product_count"),
        )
        .outerjoin(models.Product, models.Supplier.id == models.Product.supplier_id)
        .outerjoin(models.ReceiptItem, models.Product.id == models.ReceiptItem.product_id)
        .outerjoin(models.DispatchItem, models.Product.id == models.DispatchItem.product_id)
        .group_by(models.Supplier.id, models.Supplier.name)
        .having(sales_revenue >= min_revenue)
        .order_by(desc(gross_profit))
        .all()
    )

    return [
        schemas.SalesBySupplierResponse(
            supplier_id=row.supplier_id,
            supplier_name=row.supplier_name,
            total_sold_quantity=_to_float(row.total_sold_quantity),
            total_sales_revenue=_to_float(row.total_sales_revenue),
            total_purchase_cost=_to_float(row.total_purchase_cost),
            gross_profit=_to_float(row.gross_profit),
            product_count=row.product_count,
        )
        for row in rows
    ]


@router.get("/top-destinations", response_model=List[schemas.TopDestinationResponse])
def top_destinations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Топ клиентов (пунктов назначения) по сумме закупок из расходных накладных.
    """
    total_sales_revenue = func.coalesce(
        func.sum(models.DispatchItem.quantity * models.DispatchItem.write_off_price), 0
    )

    rows = (
        db.query(
            models.DispatchInvoice.destination.label("destination"),
            func.coalesce(func.sum(models.DispatchItem.quantity), 0).label("total_sold_quantity"),
            total_sales_revenue.label("total_sales_revenue"),
            func.count(func.distinct(models.DispatchInvoice.id)).label("number_of_invoices"),
            func.count(func.distinct(models.DispatchItem.product_id)).label("unique_products_count"),
        )
        .join(models.DispatchItem, models.DispatchInvoice.id == models.DispatchItem.dispatch_invoice_id)
        .group_by(models.DispatchInvoice.destination)
        .order_by(desc(total_sales_revenue))
        .limit(limit)
        .all()
    )

    return [
        schemas.TopDestinationResponse(
            destination=row.destination,
            total_sold_quantity=_to_float(row.total_sold_quantity),
            total_sales_revenue=_to_float(row.total_sales_revenue),
            number_of_invoices=row.number_of_invoices,
            unique_products_count=row.unique_products_count,
        )
        for row in rows
    ]


@router.get("/inventory-summary", response_model=List[schemas.InventorySummaryResponse])
def inventory_summary(
    low_stock_threshold: float = Query(10, ge=0),
    sort_by: str = Query("current_balance", pattern="^(current_balance|total_sold|turnover_percentage)$"),
    db: Session = Depends(get_db)
):
    """
    Сводка по товарам: текущий остаток, оборачиваемость, дней с последней продажи.
    """
    total_received = func.coalesce(func.sum(models.ReceiptItem.quantity), 0)
    total_sold = func.coalesce(func.sum(models.DispatchItem.quantity), 0)
    current_balance = total_received - total_sold

    stats = (
        db.query(
            models.Product.id.label("id"),
            models.Product.name.label("name"),
            total_received.label("total_received"),
            total_sold.label("total_sold"),
            current_balance.label("current_balance"),
            func.max(models.DispatchInvoice.date).label("last_sale_date"),
            func.coalesce(
                func.sum(models.DispatchItem.quantity * models.DispatchItem.write_off_price), 0
            ).label("estimated_value"),
        )
        .outerjoin(models.ReceiptItem, models.Product.id == models.ReceiptItem.product_id)
        .outerjoin(models.DispatchItem, models.Product.id == models.DispatchItem.product_id)
        .outerjoin(
            models.DispatchInvoice,
            models.DispatchItem.dispatch_invoice_id == models.DispatchInvoice.id,
        )
        .group_by(models.Product.id, models.Product.name)
        .subquery()
    )

    turnover_percentage = case(
        (stats.c.total_received > 0, func.round(100.0 * stats.c.total_sold / stats.c.total_received, 1)),
        else_=0,
    )
    days_since_last_sale = case(
        (stats.c.last_sale_date.isnot(None), func.current_date() - stats.c.last_sale_date),
        else_=None,
    )

    sort_columns = {
        "current_balance": stats.c.current_balance,
        "total_sold": stats.c.total_sold,
        "turnover_percentage": turnover_percentage,
    }

    rows = (
        db.query(
            stats.c.id.label("product_id"),
            stats.c.name.label("product_name"),
            stats.c.current_balance.label("current_balance"),
            stats.c.total_received.label("total_received"),
            stats.c.total_sold.label("total_sold"),
            turnover_percentage.label("turnover_percentage"),
            days_since_last_sale.label("days_since_last_sale"),
            stats.c.estimated_value.label("estimated_value"),
        )
        .filter(or_(stats.c.current_balance < low_stock_threshold, stats.c.total_sold > 0))
        .order_by(desc(sort_columns[sort_by]))
        .all()
    )

    return [
        schemas.InventorySummaryResponse(
            product_id=row.product_id,
            product_name=row.product_name,
            current_balance=_to_float(row.current_balance),
            total_received=_to_float(row.total_received),
            total_sold=_to_float(row.total_sold),
            turnover_percentage=_to_float(row.turnover_percentage),
            days_since_last_sale=int(row.days_since_last_sale)
            if row.days_since_last_sale is not None
            else None,
            estimated_value=_to_float(row.estimated_value),
        )
        for row in rows
    ]
