-- 1. ПРОВЕРКА ФУНКЦИИ ОСТАТКА (ИЗНАЧАЛЬНО ДОЛЖЕН БЫТЬ > 0 БЛАГОДАРЯ 02-insert.sql)
SELECT 
    p.id,
    p.name,
    get_product_balance(p.id) AS current_balance
FROM product p
ORDER BY p.id
LIMIT 5;

-- 2. УСПЕШНОЕ ДОБАВЛЕНИЕ ПРИХОДНОЙ ПОЗИЦИИ
-- Предварительно посмотрим последнюю запись в receipt_item
SELECT * FROM receipt_item ORDER BY id DESC LIMIT 1;

-- Вызов процедуры для товара id=1, накладная id=1 (существует), количество 10, цена 1500
CALL add_receipt_item(
    p_invoice_id := 1,
    p_product_id := 1,
    p_quantity := 10.5,
    p_price := 1500.00
);

-- Проверим, что запись добавилась
SELECT * FROM receipt_item ORDER BY id DESC LIMIT 1;

-- 3. ПРОВЕРКА ТРИГГЕРА АУДИТА ПОСЛЕ ДОБАВЛЕНИЯ
SELECT * FROM audit_log WHERE table_name = 'receipt_item' ORDER BY changed_at DESC LIMIT 1;

-- 4. УСПЕШНОЕ ДОБАВЛЕНИЕ РАСХОДНОЙ ПОЗИЦИИ (с контролем остатка)
-- Проверим текущий остаток товара 1
SELECT get_product_balance(1) AS balance_before_dispatch;

-- Вызов процедуры (спишем 5 единиц)
CALL add_dispatch_item(
    p_invoice_id := 1,    -- расходная накладная id=1 (существует из 02-insert.sql)
    p_product_id := 1,
    p_quantity := 5.0,
    p_price := 1600.00
);

-- Проверим остаток после списания
SELECT get_product_balance(1) AS balance_after_dispatch;

-- Последняя добавленная расходная позиция
SELECT * FROM dispatch_item ORDER BY id DESC LIMIT 1;

-- 5. ПРОВЕРКА ТРИГГЕРА АУДИТА ДЛЯ РАСХОДНЫХ ПОЗИЦИЙ
SELECT * FROM audit_log WHERE table_name = 'dispatch_item' ORDER BY changed_at DESC LIMIT 1;

-- 6. ОШИБКА: ПОПЫТКА ДОБАВИТЬ НЕСУЩЕСТВУЮЩИЙ ТОВАР

CALL add_receipt_item(1, 9999, 10, 100);
-- Ожидаемое сообщение: "Товар с ID 9999 не найден"

-- 7. ОШИБКА: НЕДОСТАТОЧНО ТОВАРА НА СКЛАДЕ
-- Узнаем текущий остаток
SELECT get_product_balance(1) AS current_balance_for_error;
-- Попробуем списать больше, чем есть (например, 1000 единиц)
-- CALL add_dispatch_item(1, 1, 1000.0, 1000);
-- Ожидаемое сообщение: "Недостаточно товара на складе. Остаток: ..., запрошено: 1000"

-- 8. ПРОВЕРКА ФУНКЦИИ АКТИВНОСТИ ПОСТАВЩИКА
SELECT 
    s.id,
    s.name,
    is_supplier_active(s.id) AS active_last_90_days,
    is_supplier_active(s.id, 0) AS active_today
FROM supplier s
LIMIT 5;

-- 9. ОБНОВЛЕНИЕ ДАННЫХ И АУДИТ
-- Обновим количество в последней добавленной приходной позиции
UPDATE receipt_item 
SET quantity = quantity + 2 
WHERE id = (SELECT MAX(id) FROM receipt_item);

-- Проверим запись аудита для UPDATE
SELECT * FROM audit_log 
WHERE table_name = 'receipt_item' AND operation = 'UPDATE' 
ORDER BY changed_at DESC LIMIT 1;

-- 11. УДАЛЕНИЕ ДАННЫХ И АУДИТ
-- Удалим только что обновлённую запись
DELETE FROM receipt_item WHERE id = (SELECT MAX(id) FROM receipt_item);

-- Проверим аудит для DELETE
SELECT * FROM audit_log 
WHERE table_name = 'receipt_item' AND operation = 'DELETE' 
ORDER BY changed_at DESC LIMIT 1;