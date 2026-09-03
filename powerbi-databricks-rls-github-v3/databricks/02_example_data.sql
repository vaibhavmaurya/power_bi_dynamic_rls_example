INSERT INTO mart.sales VALUES
  (1, 'INDIA',   'Customer A', 100000.00),
  (2, 'INDIA',   'Customer B', 200000.00),
  (3, 'GERMANY', 'Customer C', 300000.00),
  (4, 'USA',     'Customer D', 400000.00);

INSERT INTO security.user_access
  (user_upn, region_key, valid_from, valid_to, is_active, source_group)
VALUES
  ('john@company.com', 'INDIA',   current_timestamp(), NULL, TRUE, 'SG_SALES_INDIA'),
  ('john@company.com', 'GERMANY', current_timestamp(), NULL, TRUE, 'SG_SALES_GERMANY'),
  ('mary@company.com', 'USA',     current_timestamp(), NULL, TRUE, 'SG_SALES_USA');
