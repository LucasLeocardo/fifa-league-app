-- =============================================================================
-- FIFA League App - Schema PostgreSQL
-- Gerado a partir de database/Database-Diagram.drawio
--
-- Mapeamento de tipos do diagrama -> PostgreSQL:
--   guid       -> uuid
--   string     -> varchar(255)   (url usa text)
--   int        -> integer
--   float      -> double precision
--   date       -> date
--   timestamp  -> timestamptz
--   boolean    -> boolean
--
-- Regra de nullability das FKs (definida pelo autor):
--   * FKs de tabelas de ENTIDADE sao ANULAVEIS (permitem NULL).
--   * FKs de tabelas de RELACIONAMENTO sao NOT NULL.
--     Tabelas de relacionamento consideradas:
--       PlayerPosition, CycleSeason, TeamCycleSeason, TeamSquad, UserFeature,
--       MatchPlayerStat.
--     (Em MatchPlayerStat, matchId e playerId sao NOT NULL; sourceFile continua
--      anulavel por ser opcional -- referencia ao arquivo de origem.)
--
-- Outras premissas (nao explicitas no diagrama):
--   * Todos os "id" sao PK uuid com default gen_random_uuid().
--   * "createdAt"/"updatedAt" recebem DEFAULT now() e NOT NULL.
--   * Colunas de placar/estatistica (scores, goals, assists, rating, shirtNumber)
--     ficam anulaveis.
--   * Adicionadas UNIQUE nas tabelas de relacionamento e indices nas colunas FK.
--   * authUserId referencia auth.users(id) do Supabase (FK inline, ON DELETE SET NULL).
--   * Nomes preservam o casing do diagrama (PascalCase/camelCase) -> aspas duplas.
--
-- Obs.: CREATE DATABASE nao pode rodar dentro de transacao; crie o banco antes
-- e execute este script conectado nele.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Tabelas
-- ---------------------------------------------------------------------------

