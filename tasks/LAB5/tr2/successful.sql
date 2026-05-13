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