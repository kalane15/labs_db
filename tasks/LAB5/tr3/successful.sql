BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ООО "Розничный магазин"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (10.000, 150.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier
SET contact_person = 'Смирнова А.В.'
WHERE id = (SELECT supplier_id FROM product WHERE id = 5);

COMMIT;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');
SELECT * FROM dispatch_item WHERE dispatch_invoice_id = currval('dispatch_invoice_id_seq');
SELECT id, name, contact_person FROM supplier WHERE id = (SELECT supplier_id FROM product WHERE id = 5);