-- =============================================================================
-- Migration: adiciona "teamCycleSeasonId" na tabela "File"
--   * Nova coluna uuid (anulavel, para nao quebrar linhas ja existentes).
--   * FK para "TeamCycleSeason"("id").
--   * Indice na coluna de FK (PostgreSQL nao cria automaticamente).
-- Execute no SQL Editor do Supabase (ou psql) conectado ao banco do projeto.
-- =============================================================================

BEGIN;

ALTER TABLE "File"
    ADD COLUMN "teamCycleSeasonId" uuid;

ALTER TABLE "File"
    ADD CONSTRAINT "fk_File_teamCycleSeasonId"
    FOREIGN KEY ("teamCycleSeasonId") REFERENCES "TeamCycleSeason" ("id");

CREATE INDEX "ix_File_teamCycleSeasonId"
    ON "File" ("teamCycleSeasonId");

COMMIT;
