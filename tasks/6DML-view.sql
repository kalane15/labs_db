-- =====================================================
-- ПРЕДСТАВЛЕНИЕ 1: ТОП-10 ТОВАРОВ ПО ОБОРОТУ С АНАЛИТИКОЙ
-- =====================================================
-- Задача: выявить самые продаваемые и прибыльные товары с ключевыми метриками
CREATE VIEW top_products_by_turnover AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.unit,
    c.name as category_name,
    s.name as supplier_name,
    
    -- Основные показатели по приходу
    COALESCE(SUM(ri.quantity), 0) as total_received_quantity,
    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_purchase_cost,
    COALESCE(AVG(ri.purchase_price), 0)::numeric(15,2) as avg_purchase_price,
    COUNT(DISTINCT ri.receipt_invoice_id) as receipt_count,
    MIN(ri2.date) as first_receipt_date,
    MAX(ri2.date) as last_receipt_date,
    
    -- Основные показатели по расходу
    COALESCE(SUM(di.quantity), 0) as total_sold_quantity,
    COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as total_sales_revenue,
    COALESCE(AVG(di.write_off_price), 0)::numeric(15,2) as avg_sales_price,
    COUNT(DISTINCT di.dispatch_invoice_id) as sales_count,
    
    -- Вычисляемые показатели
    COALESCE(SUM(ri.quantity), 0) - COALESCE(SUM(di.quantity), 0) as current_balance,
    (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
     COALESCE(SUM(ri.quantity * ri.purchase_price), 0))::numeric(15,2) as estimated_profit,
    
    CASE 
        WHEN COALESCE(SUM(ri.quantity), 0) > 0 
        THEN ROUND(100.0 * COALESCE(SUM(di.quantity), 0) / COALESCE(SUM(ri.quantity), 0), 1)
        ELSE 0 
    END as turnover_percentage,
    
    CASE 
        WHEN COALESCE(SUM(di.quantity), 0) > 0 
        THEN (COALESCE(SUM(di.quantity * di.write_off_price), 0) / 
              NULLIF(COALESCE(SUM(di.quantity), 0), 0))::numeric(15,2)
        ELSE 0 
    END as avg_selling_price,    
    RANK() OVER (ORDER BY COALESCE(SUM(di.quantity * di.write_off_price), 0) DESC) as turnover_rank,
    RANK() OVER (ORDER BY (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
                           COALESCE(SUM(ri.quantity * ri.purchase_price), 0)) DESC) as profit_rank
FROM product p
LEFT JOIN category c ON p.category_id = c.id
LEFT JOIN supplier s ON p.supplier_id = s.id
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
LEFT JOIN dispatch_item di ON p.id = di.product_id
GROUP BY p.id, p.name, p.unit, c.name, s.name;

-- Использование: получить топ-10 товаров по обороту
SELECT * FROM top_products_by_turnover
WHERE total_sold_quantity > 0
ORDER BY turnover_rank
LIMIT 10;

-- =====================================================
-- ПРЕДСТАВЛЕНИЕ 2: СВОДКА ПО КАТЕГОРИЯМ ТОВАРОВ С ДИНАМИКОЙ
-- =====================================================
-- Задача: получить агрегированные показатели по категориям для анализа ассортимента
CREATE VIEW category_summary AS
SELECT 
    c.id as category_id,
    c.name as category_name,
    c.description,
    --
    -- Статистика по товарам
    COUNT(DISTINCT p.id) as total_products,
    COUNT(DISTINCT p.supplier_id) as suppliers_count,
    COUNT(DISTINCT CASE WHEN p.unit = 'шт' THEN p.id END) as products_in_pieces,
    COUNT(DISTINCT CASE WHEN p.unit = 'кг' THEN p.id END) as products_in_kg,
    COUNT(DISTINCT CASE WHEN p.unit = 'л' THEN p.id END) as products_in_liters,
    COUNT(DISTINCT CASE WHEN p.unit = 'м' THEN p.id END) as products_in_meters,
    COUNT(DISTINCT CASE WHEN p.unit = 'уп' THEN p.id END) as products_in_packs,
    --
    -- Финансовые показатели
    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_purchase_cost,
    COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as total_sales_revenue,
    (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
     COALESCE(SUM(ri.quantity * ri.purchase_price), 0))::numeric(15,2) as gross_profit,
    --
    -- Количественные показатели
    COALESCE(SUM(ri.quantity), 0) as total_received_quantity,
    COALESCE(SUM(di.quantity), 0) as total_sold_quantity,
    COALESCE(SUM(ri.quantity), 0) - COALESCE(SUM(di.quantity), 0) as current_balance_quantity,
    --
    -- Ценовые показатели
    COALESCE(AVG(ri.purchase_price), 0)::numeric(15,2) as avg_purchase_price,
    COALESCE(AVG(di.write_off_price), 0)::numeric(15,2) as avg_sales_price,
    --
    -- Маржинальность
    CASE 
        WHEN COALESCE(SUM(ri.quantity * ri.purchase_price), 0) > 0 
        THEN ROUND(100.0 * (COALESCE(SUM(di.quantity * di.write_off_price), 0) - 
                            COALESCE(SUM(ri.quantity * ri.purchase_price), 0)) / 
                   COALESCE(SUM(ri.quantity * ri.purchase_price), 0), 2)
        ELSE 0 
    END as profit_margin_percent,
    --
    -- Активность
    COUNT(DISTINCT ri2.id) as receipt_invoices_count,
    COUNT(DISTINCT di2.id) as dispatch_invoices_count,
    MIN(ri2.date) as first_receipt_date,
    MAX(ri2.date) as last_receipt_date,
    MIN(di2.date) as first_sale_date,
    MAX(di2.date) as last_sale_date,
    --  
    -- Доля в общем обороте
    ROUND(100.0 * COALESCE(SUM(di.quantity * di.write_off_price), 0) / 
          NULLIF((SELECT SUM(di2.quantity * di2.write_off_price) FROM dispatch_item di2), 0), 2) as market_share_percent
--
FROM category c
LEFT JOIN product p ON c.id = p.category_id
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
LEFT JOIN dispatch_item di ON p.id = di.product_id
LEFT JOIN dispatch_invoice di2 ON di.dispatch_invoice_id = di2.id
--
GROUP BY c.id, c.name, c.description;

-- Использование: получить категории с максимальной прибылью
SELECT * FROM category_summary
WHERE total_sales_revenue > 0
ORDER BY gross_profit DESC;
