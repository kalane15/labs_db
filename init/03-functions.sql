-- 1. Функция расчёта текущего остатка товара
CREATE OR REPLACE FUNCTION get_product_balance(p_product_id INTEGER)
RETURNS NUMERIC(15,3) AS $$
DECLARE
    v_received NUMERIC(15,3);
    v_dispatched NUMERIC(15,3);
BEGIN
    SELECT COALESCE(SUM(quantity), 0) INTO v_received
    FROM receipt_item
    WHERE product_id = p_product_id;

    SELECT COALESCE(SUM(quantity), 0) INTO v_dispatched
    FROM dispatch_item
    WHERE product_id = p_product_id;

    RETURN v_received - v_dispatched;
END;
$$ LANGUAGE plpgsql;

-- 2. Процедура добавления позиции в приходную накладную с проверками
CREATE OR REPLACE PROCEDURE add_receipt_item(
    p_invoice_id INTEGER,
    p_product_id INTEGER,
    p_quantity NUMERIC,
    p_price NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Проверка существования накладной
    IF NOT EXISTS (SELECT 1 FROM receipt_invoice WHERE id = p_invoice_id) THEN
        RAISE EXCEPTION 'Приходная накладная с ID % не найдена', p_invoice_id
            USING ERRCODE = 'P0001';
    END IF;

    -- Проверка существования товара
    IF NOT EXISTS (SELECT 1 FROM product WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Товар с ID % не найден', p_product_id
            USING ERRCODE = 'P0002';
    END IF;

    -- Бизнес-проверки
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Количество должно быть положительным'
            USING ERRCODE = 'P0003';
    END IF;
    IF p_price < 0 THEN
        RAISE EXCEPTION 'Цена не может быть отрицательной'
            USING ERRCODE = 'P0003';
    END IF;

    INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
    VALUES (p_quantity, p_price, p_invoice_id, p_product_id);

EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE EXCEPTION 'Ошибка внешнего ключа: указан несуществующий товар или накладная'
            USING ERRCODE = SQLSTATE;
    WHEN check_violation THEN
        RAISE EXCEPTION 'Нарушено ограничение CHECK: %', SQLERRM
            USING ERRCODE = SQLSTATE;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Неожиданная ошибка при добавлении приходной позиции: %', SQLERRM
            USING ERRCODE = SQLSTATE;
END;
$$;

-- 3. Процедура добавления позиции в расходную накладную с контролем остатка
CREATE OR REPLACE PROCEDURE add_dispatch_item(
    p_invoice_id INTEGER,
    p_product_id INTEGER,
    p_quantity NUMERIC,
    p_price NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_balance NUMERIC(15,3);
BEGIN
    -- Проверка существования накладной
    IF NOT EXISTS (SELECT 1 FROM dispatch_invoice WHERE id = p_invoice_id) THEN
        RAISE EXCEPTION 'Расходная накладная с ID % не найдена', p_invoice_id
            USING ERRCODE = 'P0001';
    END IF;

    -- Проверка существования товара
    IF NOT EXISTS (SELECT 1 FROM product WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Товар с ID % не найден', p_product_id
            USING ERRCODE = 'P0002';
    END IF;

    -- Бизнес-проверки
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Количество должно быть положительным'
            USING ERRCODE = 'P0003';
    END IF;
    IF p_price < 0 THEN
        RAISE EXCEPTION 'Цена списания не может быть отрицательной'
            USING ERRCODE = 'P0003';
    END IF;

    -- Проверка остатка
    v_balance := get_product_balance(p_product_id);
    IF v_balance < p_quantity THEN
        RAISE EXCEPTION 'Недостаточно товара на складе. Остаток: %, запрошено: %',
            v_balance, p_quantity
            USING ERRCODE = 'P0004';
    END IF;

    INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
    VALUES (p_quantity, p_price, p_invoice_id, p_product_id);

EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE EXCEPTION 'Ошибка внешнего ключа: указан несуществующий товар или накладная';
    WHEN check_violation THEN
        RAISE EXCEPTION 'Нарушено ограничение CHECK: %', SQLERRM;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Неожиданная ошибка при добавлении расходной позиции: %', SQLERRM;
END;
$$;

-- 4. Функция проверки активности поставщика за последние N дней
CREATE OR REPLACE FUNCTION is_supplier_active(
    p_supplier_id INTEGER,
    p_days INTEGER DEFAULT 90
)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM receipt_invoice ri
    WHERE ri.supplier_id = p_supplier_id
      AND ri.date >= CURRENT_DATE - p_days;

    RETURN v_count > 0;
END;
$$ LANGUAGE plpgsql;