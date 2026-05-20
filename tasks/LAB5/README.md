# Отчёт по лабораторной работе №5  
## Исследование транзакций в PostgreSQL

### Цель работы
Исследовать механизмы транзакций в PostgreSQL: фиксацию изменений, откат, точки сохранения, блокировки, аномалии параллельного выполнения и уровни изоляции.

### Используемая база данных
База данных складского учёта, созданная в лабораторной работе №1. Основные таблицы:
- `category` – категории товаров
- `supplier` – поставщики
- `product` – товары (связь с category и supplier)
- `receipt_invoice` / `receipt_item` – приходные накладные и их позиции
- `dispatch_invoice` / `dispatch_item` – расходные накладные и их позиции

---

## Бизнес-сценарии

### Сценарий 1: Приёмка товара от поставщика
**Изменяемые таблицы:** `receipt_invoice` (заголовок накладной) и `receipt_item` (позиции).

#### 1.1 Успешная транзакция (COMMIT)
`
BEGIN;
INSERT INTO receipt_invoice (date, supplier_id)
VALUES (CURRENT_DATE, 1);
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (10.000, 150.00, currval('receipt_invoice_id_seq'), 5),
       (5.000, 200.00, currval('receipt_invoice_id_seq'), 8);
COMMIT;
SELECT * FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq');
SELECT * FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq');
`
**Результат:** Накладная и две позиции добавлены. `currval` обеспечивает использование сгенерированного идентификатора без хардкода.

#### 1.2 Ошибка и полный откат
Моделируется ошибка: попытка вставить позицию с `quantity = 0`, что нарушает CHECK-ограничение `quantity > 0`.

```
BEGIN;

INSERT INTO receipt_invoice (date, supplier_id) VALUES (CURRENT_DATE, 1);

-- Ошибочная вставка
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (0, 150.00, currval('receipt_invoice_id_seq'), 5);

ROLLBACK;

-- Проверка отсутствия данных
SELECT EXISTS (SELECT 1 FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq')));
SELECT EXISTS (SELECT 1 FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq')));
```
**Результат:** Транзакция переходит в состояние `aborted`, выполнен `ROLLBACK`, новые записи не сохранены.

#### 1.3 Частичный откат через SAVEPOINT
Добавляются три позиции; третья – ошибочная. Откат только до savepoint `before_third` сохраняет первые две позиции.

```
BEGIN;

INSERT INTO receipt_invoice (date, supplier_id) VALUES (CURRENT_DATE, 1);

INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (20.000, 120.00, currval('receipt_invoice_id_seq'), 5);

SAVEPOINT before_second;

INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (3.000, 300.00, currval('receipt_invoice_id_seq'), 8);

SAVEPOINT before_third;

-- Ошибочная вставка (отрицательное количество)
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (-5.000, 100.00, currval('receipt_invoice_id_seq'), 10);

ROLLBACK TO SAVEPOINT before_third;

COMMIT;

SELECT * FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq') ORDER BY id;
```
**Результат:** Накладная сохранена с двумя корректными позициями; третья позиция не добавлена.

---

### Сценарий 2: Перенос товара в новую категорию
**Изменяемые таблицы:** `category` (создание новой категории) и `product` (обновление `category_id`).

#### 2.1 Успешная транзакция (COMMIT)
Используется CTE с `RETURNING`, чтобы передать сгенерированный `id` новой категории в `UPDATE`.

`
BEGIN;
WITH new_category AS (
    INSERT INTO category (name, description)
    VALUES ('Premium', 'Категория для премиум-товаров')
    RETURNING id
)
UPDATE product
SET category_id = (SELECT id FROM new_category)
WHERE id = 3;
COMMIT;
SELECT p.id, p.name, c.name
FROM product p
JOIN category c ON p.category_id = c.id
WHERE p.id = 3;
`
**Результат:** Категория создана, товар с `id=3` перенесён в неё.

#### 2.2 Ошибка и полный откат
Попытка вставить категорию с уже существующим именем нарушает уникальность.

```
BEGIN;

INSERT INTO category (name, description)
VALUES ('Старая категория', 'Попытка создать дубликат');  -- ошибка UNIQUE

UPDATE product SET category_id = 9;  -- не выполнится

ROLLBACK;

SELECT * FROM product WHERE category_id = 9;  -- пусто
```
**Результат:** Транзакция откачена, изменения отсутствуют.

