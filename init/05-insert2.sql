INSERT INTO receipt_invoice (date, supplier_id)
SELECT 
    CURRENT_DATE - (random() * 365)::int,
    (random() * 9 + 1)::int
FROM generate_series(1, 100)
ON CONFLICT DO NOTHING;


INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
SELECT 
    (random() * 100 + 0.001)::numeric(15,3),
    (random() * 10000)::numeric(15,2),
    (random() * 99 + 1)::int,
    (random() * 99 + 1)::int
FROM generate_series(1, 1000000);


INSERT INTO product (name, unit, category_id, supplier_id)
SELECT 
    CONCAT(
        (ARRAY['Смартфон', 'Ноутбук', 'Планшет', 'Наушники', 'Телевизор',
                'Холодильник', 'Микроволновка', 'Пылесос', 'Чайник', 'Кофеварка',
                'Молоко', 'Хлеб', 'Сыр', 'Колбаса', 'Печенье',
                'Вода', 'Сок', 'Кола', 'Чай', 'Кофе'])[floor(random() * 20 + 1)],
        ' ',
        floor(random() * 10000)::int
    ) as name,
    (ARRAY['шт', 'кг', 'л', 'м', 'уп'])[floor(random() * 5 + 1)] as unit,
    floor(random() * 8 + 1)::int as category_id,
    floor(random() * 10 + 1)::int as supplier_id
FROM generate_series(1, 1000000) g;

INSERT INTO product (name, unit, category_id, supplier_id)
SELECT 
    'Мультиварка ' || g::text,
    'шт',
    floor(random() * 8 + 1)::int,
    floor(random() * 10 + 1)::int
FROM generate_series(1, 10) g;