from fastapi import FastAPI
import crud.crud_products
import crud.crud_suppliers
import crud.crud_categories
from database import engine
import views
import functions
import reports
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warehouse API", version="1.0")

app.include_router(crud.crud_categories.router)
app.include_router(crud.crud_suppliers.router)
app.include_router(crud.crud_products.router)
app.include_router(views.router)
app.include_router(functions.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"message": "Warehouse API is running"}
