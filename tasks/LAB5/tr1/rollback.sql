SELECT id+1 FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq')


BEGIN;

INSERT INTO receipt_invoice (date, supplier_id)
VALUES (CURRENT_DATE, 1);

INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (20.000, 120.00, currval('receipt_invoice_id_seq'), 5);

SAVEPOINT before_se
INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (3.000, 300.00, currval('receipt_invoice_id_seq'), 8);

SAVEPOINT before_third;

INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (-5.000, 100.00, currval('receipt_invoice_id_seq'), 10);

ROLLBACK TO SAVEPOINT before_third;

COMMIT;

SELECT * FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq') ORDER BY id;