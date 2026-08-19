"""
Scor de dificultate pentru un nivel generat si validat.

Combina mai multe caracteristici ale nivelului -- lungimea traseului optim,
numarul de inamici/capcane/comori, densitatea peretilor -- intr-un singur
numar, printr-o suma ponderata (numpy).

Acest scor e "tinta" pe care algoritmul genetic o va optimiza: fitness-ul
unui nivel candidat va fi cat de aproape e scorul lui de scorul cerut pentru
dificultatea aleasa de utilizator (Easy/Medium/Hard), nu doar "grid mai
mare = mai greu".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from grid import Cell, Grid
from solver import ValidationResult

# Ordinea caracteristicilor conteaza -- trebuie sa corespunda cu WEIGHTS.
FEATURE_NAMES = ("path_length", "enemies", "traps", "treasures", "wall_density")

# Ponderi: cat de mult conteaza fiecare caracteristica in scorul final.
# wall_density e o proportie (0..1), de-asta ponderea ei e mult mai mare ca
# sa fie comparabila cu celelalte caracteristici (numere intregi).
WEIGHTS = np.array([1.0, 4.0, 3.0, 1.5, 22.0])

# Praguri de categorie, calibrate empiric: am generat 50 de niveluri pentru
# fiecare dificultate (seed 0..49) si am masurat distributia scorurilor --
#   easy:   53 .. 67   (medie ~61)
#   medium: 90 .. 124  (medie ~111)
#   hard:   158 .. 222 (medie ~192)
# pragurile de mai jos sunt la mijlocul distantei dintre categorii vecine.
# Ajustabile daca se schimba DIFFICULTY_PRESETS din generator.py.
EASY_MAX = 78.0
MEDIUM_MAX = 141.0

# Scor "tinta" reprezentativ pentru fiecare dificultate (media masurata) --
# folosit de algoritmul genetic (genetic.py) ca obiectiv de optimizare, ca
# sa poata cauta un nivel cat mai aproape de mijlocul benzii, nu doar
# "undeva in interiorul ei".
CATEGORY_TARGET_SCORE = {"easy": 61.0, "medium": 111.0, "hard": 192.0}


@dataclass
class DifficultyScore:
    path_length: int
    enemy_count: int
    trap_count: int
    treasure_count: int
    wall_density: float
    raw_score: float

    @property
    def category(self) -> str:
        """Dificultatea "masurata" a nivelului, dedusa din scor (poate sa nu
        coincida cu dificultatea CERUTA -- de-asta avem nevoie de algoritmul
        genetic, ca sa le aducem cat mai aproape)."""
        if self.raw_score <= EASY_MAX:
            return "easy"
        if self.raw_score <= MEDIUM_MAX:
            return "medium"
        return "hard"

    def as_dict(self) -> dict:
        return {
            "path_length": self.path_length,
            "enemy_count": self.enemy_count,
            "trap_count": self.trap_count,
            "treasure_count": self.treasure_count,
            "wall_density": round(self.wall_density, 4),
            "raw_score": round(self.raw_score, 2),
            "category": self.category,
        }


def compute_difficulty_score(grid: Grid, result: ValidationResult) -> DifficultyScore:
    """Calculeaza scorul de dificultate al unui nivel deja validat.
    Presupune ca `result.is_valid` e True (scorul unui nivel invalid nu are
    sens - nu exista "lungime de traseu" daca nu exista traseu)."""
    total_cells = grid.width * grid.height
    wall_density = grid.count(Cell.WALL) / total_cells if total_cells else 0.0

    features = np.array(
        [
            result.total_length,
            grid.count(Cell.ENEMY),
            grid.count(Cell.TRAP),
            grid.count(Cell.TREASURE),
            wall_density,
        ]
    )

    raw_score = float(np.dot(features, WEIGHTS))

    return DifficultyScore(
        path_length=int(features[0]),
        enemy_count=int(features[1]),
        trap_count=int(features[2]),
        treasure_count=int(features[3]),
        wall_density=wall_density,
        raw_score=raw_score,
    )
