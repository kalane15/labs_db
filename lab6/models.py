from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String)

    products = relationship("Product", back_populates="category", passive_deletes=True)


class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20), unique=True)
    email = Column(String(100), unique=True)

    products = relationship("Product", back_populates="supplier", passive_deletes=True)


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    unit = Column(String(10), nullable=False, default="шт")
    category_id = Column(Integer, ForeignKey("category.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("supplier.id", ondelete="RESTRICT"), nullable=False)

    category = relationship("Category", back_populates="products", passive_deletes=True)
    supplier = relationship("Supplier", back_populates="products", passive_deletes=True)
    receipt_items = relationship("ReceiptItem", back_populates="product", passive_deletes=True)
    dispatch_items = relationship("DispatchItem", back_populates="product", passive_deletes=True)


class ReceiptInvoice(Base):
    __tablename__ = "receipt_invoice"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    supplier_id = Column(Integer, ForeignKey("supplier.id", ondelete="RESTRICT"), nullable=False)

    items = relationship("ReceiptItem", back_populates="invoice", passive_deletes=True)


class ReceiptItem(Base):
    __tablename__ = "receipt_item"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    purchase_price = Column(Numeric(15, 2), nullable=False)
    receipt_invoice_id = Column(Integer, ForeignKey("receipt_invoice.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="RESTRICT"), nullable=False)

    invoice = relationship("ReceiptInvoice", back_populates="items", passive_deletes=True)
    product = relationship("Product", back_populates="receipt_items", passive_deletes=True)


class DispatchInvoice(Base):
    __tablename__ = "dispatch_invoice"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    destination = Column(String(200), nullable=False)

    items = relationship("DispatchItem", back_populates="invoice", passive_deletes=True)


class DispatchItem(Base):
    __tablename__ = "dispatch_item"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    write_off_price = Column(Numeric(15, 2), nullable=False)
    dispatch_invoice_id = Column(Integer, ForeignKey("dispatch_invoice.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="RESTRICT"), nullable=False)

    invoice = relationship("DispatchInvoice", back_populates="items", passive_deletes=True)
    product = relationship("Product", back_populates="dispatch_items", passive_deletes=True)


# ---------- Database views (read-only) ----------
class TopProductByTurnover(Base):
    """ORM mapping for PostgreSQL view top_products_by_turnover."""

    __tablename__ = "top_products_by_turnover"
    __table_args__ = {"info": {"is_view": True}}

    product_id = Column(Integer, primary_key=True)
    product_name = Column(String(200), nullable=False)
    unit = Column(String(10), nullable=False)
    category_name = Column(String(100))
    supplier_name = Column(String(150))
    total_received_quantity = Column(Numeric(15, 3), nullable=False)
    total_purchase_cost = Column(Numeric(15, 2), nullable=False)
    avg_purchase_price = Column(Numeric(15, 2), nullable=False)
    receipt_count = Column(Integer, nullable=False)
    first_receipt_date = Column(Date)
    last_receipt_date = Column(Date)
    total_sold_quantity = Column(Numeric(15, 3), nullable=False)
    total_sales_revenue = Column(Numeric(15, 2), nullable=False)
    avg_sales_price = Column(Numeric(15, 2), nullable=False)
    sales_count = Column(Integer, nullable=False)
    current_balance = Column(Numeric(15, 3), nullable=False)
    estimated_profit = Column(Numeric(15, 2), nullable=False)
    turnover_percentage = Column(Numeric, nullable=False)
    avg_selling_price = Column(Numeric(15, 2), nullable=False)
    turnover_rank = Column(Integer, nullable=False)
    profit_rank = Column(Integer, nullable=False)


class CategorySummary(Base):
    """ORM mapping for PostgreSQL view category_summary."""

    __tablename__ = "category_summary"
    __table_args__ = {"info": {"is_view": True}}

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(100), nullable=False)
    description = Column(String)
    total_products = Column(Integer, nullable=False)
    suppliers_count = Column(Integer, nullable=False)
    products_in_pieces = Column(Integer, nullable=False)
    products_in_kg = Column(Integer, nullable=False)
    products_in_liters = Column(Integer, nullable=False)
    products_in_meters = Column(Integer, nullable=False)
    products_in_packs = Column(Integer, nullable=False)
    total_purchase_cost = Column(Numeric(15, 2), nullable=False)
    total_sales_revenue = Column(Numeric(15, 2), nullable=False)
    gross_profit = Column(Numeric(15, 2), nullable=False)
    total_received_quantity = Column(Numeric(15, 3), nullable=False)
    total_sold_quantity = Column(Numeric(15, 3), nullable=False)
    current_balance_quantity = Column(Numeric(15, 3), nullable=False)
    avg_purchase_price = Column(Numeric(15, 2), nullable=False)
    avg_sales_price = Column(Numeric(15, 2), nullable=False)
    profit_margin_percent = Column(Numeric, nullable=False)
    receipt_invoices_count = Column(Integer, nullable=False)
    dispatch_invoices_count = Column(Integer, nullable=False)
    first_receipt_date = Column(Date)
    last_receipt_date = Column(Date)
    first_sale_date = Column(Date)
    last_sale_date = Column(Date)
    market_share_percent = Column(Numeric, nullable=False)
