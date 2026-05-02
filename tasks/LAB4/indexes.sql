CREATE INDEX idx_receipt_item_product_price ON receipt_item (product_id, purchase_price);

CREATE INDEX idx_receipt_item_price_desc ON receipt_item (purchase_price DESC);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_product_name_gin ON product USING GIN (lower(name) gin_trgm_ops);

CREATE INDEX idx_product_name_gist_l ON product USING GiST (lower(name) gist_trgm_ops);

CREATE INDEX idx_product_name_trgm ON product USING GIN (name gin_trgm_ops);

CREATE INDEX idx_receipt_item_price_plain ON receipt_item (purchase_price);