#### 2.3 Частичный откат через SAVEPOINT
Обновляются товары из категории 1 в категорию 8, затем делается savepoint. Попытка удалить категорию 1 откатывается, а обновление товаров фиксируется.

`
BEGIN;
WITH limited_rows AS (
    SELECT id FROM product WHERE category_id = 1
)
UPDATE product
SET category_id = 8
WHERE id IN (SELECT id FROM limited_rows);
SAVEPOINT after_update;
DELETE FROM category WHERE id = 1;  -- может нарушить внешний ключ
ROLLBACK TO SAVEPOINT after_update;
COMMIT;
SELECT * FROM product WHERE category_id = 1;
SELECT * FROM category WHERE id = 1;
`
**Результат:** Товары переведены в категорию 8, категория 1 не удалена.

---

### Сценарий 3: Оформление расходной накладной и обновление контакта поставщика
**Изменяемые таблицы:** `dispatch_invoice`, `dispatch_item`, `supplier`.

#### 3.1 Успешная транзакция (COMMIT)
```
BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ООО "Розничный магазин"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (10.000, 150.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier
SET contact_person = 'Смирнова А.В.'
WHERE id = (SELECT supplier_id FROM product WHERE id = 5);

COMMIT;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');
SELECT * FROM dispatch_item WHERE dispatch_invoice_id = currval('dispatch_invoice_id_seq');
SELECT id, name, contact_person FROM supplier WHERE id = (SELECT supplier_id FROM product WHERE id = 5);
```
**Результат:** Накладная создана, позиция добавлена, контакт поставщика обновлён.

#### 3.2 Ошибка и полный откат
Отрицательная цена списания (`write_off_price = -100`) нарушает CHECK-ограничение.

```
BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ИП "Покупатель"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (5.000, -100.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier SET contact_person = 'Новый контакт' WHERE id = (SELECT supplier_id FROM product WHERE id = 5);

ROLLBACK;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');  -- нет строк
SELECT contact_person FROM supplier WHERE id = (SELECT supplier_id FROM product WHERE id = 5);  -- не изменился
```
**Результат:** Ошибка в `dispatch_item` вызывает откат всей транзакции.

#### 3.3 Частичный откат через SAVEPOINT
Первая позиция и обновление поставщика сохраняются, вторая ошибочная позиция откатывается.

```
BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ООО "Оптовик"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (20.000, 120.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier SET contact_person = 'Петров П.П.' WHERE id = 5;

SAVEPOINT after_good;

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (0, 110.00, currval('dispatch_invoice_id_seq'), 8);  -- quantity = 0 – ошибка

ROLLBACK TO SAVEPOINT after_good;

COMMIT;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');
SELECT * FROM dispatch_item WHERE dispatch_invoice_id = currval('dispatch_invoice_id_seq');
SELECT contact_person FROM supplier WHERE id = 5;
```
**Результат:** Накладная, первая позиция и обновлённый контакт сохранены; вторая позиция не добавлена.

---

## Дополнительное задание: исследование конкурентного выполнения транзакций (сценарий 2)

### Подготовка данных

```
INSERT INTO category (name, description) VALUES ('Кат A', 'Первая') ON CONFLICT DO NOTHING;
INSERT INTO category (name, description) VALUES ('Кат B', 'Вторая') ON CONFLICT DO NOTHING;
INSERT INTO category (id, name) VALUES (10, 'Премиум') ON CONFLICT (id) DO NOTHING;

-- Товар для блокировки и lost update
INSERT INTO product (name, unit, category_id, supplier_id)
VALUES ('Конкурентный товар', 'шт', 
        (SELECT id FROM category WHERE name = 'Кат A'),
        (SELECT id FROM supplier LIMIT 1))
RETURNING id;  -- допустим, вернулся id = 123

-- Товары для write skew
INSERT INTO product (id, name, unit, category_id, supplier_id) VALUES
(1, 'Товар 1', 'шт', 10, (SELECT id FROM supplier LIMIT 1)),
(2, 'Товар 2', 'шт', 10, (SELECT id FROM supplier LIMIT 1)),
(101, 'Переносимый A', 'шт', 1, (SELECT id FROM supplier LIMIT 1)),
(102, 'Переносимый B', 'шт', 1, (SELECT id FROM supplier LIMIT 1))
ON CONFLICT (id) DO NOTHING;
```

