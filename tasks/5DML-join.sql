-- =====================================================
-- 1. ТОВАРЫ С ИНФОРМАЦИЕЙ О КАТЕГОРИЯХ И ПОСТАВЩИКАХ
-- =====================================================
-- Выбор всех товаров с их категориями и поставщиками
SELECT 
    p.name as product_name,
    p.unit,
    p.id as product_id,
    c.name as category_name,
    s.name as supplier_name,
    s.contact_person,
    s.phone
FROM product p
JOIN category c ON p.category_id = c.id
JOIN supplier s ON p.supplier_id = s.id
ORDER BY c.name, p.name
LIMIT 20;

-- =====================================================
-- 2. ПРИХОД ТОВАРОВ
-- =====================================================
-- Товары и информация об их приходе
SELECT 
    p.id,
    p.name as product_name,
    p.unit,
    c.name as category_name,
    s.name as supplier_name,
    COUNT(ri.id) as receipt_count,
    COALESCE(SUM(ri.quantity), 0) as total_received
FROM product p
JOIN category c ON p.category_id = c.id
JOIN supplier s ON p.supplier_id = s.id
LEFT JOIN receipt_item ri ON p.id = ri.product_id
GROUP BY p.id, p.name, p.unit, c.name, s.name
HAVING COUNT(ri.id) = 0
ORDER BY p.name;

-- =====================================================
-- 3. ПОСТАВЩИКИ И ИХ ПОСТАВКИ
-- =====================================================
-- Показывает всех поставщиков и суммы их поставок (включая тех, кто еще не поставлял)
SELECT 
    s.id,
    s.name as supplier_name,
    s.contact_person,
    s.phone,
    COUNT(DISTINCT ri2.id) as delivery_count,
    COUNT(DISTINCT p.id) as products_supplied,
    COALESCE(SUM(ri.quantity), 0) as total_quantity,
    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_amount,
    COALESCE(AVG(ri.purchase_price), 0)::numeric(15,2) as avg_price
FROM supplier s
LEFT JOIN product p ON s.id = p.supplier_id
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
GROUP BY s.id, s.name, s.contact_person, s.phone
ORDER BY total_amount DESC;

-- =====================================================
-- 4. СВОДКА ПРИХОДА И РАСХОДА ПО ТОВАРАМ
-- =====================================================
-- Сравнивает поступление и отгрузку каждого товара (включая товары без движений)
SELECT 
    COALESCE(p.id, ri.product_id, di.product_id) as product_id,
    COALESCE(p.name, 'Товар удален') as product_name,
    COALESCE(c.name, 'Без категории') as category,
    COALESCE(SUM(ri.quantity), 0) as received_quantity,
    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as received_value,
    COALESCE(SUM(di.quantity), 0) as sold_quantity,
    COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as sold_value,
    COALESCE(SUM(ri.quantity), 0) - COALESCE(SUM(di.quantity), 0) as current_balance
FROM product p
LEFT JOIN category c ON p.category_id = c.id
FULL OUTER JOIN receipt_item ri ON p.id = ri.product_id
FULL OUTER JOIN dispatch_item di ON p.id = di.product_id
GROUP BY COALESCE(p.id, ri.product_id, di.product_id), 
         COALESCE(p.name, 'Товар удален'),
         COALESCE(c.name, 'Без категории')
ORDER BY current_balance DESC;

-- =====================================================
-- 5. ПОЛНАЯ ИСТОРИЯ ДВИЖЕНИЯ ТОВАРА
-- =====================================================
-- Детальная информация по конкретному товару с расшифровкой всех документов
SELECT 
    p.name as product_name,
    p.unit,
    'ПРИХОД' as operation_type,
    ri2.date as operation_date,
    ri2.id as invoice_id,
    s.name as counterparty,
    ri.quantity,
    ri.purchase_price as price,
    ri.quantity * ri.purchase_price as total,
    NULL as destination
FROM product p
JOIN receipt_item ri ON p.id = ri.product_id
JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
JOIN supplier s ON ri2.supplier_id = s.id
WHERE p.id = 1  -- конкретный товар

UNION

SELECT 
    p.name as product_name,
    p.unit,
    'РАСХОД' as operation_type,
    di2.date as operation_date,
    di2.id as invoice_id,
    di2.destination as counterparty,
    di.quantity,
    di.write_off_price as price,
    di.quantity * di.write_off_price as total,
    di2.destination
FROM product p
JOIN dispatch_item di ON p.id = di.product_id
JOIN dispatch_invoice di2 ON di.dispatch_invoice_id = di2.id
WHERE p.id = 1  -- конкретный товар
ORDER BY operation_date DESC, operation_type;