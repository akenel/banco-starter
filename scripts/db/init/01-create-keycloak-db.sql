-- Runs ONCE at Postgres first-init (docker-entrypoint-initdb.d).
-- Gives Keycloak its own database on the same Postgres instance, so KC's
-- tables never mingle with the app schema, the audit triggers, or a POS
-- data restore. The app database itself is created by POSTGRES_DB.
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec
