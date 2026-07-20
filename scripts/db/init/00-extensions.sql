-- Runs ONCE at Postgres first-init, against POSTGRES_DB (the app database),
-- BEFORE the app ever connects. The app's schema build (create_all) declares a
-- GIN trigram index, which needs the pg_trgm operator class to already exist —
-- on a virgin database the app's own late CREATE EXTENSION is too late and
-- create_all fails with: operator class "gin_trgm_ops" does not exist.
-- Installing it here makes a from-zero stand-up work. (Restored backups already
-- carry the extension via pg_dump.)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
