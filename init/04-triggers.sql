-- 0. Создание таблицы аудита (если ещё не создана)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(10) NOT NULL,        -- INSERT, UPDATE, DELETE
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- 1. Триггерная функция для аудита приходных позиций
CREATE OR REPLACE FUNCTION audit_receipt_item()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('INSERT', 'receipt_item', NEW.id,
                jsonb_build_object('quantity', NEW.quantity,
                                   'price', NEW.purchase_price,
                                   'invoice_id', NEW.receipt_invoice_id,
                                   'product_id', NEW.product_id));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('UPDATE', 'receipt_item', NEW.id,
                jsonb_build_object('old_quantity', OLD.quantity,
                                   'new_quantity', NEW.quantity,
                                   'old_price', OLD.purchase_price,
                                   'new_price', NEW.purchase_price));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('DELETE', 'receipt_item', OLD.id,
                jsonb_build_object('quantity', OLD.quantity,
                                   'price', OLD.purchase_price));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Создание триггера
DROP TRIGGER IF EXISTS trg_audit_receipt_item ON receipt_item;
CREATE TRIGGER trg_audit_receipt_item
AFTER INSERT OR UPDATE OR DELETE ON receipt_item
FOR EACH ROW EXECUTE FUNCTION audit_receipt_item();

-- 2. Триггерная функция для аудита расходных позиций
CREATE OR REPLACE FUNCTION audit_dispatch_item()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('INSERT', 'dispatch_item', NEW.id,
                jsonb_build_object('quantity', NEW.quantity,
                                   'price', NEW.write_off_price,
                                   'invoice_id', NEW.dispatch_invoice_id,
                                   'product_id', NEW.product_id));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('UPDATE', 'dispatch_item', NEW.id,
                jsonb_build_object('old_quantity', OLD.quantity,
                                   'new_quantity', NEW.quantity,
                                   'old_price', OLD.write_off_price,
                                   'new_price', NEW.write_off_price));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (operation, table_name, record_id, details)
        VALUES ('DELETE', 'dispatch_item', OLD.id,
                jsonb_build_object('quantity', OLD.quantity,
                                   'price', OLD.write_off_price));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_dispatch_item ON dispatch_item;
CREATE TRIGGER trg_audit_dispatch_item
AFTER INSERT OR UPDATE OR DELETE ON dispatch_item
FOR EACH ROW EXECUTE FUNCTION audit_dispatch_item();
