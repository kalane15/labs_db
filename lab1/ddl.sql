-- Таблица категорий товаров
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
    -- add created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- add is_active BOOLEAN DEFAULT TRUE
);

-- Таблица поставщиков
CREATE TABLE supplier (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE
    
    CONSTRAINT chk_supplier_phone CHECK (phone ~ '^[0-9+\-() ]+$'),
    CONSTRAINT chk_supplier_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_supplier_contact CHECK ((contact_person IS NOT NULL) OR (phone IS NOT NULL) OR (email IS NOT NULL)),
);

-- Таблица товаров
CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(10) NOT NULL DEFAULT 'шт',
    category_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    
    CONSTRAINT chk_product_unit CHECK (unit IN ('шт', 'кг', 'л', 'м', 'уп')),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT,
    CONSTRAINT fk_product_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT
);

-- =====================================================
-- 2. Приходные документы
-- =====================================================

-- Таблица приходных накладных
CREATE TABLE receipt_invoice (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    supplier_id INTEGER NOT NULL,
    
    CONSTRAINT fk_receipt_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT
);

-- Таблица позиций приходной накладной
CREATE TABLE receipt_item (
    id SERIAL PRIMARY KEY,
    quantity NUMERIC(15, 3) NOT NULL CHECK (quantity > 0),
    purchase_price NUMERIC(15, 2) NOT NULL CHECK (purchase_price >= 0),
    receipt_invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    
    CONSTRAINT fk_receipt_item_invoice FOREIGN KEY (receipt_invoice_id) REFERENCES receipt_invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_receipt_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,
    CONSTRAINT chk_receipt_item_total CHECK (quantity * purchase_price >= 0)
);

-- =====================================================
-- 3. Расходные документы
-- =====================================================

-- Таблица расходных накладных
CREATE TABLE dispatch_invoice (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    destination VARCHAR(200) NOT NULL
    CONSTRAINT chk_dispatch_date CHECK (date <= CURRENT_DATE),
);

-- Таблица позиций расходной накладной
CREATE TABLE dispatch_item (
    id SERIAL PRIMARY KEY,
    quantity NUMERIC(15, 3) NOT NULL CHECK (quantity > 0),
    write_off_price NUMERIC(15, 2) NOT NULL CHECK (write_off_price >= 0),
    dispatch_invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    
    CONSTRAINT fk_dispatch_item_invoice FOREIGN KEY (dispatch_invoice_id) REFERENCES dispatch_invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_dispatch_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT
    CONSTRAINT chk_dispatch_item_total CHECK (quantity * write_off_price >= 0)
);