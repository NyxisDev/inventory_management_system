-- Creates the app_owner / app_user roles and the database. Safe to run more than once.
--
-- Docker: docker-compose.yml mounts backend/db/ as /docker-entrypoint-initdb.d, so this file runs
-- automatically on the first start of the db container. The passwords come from the
-- APP_OWNER_PASSWORD and APP_USER_PASSWORD environment variables (set them in .env).
--
-- Without Docker, run it as a superuser:
--   APP_OWNER_PASSWORD=... APP_USER_PASSWORD=... psql -U postgres -f backend/db/init_roles.sql
-- or pass the passwords as psql variables:
--   psql -U postgres -v owner_password=... -v app_password=... -f backend/db/init_roles.sql
--
--   app_owner  owns the tables; Alembic migrations run as this role.
--   app_user   the application role: no SUPERUSER, no CREATE; SELECT/INSERT/UPDATE/DELETE on tables,
--              but only SELECT and INSERT on audit_log (set by the first migration).

\set ON_ERROR_STOP on

-- psql variables win; otherwise take the values from the environment.
\if :{?owner_password}
\else
  \getenv owner_password APP_OWNER_PASSWORD
\endif
\if :{?app_password}
\else
  \getenv app_password APP_USER_PASSWORD
\endif
\if :{?db_name}
\else
  \getenv db_name POSTGRES_DB
\endif
\if :{?db_name}
\else
  \set db_name inventory
\endif

\if :{?owner_password}
\else
  \warn 'APP_OWNER_PASSWORD is not set'
  SELECT 1/0 AS app_owner_password_missing;
\endif
\if :{?app_password}
\else
  \warn 'APP_USER_PASSWORD is not set'
  SELECT 1/0 AS app_user_password_missing;
\endif

-- Roles (created if missing, password always updated)
SELECT 'CREATE ROLE app_owner' WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_owner') \gexec
SELECT 'CREATE ROLE app_user' WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') \gexec
ALTER ROLE app_owner LOGIN PASSWORD :'owner_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE app_user LOGIN PASSWORD :'app_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Database (in Docker it already exists: the image creates POSTGRES_DB)
SELECT format('CREATE DATABASE %I OWNER app_owner ENCODING %L TEMPLATE template0', :'db_name', 'UTF8')
  WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_name') \gexec
ALTER DATABASE :"db_name" OWNER TO app_owner;

REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db_name" TO app_owner, app_user;
GRANT TEMPORARY ON DATABASE :"db_name" TO app_owner;

\connect :"db_name"

-- pg_trgm is a trusted extension, but create it here as superuser to be safe.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Only app_owner may create objects in the public schema.
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO app_owner;
GRANT USAGE ON SCHEMA public TO app_user;

-- Tables and sequences created later by app_owner (migrations) are usable by app_user.
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- The first migration additionally restricts audit_log to SELECT and INSERT for app_user
-- and revokes access to alembic_version.
