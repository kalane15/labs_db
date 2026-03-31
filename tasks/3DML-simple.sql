-- =====================================================
-- 1. ВСТАВКА НОВЫХ ЗАПИСЕЙ (INSERT)
-- =====================================================

-- 1.1 Добавление новой категории товаров
INSERT INTO category (name, description) 
VALUES ('Инструменты', 'Ручной и электроинструмент');

-- 1.2 Добавление нового поставщика
INSERT INTO supplier (name, contact_person, phone, email) 
VALUES (
    'ООО "Инструмент-Сервис"',
    'Сергеев Сергей Сергеевич',
    '+7-495-987-65-43',
    'info@instrument-service.ru'
);

-- 1.3 Добавление нового товара с проверкой существования категории и поставщика
INSERT INTO product (name, unit, category_id, supplier_id)
SELECT 
    'Дрель аккумуляторная',
    'шт',
    c.id,
    s.id
FROM category c, supplier s
WHERE c.name = 'Инструменты' 
  AND s.name = 'ООО "Инструмент-Сервис"';

-- 1.4 Создание приходной накладной с автоматической датой
INSERT INTO receipt_invoice (supplier_id)
SELECT id FROM supplier WHERE name = 'ООО "Инструмент-Сервис"';

-- 1.5 Добавление позиций в приходную накладную
WITH new_invoice AS (
    SELECT id FROM receipt_invoice 
    WHERE supplier_id = (SELECT id FROM supplier WHERE name = 'ООО "Инструмент-Сервис"')
    ORDER BY id DESC LIMIT 1
)
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
SELECT 
    10.000 as quantity,
    4500.00 as purchase_price,
    new_invoice.id as receipt_invoice_id,
    p.id as product_id
FROM product p, new_invoice
WHERE p.name LIKE 'Дрель%';

-- 1.6 Создание расходной накладной для отгрузки товара
INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'Магазин "СтройМаркет" на ул. Ленина');

-- 1.7 Добавление позиций в расходную накладную
WITH new_dispatch AS (
    SELECT id FROM dispatch_invoice 
    WHERE destination = 'Магазин "СтройМаркет" на ул. Ленина'
    ORDER BY id DESC LIMIT 1
)
INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
SELECT 
    5.000 as quantity,
    p.avg_price as write_off_price,
    new_dispatch.id as dispatch_invoice_id,
    p.product_id as product_id
FROM (
    SELECT 
        product_id,
        AVG(purchase_price) as avg_price
    FROM receipt_item
    GROUP BY product_id
) p, new_dispatch
WHERE p.product_id = (SELECT id FROM product WHERE name LIKE 'Дрель%' LIMIT 1);

-- =====================================================
-- 2. ОБНОВЛЕНИЕ СУЩЕСТВУЮЩИХ ЗАПИСЕЙ (UPDATE)
-- =====================================================

-- 2.1 Обновление контактной информации поставщика
UPDATE supplier 
SET 
    contact_person = 'Иванов Иван Иванович',
    phone = '+7-495-123-45-67',
    email = 'ivanov@tehno.ru'
WHERE name = 'Поставщик №1';

-- 2.2 Изменение цены товара во всех приходных накладных (индексация на 10%)
UPDATE receipt_item 
SET purchase_price = purchase_price * 1.10
WHERE product_id IN (
    SELECT id FROM product 
    WHERE category_id = (SELECT id FROM category WHERE name = 'Электроника')
);

-- 2.3 Корректировка количества товара в расходной накладной (возврат части товара)
UPDATE dispatch_item 
SET quantity = quantity - 2.000
WHERE dispatch_invoice_id = (
    SELECT id FROM dispatch_invoice 
    WHERE destination LIKE '%СтройМаркет%' 
    ORDER BY date DESC LIMIT 1
)
AND product_id = (SELECT id FROM product WHERE name LIKE 'Дрель%');

-- 2.4 Массовое обновление единиц измерения для товаров определенной категории
UPDATE product 
SET unit = 'уп'
WHERE category_id = (SELECT id FROM category WHERE name = 'Канцелярия')
AND unit = 'шт';

-- =====================================================
-- 2. УДАЛЕНИЕ СУЩЕСТВУЮЩИХ ЗАПИСЕЙ (DELETE)
-- =====================================================

-- 3.1 Удаление категории без товаров
DELETE FROM category 
WHERE id NOT IN (SELECT DISTINCT category_id FROM product);

-- 3.2 Удаление поставщиков, которые не поставляли товары (нет приходных накладных)
DELETE FROM supplier 
WHERE id NOT IN (SELECT DISTINCT supplier_id FROM receipt_invoice);

-- 3.3 Удаление пустых расходных накладных (без позиций)
DELETE FROM dispatch_invoice 
WHERE id NOT IN (SELECT DISTINCT dispatch_invoice_id FROM dispatch_item);

-- 3.4 Удаление устаревших чеков (приходных накладных) вместе с их позициями (CASCADE)
DELETE FROM receipt_invoice 
WHERE date < CURRENT_DATE - INTERVAL '2 years'
  AND id NOT IN (
      SELECT receipt_invoice_id 
      FROM receipt_item ri
      JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
      WHERE ri2.date >= CURRENT_DATE - INTERVAL '1 year'
  );

-- 3.5 Удаление всех документов за определенный месяц (с каскадом через внешние ключи)
DELETE FROM receipt_invoice 
WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month')
  AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month');