### 1. Демонстрация блокировки строки

**Сессия 1** (начинает, но не фиксирует):
```
BEGIN;
UPDATE product SET category_id = (SELECT id FROM category WHERE name = 'Кат B')
WHERE id = 123;
```

**Сессия 2** (пытается обновить ту же строку):
```
BEGIN;
UPDATE product SET category_id = (SELECT id FROM category WHERE name = 'Кат A')
WHERE id = 123;
```
Вторая сессия зависает в ожидании – это блокировка на уровне строки (ROW EXCLUSIVE). После `COMMIT` в первой сессии вторая получает блокировку и выполняет обновление.

### 2. Потерянное обновление (Lost Update)

**Исходное значение:** `category_id = 1` для товара с `id = 1`.

#### На уровне READ COMMITTED (по умолчанию)

**Сессия 1:**
```
BEGIN;
SELECT category_id FROM product WHERE id = 1;   -- результат 1
```

**Сессия 2:**
```
BEGIN;
SELECT category_id FROM product WHERE id = 1;   -- тоже 1
UPDATE product SET category_id = category_id + 1 WHERE id = 1;
COMMIT;   -- теперь в базе 2
```

**Сессия 1 (после COMMIT сессии 2):**
```
UPDATE product SET category_id = category_id + 1 WHERE id = 1; 
COMMIT;
SELECT category_id FROM product WHERE id = 1;   -- результат 2 (должно быть 3)
```
**Аномалия:** Одно увеличение потеряно, потому что первая транзакция использовала старое прочитанное значение вместо актуального.

#### На уровне REPEATABLE READ

Обе сессии начинаются с `BEGIN ISOLATION LEVEL REPEATABLE READ;`. После выполнения тех же шагов, при `COMMIT` в сессии 1 возникает ошибка:
```
ERROR: could not serialize access due to concurrent update
```
Транзакция сессии 1 откатывается, потеря обновления предотвращена. При повторном запуске она увидит уже новое значение и корректно увеличит.

### 3. Write skew – разница между REPEATABLE READ и SERIALIZABLE

**Бизнес-правило:** В категории 10 (Премиум) не может быть более 3 товаров. Исходно в ней 2 товара (id=1 и id=2). Две параллельные транзакции пытаются добавить два разных товара (id=101 и id=102).

#### На уровне REPEATABLE READ

```
-- Сессия 1
BEGIN ISOLATION LEVEL REPEATABLE READ;
DO $$
DECLARE current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;  -- 2
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 101;
    END IF;
END $$;
COMMIT;

-- Сессия 2 (параллельно)
BEGIN ISOLATION LEVEL REPEATABLE READ;
DO $$
DECLARE current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count FROM product WHERE category_id = 10;  -- тоже 2 (снимок)
    IF current_count < 3 THEN
        UPDATE product SET category_id = 10 WHERE id = 102;
    END IF;
END $$;
COMMIT;
```
**Результат:** Обе транзакции успешны. В категории 10 теперь 4 товара (1, 2, 101, 102) – бизнес-правило нарушено. Это **write skew**: транзакции читают условие, а затем обновляют разные строки; `REPEATABLE READ` не отслеживает зависимости чтения.

#### На уровне SERIALIZABLE

Те же транзакции, но с `BEGIN ISOLATION LEVEL SERIALIZABLE;`. При попытке `COMMIT` одной из них (второй) возникает ошибка:
```
ERROR: could not serialize access due to read/write dependencies among transactions
```
PostgreSQL обнаруживает, что прочитанное условие `COUNT(*)` стало неверным после фиксации другой транзакции, и откатывает одну из них. Категория 10 остаётся с 3 товарами – правило соблюдено.

### Итог по уровням изоляции

| Аномалия / Поведение | READ COMMITTED | REPEATABLE READ | SERIALIZABLE |
|---------------------|----------------|------------------|---------------|
| Lost update (чтение+обновление) | Возможна | Ошибка при коммите | Ошибка при коммите |
| Write skew | Возможна | Возможна | Ошибка, предотвращена |
| Блокировка строки | Да (при UPDATE) | Да | Да |
| Снимок данных | Для каждого оператора | Один на транзакцию | Один + отслеживание зависимостей |
