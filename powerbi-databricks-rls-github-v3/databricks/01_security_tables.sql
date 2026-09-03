-- Databricks / Delta security tables.
-- Adapt catalog and schema names to your platform standards.

CREATE SCHEMA IF NOT EXISTS security;

CREATE TABLE IF NOT EXISTS security.user_access (
    user_upn        STRING NOT NULL,
    region_key      STRING NOT NULL,
    valid_from      TIMESTAMP,
    valid_to        TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    source_group    STRING,
    updated_at      TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA;

-- Business table shown only for example.
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.sales (
    sales_id        BIGINT,
    region_key      STRING NOT NULL,
    customer_name   STRING,
    revenue         DECIMAL(18,2)
)
USING DELTA;

-- Useful for entitlement checks and operational auditing.
CREATE OR REPLACE VIEW security.v_active_user_access AS
SELECT
    lower(trim(user_upn)) AS user_upn,
    region_key
FROM security.user_access
WHERE is_active = TRUE
  AND (valid_from IS NULL OR valid_from <= current_timestamp())
  AND (valid_to   IS NULL OR valid_to   >  current_timestamp());
