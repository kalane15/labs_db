-- =====================================================
-- 1. ÑÂÎÄÍÀß ÑÒÀÒÈÑÒÈÊÀ ÏÎ ÑÊËÀÄÓ
-- =====================================================
SELECT 
    COUNT(DISTINCT p.id) as total_products,
    COUNT(DISTINCT s.id) as total_suppliers,
    COUNT(DISTINCT c.id) as total_categories,
    COALESCE(SUM(ri.quantity), 0) as total_received,
    COALESCE(SUM(di.quantity), 0) as total_dispatched,
    COALESCE(SUM(ri.quantity * ri.purchase_price), 0)::numeric(15,2) as total_purchase_value,
    COALESCE(SUM(di.quantity * di.write_off_price), 0)::numeric(15,2) as total_sales_value,
    COALESCE(AVG(ri.purchase_price), 0)::numeric(15,2) as avg_purchase_price,
    COALESCE(AVG(di.write_off_price), 0)::numeric(15,2) as avg_sales_price
FROM product p
CROSS JOIN (SELECT COUNT(*) FROM supplier) s
CROSS JOIN (SELECT COUNT(*) FROM category) c
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN dispatch_item di ON p.id = di.product_id;

-- =====================================================
-- 2. ÑÒÀÒÈÑÒÈÊÀ ÏÎ ÊÀÒÅÃÎÐÈßÌ (GROUP BY, HAVING, ORDER BY)
-- =====================================================
SELECT 
    c.name as category,
    COUNT(DISTINCT p.id) as products,
    COUNT(DISTINCT s.id) as suppliers,
    SUM(ri.quantity)::int as received,
    SUM(di.quantity)::int as sold,
    SUM(ri.quantity * ri.purchase_price)::numeric(15,2) as purchase_cost,
    SUM(di.quantity * di.write_off_price)::numeric(15,2) as sales_revenue,
    AVG(ri.purchase_price)::numeric(15,2) as avg_cost,
    MAX(ri.purchase_price)::numeric(15,2) as max_cost,
    MIN(ri.purchase_price)::numeric(15,2) as min_cost
FROM category c
JOIN product p ON c.id = p.category_id
JOIN supplier s ON p.supplier_id = s.id
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN dispatch_item di ON p.id = di.product_id
GROUP BY c.id, c.name
HAVING SUM(ri.quantity * ri.purchase_price) > 10000
ORDER BY sales_revenue DESC NULLS LAST
LIMIT 10;

-- =====================================================
-- 3. ÒÎÏ-10 ÒÎÂÀÐÎÂ ÏÎ ÎÁÎÐÀ×ÈÂÀÅÌÎÑÒÈ (ÀÃÐÅÃÀÖÈß + ÂÛ×ÈÑËÅÍÈß)
-- =====================================================
SELECT 
    p.name as product,
    p.unit,
    COALESCE(SUM(ri.quantity), 0) as received,
    COALESCE(SUM(di.quantity), 0) as sold,
    COALESCE(SUM(ri.quantity), 0) - COALESCE(SUM(di.quantity), 0) as balance,
    CASE 
        WHEN SUM(ri.quantity) > 0 
        THEN (SUM(di.quantity)::numeric / NULLIF(SUM(ri.quantity), 0) * 100)::numeric(5,1)
        ELSE 0 
    END as turnover_percent,
    AVG(ri.purchase_price)::numeric(15,2) as avg_cost,
    AVG(di.write_off_price)::numeric(15,2) as avg_sale_price,
    (AVG(di.write_off_price) - AVG(ri.purchase_price))::numeric(15,2) as profit_per_unit
FROM product p
LEFT JOIN receipt_item ri ON p.id = ri.product_id
LEFT JOIN dispatch_item di ON p.id = di.product_id
GROUP BY p.id, p.name, p.unit
HAVING COALESCE(SUM(ri.quantity), 0) > 0
ORDER BY turnover_percent DESC
LIMIT 10;

