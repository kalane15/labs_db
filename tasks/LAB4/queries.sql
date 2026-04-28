-- Сложный фильтр

EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM receipt_item
WHERE product_id = 25
  AND purchase_price BETWEEN 100 AND 500;