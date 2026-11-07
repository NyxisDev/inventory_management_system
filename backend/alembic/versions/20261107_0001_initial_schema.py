"""Initial schema: extension, enum types, tables, CHECKs, indexes, triggers.

The SQL matches the schema from docs/deepseek-prompts.md (Part 1) exactly.

Revision ID: 0001
Revises:
Create Date: 2026-11-07

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# asyncpg runs one statement per call, so every statement is a separate item.
UPGRADE_STATEMENTS: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE TYPE employee_role AS ENUM ('admin', 'staff')",
    "CREATE TYPE movement_type AS ENUM ('income', 'outcome', 'adjustment', 'transfer_in', 'transfer_out')",
    "CREATE TYPE audit_action AS ENUM "
    "('create', 'update', 'delete', 'login', 'login_failed', 'logout', 'stock_change')",
    # --- employees ---
    """
    CREATE TABLE employees (
      id            SERIAL PRIMARY KEY,
      first_name    VARCHAR(100) NOT NULL,
      last_name     VARCHAR(100) NOT NULL,
      username      VARCHAR(50)  NOT NULL UNIQUE,
      password_hash VARCHAR(255) NOT NULL,
      role          employee_role NOT NULL DEFAULT 'staff',
      is_active     BOOLEAN NOT NULL DEFAULT TRUE,
      failed_login_attempts INT NOT NULL DEFAULT 0,
      locked_until  TIMESTAMPTZ,
      password_changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_login_at TIMESTAMPTZ,
      created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    # --- refresh_tokens ---
    """
    CREATE TABLE refresh_tokens (
      id          BIGSERIAL PRIMARY KEY,
      employee_id INT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
      token_hash  CHAR(64) NOT NULL UNIQUE,
      expires_at  TIMESTAMPTZ NOT NULL,
      revoked_at  TIMESTAMPTZ,
      replaced_by BIGINT REFERENCES refresh_tokens(id),
      ip_address  INET,
      user_agent  VARCHAR(500),
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_refresh_employee ON refresh_tokens(employee_id)",
    # --- categories ---
    """
    CREATE TABLE categories (
      id         SERIAL PRIMARY KEY,
      name       VARCHAR(150) NOT NULL,
      slug       VARCHAR(150) NOT NULL UNIQUE,
      parent_id  INT REFERENCES categories(id) ON DELETE SET NULL,
      sort_order INT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    # --- warehouses ---
    """
    CREATE TABLE warehouses (
      id           SERIAL PRIMARY KEY,
      name         VARCHAR(150) NOT NULL UNIQUE,
      address      VARCHAR(255),
      is_active    BOOLEAN NOT NULL DEFAULT TRUE,
      show_on_site BOOLEAN NOT NULL DEFAULT TRUE,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    # --- products ---
    """
    CREATE TABLE products (
      id           SERIAL PRIMARY KEY,
      sku          VARCHAR(64)  NOT NULL UNIQUE,
      name         VARCHAR(255) NOT NULL,
      slug         VARCHAR(255) NOT NULL UNIQUE,
      description  TEXT,
      category_id  INT REFERENCES categories(id) ON DELETE SET NULL,
      unit         VARCHAR(16)  NOT NULL DEFAULT 'pcs',
      price        NUMERIC(12,2) NOT NULL CHECK (price >= 0),
      is_published BOOLEAN NOT NULL DEFAULT FALSE,
      is_archived  BOOLEAN NOT NULL DEFAULT FALSE,
      created_by   INT REFERENCES employees(id) ON DELETE SET NULL,
      updated_by   INT REFERENCES employees(id) ON DELETE SET NULL,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_products_category  ON products(category_id)",
    "CREATE INDEX ix_products_name_trgm ON products USING gin (name gin_trgm_ops)",
    "CREATE INDEX ix_products_sku_trgm  ON products USING gin (sku gin_trgm_ops)",
    # --- product_images ---
    """
    CREATE TABLE product_images (
      id         SERIAL PRIMARY KEY,
      product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
      file_path  VARCHAR(500) NOT NULL,
      is_main    BOOLEAN NOT NULL DEFAULT FALSE,
      sort_order INT NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE UNIQUE INDEX ux_product_images_main ON product_images(product_id) WHERE is_main",
    # --- stock ---
    """
    CREATE TABLE stock (
      product_id   INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
      warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
      quantity     NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
      min_quantity NUMERIC(14,3) NOT NULL DEFAULT 0,
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
      PRIMARY KEY (product_id, warehouse_id)
    )
    """,
    # --- stock_movements ---
    """
    CREATE TABLE stock_movements (
      id              BIGSERIAL PRIMARY KEY,
      product_id      INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
      warehouse_id    INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
      employee_id     INT REFERENCES employees(id) ON DELETE SET NULL,
      type            movement_type NOT NULL,
      quantity_change NUMERIC(14,3) NOT NULL,
      quantity_after  NUMERIC(14,3) NOT NULL,
      transfer_group  UUID,
      comment         VARCHAR(500),
      created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_movements_product   ON stock_movements(product_id, created_at DESC)",
    "CREATE INDEX ix_movements_warehouse ON stock_movements(warehouse_id, created_at DESC)",
    "CREATE INDEX ix_movements_employee  ON stock_movements(employee_id, created_at DESC)",
    # --- audit_log ---
    """
    CREATE TABLE audit_log (
      id            BIGSERIAL PRIMARY KEY,
      employee_id   INT REFERENCES employees(id) ON DELETE SET NULL,
      employee_name VARCHAR(201),
      action        audit_action NOT NULL,
      entity_type   VARCHAR(50) NOT NULL,
      entity_id     VARCHAR(64),
      old_data      JSONB,
      new_data      JSONB,
      ip_address    INET,
      user_agent    VARCHAR(500),
      created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_audit_employee ON audit_log(employee_id, created_at DESC)",
    "CREATE INDEX ix_audit_entity   ON audit_log(entity_type, entity_id)",
    "CREATE INDEX ix_audit_created  ON audit_log(created_at DESC)",
    # --- updated_at triggers ---
    """
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
    BEGIN NEW.updated_at = now(); RETURN NEW; END;
    $$ LANGUAGE plpgsql
    """,
    "CREATE TRIGGER trg_employees_upd  BEFORE UPDATE ON employees  FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    "CREATE TRIGGER trg_categories_upd BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    "CREATE TRIGGER trg_warehouses_upd BEFORE UPDATE ON warehouses FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    "CREATE TRIGGER trg_products_upd   BEFORE UPDATE ON products   FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    "CREATE TRIGGER trg_stock_upd      BEFORE UPDATE ON stock      FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    # --- audit_log is append-only ---
    """
    CREATE OR REPLACE FUNCTION forbid_audit_change() RETURNS trigger AS $$
    BEGIN RAISE EXCEPTION 'audit_log is append-only'; END;
    $$ LANGUAGE plpgsql
    """,
    "CREATE TRIGGER trg_audit_readonly BEFORE UPDATE OR DELETE ON audit_log "
    "FOR EACH ROW EXECUTE FUNCTION forbid_audit_change()",
    # --- privileges for the runtime role (skipped if app_user does not exist, e.g. in some test setups) ---
    """
    DO $$
    BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON
          employees, refresh_tokens, categories, warehouses, products,
          product_images, stock, stock_movements TO app_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
        -- audit_log: read and append only
        REVOKE ALL ON audit_log FROM app_user;
        GRANT SELECT, INSERT ON audit_log TO app_user;
        -- app_user must not touch the migration bookkeeping
        REVOKE ALL ON alembic_version FROM app_user;
      END IF;
    END
    $$
    """,
]

DOWNGRADE_STATEMENTS: list[str] = [
    "DROP TABLE IF EXISTS audit_log",
    "DROP TABLE IF EXISTS stock_movements",
    "DROP TABLE IF EXISTS stock",
    "DROP TABLE IF EXISTS product_images",
    "DROP TABLE IF EXISTS products",
    "DROP TABLE IF EXISTS warehouses",
    "DROP TABLE IF EXISTS categories",
    "DROP TABLE IF EXISTS refresh_tokens",
    "DROP TABLE IF EXISTS employees",
    "DROP FUNCTION IF EXISTS forbid_audit_change()",
    "DROP FUNCTION IF EXISTS set_updated_at()",
    "DROP TYPE IF EXISTS audit_action",
    "DROP TYPE IF EXISTS movement_type",
    "DROP TYPE IF EXISTS employee_role",
    # The pg_trgm extension is left in place: other objects may use it.
]


def upgrade() -> None:
    for statement in UPGRADE_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE_STATEMENTS:
        op.execute(statement)
