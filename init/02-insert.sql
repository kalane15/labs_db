-- Очистка таблиц в правильном порядке (если нужно)
TRUNCATE TABLE dispatch_item CASCADE;
TRUNCATE TABLE dispatch_invoice CASCADE;
TRUNCATE TABLE receipt_item CASCADE;
TRUNCATE TABLE receipt_invoice CASCADE;
TRUNCATE TABLE product CASCADE;
TRUNCATE TABLE supplier CASCADE;
TRUNCATE TABLE category CASCADE;

-- 1. Категории (8 штук)
INSERT INTO category (name, description) VALUES
('Электроника', 'Телефоны, ноутбуки, планшеты'),
('Бытовая техника', 'Холодильники, стиральные машины'),
('Продукты питания', 'Молочные продукты, бакалея'),
('Напитки', 'Вода, соки, газировка'),
('Канцелярия', 'Ручки, бумага, папки'),
('Стройматериалы', 'Краски, инструменты'),
('Мебель', 'Столы, стулья, шкафы'),
('Одежда', 'Мужская, женская, детская');

-- 2. Поставщики (10 штук)
INSERT INTO supplier (name, contact_person, phone, email) 
SELECT 
    CONCAT('Поставщик №', generate_series) as name,
    CONCAT('Контактное лицо ', generate_series) as contact_person,
    CONCAT('+7', LPAD((random() * 9999999999)::bigint::text, 10, '0')) as phone,
    CONCAT('supplier', generate_series, '@example.com') as email
FROM generate_series(1, 10);

-- 3. Товары (100 штук)
INSERT INTO product (name, unit, category_id, supplier_id)
WITH product_templates AS (
    SELECT 
        unnest(ARRAY[
            'Смартфон', 'Ноутбук', 'Планшет', 'Наушники', 'Телевизор',
            'Холодильник', 'Микроволновка', 'Пылесос', 'Чайник', 'Кофеварка',
            'Молоко', 'Хлеб', 'Сыр', 'Колбаса', 'Печенье',
            'Вода', 'Сок', 'Кола', 'Чай', 'Кофе'
        ]) as name_base,
        unnest(ARRAY[
            'шт', 'шт', 'шт', 'шт', 'шт',
            'шт', 'шт', 'шт', 'шт', 'шт',
            'л', 'шт', 'кг', 'кг', 'кг',
            'л', 'л', 'л', 'уп', 'уп'
        ]) as unit_base,
        unnest(ARRAY[
            1, 1, 1, 1, 1,
            2, 2, 2, 2, 2,
            3, 3, 3, 3, 3,
            4, 4, 4, 4, 4
        ]) as category_base
)
SELECT 
    CONCAT(name_base, ' ', floor(random() * 1000)::int) as name,
    unit_base as unit,
    category_base as category_id,
    (floor(random() * 10 + 1))::int as supplier_id
FROM product_templates
CROSS JOIN generate_series(1, 5);

-- 4. Приходные накладные (50 штук)
INSERT INTO receipt_invoice (date, supplier_id)
SELECT 
    CURRENT_DATE - (random() * 365)::int * interval '1 day' as date,
    (floor(random() * 10 + 1))::int as supplier_id
FROM generate_series(1, 50);

-- 5. Позиции приходных накладных
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
SELECT 
    (random() * 100 + 1)::numeric(15,3) as quantity,
    (random() * 1000 + 10)::numeric(15,2) as purchase_price,
    (floor(random() * 50 + 1))::int as receipt_invoice_id,
    (floor(random() * 100 + 1))::int as product_id
FROM generate_series(1, 500);

-- 6. Расходные накладные
INSERT INTO dispatch_invoice (date, destination)
SELECT 
    CURRENT_DATE - (random() * 180)::int * interval '1 day' as date,
    CONCAT('Пункт назначения ', floor(random() * 20 + 1)::int) as destination
FROM generate_series(1, 30);

-- 7. Позиции расходных накладных (300 штук)
INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
SELECT 
    (random() * 50 + 1)::numeric(15,3) as quantity,
    (random() * 1000 + 10)::numeric(15,2) as write_off_price,
    (floor(random() * 30 + 1))::int as dispatch_invoice_id,
    (floor(random() * 100 + 1))::int as product_id
FROM generate_series(1, 300);