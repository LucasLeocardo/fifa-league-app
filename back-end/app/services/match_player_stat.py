"""Camada de servico de MatchPlayerStat (confirmacao de ratings OCR)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.player_name_match import pick_best_player_match
from app.models.match_player_stat import MatchPlayerStat
from app.repositories.file import FileRepository
from app.repositories.match_player_stat import MatchPlayerStatRepository
from app.repositories.player import PlayerRepository
from app.schemas.file import (
    ConfirmPlayerStatItem,
    ConfirmPlayerStatsPayload,
    MatchPlayerStatRead,
)


class MatchPlayerStatService:
    def __init__(
        self,
        db: AsyncSession,
        player_repository: PlayerRepository,
        file_repository: FileRepository,
        match_player_stat_repository: MatchPlayerStatRepository,
    ) -> None:
        self.db = db
        self.player_repository = player_repository
        self.file_repository = file_repository
        self.match_player_stat_repository = match_player_stat_repository

    async def confirm_from_ocr(
        self, payload: ConfirmPlayerStatsPayload
    ) -> list[MatchPlayerStatRead]:
        """Resolve jogadores por nome, grava MatchPlayerStat e marca o File.

        Se qualquer nome nao resolver para exatamente um jogador confiavel,
        aborta com BadRequestError (sem gravar nada).
        """
        file_row = await self.file_repository.get_by_id(payload.file_id)
        if file_row is None:
            raise NotFoundError("Arquivo (fileId) nao encontrado.")

        squad_cache: dict[
            uuid.UUID, list[tuple[uuid.UUID, str, uuid.UUID]]
        ] = {}

        pending_rows: list[
            tuple[ConfirmPlayerStatItem, uuid.UUID, str, uuid.UUID | None]
        ] = []
        unresolved: list[str] = []

        for item in payload.players:
            tcs_id = item.team_cycle_season_id
            if tcs_id not in squad_cache:
                squad_cache[tcs_id] = list(
                    await self.player_repository.list_squad_players_by_team_cycle_season(
                        tcs_id
                    )
                )

            squad_players = squad_cache[tcs_id]
            match = pick_best_player_match(item.player_name, list(squad_players))

            player_id: uuid.UUID | None = None
            player_name: str | None = None
            team_squad_id: uuid.UUID | None = None

            if match is not None:
                player_id, player_name, team_squad_id = match
            else:
                candidates = list(
                    await self.player_repository.list_name_candidates(
                        item.player_name
                    )
                )
                global_match = pick_best_player_match(
                    item.player_name, list(candidates)
                )
                if global_match is None:
                    unresolved.append(item.player_name)
                    continue

                player_id, player_name = global_match
                team_squad_id = await self.player_repository.get_team_squad_id(
                    team_cycle_season_id=tcs_id,
                    player_id=player_id,
                )

            if player_id is None or player_name is None:
                unresolved.append(item.player_name)
                continue

            pending_rows.append((item, player_id, player_name, team_squad_id))

        if unresolved:
            names = ", ".join(f'"{name}"' for name in unresolved)
            raise BadRequestError(
                f"Nao foi possivel identificar o(s) jogador(es): {names}."
            )

        seen_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
        duplicate_names: list[str] = []
        for item, player_id, player_name, _team_squad_id in pending_rows:
            pair = (item.source_game_id, player_id)
            if pair in seen_pairs:
                duplicate_names.append(player_name)
            else:
                seen_pairs.add(pair)

        if duplicate_names:
            names = ", ".join(f'"{name}"' for name in duplicate_names)
            raise BadRequestError(
                "Ha jogadores duplicados na lista para a mesma partida: "
                f"{names}."
            )

        existing_pairs = (
            await self.match_player_stat_repository.list_existing_match_player_pairs(
                list(seen_pairs)
            )
        )
        if existing_pairs:
            conflict_names = [
                player_name
                for item, player_id, player_name, _ in pending_rows
                if (item.source_game_id, player_id) in existing_pairs
            ]
            names = ", ".join(f'"{name}"' for name in conflict_names)
            raise BadRequestError(
                "Ja existem estatisticas nesta partida para: "
                f"{names}. Remova a duplicata ou ajuste os nomes."
            )

        entities = [
            MatchPlayerStat(
                match_id=item.source_game_id,
                player_id=player_id,
                team_squad_id=team_squad_id,
                source_file=payload.file_id,
                goals=item.goals,
                assists=item.assists,
                rating=item.average_rating,
            )
            for item, player_id, _player_name, team_squad_id in pending_rows
        ]

        created = await self.match_player_stat_repository.create_many(
            entities, commit=False
        )
        updated = await self.file_repository.mark_processed(
            payload.file_id, commit=False
        )
        if updated is None:
            await self.db.rollback()
            raise NotFoundError("Arquivo (fileId) nao encontrado.")

        await self.db.commit()

        return [
            MatchPlayerStatRead(
                match_player_stat_id=entity.id,
                match_id=entity.match_id,
                player_id=entity.player_id,
                player_name=player_name,
                team_squad_id=entity.team_squad_id,
                source_file=entity.source_file,
                goals=entity.goals,
                assists=entity.assists,
                rating=entity.rating,
            )
            for entity, (_item, _pid, player_name, _tsid) in zip(
                created, pending_rows, strict=True
            )
        ]
