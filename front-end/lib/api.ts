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

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

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
