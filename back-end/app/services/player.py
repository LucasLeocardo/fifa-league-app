"""Camada de servico de Player."""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.repositories.player import PlayerRepository, PlayerSearchRow
from app.schemas.player import PlayerCreate, PlayerSearchRead, PlayerUpdate

PLAYER_DELETE_ALLOWED_NAME = "Leocardo"


class PlayerService:
    def __init__(self, repository: PlayerRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_read(row: PlayerSearchRow) -> PlayerSearchRead:
        return PlayerSearchRead(
            player_id=row.player_id,
            player_name=row.player_name,
            overall=row.overall,
            positions=list(row.positions or []),
            position_ids=list(row.position_ids or []),
            team_name=row.team_name,
            team_cycle_season_id=row.team_cycle_season_id,
        )

    async def search_by_name(self, name: str) -> list[PlayerSearchRead]:
        """Busca jogadores por trecho do nome (contains / ILIKE)."""
        trimmed = name.strip()
        if not trimmed:
            raise BadRequestError("Informe um nome para buscar jogadores.")

        rows = await self.repository.search_by_name(trimmed)
        return [self._to_read(row) for row in rows]

    async def get_player(self, player_id: uuid.UUID) -> PlayerSearchRead:
        """Retorna o detalhe de um jogador pelo id."""
        row = await self.repository.get_detail(player_id)
        if row is None:
            raise NotFoundError("Jogador nao encontrado.")
        return self._to_read(row)

    async def create_player(self, payload: PlayerCreate) -> PlayerSearchRead:
        """Cadastra jogador com overall (lookup por value) e posicoes."""
        trimmed_name = payload.name.strip()
        if not trimmed_name:
            raise BadRequestError("Informe o nome do jogador.")

        if await self.repository.exists_by_name(trimmed_name):
            raise ConflictError(
                f'Ja existe um jogador com o nome "{trimmed_name}".'
            )

        overall = await self.repository.get_overall_by_value(payload.overall)
        if overall is None:
            raise NotFoundError(
                f"Overall com value={payload.overall} nao encontrado."
            )

        unique_position_ids = list(dict.fromkeys(payload.position_ids))
        found_by_id = await self._validate_positions(unique_position_ids)

        player = await self.repository.create(
            name=trimmed_name,
            overall_id=overall.id,
            position_ids=unique_position_ids,
        )

        position_codes = [found_by_id[pid] for pid in unique_position_ids]
        return PlayerSearchRead(
            player_id=player.id,
            player_name=player.name,
            overall=overall.value,
            positions=position_codes,
            position_ids=unique_position_ids,
            team_name=None,
            team_cycle_season_id=None,
        )

    async def update_player(
        self, player_id: uuid.UUID, payload: PlayerUpdate
    ) -> PlayerSearchRead:
        """Atualiza nome, overall, posicoes e opcionalmente o time atual."""
        player = await self.repository.get_by_id(player_id)
        if player is None:
            raise NotFoundError("Jogador nao encontrado.")

        trimmed_name = payload.name.strip()
        if not trimmed_name:
            raise BadRequestError("Informe o nome do jogador.")

        if await self.repository.exists_by_name(
            trimmed_name, exclude_player_id=player_id
        ):
            raise ConflictError(
                f'Ja existe um jogador com o nome "{trimmed_name}".'
            )

        overall = await self.repository.get_overall_by_value(payload.overall)
        if overall is None:
            raise NotFoundError(
                f"Overall com value={payload.overall} nao encontrado."
            )

        unique_position_ids = list(dict.fromkeys(payload.position_ids))
        await self._validate_positions(unique_position_ids)

        team_cycle_season_id = payload.team_cycle_season_id
        if team_cycle_season_id is not None:
            tcs = await self.repository.get_team_cycle_season_in_current_season(
                team_cycle_season_id
            )
            if tcs is None:
                raise NotFoundError(
                    "TeamCycleSeason nao encontrado na temporada atual."
                )

        await self.repository.update(
            player=player,
            name=trimmed_name,
            overall_id=overall.id,
            position_ids=unique_position_ids,
            team_cycle_season_id=team_cycle_season_id,
        )

        row = await self.repository.get_detail(player_id)
        if row is None:
            raise NotFoundError("Jogador atualizado nao encontrado.")
        return self._to_read(row)

    async def delete_player(
        self, player_id: uuid.UUID, requester_name: str
    ) -> None:
        """Remove o jogador e vinculos em MatchPlayerStat, PlayerPosition e TeamSquad.

        Somente o usuario com name == Leocardo pode executar a exclusao.
        """
        if requester_name != PLAYER_DELETE_ALLOWED_NAME:
            raise ForbiddenError(
                "Apenas o usuario Leocardo pode deletar jogadores."
            )

        player = await self.repository.get_by_id(player_id)
        if player is None:
            raise NotFoundError("Jogador nao encontrado.")
        await self.repository.delete(player)

    async def _validate_positions(
        self, position_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str]:
        found_positions = await self.repository.list_position_codes_by_ids(
            position_ids
        )
        found_by_id = {row.id: row.code for row in found_positions}
        missing = [str(pid) for pid in position_ids if pid not in found_by_id]
        if missing:
            raise NotFoundError(
                "Posicoes nao encontradas: " + ", ".join(missing)
            )
        return found_by_id
