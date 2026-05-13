BEGIN;

WITH limited_rows AS (
    SELECT id
    FROM product
    WHERE category_id = 1
)
UPDATE product
SET category_id = 8
WHERE id IN (SELECT id FROM limited_rows);

SAVEPOINT after_update;

DELETE FROM category
WHERE id = 1;

ROLLBACK TO SAVEPOINT after_update;

COMMIT;

select * from product p where p.category_id = 1
SELECT * from category where id = 1;