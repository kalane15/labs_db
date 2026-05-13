BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ООО "Оптовик"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (20.000, 120.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier
SET contact_person = 'Петров П.П.'
WHERE id = 5;

SAVEPOINT after_good;

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (0, 110.00, currval('dispatch_invoice_id_seq'), 8);

ROLLBACK TO SAVEPOINT after_good;

COMMIT;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');
SELECT * FROM dispatch_item WHERE dispatch_invoice_id = currval('dispatch_invoice_id_seq');
SELECT contact_person FROM supplier WHERE id = 5;