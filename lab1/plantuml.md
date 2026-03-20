@startuml
!define table class

entity "Category" as category {
    * id : bigint <<PK>>
    --
    name : varchar(100)
    description : text
}

entity "Supplier" as supplier {
    * id : bigint <<PK>>
    --
    name : varchar(150)
    contact_person : varchar(100)
    phone : varchar(20)
    email : varchar(100)
}

entity "Product" as product {
    * id : bigint <<PK>>
    --
    name : varchar(200)
    unit : varchar(10)
    current_quantity : numeric(15,3)
    average_cost : numeric(15,2)
    --
    category_id : bigint <<FK>>
    supplier_id : bigint <<FK>>
}

entity "ReceiptInvoice" as receipt_invoice {
    * id : bigint <<PK>>
    --
    date : date
    total_amount : numeric(15,2)
    --
    supplier_id : bigint <<FK>>
}

entity "ReceiptItem" as receipt_item {
    * id : bigint <<PK>>
    --
    quantity : numeric(15,3)
    purchase_price : numeric(15,2)
    --
    receipt_invoice_id : bigint <<FK>>
    product_id : bigint <<FK>>
}

entity "DispatchInvoice" as dispatch_invoice {
    * id : bigint <<PK>>
    --
    date : date
    destination : varchar(200)
    total_amount : numeric(15,2)
}

entity "DispatchItem" as dispatch_item {
    * id : bigint <<PK>>
    --
    quantity : numeric(15,3)
    write_off_price : numeric(15,2)
    --
    dispatch_invoice_id : bigint <<FK>>
    product_id : bigint <<FK>>
}

' Relationships
category ||--|{ product : "содержит"
supplier ||--|{ product : "поставляет"
supplier ||--o{ receipt_invoice : "оформляет"
receipt_invoice ||--|{ receipt_item : "состоит из"
product ||--o{ receipt_item : "указан в"
dispatch_invoice ||--|{ dispatch_item : "состоит из"
product ||--o{ dispatch_item : "списывается в"
@enduml