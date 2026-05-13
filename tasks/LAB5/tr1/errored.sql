SELECT id+1 FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq')

BEGIN;

INSERT INTO receipt_invoice (date, supplier_id)
VALUES (CURRENT_DATE, 1);

INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES (0, 150.00, currval('receipt_invoice_id_seq'), 5);

ROLLBACK;

SELECT EXISTS (SELECT 1 FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq')) AS invoice_exists;
SELECT EXISTS (SELECT 1 FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq')) AS item_exists;