-- =====================================================
-- 4. ÄÈÍÀÌÈÊÀ ÏÎ ÌÅÑßÖÀÌ (ÀÃÐÅÃÀÖÈß + ÔÎÐÌÀÒÈÐÎÂÀÍÈÅ + ÎÊÎÍÍÛÅ ÔÓÍÊÖÈÈ)
-- =====================================================
SELECT 
    TO_CHAR(date, 'YYYY-MM') as month,
    COUNT(DISTINCT ri.id) as receipts_count,
    SUM(ri.quantity) as quantity_received,
    SUM(ri.quantity * ri.purchase_price)::numeric(15,2) as amount_received,
    COUNT(DISTINCT di.id) as dispatches_count,
    SUM(di.quantity) as quantity_sold,
    SUM(di.quantity * di.write_off_price)::numeric(15,2) as amount_sold,
    AVG(ri.purchase_price)::numeric(15,2) as avg_price,
    SUM(SUM(ri.quantity * ri.purchase_price)) OVER (ORDER BY TO_CHAR(date, 'YYYY-MM'))::numeric(15,2) as cumulative_revenue
FROM receipt_invoice ri2
LEFT JOIN receipt_item ri ON ri2.id = ri.receipt_invoice_id
FULL OUTER JOIN dispatch_invoice di2 ON TO_CHAR(ri2.date, 'YYYY-MM') = TO_CHAR(di2.date, 'YYYY-MM')
LEFT JOIN dispatch_item di ON di2.id = di.dispatch_invoice_id
GROUP BY TO_CHAR(date, 'YYYY-MM')
ORDER BY month DESC
LIMIT 12;

-- =====================================================
-- 5. ÑÒÀÒÈÑÒÈÊÀ ÏÎ ÏÎÑÒÀÂÙÈÊÀÌ (Ñ ÌÅÄÈÀÍÎÉ È ÐÀÍÆÈÐÎÂÀÍÈÅÌ)
-- =====================================================
SELECT 
    s.name as supplier,
    COUNT(DISTINCT p.id) as products,
    COUNT(DISTINCT ri2.id) as deliveries,
    SUM(ri.quantity) as total_quantity,
    SUM(ri.quantity * ri.purchase_price)::numeric(15,2) as total_amount,
    AVG(ri.purchase_price)::numeric(15,2) as avg_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ri.purchase_price)::numeric(15,2) as median_price,
    MIN(ri.purchase_price)::numeric(15,2) as min_price,
    MAX(ri.purchase_price)::numeric(15,2) as max_price,
    RANK() OVER (ORDER BY SUM(ri.quantity * ri.purchase_price) DESC) as rank_by_amount
FROM supplier s
JOIN product p ON s.id = p.supplier_id
JOIN receipt_item ri ON p.id = ri.product_id
JOIN receipt_invoice ri2 ON ri.receipt_invoice_id = ri2.id
GROUP BY s.id, s.name
HAVING COUNT(DISTINCT ri2.id) >= 2
ORDER BY total_amount DESC;

-- =====================================================
-- 6. ÀÍÀËÈÇ ÏÐÈÁÛËÜÍÎÑÒÈ (ÏÐÎÖÅÍÒÍÛÅ ÑÎÎÒÍÎØÅÍÈß)
-- =====================================================
WITH stats AS (
    SELECT 
        c.name as category,
        COALESCE(SUM(ri.quantity * ri.purchase_price), 0) as cost,
        COALESCE(SUM(di.quantity * di.write_off_price), 0) as revenue,
        COALESCE(SUM(ri.quantity), 0) as received_qty,
        COALESCE(SUM(di.quantity), 0) as sold_qty
    FROM category c
    LEFT JOIN product p ON c.id = p.category_id
    LEFT JOIN receipt_item ri ON p.id = ri.product_id
    LEFT JOIN dispatch_item di ON p.id = di.product_id
    GROUP BY c.id, c.name
)
SELECT 
    category,
    cost::numeric(15,2),
    revenue::numeric(15,2),
    (revenue - cost)::numeric(15,2) as profit,
    CASE WHEN cost > 0 THEN ROUND(100.0 * (revenue - cost) / cost, 2) ELSE 0 END as roi_percent,
    ROUND(100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) as revenue_share,
    ROUND(100.0 * sold_qty / NULLIF(SUM(sold_qty) OVER (), 0), 2) as sales_volume_share
FROM stats
WHERE cost > 0 OR revenue > 0
ORDER BY profit DESC;