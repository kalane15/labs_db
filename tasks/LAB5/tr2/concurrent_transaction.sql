INSERT INTO category (name, description) VALUES ('Кат A', 'Первая') ON CONFLICT DO NOTHING;
INSERT INTO category (name, description) VALUES ('Кат B', 'Вторая') ON CONFLICT DO NOTHING;

INSERT INTO product (name, unit, category_id, supplier_id)
VALUES ('Конкурентный товар', 'шт', 
        (SELECT id FROM category WHERE name = 'Кат A'),
        (SELECT id FROM supplier LIMIT 1))
RETURNING id;

-- 1. Демонстрация блокировки
-- Сессия 1
BEGIN;
UPDATE product SET category_id = (SELECT id FROM category WHERE name = 'Кат B')
WHERE id = 123;

-- Сессия 2
BEGIN;
UPDATE product SET category_id = (SELECT id FROM category WHERE name = 'Кат A')
WHERE id = 123;
COMMIT;


-- 2. Аномалия потерянного обновления (Lost Update). Разница между READ COMMITED и REPEATABLE READ
SELECT id, category_id FROM product WHERE id = 1;
--READ COMMITED
--сессия 1
BEGIN;
SELECT category_id FROM product WHERE id = 1;

--сессия 2
BEGIN;
SELECT category_id FROM product WHERE id = 1;
UPDATE product SET category_id = category_id + 1 WHERE id = 1;
COMMIT;

--сессия 1
UPDATE product SET category_id = category_id + 1 WHERE id = 1;
COMMIT;

SELECT id, category_id FROM product WHERE id = 1;

--REPEATABLE READ
--сессия 1
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT category_id FROM product WHERE id = 1;

--сессия 2
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT category_id FROM product WHERE id = 1;
UPDATE product SET category_id = category_id + 1 WHERE id = 1;
COMMIT;

--сессия 1
UPDATE product SET category_id = category_id + 1 WHERE id = 1;
COMMIT;

SELECT id, category_id FROM product WHERE id = 1;

--3. Разница между REPEATABLE READ и SERIALIZABLE
BEGIN ISOLATION LEVEL REPEATABLE READ;
DO $$
DECLARE
    current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;
    
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 1;
    END IF;
END $$;
COMMIT;

BEGIN ISOLATION LEVEL REPEATABLE READ;
DO $$
DECLARE
    current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;
    
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 2;
    END IF;
END $$;
COMMIT;

BEGIN ISOLATION LEVEL SERIALIZABLE;
DO $$
DECLARE
    current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;
    
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 1;
    END IF;
END $$;
COMMIT;

BEGIN ISOLATION LEVEL SERIALIZABLE;
DO $$
DECLARE
    current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;
    
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 2;
    END IF;
END $$;
COMMIT;