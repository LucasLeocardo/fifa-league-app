-- =============================================================================
-- View: TeamStandings
-- Classificacao por TeamCycleSeason (time + temporada + tecnico).
--
-- Uso:
--   SELECT *
--   FROM "TeamStandings"
--   WHERE "cycleSeasonId" = '<uuid>'
--   ORDER BY "points" DESC, "goalDifference" DESC, "goalsFor" DESC, "wins" DESC;
--
-- Premissas:
--   * Match.homeTeamId / awayTeamId apontam para TeamCycleSeason.id
--   * So entram partidas com homeScore e awayScore preenchidos
--   * Vitoria = 3 pts, empate = 1 pt, derrota = 0 pt
--   * Times sem jogos aparecem com zeros
-- =============================================================================

CREATE OR REPLACE VIEW "TeamStandings" AS
WITH "PlayedMatch" AS (
    SELECT
        m."id",
        m."homeTeamId",
        m."awayTeamId",
        m."homeScore",
        m."awayScore"
    FROM "Match" m
    WHERE m."homeScore" IS NOT NULL
      AND m."awayScore" IS NOT NULL
      AND m."homeTeamId" IS NOT NULL
      AND m."awayTeamId" IS NOT NULL
),
"TeamMatchResult" AS (
    -- Resultado sob a otica do mandante
    SELECT
        pm."homeTeamId" AS "teamCycleSeasonId",
        pm."homeScore"  AS "goalsFor",
        pm."awayScore"  AS "goalsAgainst",
        CASE
            WHEN pm."homeScore" > pm."awayScore" THEN 3
            WHEN pm."homeScore" = pm."awayScore" THEN 1
            ELSE 0
        END AS "points",
        CASE WHEN pm."homeScore" > pm."awayScore" THEN 1 ELSE 0 END AS "wins",
        CASE WHEN pm."homeScore" = pm."awayScore" THEN 1 ELSE 0 END AS "draws",
        CASE WHEN pm."homeScore" < pm."awayScore" THEN 1 ELSE 0 END AS "losses"
    FROM "PlayedMatch" pm

    UNION ALL

    -- Resultado sob a otica do visitante
    SELECT
        pm."awayTeamId" AS "teamCycleSeasonId",
        pm."awayScore"  AS "goalsFor",
        pm."homeScore"  AS "goalsAgainst",
        CASE
            WHEN pm."awayScore" > pm."homeScore" THEN 3
            WHEN pm."awayScore" = pm."homeScore" THEN 1
            ELSE 0
        END AS "points",
        CASE WHEN pm."awayScore" > pm."homeScore" THEN 1 ELSE 0 END AS "wins",
        CASE WHEN pm."awayScore" = pm."homeScore" THEN 1 ELSE 0 END AS "draws",
        CASE WHEN pm."awayScore" < pm."homeScore" THEN 1 ELSE 0 END AS "losses"
    FROM "PlayedMatch" pm
)
SELECT
    tcs."id"            AS "teamCycleSeasonId",
    tcs."cycleSeasonId" AS "cycleSeasonId",
    t."id"              AS "teamId",
    t."name"            AS "teamName",
    u."id"              AS "userId",
    u."coachName"       AS "coachName",
    COALESCE(SUM(r."points"), 0)::integer       AS "points",
    COALESCE(SUM(r."wins"), 0)::integer         AS "wins",
    COALESCE(SUM(r."draws"), 0)::integer        AS "draws",
    COALESCE(SUM(r."losses"), 0)::integer       AS "losses",
    COALESCE(SUM(r."goalsFor"), 0)::integer     AS "goalsFor",
    COALESCE(SUM(r."goalsAgainst"), 0)::integer AS "goalsAgainst",
    (
        COALESCE(SUM(r."goalsFor"), 0)
        - COALESCE(SUM(r."goalsAgainst"), 0)
    )::integer AS "goalDifference"
FROM "TeamCycleSeason" tcs
INNER JOIN "Team" t
    ON t."id" = tcs."teamId"
INNER JOIN "User" u
    ON u."id" = tcs."userId"
LEFT JOIN "TeamMatchResult" r
    ON r."teamCycleSeasonId" = tcs."id"
GROUP BY
    tcs."id",
    tcs."cycleSeasonId",
    t."id",
    t."name",
    u."id",
    u."coachName";
