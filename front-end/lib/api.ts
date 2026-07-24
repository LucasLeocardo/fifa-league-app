export type LoginResponse = {
  accessToken: string;
  refreshToken: string;
  isAdmin: boolean;
  name: string;
  coachName: string | null;
  numberOfTitles: number;
};

export type RegisterResponse = {
  id: string;
  name: string;
  email: string;
  coachName: string | null;
  authUserId: string | null;
  numberOfTitles: number;
  isAdmin: boolean;
  createdAt: string;
};

export type TeamStanding = {
  teamCycleSeasonId: string;
  cycleSeasonId: string;
  teamId: string;
  teamName: string;
  userId: string;
  coachName: string | null;
  points: number;
  wins: number;
  draws: number;
  losses: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
};

export type StandingsResponse = {
  cycleSeasonId: string;
  standings: TeamStanding[];
};

export type CycleSeason = {
  cycleSeasonId: string;
  cycleName: string;
  seasonName: string;
  isCurrentSeason: boolean;
};

export type SquadPlayer = {
  teamSquadId: string;
  playerName: string;
  overall: number | null;
  playerCost: number | null;
  currency: string | null;
  shirtNumber: number | null;
  positions: string[];
  gamesPlayed: number;
  totalGoals: number;
  totalAssists: number;
  averageRating: number | null;
};

export type SquadResponse = {
  teamCycleSeasonId: string;
  players: SquadPlayer[];
};

export type TeamSquadEntry = {
  teamSquadId: string;
  shirtNumber: number | null;
};

export type TeamCycleSeason = {
  teamCycleSeasonId: string;
  teamName: string;
  isMyTeam: boolean;
};

export type LeaderboardGoalsEntry = {
  playerName: string;
  teamName: string;
  totalGoals: number;
};

export type LeaderboardAssistsEntry = {
  playerName: string;
  teamName: string;
  totalAssists: number;
};

export type LeaderboardRatingsEntry = {
  playerName: string;
  teamName: string;
  averageRating: number;
  gamesPlayed: number;
};

export type LeaderboardResponse = {
  cycleSeasonId: string;
  goals: LeaderboardGoalsEntry[];
  assists: LeaderboardAssistsEntry[];
  ratings: LeaderboardRatingsEntry[];
};

export type Position = {
  id: string;
  code: string;
};

export type RefreshResponse = {
  accessToken: string;
  refreshToken: string;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new ApiError(500, "NEXT_PUBLIC_API_URL nao configurada.");
  }
  return base.replace(/\/$/, "");
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();
    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data
    ) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (typeof item === "object" && item !== null && "msg" in item) {
              return String((item as { msg: unknown }).msg);
            }
            return String(item);
          })
          .join(" ");
      }
    }
  } catch {
    // ignora JSON invalido
  }
  return "Erro inesperado na API.";
}

function hasAuthorizationHeader(headers: HeadersInit | undefined): boolean {
  if (!headers) return false;
  if (headers instanceof Headers) {
    return Boolean(headers.get("Authorization") ?? headers.get("authorization"));
  }
  if (Array.isArray(headers)) {
    return headers.some(([key]) => key.toLowerCase() === "authorization");
  }
  const record = headers as Record<string, string>;
  return Boolean(record.Authorization ?? record.authorization);
}

function withAccessToken(
  headers: HeadersInit | undefined,
  accessToken: string,
): HeadersInit {
  return {
    ...((headers as Record<string, string> | undefined) ?? {}),
    Authorization: `Bearer ${accessToken}`,
  };
}

type RequestOptions = {
  /** Evita loop de refresh (retry ja feito ou rota de auth). */
  skipAuthRetry?: boolean;
};

let refreshInFlight: Promise<RefreshResponse> | null = null;

