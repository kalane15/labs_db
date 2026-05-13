INSERT INTO category (name, description)
VALUES ('Старая категория', 'Попытка создать дубликат')
RETURNING id;

BEGIN;

INSERT INTO category (name, description)
VALUES ('Старая категория', 'Попытка создать дубликат')

UPDATE product
SET category_id = 9;

ROLLBACK;

SELECT * FROM product P WHERE p.category_id = 9;