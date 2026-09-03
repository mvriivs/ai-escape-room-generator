"""
Functie complexa de fitness pentru optimizarea nivelurilor Escape Room.

Fitness-ul combina mai multe criterii:

    1. apropierea scorului global de tinta;
    2. apropierea caracteristicilor individuale de valorile tinta;
    3. complexitatea structurala;
    4. interactiuni intre caracteristici;
    5. penalizarea dezechilibrului.

Cu cat fitness-ul este mai mare, cu atat nivelul este considerat
mai potrivit pentru dificultatea ceruta.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from difficulty import DifficultyScore


@dataclass
class FitnessBreakdown:
    """
    Descompunerea completa a fitness-ului.

    Este utila pentru:
        - debugging;
        - teste;
        - grafice;
        - explicarea algoritmului genetic in proiect.
    """

    total_similarity: float
    feature_similarity: float
    structural_complexity: float
    interaction_bonus: float
    balance_penalty: float
    final_fitness: float

    def as_dict(self) -> dict:
        return {
            "total_similarity": round(self.total_similarity, 4),
            "feature_similarity": round(self.feature_similarity, 4),
            "structural_complexity": round(self.structural_complexity, 4),
            "interaction_bonus": round(self.interaction_bonus, 4),
            "balance_penalty": round(self.balance_penalty, 4),
            "final_fitness": round(self.final_fitness, 4),
        }


# ---------------------------------------------------------------------
# VALORI TINTA
# ---------------------------------------------------------------------

TARGET_FEATURES = {
    "easy": {
        "path_length": 12.0,
        "enemies": 1.0,
        "traps": 1.0,
        "treasures": 2.0,
        "wall_density": 0.45,
        "dead_end_ratio": 0.20,
    },

    "medium": {
        "path_length": 25.0,
        "enemies": 3.0,
        "traps": 3.0,
        "treasures": 3.0,
        "wall_density": 0.50,
        "dead_end_ratio": 0.25,
    },

    "hard": {
        "path_length": 40.0,
        "enemies": 6.0,
        "traps": 6.0,
        "treasures": 4.0,
        "wall_density": 0.55,
        "dead_end_ratio": 0.30,
    },
}


# ---------------------------------------------------------------------
# TOLERANTE
# ---------------------------------------------------------------------

FEATURE_TOLERANCES = {
    "path_length": 25.0,
    "enemies": 6.0,
    "traps": 6.0,
    "treasures": 4.0,
    "wall_density": 0.25,
    "dead_end_ratio": 0.20,
}


# ---------------------------------------------------------------------
# PONDERI CARACTERISTICI
# ---------------------------------------------------------------------

FEATURE_WEIGHTS = {
    "path_length": 0.25,
    "enemies": 0.18,
    "traps": 0.18,
    "treasures": 0.09,
    "wall_density": 0.15,
    "dead_end_ratio": 0.15,
}


# ---------------------------------------------------------------------
# PONDERI FITNESS
# ---------------------------------------------------------------------

TOTAL_SCORE_WEIGHT = 0.40
FEATURE_WEIGHT = 0.30
STRUCTURE_WEIGHT = 0.15
INTERACTION_WEIGHT = 0.15

BALANCE_PENALTY_WEIGHT = 0.15


def _similarity(
    value: float,
    target: float,
    tolerance: float,
) -> float:
    """
    Similaritate exponentiala.

    1.0 -> valoarea este exact tinta.
    0.0 -> valoarea este foarte departe de tinta.
    """

    if tolerance <= 0:
        return 1.0 if value == target else 0.0

    difference = abs(value - target)

    return float(
        np.exp(
            -((difference / tolerance) ** 2)
        )
    )


def _feature_similarity(
    score: DifficultyScore,
    difficulty: str,
) -> float:
    """
    Compara caracteristicile nivelului cu valorile tinta
    pentru dificultatea ceruta.
    """

    if difficulty not in TARGET_FEATURES:
        raise ValueError(
            f"Dificultate necunoscuta: {difficulty}. "
            f"Foloseste easy, medium sau hard."
        )

    targets = TARGET_FEATURES[difficulty]

    values = {
        "path_length": float(score.path_length),
        "enemies": float(score.enemy_count),
        "traps": float(score.trap_count),
        "treasures": float(score.treasure_count),
        "wall_density": float(score.wall_density),
        "dead_end_ratio": float(score.dead_end_ratio),
    }

    total = 0.0

    for name, weight in FEATURE_WEIGHTS.items():

        similarity = _similarity(
            values[name],
            targets[name],
            FEATURE_TOLERANCES[name],
        )

        total += weight * similarity

    return float(total)


def _structural_complexity(
    score: DifficultyScore,
) -> float:
    """
    Masoara complexitatea structurala a nivelului.

    Se folosesc:
        - lungimea traseului;
        - inamici;
        - capcane;
        - comori;
        - densitatea peretilor;
        - fundaturi.
    """

    path_component = min(
        score.path_length / 40.0,
        1.0,
    )

    enemy_component = min(
        score.enemy_count / 10.0,
        1.0,
    )

    trap_component = min(
        score.trap_count / 10.0,
        1.0,
    )

    treasure_component = min(
        score.treasure_count / 6.0,
        1.0,
    )

    wall_component = min(
        score.wall_density / 0.60,
        1.0,
    )

    dead_end_component = min(
        score.dead_end_ratio / 0.40,
        1.0,
    )

    components = np.array(
        [
            path_component,
            enemy_component,
            trap_component,
            treasure_component,
            wall_component,
            dead_end_component,
        ],
        dtype=float,
    )

    mean_value = float(
        np.mean(components)
    )

    variation = float(
        np.std(components)
    )

    balance = max(
        0.0,
        1.0 - variation * 2.0,
    )

    return float(
        0.65 * mean_value
        + 0.35 * balance
    )


def _interaction_bonus(
    score: DifficultyScore,
) -> float:
    """
    Bonus pentru combinatii care pot produce dificultate suplimentara.

    Exemple:
        traseu lung + inamici;
        traseu lung + capcane;
        capcane + pereti;
        inamici + pereti;
        fundaturi + traseu lung.
    """

    path_norm = min(
        score.path_length / 40.0,
        1.0,
    )

    enemies_norm = min(
        score.enemy_count / 10.0,
        1.0,
    )

    traps_norm = min(
        score.trap_count / 10.0,
        1.0,
    )

    wall_norm = min(
        score.wall_density / 0.60,
        1.0,
    )

    dead_end_norm = min(
        score.dead_end_ratio / 0.40,
        1.0,
    )

    long_path_obstacles = (
        path_norm
        * (
            0.5 * enemies_norm
            + 0.5 * traps_norm
        )
    )

    trap_wall_interaction = (
        traps_norm * wall_norm
    )

    enemy_wall_interaction = (
        enemies_norm * wall_norm
    )

    path_dead_end_interaction = (
        path_norm * dead_end_norm
    )

    interaction = (
        0.35 * long_path_obstacles
        + 0.25 * trap_wall_interaction
        + 0.20 * enemy_wall_interaction
        + 0.20 * path_dead_end_interaction
    )

    return float(
        min(interaction, 1.0)
    )


def _balance_penalty(
    score: DifficultyScore,
) -> float:
    """
    Penalizeaza nivelurile in care o singura caracteristica domina
    puternic restul.
    """

    values = np.array(
        [
            min(score.path_length / 40.0, 1.0),
            min(score.enemy_count / 10.0, 1.0),
            min(score.trap_count / 10.0, 1.0),
            min(score.treasure_count / 6.0, 1.0),
            min(score.wall_density / 0.60, 1.0),
            min(score.dead_end_ratio / 0.40, 1.0),
        ],
        dtype=float,
    )

    spread = float(
        np.max(values) - np.min(values)
    )

    return float(
        min(spread, 1.0)
    )


def complex_fitness(
    score: DifficultyScore,
    target_score: float,
    difficulty: str,
) -> FitnessBreakdown:
    """
    Calculeaza fitness-ul complex.

    Parameters
    ----------
    score:
        Scorul calculat pentru nivel.

    target_score:
        Scorul global dorit.

    difficulty:
        easy / medium / hard.
    """

    if difficulty not in TARGET_FEATURES:
        raise ValueError(
            f"Dificultate necunoscuta: {difficulty}"
        )

    # 1. Similaritatea scorului global.
    total_similarity = _similarity(
        score.raw_score,
        target_score,
        max(
            target_score * 0.20,
            10.0,
        ),
    )

    # 2. Similaritatea caracteristicilor.
    feature_similarity = _feature_similarity(
        score,
        difficulty,
    )

    # 3. Complexitatea structurala.
    structural_complexity = _structural_complexity(
        score
    )

    # 4. Bonus interactiuni.
    interaction_bonus = _interaction_bonus(
        score
    )

    # 5. Penalizare dezechilibru.
    balance_penalty = _balance_penalty(
        score
    )

    # 6. Fitness final.
    final_fitness = (
        TOTAL_SCORE_WEIGHT * total_similarity
        + FEATURE_WEIGHT * feature_similarity
        + STRUCTURE_WEIGHT * structural_complexity
        + INTERACTION_WEIGHT * interaction_bonus
        - BALANCE_PENALTY_WEIGHT * balance_penalty
    )

    return FitnessBreakdown(
        total_similarity=float(total_similarity),
        feature_similarity=float(feature_similarity),
        structural_complexity=float(structural_complexity),
        interaction_bonus=float(interaction_bonus),
        balance_penalty=float(balance_penalty),
        final_fitness=float(final_fitness),
    )