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
