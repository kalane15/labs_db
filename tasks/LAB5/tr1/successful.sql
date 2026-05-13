BEGIN;


INSERT INTO receipt_invoice (date, supplier_id)
VALUES (CURRENT_DATE, 1);


INSERT INTO receipt_item (quantity, purchase_price, receipt_invoice_id, product_id)
VALUES 
    (10.000, 150.00, currval('receipt_invoice_id_seq'), 5),
    (5.000, 200.00, currval('receipt_invoice_id_seq'), 8);

COMMIT;


SELECT * FROM receipt_invoice WHERE id = currval('receipt_invoice_id_seq');
SELECT * FROM receipt_item WHERE receipt_invoice_id = currval('receipt_invoice_id_seq');