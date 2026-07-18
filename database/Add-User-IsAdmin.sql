-- =============================================================================
-- Migration: adiciona "isAdmin" na tabela "User"
-- Execute no SQL Editor do Supabase (ou psql) conectado ao banco do projeto.
-- Idempotente: so adiciona a coluna se ela ainda nao existir.
-- =============================================================================

BEGIN;

ALTER TABLE "User"
    ADD COLUMN IF NOT EXISTS "isAdmin" boolean NOT NULL DEFAULT false;

COMMIT;