async function refreshSessionTokens(): Promise<RefreshResponse> {
  const { useAuthStore } = await import("@/store/auth");
  const { refreshToken, setTokens, clearSession } = useAuthStore.getState();

  if (!refreshToken) {
    clearSession();
    throw new ApiError(401, "Sessao expirada. Faca login novamente.");
  }

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refreshToken }),
        });
        if (!response.ok) {
          throw new ApiError(response.status, await readErrorMessage(response));
        }
        const tokens = (await response.json()) as RefreshResponse;
        setTokens(tokens.accessToken, tokens.refreshToken);
        return tokens;
      } catch (err) {
        clearSession();
        throw err;
      } finally {
        refreshInFlight = null;
      }
    })();
  }

  return refreshInFlight;
}

function isAuthPath(path: string): boolean {
  return (
    path.startsWith("/api/v1/auth/login") ||
    path.startsWith("/api/v1/auth/register") ||
    path.startsWith("/api/v1/auth/refresh")
  );
}

async function request<T>(
  path: string,
  init?: RequestInit,
  options?: RequestOptions,
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (
    response.status === 401 &&
    !options?.skipAuthRetry &&
    !isAuthPath(path) &&
    hasAuthorizationHeader(init?.headers)
  ) {
    const tokens = await refreshSessionTokens();
    return request<T>(
      path,
      {
        ...init,
        headers: withAccessToken(init?.headers, tokens.accessToken),
      },
      { skipAuthRetry: true },
    );
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Renova accessToken e refreshToken. O refreshToken antigo deixa de valer.
 */
export function refresh(refreshToken: string): Promise<RefreshResponse> {
  return request<RefreshResponse>(
    "/api/v1/auth/refresh",
    {
      method: "POST",
      body: JSON.stringify({ refreshToken }),
    },
    { skipAuthRetry: true },
  );
}

export function register(
  name: string,
  email: string,
  password: string,
): Promise<RegisterResponse> {
  return request<RegisterResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export function logout(accessToken: string): Promise<void> {
  return request<void>("/api/v1/auth/logout", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Classificacao do torneio. Sem cycleSeasonId, o back-end usa a temporada
 * aberta (CycleSeason com endDate nulo).
 */
export function getStandings(
  accessToken: string,
  cycleSeasonId?: string,
): Promise<StandingsResponse> {
  const query = cycleSeasonId
    ? `?cycleSeasonId=${encodeURIComponent(cycleSeasonId)}`
    : "";
  return request<StandingsResponse>(`/api/v1/standings${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Lista todas as CycleSeasons (com nome do ciclo e da temporada). A temporada
 * atual e a que possui isCurrentSeason igual a true (endDate nulo no back-end).
 */
export function getCycleSeasons(accessToken: string): Promise<CycleSeason[]> {
  return request<CycleSeason[]>("/api/v1/cycle-seasons", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Elenco (TeamSquad). Sem teamCycleSeasonId, o back-end usa o TeamCycleSeason
 * do usuario (do token) na temporada atual (CycleSeason com endDate nulo).
 */
export function getSquad(
  accessToken: string,
  teamCycleSeasonId?: string,
): Promise<SquadResponse> {
  const query = teamCycleSeasonId
    ? `?teamCycleSeasonId=${encodeURIComponent(teamCycleSeasonId)}`
    : "";
  return request<SquadResponse>(`/api/v1/squad${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * TeamCycleSeasons de uma temporada. Sem cycleSeasonId, o back-end usa a
 * temporada atual (CycleSeason com endDate nulo). isMyTeam indica o time do
 * usuario logado.
 */
export function getTeamCycleSeasons(
  accessToken: string,
  cycleSeasonId?: string,
): Promise<TeamCycleSeason[]> {
  const query = cycleSeasonId
    ? `?cycleSeasonId=${encodeURIComponent(cycleSeasonId)}`
    : "";
  return request<TeamCycleSeason[]>(`/api/v1/team-cycle-seasons${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Atualiza o numero da camisa (shirtNumber) de uma linha de TeamSquad.
 */
export function updateShirtNumber(
  accessToken: string,
  teamSquadId: string,
  shirtNumber: number,
): Promise<TeamSquadEntry> {
  return request<TeamSquadEntry>(
    `/api/v1/squad/${encodeURIComponent(teamSquadId)}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ shirtNumber }),
    },
  );
}

/**
 * Leaderboard de gols, assistencias e notas medias. Sem cycleSeasonId, o
 * back-end usa a temporada atual (CycleSeason com endDate nulo). positionIds
 * filtra por posicoes; vazio/omitido nao filtra.
 */
export function getLeaderboard(
  accessToken: string,
  cycleSeasonId?: string,
  positionIds?: string[],
): Promise<LeaderboardResponse> {
  const params = new URLSearchParams();
  if (cycleSeasonId) {
    params.set("cycleSeasonId", cycleSeasonId);
  }
  for (const positionId of positionIds ?? []) {
    params.append("positionIds", positionId);
  }
  const query = params.toString() ? `?${params.toString()}` : "";
  return request<LeaderboardResponse>(`/api/v1/leaderboard${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Lista todas as posicoes (id e code).
 */
export function getPositions(accessToken: string): Promise<Position[]> {
  return request<Position[]>("/api/v1/positions", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export type MatchResult = {
  matchId: string;
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number | null;
  awayScore: number | null;
  matchTypeName: string | null;
};

export type MatchType = {
  matchTypeId: string;
  name: string;
};

export type CreateMatchPayload = {
  homeTeamId: string;
  awayTeamId: string;
  matchTypeId: string;
  homeScore: number;
  awayScore: number;
};

/**
 * Partidas de um TeamCycleSeason (mandante ou visitante). Sem
 * teamCycleSeasonId, o back-end usa o time do usuario na temporada atual.
 */
export function getMatches(
  accessToken: string,
  teamCycleSeasonId?: string,
): Promise<MatchResult[]> {
  const query = teamCycleSeasonId
    ? `?teamCycleSeasonId=${encodeURIComponent(teamCycleSeasonId)}`
    : "";
  return request<MatchResult[]>(`/api/v1/matches${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Lista todos os MatchTypes (matchTypeId e name).
 */
export function getMatchTypes(accessToken: string): Promise<MatchType[]> {
  return request<MatchType[]>("/api/v1/match-types", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Cria uma nova partida.
 */
export function createMatch(
  accessToken: string,
  payload: CreateMatchPayload,
): Promise<MatchResult> {
  return request<MatchResult>("/api/v1/matches", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
}

export type PlayerSearchResult = {
  playerId: string;
  playerName: string;
  overall: number | null;
  positions: string[];
  positionIds: string[];
  teamName: string | null;
  teamCycleSeasonId: string | null;
};

/**
 * Busca jogadores pelo nome (contains / ILIKE no back-end).
 */
export function searchPlayers(
  accessToken: string,
  name: string,
): Promise<PlayerSearchResult[]> {
  const query = `?name=${encodeURIComponent(name)}`;
  return request<PlayerSearchResult[]>(`/api/v1/players${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

/**
 * Detalhe de um jogador pelo id.
 */
export function getPlayer(
  accessToken: string,
  playerId: string,
): Promise<PlayerSearchResult> {
  return request<PlayerSearchResult>(
    `/api/v1/players/${encodeURIComponent(playerId)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );
}

export type CreatePlayerPayload = {
  name: string;
  overall: number;
  positionIds: string[];
};

/**
 * Cadastra um novo jogador (admin).
 */
export function createPlayer(
  accessToken: string,
  payload: CreatePlayerPayload,
): Promise<PlayerSearchResult> {
  return request<PlayerSearchResult>("/api/v1/players", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
}

export type UpdatePlayerPayload = {
  name: string;
  overall: number;
  positionIds: string[];
  teamCycleSeasonId?: string | null;
};

/**
 * Atualiza um jogador existente (admin).
 */
export function updatePlayer(
  accessToken: string,
  playerId: string,
  payload: UpdatePlayerPayload,
): Promise<PlayerSearchResult> {
  return request<PlayerSearchResult>(
    `/api/v1/players/${encodeURIComponent(playerId)}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    },
  );
}

/**
 * Remove um jogador (somente usuario Leocardo + admin).
 */
export function deletePlayer(
  accessToken: string,
  playerId: string,
): Promise<void> {
  return request<void>(`/api/v1/players/${encodeURIComponent(playerId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
