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
