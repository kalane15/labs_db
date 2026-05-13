BEGIN;

INSERT INTO dispatch_invoice (date, destination)
VALUES (CURRENT_DATE, 'ИП "Покупатель"');

INSERT INTO dispatch_item (quantity, write_off_price, dispatch_invoice_id, product_id)
VALUES (5.000, -100.00, currval('dispatch_invoice_id_seq'), 5);

UPDATE supplier SET contact_person = 'Новый контакт' WHERE id = (SELECT supplier_id FROM product WHERE id = 5);

ROLLBACK;

SELECT * FROM dispatch_invoice WHERE id = currval('dispatch_invoice_id_seq');
SELECT contact_person FROM supplier WHERE id = (SELECT supplier_id FROM product WHERE id = 5);