CREATE TABLE "User" (
    "id"             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "authUserId"     uuid        CONSTRAINT "fk_User_authUserId" REFERENCES "auth"."users" ("id") ON DELETE SET NULL
                                 CONSTRAINT "uq_User_authUserId" UNIQUE,
    "name"           varchar(255) NOT NULL,
    "email"          varchar(255) NOT NULL,
    "coachName"      varchar(255),
    "numberOfTitles" integer      NOT NULL DEFAULT 0,
    "isAdmin"        boolean      NOT NULL DEFAULT false,
    "createdAt"      timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "Player" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "overallId" uuid,
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now(),
    "updatedAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "Position" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "code"      varchar(255) NOT NULL,
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "PlayerPosition" (
    "id"         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "playerId"   uuid        NOT NULL,
    "positionId" uuid        NOT NULL,
    "createdAt"  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "Overall" (
    "id"         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "value"      integer     NOT NULL,
    "playerCost" integer     NOT NULL,
    "currency"   varchar(255),
    "createdAt"  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "Team" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "Cycle" (
    "id"           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "name"         varchar(255) NOT NULL,
    "friendlyName" varchar(255),
    "createdAt"    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "Season" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "CycleSeason" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "cycleId"   uuid        NOT NULL,
    "seasonId"  uuid        NOT NULL,
    "startDate" date        NOT NULL,
    "endDate"   date,
    "createdAt" timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "TeamCycleSeason" (
    "id"            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "teamId"        uuid        NOT NULL,
    "cycleSeasonId" uuid        NOT NULL,
    "userId"        uuid        NOT NULL,
    "createdAt"     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "TeamSquad" (
    "id"                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "teamCycleSeasonId" uuid        NOT NULL,
    "playerId"          uuid        NOT NULL,
    "shirtNumber"       integer,
    "createdAt"         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "MatchType" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "Match" (
    "id"         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "homeTeamId" uuid,
    "awayTeamId" uuid,
    "typeId"     uuid,
    "homeScore"  integer,
    "awayScore"  integer,
    "createdAt"  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "File" (
    "id"                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "parentId"          uuid,
    "sourceGameId"      uuid,
    "teamCycleSeasonId" uuid,
    "name"              varchar(255) NOT NULL,
    "extension"         varchar(255),
    "mimeType"          varchar(255),
    "url"               text        NOT NULL,
    "isProcessed"       boolean     NOT NULL DEFAULT false,
    "createdAt"         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "MatchPlayerStat" (
    "id"          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "matchId"     uuid        NOT NULL,
    "playerId"    uuid        NOT NULL,
    "teamSquadId" uuid,
    "sourceFile"  uuid,
    "goals"       integer,
    "assists"     integer,
    "rating"      double precision,
    "createdAt"   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE "Feature" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "name"      varchar(255) NOT NULL,
    "createdAt" timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE "UserFeature" (
    "id"        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    "userId"    uuid        NOT NULL,
    "featureId" uuid        NOT NULL,
    "createdAt" timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Chaves estrangeiras (conexoes do diagrama)
-- ---------------------------------------------------------------------------

-- FKs anulaveis (colunas opcionais)
-- Obs.: a FK de "User"."authUserId" -> auth.users(id) esta definida inline no CREATE TABLE.
ALTER TABLE "Player"
    ADD CONSTRAINT "fk_Player_overallId"
    FOREIGN KEY ("overallId") REFERENCES "Overall" ("id");

ALTER TABLE "Match"
    ADD CONSTRAINT "fk_Match_homeTeamId"
    FOREIGN KEY ("homeTeamId") REFERENCES "TeamCycleSeason" ("id");

ALTER TABLE "Match"
    ADD CONSTRAINT "fk_Match_awayTeamId"
    FOREIGN KEY ("awayTeamId") REFERENCES "TeamCycleSeason" ("id");

ALTER TABLE "Match"
    ADD CONSTRAINT "fk_Match_typeId"
    FOREIGN KEY ("typeId") REFERENCES "MatchType" ("id");

ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "fk_MatchPlayerStat_sourceFile"
    FOREIGN KEY ("sourceFile") REFERENCES "File" ("id");

ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "fk_MatchPlayerStat_teamSquadId"
    FOREIGN KEY ("teamSquadId") REFERENCES "TeamSquad" ("id");

ALTER TABLE "File"
    ADD CONSTRAINT "fk_File_parentId"
    FOREIGN KEY ("parentId") REFERENCES "File" ("id");

ALTER TABLE "File"
    ADD CONSTRAINT "fk_File_sourceGameId"
    FOREIGN KEY ("sourceGameId") REFERENCES "Match" ("id");

ALTER TABLE "File"
    ADD CONSTRAINT "fk_File_teamCycleSeasonId"
    FOREIGN KEY ("teamCycleSeasonId") REFERENCES "TeamCycleSeason" ("id");

-- FKs de tabelas de relacionamento (colunas NOT NULL)
ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "fk_MatchPlayerStat_matchId"
    FOREIGN KEY ("matchId") REFERENCES "Match" ("id");

ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "fk_MatchPlayerStat_playerId"
    FOREIGN KEY ("playerId") REFERENCES "Player" ("id");

ALTER TABLE "PlayerPosition"
    ADD CONSTRAINT "fk_PlayerPosition_playerId"
    FOREIGN KEY ("playerId") REFERENCES "Player" ("id");

ALTER TABLE "PlayerPosition"
    ADD CONSTRAINT "fk_PlayerPosition_positionId"
    FOREIGN KEY ("positionId") REFERENCES "Position" ("id");

ALTER TABLE "CycleSeason"
    ADD CONSTRAINT "fk_CycleSeason_cycleId"
    FOREIGN KEY ("cycleId") REFERENCES "Cycle" ("id");

ALTER TABLE "CycleSeason"
    ADD CONSTRAINT "fk_CycleSeason_seasonId"
    FOREIGN KEY ("seasonId") REFERENCES "Season" ("id");

ALTER TABLE "TeamCycleSeason"
    ADD CONSTRAINT "fk_TeamCycleSeason_teamId"
    FOREIGN KEY ("teamId") REFERENCES "Team" ("id");

ALTER TABLE "TeamCycleSeason"
    ADD CONSTRAINT "fk_TeamCycleSeason_cycleSeasonId"
    FOREIGN KEY ("cycleSeasonId") REFERENCES "CycleSeason" ("id");

ALTER TABLE "TeamCycleSeason"
    ADD CONSTRAINT "fk_TeamCycleSeason_userId"
    FOREIGN KEY ("userId") REFERENCES "User" ("id");

ALTER TABLE "TeamSquad"
    ADD CONSTRAINT "fk_TeamSquad_teamCycleSeasonId"
    FOREIGN KEY ("teamCycleSeasonId") REFERENCES "TeamCycleSeason" ("id");

ALTER TABLE "TeamSquad"
    ADD CONSTRAINT "fk_TeamSquad_playerId"
    FOREIGN KEY ("playerId") REFERENCES "Player" ("id");

ALTER TABLE "UserFeature"
    ADD CONSTRAINT "fk_UserFeature_userId"
    FOREIGN KEY ("userId") REFERENCES "User" ("id");

ALTER TABLE "UserFeature"
    ADD CONSTRAINT "fk_UserFeature_featureId"
    FOREIGN KEY ("featureId") REFERENCES "Feature" ("id");

-- ---------------------------------------------------------------------------
-- Unicidade das tabelas de relacionamento
-- ---------------------------------------------------------------------------

ALTER TABLE "PlayerPosition"
    ADD CONSTRAINT "uq_PlayerPosition_player_position"
    UNIQUE ("playerId", "positionId");

ALTER TABLE "CycleSeason"
    ADD CONSTRAINT "uq_CycleSeason_cycle_season"
    UNIQUE ("cycleId", "seasonId");

ALTER TABLE "TeamCycleSeason"
    ADD CONSTRAINT "uq_TeamCycleSeason_team_cycleSeason_user"
    UNIQUE ("teamId", "cycleSeasonId", "userId");

ALTER TABLE "TeamSquad"
    ADD CONSTRAINT "uq_TeamSquad_teamCycleSeason_player"
    UNIQUE ("teamCycleSeasonId", "playerId");

ALTER TABLE "UserFeature"
    ADD CONSTRAINT "uq_UserFeature_user_feature"
    UNIQUE ("userId", "featureId");

ALTER TABLE "MatchPlayerStat"
    ADD CONSTRAINT "uq_MatchPlayerStat_match_player"
    UNIQUE ("matchId", "playerId");

-- ---------------------------------------------------------------------------
-- Indices nas colunas de FK (PostgreSQL nao cria automaticamente)
-- ---------------------------------------------------------------------------

CREATE INDEX "ix_Player_overallId"                ON "Player" ("overallId");
CREATE INDEX "ix_PlayerPosition_playerId"         ON "PlayerPosition" ("playerId");
CREATE INDEX "ix_PlayerPosition_positionId"       ON "PlayerPosition" ("positionId");
CREATE INDEX "ix_CycleSeason_cycleId"             ON "CycleSeason" ("cycleId");
CREATE INDEX "ix_CycleSeason_seasonId"            ON "CycleSeason" ("seasonId");
CREATE INDEX "ix_TeamCycleSeason_teamId"          ON "TeamCycleSeason" ("teamId");
CREATE INDEX "ix_TeamCycleSeason_cycleSeasonId"   ON "TeamCycleSeason" ("cycleSeasonId");
CREATE INDEX "ix_TeamCycleSeason_userId"          ON "TeamCycleSeason" ("userId");
CREATE INDEX "ix_TeamSquad_teamCycleSeasonId"     ON "TeamSquad" ("teamCycleSeasonId");
CREATE INDEX "ix_TeamSquad_playerId"              ON "TeamSquad" ("playerId");
CREATE INDEX "ix_Match_homeTeamId"                ON "Match" ("homeTeamId");
CREATE INDEX "ix_Match_awayTeamId"                ON "Match" ("awayTeamId");
CREATE INDEX "ix_Match_typeId"                    ON "Match" ("typeId");
CREATE INDEX "ix_MatchPlayerStat_matchId"         ON "MatchPlayerStat" ("matchId");
CREATE INDEX "ix_MatchPlayerStat_playerId"        ON "MatchPlayerStat" ("playerId");
CREATE INDEX "ix_MatchPlayerStat_teamSquadId"     ON "MatchPlayerStat" ("teamSquadId");
CREATE INDEX "ix_MatchPlayerStat_sourceFile"      ON "MatchPlayerStat" ("sourceFile");
CREATE INDEX "ix_File_parentId"                   ON "File" ("parentId");
CREATE INDEX "ix_File_sourceGameId"               ON "File" ("sourceGameId");
CREATE INDEX "ix_File_teamCycleSeasonId"          ON "File" ("teamCycleSeasonId");
CREATE INDEX "ix_UserFeature_userId"              ON "UserFeature" ("userId");
CREATE INDEX "ix_UserFeature_featureId"           ON "UserFeature" ("featureId");

COMMIT;
