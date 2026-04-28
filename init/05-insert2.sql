-- Insert 01

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