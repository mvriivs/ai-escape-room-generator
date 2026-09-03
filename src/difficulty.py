"""
Scor de dificultate pentru un nivel generat si validat.

Scorul combina:
    - lungimea traseului optim;
    - numarul de inamici;
    - numarul de capcane;
    - numarul de comori;
    - densitatea peretilor;
    - proportia de fundaturi.

Scorul este calculat printr-o suma ponderata.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from grid import Cell, Grid, Position
from solver import ValidationResult


# Ordinea caracteristicilor trebuie sa corespunda cu WEIGHTS.
FEATURE_NAMES = (
    "path_length",
    "enemies",
    "traps",
    "treasures",
    "wall_density",
    "dead_end_ratio",
)


# Ponderile caracteristicilor.
WEIGHTS = np.array(
    [
        1.0,   # path_length
        4.0,   # enemies
        3.0,   # traps
        1.5,   # treasures
        18.0,  # wall_density
        14.0,  # dead_end_ratio
    ]
)


# Praguri pentru clasificarea dificultatii.
EASY_MAX = 77.5
MEDIUM_MAX = 140.0


# Scorurile tinta folosite de algoritmul genetic.
CATEGORY_TARGET_SCORE = {
    "easy": 60.0,
    "medium": 109.0,
    "hard": 191.0,
}


@dataclass
class DifficultyScore:
    """
    Contine toate caracteristicile care participa la scorul de dificultate.
    """

    path_length: int
    enemy_count: int
    trap_count: int
    treasure_count: int
    wall_density: float
    dead_end_ratio: float
    raw_score: float

    @property
    def category(self) -> str:
        """
        Determina categoria nivelului pe baza scorului final.
        """

        if self.raw_score <= EASY_MAX:
            return "easy"

        if self.raw_score <= MEDIUM_MAX:
            return "medium"

        return "hard"

    def as_dict(self) -> dict:
        """
        Returneaza scorul sub forma de dictionar.
        """

        return {
            "path_length": self.path_length,
            "enemy_count": self.enemy_count,
            "trap_count": self.trap_count,
            "treasure_count": self.treasure_count,
            "wall_density": round(self.wall_density, 4),
            "dead_end_ratio": round(self.dead_end_ratio, 4),
            "raw_score": round(self.raw_score, 2),
            "category": self.category,
        }


def _dead_end_ratio(grid: Grid) -> float:
    """
    Calculeaza proportia celulelor accesibile care sunt fundaturi.

    O fundatura este o celula accesibila care are cel mult un vecin
    accesibil.
    """

    walkable_positions = [
        Position(x, y)
        for y in range(grid.height)
        for x in range(grid.width)
        if grid.is_walkable(Position(x, y))
    ]

    if not walkable_positions:
        return 0.0

    dead_ends = sum(
        1
        for pos in walkable_positions
        if sum(
            1
            for neighbor in grid.neighbors(pos)
            if grid.is_walkable(neighbor)
        ) <= 1
    )

    return dead_ends / len(walkable_positions)


def compute_difficulty_score(
    grid: Grid,
    result: ValidationResult,
) -> DifficultyScore:
    """
    Calculeaza scorul de dificultate pentru un nivel validat.
    """

    total_cells = grid.width * grid.height

    wall_density = (
        grid.count(Cell.WALL) / total_cells
        if total_cells
        else 0.0
    )

    dead_end_ratio = _dead_end_ratio(grid)

    features = np.array(
        [
            result.total_length,
            grid.count(Cell.ENEMY),
            grid.count(Cell.TRAP),
            grid.count(Cell.TREASURE),
            wall_density,
            dead_end_ratio,
        ],
        dtype=float,
    )

    raw_score = float(np.dot(features, WEIGHTS))

    return DifficultyScore(
        path_length=int(features[0]),
        enemy_count=int(features[1]),
        trap_count=int(features[2]),
        treasure_count=int(features[3]),
        wall_density=wall_density,
        dead_end_ratio=dead_end_ratio,
        raw_score=raw_score,
    )