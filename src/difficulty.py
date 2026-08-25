"""
Scor de dificultate pentru un nivel generat si validat.

Combina mai multe caracteristici ale nivelului -- lungimea traseului optim,
numarul de inamici/capcane/comori, densitatea peretilor si densitatea
zonelor accesibile -- intr-un singur numar, printr-o suma ponderata (numpy).

Nota despre "densitatea peretilor si a zonelor accesibile": intr-un labirint
facut doar din WALL/FLOOR, procentul de zone accesibile e literal 1 minus
procentul de pereti (perfect complementare) -- a le pune pe amandoua ca
ponderi separate n-ar aduce nicio informatie noua, matematic ar fi doar o
rescriere a aceleiasi caracteristici. De-asta "densitatea zonelor
accesibile" e operationalizata aici ca ceva structural diferit: proportia
de celule accesibile care sunt FUNDATURI (`dead_end_ratio`) -- cat de
"ramificat"/confuz e labirintul, nu doar cat de multa piatra are. Doua
labirinturi cu aceeasi densitate de pereti pot avea numar foarte diferit de
fundaturi, deci chiar aduce semnal independent.

Acest scor e "tinta" pe care algoritmul genetic o va optimiza: fitness-ul
unui nivel candidat va fi cat de aproape e scorul lui de scorul cerut pentru
dificultatea aleasa de utilizator (Easy/Medium/Hard), nu doar "grid mai
mare = mai greu".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from grid import Cell, Grid, Position
from solver import ValidationResult

# Ordinea caracteristicilor conteaza -- trebuie sa corespunda cu WEIGHTS.
FEATURE_NAMES = ("path_length", "enemies", "traps", "treasures", "wall_density", "dead_end_ratio")

# Ponderi: cat de mult conteaza fiecare caracteristica in scorul final.
# wall_density si dead_end_ratio sunt proportii (0..1), de-asta ponderile lor
# sunt mult mai mari, ca sa fie comparabile cu celelalte caracteristici
# (numere intregi).
WEIGHTS = np.array([1.0, 4.0, 3.0, 1.5, 18.0, 14.0])

# Praguri de categorie, calibrate empiric: am generat 50 de niveluri pentru
# fiecare dificultate (seed 0..49) si am masurat distributia scorurilor,
# dupa adaugarea lui dead_end_ratio --
#   easy:   52 .. 66   (medie ~60)
#   medium: 89 .. 123  (medie ~109)
#   hard:   157 .. 221 (medie ~191)
# pragurile de mai jos sunt la mijlocul distantei dintre categorii vecine.
# Ajustabile daca se schimba DIFFICULTY_PRESETS din generator.py sau WEIGHTS.
EASY_MAX = 77.5
MEDIUM_MAX = 140.0

# Scor "tinta" reprezentativ pentru fiecare dificultate (media masurata) --
# folosit de algoritmul genetic (genetic.py) ca obiectiv de optimizare, ca
# sa poata cauta un nivel cat mai aproape de mijlocul benzii, nu doar
# "undeva in interiorul ei".
CATEGORY_TARGET_SCORE = {"easy": 60.0, "medium": 109.0, "hard": 191.0}


@dataclass
class DifficultyScore:
    path_length: int
    enemy_count: int
    trap_count: int
    treasure_count: int
    wall_density: float
    dead_end_ratio: float
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
            "dead_end_ratio": round(self.dead_end_ratio, 4),
            "raw_score": round(self.raw_score, 2),
            "category": self.category,
        }


def _dead_end_ratio(grid: Grid) -> float:
    """Proportia de celule accesibile care sunt fundaturi (au un singur
    vecin accesibil) -- caracteristica structurala, independenta de
    densitatea bruta de pereti (vezi nota din capul fisierului)."""
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
        if sum(1 for n in grid.neighbors(pos) if grid.is_walkable(n)) <= 1
    )
    return dead_ends / len(walkable_positions)


def compute_difficulty_score(grid: Grid, result: ValidationResult) -> DifficultyScore:
    """Calculeaza scorul de dificultate al unui nivel deja validat.
    Presupune ca `result.is_valid` e True (scorul unui nivel invalid nu are
    sens - nu exista "lungime de traseu" daca nu exista traseu)."""
    total_cells = grid.width * grid.height
    wall_density = grid.count(Cell.WALL) / total_cells if total_cells else 0.0
    dead_end_ratio = _dead_end_ratio(grid)

    features = np.array(
        [
            result.total_length,
            grid.count(Cell.ENEMY),
            grid.count(Cell.TRAP),
            grid.count(Cell.TREASURE),
            wall_density,
            dead_end_ratio,
        ]
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
