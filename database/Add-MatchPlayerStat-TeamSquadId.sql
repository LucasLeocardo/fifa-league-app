-- =============================================================================
-- Migração: adiciona "teamSquadId" em "MatchPlayerStat"
--   * Nova coluna uuid (anulável, para nao quebrar linhas ja existentes).
--   * FK para "TeamSquad"("id").
--   * Indice na coluna de FK (PostgreSQL nao cria automaticamente).
-- =============================================================================

BEGIN;

ALTER TABLE "MatchPlayerStat"
    ADD COLUMN "teamSquadId" uuid;

ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "fk_MatchPlayerStat_teamSquadId"
    FOREIGN KEY ("teamSquadId") REFERENCES "TeamSquad" ("id");

CREATE INDEX "ix_MatchPlayerStat_teamSquadId"
    ON "MatchPlayerStat" ("teamSquadId");

COMMIT;
