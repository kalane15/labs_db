from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, CheckConstraint
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
