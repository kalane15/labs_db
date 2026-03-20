-- Таблица категорий товаров
CREATE TABLE category (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Таблица поставщиков
CREATE TABLE supplier (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE
);

-- Таблица товаров
CREATE TABLE product (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(10) NOT NULL DEFAULT 'шт',
    category_id BIGINT NOT NULL,
    supplier_id BIGINT NOT NULL,
    
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT,
    CONSTRAINT fk_product_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT
);

-- =====================================================
-- 2. Приходные документы
-- =====================================================

-- Таблица приходных накладных
CREATE TABLE receipt_invoice (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    supplier_id BIGINT NOT NULL,
    
    CONSTRAINT fk_receipt_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT
);

-- Таблица позиций приходной накладной
CREATE TABLE receipt_item (
    id BIGSERIAL PRIMARY KEY,
    quantity NUMERIC(15, 3) NOT NULL CHECK (quantity > 0),
    purchase_price NUMERIC(15, 2) NOT NULL CHECK (purchase_price >= 0),
    receipt_invoice_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    
    CONSTRAINT fk_receipt_item_invoice FOREIGN KEY (receipt_invoice_id) REFERENCES receipt_invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_receipt_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT
);

-- =====================================================
-- 3. Расходные документы
-- =====================================================

-- Таблица расходных накладных
CREATE TABLE dispatch_invoice (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    destination VARCHAR(200) NOT NULL
);

-- Таблица позиций расходной накладной
CREATE TABLE dispatch_item (
    id BIGSERIAL PRIMARY KEY,
    quantity NUMERIC(15, 3) NOT NULL CHECK (quantity > 0),
    write_off_price NUMERIC(15, 2) NOT NULL CHECK (write_off_price >= 0),
    dispatch_invoice_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    
    CONSTRAINT fk_dispatch_item_invoice FOREIGN KEY (dispatch_invoice_id) REFERENCES dispatch_invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_dispatch_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT
);