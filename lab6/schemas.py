from datetime import date

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


# Category
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Supplier
class SupplierBase(BaseModel):
    name: str = Field(..., max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Product
class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    unit: str = Field("шт", max_length=10)
    category_id: int
    supplier_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Views ----------
class TopProductResponse(BaseModel):
    product_id: int
    product_name: str
    unit: str
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None
    total_received_quantity: float
    total_purchase_cost: float
    avg_purchase_price: float
    receipt_count: int
    first_receipt_date: Optional[date] = None
    last_receipt_date: Optional[date] = None
    total_sold_quantity: float
    total_sales_revenue: float
    avg_sales_price: float
    sales_count: int
    current_balance: float
    estimated_profit: float
    turnover_percentage: float
    avg_selling_price: float
    turnover_rank: int
    profit_rank: int

    model_config = ConfigDict(from_attributes=True)


class CategorySummaryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str] = None
    total_products: int
    suppliers_count: int
    products_in_pieces: int
    products_in_kg: int
    products_in_liters: int
    products_in_meters: int
    products_in_packs: int
    total_purchase_cost: float
    total_sales_revenue: float
    gross_profit: float
    total_received_quantity: float
    total_sold_quantity: float
    current_balance_quantity: float
    avg_purchase_price: float
    avg_sales_price: float
    profit_margin_percent: float
    receipt_invoices_count: int
    dispatch_invoices_count: int
    first_receipt_date: Optional[date] = None
    last_receipt_date: Optional[date] = None
    first_sale_date: Optional[date] = None
    last_sale_date: Optional[date] = None
    market_share_percent: float

    model_config = ConfigDict(from_attributes=True)


# ---------- Functions / Procedures ----------
class ProductBalanceResponse(BaseModel):
    product_id: int
    balance: float


class SupplierActiveResponse(BaseModel):
    supplier_id: int
    is_active: bool
    checked_days: int


class AddReceiptItemRequest(BaseModel):
    invoice_id: int
    product_id: int
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)


class AddDispatchItemRequest(BaseModel):
    invoice_id: int
    product_id: int
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)


class ProcedureResponse(BaseModel):
    message: str
    success: bool


# ---------- Reports ----------
class SalesByCategoryResponse(BaseModel):
    category_id: int
    category_name: str
    total_sold_quantity: float
    total_sales_revenue: float
    total_purchase_cost: float
    gross_profit: float
    profit_margin_percent: float
    number_of_products_sold: int

    model_config = ConfigDict(from_attributes=True)


class SalesBySupplierResponse(BaseModel):
    supplier_id: int
    supplier_name: str
    total_sold_quantity: float
    total_sales_revenue: float
    total_purchase_cost: float
    gross_profit: float
    product_count: int

    model_config = ConfigDict(from_attributes=True)


class TopDestinationResponse(BaseModel):
    destination: str
    total_sold_quantity: float
    total_sales_revenue: float
    number_of_invoices: int
    unique_products_count: int

    model_config = ConfigDict(from_attributes=True)


class InventorySummaryResponse(BaseModel):
    product_id: int
    product_name: str
    current_balance: float
    total_received: float
    total_sold: float
    turnover_percentage: float
    days_since_last_sale: Optional[int] = None
    estimated_value: float

    model_config = ConfigDict(from_attributes=True)