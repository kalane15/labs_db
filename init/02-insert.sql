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
SELECT 
    CONCAT(
        (ARRAY['Смартфон', 'Ноутбук', 'Планшет', 'Наушники', 'Телевизор', 
                'Холодильник', 'Микроволновка', 'Пылесос', 'Чайник', 'Кофеварка',
                'Молоко', 'Хлеб', 'Сыр', 'Колбаса', 'Печенье',
                'Вода', 'Сок', 'Кола', 'Чай', 'Кофе'])[floor(random() * 20 + 1)],
        ' ',
        floor(random() * 1000)::int
    ) as name,
    (ARRAY['шт', 'кг', 'л', 'м', 'уп'])[floor(random() * 5 + 1)] as unit,
    (floor(random() * 8 + 1))::int as category_id,
    (floor(random() * 10 + 1))::int as supplier_id
FROM generate_series(1, 100);

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