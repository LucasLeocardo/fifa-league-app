"""Utilitarios de matching flexivel de nomes de jogadores (OCR -> Player)."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def normalize_player_name(name: str) -> str:
    """Normaliza nome para comparacao: sem acento, minusculo, so alfanumerico."""
    decomposed = unicodedata.normalize("NFD", name or "")
    without_marks = "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    )
    lowered = without_marks.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def name_similarity(query: str, candidate: str) -> float:
    """Score 0..1 entre nome do OCR e nome no banco.

    Combina igualdade normalizada, SequenceMatcher, tokens e sobrenome.
    """
    q = normalize_player_name(query)
    c = normalize_player_name(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0

    ratio = SequenceMatcher(None, q, c).ratio()
    q_tokens = q.split()
    c_tokens = c.split()

    if q_tokens and c_tokens:
        # Todos os tokens da query aparecem (ou sao prefixo) nos do candidato.
        matched_tokens = 0
        for qt in q_tokens:
            if any(qt == ct or qt.startswith(ct) or ct.startswith(qt) for ct in c_tokens):
                matched_tokens += 1
        token_score = matched_tokens / max(len(q_tokens), len(c_tokens))
        ratio = max(ratio, token_score)

        # Sobrenome (ultimo token) igual costuma ser forte no OCR (ex.: "F. Dimarco").
        if q_tokens[-1] == c_tokens[-1] and len(q_tokens[-1]) >= 3:
            ratio = max(ratio, 0.82)
            if len(q_tokens) == 1 or (
                len(q_tokens) >= 2 and len(q_tokens[0]) <= 2
            ):
                # "Dimarco" ou "F Dimarco" vs "Federico Dimarco"
                ratio = max(ratio, 0.88)

        # Query contida no candidato ou vice-versa.
        if q in c or c in q:
            ratio = max(ratio, 0.9)

    return min(ratio, 1.0)


def pick_best_player_match(
    query_name: str,
    candidates: list[tuple],
    *,
    min_score: float = 0.72,
    min_margin: float = 0.06,
) -> tuple | None:
    """Escolhe o melhor candidato (player_id, name, ...).

    Retorna None se nao houver match unico suficientemente bom.
    `candidates` deve ser lista de tuplas cujo indice 1 e o nome (ou
    use objetos com .name — aqui esperamos (player_id, player_name, ...)).
    """
    if not candidates:
        return None

    scored: list[tuple[float, tuple]] = []
    for candidate in candidates:
        player_name = candidate[1]
        score = name_similarity(query_name, player_name)
        scored.append((score, candidate))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]
    if best_score < min_score:
        return None

    if len(scored) > 1:
        second_score = scored[1][0]
        if best_score < 0.999 and (best_score - second_score) < min_margin:
            return None

    return best
